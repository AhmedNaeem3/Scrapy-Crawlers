import logging
import re
from typing import Iterable, Iterator
from math import ceil
import scrapy
from scrapy.http import Request, TextResponse

from Aligro.StoreScrapers.items import AligroProduct, ProductImage

logger = logging.getLogger(__name__)


class AligroProductScraper(scrapy.Spider):
    name = "aligro_product_scraper"
    CATEGORY_URL = "{url}?article_filter%5BpaginationItems%5D=192&page={page_no}"
    HEADERS = {
        "X-Requested-With": "XMLHttpRequest",
    }

    def parse(self, response, **kwargs) -> Iterable[Request]:
        """
        :param response:
        :param kwargs:

        Parse the sub category page to extract the breadcrumbs from which we are extracting the category lists.
        Start yielding requests for each page of this sub category

        :return:
        """

        page_no = 1
        date_sale_start = None
        date_sale_end = None
        breadcrumbs = (
            response.css("nav#navBreadcrumb li.breadcrumb-item")
            .xpath("normalize-space()")
            .getall()
        )
        if "Aktionen von" in breadcrumbs[0]:
            # This check is in place to ensure the keyword is in
            # place before we start getting the sale dates.
            breadcrumb = breadcrumbs[0].replace("Aktionen von ", "")
            date_sale_start, date_sale_end = re.split(r"\s?bis\s?", breadcrumb)

        if len(breadcrumbs) > 2:
            product_category = breadcrumbs[1]
            subcategory1 = breadcrumbs[2]
        else:
            product_category = breadcrumbs[1]
            subcategory1 = None

        yield scrapy.Request(
            self.CATEGORY_URL.format(url=response.url, page_no=page_no),
            callback=self.parse_category_page,
            headers=self.HEADERS,
            meta=dict(
                date_sale_start=date_sale_start,
                date_sale_end=date_sale_end,
                product_category=product_category,
                subcategory1=subcategory1,
                page_no=page_no,
                url=response.url,
            ),
        )

    def parse_category_page(
        self, response: TextResponse
    ) -> Iterable[Request] | Iterator[AligroProduct]:
        """
        :param response:

        - We get a JSON response from API.
        - From there we extract the pagination details.
        - Call the `parse_products` function that will parse through the category response to extract the products.
        - Yield requests for the next pages.

        :return:
        """
        json_response = response.json()
        if not isinstance(json_response, dict):
            logger.error(f"Product Response is invalid for url {response.url}")
            return

        pagination = json_response["pagination"]
        items_per_page = pagination.get("items_per_page")
        total_items = pagination.get("total_items")
        all_items = pagination["items"]
        if not all_items:
            logger.error(f"Items is null or empty list for url {response.url}")
            return

        yield from self.parse_products(all_items, **response.meta)
        total_pages = ceil(int(total_items) / int(items_per_page))
        if total_pages == 1:
            logger.info(f"Only 1 page of results found for {response.url}")

            return
        for page_no in range(2, total_pages):
            url = self.CATEGORY_URL.format(url=response.meta["url"], page_no=page_no)
            logger.info(f"Iterating over {url}")
            response.meta["page_no"] = page_no
            yield scrapy.Request(
                url=url,
                callback=self.parse_category_page,
                headers=self.HEADERS,
                meta=response.meta,
            )

    def parse_products(self, products, **kwargs) -> Iterable[AligroProduct]:
        """
        :param products:
        :param kwargs:

        Parse the products from the category page and yield the product items

        :return:
        """
        logger.info(f"Total Products: {len(products)}")
        for product in products:
            product_category = (
                product.get("article", {})
                .get("articleGroup", {})
                .get("translations", {})
                .get("de", {})
                .get("wording")
            )
            subcategory1 = kwargs["subcategory1"]
            subcategory2 = None
            if subcategory1 is None:
                subcategory1 = product_category
            else:
                subcategory2 = product_category

            brand = product.get("translations", {}).get("de", {}).get("brand")
            product_name = (
                product.get("translations", {}).get("de", {}).get("advertisingText")
            )
            origin = product.get("translations", {}).get("de", {}).get("origin")
            additional_designation = (
                product.get("translations", {})
                .get("de", {})
                .get("additionalDesignation")
            )

            article_pricing_dict = product.get("articleDetailPrices", [{}])
            price_with_vat = None
            professional_price = None
            unit = (
                product.get("quantityUnitBase", {})
                .get("translations", {})
                .get("de", {})
                .get("singular")
            )
            package_size = (
                product.get("translations", {}).get("de", {}).get("quantityLabel")
            )
            if not package_size:
                package_size = product.get("quantityWording")

            if article_pricing_dict:
                article_pricing_dict = article_pricing_dict[0]
                discount_percentage = article_pricing_dict.get("discountRatePro")
                if discount_percentage:
                    discount_percentage = f"{int(discount_percentage * 100)}%"
                price_with_vat = dict(
                    sale_price_with_vat=format(
                        article_pricing_dict.get("salesPriceTTC"), ".2f"
                    ),
                    discount_price_with_vat=format(
                        article_pricing_dict.get("discountPriceTTC"), ".2f"
                    ),
                    discount_percentage=discount_percentage,
                )

                discount_percentage = article_pricing_dict.get("discountRatePrivate")
                if discount_percentage:
                    discount_percentage = f"{int(discount_percentage * 100)}%"

                professional_price = dict(
                    professional_sale_price=format(
                        article_pricing_dict.get("salesPriceHT"), ".2f"
                    ),
                    professional_discount_price=format(
                        article_pricing_dict.get("discountPriceHT"), ".2f"
                    ),
                    discount_percentage=discount_percentage,
                )
                unit_price = article_pricing_dict.get("discountPriceHT")

                if (
                    unit_price
                    and format(unit_price, ".2f")
                    != professional_price["professional_discount_price"]
                ):
                    unit_price = format(unit_price, ".2f")
                    professional_price["price_per_unit"] = f"{unit_price} / {unit}"

            available_locations = product.get("availabilityLabel")
            if brand:
                product_name = f"{brand} {product_name}"
            if origin:
                product_name += f", {origin}"
            if additional_designation:
                product_name += f", {additional_designation}"

            image_url = product.get("images", {}).get("main")
            product_url = product.get("href", {}).get("self")

            yield AligroProduct(
                sku=product["sKU"],
                date_sale_start=kwargs["date_sale_start"],
                date_sale_end=kwargs["date_sale_end"],
                product_category=kwargs["product_category"],
                subcategory1=subcategory1,
                subcategory2=subcategory2,
                image_urls=[image_url],
                product_name=product_name,
                product_url=product_url,
                package_size=package_size,
                price_with_vat=price_with_vat,
                professional_price=professional_price,
                available_locations=available_locations,
            )
            yield scrapy.Request(
                image_url,
                meta={"sku": product["sKU"], "product_name": product_name},
                callback=self.parse_product_image,
            )

    def parse_product_image(self, response) -> Iterable[ProductImage]:
        """
        :param response:
        :return:
        """
        image_id = response.url.split("/")[-1]
        image_type = re.search(r"\.(jpg|jpeg|png)$", image_id)
        if not image_type:
            raise KeyError("Unable to find type of the image!")

        image_type = image_type.group(1)
        image_id = image_id.replace(f".{image_type}", "")
        yield ProductImage(
            image_url=response.url,
            image_id=image_id,
            image_type=image_type,
            sku=response.meta.get("sku"),
            product_name=response.meta.get("product_name"),
            product_image_content=response.body,
        )
