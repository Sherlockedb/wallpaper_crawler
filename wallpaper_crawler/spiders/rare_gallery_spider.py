import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from scrapy.selector import Selector
from shutil import which
from wallpaper_crawler.request_manager import RequestManager, RequestPreiod
import wallpaper_crawler.rare_gallery_setting as rare_gallery_setting


class RareGallerySpiderSpider(scrapy.Spider):
    name = "rare_gallery_spider"
    allowed_domains = ["rare-gallery.com"]
    start_urls = ["https://rare-gallery.com/xfsearch/alt/IU/"]

    def __init__(self, *args, **kwargs):
        super(scrapy.Spider, self).__init__(*args, **kwargs)

        self.driver = self._init_driver()
        self.request_manager = RequestManager(file_path=rare_gallery_setting.REQUEST_STORE, start_urls=self.start_urls)

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

    # 定义 Scrapy 的起始请求
    def start_requests(self):
        for url in self.request_manager.get_urls_by_stage(RequestPreiod.INIT):
            # print(f"[start_requests] init {url}")
            yield scrapy.Request(url=url, callback=self.parse)
        for url in self.request_manager.get_urls_by_stage(RequestPreiod.DETAILS):
            # print(f"[start_requests] details {url}")
            yield scrapy.Request(url=url, callback=self.parse_detail)
        for url in self.request_manager.get_urls_by_stage(RequestPreiod.IMAGE):
            # print(f"[start_requests] image {url}")
            yield scrapy.Request(url=url, callback=self.parse_image)

    def parse(self, response):
        # print(f"==== [parse] {response}")

        try:
            # 打开目标网站
            self.driver.get(response.url)
        except Exception as e:
            pass

        # 使用 Scrapy Selector 将 Selenium 获取的页面内容转为 Scrapy 可解析的格式
        selenium_html = self.driver.page_source
        sel = Selector(text=selenium_html)
        divs = sel.css('div.wrap div.wrap-main div.cols div.main div.sect div.sect-content div#dle-content div.th-itemiph a.th-in')
        # print("==== [parse] divs len", len(divs))

        # 从每个div中提取具体的子元素，如img或者p标签
        detail_urls = (e.css('::attr(href)').get() for e in divs) # 提取图片链接
        detail_urls = [url for url in detail_urls if url]
        if not len(detail_urls):
            # print(f"[parse_error] detail_urls is empty, url={response.url}")
            return

        # detail_urls = [detail_urls[0]] # for test
        self.request_manager.add_urls(RequestPreiod.DETAILS, detail_urls)
        self.request_manager.done_url(RequestPreiod.INIT, response.url)
        for url in detail_urls:
            yield scrapy.Request(url=url, callback=self.parse_detail)


    def parse_detail(self, response):
        # print(f"==== [parse_detail] {response}")
        try:
            # 打开目标网站
            self.driver.get(response.url)
        except Exception as e:
            pass

        # 使用 Scrapy Selector 将 Selenium 获取的页面内容转为 Scrapy 可解析的格式
        selenium_html = self.driver.page_source
        sel = Selector(text=selenium_html)
        divs = sel.css('div.wrap div.wrap-main div.cols div.main div.clearfix div#dle-content div.full-page div.vpm div.vpm-left div.ftabs input[value="OPEN"]')
        # print("==== [parse_detail] divs len", len(divs))
        # 遍历找到的 <input> 元素，获取其父级的 <a> 标签
        image_urls = (ele.xpath('..').css('::attr(href)').get() for ele in divs)
        image_urls = [response.urljoin(url) for url in image_urls if url]
        if not len(image_urls):
            print(f"[parse_detail_error] image_urls is empty, url={response.url}")
            return

        self.request_manager.add_urls(RequestPreiod.IMAGE, image_urls)
        self.request_manager.done_url(RequestPreiod.DETAILS, response.url)
        yield {
            'image_urls': image_urls,  # Scrapy Image Pipeline 需要这个格式
        }

    def parse_image(self, response):
        # print(f"==== [parse_image] url {response.url}")
        yield {
            'image_urls': [response.url],  # Scrapy Image Pipeline 需要这个格式
        }