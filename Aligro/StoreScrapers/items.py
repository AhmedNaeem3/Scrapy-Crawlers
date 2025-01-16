import scrapy


class ProductImage(scrapy.Item):
    image_url = scrapy.Field()
    image_id = scrapy.Field()
    image_type = scrapy.Field()
    sku = scrapy.Field()
    product_name = scrapy.Field()
    product_image_content = scrapy.Field()


class AligroProduct(scrapy.Item):
    sku = scrapy.Field()
    date_sale_start = scrapy.Field()
    date_sale_end = scrapy.Field()
    product_category = scrapy.Field()
    subcategory1 = scrapy.Field()
    subcategory2 = scrapy.Field()
    image_urls = scrapy.Field()
    product_name = scrapy.Field()
    product_url = scrapy.Field()
    package_size = scrapy.Field()
    price_with_vat = scrapy.Field()
    professional_price = scrapy.Field()
    available_locations = scrapy.Field()
