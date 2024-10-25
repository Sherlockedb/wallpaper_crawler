# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter

import time

from shutil import which
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

from scrapy.http import HtmlResponse

import pycurl
from io import BytesIO

from wallpaper_crawler.request_manager import RequestPreiod

class WallpaperCrawlerSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class WallpaperCrawlerDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def __init__(self):
        self.driver = self._init_driver()

    def _init_driver(self):
        service = Service(which('chromedriver'))
        # 设置 Chrome 无头模式
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('User-Agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36')

        # 启动 Chrome 浏览器
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # driver.set_script_timeout(5)  # 设置脚本执行超时为 10 秒
        driver.set_page_load_timeout(5)

        return driver

    def _download_html(self, request, spider, retry=0):
        try:
            # 打开目标网站
            self.driver.get(request.url)
        except TimeoutException:
            pass
        except Exception as e:
            if retry:
                time.sleep(5)
                return self._download_html(request, spider, retry-1)
            return HtmlResponse(url=request.url, body=str(e), status=0, encoding='utf-8')

        # 返回新的响应对象
        return HtmlResponse(
            url=request.url,
            body=self.driver.page_source,
            status=200,
            encoding='utf-8',
            request=request
        )

    def _download_image(self, image_url, spider, retry=0):
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
                spider.log(f"Success to download image: {image_url}, Status code: {status_code}")
                response = HtmlResponse(url=image_url, body=buffer.getvalue(), status=200, encoding='utf-8')
                return response
            else:
                spider.log(f"Failed to download image: {image_url}, Status code: {status_code}")
                if retry:
                    time.sleep(5)
                    return self._download_image(image_url, spider, retry-1)
                return HtmlResponse(url=image_url, body="", status=status_code, encoding='utf-8')

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called

        spider.logger.info(f"==== process_request {request}")
        preiod = request.meta.get('preiod')
        if preiod in [RequestPreiod.INIT, RequestPreiod.NAVIGATION, RequestPreiod.DETAILS]:
            return self._download_html(request, spider, retry=5)
        elif preiod in [RequestPreiod.IMAGE]:
            return self._download_image(request.url, spider, retry=5)
        else:
            return

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)
