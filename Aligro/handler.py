import logging
import os
import subprocess
from scrapy import cmdline

logger = logging.getLogger(__name__)


def lambda_handler(event, context):
    # The calling methods are different because with cmdline.execute,
    # lambda generates runtime error at the end of the execution
    # because of Scrapy Reactor.
    scraper_name = event.get("scraper_name")
    if not scraper_name:
        scraper_name = os.environ.get("scraper_name")
    if not scraper_name:
        logger.error("Please provide scraper_name to run the spider for!")
    if os.environ.get("DEBUG_MODE"):
        cmdline.execute(f"scrapy crawl {scraper_name}".split())
    else:
        subprocess.call(["scrapy", "crawl", scraper_name])
    print("Completed Scraping..")
