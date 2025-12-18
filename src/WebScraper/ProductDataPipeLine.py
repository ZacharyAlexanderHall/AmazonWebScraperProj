import csv
import json
import os
import time

from dataclasses import fields, asdict
from pathlib import Path

from WebScraper.Utilities import logger
from WebScraper.Product import Product

# Create product_data filepath
THIS_FILE = Path(__file__).resolve()
PROJ_ROOT = THIS_FILE.parents[2] # Reachers Project Folder level
PROJ_DATA = PROJ_ROOT / "data"

# Define Product Data Pipeline
class ProductDataPipeLine:
    """Pipeline to save Data to Json, and in future iterations a SQL DB"""
    def __init__(self, csv_filename="", json_filename="", storage_queue_limit=5):
        self.storage_queue = []
        self.storage_queue_limit = storage_queue_limit
        self.csv_filename = csv_filename
        self.json_filename =  PROJ_DATA / json_filename # Creates full path to data folder
        self.csv_file_open = False
        self.products_seen = []

        """
        # upon Init attempt to load existing Product Data - May delete later
        try:
            with open(self.json_filename, 'r', encoding="utf-8") as output_file:
                existing_data = json.load(output_file)
                for product in existing_data:
                    self.products_seen.append(product.get("name"))
        except FileNotFoundError:
            logger.info(f"No existing product data found for file name: {self.json_filename}") 
        """

    def save_to_json(self):
        """Saves Product Info to Json File"""
        products_to_save = []
        json_data = []
        products_to_save.extend(self.storage_queue)
        self.storage_queue.clear()

        if not products_to_save:
            return

        # If data exists, write to json data list as dictionary.
        for product in products_to_save:
            json_data.append(asdict(product))

        # Use try/catch to try and read the json file to see if it already exists, if so load existing data.
        # if it doesn't exist, pass empty list as existing data


        try:
            with open(self.json_filename, 'r', encoding="utf-8") as output_file:
                existing_data = json.load(output_file)
        except FileNotFoundError:
            existing_data = []

        existing_data.extend(json_data)

        with open(self.json_filename, 'w', encoding="utf-8") as output_file:
            json.dump(existing_data, output_file, indent=2)

    def save_to_csv(self):
        """Saves product info to CSV File"""
        # Open CSV file, and then create List to save while clearing storage queue.
        self.csv_file_open = True
        products_to_save = []
        products_to_save.extend(self.storage_queue)
        self.storage_queue.clear()
        # if list is empty return.
        if not products_to_save:
            return

        keys = [field.name for field in fields(products_to_save[0])]
        file_exists = (
            os.path.isfile(self.csv_filename) and os.path.getsize(self.csv_filename) > 0
        )

        with open(self.csv_filename, mode="a", newline="", encoding="utf-8") as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=keys)

            if not file_exists:
                dict_writer.writeheader()

            for product in products_to_save:
                dict_writer.writerow(asdict(product))

        self.csv_file_open = False

    def clean_raw_products(self, scraped_data):
        """Takes Scraped Data and Returns a Member of the Product DataClass"""
        return Product( 
            name = scraped_data.get("name", ""),
            price = scraped_data.get("price", ""),
            url = scraped_data.get("url", ""),
            imageUrls = scraped_data.get("imageUrls", []),
            productDetails = scraped_data.get("productDetails", {})
        )

    #NOTE: added post_init to DataPipeline to handle duplicate checking - disabled for now.
    def is_duplicate(self, product_data):
        """Checks Existing Files to see if Product Information Already exists - Note: to be updated to include sql"""
        if product_data.name in self.products_seen:
            print(f"Duplicate Item Found: {product_data.name}. Skipping...")
            return True
        else:
            self.products_seen.append(product_data.name)
            return False

    def add_product(self, product: Product):
        """Save product Data to Json"""
        #product = self.clean_raw_products(scraped_data)
        if not self.is_duplicate(product):
            self.storage_queue.append(product)

            if (len(self.storage_queue) >= self.storage_queue_limit
                and self.csv_file_open == False):
                #self.save_to_csv()
                self.save_to_json()

    def close_pipeline(self):
        """Closes Data Pipeline and saves any remaining Data in Queue"""
        if self.csv_file_open:
            time.sleep(3)
        if len(self.storage_queue) > 0:
            #self.save_to_csv()
            self.save_to_json()