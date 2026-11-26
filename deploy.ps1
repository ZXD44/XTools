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

# $ErrorActionPreference ไม่จับ exit code ของ native command — ต้องเช็คเอง
# ไม่งั้น push ล้มเหลว (เช่น network/protected branch) แต่สคริปต์ยังบอก [OK]
git push origin main
if ($LASTEXITCODE -ne 0) {
    Write-Host "[X] git push main failed (exit $LASTEXITCODE) — nothing was released." -ForegroundColor Red
    exit 1
}
$sha = (git rev-parse --short HEAD).Trim()

# workflow เฝ้าแค่ bin/, scripts/, assets/ — push ที่แตะแค่ rust/, deploy.ps1 หรือ
# .gitignore จะไม่ trigger CI เลย จึงต้องรายงานตามจริง ไม่ใช่บอกว่า 'dev กำลังอัปเดต'
$watched = @(git diff-tree --no-commit-id --name-only -r HEAD | Where-Object { $_ -match '^(bin|scripts|assets)/' })
if ($watched.Count -gt 0) {
    Write-Host "[OK] Pushed main ($sha) -> Rolling 'dev' pre-release updating ($($watched.Count) watched file(s))." -ForegroundColor Cyan
} else {
    Write-Host "[i] Pushed main ($sha), but no file under bin/, scripts/ or assets/ changed -> CI will NOT rebuild 'dev'." -ForegroundColor Yellow
}

if ($Tag) {
    git tag -f $Tag HEAD
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[X] git tag $Tag failed (exit $LASTEXITCODE)" -ForegroundColor Red
        exit 1
    }
    git push -f origin "refs/tags/$Tag"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[X] git push tag $Tag failed (exit $LASTEXITCODE) — tag exists locally only." -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] Tagged & pushed stable release: $Tag" -ForegroundColor Green
}
