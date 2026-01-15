from setuptools import setup, find_packages

setup(
    name="amazon-price-tracker",
    version="1.0.0",
    description="Track Amazon product prices and get email alerts",
    author="Your Name",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        'requests>=2.31.0',
        'beautifulsoup4>=4.12.2',
        'brotli>=1.1.0',
        'python-dotenv>=1.0.0',
        'google-auth-oauthlib>=1.2.0',
        'google-api-python-client>=2.108.0',
    ],
    entry_points={
    'console_scripts': [
        'amazon-tracker=WebScraper.cli:main',  # ← Should reference CLI.py
    ],
    },
    python_requires='>=3.9',
)