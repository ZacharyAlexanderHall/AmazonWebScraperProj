from bs4 import BeautifulSoup

from WebScraper.core.utilities import clean_text, logger
from WebScraper.data.product import Product
from WebScraper.core.retry_logic import RetryLogic
from WebScraper.services.email_service import EmailService
from WebScraper.data.database_service import DatabaseService

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
        product = html_scraper(soup, url)

        # Add Info to scraped Data List as Dictionary.
        #data_pipeline.add_product(product)

        # check if product exists in database
        existing_product = db_service.get_product_by_asin(product.asin)
        old_price = existing_product.price if existing_product else None

        # add or update product in database, returns True if price changed
        price_changed = db_service.add_product(product)

        # delete later...
        email_service.send_email("Zachdacrack@gmail.com", product)        

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
def html_scraper(soup, url):
    try:
        """takes html content and scrapes product data returning product"""
        # Get Product Name and Price
        prodName = soup.find("span", {"id": "productTitle"}).text.strip()
        priceWhole = soup.find("span", {"class": "a-price-whole"}).text.strip()
        priceDecimal = soup.find("span", {"class": "a-price-fraction"}).text.strip()
        price = float(f"{priceWhole}{priceDecimal}")

        # see if this can be cleaned up. Currently loops through multiple nested spans to get all specific product images.
        # load product image(s)
        images_to_save = []
        spans = soup.find_all('span')
        for span in spans:
            image_array = span.find_all('span')
            for item in image_array:
                image_span = item.find('span')
                if image_span is not None:
                    images = image_span.find_all('img')
                    for img in images:
                        img_url = img.get('src')
                        if "https://m.media-amazon.com/images/" in img_url and img_url not in images_to_save:
                            images_to_save.append(img_url)

        #Get Product Features
        prod_features = {}

        features_bullets = soup.find("div", id="detailBullets_feature_div")
        if features_bullets:
            for li in features_bullets.select("ul li"):
                text_span = li.find("span", class_="a-list-item")
                if text_span:

                    # Extract text and clean it
                    raw_text = text_span.get_text(strip=True)

                    # Remove Unicode BiDi control characters
                    cleaned_text = clean_text(raw_text)

                    # Must contain a key:value pattern - helps to avoid links and other non relevant data.
                    if ":" not in cleaned_text:
                        continue

                    key, value = [part.strip() for part in cleaned_text.split(":", 1)]

                    prod_features[key] = value
        else:
            details = soup.find("div", id="prodDetails")
            if details:
                for row in details.select("tr"): #select tablerows
                    key = clean_text(row.find("th").text)
                    value = clean_text(row.find("td").text)
                    prod_features[key] = value
        
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