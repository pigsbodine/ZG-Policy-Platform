"""Spiders for provincial government policy portals.

Covered provinces/municipalities:
  - Beijing  (www.beijing.gov.cn)
  - Shanghai  (www.shanghai.gov.cn)
  - Guangdong (www.gd.gov.cn)
  - Zhejiang  (www.zj.gov.cn)
  - Shandong  (www.shandong.gov.cn)
"""
import re
from scrapy import Spider
from scraper.spiders.base import PolicySpider, extract_text
from scraper.items import PolicyDocument


# ---------------------------------------------------------------------------
# Generic helper — most provincial portals follow a similar structure
# ---------------------------------------------------------------------------

def _generic_list_parse(spider, response, source, doc_url_pattern):
    for href in response.css("a::attr(href)").getall():
        if re.search(doc_url_pattern, href):
            yield response.follow(href, lambda r, s=source: _parse_doc(r, s))
    next_page = response.css(
        "a.next::attr(href), a[rel='next']::attr(href), a[title='下一页']::attr(href)"
    ).get()
    if next_page:
        yield response.follow(next_page, lambda r, sp=spider, src=source, pat=doc_url_pattern: _generic_list_parse(sp, r, src, pat))


def _parse_doc(response, source):
    title = (
        response.css(".article-title::text, h1::text, .tit::text, .zwTitle::text").get("").strip()
        or response.css("title::text").get("").strip()
    )
    date = response.css(
        ".date::text, .pubTime::text, .riqi::text, time::text, .zwDate::text"
    ).get("").strip()
    return PolicyDocument(
        url=response.url,
        title=title,
        source=source,
        published_date=date,
        raw_html=response.text,
        text_content=extract_text(response),
    )


# ---------------------------------------------------------------------------
# Beijing
# ---------------------------------------------------------------------------

class BeijingSpider(PolicySpider):
    name = "beijing"
    allowed_domains = ["www.beijing.gov.cn"]
    start_urls = [
        "https://www.beijing.gov.cn/zhengce/zhengcefagui/",
        "https://www.beijing.gov.cn/zhengce/zfwj/",
    ]

    def parse(self, response):
        yield from _generic_list_parse(
            self, response, "beijing",
            r"/zhengce/(zhengcefagui|zfwj|zcjd)/\d{4}"
        )

    def parse_document(self, response):
        yield _parse_doc(response, "beijing")


# ---------------------------------------------------------------------------
# Shanghai
# ---------------------------------------------------------------------------

class ShanghaiSpider(PolicySpider):
    name = "shanghai"
    allowed_domains = ["www.shanghai.gov.cn"]
    start_urls = [
        "https://www.shanghai.gov.cn/nw4411/",  # Policies & regulations
    ]

    def parse(self, response):
        yield from _generic_list_parse(
            self, response, "shanghai",
            r"/nw\d+/\d{4}/\d{2}/\d{2}/"
        )

    def parse_document(self, response):
        yield _parse_doc(response, "shanghai")


# ---------------------------------------------------------------------------
# Guangdong
# ---------------------------------------------------------------------------

class GuangdongSpider(PolicySpider):
    name = "guangdong"
    allowed_domains = ["www.gd.gov.cn"]
    start_urls = [
        "https://www.gd.gov.cn/zwgk/wjk/qbwj/szfbgt/",  # Gov't circulars
        "https://www.gd.gov.cn/zwgk/wjk/qbwj/yzf/",     # Governor's decrees
    ]

    def parse(self, response):
        yield from _generic_list_parse(
            self, response, "guangdong",
            r"/zwgk/wjk/\S+/\d{6}/"
        )

    def parse_document(self, response):
        yield _parse_doc(response, "guangdong")


# ---------------------------------------------------------------------------
# Zhejiang
# ---------------------------------------------------------------------------

class ZhejiangSpider(PolicySpider):
    name = "zhejiang"
    allowed_domains = ["www.zj.gov.cn"]
    start_urls = [
        "https://www.zj.gov.cn/col/col1229542284/",  # Provincial policies
    ]

    def parse(self, response):
        yield from _generic_list_parse(
            self, response, "zhejiang",
            r"/art/\d{4}/\d{1,2}/\d{1,2}/art_\d+_\d+\.html"
        )

    def parse_document(self, response):
        yield _parse_doc(response, "zhejiang")


# ---------------------------------------------------------------------------
# Shandong
# ---------------------------------------------------------------------------

class ShandongSpider(PolicySpider):
    name = "shandong"
    allowed_domains = ["www.shandong.gov.cn"]
    start_urls = [
        "https://www.shandong.gov.cn/col/col100019/",  # Policy documents
    ]

    def parse(self, response):
        yield from _generic_list_parse(
            self, response, "shandong",
            r"/art/\d{4}/\d{1,2}/\d{1,2}/art_\d+_\d+\.html"
        )

    def parse_document(self, response):
        yield _parse_doc(response, "shandong")
