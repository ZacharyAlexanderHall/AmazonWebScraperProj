# config.py

import os

# Default Yahoo SMTP settings
SMTP_SERVER = "smtp.mail.yahoo.com"
SMTP_PORT = 465 # SSL Port

# Default "template" account
DEFAULT_FROM_EMAIL = "WebScraperProj@yahoo.com"

# Temporary password for the "template" account
DEFAULT_EMAIL_PASSWORD = "LetsScrapeAmazon69!"

# Optionally use environment variable for password (safer than hardcoding) - Use later 
# DEFAULT_EMAIL_PASSWORD = os.environ.get("DEFAULT_EMAIL_PASSWORD")