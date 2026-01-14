import sys
import time
import random
from datetime import datetime, timedelta

from WebScraper.data.database_service import DatabaseService
from WebScraper.services.email_service import EmailService
from WebScraper.core.amazon_product_scraper import scrape_page
from WebScraper.core.utilities import logger, is_amazon_url, extract_asin_from_url, is_email_address

db_service = DatabaseService()

# ============================================================================
# URL MANAGEMENT
# ============================================================================
def add_url(url:str):
    """Add a new URL to be tracked in the database."""
    # Validate URL
    if not is_amazon_url(url):
        print(f"❌ INVALID URL: {url}")
        print("Please provide a valid Amazon product URL...")
        return
    
    # Extract ASIN
    asin = extract_asin_from_url(url)
    if not asin:
        print(f"❌ INVALID URL: Could not extract ASIN from URL: {url}")
        print("Please provide a valid Amazon product URL...")
        return

    # Ensure Product doesn't already exist in Db
    existing_urls = db_service.get_all_tracked_urls()
    for entry in existing_urls:
        if entry['asin'] == asin:
            print(f"⚠️ Product already being tracked!")
            print(f"ASIN: {asin}")
            print(f"Existing Url:{url}")
            
            print("Setting Existing URL to active...")
            db_service.set_url_to_active(asin)
            print(f"✅ URL for Product: '{asin}' set to actively track!")
            print(f"   ASIN: {asin}")
            print(f"   URL: {url}")
            return

    # Add URL to Database
    db_service.add_url(url, asin)
    print(f"✅ URL added to tracking list!")
    print(f"   ASIN: {asin}")
    print(f"   URL: {url}")
    print(f"\n   Run 'run-scrape' to scrape it now")
 
def show_urls():
    """Display all currently tracked URLs."""
    tracked_urls = db_service.get_all_active_urls()
    if not tracked_urls:
        print("No URLs are currently being tracked.")
        return

    print(f"\n🔗 Tracked URLs ({len(tracked_urls)}):\n")
    print("-" * 100)
    
    for url_data in tracked_urls:
        print(f"ID: {url_data['id']}")
        print(f"ASIN: {url_data['asin']}")
        print(f"URL: {url_data['url']}")
        print(f"Added: {url_data['created_at']}")
        print()

def remove_url(asin:str):
    tracked_urls = db_service.get_all_active_urls()
    if not tracked_urls:
        print("No URLs are currently being tracked.")
        return

    for urlData in tracked_urls:
        if urlData["asin"] == asin:
            db_service.removed_tracked_url(asin)
            print(f"Product: {asin} is no longer being tracked...")
            return

    print(F"URL for Product: {asin} Not found...")

# ============================================================================
# SCRAPING
# ============================================================================
def run_scrape():
    """Scrape all currently tracked URLs."""
    url_data_list = db_service.get_all_active_urls()
    if not url_data_list:
        print("No URLs to scrape. Please add URLs first.")
        return

    print(f"Starting scrape for {len(url_data_list)} URLs...\n")

    email_service = EmailService()
    success_count = 0
    fail_count = 0

    for url_data in url_data_list:
        try:
            url = url_data['url']
            print(f"   🔍 Scraping URL: {url}")

            if scrape_page(url, db_service=db_service, email_service=email_service):
                print(f"   ✅ Scrape successful!\n")
                success_count += 1
            else:
                print(f"Scrape unsccessful for Url: {url}")
                fail_count += 1
        except Exception as e:
            print(f"   ❌ Scrape failed: {e}\n")
            logger.error(f"Error scraping URL {url}: {e}")
            fail_count += 1
        finally:
            time.sleep(random.uniform(3,10))
    
    print("-" * 60)
    print(f"Scraping complete!")
    print(f"  Success: {success_count}")
    print(f"  Errors: {fail_count}")

    return success_count, fail_count

def run_scheduler(interval_hours: int = 48):
    """Run Scraper on a scheduled interval, defauklts to every 48 hours."""
    print(f"🕐 Starting scheduler: scraping every {interval_hours} hours")
    print("Press Ctrl+C to stop\n")

    try:
        run_number = 1
        while True:
            # Runtime Info
            now = datetime.now()
            print(f"\n{'='*60}")
            print(f"Run #{run_number} - {now.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}\n")

            # Run Scrape
            run_scrape()

            # Next run info
            next_run = now + timedelta(hours=interval_hours)
            print(f"{run_number} consecutive sucessful runs")
            print(f"\nNext scrape: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Sleeping for {interval_hours} hours...\n")
            print("Press Ctrl+C to stop\n")
            
            # Sleep until next Scheduled Scrape 
            time.sleep(interval_hours * 3600)
            run_number += 1
    except KeyboardInterrupt:
        print("\n\nScheduler stopped by user.")
# ============================================================================
# ALERT MANAGEMENT
# ===========================================================================+
def add_alert(asin: str, target_price: float, target_email: str):
    """Add a price alert for a specific product."""
    # Verify product exists
    product = db_service.get_product_by_asin(asin)
    
    if not product:
        print(f"❌ Product with ASIN {asin} not found in database.")
        print("   Tip: Scrape the product first with: python Amazon_Web_Scraper.py run-scrape")
        return
    
    if not is_email_address(target_email):
        print(f"Email: '{target_email}' is not a valid email address, please enter Valid Email")
        return
    
    # Create alert
    db_service.set_price_alert(asin, target_price, target_email)
    
    print(f"✅ Alert created successfully!")
    print(f"   Product: {product.name[:60]}")
    print(f"   Current price: ${product.price:.2f}")
    print(f"   Alert price: ${target_price:.2f}")
    print(f"   Email: {target_email}")
    
    if product.price <= target_price:
        print(f"   ⚠️  Current price already meets alert threshold!")

def show_alerts():
    """List all active price alerts."""
    alerts = db_service.get_active_alerts()
    
    if not alerts:
        print("No active alerts.")
        print("Tip: Add an alert with: python manage_alerts.py add-alert <asin> <price> <email>")
        return
    
    print(f"\n📊 Active Price Alerts ({len(alerts)}):\n")
    print("-" * 100)
    
    for alert in alerts:
        status = "🟢" if alert["current_price"] <= alert["target_price"] else "🔴"
        
        print(f"{status} Alert ID: {alert['id']}")
        print(f"   Product: {alert['product_name'][:60]}")
        print(f"   ASIN: {alert['asin']}")
        print(f"   Target: ${alert['target_price']:.2f} | Current: ${alert['current_price']:.2f}")
        print(f"   Email: {alert['target_email']}")
        print()

def delete_alert(asin:str):
    """Delete Price Alerts"""
    success = db_service.delete_price_alert(asin)

    if success:
        print(f"✅ Alert deleted for Product: '{asin}'")
    else:
        print(f"❌ Alert for Product '{asin}' not found")

# ============================================================================
# VIEWING DATA
# ============================================================================
def show_products():
    """List all tracked products."""
    products = db_service.get_all_products()
    
    if not products:
        print("No products in database.")
        print("Tip: Run scraper with: python manage_alerts.py run-scrape")
        return
    
    print(f"\n📦 Tracked Products ({len(products)}):\n")
    print("-" * 100)
    
    for product in products:
        print(f"• {product.name[:70]}")
        print(f"  ASIN: {product.asin}")
        print(f"  Price: ${product.price:.2f}")
        print(f"  Last updated: {product.updated_at or 'N/A'}")
        
        # Show price history count
        history = db_service.get_price_history(product.asin)
        if len(history) > 1:
            print(f"  Price changes: {len(history)}")
        print()

# ============================================================================
# HELP & USAGE
# ============================================================================
def show_usage():
    """Display help message."""
    print("""
Amazon Price Tracker - Management Tool

USAGE:
    python manage_alerts.py <command> [arguments]

URL MANAGEMENT:
    add-url <url>                 Add a product URL to track
    show-urls                     Show all tracked URLs
    remove-url <id>               Remove a URL by ID
    run-scrape                    Scrape all tracked URLs now
    run-schedule <hours>          Run Scraper ever X hours (continuous)

ALERT MANAGEMENT:
    add-alert <asin> <price> <email>   Create price alert
    list-alerts                        Show all active alerts
    delete-alert <id>                  Delete alert by ID

VIEWING DATA:
    show-products                 Show all tracked products
    help                          Show this help message

EXAMPLES:
    # Add a product URL to track
    python manage_alerts.py add-url "https://www.amazon.com/dp/B0CHRNR43T/"
    
    # Scrape all tracked URLs
    python manage_alerts.py run-scrape
    
    # Create price alert
    python manage_alerts.py add-alert B0CHRNR43T 25.00 you@example.com
    
    # List all alerts
    python manage_alerts.py list-alerts
    
    # Delete an alert
    python manage_alerts.py delete-alert 1

WORKFLOW:
    1. Add URLs: python manage_alerts.py add-url <amazon_url>
    2. Scrape: python manage_alerts.py run-scrape
    3. Check products: python manage_alerts.py show-products
    4. Set alerts: python manage_alerts.py add-alert <asin> <price> <email>
    5. Run scraper periodically (manually or scheduled)
    """)

def main():
    """Main CLI router."""
    if len(sys.argv) < 2:
        show_usage()
        return
    
    command = sys.argv[1].lower()
    
    try:
        if command == "add-url":
            if len(sys.argv) != 3:
                print("❌ Usage: add-url <amazon_url>")
                return
            add_url(sys.argv[2])
        
        elif command == "show-urls":
            show_urls()
        
        elif command == "remove-url":
            if len(sys.argv) != 3:
                print("❌ Usage: remove-url <asin>")
                print("Please enter Product ASIN (Use command 'show-products' to view all saved products)")
                print("the URL associated with the provided ASIN will be deleted")
                return
            try:
                asin = sys.argv[2]
                remove_url(asin)
            except ValueError:
                print("❌ ID must be a number")
        
        elif command == "run-scrape":
            run_scrape()

        elif command == "run-schedule":
            if len(sys.argv) != 3:
                print("❌ Usage: schedule <hours>")
                print("   Example: schedule 48")
                return
            try:
                hours = int(sys.argv[2])
                if hours < 1:
                    print("❌ Hours must be at least 1")
                    return
                run_scheduler(hours)
            except ValueError:
                print("❌ Hours must be a number")
        
        elif command == "add-alert":
            if len(sys.argv) != 5:
                print("❌ Usage: add-alert <asin> <price> <email>")
                return
            asin = sys.argv[2]
            try:
                price = float(sys.argv[3])
            except ValueError:
                print(f"❌ Price must be a number, got: '{sys.argv[3]}'")
                return
            email = sys.argv[4]
            add_alert(asin, price, email)
        
        elif command == "show-alerts":
            show_alerts()
        
        elif command == "delete-alert":
            if len(sys.argv) != 3:
                print("❌ Usage: delete-alert <asin>")
                return
            try:
                asin = sys.argv[2]
                delete_alert(asin)
            except ValueError:
                print(f"❌ Unable to delete Alert for Product: {asin}")
        
        elif command == "show-products":
            show_products()
        
        elif command == "help":
            show_usage()
        
        else:
            print(f"❌ Unknown command: '{command}'")
            print()
            show_usage()
    
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.error(f"CLI error: {e}")

if __name__ == "__main__":
    main()