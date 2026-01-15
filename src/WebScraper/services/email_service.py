import os
import pickle
import base64
from pathlib import Path
from email.message import EmailMessage
from typing import Optional

# Gmail API utils
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError

# Product Info
from WebScraper.data.product import Product
from WebScraper.core.utilities import logger

# Scope only allowing user to send emails
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def get_credentials_directory():
    """Get or create the credentials directory."""
    # Check multiple possible locations
    possible_locations = [
        Path.cwd(),  # Current directory (next to .exe)
        Path(__file__).resolve().parents[3],  # Development mode
        Path.home() / "AmazonPriceTracker",  # Production mode
    ]
        
    # Return first location that has GmailCredentials.json
    for location in possible_locations:
        if (location / "GmailCredentials.json").exists():
            return location
        
    # If not found anywhere, use production folder as default
    creds_dir = Path.home() / "AmazonPriceTracker"
    creds_dir.mkdir(parents=True, exist_ok=True)
    return creds_dir
    
CREDS_ROOT = get_credentials_directory()
TOKEN_PATH = os.path.join(CREDS_ROOT, "token.pickle")
CREDS_PATH = os.path.join(CREDS_ROOT, "GmailCredentials.json")

class EmailService:
    def __init__(self):
        self.service = self._gmail_authenticate()
        
    def _gmail_authenticate(self):
        creds = None

        # token.pickle stores user access / refresh tokens
        # Created automatically when the authorization flow completes the first time
        if os.path.exists(TOKEN_PATH):
            with open(TOKEN_PATH, "rb") as token:
                creds = pickle.load(token)

        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except RefreshError:
                logger.warning(f"Gmail token refresh failed. Re-authenticating user...")
                creds = None

        # if no valid credentials exist, let user log in
        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

            # save credentials for next run
            with open(TOKEN_PATH, "wb") as token:
                pickle.dump(creds, token)
            
        return build("gmail", "v1", credentials=creds, cache_discovery=False)

    def send_price_alert(self, target_email:str, product: Product, target_price: float, old_price: Optional[float]) -> bool:
        """
        Send price alert email when product drops below target price.
        
        Args:
            target_email: Recipient email address
            product: Product object with current details
            target_price: The alert threshold that was triggered
            old_price: Previous price (if available)
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        message = EmailMessage()
        message["To"] = target_email
        message["From"] = "me" # Stand Gmail API Practice
        message["Subject"] = f"Price Alert for Product: {product.asin} - {product.name[:10]}..."

        html_body = self._build_notification_html_body(product, target_price, old_price)

        # add HTML alternative for formatting
        message.add_alternative(html_body, subtype="html")

        # Encode for Gmail API
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # Send the email
        try:
            self.service.users().messages().send(
                userId="me",
                body={"raw": encoded_message}
            ).execute()
            logger.info(f"Price alert email sent to {target_email} for product {product.asin}")
            return True
        except Exception as e:
            logger.info(f"Failed to send price alert email via Gmail API: {e}")
            return False

    def _build_notification_html_body(self, product: Product, target_price: float, old_price: Optional[float]) -> str:
        # Calculate savings if old price available
        savings_text = ""
        if old_price and old_price > product.price:
            savings = old_price - product.price
            savings_percent = (savings / old_price) * 100
            savings_text = f"""
            <p style="background-color: #d4edda; padding: 15px; border-radius: 5px; border-left: 4px solid #28a745;">
                <strong>💰 Savings:</strong> ${savings:.2f} ({savings_percent:.1f}% off)<br>
                <strong>Was:</strong> <span style="text-decoration: line-through;">${old_price:.2f}</span><br>
                <strong>Now:</strong> <span style="color: #28a745; font-size: 1.2em; font-weight: bold;">${product.price:.2f}</span>
            </p>
            """
        
        # Build HTML body
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 10px;">
                    🎉 Price Drop Alert!
                </h2>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">{product.name}</h3>
                    <p><strong>ASIN:</strong> {product.asin}</p>
                    <a href="{product.url}"> 🛒 View on Amazon</a>
                </div>
                
                {savings_text}
                
                <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107; margin: 20px 0;">
                    <p style="margin: 0;">
                        <strong>✅ Your target price:</strong> ${target_price:.2f}<br>
                        <strong>📉 Current price:</strong> <span style="color: #28a745; font-weight: bold;">${product.price:.2f}</span>
                    </p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{product.url}" 
                       style="background-color: #ff9900; color: white; padding: 15px 30px; 
                              text-decoration: none; border-radius: 5px; font-weight: bold; 
                              display: inline-block;">
                        🛒 View on Amazon
                    </a>
                </div>
        """

        # Add product images if available
        if product.imageUrls:
            html_body += """
            <div style="margin: 20px 0;">
                <h4>Product Images:</h4>
                <div style="display: flex; gap: 10px; flex-wrap: wrap;">
            """
            for url in product.imageUrls[:5]:  # Max 3 images
                html_body += f'<img src="{url}" style="max-width: 180px; border: 1px solid #ddd; border-radius: 5px;" />'
            html_body += "</div></div>"

        html_body += """
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                <p style="color: #666; font-size: 0.9em;">
                    This is an automated alert from your Amazon Price Tracker.<br>
                    Prices may change after this alert is sent.
                </p>
            </div>
        </body>
        </html>
        """

        return html_body

# ============================================================================
# Legacy Email Methods
# ============================================================================
    def send_email(self, target:str, product: Product) -> None:
        """
        Send an email with product information to target email address. - (Legacy Method)
        """
        message = EmailMessage()
        message["To"] = target
        message["From"] = "me" # Stand Gmail API Practice
        message["Subject"] = f"Notification for Product: {product.asin} - {product.name[:10]}..."
    
        # Build HTML body
        html_body = self._build_html_body(product)

        # add HTML alternative for formatting
        message.add_alternative(html_body, subtype="html")

        # Encode for Gmail API
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # Send the email
        # pylint: disable=no-member 
        try:
            self.service.users().messages().send(
                userId="me",
                body={"raw": encoded_message}
            ).execute()
        except Exception as e:
            raise RuntimeError(f"Failed to send email via Gmail API: {e}")

    def _build_html_body(self, product: Product) -> str:
        """Builds the HTML body of the email with product information."""
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.5;">
            <h2 style="color: #1a73e8;">Product Alert: {product.name}</h2>
            <p><strong>ASIN:</strong> {product.asin}</p>
            <p><strong>Price:</strong> ${product.price:.2f}</p>
            <p><a href="{product.url}">View Product on Amazon</a></p>
        """

        # Optional: add product images if any
        if product.imageUrls:
            html_body += "<p><strong>Images:</strong></p>"
            for url in product.imageUrls:
                html_body += f'<img src="{url}" style="max-width:200px; margin:5px;" />'

        # Optional: add productDetails table
        if product.productDetails:
            html_body += "<h3>Product Details</h3>"
            html_body += """
            <table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse;">
                <tr style="background-color:#f2f2f2;">
                    <th>Attribute</th>
                    <th>Value</th>
                </tr>
            """
            for key, value in product.productDetails.items():
                html_body += f"""
                <tr>
                    <td>{key}</td>
                    <td>{value}</td>
                </tr>
                """
            html_body += "</table>"    

        html_body += """
        </body>
        </html>
        """
        return html_body