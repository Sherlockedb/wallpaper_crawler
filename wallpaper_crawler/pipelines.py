# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.pipelines.images import ImagesPipeline
from scrapy.http import Request

import requests
from scrapy.exceptions import DropItem

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

import pycurl
from io import BytesIO

class WallpaperCrawlerPipeline(ImagesPipeline):
    # def process_item(self, item, spider):
    #     return item

    def get_media_requests(self, item, info):
        print("===== item:", item, info)
        for image_url in item.get('image_urls', []):
            print("===== image_url:", image_url)
            yield Request(image_url, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Connection': 'keep-alive',
                'Referer': 'https://rare-gallery.com/',
                'Sec-Ch-Ua': '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"macOS"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
            })


class CustomImagePipeline:

    def process_item(self, item, spider):
        for image_url in item.get('image_urls', []):
            if not image_url:
                continue
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Connection': 'keep-alive',
                'Referer': 'https://rare-gallery.com/',
                'Sec-Ch-Ua': '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"macOS"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
            }

            # 手动发送请求下载图片
            response = requests.get(image_url, headers=headers)

            if response.status_code == 200:
                # 保存图片
                image_path = f"/Users/sherlock/Project/wallpaper_crawler/test_wallpaper/{image_url.split('/')[-1]}"
                with open(image_path, 'wb') as f:
                    f.write(response.content)
                spider.log(f"Image saved at {image_path}")
                return item
            else:
                raise DropItem(f"Failed to download image: {image_url}, Status code: {response.status_code}")


class SeleniumImagePipeline:

    def __init__(self):
        self.driver = self._init_driver()

    def _init_driver(self):
        service = Service('/usr/local/bin/chromedriver')
        # 设置 Chrome 无头模式
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument('User-Agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36')

        # 启动 Chrome 浏览器
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # driver.set_script_timeout(5)  # 设置脚本执行超时为 10 秒
        driver.set_page_load_timeout(5)

        return driver

    def process_item(self, item, spider):
        for image_url in item.get('image_urls', []):
            if not image_url:
                continue

            print("===== image_url", image_url)
            try:
                # 使用 Selenium 获取图片页面
                self.driver.get(image_url)
            except Exception as e:
                pass

            img_element = self.driver.find_element(By.TAG_NAME, 'img')
            img_src = img_element.get_attribute('src')

            print(f"===== Image URL: {img_src}")

            # 获取浏览器的 User-Agent
            user_agent = self.driver.execute_script("return navigator.userAgent;")
            # 获取浏览器的 Cookies
            cookies = self.driver.get_cookies()
            # 构造 Cookies 字符串
            cookies_str = "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])

            # 设置请求头，模仿 Selenium 浏览器
            headers = {
                'User-Agent': user_agent,
                'Referer': self.driver.current_url,  # 当前页面作为 Referer
                'Cookie': cookies_str,  # 从 Selenium 获取的 cookies
            }
            # 使用 requests 下载图片
            response = requests.get(img_src, headers=headers)
            if response.status_code == 200:
                image_path = f"/Users/sherlock/Project/wallpaper_crawler/test_wallpaper/{image_url.split('/')[-1]}"
                with open(image_path, 'wb') as f:
                    f.write(response.content)
                spider.log(f"Image saved at {image_path}")
            else:
                spider.log(f"Failed to download image: {img_src} code: {response.status_code}")

    def close_spider(self, spider):
        self.driver.quit()

class PyCurlImagePipeline:

    def process_item(self, item, spider):
        for image_url in item.get('image_urls', []):
            if not image_url:
                continue

            # 创建一个 BytesIO 对象来保存下载的数据
            buffer = BytesIO()

            # 创建 pycurl 对象
            c = pycurl.Curl()
            c.setopt(c.URL, image_url)  # 设置下载的 URL
            c.setopt(c.WRITEDATA, buffer)  # 将数据写入 BytesIO 对象
            c.setopt(c.FOLLOWLOCATION, True)  # 允许跟随重定向
            c.setopt(c.USERAGENT, 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36') # 设置 User-Agent，模拟 curl 请求

            status_code = 0
            try:
                # 执行下载
                c.perform()
                # 获取 HTTP 状态码
                status_code = c.getinfo(c.RESPONSE_CODE)
            except pycurl.error as e:
                print(f'An error occurred: {e}')
            finally:
                # 关闭 pycurl 对象
                c.close()

            if status_code == 200:
                # 保存图片
                image_path = f"/Users/sherlock/Project/wallpaper_crawler/test_wallpaper/{image_url.split('/')[-1]}"
                with open(image_path, 'wb') as f:
                    f.write(buffer.getvalue())
                spider.log(f"Image saved at {image_path}")
                return item
            else:
                raise DropItem(f"Failed to download image: {image_url}, Status code: {status_code}")
