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

# ต้องใช้ -A เพื่อเก็บ "ไฟล์ใหม่" ด้วย (เช่น scripts/dev/<tool> ที่เพิ่งสร้าง)
# เดิมใช้ git add -u ซึ่งข้าม untracked files ทำให้ tool ใหม่ไม่ถูก deploy
# ถ้าไม่มีไฟล์ใน pathspec ให้ข้ามไปไม่ให้ git ล้ม
foreach ($p in @('scripts', 'bin', 'assets', 'docs', 'rust', '.github', '.agent', 'README.md', 'install.ps1', 'install.sh', 'deploy.ps1')) {
    if (Test-Path $p) { git add -A -- $p }
}

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
