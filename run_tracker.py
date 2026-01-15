"""
Amazon Price Tracker - Entry Point
Run this file to start the application.
"""
import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Now import and run
from WebScraper.cli import main

if __name__ == "__main__":
    main()