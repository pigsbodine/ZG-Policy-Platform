"""
Helper script invoked by e2e tests as a subprocess.

Usage:
  python tests/e2e/run_spider.py <spider_name> <start_url> <db_path>

Runs a single spider with start_urls overridden to <start_url> and
DB_PATH set to <db_path>.  Each run happens in a fresh process so
Twisted's reactor can be started cleanly.
"""
import os
import sys

# Add the scraper project to the path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import importlib
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

spider_name, start_url, db_path = sys.argv[1], sys.argv[2], sys.argv[3]

# Dynamically find the spider class by name
from scrapy.spiderloader import SpiderLoader
settings = get_project_settings()
settings.update({
    "DB_PATH": db_path,
    "LOG_LEVEL": "WARNING",
    "AUTOTHROTTLE_ENABLED": False,
    "DOWNLOAD_DELAY": 0,
    "CONCURRENT_REQUESTS": 4,
    "RETRY_TIMES": 0,
})

loader = SpiderLoader.from_settings(settings)
base_cls = loader.load(spider_name)

# Subclass to override start_urls and allowed_domains
LocalSpider = type(
    f"Local_{spider_name}",
    (base_cls,),
    {
        "name": f"local_{spider_name}",
        "start_urls": [start_url],
        "allowed_domains": ["127.0.0.1"],
    },
)

process = CrawlerProcess(settings)
process.crawl(LocalSpider)
process.start()
