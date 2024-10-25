# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

from wallpaper_crawler.request_manager import RequestManager, RequestPreiod
import wallpaper_crawler.rare_gallery_setting as rare_gallery_setting


class PyCurlImagePipeline:

    def __init__(self):
        self.request_manager = RequestManager(file_path=rare_gallery_setting.REQUEST_STORE)

    def process_item(self, item, spider):
        spider.logger.debug("===== process_item")

        image_url = item['image_src']
        image_path = f"{rare_gallery_setting.IMAGES_STORE}/{image_url.split('/')[-1]}"
        with open(image_path, 'wb') as f:
            f.write(item['image'])
        spider.logger.info(f"Image {image_url} saved at {image_path}")
        self.request_manager.done_url(RequestPreiod.IMAGE, image_url)

