import scrapy
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from scrapy.selector import Selector


class RareGallerySpiderSpider(scrapy.Spider):
    name = "rare_gallery_spider"
    allowed_domains = ["rare-gallery.com"]
    # start_urls = ["https://rare-gallery.com/xfsearch/alt/IU/"]

    def __init__(self, *args, **kwargs):
        super(scrapy.Spider, self).__init__(*args, **kwargs)

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

    # 定义 Scrapy 的起始请求
    def start_requests(self):
        urls = [
            'https://rare-gallery.com/xfsearch/alt/IU/'
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        print("===== parse", response)

        try:
            # 打开目标网站
            self.driver.get(response.url)
        except Exception as e:
            pass

        # 使用 Scrapy Selector 将 Selenium 获取的页面内容转为 Scrapy 可解析的格式
        selenium_html = self.driver.page_source
        sel = Selector(text=selenium_html)
        divs = sel.css('div.wrap div.wrap-main div.cols div.main div.sect div.sect-content div#dle-content div.th-item a.th-in')
        print("==== divs len", len(divs))
        # elements = [ele for ele in divs if ele.css('::attr(class)').get() == 'th-in']
        # print("==== elements len", len(elements))

        # 从每个div中提取具体的子元素，如img或者p标签
        for e in divs:
            detail_url = e.css('a::attr(href)').get() # 提取图片链接
            print("=== detail_url", detail_url)
            # text = div.css('p.description::text').get()  # 提取描述文本

            if detail_url:
                # yield {
                #     'detail_url': detail_url,
                #     # 'description': text
                # }
                yield scrapy.Request(url=detail_url, callback=self.parse_detail)

            break


    def parse_detail(self, response):
        print("===== parse_detail", response)
        try:
            # 打开目标网站
            self.driver.get(response.url)
        except Exception as e:
            pass

        # 使用 Scrapy Selector 将 Selenium 获取的页面内容转为 Scrapy 可解析的格式
        selenium_html = self.driver.page_source
        sel = Selector(text=selenium_html)
        divs = sel.css('div.wrap div.wrap-main div.cols div.main div.clearfix div#dle-content div.full-page div.vpm div.vpm-left div.ftabs input[value="OPEN"]')
        print("==== divs len", len(divs))
        # 遍历找到的 <input> 元素，获取其父级的 <a> 标签
        for ele in divs:
            # 获取父级的 <a> 标签
            a_tag = ele.xpath('..')  # 使用 XPath 获取父级
            href = a_tag.css('::attr(href)').get()  # 获取 href 属性
            print("找到的 href:", href)
            image_urls = [response.urljoin(href)]
            print("image_urls:", image_urls)
            if href:
                yield {
                    'image_urls': image_urls,  # Scrapy Image Pipeline 需要这个格式
                }
                # yield ImageItem(image_urls=[href])
