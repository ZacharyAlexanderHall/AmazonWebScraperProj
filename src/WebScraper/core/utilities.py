import re
import unicodedata
import logging

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
    match = re.search(r"/dp/([A-Z0-9]{10})", url)
    if match:
        return match.group(1)
    else:
        logger.warning(f"ASIN not found in URL: {url}")
        return ""
    
def is_amazon_url(url: str) -> bool:
    """Rejects non-Amazon URLs."""
    if not url.startswith("https://www.amazon.com"):
        logger.warning(f"Non-Amazon URL detected: {url}")
        return False
    return True

def is_email_address(email: str) -> bool:
    """Rejects strings that don't follow standard Email formatting"""
    if not email or not isinstance(email, str):
        return False

    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return bool(re.match(pattern, email))