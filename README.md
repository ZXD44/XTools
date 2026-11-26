<div align="center">

# ⚡ XTools

**ชุดเครื่องมือ Automation หลายภาษา (Python, Batch, Rust) ติดตั้งง่ายในคำสั่งเดียว พร้อมระบบ Auto-Release**

[![Release](https://img.shields.io/github/v/release/ZXD44/Xtools?style=flat-square&color=00b4d8)](https://github.com/ZXD44/Xtools/releases)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-blue?style=flat-square)](https://github.com/ZXD44/Xtools)
[![License](https://img.shields.io/github/license/ZXD44/Xtools?style=flat-square)](https://github.com/ZXD44/Xtools)

</div>

---

## 📦 การติดตั้ง (Installation)

### Windows (PowerShell)
```powershell
irm 'https://raw.githubusercontent.com/ZXD44/XTools/main/install.ps1' | iex
```

### macOS / Linux
```bash
curl -fsSL https://raw.githubusercontent.com/ZXD44/XTools/main/install.sh | bash
```

> ตรวจสอบโค้ดก่อนรัน: [`install.ps1`](install.ps1) | [`install.sh`](install.sh)

---

## 🚀 การใช้งาน (Usage)

เปิดใช้งานได้ 2 วิธี:
- ดับเบิลคลิกไอคอน **XTools** บน Desktop
- หรือพิมพ์คำสั่งใน Terminal:

| คำสั่ง | ความหมาย |
|---|---|
| `xtools` | เปิดหน้าเมนู Interactive Hub |
| `xtools doctor` | เช็คความพร้อมของระบบ (Python, Git, Rust, Node, PATH, Disk) |
| `xtools update` | อัปเดต XTools เป็นเวอร์ชันล่าสุด |
| `xtools <ชื่อเครื่องมือ>` | รันเครื่องมือนั้นโดยตรง |

---

## 🔍 สิ่งที่ตัวติดตั้งทำให้อัตโนมัติ
1. ดึง release ล่าสุดจาก GitHub พร้อมแสดง URL ที่ดาวน์โหลด
2. ตรวจสอบความถูกต้องของไฟล์ด้วย **SHA256** ก่อนแตกไฟล์
3. แตกไฟล์ไปที่ `%LOCALAPPDATA%\XTools` (Windows) หรือ `~/.local/share/XTools` (macOS/Linux)
4. เพิ่ม `XTools\bin` เข้า **User PATH** (ไม่ต้องใช้สิทธิ์ Admin)
5. สร้าง Desktop Shortcut (`XTools.lnk`) พร้อมไอคอน `assets/xtools.ico`

---

## 📌 ปักหมุดขึ้น Taskbar (Windows)
Windows ไม่อนุญาตให้ script ปักหมุด Taskbar อัตโนมัติ — ทำได้โดยคลิกขวาที่ไอคอน `XTools` บน Desktop แล้วเลือก **Pin to taskbar**

---

## 🚢 การ Deploy / ออก Release ใหม่
ทุกครั้งที่แก้ไขโค้ดเสร็จ ให้ push tag เวอร์ชันใหม่:
```bash
git add -A
git commit -m "feat: update tools"
git push origin main
git tag v1.2.0
git push origin v1.2.0
```
GitHub Actions (`.github/workflows/release.yml`) จะแพ็ก `xtools.zip` + `xtools.zip.sha256` และสร้าง Release ให้อัตโนมัติ

---

## 🗑️ การถอนการติดตั้ง (Uninstall)

**Windows (PowerShell):**
```powershell
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\XTools"
```
*(จากนั้นลบ `%LOCALAPPDATA%\XTools\bin` ออกจาก User PATH ใน Environment Variables)*

**macOS / Linux:**
```bash
rm -rf ~/.local/share/XTools
```
*(จากนั้นลบบรรทัด PATH ของ XTools ใน `~/.bashrc` หรือ `~/.zshrc`)*
