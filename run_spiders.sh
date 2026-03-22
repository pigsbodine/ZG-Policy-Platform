#!/usr/bin/env bash
# Run all spiders sequentially.
# Usage: ./run_spiders.sh
# Or run a single spider: scrapy crawl gov_cn (from scraper/ directory)

set -e

SPIDERS=(gov_cn ndrc mofcom beijing shanghai guangdong zhejiang shandong)

cd scraper

for spider in "${SPIDERS[@]}"; do
    echo "==> Running spider: $spider"
    scrapy crawl "$spider" || echo "  WARNING: $spider failed, continuing..."
done

echo "Done."
