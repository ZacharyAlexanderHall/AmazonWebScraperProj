import requests
from bs4 import BeautifulSoup

from WebScraper.Utilities import clean_text, logger
from WebScraper.Product import Product
from WebScraper.ProductDataPipeLine import ProductDataPipeLine
from WebScraper.RetryLogic import RetryLogic

# testing
from WebScraper.EmailService import EmailService
email_serice = EmailService()

# Do I make my instance of Data Pipeline and Retry Logic here, or in main and pass them in?
data_pipeline = ProductDataPipeLine(
        csv_filename="product_data.csv", json_filename="product_data.json"
    )
retry_request = RetryLogic(retry_limit=5, anti_bot_check=False, use_fake_browser_headers=True)

# Page Scraping Function
def scrape_page(url):
    """Main Page Scraping Fucntion"""
    valid, response = retry_request.make_request(url)
    if valid and response.status_code == 200:
        logger.info(f"Successfully Connected to Url: {url}")

        # Get HTML Content
        soup = BeautifulSoup(response.content, "html.parser")

        # Use HTML Scraper to parse product data
        product = html_scraper(soup, url)

        # Add Info to scraped Data List as Dictionary.
        data_pipeline.add_product(product)

        logger.info(f"Successfully Scraped Product: {product.name}")

        # Send email notification
        email_serice.send_email("Zachdacrack@gmail.com", product)

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
        prodFeatures = {}

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

                    prodFeatures[key] = value
        else:
            details = soup.find("div", id="prodDetails")
            if details:
                for row in details.select("tr"): #select tablerows
                    key = clean_text(row.find("th").text)
                    value = clean_text(row.find("td").text)
                    prodFeatures[key] = value
        
        return Product(
            name = prodName,
            price = price,
            url = url, # Passed URL from Scrape Page Function
            imageUrls = images_to_save,
            productDetails = prodFeatures
        )
    except Exception as e:
        logger.error(f"Error in html_scraper: {e}")
        return None