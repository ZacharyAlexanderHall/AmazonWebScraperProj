from WebScraper.core.utilities import logger, is_amazon_url
from WebScraper.core.amazon_product_scraper import scrape_page
from WebScraper.data.database_service import DatabaseService
from WebScraper.services.email_service import EmailService
 
# Url of product we are scraping for - using various URL types for testing.
url_list  = [
    "https://www.amazon.com/Nongshim-Ramyun-Black-Premium-Broth/dp/B0CHRNR43T/",
    "https://www.amazon.com/Jim-Dunlop-Tortex-Standard-1-0MM/dp/B0002D0CFS/",
    "https://www.amazon.com/adidas-Unisex-Samba-Sneaker-White/dp/B0CKMM41FY/",
    "https://www.amazon.com/Mario-Badescu-Drying-Lotion-fl/dp/B0017SWIU4/",
    "https://www.amazon.com/Fender-Stratocaster-Electric-Beginner-Warranty/dp/B0DTC2H4K2/ref=sr_1_11?crid=3NXKE6ILJVE5R&dib=eyJ2IjoiMSJ9.qE6vPozUOUXSHgTwdwq1Cu4CQqc1zmHXgsTgimN63bRACmnWJtKMWg5oFvBTwL6nJW8cUx_HJzGUlOsFGKs1zxrDneSjX-zc8BOnP5YHyRgqU0l3BQSLa4GmCc-Kau1qMnrnran88uPnTN1kqNY_6TAapcYdY1fJubSRFtYhp4EqYeq90mujwvk2wYYDW9Cxt-CLCRadM5Bcmevbkk9OLJm9IpBfq69kRN3qz24LeQkYi17oYKxd5cF3HcwAlOdwwR2BzXoJS7LBLebv5pljdcQdurLJkwGpp4uZCawEDZs.am-y1TpiYflSvz18V9LqtvnMWQyb4Yk0Szq7EtZs6vA&dib_tag=se&keywords=fender+stratocaster&qid=1765486222&sprefix=fender+stratocas%2Caps%2C202&sr=8-11",
    #"https://www.google.com/search?q=if+i+build+a+iphone+app&rlz=1C1CHBF_enUS946US946&oq=if+i+build+a+iphone+app&gs_lcrp=EgZjaHJvbWUyBggAEEUYOTIICAEQABgWGB4yDQgCEAAYhgMYgAQYigUyDQgDEAAYhgMYgAQYigUyBwgEEAAY7wUyBwgFEAAY7wUyBwgGEAAY7wUyBwgHEAAY7wXSAQg5MTEwajBqN6gCALACAA&sourceid=chrome&ie=UTF-8"
]

# Main Method
if __name__ == "__main__":
    logger.info("Starting Scraper...")

    db_service = DatabaseService()
    email_service = EmailService()

    for url in url_list:
        logger.info(f"Attempting to Scrape URL: {url}")
            
        if not is_amazon_url(url):
            logger.error(f"URL is not a valid Amazon URL: {url}")
            continue
        scrape_page(url, db_service=db_service, email_service=email_service)

    logger.info("Scraping Complete!")