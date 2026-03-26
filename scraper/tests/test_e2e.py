"""
End-to-end tests: full spider → pipeline → SQLite flow against a local
HTTP server serving fixture HTML files.  No external network required.

Each crawl runs in a subprocess (via tests/e2e/run_spider.py) so Twisted's
reactor starts fresh every time.

Run from the scraper/ directory:
  pytest tests/test_e2e.py -v
"""
import sqlite3
import subprocess
import sys
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "e2e"
RUN_SPIDER = Path(__file__).parent / "e2e" / "run_spider.py"


# ---------------------------------------------------------------------------
# Local HTTP server
# ---------------------------------------------------------------------------

class _SilentHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, directory, **kwargs):
        super().__init__(*args, directory=directory, **kwargs)

    def log_message(self, *args):
        pass


def _start_server(serve_dir: Path) -> tuple[HTTPServer, int]:
    """Serve serve_dir over HTTP on a random port; return (server, port)."""
    handler = lambda *a, **kw: _SilentHandler(*a, directory=str(serve_dir), **kw)
    server = HTTPServer(("127.0.0.1", 0), handler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, port


# ---------------------------------------------------------------------------
# Subprocess runner
# ---------------------------------------------------------------------------

def _crawl(spider_name: str, start_url: str, db_path: str) -> int:
    """Run a spider in a subprocess; return its exit code."""
    result = subprocess.run(
        [sys.executable, str(RUN_SPIDER), spider_name, start_url, db_path],
        cwd=str(RUN_SPIDER.parent.parent.parent),  # scraper/
    )
    return result.returncode


def _doc_count(db_path: str) -> int:
    return sqlite3.connect(db_path).execute(
        "SELECT COUNT(*) FROM documents"
    ).fetchone()[0]


def _all_docs(db_path: str):
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT url, title, source, published_date, text_content FROM documents ORDER BY id"
    ).fetchall()
    conn.close()
    return rows


# ---------------------------------------------------------------------------
# gov_cn end-to-end tests
# ---------------------------------------------------------------------------

class TestGovCnE2E:
    def test_crawl_stores_two_documents(self, tmp_path):
        server, port = _start_server(FIXTURES_DIR / "gov_cn")
        db_path = str(tmp_path / "policies.db")
        start_url = f"http://127.0.0.1:{port}/zhengce/zuixin/index.html"

        try:
            rc = _crawl("gov_cn", start_url, db_path)
        finally:
            server.shutdown()

        assert rc == 0, "Spider subprocess exited non-zero"
        rows = _all_docs(db_path)
        assert len(rows) == 2, f"Expected 2 docs, got {len(rows)}: {[r[0] for r in rows]}"

    def test_crawl_sets_correct_metadata(self, tmp_path):
        server, port = _start_server(FIXTURES_DIR / "gov_cn")
        db_path = str(tmp_path / "policies.db")
        start_url = f"http://127.0.0.1:{port}/zhengce/zuixin/index.html"

        try:
            _crawl("gov_cn", start_url, db_path)
        finally:
            server.shutdown()

        rows = _all_docs(db_path)
        for url, title, source, date, text in rows:
            assert source == "gov.cn", f"Wrong source on {url}"
            assert date in ("2024-03-15", "2024-02-28"), f"Wrong date on {url}"
            assert title, f"Empty title on {url}"
            assert text, f"Empty text_content on {url}"

    def test_crawl_deduplicates_on_second_run(self, tmp_path):
        server, port = _start_server(FIXTURES_DIR / "gov_cn")
        db_path = str(tmp_path / "policies.db")
        start_url = f"http://127.0.0.1:{port}/zhengce/zuixin/index.html"

        try:
            _crawl("gov_cn", start_url, db_path)
            count_1 = _doc_count(db_path)
            _crawl("gov_cn", start_url, db_path)
            count_2 = _doc_count(db_path)
        finally:
            server.shutdown()

        assert count_1 == 2
        assert count_2 == 2, f"Dedup failed: second run grew count to {count_2}"

    def test_crawl_survives_pdf_404(self, tmp_path):
        """PDF link on doc page 404s — spider must not crash and HTML docs still stored."""
        server, port = _start_server(FIXTURES_DIR / "gov_cn")
        db_path = str(tmp_path / "policies.db")
        start_url = f"http://127.0.0.1:{port}/zhengce/zuixin/index.html"

        try:
            rc = _crawl("gov_cn", start_url, db_path)
        finally:
            server.shutdown()

        assert rc == 0
        assert _doc_count(db_path) == 2
