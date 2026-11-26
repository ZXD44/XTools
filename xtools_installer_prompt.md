# Xtools Installer — Full Build Prompt

> ใช้ไฟล์นี้เป็น prompt เดียวจบ ส่งให้ AI (Claude Code, Cursor ฯลฯ) เพื่อสร้างระบบ installer ทั้งหมดของโปรเจค Xtools

---

## 🎯 บริบทโปรเจค

- **ชื่อโปรเจค:** Xtools
- **เนื้อหา:** ชุด automation scripts หลายภาษา (Python, `.bat`, และสามารถขยายไปถึง Rust หรือภาษาอื่นได้ในอนาคต — แต่ละโปรเจคย่อยอาจใช้คนละ runtime) ที่ใช้งานส่วนตัว/ทีม
- **เป้าหมาย:** ให้คนติดตั้งได้ด้วยคำสั่งเดียวแบบ one-liner คล้าย
  ```powershell
  irm 'https://cursor.com/install?win32=true' | iex
  ```
- **โฮสต์:** GitHub (`github.com/<user>/Xtools`)
- **แพลตฟอร์มเป้าหมาย:** Windows (หลัก), macOS/Linux (รอง)

---

## 📦 สิ่งที่ต้องการให้สร้างทั้งหมด

### 1. `install.ps1` — Windows PowerShell Bootstrapper

หน้าที่:
- ดาวน์โหลด release ล่าสุดจาก GitHub Releases ของ repo (zip ที่รวม python scripts + `.bat` files)
- เช็คว่าเครื่องมี Python ติดตั้งหรือยัง (`python --version`) — ถ้าไม่มี แจ้งเตือนพร้อมลิงก์ติดตั้งที่ python.org
- ถ้ามีโปรเจคย่อยที่เป็น Rust (แจกเป็น compiled binary ใน release ไม่ใช่ source) ให้ข้ามการเช็ค runtime และแค่แตกไฟล์ `.exe` ไปวางในโฟลเดอร์เดียวกัน
- แตกไฟล์ไปที่ `$env:LOCALAPPDATA\Xtools`
- เพิ่ม `Xtools\bin` เข้า **User PATH** (ไม่แตะ System PATH เพื่อไม่ต้องขอสิทธิ์ admin)
- สร้าง Desktop shortcut (`.lnk`) ชี้ไปยังไฟล์ `.bat` หลัก พร้อมไอคอนที่กำหนดเอง
- แสดงผลสวยงามด้วย ANSI escape codes:
  - ASCII art banner ชื่อ "XTOOLS" ตอนเริ่ม
  - Progress indicator ระหว่างดาวน์โหลด/แตกไฟล์
  - ข้อความสำเร็จสีเขียวตอนจบ พร้อมสรุปว่าไฟล์ไปอยู่ที่ไหน
- Error handling ครบ:
  - ดาวน์โหลดล้มเหลว (network/404)
  - ไม่มีสิทธิ์เขียนไฟล์
  - Python ไม่พบ
  - แต่ละกรณีบอกผู้ใช้ชัดเจนว่าต้องทำอะไรต่อ

### 2. `install.sh` — macOS/Linux Bootstrapper

- Logic เดียวกับข้อ 1 แต่ใช้ `curl` + `tar`/`unzip`
- แตกไฟล์ไปที่ `~/.local/share/Xtools`
- เพิ่ม `~/.local/share/Xtools/bin` เข้า `PATH` ผ่าน `.bashrc`/`.zshrc` (เช็ค shell ปัจจุบันก่อนแก้)
- ใช้ ANSI colors (`tput` หรือ raw escape codes) ให้ feel เดียวกับฝั่ง Windows

### 3. `.github/workflows/release.yml` — Auto Release Workflow

- Trigger: เมื่อ push tag ใหม่ (เช่น `v1.0.0`)
- ขั้นตอน:
  1. Checkout code
  2. Build/package scripts ทั้งหมดเป็น `xtools.zip`
  3. แนบ zip เป็น GitHub Release asset โดยอัตโนมัติ (ใช้ `softprops/action-gh-release` หรือเทียบเท่า)
- ไม่ require secrets เพิ่มเติมนอกจาก `GITHUB_TOKEN` ที่มีให้อัตโนมัติ

### 4. `README.md` — ส่วน Installation

ต้องมี:
- คำสั่งติดตั้งแบบ copy-paste ได้ทันที โดยใช้ลิงก์แบบสั้น (short domain) แทน raw.githubusercontent.com ที่ยาว เช่น ตั้ง custom domain หรือใช้ GitHub Pages redirect (`xtools.sh/install` หรือ `get.xtools.dev`) ที่ proxy ไปยังไฟล์ script จริงใน repo:
  ```powershell
  irm 'https://xtools.sh/install' | iex
  ```
  ```bash
  curl -fsSL https://xtools.sh/install.sh | bash
  ```
  (ด้านล่างของ README ให้ระบุ fallback เป็นลิงก์ raw.githubusercontent.com เต็มๆ ไว้ด้วย เผื่อ short domain ล่ม)
- ขั้นตอน/คำแนะนำสำหรับทำ **Desktop/Taskbar shortcut ไอคอนเท่ๆ** หลังติดตั้งเสร็จ:
  - ให้ installer สร้างไฟล์ `.ico` ของ Xtools เอง (วางไว้ใน repo ที่ `assets/xtools.ico`) แล้วผูกกับ shortcut `.lnk` ที่สร้างใน `install.ps1`
  - แนะนำขนาดไอคอนมาตรฐาน (256x256, multi-resolution .ico) เพื่อให้คมชัดทั้งบน Desktop และ Taskbar
  - ถ้า pin ขึ้น Taskbar ต้องให้คำแนะนำผู้ใช้ลาก shortcut ไป pin เอง (Windows ไม่อนุญาตให้ script pin Taskbar อัตโนมัติโดยไม่ผ่าน user action)
- คำอธิบายสั้นๆ ว่า script ทำอะไรบ้าง (ดาวน์โหลด, แตกไฟล์, เพิ่ม PATH, สร้าง shortcut) — เพื่อความโปร่งใส ให้คนอ่านก่อนรันได้
- ลิงก์ตรงไปที่ไฟล์ `install.ps1` / `install.sh` ใน repo เผื่อใครอยากอ่านซอร์สก่อน
- หัวข้อ "Uninstall" บอกวิธีลบ (ลบโฟลเดอร์ + เอา PATH entry ออก)

### 5. (ตัวเลือกเสริม) GUI Installer

- ใช้ **Python + customtkinter**
- หน้าต่างมี: โลโก้ Xtools, ปุ่ม "Install", progress bar แบบ real-time, ปุ่ม "Open Folder" หลังเสร็จ
- คอมไพล์เป็น `.exe` เดียวด้วย **PyInstaller** เพื่อให้ non-technical user ดับเบิลคลิกรันได้โดยไม่ต้องมี Python ติดตั้งมาก่อน
- ใช้ logic ดาวน์โหลด/แตกไฟล์เดียวกับ `install.ps1` (เขียนเป็น Python function แยก เพื่อ reuse ได้)

---

## 🔒 ข้อกำหนดด้านความปลอดภัย/คุณภาพ (บังคับทุกไฟล์)

- ❌ ห้าม hardcode credentials, token, API key ใดๆ ใน script
- ✅ Script ต้อง **idempotent** — รันซ้ำได้โดยไม่พัง ถ้าเจอว่าติดตั้งอยู่แล้วให้ถาม overwrite หรือ update
- ✅ แสดง URL ปลายทางที่กำลังดาวน์โหลดให้ผู้ใช้เห็นเสมอ ไม่ซ่อนไว้เบื้องหลัง
- ✅ Comment อธิบายทุก section ว่าทำอะไร เพื่อให้คนอื่น audit โค้ดได้ง่าย
- ✅ ตรวจ checksum (SHA256) ของไฟล์ที่ดาวน์โหลดมา เทียบกับค่าที่ publish ไว้ใน release notes ก่อนแตกไฟล์
- ✅ ไม่ execute โค้ดใดๆ แบบ remote โดยไม่ผ่านการดาวน์โหลดเป็นไฟล์ก่อน (bootstrapper ทำหน้าที่แค่ "ติดตั้ง" ไม่ใช่รัน business logic ผ่าน pipe โดยตรง)

---

## ✅ ลำดับการทำงานที่ต้องการ

1. เริ่มจาก **ข้อ 1 (`install.ps1`)** และ **ข้อ 2 (`install.sh`)** ก่อน — ทดสอบ logic หลักให้เสถียร
2. ต่อด้วย **ข้อ 3 (GitHub Actions)** เพื่อให้ release อัตโนมัติ
3. ตามด้วย **ข้อ 4 (README)** 
4. สุดท้ายค่อยทำ **ข้อ 5 (GUI)** ถ้าต้องการ

---

### หมายเหตุการใช้ไฟล์นี้
แทนที่ `<user>` ด้วย GitHub username จริงก่อนใช้งาน แล้วส่ง prompt นี้ทั้งก้อนให้ AI เพื่อเริ่มสร้างไฟล์จริงทีละข้อ
