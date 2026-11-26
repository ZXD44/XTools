# XTools

ชุดเครื่องมือ Automation หลายภาษา (Python, Batch, Rust) ติดตั้งง่ายในคำสั่งเดียว
Multi-language automation toolkit (Python, Batch, Rust) with one-liner installers.

[![Release](https://img.shields.io/github/v/release/ZXD44/XTools?style=flat-square&color=00b4d8)](https://github.com/ZXD44/XTools/releases)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-blue?style=flat-square)](https://github.com/ZXD44/XTools)

---

## การติดตั้ง / Installation

**Windows (PowerShell):**
```powershell
irm 'https://raw.githubusercontent.com/ZXD44/XTools/main/install.ps1' | iex
```

**macOS / Linux:**
```bash
curl -fsSL https://raw.githubusercontent.com/ZXD44/XTools/main/install.sh | bash
```

---

## การใช้งาน / Usage

| คำสั่ง / Command | คำอธิบาย / Description |
|---|---|
| `xtools` | เปิดเมนู Interactive Hub / Open Interactive Hub |
| `xtools doctor` | เช็คความพร้อมระบบ / System & environment check |
| `xtools update` | อัปเดตเวอร์ชันล่าสุด / Update to latest release |
| `xtools <tool>` | รันเครื่องมือโดยตรง / Run a tool directly |

---

## ถอนการติดตั้ง / Uninstall

**Windows:**
```powershell
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\XTools"
```

**macOS / Linux:**
```bash
rm -rf ~/.local/share/XTools
```
