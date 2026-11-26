<#
.SYNOPSIS
    XTools Windows Bootstrapper (install.ps1)
    ตัวติดตั้งและอัปเดต XTools สำหรับ Windows (ภาษาไทย + Bento Box UI)
#>

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# ==============================================================================
# 1. การตั้งค่าหลัก
# ==============================================================================
$Repo        = if ($env:XTOOLS_REPO) { $env:XTOOLS_REPO } else { 'ZXD44/XTools' }
$InstallDir  = Join-Path $env:LOCALAPPDATA 'XTools'
$BinDir      = Join-Path $InstallDir 'bin'
$TempDir     = Join-Path $env:TEMP ('xtools-install-' + [guid]::NewGuid().ToString('N'))
$ZipPath     = Join-Path $TempDir 'xtools.zip'
$ApiUrl      = if ($env:XTOOLS_CHANNEL -eq 'dev') {
    "https://api.github.com/repos/$Repo/releases/tags/dev"
} else {
    "https://api.github.com/repos/$Repo/releases/latest"
}

$ESC    = [char]27
$CYAN   = "$ESC[96m"
$BLUE   = "$ESC[94m"
$GREEN  = "$ESC[92m"
$YELLOW = "$ESC[93m"
$RED    = "$ESC[91m"
$DIM    = "$ESC[90m"
$BOLD   = "$ESC[1m"
$RESET  = "$ESC[0m"

# ==============================================================================
# 2. แบนเนอร์คลื่นน้ำ (Water Wave Gradient Banner)
# ==============================================================================
$ArtLines = @(
    " __  _______ ___   ___  _     ____  ",
    " \ \/ /_   _/ _ \ / _ \| |   / ___| ",
    "  \  /  | || | | | | | | |   \___ \ ",
    "  /  \  | || |_| | |_| | |___ ___) |",
    " /_/\_\ |_| \___/ \___/|_____|____/ "
)
Write-Host ""
for ($r = 0; $r -lt $ArtLines.Count; $r++) {
    $line = $ArtLines[$r]
    $out = ""
    for ($c = 0; $c -lt $line.Length; $c++) {
        $ch = $line[$c]
        if ($ch -eq ' ') { $out += ' '; continue }
        $v = ([Math]::Sin($c * 0.22 + $r * 0.65) + 1.0) * 0.5
        $cr = [Math]::Pow($v, 2.2)
        $Rcol = [Math]::Min(255, [int](10 + $cr * 200))
        $Gcol = [Math]::Min(255, [int](90 + $v * 150))
        $Bcol = [Math]::Min(255, [int](180 + $v * 75))
        $out += "$ESC[38;2;${Rcol};${Gcol};${Bcol}m${BOLD}${ch}"
    }
    Write-Host "${out}${RESET}"
}
Write-Host "  ${CYAN}XTools ตัวติดตั้ง Windows${RESET} ${DIM}|${RESET} ${RED}${BOLD}ZXD44${RESET}${DIM}/XTools${RESET}`n"

# ==============================================================================
# 3. ตรวจสอบเวอร์ชันปัจจุบัน & ดึงเวอร์ชันใหม่จาก GitHub
# ==============================================================================
$localVer = "ยังไม่ได้ติดตั้ง"
$constFile = Join-Path $InstallDir 'scripts\config\constants.py'
if (Test-Path $constFile) {
    $rawConst = Get-Content $constFile -Raw -ErrorAction SilentlyContinue
    $vMatch = if ($rawConst -match 'VERSION\s*=\s*"([^"]+)"') { $Matches[1] } else { "0.0.1" }
    $bMatch = if ($rawConst -match 'BUILD\s*=\s*"([^"]+)"') { $Matches[1] } else { "" }
    $localVer = if ($bMatch) { "v$vMatch ($bMatch)" } else { "v$vMatch" }
}

try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Write-Host "${CYAN}[1/4]${RESET} กำลังตรวจสอบเวอร์ชันล่าสุดจาก GitHub..."
    $headers = @{ 'User-Agent' = 'XTools-Installer' }
    $release = Invoke-RestMethod -Uri $ApiUrl -Headers $headers -UseBasicParsing
    $rawTag = $release.tag_name
    $shortSha = if ($release.target_commitish -match '^[0-9a-fA-F]{7,40}$') {
        $release.target_commitish.Substring(0, 7)
    } else {
        try {
            $cInfo = Invoke-RestMethod -Uri "https://api.github.com/repos/$Repo/commits/main" -Headers $headers -UseBasicParsing
            $cInfo.sha.Substring(0, 7)
        } catch { "" }
    }
    $baseVer = if ($rawTag -eq 'dev') { if ($vMatch) { "v$vMatch" } else { "v0.0.2" } } else { $rawTag }
    $newVer = if ($shortSha) { "$baseVer ($shortSha)" } else { $baseVer }

    if (Test-Path $InstallDir) {
        Write-Host ""
        Write-Host "${BOLD}┌── [ ตรวจพบการติดตั้งเดิม ] ────────────────────────────┐${RESET}"
        Write-Host "│  ${DIM}ตำแหน่งติดตั้ง :${RESET} $InstallDir"
        Write-Host "│  ${YELLOW}เวอร์ชันเดิม   :${RESET} $localVer"
        Write-Host "│  ${GREEN}เวอร์ชันใหม่   :${RESET} ${BOLD}$newVer${RESET}"
        Write-Host "${BOLD}└─────────────────────────────────────────────────────────┘${RESET}"
        $choice = Read-Host "  ต้องการอัปเดตเป็นเวอร์ชันใหม่หรือไม่? [y/N]"
        if ($choice -notmatch '^[Yy]$') {
            Write-Host "${DIM}  ยกเลิกการอัปเดตเรียบร้อย${RESET}"
            exit 0
        }
    }

    # ==========================================================================
    # 4. ตรวจสอบ Runtime (Python)
    # ==========================================================================
    $pyCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pyCmd) {
        $pyVer = (& python --version 2>&1) -join ' '
        Write-Host "${GREEN}[OK]${RESET} ตรวจพบ $pyVer"
    } else {
        Write-Host "${YELLOW}[!] ไม่พบ Python ใน PATH (จำเป็นสำหรับรัน Hub)${RESET}"
    }

    # ==========================================================================
    # 5. ดาวน์โหลดและตรวจสอบ SHA256
    # ==========================================================================
    $zipAsset = $release.assets | Where-Object { $_.name -eq 'xtools.zip' } | Select-Object -First 1
    if (-not $zipAsset) {
        throw "ไม่พบไฟล์ 'xtools.zip' ใน Release ($newVer)"
    }

    New-Item -ItemType Directory -Path $TempDir -Force | Out-Null
    Write-Host "${CYAN}[2/4]${RESET} กำลังดาวน์โหลด ${BOLD}$newVer${RESET}..."
    Invoke-WebRequest -Uri $zipAsset.browser_download_url -OutFile $ZipPath -Headers $headers -UseBasicParsing

    $actualHash = (Get-FileHash -Path $ZipPath -Algorithm SHA256).Hash.ToLower()
    $expectedHash = $null
    $shaAsset = $release.assets | Where-Object { $_.name -eq 'xtools.zip.sha256' } | Select-Object -First 1
    if ($shaAsset) {
        $shaContent = (Invoke-RestMethod -Uri $shaAsset.browser_download_url -UseBasicParsing).Trim()
        $expectedHash = ($shaContent -split '\s+')[0].ToLower()
    } elseif ($release.body -match '([a-fA-F0-9]{64})') {
        $expectedHash = $Matches[1].ToLower()
    }

    if ($expectedHash) {
        if ($actualHash -ne $expectedHash) {
            throw "SHA256 ไม่ตรงกัน! (คาดหวัง: $expectedHash, ได้รับ: $actualHash)"
        }
        Write-Host "${GREEN}[OK]${RESET} ตรวจสอบ SHA256 ผ่าน ($($actualHash.Substring(0,16))...)"
    }

    # ==========================================================================
    # 6. แตกไฟล์และอัปเดตทับอย่างปลอดภัย
    # ==========================================================================
    Write-Host "${CYAN}[3/4]${RESET} กำลังติดตั้งไปยัง: $InstallDir"
    $StageDir = Join-Path $TempDir 'stage'
    Expand-Archive -Path $ZipPath -DestinationPath $StageDir -Force
    if (-not (Test-Path $InstallDir)) {
        New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
    }
    # Windows ล็อก .exe ที่กำลังรันอยู่ แต่ยอมให้ Move/Rename ได้
    $runningExe = Join-Path $BinDir 'xtools.exe'
    $oldExe = Join-Path $BinDir 'xtools.exe.old'
    if (Test-Path $oldExe) { Remove-Item -Path $oldExe -Force -ErrorAction SilentlyContinue }
    if (Test-Path $runningExe) {
        Move-Item -Path $runningExe -Destination $oldExe -Force -ErrorAction SilentlyContinue
    }
    Copy-Item -Path (Join-Path $StageDir '*') -Destination $InstallDir -Recurse -Force

    # ==========================================================================
    # 7. อัปเดต User PATH & Desktop Shortcut
    # ==========================================================================
    Write-Host "${CYAN}[4/4]${RESET} กำลังอัปเดต User PATH และทางลัด..."
    $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
    $pathEntries = if ($userPath) { $userPath -split ';' | Where-Object { $_ -ne '' } } else { @() }
    if ($pathEntries -notcontains $BinDir) {
        [Environment]::SetEnvironmentVariable('Path', (($pathEntries + $BinDir) -join ';'), 'User')
        $env:Path = "$env:Path;$BinDir"
        Write-Host "${GREEN}[OK]${RESET} เพิ่ม $BinDir ลงใน User PATH แล้ว"
    }

    $mainBat = Get-ChildItem -Path $InstallDir -Filter '*.bat' -Recurse | Select-Object -First 1
    $iconFile = Join-Path $InstallDir 'assets\xtools.ico'
    if ($mainBat) {
        $shortcutPath = Join-Path ([Environment]::GetFolderPath('Desktop')) 'XTools.lnk'
        $wsh = New-Object -ComObject WScript.Shell
        $shortcut = $wsh.CreateShortcut($shortcutPath)
        $shortcut.TargetPath = $mainBat.FullName
        $shortcut.WorkingDirectory = $InstallDir
        if (Test-Path $iconFile) { $shortcut.IconLocation = $iconFile }
        $shortcut.Save()
    }

    Write-Host ""
    Write-Host "${GREEN}${BOLD}┌── [ ติดตั้ง / อัปเดต XTools สำเร็จ ] ───────────────────┐${RESET}"
    Write-Host "${GREEN}│${RESET}  เวอร์ชัน : ${BOLD}$newVer${RESET}"
    Write-Host "${GREEN}│${RESET}  ตำแหน่ง  : $InstallDir"
    Write-Host "${GREEN}│${RESET}  คำสั่ง   : พิมพ์ ${CYAN}xtools${RESET} เพื่อเปิดใช้งาน"
    Write-Host "${GREEN}${BOLD}└─────────────────────────────────────────────────────────┘${RESET}`n"
}
catch [System.Net.WebException] {
    Write-Host "${RED}[ผิดพลาด] ดาวน์โหลดไม่สำเร็จ: $($_.Exception.Message)${RESET}"
    exit 1
}
catch [System.UnauthorizedAccessException] {
    Write-Host "${RED}[ผิดพลาด] ไม่มีสิทธิ์เขียนไฟล์ที่ $InstallDir${RESET}"
    exit 1
}
catch {
    Write-Host "${RED}[ผิดพลาด] $($_.Exception.Message)${RESET}"
    exit 1
}
finally {
    if (Test-Path $TempDir) {
        Remove-Item -Path $TempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}
