from WebScraper.core.utilities import logger, is_amazon_url
from WebScraper.core.parser import scrape_page
from WebScraper.Widgets import TextHandler

from tkinter import *
from tkinter import ttk, scrolledtext
import sv_ttk
 
# Url of product we are scraping for - using various URL types for testing.
url_list  = [
    "https://www.amazon.com/Nongshim-Ramyun-Black-Premium-Broth/dp/B0CHRNR43T/",
    "https://www.amazon.com/Jim-Dunlop-Tortex-Standard-1-0MM/dp/B0002D0CFS/",
    "https://www.amazon.com/adidas-Unisex-Samba-Sneaker-White/dp/B0CKMM41FY/",
    "https://www.amazon.com/Mario-Badescu-Drying-Lotion-fl/dp/B0017SWIU4/",
    "https://www.amazon.com/Fender-Stratocaster-Electric-Beginner-Warranty/dp/B0DTC2H4K2/ref=sr_1_11?crid=3NXKE6ILJVE5R&dib=eyJ2IjoiMSJ9.qE6vPozUOUXSHgTwdwq1Cu4CQqc1zmHXgsTgimN63bRACmnWJtKMWg5oFvBTwL6nJW8cUx_HJzGUlOsFGKs1zxrDneSjX-zc8BOnP5YHyRgqU0l3BQSLa4GmCc-Kau1qMnrnran88uPnTN1kqNY_6TAapcYdY1fJubSRFtYhp4EqYeq90mujwvk2wYYDW9Cxt-CLCRadM5Bcmevbkk9OLJm9IpBfq69kRN3qz24LeQkYi17oYKxd5cF3HcwAlOdwwR2BzXoJS7LBLebv5pljdcQdurLJkwGpp4uZCawEDZs.am-y1TpiYflSvz18V9LqtvnMWQyb4Yk0Szq7EtZs6vA&dib_tag=se&keywords=fender+stratocaster&qid=1765486222&sprefix=fender+stratocas%2Caps%2C202&sr=8-11",
    "https://www.google.com/search?q=if+i+build+a+iphone+app&rlz=1C1CHBF_enUS946US946&oq=if+i+build+a+iphone+app&gs_lcrp=EgZjaHJvbWUyBggAEEUYOTIICAEQABgWGB4yDQgCEAAYhgMYgAQYigUyDQgDEAAYhgMYgAQYigUyBwgEEAAY7wUyBwgFEAAY7wUyBwgGEAAY7wUyBwgHEAAY7wXSAQg5MTEwajBqN6gCALACAA&sourceid=chrome&ie=UTF-8"
]

# Main Method
if __name__ == "__main__":
    logger.info("Starting Scraper...")
    # Create URL Queue and add URLs - useo for threading.
    #url_queue = Queue()\
    #for url in url_list:
    #    url_queue.put(url)

    #NOTE: disable url_list removal in scrape_page to avoid threading issues.
    #start_concurrent_scrape(num_threads=5)

    for url in url_list:
        logger.info(f"Attempting to Scrape URL: {url}")
        if not is_amazon_url(url):
            logger.error(f"URL is not a valid Amazon URL: {url}")
            continue
        scrape_page(url)

"""
# attemping to use tkinter to build UI
def scrape_clicked():
        for url in url_list:

            if not is_amazon_url(url):
                logger.error(f"URL is not a valid Amazon URL: {url}")
                continue

            logger.info(f"Attempting to Scrape URL: {url}")
            scrape_page(url)

def add_url(url_text: Entry, url_box: Listbox):
    url = url_text.get()
     
    if url:
        url_list.append(url)
        url_box.insert(END, url)
        url_text.delete(0, END)

if __name__ == "__main__":
    root = Tk()
    root.title("Amazon Web Scraper")
    root.geometry("200x100")

    # Scrape All and Url Box
    scrape_button = ttk.Button(root, text="Scrape All", command=scrape_clicked)

    url_box = Listbox(root, width=50)
    for url in url_list:
        url_box.insert(END, url)


    # Add Url Button WIdgets
    url_lbl = ttk.Label(root, text="Add Urls to List")
    url_text = Entry(root)
    add_url_button = ttk.Button(root, text="Add Url", command=add_url(url_text, url_box))

    # Create Scrolled Text widget to display logs
    log_text = scrolledtext.ScrolledText(root, state="disabled")
    text_handler = TextHandler(log_text)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    text_handler.setFormatter(formatter)
    logger.addHandler(text_handler)
    log_text.insert(END, logger)#

    # row 0
    url_lbl.grid(row=0, column=0)
    url_text.grid(row=0, column=1)
    add_url_button.grid(row=0, column=2)

    # row 1
    scrape_button.grid(row=1, column=1)

    # row 2
    url_box.grid(row=2, column= 0)

    # row 3
    log_text.grid(row=2, column=1)

    sv_ttk.set_theme("dark")
    root.mainloop()
"""