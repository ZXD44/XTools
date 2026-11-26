<#
.SYNOPSIS
    XTools Deploy Script — Rolling Dev on main push, Stable Release on -Tag
.EXAMPLE
    .\deploy.ps1 -Message "fix: tweak wave speed"
    .\deploy.ps1 -Tag "v0.0.1" -Message "release: XTools v0.0.1"
#>
param(
    [string]$Message = "chore: deploy XTools update",
    [string]$Tag = ""
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

git add -u
if (Test-Path "deploy.ps1") { git add deploy.ps1 }

$status = git status --porcelain --untracked-files=no
if ($status) {
    git commit -m $Message
} else {
    Write-Host "[i] No tracked changes to commit." -ForegroundColor Yellow
}

git push origin main
$sha = (git rev-parse --short HEAD).Trim()
Write-Host "[OK] Pushed main ($sha) -> Rolling 'dev' pre-release updating." -ForegroundColor Cyan

if ($Tag) {
    git tag -f $Tag HEAD
    git push -f origin "refs/tags/$Tag"
    Write-Host "[OK] Tagged & pushed stable release: $Tag" -ForegroundColor Green
}
