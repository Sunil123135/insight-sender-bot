#!/usr/bin/env bash
# Test Apify run-sync-get-dataset-items with curl (same API pattern as ScrapeSignal).
#
# Usage:
#   export APIFY_API_TOKEN="apify_api_..."
#   ./scripts/test_apify_curl.sh
#   ./scripts/test_apify_curl.sh "https://www.supplychaindive.com"

set -euo pipefail

TOKEN="${APIFY_API_TOKEN:-}"
SOURCE_URL="${1:-https://www.supplychaindive.com}"
ACTOR_ID="${APIFY_ACTOR_ID:-apify~website-content-crawler}"

if [[ -z "$TOKEN" ]]; then
  echo "Set APIFY_API_TOKEN first." >&2
  exit 1
fi

echo "Running Apify actor ${ACTOR_ID} for ${SOURCE_URL} ..."

echo "{\"startUrls\":[{\"url\":\"${SOURCE_URL}\"}],\"maxCrawlPages\":5,\"maxCrawlDepth\":1}" |
curl -X POST -d @- \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -L "https://api.apify.com/v2/acts/${ACTOR_ID}/run-sync-get-dataset-items?clean=true&timeout=300"
