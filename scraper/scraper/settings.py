import os

BOT_NAME = "scraper"
SPIDER_MODULES = ["scraper.spiders"]
NEWSPIDER_MODULE = "scraper.spiders"

# These are public government transparency portals; robots.txt often blocks
# all bots but the content is meant to be publicly accessible.
ROBOTSTXT_OBEY = False
CONCURRENT_REQUESTS = 2
CONCURRENT_REQUESTS_PER_DOMAIN = 1

# AutoThrottle adjusts delay based on server response times, so we don't
# hammer a single server.
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 2
AUTOTHROTTLE_MAX_DELAY = 30
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
AUTOTHROTTLE_DEBUG = False

DOWNLOAD_DELAY = 2
RANDOMIZE_DOWNLOAD_DELAY = True
DOWNLOAD_TIMEOUT = 30

# Retry on transient errors
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# Cookies not needed and can cause tracking issues
COOKIES_ENABLED = False

# Browser-like headers to reduce block rate
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Cache-Control": "max-age=0",
}

# Pipeline
ITEM_PIPELINES = {
    "scraper.pipelines.DeduplicationPipeline": 100,
    "scraper.pipelines.DatabasePipeline": 200,
}

# SQLite path (override via env DB_PATH)
DB_PATH = os.getenv("DB_PATH", "../data/policies.db")

# HTTP cache — speeds up development runs; disable in production cron jobs
HTTPCACHE_ENABLED = os.getenv("SCRAPY_CACHE", "0") == "1"
HTTPCACHE_EXPIRATION_SECS = 86400
HTTPCACHE_IGNORE_HTTP_CODES = [403, 404, 500, 503]
HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Logging
LOG_LEVEL = "INFO"

# Telnet console off (not needed)
TELNETCONSOLE_ENABLED = False
