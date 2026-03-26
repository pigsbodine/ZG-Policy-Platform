"""Spider for MOFCOM policy documents (www.mofcom.gov.cn).

MOFCOM document URL pattern:
  /article/<category>/<YYYYMM>/<20-digit-id>.shtml
  e.g. /article/zcfg/fzjd/202401/20240103450999.shtml
"""
import re
from scraper.spiders.base import PolicySpider

# Matches MOFCOM .shtml article URLs that contain a date segment
_DOC_PATTERN = re.compile(r"/article/[^?#]+/\d{6}/\d+\.shtml")

_TITLE_SELS = ", ".join([
    ".article-title::text",
    "h1.tit::text",
    "h1::text",
    ".tit::text",
    ".articleTitle::text",
])

_DATE_SELS = ", ".join([
    ".date::text",
    ".pubTime::text",
    "span.time::text",
    "time::attr(datetime)",
    "time::text",
    "p.date::text",
])

_NEXT_SELS = ", ".join([
    "a.next::attr(href)",
    "a[title='下一页']::attr(href)",
    "li.next a::attr(href)",
    ".page-next a::attr(href)",
])


class MofcomSpider(PolicySpider):
    name = "mofcom"
    allowed_domains = ["www.mofcom.gov.cn"]

    start_urls = [
        "https://www.mofcom.gov.cn/article/zcfg/",       # Regulations
        "https://www.mofcom.gov.cn/article/zcfg/fzjd/",  # Interpretation
        "https://www.mofcom.gov.cn/article/gzdt/",       # Work updates
        "https://www.mofcom.gov.cn/article/toutiao/",    # Headlines
    ]

    def parse(self, response):
        for href in response.css("a::attr(href)").getall():
            if _DOC_PATTERN.search(href):
                yield response.follow(href, self.parse_document)

        next_page = response.css(_NEXT_SELS).get()
        if next_page:
            yield response.follow(next_page, self.parse)

    def parse_document(self, response):
        title = (
            response.css(_TITLE_SELS).get("").strip()
            or response.css("title::text").get("").strip()
        )
        date = response.css(_DATE_SELS).get("").strip()
        yield self.make_item(response, source="mofcom", title=title, date=date)
