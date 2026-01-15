import re
import unicodedata
import logging

from urllib.parse import urlparse, parse_qs

# Create logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("WebScraper")

# Unicode BiDi control characters (explicit list for clarity and safety)
_BIDI_CONTROLS = {
    "\u061C",  # ARABIC LETTER MARK
    "\u200E",  # LEFT-TO-RIGHT MARK
    "\u200F",  # RIGHT-TO-LEFT MARK
    "\u202A",  # LEFT-TO-RIGHT EMBEDDING
    "\u202B",  # RIGHT-TO-LEFT EMBEDDING
    "\u202C",  # POP DIRECTIONAL FORMATTING
    "\u202D",  # LEFT-TO-RIGHT OVERRIDE
    "\u202E",  # RIGHT-TO-LEFT OVERRIDE
    "\u2066",  # LEFT-TO-RIGHT ISOLATE
    "\u2067",  # RIGHT-TO-LEFT ISOLATE
    "\u2068",  # FIRST STRONG ISOLATE
    "\u2069",  # POP DIRECTIONAL ISOLATE
}

ASIN_REGEX = re.compile(r'[A-Z0-9]{10}')

PATH_PATTERNS = [
    re.compile(r'/dp/([A-Z0-9]{10})', re.IGNORECASE),
    re.compile(r'/gp/product/([A-Z0-9]{10})', re.IGNORECASE),
    re.compile(r'/gp/aw/d/([A-Z0-9]{10})', re.IGNORECASE),
    re.compile(r'/product/([A-Z0-9]{10})', re.IGNORECASE),
]

AMAZON_DOMAINS = {
    "amazon.com",
    "www.amazon.com",
}

def clean_text(s: str) -> str:
    """Cleans text by removing BiDi control characters and normalizing whitespace."""
    if not s:
        return s

    # Remove BiDi control characters
    s = "".join(ch for ch in s if ch not in _BIDI_CONTROLS)

    # Normalize unicode to collapse odd space characters
    s = unicodedata.normalize("NFKC", s)

    # Collapse all runs of whitespace into a single space and trim
    s = re.sub(r"\s+", " ", s).strip()

    return s

def extract_asin_from_url(url: str) -> str:
    """Extracts the ASIN from an Amazon product URL via Regex."""
    if not url:
        return None
    
    parsed = urlparse(url)
    path = parsed.path 
    
    # asin via url path
    for pattern in PATH_PATTERNS:
        match = pattern.search(path)
        if match:
                return match.group(1).upper() # for ASIN consistency
        
    # asin via query string, fallback
    query_params = parse_qs(parsed.query)
    for key in ("asin", "ASIN"):
        if key in query_params:
            value = query_params[key][0].upper()
            if ASIN_REGEX.fullmatch(value):
                return value
    
def standardize_product_url(asin: str) -> str:
    if not asin:
        return None
    return f"https://www.amazon.com/dp/{asin}"
    
def is_amazon_url(url: str) -> bool:
    """Rejects non-Amazon URLs."""
    if not url:
        return False

    url = url.strip('"').strip() # remove optional quotes from arguement string
    parsed = urlparse(url)

    if parsed.scheme not in {"http", "https"}:
        return False

    if parsed.netloc.lower() not in AMAZON_DOMAINS:
        return False

    return True

def is_email_address(email: str) -> bool:
    """Rejects strings that don't follow standard Email formatting"""
    if not email or not isinstance(email, str):
        return False

    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return bool(re.match(pattern, email))