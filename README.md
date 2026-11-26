# XTools

Personal & team multi-language automation toolkit (Python, `.bat`, Rust binaries).

## Installation

### Windows (PowerShell)
```powershell
irm 'https://xtools.sh/install' | iex
```
Fallback (direct GitHub raw):
```powershell
irm 'https://raw.githubusercontent.com/ZXD44/Xtools/main/install.ps1' | iex
```

### macOS / Linux
```bash
curl -fsSL https://xtools.sh/install.sh | bash
```
Fallback (direct GitHub raw):
```bash
curl -fsSL https://raw.githubusercontent.com/ZXD44/Xtools/main/install.sh | bash
```

### What the installer does
1. Fetches the latest release from GitHub Releases and prints the download URL.
2. Verifies the `SHA256` checksum of `xtools.zip` before extracting.
3. Extracts files to `%LOCALAPPDATA%\Xtools` (Windows) or `~/.local/share/Xtools` (Unix).
4. Adds `Xtools\bin` to your **User PATH** (no admin required).
5. Creates a Desktop shortcut (`XTools.lnk`) with `assets/xtools.ico` on Windows.

Read the source before running: [`install.ps1`](install.ps1) | [`install.sh`](install.sh)

### Pinning to Taskbar (Windows)
Windows does not allow scripts to pin shortcuts to the Taskbar automatically. To pin XTools:
1. Right-click `XTools` on your Desktop (or drag it directly onto the Taskbar).
2. Select **Pin to taskbar**.

## Uninstall

### Windows
```powershell
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Xtools"
# Remove %LOCALAPPDATA%\Xtools\bin from User PATH via System Properties -> Environment Variables
```

### macOS / Linux
```bash
rm -rf ~/.local/share/Xtools
# Remove the XTools PATH line from ~/.bashrc or ~/.zshrc
```
