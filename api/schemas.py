from pydantic import BaseModel
from typing import Optional


class DocumentSummary(BaseModel):
    id: int
    url: str
    title: Optional[str]
    source: Optional[str]
    published_date: Optional[str]
    scraped_at: Optional[str]


class DocumentDetail(DocumentSummary):
    raw_html: Optional[str]
    text_content: Optional[str]
    checksum: Optional[str]


class SearchResult(BaseModel):
    id: int
    url: str
    title: Optional[str]
    source: Optional[str]
    published_date: Optional[str]
    snippet: Optional[str]   # FTS excerpt
