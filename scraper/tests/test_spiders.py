"""
Spider unit tests using fake HTML fixtures.

These tests verify that:
  - URL patterns accept the right document URLs and reject list/news URLs
  - CSS selectors extract title and date correctly from document pages
  - Pagination requests are generated
  - The correct source label is set on scraped items

Run from the scraper/ directory:
  pytest tests/
"""
import os
from pathlib import Path

import pytest
from scrapy.http import HtmlResponse, Request

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def fake_response(filename: str, url: str) -> HtmlResponse:
    """Build a Scrapy HtmlResponse from a local HTML fixture file."""
    html = (FIXTURES_DIR / filename).read_bytes()
    return HtmlResponse(url=url, body=html, encoding="utf-8")


def collect(generator):
    """Drain a generator (spider callback) and split into requests vs items."""
    from scrapy import Request
    from scrapy.item import Item

    requests, items = [], []
    for obj in generator:
        if isinstance(obj, Request):
            requests.append(obj)
        elif isinstance(obj, Item):
            items.append(obj)
    return requests, items


# ---------------------------------------------------------------------------
# gov_cn spider
# ---------------------------------------------------------------------------

class TestGovCnSpider:
    @pytest.fixture
    def spider(self):
        from scraper.spiders.gov_cn import GovCnSpider
        return GovCnSpider()

    def test_list_page_finds_doc_urls(self, spider):
        resp = fake_response(
            "gov_cn_list.html",
            "https://www.gov.cn/zhengce/zuixin/",
        )
        requests, items = collect(spider.parse(resp))
        doc_urls = [r.url for r in requests if "zhengce/content" in r.url or "zhengceku" in r.url]
        # 3 matching policy doc links + 1 pagination
        assert len(doc_urls) == 4, f"Expected 4 doc requests, got {doc_urls}"

    def test_list_page_pagination(self, spider):
        resp = fake_response(
            "gov_cn_list.html",
            "https://www.gov.cn/zhengce/zuixin/",
        )
        requests, _ = collect(spider.parse(resp))
        page_urls = [r.url for r in requests if "page=2" in r.url]
        assert len(page_urls) == 1

    def test_list_page_ignores_non_policy_links(self, spider):
        resp = fake_response(
            "gov_cn_list.html",
            "https://www.gov.cn/zhengce/zuixin/",
        )
        requests, _ = collect(spider.parse(resp))
        bad = [r for r in requests if "xinwen" in r.url or "moe.gov.cn" in r.url]
        assert bad == [], f"Non-policy URLs followed: {bad}"

    def test_doc_page_extracts_title_and_date(self, spider):
        resp = fake_response(
            "gov_cn_doc.html",
            "https://www.gov.cn/zhengce/content/2024-03/15/content_5878901.htm",
        )
        _, items = collect(spider.parse_document(resp))
        assert len(items) == 1
        item = items[0]
        assert "数字经济" in item["title"]
        assert item["published_date"] == "2024-03-15"
        assert item["source"] == "gov.cn"
        assert len(item["text_content"]) > 10

    def test_doc_page_falls_back_to_page_title(self, spider):
        """If no .pages-title/h1, use <title> tag."""
        html = b"<html><head><title>Fallback Title - gov.cn</title></head><body><p>content</p></body></html>"
        resp = HtmlResponse(
            url="https://www.gov.cn/zhengce/content/2024-03/01/content_0001.htm",
            body=html,
            encoding="utf-8",
        )
        _, items = collect(spider.parse_document(resp))
        assert items[0]["title"] == "Fallback Title - gov.cn"


# ---------------------------------------------------------------------------
# ndrc spider
# ---------------------------------------------------------------------------

class TestNdrcSpider:
    @pytest.fixture
    def spider(self):
        from scraper.spiders.ndrc import NdrcSpider
        return NdrcSpider()

    def test_list_page_finds_doc_urls(self, spider):
        resp = fake_response(
            "ndrc_list.html",
            "https://www.ndrc.gov.cn/xxgk/zcfb/",
        )
        requests, _ = collect(spider.parse(resp))
        doc_urls = [r.url for r in requests if "/xxgk/zcfb/" in r.url and r.url.endswith(".html")]
        assert len(doc_urls) == 3, f"Expected 3 doc links, got {doc_urls}"

    def test_list_page_ignores_non_zcfb_links(self, spider):
        resp = fake_response(
            "ndrc_list.html",
            "https://www.ndrc.gov.cn/xxgk/zcfb/",
        )
        requests, _ = collect(spider.parse(resp))
        bad = [r for r in requests if "jd/wsjd" in r.url or "xwdt" in r.url]
        assert bad == []

    def test_list_page_pagination(self, spider):
        resp = fake_response(
            "ndrc_list.html",
            "https://www.ndrc.gov.cn/xxgk/zcfb/",
        )
        requests, _ = collect(spider.parse(resp))
        assert any("page=2" in r.url for r in requests)

    def test_doc_page_extracts_title_and_date(self, spider):
        resp = fake_response(
            "ndrc_doc.html",
            "https://www.ndrc.gov.cn/xxgk/zcfb/tz/202403/t20240315_1365201.html",
        )
        _, items = collect(spider.parse_document(resp))
        assert len(items) == 1
        item = items[0]
        assert "水污染" in item["title"]
        assert item["published_date"] == "2024-03-15"
        assert item["source"] == "ndrc"


# ---------------------------------------------------------------------------
# mofcom spider
# ---------------------------------------------------------------------------

class TestMofcomSpider:
    @pytest.fixture
    def spider(self):
        from scraper.spiders.mofcom import MofcomSpider
        return MofcomSpider()

    def test_list_page_finds_doc_urls(self, spider):
        resp = fake_response(
            "mofcom_list.html",
            "https://www.mofcom.gov.cn/article/zcfg/",
        )
        requests, _ = collect(spider.parse(resp))
        doc_urls = [r.url for r in requests if r.url.endswith(".shtml")]
        assert len(doc_urls) == 3, f"Expected 3 doc links, got {doc_urls}"

    def test_list_page_ignores_non_shtml_links(self, spider):
        resp = fake_response(
            "mofcom_list.html",
            "https://www.mofcom.gov.cn/article/zcfg/",
        )
        requests, _ = collect(spider.parse(resp))
        # The bare /article/zcfg/ and /news/*.html links should be ignored
        bad = [r for r in requests if r.url.endswith(".html") or r.url == "https://www.mofcom.gov.cn/article/zcfg/"]
        assert bad == [], f"Unexpected requests: {bad}"

    def test_doc_page_extracts_title_and_date(self, spider):
        html = (
            "<html><head><title>Foreign Trade Law - MOFCOM</title></head>"
            "<body>"
            '<h1 class="tit">Foreign Trade Law Implementation Rules (Revised)</h1>'
            '<span class="date">2024-03-03</span>'
            "<div class=\"article-body\"><p>Chapter 1: General Provisions</p></div>"
            "</body></html>"
        ).encode("utf-8")
        resp = HtmlResponse(
            url="https://www.mofcom.gov.cn/article/zcfg/202403/20240303489301.shtml",
            body=html,
            encoding="utf-8",
        )
        _, items = collect(spider.parse_document(resp))
        assert len(items) == 1
        assert "Foreign Trade Law" in items[0]["title"]
        assert items[0]["published_date"] == "2024-03-03"
        assert items[0]["source"] == "mofcom"


# ---------------------------------------------------------------------------
# provincial spiders
# ---------------------------------------------------------------------------

class TestBeijingSpider:
    @pytest.fixture
    def spider(self):
        from scraper.spiders.provincial import BeijingSpider
        return BeijingSpider()

    def test_list_page_finds_doc_urls(self, spider):
        resp = fake_response(
            "beijing_list.html",
            "https://www.beijing.gov.cn/zhengce/zhengcefagui/",
        )
        requests, _ = collect(spider.parse(resp))
        doc_urls = [r.url for r in requests if "/zhengce/" in r.url and "page" not in r.url]
        assert len(doc_urls) == 3, f"Got: {doc_urls}"

    def test_list_page_ignores_news(self, spider):
        resp = fake_response(
            "beijing_list.html",
            "https://www.beijing.gov.cn/zhengce/zhengcefagui/",
        )
        requests, _ = collect(spider.parse(resp))
        bad = [r for r in requests if "xinwen" in r.url]
        assert bad == []

    def test_list_page_pagination(self, spider):
        resp = fake_response(
            "beijing_list.html",
            "https://www.beijing.gov.cn/zhengce/zhengcefagui/",
        )
        requests, _ = collect(spider.parse(resp))
        assert any("page=2" in r.url for r in requests)

    def test_doc_page_extracts_fields(self, spider):
        resp = fake_response(
            "provincial_doc.html",
            "https://www.beijing.gov.cn/zhengce/zhengcefagui/2024/content_001.html",
        )
        # parse_document calls _parse_doc which yields the item
        _, items = collect(spider.parse_document(resp))
        assert len(items) == 1
        item = items[0]
        assert "数字经济" in item["title"]
        assert item["published_date"] == "2024-03-15"
        assert item["source"] == "beijing"
        assert item["url"] == "https://www.beijing.gov.cn/zhengce/zhengcefagui/2024/content_001.html"


# ---------------------------------------------------------------------------
# Pipeline tests
# ---------------------------------------------------------------------------

class TestDeduplicationPipeline:
    def test_drops_duplicate_url(self):
        from scrapy.exceptions import DropItem
        from scraper.pipelines import DeduplicationPipeline
        from scraper.items import PolicyDocument

        dedup = DeduplicationPipeline()
        dedup._seen_urls = {"https://example.com/doc1"}

        with pytest.raises(DropItem):
            dedup.process_item(
                PolicyDocument(url="https://example.com/doc1", title="x", source="x"),
                spider=None,
            )

    def test_passes_new_url(self):
        from scraper.pipelines import DeduplicationPipeline
        from scraper.items import PolicyDocument

        dedup = DeduplicationPipeline()
        dedup._seen_urls = {"https://example.com/doc1"}

        item = PolicyDocument(url="https://example.com/doc2", title="x", source="x")
        result = dedup.process_item(item, spider=None)
        assert result is item

    def test_second_call_with_same_url_is_dropped(self):
        from scrapy.exceptions import DropItem
        from scraper.pipelines import DeduplicationPipeline
        from scraper.items import PolicyDocument

        dedup = DeduplicationPipeline()
        dedup._seen_urls = set()

        item = PolicyDocument(url="https://example.com/doc1", title="x", source="x")
        dedup.process_item(item, spider=None)  # first pass: OK
        with pytest.raises(DropItem):
            dedup.process_item(item, spider=None)  # second pass: dropped


class TestDatabasePipeline:
    def test_insert_and_retrieve(self, tmp_path):
        import sqlite3
        from scraper.pipelines import DatabasePipeline
        from scraper.items import PolicyDocument

        db_path = str(tmp_path / "test.db")
        pipe = DatabasePipeline()
        pipe.conn = sqlite3.connect(db_path)
        pipe._setup_db()

        item = PolicyDocument(
            url="https://example.com/doc1",
            title="Test Policy",
            source="test",
            published_date="2024-01-01",
            raw_html="<html></html>",
            text_content="test content",
        )
        pipe.process_item(item, spider=None)

        row = pipe.conn.execute("SELECT title, source FROM documents WHERE url=?", (item["url"],)).fetchone()
        assert row is not None
        assert row[0] == "Test Policy"
        assert row[1] == "test"

        pipe.conn.close()

    def test_duplicate_url_silently_ignored(self, tmp_path):
        import sqlite3
        from scraper.pipelines import DatabasePipeline
        from scraper.items import PolicyDocument

        db_path = str(tmp_path / "test.db")
        pipe = DatabasePipeline()
        pipe.conn = sqlite3.connect(db_path)
        pipe._setup_db()

        item = PolicyDocument(url="https://example.com/doc1", title="T", source="s",
                               published_date="", raw_html="", text_content="")
        pipe.process_item(item, spider=None)
        pipe.process_item(item, spider=None)  # should not raise

        count = pipe.conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        assert count == 1
        pipe.conn.close()


# ---------------------------------------------------------------------------
# PDF support tests
# ---------------------------------------------------------------------------

class TestPdfUtils:
    def test_extract_text_from_valid_pdf(self):
        from scraper.pdf_utils import extract_pdf_text
        pdf_bytes = (FIXTURES_DIR / "sample.pdf").read_bytes()
        text = extract_pdf_text(pdf_bytes)
        assert "Test Policy Text" in text

    def test_extract_text_from_empty_bytes_returns_empty(self):
        from scraper.pdf_utils import extract_pdf_text
        assert extract_pdf_text(b"") == ""

    def test_extract_text_from_garbage_returns_empty(self):
        from scraper.pdf_utils import extract_pdf_text
        assert extract_pdf_text(b"this is not a pdf") == ""

    def test_looks_like_pdf_by_content_type(self):
        from scraper.pdf_utils import looks_like_pdf
        assert looks_like_pdf("https://example.com/doc", "application/pdf") is True
        assert looks_like_pdf("https://example.com/doc", "text/html") is False

    def test_looks_like_pdf_by_url(self):
        from scraper.pdf_utils import looks_like_pdf
        assert looks_like_pdf("https://example.com/doc.pdf", "text/html") is True
        assert looks_like_pdf("https://example.com/doc.pdf?dl=1", "text/html") is True
        assert looks_like_pdf("https://example.com/doc.html", "text/html") is False


class TestFollowPdfLinks:
    """Test that spiders generate PDF requests from HTML pages with PDF links."""

    @pytest.fixture
    def spider(self):
        from scraper.spiders.gov_cn import GovCnSpider
        return GovCnSpider()

    def test_follow_pdf_links_yields_requests(self, spider):
        html = (
            "<html><body>"
            '<a href="/zhengce/files/policy.pdf">Download PDF</a>'
            '<a href="/zhengce/files/annex.pdf">Annex</a>'
            "<p>Some content</p>"
            "</body></html>"
        ).encode("utf-8")
        resp = HtmlResponse(
            url="https://www.gov.cn/zhengce/content/2024-03/15/content_001.htm",
            body=html,
            encoding="utf-8",
        )
        requests = list(spider.follow_pdf_links(resp, source="gov.cn", title="Test", date="2024-03-15"))
        assert len(requests) == 2
        assert all(r.url.endswith(".pdf") for r in requests)
        assert all(r.meta["pdf_source"] == "gov.cn" for r in requests)
        assert all(r.meta["pdf_title"] == "Test" for r in requests)
        assert all(r.meta["pdf_date"] == "2024-03-15" for r in requests)
        assert all(r.callback == spider.parse_pdf for r in requests)

    def test_follow_pdf_links_deduplicates(self, spider):
        html = (
            "<html><body>"
            '<a href="/files/doc.pdf">PDF</a>'
            '<a href="/files/doc.pdf">PDF again</a>'
            "</body></html>"
        ).encode("utf-8")
        resp = HtmlResponse(
            url="https://www.gov.cn/zhengce/content/2024-03/15/content_001.htm",
            body=html,
            encoding="utf-8",
        )
        requests = list(spider.follow_pdf_links(resp, source="gov.cn"))
        assert len(requests) == 1

    def test_follow_pdf_links_ignores_non_pdf(self, spider):
        html = (
            "<html><body>"
            '<a href="/doc.html">HTML doc</a>'
            '<a href="/doc.docx">Word doc</a>'
            "</body></html>"
        ).encode("utf-8")
        resp = HtmlResponse(
            url="https://www.gov.cn/zhengce/content/2024-03/15/content_001.htm",
            body=html,
            encoding="utf-8",
        )
        requests = list(spider.follow_pdf_links(resp, source="gov.cn"))
        assert requests == []


class TestParsePdf:
    @pytest.fixture
    def spider(self):
        from scraper.spiders.gov_cn import GovCnSpider
        return GovCnSpider()

    def test_parse_pdf_yields_item(self, spider):
        from scrapy.http import Response, Request
        pdf_bytes = (FIXTURES_DIR / "sample.pdf").read_bytes()
        req = Request(
            url="https://www.gov.cn/zhengce/files/policy.pdf",
            meta={"pdf_title": "Test Policy", "pdf_date": "2024-03-15", "pdf_source": "gov.cn"},
        )
        resp = Response(
            url="https://www.gov.cn/zhengce/files/policy.pdf",
            body=pdf_bytes,
            headers={"Content-Type": "application/pdf"},
            request=req,
        )
        _, items = collect(spider.parse_pdf(resp))
        assert len(items) == 1
        item = items[0]
        assert item["source"] == "gov.cn"
        assert item["title"] == "Test Policy"
        assert item["published_date"] == "2024-03-15"
        assert "Test Policy Text" in item["text_content"]
        assert item["raw_html"] == ""

    def test_parse_pdf_skips_non_pdf_content_type(self, spider):
        from scrapy.http import Response, Request
        req = Request(
            url="https://www.gov.cn/zhengce/content/2024-03/15/content_001.htm",
            meta={"pdf_title": "", "pdf_date": "", "pdf_source": "gov.cn"},
        )
        resp = Response(
            url="https://www.gov.cn/doc.htm",
            body=b"<html></html>",
            headers={"Content-Type": "text/html"},
            request=req,
        )
        _, items = collect(spider.parse_pdf(resp))
        assert items == []

    def test_parse_pdf_skips_empty_pdf(self, spider):
        from scrapy.http import Response, Request
        req = Request(
            url="https://www.gov.cn/files/empty.pdf",
            meta={"pdf_title": "", "pdf_date": "", "pdf_source": "gov.cn"},
        )
        resp = Response(
            url="https://www.gov.cn/files/empty.pdf",
            body=b"",
            headers={"Content-Type": "application/pdf"},
            request=req,
        )
        _, items = collect(spider.parse_pdf(resp))
        assert items == []


class TestDocPageFollowsPdfLinks:
    """Integration: parse_document yields both an HTML item and PDF requests."""

    @pytest.fixture
    def spider(self):
        from scraper.spiders.gov_cn import GovCnSpider
        return GovCnSpider()

    def test_parse_document_also_yields_pdf_requests(self, spider):
        html = (
            "<html><head><title>Policy - gov.cn</title></head><body>"
            '<h1 class="pages-title">Some Policy</h1>'
            '<time datetime="2024-03-15">2024-03-15</time>'
            '<a href="/files/policy_full.pdf">Full text PDF</a>'
            "<p>Brief summary...</p>"
            "</body></html>"
        ).encode("utf-8")
        resp = HtmlResponse(
            url="https://www.gov.cn/zhengce/content/2024-03/15/content_001.htm",
            body=html,
            encoding="utf-8",
        )
        requests, items = collect(spider.parse_document(resp))
        assert len(items) == 1, "Should yield 1 HTML item"
        assert len(requests) == 1, "Should yield 1 PDF request"
        assert requests[0].url.endswith(".pdf")
        assert requests[0].meta["pdf_title"] == "Some Policy"
