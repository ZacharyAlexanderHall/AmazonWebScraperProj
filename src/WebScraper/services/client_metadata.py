import random
import requests
import os
from pathlib import Path
from dotenv import load_dotenv
from WebScraper.core.utilities import logger

# Load environment variables from .env
def load_env_file():
    """ Load .env file from proj root or user config directioery"""
    possible_paths = [
        Path.cwd() / ".env", # Current Directory (if placed next to .exe)
        Path(__file__).resolve().parent[3] / ".env", # Dev Mode
        Path.home() / "AmazonPriceTracker" / ".env", # Prod Mode
    ]

    for env_path in possible_paths:
        if env_path.exists():
            load_dotenv(env_path)
            return

# ScrapeOps API Key specific to your account.
SCRAPEOPS_API_KEY = os.getenv("SCRAPEOPS_API_KEY")
if not SCRAPEOPS_API_KEY:
    logger.warning(
        "SCRAPEOPS_API_KEY not set. Using fallback headers only."
        "Set the Key in your .env file for better results"
        )
    
# Uses ScrapeOps Api to get randomly generated list of Browser Headers
class BrowserHeadersMiddleware:
    """Uses Scrape Ops Api to generate Browser Headers, or uses default list taken from ScrapeOps"""
    def __init__(self, num_headers=10):
        self.browser_headers_list = []
        self.scrapeops_api_key = SCRAPEOPS_API_KEY
        self.num_headers = num_headers
        self.get_browser_headers()

    def get_browser_headers(self):
        """Gets list of Browser Headers"""
        response = requests.get(
            url='http://headers.scrapeops.io/v1/browser-headers',
            params={
                'api_key': self.scrapeops_api_key,
                'num_results': self.num_headers},
            timeout=30
        )

        if response.status_code == 200:
            json_response = response.json()
            self.browser_headers_list = json_response.get("result", [])
            self.filter_desktop_only_headers()

            if len(self.browser_headers_list) == 0:
                logger.info("Warning Browser Headers List is empty")
                self.browser_headers_list = self.use_fallback_headers_list()
        else:
            logger.info(f"WARNING: ScrapeOps Status Code: {response.status_code}, Error Message: {response.text}")
            self.browser_headers_list = self.use_fallback_headers_list()

    def use_fallback_headers_list(self):
        """Generic List of Headers from ScrapeOps Site"""
        return [
            {'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"', 'upgrade-insecure-requests': '1', 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7', 'sec-fetch-site': 'same-site', 'sec-fetch-mode': 'navigate', 'sec-fetch-user': '?1', 'sec-fetch-dest': 'document', 'accept-encoding': 'gzip, deflate, br, zstd', 'accept-language': 'en-US'},
            {'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"', 'upgrade-insecure-requests': '1', 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7', 'sec-fetch-site': 'same-site', 'sec-fetch-mode': 'navigate', 'sec-fetch-user': '?1', 'sec-fetch-dest': 'document', 'accept-encoding': 'gzip, deflate, br, zstd', 'accept-language': 'en-US'},
            {'sec-ch-ua': '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Linux"', 'upgrade-insecure-requests': '1', 'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7', 'sec-fetch-site': 'same-site', 'sec-fetch-mode': 'navigate', 'sec-fetch-user': '?1', 'sec-fetch-dest': 'document', 'accept-encoding': 'gzip, deflate, br, zstd', 'accept-language': 'en-US'},
            {'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"macOS"', 'upgrade-insecure-requests': '1', 'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7', 'sec-fetch-site': 'same-site', 'sec-fetch-mode': 'navigate', 'sec-fetch-user': '?1', 'sec-fetch-dest': 'document', 'accept-encoding': 'gzip, deflate, br, zstd', 'accept-language': 'en-US'},
            {'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"macOS"', 'upgrade-insecure-requests': '1', 'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7', 'sec-fetch-site': 'same-site', 'sec-fetch-mode': 'navigate', 'sec-fetch-user': '?1', 'sec-fetch-dest': 'document', 'accept-encoding': 'gzip, deflate, br, zstd', 'accept-language': 'en-US', 'dnt': '1'},
        ]

    def get_random_brouwer_header(self):
        """Return a Random Header from Browser Headers List"""
        header = random.choice(self.browser_headers_list)
        return header
    
    def filter_desktop_only_headers(self):
        """Filters out Mobile Headers from Browser Headers List"""
        desktop_headers = []
        for header in self.browser_headers_list:
            user_agent = header.get("user-agent", "").lower()
            if "mobile" in user_agent or "iphone" in user_agent or "android" in user_agent:
                continue
            desktop_headers.append(header)
        
        self.browser_headers_list = desktop_headers

# uses ScrapeOps Api to get randomly generated list of User_Agents:
class UserAgentMiddleware:
    """Use ScrapeOps Api to Generate User Agents, or else fallback on generic list"""
    def __init__(self, num_user_agents=10):
        self.user_agents_list = []
        self.scrapeops_api_key = SCRAPEOPS_API_KEY
        self.num_user_agents = num_user_agents
        self.get_user_agents()

    def get_user_agents(self):
        """Use ScrapeOps Api to Generate Browser Headers"""
        response = requests.get(
            url='http://headers.scrapeops.io/v1/browser-headers',
            params={
                'api_key': self.scrapeops_api_key,
                'num_results': self.num_user_agents
                },
            timeout=60
        )

        if response.status_code == 200:
            json_response = response.json()
            response_list = json_response.get("result", [])

            for response in response_list:
                self.user_agents_list.append(response.get("user-agent"))

            if len(self.user_agents_list) == 0:
                logger.info("Warning: ScrapeOps user-agents list was empty")
        else:
            logger.info(f"Warning ScrapeOps Status Code: {response.status_code}, error Message: {response.text}")
            self.user_agents_list = self.use_fallback_user_agent_list

    def use_fallback_user_agent_list(self):
        """Generic List Copy pasted from ScrapeOps Site"""
        logger.info("Using Fallback User Agent List")
        return [
            "Dalvik/2.1.0 (Linux; U; Android 9; FIG-TL10 Build/HUAWEIFIG-TL10)",
            "Mozilla/5.0 (Linux; Android 10; SM-A315G) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.66 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 6.0; VFD 700 Build/MRA58K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.91 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 9; JAT-LX1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.101 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 11; Mi 9 SE) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.85 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 10; VOG-L29) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.80 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 8.0.0; SM-A520W) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.105 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 10; ONEPLUS A5000) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.101 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 10; Nokia 6.2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.96 Mobile Safari/537.36",
        ]

    def get_random_user_agent(self):
        """Returns a Randomly select user Agent from User Agents List"""
        return random.choice(self.user_agents_list)