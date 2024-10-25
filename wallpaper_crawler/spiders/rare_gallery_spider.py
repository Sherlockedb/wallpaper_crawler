import scrapy
from scrapy.selector import Selector
from wallpaper_crawler.items import RareGalleryItem
from wallpaper_crawler.request_manager import RequestManager, RequestPreiod
import wallpaper_crawler.rare_gallery_setting as rare_gallery_setting


class RareGallerySpiderSpider(scrapy.Spider):
    name = "rare_gallery_spider"
    allowed_domains = ["rare-gallery.com"]

    def __init__(self, *args, **kwargs):
        super(scrapy.Spider, self).__init__(*args, **kwargs)

        self.request_manager = RequestManager(file_path=rare_gallery_setting.REQUEST_STORE, start_urls=rare_gallery_setting.START_URLS)

    # 定义 Scrapy 的起始请求
    def start_requests(self):
        for url in self.request_manager.get_urls_by_stage(RequestPreiod.INIT):
            # self.logger.debug(f"[start_requests] init {url}")
            yield scrapy.Request(url=url, callback=self.parse_navigation, meta={"preiod": RequestPreiod.INIT})
        for url in self.request_manager.get_urls_by_stage(RequestPreiod.NAVIGATION):
            # self.logger.debug(f"[start_requests] list {url}")
            yield scrapy.Request(url=url, callback=self.parse_list, meta={"preiod": RequestPreiod.NAVIGATION})
        for url in self.request_manager.get_urls_by_stage(RequestPreiod.DETAILS):
            # self.logger.debug(f"[start_requests] details {url}")
            yield scrapy.Request(url=url, callback=self.parse_detail, meta={"preiod": RequestPreiod.DETAILS})
        for url in self.request_manager.get_urls_by_stage(RequestPreiod.IMAGE):
            # self.logger.debug(f"[start_requests] image {url}")
            yield scrapy.Request(url=url, callback=self.parse_image, meta={"preiod": RequestPreiod.IMAGE})


    def parse_navigation(self, response):
        page_list = [response.url]
        sel = Selector(response)
        a_tags = sel.css('div.wrap div.wrap-main div.cols div.main div.sect div.sect-content div#dle-content div.bottom-nav div.pagi-nav div.navigation a')
        self.logger.debug("a_tags len", len(a_tags))
        if len(a_tags):
            last_tag = a_tags[-1]
            href = last_tag.css("::attr(href)").get()  # 获取href属性
            text = last_tag.css("::text").get()  # 获取标签文本
            max_page = int(text)
            # self.logger.debug(f"链接: {href}, 文本: {text} max_page: {max_page}")

            for page in range(2, max_page+1):
                page_url = f"{response.url}/page/{page}/"
                page_list.append(page_url)
        self.logger.info(f"parse_navigation page_list_len={len(page_list)}")
        self.request_manager.add_urls(RequestPreiod.NAVIGATION, page_list)
        self.request_manager.done_url(RequestPreiod.INIT, response.url)
        for url in page_list:
            yield scrapy.Request(url=url, callback=self.parse_list, meta={"preiod": RequestPreiod.NAVIGATION})

    def parse_list(self, response):
        # self.logger.debug(f"{response}")
        sel = Selector(response)
        divs = sel.css('div.wrap div.wrap-main div.cols div.main div.sect div.sect-content div#dle-content div.th-item a.th-in')
        # self.logger.debug("divs len", len(divs))

        # 从每个div中提取具体的子元素，如img或者p标签
        detail_urls = (e.css('::attr(href)').get() for e in divs) # 提取图片链接
        detail_urls = [url for url in detail_urls if url]
        if not len(detail_urls):
            self.logger.error(f"[parse_list_error] detail_urls is empty, url={response.url}")
            return

        # detail_urls = [detail_urls[0]] # for test
        self.logger.info(f"parse_list detail_urls_len={len(detail_urls)}")
        self.request_manager.add_urls(RequestPreiod.DETAILS, detail_urls)
        self.request_manager.done_url(RequestPreiod.NAVIGATION, response.url)
        for url in detail_urls:
            yield scrapy.Request(url=url, callback=self.parse_detail, meta={"preiod": RequestPreiod.DETAILS})


    def parse_detail(self, response):
        # self.logger.debug(f"{response}")
        sel = Selector(response)
        divs = sel.css('div.wrap div.wrap-main div.cols div.main div.clearfix div#dle-content div.full-page div.vpm div.vpm-left div.ftabs input[value="OPEN"]')
        # self.logger.debug("divs len", len(divs))
        # 遍历找到的 <input> 元素，获取其父级的 <a> 标签
        image_urls = (ele.xpath('..').css('::attr(href)').get() for ele in divs)
        image_urls = [response.urljoin(url) for url in image_urls if url]
        if not len(image_urls):
            self.logger.error(f"[parse_detail_error] image_urls is empty, url={response.url}")
            return

        self.request_manager.add_urls(RequestPreiod.IMAGE, image_urls)
        self.request_manager.done_url(RequestPreiod.DETAILS, response.url)
        for url in image_urls:
            yield scrapy.Request(url=url, callback=self.parse_image, meta={"preiod": RequestPreiod.IMAGE})

    def parse_image(self, response):
        self.logger.debug(f"==== [parse_image] url {response.url} {response.status}")
        if response.status != 200:
            return
        item = RareGalleryItem()
        item['image_src'] = response.url
        item['image'] = response.body
        yield item
