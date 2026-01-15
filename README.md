# Amazon Price Tracker

A Python-based web scraper that tracks Amazon product prices and sends email alerts when prices drop below your target.

## Features

- 🔍 Scrape Amazon product data (name, price, images, details)
- 💾 Store product history in SQLite database
- 📧 Email alerts via Gmail when prices drop
- ⏰ Scheduled scraping (run every X hours)
- 🎯 Set custom price targets per product

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Gmail API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download credentials as `GmailCredentials.json`
6. Place `GmailCredentials.json` in the project root

### 3. (Optional) Configure ScrapeOps API

For better anti-detection headers:

1. Get free API key from [ScrapeOps](https://scrapeops.io/)
2. Create `.env` file in project root:
```
SCRAPEOPS_API_KEY=your_key_here
```

## Usage

### Add Products to Track
```bash
python run_tracker.py add-url "https://www.amazon.com/dp/PRODUCT_ASIN"
```

### Scrape All Tracked Products
```bash
python run_tracker.py run-scrape
```

### View Tracked Products
```bash
python run_tracker.py show-products
```

### Set Price Alert
```bash
python run_tracker.py add-alert ASIN 29.99 your.email@example.com
```

### View Active Alerts
```bash
python run_tracker.py show-alerts
```

### Run Scheduled Scraping
```bash
# Scrape every 48 hours
python run_tracker.py run-schedule 48
```

## Project Structure
```
amazon-price-tracker/
├── run_tracker.py          # Main entry point
├── requirements.txt        # Dependencies
├── .env                    # API keys (create this)
├── GmailCredentials.json   # Gmail OAuth (create this)
├── data/                   # Database storage
│   └── Amazon_Scraper.db
└── src/WebScraper/
    ├── CLI.py              # CLI logic
    ├── core/               # Scraping & parsing
    ├── data/               # Database models
    └── services/           # Email & metadata
```

## Troubleshooting

**Import Errors**: Make sure you run via `run_tracker.py`, not directly

**Database Not Found**: First run will create it automatically in `data/`

**Gmail Auth Fails**: Delete `token.pickle` and re-authenticate

**Scraping Fails**: Amazon may be blocking - try setting SCRAPEOPS_API_KEY

## Known Limitations

- Only works with Amazon.com (not international sites)
- Requires active internet connection
- Gmail API has daily sending limits (500 emails/day for free tier)

## License

Personal/Educational Use