import logging
from typing import Iterable

import scrapy

from Aligro.StoreScrapers.spiders.aligro.product_scraper import AligroProductScraper
from scrapy.http import Request, Response

logger = logging.getLogger(__name__)


class AligroCategoryScraper(scrapy.Spider):
    name = "aligro_category_scraper"
    domain_name = "aligro"
    start_urls = ["https://www.aligro.ch/de/"]
    product_scraper = AligroProductScraper()
    categories_to_scrape = [
        "Frischprodukte",
        "Wein und Getränke",
        "Allgemeine Lebensmittel",
        "Non-Food",
    ]

    def parse(self, response: Response, **kwargs) -> Iterable[Request]:
        categories = response.css("ul.navbar-nav li.dropdown")
        for item in categories:  # type: ignore
            category_name = (
                item.css("a.dropdown-toggle").xpath("normalize-space()").get()
            )
            if category_name in self.categories_to_scrape:
                sub_categories = item.css("ul.dropdown-menu li")
                for sub_category in sub_categories:
                    sub_category_url = sub_category.css("a::attr(href)").get()
                    logger.info(f"Iterating over url={sub_category_url}")
                    yield scrapy.Request(
                        sub_category_url,
                        callback=self.product_scraper.parse,
                    )
