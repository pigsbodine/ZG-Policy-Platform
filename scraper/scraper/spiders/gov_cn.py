"""Spider for State Council policy portal (www.gov.cn/zhengce)."""
import re
from scraper.spiders.base import PolicySpider

# Matches both /zhengce/content/ and /zhengce/zhengceku/ document pages
_DOC_PATTERN = re.compile(
    r"/zhengce/(content|zhengceku|guowuyuanwenjian)/\d{4}-\d{2}/\d{2}/"
)

_TITLE_SELS = ", ".join([
    ".article-title::text",
    "h1.pages-title::text",
    ".primoHeading::text",
    "h1::text",
    ".tit::text",
])

_DATE_SELS = ", ".join([
    ".article-meta time::attr(datetime)",
    ".article-meta time::text",
    ".pubTime::text",
    ".date::text",
    "span.date::text",
    "p.date::text",
])

_NEXT_SELS = ", ".join([
    "a.next::attr(href)",
    "a[rel='next']::attr(href)",
    "a[title='下一页']::attr(href)",
    ".pager-next a::attr(href)",
    "li.next a::attr(href)",
])


class GovCnSpider(PolicySpider):
    name = "gov_cn"
    allowed_domains = ["www.gov.cn"]

    start_urls = [
        "https://www.gov.cn/zhengce/zuixin/",           # Latest policies
        "https://www.gov.cn/zhengce/zhengceku/",         # Policy announcements
        "https://www.gov.cn/zhengce/guowuyuanwenjian/",  # State Council docs
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
        yield self.make_item(response, source="gov.cn", title=title, date=date)
        yield from self.follow_pdf_links(response, source="gov.cn", title=title, date=date)
