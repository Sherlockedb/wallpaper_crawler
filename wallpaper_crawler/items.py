# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class WallpaperCrawlerItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class RareGalleryItem(scrapy.Item):
    image_src = scrapy.Field()
    image = scrapy.Field()
