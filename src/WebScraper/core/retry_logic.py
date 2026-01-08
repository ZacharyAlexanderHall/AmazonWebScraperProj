import requests

from WebScraper.services.client_metadata import BrowserHeadersMiddleware, UserAgentMiddleware

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

        # NOTE: Had to install the brotli package to account for brotli encoding.
        # Use Fake Browser Headers
        headers = kwargs.get("headers", {})
        if self.use_fake_browser_headers:
            fake_browser_headers = browser_headers_middleware.get_random_brouwer_header()
            for key, value in fake_browser_headers.items():
                headers[key] = value

        # Use Fake User Agents - Disabled in favor of Browser Headers
        #headers = kwargs.get("headers", {})
        #if self.use_fake_browser_headers:
        #    headers["User-Agent"] = user_agent_middleware.get_random_user_agent()

        for _ in range(self.retry_limit):
            try:
                response = requests.request(method, url, headers=headers, **kwargs, timeout=(10, 30))
                if response.status_code in [200, 404]:
                    if response.status_code == 200 and self.anti_bot_check:
                        if self.passed_anti_bot_check(response) == False:
                            return False, response
                    return True, response
            except Exception as ex:
                print("Error ", ex)
        return False, None

    # Simple placeholder logic for anti bot checking.
    def passed_anti_bot_check(self, response):
        """Simple placeholder logic for anti bot checking."""
        if "<title>Robot or human?</title>" in response.text:
            return False
        return True
