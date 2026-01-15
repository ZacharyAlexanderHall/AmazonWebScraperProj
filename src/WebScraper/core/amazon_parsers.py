import re
from typing import Optional
from bs4 import BeautifulSoup

from WebScraper.core.utilities import logger
from WebScraper.core.utilities import clean_text

# Selectors for parsing product name and price from Amazon product pages - NOTE: Dictionary Order matters as ID is more reliable than class
AMAZON_PRODUCT_TITLE_SELECTORS = [
    {
        "tag": "span",
        "attrs": {"id": "productTitle"}
    },
    {
        "tag": "h1",
        "attrs": {"id": "title"}
    },
    {
        "tag": "span",
        "attrs": {"id": "ebooksProductTitle"}
    },
    {
        "tag": "span",
        "attrs": {"class": "a-size-large product-title-word-break"}
    },
    {
        "tag": "span",
        "attrs": {"class": "a-size-large a-spacing-none"}
    },
    {
        "tag": "h1",
        "attrs": {"class": "a-size-large a-spacing-none"}
    },
]

AMAZON_PRICE_WHOLE_SELECTORS = [
    {
        "tag": "span",
        "attrs": {"class": "a-price-whole"}
    },
    {
        "tag": "span",
        "attrs": {"class": "a-price a-text-price"}
    },
    {
        "tag": "span",
        "attrs": {"class": "a-offscreen"}
    },
]

AMAZON_PRICE_FRACTION_SELECTORS = [
    {
        "tag": "span",
        "attrs": {"class": "a-price-fraction"}
    },
    {
        "tag": "span",
        "attrs": {"class": "a-offscreen"}
    },
]

AMAZON_PRICE_OFFSCREEN_SELECTORS = [
    {
        "tag": "span",
        "attrs": {"class": "a-offscreen"}
    },
]

AMAZON_BUYBOX_IDS = [
    "corePriceDisplay_desktop_feature_div",
    "corePrice_desktop",
    "centerCol",
]

def parse_product_name(soup: BeautifulSoup) -> str:
    """Parses product name from soup object using multiple selectors."""
    for selector in AMAZON_PRODUCT_TITLE_SELECTORS:
        title_tag = soup.find(selector["tag"], selector["attrs"])
        if title_tag:
            return title_tag.text.strip()
    return "Unknown Product"

def parse_product_price(soup: BeautifulSoup) -> Optional[float]:
    """Attempts tp parse price via Whole & Fraction selectors, and then falls back to a-offscreen price as last resort."""
    # First try to find price by using seperate selectors for the "Whole" and "Fraction" of price.
    price_whole = None
    price_fraction = "00"  # Default to 00 if no fraction found

    for selector in AMAZON_PRICE_WHOLE_SELECTORS:
        whole_tag = soup.find(selector["tag"], selector["attrs"])
        if whole_tag:
            price_whole = whole_tag.text.strip().replace(',', '').replace('.', '')
            break
        logger.info(f"Initial Amazon Price Whole selector 'Tag: {selector['tag']} Selector: {selector['attrs']}' not found, trying alternative selectors...")

    # Try to find the fractional part of the price
    for selector in AMAZON_PRICE_FRACTION_SELECTORS:
        fraction_tag = soup.find(selector["tag"], selector["attrs"])
        if fraction_tag:
            price_fraction = fraction_tag.text.strip().replace(',', '')
            break
        logger.info(f"Amazon Price Fraction selector 'Tag: {selector['tag']} Selector: {selector['attrs']}' not found, trying alternative selectors...")

    if price_whole is not None:
        try:
            return float(f"{price_whole}.{price_fraction}")
        except ValueError:
            logger.error(f"Error converting price to float: {price_whole}.{price_fraction}")

    # Try to find price using a-offscreen selectors as last resort.
    for container_id in AMAZON_BUYBOX_IDS:
        container = soup.find("div", {"id": container_id})
        if not container:
            continue

        for selector in AMAZON_PRICE_OFFSCREEN_SELECTORS:
            offscreen_tag = container.find(selector["tag"], selector["attrs"])
            if offscreen_tag:
                price = re.sub(r'[^\d\.]', '', offscreen_tag.text.strip())
                if price:
                    try:
                        return float(price)
                    except ValueError:
                        logger.error(f"Error converting price to float: {price}")

    logger.info("a-offscreen price not found...")

    return None # return None if price could not be determined

def parse_images(soup: BeautifulSoup) -> list:
    """Parses product image URLs from soup object."""
    # see if this can be cleaned up. Currently loops through multiple nested spans to get all specific product images.
    # Trying to avoid specificing looking for all "img" as that pulls irrelevant data, need to find consistent selector for only product info 
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
    return images_to_save

def parse_product_features(soup: BeautifulSoup) -> dict:
    """Parses product features from soup object."""
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
            for row in details.select("tr"): # Select tablerows
                key = clean_text(row.find("th").text)
                value = clean_text(row.find("td").text)
                prod_features[key] = value

    return prod_features