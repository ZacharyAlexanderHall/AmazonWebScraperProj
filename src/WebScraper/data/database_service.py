import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict
from WebScraper.data.product import Product
from WebScraper.core.utilities import logger

# Create product_data filepath
THIS_FILE = Path(__file__).resolve()
PROJ_ROOT = THIS_FILE.parents[3] # Reachers Project Folder level
PROJ_DATA = PROJ_ROOT / "data"
DB_PATH = str(PROJ_DATA / "Amazon_Scraper.db")

class DatabaseService:
    """Service for interacting with the SQLite database."""
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

        # if table does not exist, create it
        self._ensure_tables_exist()

    def _ensure_tables_exist(self):
        """Create Products, PriceHistory, and PriceAlerts Table if it does not exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Create Products Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS Products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asin TEXT UNIQUE NOT NULL,
                product_name TEXT NOT NULL,
                current_price REAL NOT NULL,
                url TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                details_json TEXT,
                images_json TEXT
            );
            """)

            # Create PriceHistory Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS PriceHistory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asin TEXT NOT NULL,
                price REAL NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (asin) REFERENCES Products(asin)
            );
            """)

            # Create PriceAlerts Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS PriceAlerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asin TEXT NOT NULL,
                target_price REAL NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (asin) REFERENCES Products(asin)
            );
            """)

            # Create URL Tracking Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS TrackedURLs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                asin TEXT UNIQUE NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            );
            """)

            # Commit changes
            conn.commit()

    def add_product(self, product: Product) -> bool:
        """
        Add new product or update existing one. Track price history.
        
        Returns:
            bool: True if price changed, False if new product or same price
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if product exists
                cursor.execute(
                    "SELECT current_price FROM Products WHERE asin = ?", 
                    (product.asin,)
                )
                result = cursor.fetchone()
                
                details_json = json.dumps(product.productDetails)
                images_json = json.dumps(product.imageUrls)
                
                price_changed = False
                
                if result:
                    # Product exists - check if price changed
                    old_price = result[0]
                    if abs(old_price - product.price) > 0.01:  # Account for floating point
                        price_changed = True
                        
                        # Update product
                        cursor.execute("""
                        UPDATE Products 
                        SET current_price = ?, product_name = ?, url = ?, 
                            details_json = ?, images_json = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE asin = ?
                        """, (product.price, product.name, product.url, 
                            details_json, images_json, product.asin))
                        
                        # Add to price history
                        cursor.execute("""
                        INSERT INTO PriceHistory (asin, price)
                        VALUES (?, ?)
                        """, (product.asin, product.price))
                        
                        logger.info(
                            f"Price changed for {product.name}: ${old_price:.2f} -> ${product.price:.2f}"
                        )
                else:
                    # New product - insert
                    cursor.execute("""
                    INSERT INTO Products (asin, product_name, current_price, url, details_json, images_json)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, (product.asin, product.name, product.price, product.url, 
                        details_json, images_json))
                    
                    # Add initial price to history
                    cursor.execute("""
                    INSERT INTO PriceHistory (asin, price)
                    VALUES (?, ?)
                    """, (product.asin, product.price))
                    
                    logger.info(f"Added new product: {product.name} at ${product.price:.2f}")
                
                conn.commit()
                return price_changed
        except sqlite3.IntegrityError:
            print(f"Product with ASIN {product.asin} already exists in the database.")
        except Exception as e:
            print(f"An error occurred while adding the product: {e}")

    def get_product_by_asin(self, asin: str) -> Optional[Product]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""SELECT asin, product_name, current_price, url, details_json, images_json
                                FROM Products WHERE asin = ?""", (asin,))
                row = cursor.fetchone()
                
                if row:
                    details = json.loads(row[4]) if row[4] else {}
                    images = json.loads(row[5]) if row[5] else []
                    
                    product = Product(
                        asin=row[0],
                        name=row[1],
                        price=row[2],
                        url=row[3],
                        productDetails=details,
                        imageUrls=images
                    )
                    return product
                else:
                    logger.info(f"No product found with ASIN: {asin}")
                    return None
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            return None
    
    def get_price_history(self, asin: str) -> List[Dict]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                SELECT price, timestamp FROM PriceHistory WHERE asin = ? ORDER BY timestamp ASC
                """, (asin,))

                # create list of dicts for price history
                rows = cursor.fetchall()
                history = [
                    {"price": row[0], "timestamp": row[1]} for row in rows
                ]

                return history
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            return []
        
    def get_all_products(self) -> List[Product]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM Products ORDER BY updated_at DESC")
                rows = cursor.fetchall()
                
                products = []
                for row in rows:
                    details = json.loads(row[7]) if row[7] else {}
                    images = json.loads(row[8]) if row[8] else []
                    
                    product = Product(
                        asin=row[1],
                        name=row[2],
                        price=row[3],
                        url=row[4],
                        productDetails=details,
                        imageUrls=images
                    )
                    products.append(product)
                
                return products
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            return []

    def set_price_alert(self, asin: str, target_price: float, email: str) -> bool:
        """Set a price alert for a product via asin"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert price alert
                cursor.execute("""
                INSERT INTO PriceAlerts (asin, target_price, email)
                VALUES (?, ?, ?)
                """, (asin, target_price, email))
                
                conn.commit()
                logger.info(f"Set price alert for ASIN {asin} at ${target_price:.2f} to {email}")
                return True
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            return False
    
    def check_price_alerts(self, asin: str, current_price: float) -> List[Dict]:
        """Check if any price alerts are triggered for a given product asin"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get active price alerts for the product
                cursor.execute("""
                SELECT id, target_price, email FROM PriceAlerts 
                WHERE asin = ? AND is_active = 1 AND target_price >= ?
                """, (asin, current_price))
                
                rows = cursor.fetchall()
                alerts_triggered = [
                    {
                        "id": row[0],
                        "target_price": row[1],
                        "email": row[2]
                    } 
                    for row in rows
                ]

                # Deactivate Triggered Alerts to avoid spamming
                if alerts_triggered:
                    alert_ids = [alert["id"] for alert in alerts_triggered]
                    sql_placeholder = ','.join('?' * len(alert_ids))
                    cursor.execute(
                        f"""UPDATE PriceAlerts SET is_active = 0 WHERE id IN ({sql_placeholder})""",
                        alert_ids
                    )
                    conn.commit()
                
                return alerts_triggered
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            return []
        
    def get_active_alerts(self) -> List[Dict]:
        """Retrieve all active price alerts"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                SELECT pa.id, pa.asin, pa.target_price, pa.email, p.product_name, p.current_price
                FROM PriceAlerts pa
                JOIN Products p ON pa.asin = p.asin
                WHERE pa.is_active = 1
                ORDER BY pa.created_at desc
                """)
                
                active_alerts = [
                    {
                    "id": row[0],
                    "asin": row[1],
                    "target_price": row[2],
                    "email": row[3],
                    "product_name": row[4],
                    "current_price": row[5]
                    } 
                    for row in cursor.fetchall()
                ]
                return active_alerts
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            return []
    
    def add_url(url:str, asin:str) -> bool:
        """Add a new URL to be tracked in the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO TrackedURLs (url, asin)
                VALUES (?, ?)
                """, (url, asin))
                
                conn.commit()
                logger.info(f"Added new URL to track: {url}")
                return True
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            return False
        
    def get_all_active_urls(self) -> list[Dict]:
        """Retrieve all tracked URLs from the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                SELECT id, url, asin FROM TrackedURLs
                WHERE is_active = 1
                ORDER BY created_at DESC
                """)
                
                tracked_urls = [
                    {"id": row[0], "url": row[1], "asin": row[2]} 
                    for row in cursor.fetchall()
                ]
                return tracked_urls
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            return []

    def get_all_tracked_urls(self) -> list[Dict]:
        """Retrieve all tracked URLs from the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                SELECT id, url, asin FROM TrackedURLs
                ORDER BY created_at DESC
                """)
                
                tracked_urls = [
                    {"id": row[0], "url": row[1], "asin": row[2]} 
                    for row in cursor.fetchall()
                ]
                return tracked_urls
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            return []

    def removed_tracked_url(self, asin: str) -> bool:
        """Remove a tracked URL from the database by its ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                UPDATE TrackedURLs 
                SET is_active = 0 
                WHERE asin = ?
                """, (asin,))
                
                conn.commit()
                logger.info(f"Removed URL from Tracking: {url_id}")
                return True
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            return False
        
    def delete_price_alert(self, asin: str) -> bool:
        """Delete a price alert by its ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM PriceAlerts WHERE asin = ?", (asin,))
                
                conn.commit()
                logger.info(f"Deleted price alert with ASIN: {asin}")
                return True
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            return False