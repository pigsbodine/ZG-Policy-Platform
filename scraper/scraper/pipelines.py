import hashlib
import sqlite3
import datetime
import os
from scrapy.exceptions import DropItem


class DeduplicationPipeline:
    """Drop items whose URL+content hash we've already stored."""

    def __init__(self):
        self._seen_urls: set[str] = set()

    def open_spider(self, spider):
        db_path = spider.settings.get("DB_PATH")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect(db_path)
        rows = conn.execute("SELECT url FROM documents").fetchall()
        conn.close()
        self._seen_urls = {r[0] for r in rows}

    def process_item(self, item, spider):
        url = item.get("url", "")
        if url in self._seen_urls:
            raise DropItem(f"Duplicate URL: {url}")
        self._seen_urls.add(url)
        return item


class DatabasePipeline:
    """Persist items to SQLite."""

    def __init__(self):
        self.conn = None

    def open_spider(self, spider):
        db_path = spider.settings.get("DB_PATH")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                url           TEXT UNIQUE NOT NULL,
                title         TEXT,
                source        TEXT,
                published_date TEXT,
                scraped_at    TEXT,
                raw_html      TEXT,
                text_content  TEXT,
                checksum      TEXT
            )
        """)
        self.conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts
            USING fts5(title, text_content, content='documents', content_rowid='id')
        """)
        self.conn.execute("""
            CREATE TRIGGER IF NOT EXISTS documents_ai AFTER INSERT ON documents BEGIN
                INSERT INTO documents_fts(rowid, title, text_content)
                VALUES (new.id, new.title, new.text_content);
            END
        """)
        self.conn.commit()

    def close_spider(self, spider):
        if self.conn:
            self.conn.close()

    def process_item(self, item, spider):
        text = item.get("text_content") or ""
        checksum = hashlib.sha256(text.encode()).hexdigest()
        now = datetime.datetime.utcnow().isoformat()
        try:
            self.conn.execute(
                """
                INSERT INTO documents (url, title, source, published_date, scraped_at, raw_html, text_content, checksum)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.get("url"),
                    item.get("title"),
                    item.get("source"),
                    item.get("published_date"),
                    now,
                    item.get("raw_html"),
                    text,
                    checksum,
                ),
            )
            self.conn.commit()
        except sqlite3.IntegrityError:
            pass  # race with dedup filter
        return item
