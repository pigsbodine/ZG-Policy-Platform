"""Spider for MOFCOM policy documents (www.mofcom.gov.cn)."""
import re
from scraper.spiders.base import PolicySpider


class MofcomSpider(PolicySpider):
    name = "mofcom"
    allowed_domains = ["www.mofcom.gov.cn"]

    start_urls = [
        "https://www.mofcom.gov.cn/article/zcfg/",       # Regulations
        "https://www.mofcom.gov.cn/article/zcfg/fzjd/",  # Interpretation
        "https://www.mofcom.gov.cn/article/gzdt/",       # Work updates
    ]

    def parse(self, response):
        for href in response.css("a::attr(href)").getall():
            if re.search(r"/article/\w+/\d{6}/\d+\.shtml", href):
                yield response.follow(href, self.parse_document)

        next_page = response.css("a.next::attr(href), a[title='下一页']::attr(href)").get()
        if next_page:
            yield response.follow(next_page, self.parse)

    def parse_document(self, response):
        title = (
            response.css(".article-title::text, h1::text, .tit::text").get("").strip()
            or response.css("title::text").get("").strip()
        )
        date = response.css(".date::text, .pubTime::text, span.time::text").get("").strip()
        yield self.make_item(response, source="mofcom", title=title, date=date)
