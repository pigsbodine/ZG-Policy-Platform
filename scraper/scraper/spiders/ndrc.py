"""Spider for NDRC policy publications (www.ndrc.gov.cn)."""
import re
from scraper.spiders.base import PolicySpider


class NdrcSpider(PolicySpider):
    name = "ndrc"
    allowed_domains = ["www.ndrc.gov.cn"]

    start_urls = [
        "https://www.ndrc.gov.cn/xxgk/zcfb/",    # Regulations & policies
        "https://www.ndrc.gov.cn/xxgk/zcfb/ghwb/", # Plans
        "https://www.ndrc.gov.cn/xxgk/zcfb/tz/",   # Notices
    ]

    def parse(self, response):
        for href in response.css("a::attr(href)").getall():
            # NDRC article URLs typically contain /xxgk/ and end with .html
            if re.search(r"/xxgk/\S+\.html", href) and "/zcfb/" in href:
                yield response.follow(href, self.parse_document)

        next_page = response.css("a.next::attr(href), .page-next a::attr(href)").get()
        if next_page:
            yield response.follow(next_page, self.parse)

    def parse_document(self, response):
        title = (
            response.css(".article-title::text, h1::text, .Title::text").get("").strip()
            or response.css("title::text").get("").strip()
        )
        date = response.css(".pubTime::text, .riqi::text, .date::text").get("").strip()
        yield self.make_item(response, source="ndrc", title=title, date=date)
