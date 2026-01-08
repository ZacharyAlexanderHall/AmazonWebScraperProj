from bs4 import BeautifulSoup
from typing import Optional

from WebScraper.core.utilities import logger
from WebScraper.data.product import Product
from WebScraper.core.retry_logic import RetryLogic
from WebScraper.services.email_service import EmailService
from WebScraper.data.database_service import DatabaseService
from WebScraper.core.amazon_parsers import parse_product_name, parse_product_price, parse_images, parse_product_features

retry_request = RetryLogic(retry_limit=5, anti_bot_check=False, use_fake_browser_headers=True)

# Page Scraping Function
def scrape_page(url:str, db_service = None, email_service = None) -> None:
    """Main Page Scraping Function"""
    if db_service is None:
        db_service = DatabaseService()
    if email_service is None:
        email_service = EmailService()

    valid, response = retry_request.make_request(url)
    if valid and response.status_code == 200:
        logger.info(f"Successfully Connected to Url: {url}")

        # Get HTML Content
        soup = BeautifulSoup(response.content, "html.parser")

        # Use HTML Scraper to parse product data
        product = _html_scraper(soup, url)

        # Check if product parsing was successful
        if product is None:
            logger.info(f"Error parsing product data from page: {url}")
            return

        # check if product exists in database
        existing_product = db_service.get_product_by_asin(product.asin)
        old_price = existing_product.price if existing_product else None

        # add or update product in database, returns True if price changed
        price_changed = db_service.add_product(product)

        # delete later...
        #email_service.send_email("zachdacrack@gmail.com", product)        

        if price_changed:
            logger.info(f"Price Change Detected for {product.name}: Old Price: {old_price}, New Price: {product.price}")
            triggered_alerts = db_service.check_price_alerts(product.asin, product.price)

            if triggered_alerts:
                for alert in triggered_alerts:
                    #send email
                    #email_service.send_price_alert(alert.user_email, product, alert.target_price)
                    logger.info(f"Price Alert Triggered for {product.name} at price {product.price} for {alert.user_email}")

        logger.info(f"Successfully Scraped Product: {product.name}")

        # Send email notification
        #email_serice.send_email("Zachdacrack@gmail.com", product)

    else:
        logger.info(f"Error getting page... Response status code: {response.status_code} \n URL: {url}")

# HTML Parser Function
def _html_scraper(soup: BeautifulSoup, url:str) -> Optional[Product]:
    try:
        """takes html content and scrapes product data returning product"""
        # Get Product Name and Price
        prodName = parse_product_name(soup)
        price = parse_product_price(soup)

        if prodName == "Unknown Product" or price is None:
            logger.info(f"Failed to parse product name or price. Name: {prodName}, Price: {price}")
            raise ValueError("Product name or price could not be determined.")

        # load product image(s)
        images_to_save = parse_images(soup)
        # Get Product Features
        prod_features = parse_product_features(soup)
        
        return Product(
            name = prodName,
            price = price,
            url = url, # Passed URL from Scrape Page Function
            imageUrls = images_to_save,
            productDetails = prod_features
        )
    except Exception as e:
        logger.error(f"Error in html_scraper: {e}")
        return None