<div align="center">

# ⚡ XTools

**Multi-language automation toolkit (Python, Batch, Rust) with one-liner installers & automated GitHub Releases.**

[![Release](https://img.shields.io/github/v/release/ZXD44/Xtools?style=flat-square&color=00b4d8)](https://github.com/ZXD44/Xtools/releases)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-blue?style=flat-square)](https://github.com/ZXD44/Xtools)
[![License](https://img.shields.io/github/license/ZXD44/Xtools?style=flat-square)](https://github.com/ZXD44/Xtools)

</div>

---

## 📦 Installation

### Windows (PowerShell)
```powershell
irm 'https://xtools.sh/install' | iex
```
<details>
<summary>Fallback (Direct GitHub Raw)</summary>

```powershell
irm 'https://raw.githubusercontent.com/ZXD44/XTools/main/install.ps1' | iex
```

</details>

### macOS / Linux
```bash
curl -fsSL https://xtools.sh/install.sh | bash
```
<details>
<summary>Fallback (Direct GitHub Raw)</summary>

```bash
curl -fsSL https://raw.githubusercontent.com/ZXD44/XTools/main/install.sh | bash
```

</details>

---

## 🔍 What the Installer Does
1. Fetches the latest release from GitHub Releases and prints the download URL.
2. Verifies the `SHA256` checksum of `xtools.zip` before extracting.
3. Extracts files to `%LOCALAPPDATA%\XTools` (Windows) or `~/.local/share/XTools` (Unix).
4. Adds `XTools\bin` to your **User PATH** (no admin privileges required).
5. Creates a Desktop shortcut (`XTools.lnk`) with `assets/xtools.ico` on Windows.

> Inspect the source before running: [`install.ps1`](install.ps1) | [`install.sh`](install.sh)

---

## 📌 Pinning to Taskbar (Windows)
Windows does not allow scripts to pin shortcuts to the Taskbar automatically:
1. Right-click `XTools` on your Desktop (or drag it directly onto the Taskbar).
2. Select **Pin to taskbar**.

---

## 🗑️ Uninstall

### Windows
```powershell
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\XTools"
# Remove %LOCALAPPDATA%\XTools\bin from User PATH via Environment Variables
```

### macOS / Linux
```bash
rm -rf ~/.local/share/XTools
# Remove the XTools PATH line from ~/.bashrc or ~/.zshrc
```
