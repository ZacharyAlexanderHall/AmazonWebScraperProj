import os
import pickle
import base64
from pathlib import Path
from email.message import EmailMessage
# Gmail API utils
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Product Info
from WebScraper.Product import Product

# Scope only allowing user to send emails
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

# Creates path to token.pickle and credentials
THIS_FILE = Path(__file__).resolve()
PROJ_ROOT = THIS_FILE.parents[2] # Reachers Project Folder level
TOKEN_PATH = os.path.join(PROJ_ROOT, "token.pickle")
CREDS_PATH = os.path.join(PROJ_ROOT, "GmailCredentials.json")

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

        # if no valid credentials exist, let user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # save credentials for next run
            with open(TOKEN_PATH, "wb") as token:
                pickle.dump(creds, token)
            
        return build("gmail", "v1", credentials=creds)

    def send_email(self, target:str, product: Product) -> None:
        """Send an email with product information to target email address."""
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