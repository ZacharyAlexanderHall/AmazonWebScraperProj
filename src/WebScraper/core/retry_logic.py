import requests
import random
import time

from WebScraper.services.client_metadata import BrowserHeadersMiddleware, UserAgentMiddleware
from WebScraper.core.utilities import logger

browser_headers_middleware = BrowserHeadersMiddleware(num_headers=20)

# Use as needed.
#user_agent_middleware = UserAgentMiddleware(num_user_agents=20)

# Triggers get requests with a specific number of retries.
class RetryLogic:
    """Triggers get requests with a specific number of retries."""
    def __init__(self, retry_limit=5, anti_bot_check=False, use_fake_browser_headers=False):
        self.retry_limit = retry_limit
        self.anti_bot_check = anti_bot_check
        self.use_fake_browser_headers = use_fake_browser_headers

    # Make request to URL and possibly preform the anti-bot check
    def make_request(self, url, method = "GET", **kwargs):
        """Make request to URL and possibly preform the anti-bot check"""
        kwargs.setdefault("allow_redirects", True)

        for attempt in range(self.retry_limit):
            try:
                # NOTE: Had to install the brotli package to account for brotli encoding.
                # Use different Fake Browser Header in each scrape attempt
                headers = kwargs.get("headers", {})
                if self.use_fake_browser_headers:
                    fake_browser_headers = browser_headers_middleware.get_random_brouwer_header()
                    for key, value in fake_browser_headers.items():
                        headers[key] = value

                response = requests.request(
                    method,
                    url, 
                    headers=headers, 
                    **kwargs, 
                    timeout=(10, 30)
                )

                # Check for Successful Status Codes
                if response.status_code in [200, 404]:
                    # Perform Anti-Bot check if enabled.
                    if response.status_code == 200 and self.anti_bot_check:
                        if self._passed_anti_bot_check(response) == False:
                            logger.warning(f"Anti-Bot check failed for {url}")
                            # if not last attempt, wait...
                            if attempt < (self.retry_limit -1):
                                self._wait_before_retry(attempt)
                            continue

                    return True, response
            
                # If we got a bad status code, log it and retry
                logger.warning(f"Attempt {attempt + 1}/{self.retry_limit}: Status {response.status_code}")
                self._wait_before_retry(attempt)

            except Exception as ex:
                print("Error ", ex)

        # If all attempts fail, log and return False
        logger.error(f"All {self.retry_limit} attempts failed for {url}")
        return False, None

    # Simple placeholder logic for anti bot checking. - This currently does not 'actually' check anything
    def _passed_anti_bot_check(self, response):
        """Simple placeholder logic for anti bot checking."""
        if "<title>Robot or human?</title>" in response.text:
            return False
        return True


    def _wait_before_retry(self, attempt):
        """Creates growing delay in between attempts based off current attempt number"""
        # Exponetial backoff in attempts
        # Attempt 0: 1 sec, 1: 2 sec, 2: 4 sec, 3: 8 sec, 4: 16 sec
        base_delay = 2 ^ attempt 

        # Add randomized jitter 
        jitter = random.uniform(-.3, .7)

        # Calculate total delay
        total_delay = base_delay + jitter

        # Cap Max delay at 30 secs
        total_delay = min(total_delay, 30)

        logger.info(
            f"Waiting {total_delay:.1f} seconds before retry - Attempt: {attempt + 1} "
        )

        time.sleep(total_delay)