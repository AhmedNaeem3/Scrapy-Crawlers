import html
import unicodedata
import pytz
import json
import os
from datetime import datetime
from io import BytesIO

import boto3  # type: ignore

from Aligro.StoreScrapers.items import ProductImage

SCRAPE_DATE_TIME = datetime.now(tz=pytz.utc).strftime("%d%m%Y_%H%M")


class ValidatorPipeline:
    """
    This pipeline is used to validate the items before they are saved to S3.
    """

    def process_item(self, item, spider):
        for key in list(item.keys()):
            if item[key] and isinstance(item[key], str):
                item[key] = html.unescape(item[key])
                item[key] = unicodedata.normalize("NFKD", item[key])
        return item


class ProductImageUploaderPipeline:
    """
    This pipeline is used to upload the images to S3.
    """

    def __init__(self):
        self.s3_client = boto3.client("s3")
        self.bucket_name = os.environ.get("AWS_BUCKET_NAME")

    def process_item(self, item: ProductImage, spider):
        if not isinstance(item, ProductImage):
            return item

        folder_prefix = (
            f"/{spider.folder_prefix}" if hasattr(spider, "folder_prefix") else ""
        )
        if os.environ.get("DEBUG_MODE"):
            os.makedirs(
                f"product_data/{spider.domain_name}/"
                f"{SCRAPE_DATE_TIME}{folder_prefix}/{item['sku']}",
                exist_ok=True,
            )
            with open(
                f"product_data/{spider.domain_name}/{SCRAPE_DATE_TIME}{folder_prefix}/"
                f"{item['sku']}/{item['image_id']}.{item['image_type']}",
                "wb",
            ) as f:
                f.write(item["product_image_content"])
            return item

        img = BytesIO(item["product_image_content"])
        file_name = (
            f"{spider.domain_name}/{SCRAPE_DATE_TIME}{folder_prefix}/"
            f"{item['sku']}/{item['image_id']}.{item['image_type']}"
        )
        spider.logger.info(f"saving image with name {file_name}")
        self.s3_client.upload_fileobj(img, self.bucket_name, file_name)
        item.pop("product_image_content")
        return item


class UploadToS3Pipeline:
    """
    This pipeline is used to upload the items to S3.
    """

    def __init__(self):
        self.s3_client = boto3.client("s3")
        self.bucket_name = os.environ.get("AWS_BUCKET_NAME")

    def process_item(self, item, spider):
        if isinstance(item, ProductImage):
            return item

        folder_prefix = (
            f"/{spider.folder_prefix}" if hasattr(spider, "folder_prefix") else ""
        )
        json_object = dict(item)
        if os.environ.get("DEBUG_MODE"):
            os.makedirs(
                f"product_data/{spider.domain_name}/"
                f"{SCRAPE_DATE_TIME}{folder_prefix}/{item['sku']}",
                exist_ok=True,
            )
            with open(
                f"product_data/{spider.domain_name}/"
                f"{SCRAPE_DATE_TIME}{folder_prefix}/{item['sku']}/product.json",
                "w+",
            ) as f:
                f.write(json.dumps(json_object, ensure_ascii=False))
            return item

        self.s3_client.put_object(
            Body=json.dumps(json_object, ensure_ascii=False),
            Bucket=self.bucket_name,
            Key=f"{spider.domain_name}/{SCRAPE_DATE_TIME}{folder_prefix}/{item['sku']}/product.json",
        )
        spider.logger.info(f"Saving Product {item['sku']}")

        return item
