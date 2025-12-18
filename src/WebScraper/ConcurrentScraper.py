"""
import concurrent
import concurrent.futures

#from queue import Queue
from WebScraper.Parser import scrape_page, data_pipeline

# Scraper Worker Fucntion
def scrape_worker():
    # While Loop keeps scrapers running concurrently until the list empty throws exception, resulting in return.
    while True:

        url = url_queue.get()

        if url is None:
            url_queue.task_done()
            break

        try:
            scrape_page(url)
        finally:
            url_queue.task_done()

# uses a thread pool executor to start concurrent scrapes.
def start_concurrent_scrape(num_threads=5):
    #uses a thread pool executor to start concurrent scrapes.
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:

        # Start worker threads
        for _ in range(num_threads):
            executor.submit(scrape_worker)

        # IMPORTANT: Add sentinels BEFORE join
        # So workers can exit cleanly after finishing URLs.
        for _ in range(num_threads):
            url_queue.put(None)

        # Wait for all tasks AND sentinels to be processed
        url_queue.join()
"""