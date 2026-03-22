"""Spider for State Council policy portal (www.gov.cn/zhengce)."""
import re
from scrapy import Request
from scraper.spiders.base import PolicySpider


class GovCnSpider(PolicySpider):
    name = "gov_cn"
    allowed_domains = ["www.gov.cn"]

    # Policy index pages to seed from
    start_urls = [
        "https://www.gov.cn/zhengce/zuixin/",          # Latest policies
        "https://www.gov.cn/zhengce/zhengceku/",        # Policy announcements
        "https://www.gov.cn/zhengce/guowuyuanwenjian/", # State Council docs
    ]

    def parse(self, response):
        # Follow links to individual policy documents
        for href in response.css("a::attr(href)").getall():
            if re.search(r"/zhengce/content/\d{4}-\d{2}/\d{2}/", href):
                yield response.follow(href, self.parse_document)

        # Follow pagination
        next_page = response.css("a.next::attr(href), a[rel='next']::attr(href)").get()
        if next_page:
            yield response.follow(next_page, self.parse)

    def parse_document(self, response):
        title = (
            response.css(".article-title::text, h1::text, .tit::text").get("").strip()
            or response.css("title::text").get("").strip()
        )
        date = (
            response.css(".article-meta time::text, .date::text, .pubTime::text").get("").strip()
        )
        yield self.make_item(response, source="gov.cn", title=title, date=date)
