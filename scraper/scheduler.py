"""
Daily spider scheduler.

Reads configuration from environment variables:

  SCRAPE_TIME        HH:MM (UTC) at which to run all spiders each day.
                     Default: "02:00"

  SCRAPE_INTERVAL_HOURS
                     If set, run every N hours instead of once daily.
                     Takes precedence over SCRAPE_TIME.

  RUN_ON_START       Set to "1" to run all spiders immediately at startup,
                     before the first scheduled run. Useful for first-time
                     setup. Default: "0"

Usage (from project root):
  docker compose up            # starts API + scheduler together
  docker compose up scheduler  # scheduler only
"""
import logging
import os
import subprocess
import sys
import time

import schedule

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [scheduler] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
    force=True,
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SPIDERS = [
    "gov_cn",
    "ndrc",
    "mofcom",
    "beijing",
    "shanghai",
    "guangdong",
    "zhejiang",
    "shandong",
]

# Spiders run from this directory (the scrapy project root)
SCRAPY_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# Core runner
# ---------------------------------------------------------------------------

def run_spiders():
    """Run every spider sequentially; log summary when done."""
    logger.info("=== Crawl run starting ===")
    succeeded, failed = [], []

    for spider in SPIDERS:
        logger.info("Starting spider: %s", spider)
        result = subprocess.run(
            ["scrapy", "crawl", spider],
            cwd=SCRAPY_PROJECT_DIR,
        )
        if result.returncode == 0:
            succeeded.append(spider)
            logger.info("Spider %s finished OK", spider)
        else:
            failed.append(spider)
            logger.warning("Spider %s exited with code %d", spider, result.returncode)

    logger.info(
        "=== Crawl run complete: %d OK, %d failed (%s) ===",
        len(succeeded),
        len(failed),
        ", ".join(failed) if failed else "none",
    )


# ---------------------------------------------------------------------------
# Schedule setup
# ---------------------------------------------------------------------------

def setup_schedule():
    """Register jobs on the global schedule based on env vars.

    Separated from the main loop so tests can call it and inspect jobs
    without starting an infinite loop.
    """
    scrape_time = os.getenv("SCRAPE_TIME", "02:00")
    interval_hours = os.getenv("SCRAPE_INTERVAL_HOURS", "")

    schedule.clear()

    if interval_hours:
        try:
            hours = int(interval_hours)
            schedule.every(hours).hours.do(run_spiders)
            logger.info("Scheduler: running every %d hour(s).", hours)
        except ValueError:
            logger.error(
                "SCRAPE_INTERVAL_HOURS must be an integer; got %r. Falling back to daily.",
                interval_hours,
            )
            schedule.every().day.at(scrape_time).do(run_spiders)
            logger.info("Scheduler: daily run at %s UTC.", scrape_time)
    else:
        schedule.every().day.at(scrape_time).do(run_spiders)
        logger.info("Scheduler: daily run at %s UTC.", scrape_time)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    setup_schedule()

    if os.getenv("RUN_ON_START", "0") == "1":
        logger.info("RUN_ON_START=1 — running spiders now before first scheduled run.")
        run_spiders()

    logger.info("Scheduler waiting. Next run: %s", schedule.next_run())

    while True:
        schedule.run_pending()
        time.sleep(30)
