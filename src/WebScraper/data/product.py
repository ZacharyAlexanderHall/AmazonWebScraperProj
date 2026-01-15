from dataclasses import dataclass, field
from datetime import datetime
from WebScraper.core.utilities import extract_asin_from_url
from typing import List, Optional

# Define DataClass
@dataclass
class Product:
    """Data Class for Product Data"""
    name: str = ""                                      # Product Name
    price:float = 0.0                                   # Product Price
    url: str = ""                                       # Product URL
    asin: str = ""                                      # ASIN code - Amazon Standard Identification Number - Unique identifier for products on Amazon
    imageUrls: List[str] = field(default_factory=list)  # list of image URLs
    productDetails: dict = field(default_factory=dict)  # Dictonary for product details
    created_at:datetime = field(init=False)                              # Product record creation time
    updated_at:Optional[datetime] = None                                 # Last Product Price Update time

    def __post_init__(self):
        """Post Init Data Cleaning"""
        self.asin =  self.productDetails.get("ASIN", "MISSING ASIN")

        if (self.asin == "MISSING ASIN" or self.asin == "") and self.url != "":
            # Try to extract ASIN from URL if not provided in product details
            self.asin = extract_asin_from_url(self.url)

        object.__setattr__(self, "created_at", datetime.now())