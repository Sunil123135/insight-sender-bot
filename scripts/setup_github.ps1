#Requires -Version 5.1
<#
.SYNOPSIS
  Configure GitHub Actions secrets and trigger the first dry-run workflow.
.DESCRIPTION
  Reads values from .env and pushes them to the repository's GitHub Actions secrets.
  Requires GitHub CLI (gh) authenticated: gh auth login
#>
param(
    [string]$Repo = "",
    [switch]$SkipWorkflowDispatch
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

function Get-GhPath {
    $root = Split-Path -Parent $PSScriptRoot
    $candidates = @(
        (Join-Path $root ".tools\bin\gh.exe"),
        "C:\Program Files\GitHub CLI\gh.exe",
        "$env:LOCALAPPDATA\Programs\GitHub CLI\gh.exe"
    )
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) { return $candidate }
    }
    $fromPath = Get-Command gh -ErrorAction SilentlyContinue
    if ($fromPath) { return $fromPath.Source }
    throw "GitHub CLI (gh) is not installed. Install from https://cli.github.com/ then run: gh auth login"
}

function Read-DotEnvValue {
    param([string]$Name)
    $line = Get-Content ".env" | Where-Object { $_ -match "^$Name=" } | Select-Object -First 1
    if (-not $line) { return "" }
    return ($line -replace "^$Name=", "").Trim('"')
}

$gh = Get-GhPath
& $gh auth status 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "GitHub CLI is not authenticated. Run: gh auth login"
}

if (-not $Repo) {
    $remote = git remote get-url origin 2>$null
    if ($remote) {
        if ($remote -match "github\.com[:/](.+?)(?:\.git)?$") {
            $Repo = $Matches[1]
        }
    }
}
if (-not $Repo) {
    throw "Pass -Repo owner/name or add a git remote first."
}

$neonPooled = npx --yes neonctl connection-string production `
    --project-id wispy-cloud-93669868 --pooled 2>$null
if ($neonPooled) {
    $databaseUrl = $neonPooled -replace "^postgresql://", "postgresql+psycopg://"
    $databaseUrl = ($databaseUrl -split "&channel_binding")[0]
} else {
    $databaseUrl = Read-DotEnvValue "DATABASE_URL"
}

$secretMap = [ordered]@{
    DATABASE_URL               = $databaseUrl
    JINA_API_KEY               = Read-DotEnvValue "JINA_API_KEY"
    APIFY_API_TOKEN            = Read-DotEnvValue "APIFY_API_TOKEN"
    GROQ_API_KEY               = Read-DotEnvValue "GROQ_API_KEY"
    GEMINI_API_KEY             = Read-DotEnvValue "GEMINI_API_KEY"
    POWER_AUTOMATE_WEBHOOK_URL = Read-DotEnvValue "POWER_AUTOMATE_WEBHOOK_URL"
    SLACK_WEBHOOK_URL          = Read-DotEnvValue "SLACK_WEBHOOK_URL"
}

Write-Host "Configuring secrets for $Repo ..."
foreach ($entry in $secretMap.GetEnumerator()) {
    if ([string]::IsNullOrWhiteSpace($entry.Value)) {
        Write-Host "Skipping empty secret: $($entry.Key)"
        continue
    }
    $entry.Value | & $gh secret set $entry.Key --repo $Repo
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to set secret $($entry.Key)"
    }
    Write-Host "Set $($entry.Key)"
}

if (-not $SkipWorkflowDispatch) {
    Write-Host "Triggering workflow dispatch (dry_run=true) ..."
    & $gh workflow run "daily-scrape.yml" --repo $Repo -f dry_run=true
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to trigger daily-scrape workflow"
    }
    Write-Host "Monitor with: gh run list --repo $Repo --workflow=daily-scrape.yml"
}
