<#
.SYNOPSIS
    XTools Windows Bootstrapper (install.ps1)
.DESCRIPTION
    Downloads the latest XTools release from GitHub Releases, verifies its SHA256
    checksum, extracts to $env:LOCALAPPDATA\Xtools, adds Xtools\bin to User PATH,
    and creates a Desktop shortcut.
#>

$ErrorActionPreference = 'Stop'

# ==============================================================================
# 1. Configuration
# ==============================================================================
$Repo        = if ($env:XTOOLS_REPO) { $env:XTOOLS_REPO } else { 'ZXD44/XTools' }
$InstallDir  = Join-Path $env:LOCALAPPDATA 'XTools'
$BinDir      = Join-Path $InstallDir 'bin'
$TempDir     = Join-Path $env:TEMP ('xtools-install-' + [guid]::NewGuid().ToString('N'))
$ZipPath     = Join-Path $TempDir 'xtools.zip'
$ApiUrl      = if ($env:XTOOLS_CHANNEL -eq 'dev') { "https://api.github.com/repos/$Repo/releases/tags/dev" } else { "https://api.github.com/repos/$Repo/releases/latest" }

# ANSI escape helper
$ESC   = [char]27
$CYAN  = "$ESC[96m"
$GREEN = "$ESC[92m"
$YELLOW= "$ESC[93m"
$RED   = "$ESC[91m"
$DIM   = "$ESC[90m"
$RESET = "$ESC[0m"

# ==============================================================================
# 2. Banner
# ==============================================================================
Write-Host @"
$CYAN
 __  _______ ___   ___  _     ____  
 \ \/ /_   _/ _ \ / _ \| |   / ___| 
  \  /  | || | | | | | | |   \___ \ 
  /  \  | || |_| | |_| | |___ ___) |
 /_/\_\ |_| \___/ \___/|_____|____/ 
$RESET
$DIM  Windows Installer | Repo: $Repo$RESET
"@

# ==============================================================================
# 3. Idempotency Check (Existing Installation)
# ==============================================================================
if (Test-Path $InstallDir) {
    Write-Host "${YELLOW}[!] XTools is already installed at: $InstallDir${RESET}"
    $choice = Read-Host "    Overwrite/Update existing installation? [y/N]"
    if ($choice -notmatch '^[Yy]$') {
        Write-Host "${DIM}Installation cancelled by user.${RESET}"
        exit 0
    }
}

# ==============================================================================
# 4. Runtime Check (Python / Rust)
# ==============================================================================
$hasPython = $false
try {
    $pyVer = & python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        $hasPython = $true
        Write-Host "${GREEN}[OK]${RESET} Detected $pyVer"
    }
} catch {
    $hasPython = $false
}

if (-not $hasPython) {
    Write-Host "${YELLOW}[!] Python not found in PATH.${RESET}"
    Write-Host "    Python scripts require Python 3.x: https://www.python.org/downloads/"
    Write-Host "    (Compiled Rust .exe tools in the release will still work without Python.)"
}

# ==============================================================================
# 5. Fetch Latest Release Metadata & Download
# ==============================================================================
New-Item -ItemType Directory -Path $TempDir -Force | Out-Null

try {
    Write-Host "${CYAN}[1/4]${RESET} Fetching release metadata from: $ApiUrl"
    $release = Invoke-RestMethod -Uri $ApiUrl -Headers @{ 'User-Agent' = 'XTools-Installer' }

    $zipAsset = $release.assets | Where-Object { $_.name -eq 'xtools.zip' } | Select-Object -First 1
    if (-not $zipAsset) {
        throw "Asset 'xtools.zip' not found in latest release ($($release.tag_name))."
    }

    $shaAsset = $release.assets | Where-Object { $_.name -eq 'xtools.zip.sha256' } | Select-Object -First 1

    Write-Host "${CYAN}[2/4]${RESET} Downloading from: $($zipAsset.browser_download_url)"
    $ProgressPreference = 'Continue'
    Invoke-WebRequest -Uri $zipAsset.browser_download_url -OutFile $ZipPath -UseBasicParsing

    # ==========================================================================
    # 6. SHA256 Checksum Verification
    # ==========================================================================
    $actualHash = (Get-FileHash -Path $ZipPath -Algorithm SHA256).Hash.ToLower()
    $expectedHash = $null

    if ($shaAsset) {
        Write-Host "${DIM}    Verifying against $($shaAsset.browser_download_url)...${RESET}"
        $shaContent = (Invoke-RestMethod -Uri $shaAsset.browser_download_url -UseBasicParsing).Trim()
        $expectedHash = ($shaContent -split '\s+')[0].ToLower()
    } elseif ($release.body -match '([a-fA-F0-9]{64})') {
        $expectedHash = $Matches[1].ToLower()
    }

    if ($expectedHash) {
        if ($actualHash -ne $expectedHash) {
            throw "SHA256 mismatch! Expected: $expectedHash, Got: $actualHash. Aborting."
        }
        Write-Host "${GREEN}[OK]${RESET} SHA256 verified ($actualHash)"
    } else {
        Write-Host "${YELLOW}[!] No SHA256 checksum found in release. File hash: $actualHash${RESET}"
    }

    # ==========================================================================
    # 7. Extract to $env:LOCALAPPDATA\Xtools
    # ==========================================================================
    Write-Host "${CYAN}[3/4]${RESET} Extracting to: $InstallDir"
    $StageDir = Join-Path $TempDir 'stage'
    Expand-Archive -Path $ZipPath -DestinationPath $StageDir -Force
    if (-not (Test-Path $InstallDir)) {
        New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
    }
    Copy-Item -Path (Join-Path $StageDir '*') -Destination $InstallDir -Recurse -Force

    # ==========================================================================
    # 8. Add Xtools\bin to User PATH (No Admin Required)
    # ==========================================================================
    Write-Host "${CYAN}[4/4]${RESET} Updating User PATH..."
    $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
    $pathEntries = if ($userPath) { $userPath -split ';' | Where-Object { $_ -ne '' } } else { @() }
    if ($pathEntries -notcontains $BinDir) {
        $newPath = ($pathEntries + $BinDir) -join ';'
        [Environment]::SetEnvironmentVariable('Path', $newPath, 'User')
        $env:Path = "$env:Path;$BinDir"
        Write-Host "${GREEN}[OK]${RESET} Added $BinDir to User PATH"
    } else {
        Write-Host "${DIM}    $BinDir is already in User PATH.${RESET}"
    }

    # ==========================================================================
    # 9. Create Desktop Shortcut (.lnk)
    # ==========================================================================
    $mainBat = Get-ChildItem -Path $InstallDir -Filter '*.bat' -Recurse | Select-Object -First 1
    $iconFile = Join-Path $InstallDir 'assets\xtools.ico'
    if ($mainBat) {
        $desktopPath = [Environment]::GetFolderPath('Desktop')
        $shortcutPath = Join-Path $desktopPath 'XTools.lnk'
        $wsh = New-Object -ComObject WScript.Shell
        $shortcut = $wsh.CreateShortcut($shortcutPath)
        $shortcut.TargetPath = $mainBat.FullName
        $shortcut.WorkingDirectory = $InstallDir
        if (Test-Path $iconFile) {
            $shortcut.IconLocation = $iconFile
        }
        $shortcut.Save()
        Write-Host "${GREEN}[OK]${RESET} Desktop shortcut created: $shortcutPath"
    }

    Write-Host "`n${GREEN}========================================${RESET}"
    Write-Host "${GREEN}  XTools installed successfully!${RESET}"
    Write-Host "${GREEN}  Location: $InstallDir${RESET}"
    Write-Host "${GREEN}========================================${RESET}`n"
}
catch [System.Net.WebException] {
    Write-Host "${RED}[ERROR] Network/Download failed: $($_.Exception.Message)${RESET}"
    Write-Host "Check your internet connection and verify repo '$Repo' has a published release."
    exit 1
}
catch [System.UnauthorizedAccessException] {
    Write-Host "${RED}[ERROR] Permission denied: $($_.Exception.Message)${RESET}"
    Write-Host "Ensure you have write access to $InstallDir."
    exit 1
}
catch {
    Write-Host "${RED}[ERROR] $($_.Exception.Message)${RESET}"
    exit 1
}
finally {
    if (Test-Path $TempDir) {
        Remove-Item -Path $TempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}
