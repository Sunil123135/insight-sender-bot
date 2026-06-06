# Test Apify run-sync-get-dataset-items with curl (same API pattern as ScrapeSignal).
#
# Usage:
#   $env:APIFY_API_TOKEN = "apify_api_..."
#   .\scripts\test_apify_curl.ps1
#   .\scripts\test_apify_curl.ps1 -SourceUrl "https://www.supplychaindive.com"

param(
    [string]$SourceUrl = "https://www.supplychaindive.com",
    [string]$ActorId = "apify~website-content-crawler"
)

$ErrorActionPreference = "Stop"
$token = $env:APIFY_API_TOKEN
if ([string]::IsNullOrWhiteSpace($token)) {
    throw "Set APIFY_API_TOKEN first."
}

$body = @{
    startUrls      = @(@{ url = $SourceUrl })
    maxCrawlPages  = 5
    maxCrawlDepth  = 1
} | ConvertTo-Json -Compress

$url = "https://api.apify.com/v2/acts/$ActorId/run-sync-get-dataset-items?clean=true&timeout=300"
Write-Host "Running Apify actor $ActorId for $SourceUrl ..."

curl.exe -X POST -d $body `
    -H "Content-Type: application/json" `
    -H "Authorization: Bearer $token" `
    -L $url
