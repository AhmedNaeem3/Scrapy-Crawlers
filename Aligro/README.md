Project Description
This Scrapy project scrapes product data from specified categories and subcategories of an e-commerce website. The scraped data includes detailed product information such as name, SKU, price, and images.
The images are also uploaded to an AWS S3 bucket for storage.

The pipeline processes the scraped items to:

Validate and clean the data (e.g., unescape HTML and normalize characters).
Upload product data to an S3 bucket in JSON format.
Upload product images to the same S3 bucket, organizing them by SKU for easy access.

The project uses the boto3 Python library to interact with AWS services and upload data to an S3 bucket. All configurations are set through environment variables to ensure flexibility for different environments.

Key Features:

Scrapes product details and images from multiple product categories.
Validates and normalizes scraped data before uploading.
Automatically uploads product images and metadata to AWS S3 using boto3.
