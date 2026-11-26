<#
.SYNOPSIS
    XTools Auto-Deploy Script — Commit, Push main & Trigger GitHub Release
#>
param(
    [string]$Message = "chore: deploy XTools update"
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# 1. Stage tracked changes only (safe against untracked/local-only files)
git add -u
if (Test-Path "deploy.ps1") { git add deploy.ps1 }

$status = git status --porcelain --untracked-files=no
if ($status) {
    git commit -m $Message
} else {
    Write-Host "[i] No tracked changes to commit." -ForegroundColor Yellow
}

# 2. Push main (auto-triggers Release XTools workflow)
git push origin main

$sha = (git rev-parse --short HEAD).Trim()
Write-Host "[OK] Pushed main ($sha). GitHub Actions will publish v0.0.1-$sha." -ForegroundColor Cyan
