## Amazon Web Scraper 
A desktop Python application that monitors Amazon products for price changes and sends email notifications to users. Designed as a portfolio project, it demonstrates web scraping, automation, SQLite database usage, and integration with the Gmail API for professional email alerts.

## Features
- Product Monitoring: Tracks Amazon products over time
- Email Notifications: HTML formatted email alerts
- Robust Scraping: Uses randomized browser headers with selector fallbacks in order to maintain future reliabilty
- Local Storage: Uses SQLite DB for product Data

## Tech Stack
- Python 3.13
- Requests & BeautifulSoup
- SQLite: Persistent Data Storage
- Gmail API: HTML Formatted email alerts
- Pickle & OAuth2
- Logging and Config Management