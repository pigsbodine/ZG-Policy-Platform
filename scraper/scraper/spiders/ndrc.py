"""Spider for NDRC policy publications (www.ndrc.gov.cn).

NDRC document URL pattern:
  /xxgk/zcfb/<category>/<YYYYMM>/t<YYYYMMDD>_<ID>.html
  e.g. /xxgk/zcfb/ghxwj/202107/t20210723_1291321.html
"""
import re
from scraper.spiders.base import PolicySpider

# Matches NDRC document URLs under /xxgk/zcfb/
_DOC_PATTERN = re.compile(r"/xxgk/zcfb/[^/]+/\d{6}/\S+\.html")

_TITLE_SELS = ", ".join([
    ".article-title::text",
    ".articleTitle::text",
    "h1.Title::text",
    "h1::text",
    ".Title::text",
])

_DATE_SELS = ", ".join([
    ".pubTime::text",
    ".riqi::text",
    ".date::text",
    "span.date::text",
    "time::attr(datetime)",
    "time::text",
])

_NEXT_SELS = ", ".join([
    "a.next::attr(href)",
    ".page-next a::attr(href)",
    "a[title='下一页']::attr(href)",
    "li.next a::attr(href)",
])


class NdrcSpider(PolicySpider):
    name = "ndrc"
    allowed_domains = ["www.ndrc.gov.cn"]

    start_urls = [
        "https://www.ndrc.gov.cn/xxgk/zcfb/",      # Regulations & policies
        "https://www.ndrc.gov.cn/xxgk/zcfb/ghwb/",  # Plans
        "https://www.ndrc.gov.cn/xxgk/zcfb/tz/",    # Notices
        "https://www.ndrc.gov.cn/xxgk/zcfb/ghxwj/", # Normative documents
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
        yield self.make_item(response, source="ndrc", title=title, date=date)
        yield from self.follow_pdf_links(response, source="ndrc", title=title, date=date)
