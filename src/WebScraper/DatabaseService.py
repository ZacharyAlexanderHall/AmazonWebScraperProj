import sqlite3
import json
from pathlib import Path
from datetime import datetime
from WebScraper.Product import Product

# Create product_data filepath
THIS_FILE = Path(__file__).resolve()
PROJ_ROOT = THIS_FILE.parents[2] # Reachers Project Folder level
PROJ_DATA = PROJ_ROOT / "data"
DB_PATH = str(PROJ_DATA / "Amazon_Scraper.db")

class DatabaseService:
    """Service for interacting with the SQLite database."""
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        # if table does not exist, create it
        self._create_tables()

    def _create_tables(self):
        """Create Products Table if it does not exist."""
        query = """
        Create Table If Not Exists Products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asin TEXT UNIQUE NOT NULL,
            product_name TEXT NOT NULL,
            price REAL NOT NULL,
            url TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            details_json TEXT,
            images_json TEXT
        );
        """
        self.cursor.execute(query)
        self.conn.commit()

    def add_product(self, product: Product):
        """Add a new product to the Products table."""
        try:
            # Convert product details and images to JSON strings
            details_json = json.dumps(product.productDetails)
            images_json = json.dumps(product.imageUrls)

            # Insert product data into the Products table
            query = """
            INSERT INTO Products (asin, product_name, price, url, details_json, images_json)
            VALUES (?, ?, ?, ?, ?, ?);
            """
            self.cursor.execute(query, (product.asin, product.name, product.price, product.url, details_json, images_json))
            self.conn.commit()
        except sqlite3.IntegrityError:
            print(f"Product with ASIN {product.asin} already exists in the database.")
        except Exception as e:
            print(f"An error occurred while adding the product: {e}")

    def get_product_by_asin(self, asin: str) -> Product:
        """Retrieve a product from the Products table by its ASIN."""
        query = """
        SELECT *
        FROM Products
        WHERE asin = ?;
        """
        self.cursor.execute(query, (asin))
        row = self.cursor.fetchone()

        if row:
            details = json.loads(row[6])
            images = json.loads(row[7])
            product = Product(row[1], row[2], row[3], row[4], details, images)
            product.id = row[0]
            product.timestamp = datetime.strptime(row[5], '%Y-%m-%d %H:%M:%S')
            return product
        else:
            return None