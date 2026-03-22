"""Shared utilities for policy spiders."""
import re
from scrapy import Spider


def extract_text(response) -> str:
    """Strip scripts/styles and return visible text from a page."""
    response.selector.remove_namespaces()
    # Remove script, style, nav, footer
    for sel in response.css("script, style, nav, footer, header"):
        sel.root.getparent().remove(sel.root)
    lines = response.css("body *::text").getall()
    text = "\n".join(l.strip() for l in lines if l.strip())
    return re.sub(r"\n{3,}", "\n\n", text)


class PolicySpider(Spider):
    """Base class with common helper."""

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
