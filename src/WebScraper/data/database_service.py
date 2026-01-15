import sqlite3
import json
import os
from pathlib import Path
from typing import List, Optional, Dict
from WebScraper.data.product import Product
from WebScraper.core.utilities import logger, extract_asin_from_url

# Create product_data filepath
def get_data_directory():
    """Get / Create the application data directiory"""
    # Check if we're in development (has src/ folder structure)
    if os.path.exists(Path(__file__).resolve().parents[3] / "data"):
        # Development mode - use project data folder
        data_dir = Path(__file__).resolve().parents[3] / "data"
    else:
        # Production mode - use user's home directory
        data_dir = Path.home() / ".amazon_price_tracker" / "data"
        
    # create Directory if it doesn't exist
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

PROJ_DATA = get_data_directory()
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
                target_email TEXT NOT NULL,
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
            logger.warning(f"Product with ASIN {product.asin} already exists in the database.")
            return False
        except Exception as e:
            logger.warning(f"An error occurred while adding the product {product.asin}: {e}")
            raise

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
            logger.error(f"Database error wile fetching product {asin}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected Error while fetching product {asin}: {e}")
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
            logger.error(f"Database error while fetching price history for product {asin}: {e}")
            return []
        except Exception as e:
            logger.error(f"error while fetching price history for product {asin}: {e}")
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
            logger.error(f"Database error while fetching all products: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error while fetching all products: {e}")
            return []

    def set_price_alert(self, asin: str, target_price: float, email: str) -> bool:
        """Set a price alert for a product via asin"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert price alert
                cursor.execute("""
                INSERT INTO PriceAlerts (asin, target_price, target_email)
                VALUES (?, ?, ?)
                """, (asin, target_price, email))
                
                conn.commit()
                logger.info(f"Set price alert for ASIN {asin} at ${target_price:.2f} to {email}")
                return True
        except sqlite3.Error as e:
            logger.error(f"Database error setting alert for {asin}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error setting alert for {asin}: {e}")
            return False
    
    def check_price_alerts(self, asin: str, current_price: float) -> List[Dict]:
        """Check if any price alerts are triggered for a given product asin"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get active price alerts for the product
                cursor.execute("""
                SELECT id, target_price, target_email FROM PriceAlerts 
                WHERE asin = ? AND is_active = 1 AND target_price >= ?
                """, (asin, current_price))
                
                rows = cursor.fetchall()
                alerts_triggered = [
                    {
                        "id": row[0],
                        "target_price": row[1],
                        "target_email": row[2]
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
            logger.error(f"Database error while fetching price alerts for product {asin}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error while fetching price alerts for product {asin}: {e}")
            return []
        
    def get_active_alerts(self) -> List[Dict]:
        """Retrieve all active price alerts"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                SELECT pa.id, pa.asin, pa.target_price, pa.target_email, p.product_name, p.current_price
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
                    "target_email": row[3],
                    "product_name": row[4],
                    "current_price": row[5]
                    } 
                    for row in cursor.fetchall()
                ]
                return active_alerts
        except sqlite3.Error as e:
            logger.error(f"Database error while fetching active alerts: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error while fetching active alerts: {e}")
            return []
    
    def add_url(self, url:str, asin:str) -> bool:
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
            logger.error(f"Database error while adding url: {url}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while adding url: {url}: {e}")
            return False
        
    def get_all_active_urls(self) -> list[Dict]:
        """Retrieve all tracked URLs from the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                SELECT id, url, asin, created_at FROM TrackedURLs
                WHERE is_active = 1
                ORDER BY created_at DESC
                """)
                
                tracked_urls = [
                    {"id": row[0], "url": row[1], "asin": row[2], "created_at": row[3]} 
                    for row in cursor.fetchall()
                ]
                return tracked_urls
        except sqlite3.Error as e:
            logger.error(f"Database error while fetching all tracked Urls: {e}")
            return []
        except Exception as e:
            logger.error(f"unexpected error while fetching all tracked Urls: {e}")
            return []

    def get_all_saved_urls(self) -> list[Dict]:
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
            logger.error(f"Database error while fetching all urls: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error while fetching all urls: {e}")
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
                logger.info(f"Removed URL associated with Product: {asin} from tracking...")
                return True
        except sqlite3.Error as e:
            logger.error(f"Database error while removing URL from tracked list: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while removing URL from tracked list: {e}")
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
            logger.error(f"Database error while deleting price alert for product {asin}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while deleting price alert for product {asin}: {e}")
            return False
        
    def set_url_to_active(self, asin:str) -> bool:
        """Updates a saved URL to the active state"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE TrackedURLS SET [is_active] = 1 WHERE [asin] = ?", (asin,))

                conn.commit()
                logger.info(f"Updated URL for Product: {asin}")
                return True
        except sqlite3.Error as e:
            logger.error(f"Database error while updating URL to be actively tracked: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error while updating URL to be actively tracked: {e}")
            return False