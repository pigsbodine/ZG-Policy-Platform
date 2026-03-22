"""
China Policy Platform — FastAPI
================================
Endpoints:
  GET  /documents          List documents (paginated, filter by source/date)
  GET  /documents/{id}     Full document detail (includes raw_html, text_content)
  GET  /search             Full-text search over title + text_content
  GET  /sources            List distinct sources with document counts
  GET  /health             Health check
"""

from fastapi import FastAPI, HTTPException, Query
from typing import Optional
from api.database import db
from api.schemas import DocumentSummary, DocumentDetail, SearchResult

app = FastAPI(title="ZG Policy Platform", version="1.0.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/sources")
def list_sources():
    with db() as conn:
        rows = conn.execute(
            "SELECT source, COUNT(*) as count FROM documents GROUP BY source ORDER BY count DESC"
        ).fetchall()
    return [{"source": r["source"], "count": r["count"]} for r in rows]


@app.get("/documents", response_model=list[DocumentSummary])
def list_documents(
    source: Optional[str] = None,
    from_date: Optional[str] = Query(None, description="ISO date, e.g. 2024-01-01"),
    to_date: Optional[str] = Query(None, description="ISO date, e.g. 2024-12-31"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    conditions = []
    params: list = []

    if source:
        conditions.append("source = ?")
        params.append(source)
    if from_date:
        conditions.append("published_date >= ?")
        params.append(from_date)
    if to_date:
        conditions.append("published_date <= ?")
        params.append(to_date)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    offset = (page - 1) * page_size

    with db() as conn:
        rows = conn.execute(
            f"""
            SELECT id, url, title, source, published_date, scraped_at
            FROM documents
            {where}
            ORDER BY scraped_at DESC
            LIMIT ? OFFSET ?
            """,
            params + [page_size, offset],
        ).fetchall()

    return [dict(r) for r in rows]


@app.get("/documents/{doc_id}", response_model=DocumentDetail)
def get_document(doc_id: int):
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM documents WHERE id = ?", (doc_id,)
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Document not found")
    return dict(row)


@app.get("/search", response_model=list[SearchResult])
def search(
    q: str = Query(..., min_length=1, description="Search query"),
    source: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """Full-text search using SQLite FTS5."""
    offset = (page - 1) * page_size

    source_filter = "AND d.source = ?" if source else ""
    params: list = [q, q]
    if source:
        params.append(source)
    params += [page_size, offset]

    with db() as conn:
        rows = conn.execute(
            f"""
            SELECT
                d.id,
                d.url,
                d.title,
                d.source,
                d.published_date,
                snippet(documents_fts, 1, '<b>', '</b>', '…', 32) AS snippet
            FROM documents_fts
            JOIN documents d ON d.id = documents_fts.rowid
            WHERE documents_fts MATCH ?
              AND rank MATCH 'bm25(10.0, 1.0)'
              {source_filter}
            ORDER BY rank
            LIMIT ? OFFSET ?
            """,
            params,
        ).fetchall()

    return [dict(r) for r in rows]
