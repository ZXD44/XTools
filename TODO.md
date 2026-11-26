# XTools — Build & Migration To-Do List

> อ้างอิงจาก [xtools_installer_prompt.md](xtools_installer_prompt.md)

---

## Phase 0: Prep & Repo Setup
- [x] กำหนด GitHub `<user>` จริง (`ZXD44`)
- [x] วางโครงสร้างโฟลเดอร์หลักใน `XTools/` (`bin/`, `assets/`, `.github/workflows/`, `scripts/`)
- [ ] ย้ายโปรเจคย่อยทั้งหมดเข้ามาใน `XTools` (Python, `.bat`, Rust binaries)

---

## Phase 1: Core Bootstrappers (`install.ps1` & `install.sh`)

### 1.1 `install.ps1` (Windows PowerShell — หลัก)
- [x] ดาวน์โหลด latest release (`xtools.zip`) จาก GitHub Releases + แสดง URL ปลายทางให้เห็นเสมอ
- [x] ตรวจสอบ SHA256 checksum เทียบกับค่าใน release notes ก่อนแตกไฟล์
- [x] เช็ค Python (`python --version`) — ถ้าไม่พบ แจ้งเตือนพร้อมลิงก์ `python.org`
- [x] รองรับ Rust compiled binaries (`.exe`) — ข้ามการเช็ค runtime และวางในโฟลเดอร์เดียวกัน
- [x] แตกไฟล์ไปที่ `$env:LOCALAPPDATA\Xtools`
- [x] เพิ่ม `Xtools\bin` เข้า **User PATH** (ไม่แตะ System PATH)
- [x] สร้าง Desktop shortcut (`.lnk`) ชี้ไปที่ `.bat` หลัก พร้อมไอคอน `assets/xtools.ico`
- [x] แสดงผลด้วย ANSI escape codes (ASCII banner `XTOOLS`, progress indicator, สรุปผลสีเขียว)
- [x] Idempotent: รันซ้ำได้ ถ้าติดตั้งอยู่แล้วให้ถาม overwrite / update
- [x] Error handling ครบ (network/404, write permission, missing Python) พร้อมวิธีแก้
- [x] Comment อธิบายทุก section

### 1.2 `install.sh` (macOS / Linux — รอง)
- [x] Logic เดียวกับ `install.ps1` โดยใช้ `curl` + `tar`/`unzip`
- [x] แสดง URL ปลายทาง + ตรวจ SHA256 checksum ก่อนแตกไฟล์
- [x] แตกไฟล์ไปที่ `~/.local/share/Xtools`
- [x] เช็ค shell ปัจจุบัน แล้วเพิ่ม `~/.local/share/Xtools/bin` เข้า `PATH` ใน `.bashrc` / `.zshrc`
- [x] ANSI colors (`tput` หรือ raw escape codes) ให้ feel เดียวกับ Windows
- [x] Idempotent + error handling ครบ + comment ทุก section

---

## Phase 2: Auto Release Workflow
- [x] สร้าง `.github/workflows/release.yml`
- [x] Trigger เมื่อ push tag ใหม่ (เช่น `v1.0.0`)
- [x] ขั้นตอน: Checkout -> Build/package scripts เป็น `xtools.zip` -> คำนวณ SHA256 checksum -> แนบเป็น GitHub Release asset (`softprops/action-gh-release`)
- [x] ใช้ `GITHUB_TOKEN` อัตโนมัติ (ไม่เพิ่ม custom secrets)

---

## Phase 3: Assets & Documentation (`README.md`)
- [x] สร้างไอคอน `assets/xtools.ico` (multi-resolution, รองรับ 256x256)
- [x] เพิ่มคำสั่งติดตั้ง one-liner แบบ short domain (`irm 'https://xtools.sh/install' | iex` / `curl -fsSL https://xtools.sh/install.sh | bash`)
- [x] เพิ่ม fallback URL แบบเต็ม (`raw.githubusercontent.com`)
- [x] อธิบายขั้นตอนที่ script ทำ (ดาวน์โหลด, แตกไฟล์, เพิ่ม PATH, สร้าง shortcut) + ลิงก์ตรงไปที่ `install.ps1` / `install.sh`
- [x] เพิ่มคำแนะนำการ pin shortcut ขึ้น Taskbar (ต้องลาก pin เองตามข้อจำกัด Windows)
- [x] เพิ่มหัวข้อ **Uninstall** (ลบโฟลเดอร์ + เอา PATH entry ออก)

---

## Phase 4: GUI Installer (Optional)
- [ ] สร้าง GUI installer ด้วย **Python + customtkinter**
- [ ] หน้าต่าง: โลโก้ Xtools, ปุ่ม `Install`, real-time progress bar, ปุ่ม `Open Folder` หลังเสร็จ
- [ ] แยก logic ดาวน์โหลด/แตกไฟล์/ตรวจ SHA256 เป็น Python function ที่ reuse ได้
- [ ] คอมไพล์เป็น `.exe` เดียวด้วย **PyInstaller**

---

## Security & Quality Gates (บังคับทุกไฟล์)
- [ ] ไม่มี hardcoded credentials, token, หรือ API key
- [ ] Idempotent (รันซ้ำไม่พัง)
- [ ] แสดง download URL ชัดเจน
- [ ] ตรวจ SHA256 checksum ก่อนแตกไฟล์เสมอ
- [ ] ไม่ execute remote code ผ่าน pipe โดยตรง (โหลดเป็นไฟล์ก่อนเสมอ)
