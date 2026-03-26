"""Shared utilities for policy spiders."""
import re
from scrapy import Spider

# Matches href attributes that point to PDFs, including URLs with query strings
_PDF_HREF_RE = re.compile(r"\.pdf(\?|#|$)", re.IGNORECASE)


def extract_text(response) -> str:
    """Strip scripts/styles and return visible text from a page."""
    response.selector.remove_namespaces()
    for sel in response.css("script, style, nav, footer, header"):
        sel.root.getparent().remove(sel.root)
    lines = response.css("body *::text").getall()
    text = "\n".join(l.strip() for l in lines if l.strip())
    return re.sub(r"\n{3,}", "\n\n", text)


class PolicySpider(Spider):
    """Base spider with HTML item creation and PDF attachment handling."""

    def make_item(self, response, source: str, title: str = "", date: str = ""):
        from scraper.items import PolicyDocument
        return PolicyDocument(
            url=response.url,
            title=title or response.css("title::text").get("").strip(),
            source=source,
            published_date=date,
            raw_html=response.text,
            text_content=extract_text(response),
        )

    def follow_pdf_links(self, response, source: str, title: str = "", date: str = ""):
        """Yield Requests for every .pdf link found in the response.

        The PDF response is handled by self.parse_pdf, which receives
        title/date/source via request meta so we can store a proper item.
        """
        seen = set()
        for href in response.css("a::attr(href)").getall():
            if _PDF_HREF_RE.search(href) and href not in seen:
                seen.add(href)
                yield response.follow(
                    href,
                    callback=self.parse_pdf,
                    meta={"pdf_title": title, "pdf_date": date, "pdf_source": source},
                )

    def parse_pdf(self, response):
        """Handle a PDF response: extract text and yield a PolicyDocument."""
        from scraper.items import PolicyDocument
        from scraper.pdf_utils import extract_pdf_text, looks_like_pdf

        content_type = response.headers.get("Content-Type", b"").decode("utf-8", errors="ignore")
        if not looks_like_pdf(response.url, content_type):
            self.logger.debug("Skipping non-PDF response at %s", response.url)
            return

        text = extract_pdf_text(response.body)
        if not text:
            self.logger.warning("Empty PDF text at %s", response.url)
            return

        yield PolicyDocument(
            url=response.url,
            title=response.meta.get("pdf_title", ""),
            source=response.meta.get("pdf_source", ""),
            published_date=response.meta.get("pdf_date", ""),
            raw_html="",
            text_content=text,
        )
