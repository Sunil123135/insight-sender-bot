#Requires -Version 5.1
<#
.SYNOPSIS
  Authenticate gh from git credentials, sync secrets, and trigger dry-run workflow.
#>
param(
    [string]$Repo = "Sunil123135/insight-sender-bot",
    [switch]$SkipWorkflowDispatch
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

function Get-GhPath {
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
    throw "GitHub CLI (gh) is not installed."
}

function Get-GitHubTokenFromCredentialManager {
    $git = (Get-Command git).Source
    $input = "protocol=https`nhost=github.com`n`n"
    $output = $input | & $git credential fill 2>&1
    foreach ($line in $output) {
        if ($line -match "^password=(.+)$") {
            return $Matches[1]
        }
    }
    throw "Could not read GitHub token from git credential manager."
}

$gh = Get-GhPath
$env:GH_TOKEN = Get-GitHubTokenFromCredentialManager
& $gh auth status | Out-Null

$params = @{ Repo = $Repo }
if ($SkipWorkflowDispatch) {
    $params.SkipWorkflowDispatch = $true
}
& (Join-Path $root "scripts\setup_github.ps1") @params
