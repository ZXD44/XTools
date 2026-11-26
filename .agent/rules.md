# XTools — Project Architecture & Rules (`.agent/rules.md`)

## 1. Naming & Identity
- Project name: **XTools** (always capital `X` and `T`).
- GitHub repository: `ZXD44/XTools`.
- Git author: `ZXD44`.
- Version Lock: `0.0.1` (sub-build format: `v0.0.1-<hash>`).

## 2. Directory Structure & Modular Design
โค้ดต้องแยกตามหน้าที่ชัดเจน (Separation of Concerns) แต่ละไฟล์ยาวไม่เกิน 500 บรรทัด:
- `bin/` — รันเนอร์หลักของระบบ (`xtools.bat`)
- `scripts/` — โครงสร้างโมดูลหลักของ XTools Hub:
  - `config/` — การตั้งค่า, ค่าคงที่ (Constants), ANSI Colors, Palettes (`constants.py`, `settings.py`)
  - `ui/` — การแสดงผลหน้าตา, แบนเนอร์, อนิเมชั่น, เมนูภาษา (`banner.py`, `menu.py`, `i18n.py`)
  - `core/` — ระบบค้นหาเครื่องมือ, รันเนอร์, เช็คระบบ (`discovery.py`, `runner.py`, `doctor.py`)
  - `hub.py` — Entry point หลักที่เรียกใช้งานคอมโพเนนต์ต่างๆ
- `assets/` — ไอคอนและไฟล์กราฟิก (`xtools.ico`)
- `docs/` — เอกสารประกอบการพัฒนาและคู่มือ
- `.agent/` — กฎระเบียบและสถาปัตยกรรมของโปรเจกต์ (`rules.md`)

## 3. UI/UX Standard (Cyber Terminal Bento & Frame System)
1. โครงสร้างหน้าต่าง CLI และ Terminal ต้องสะอาด มีมิติ (Bento Card Style / Cyber Neon Frames)
2. จัดวางเลย์เอาต์แยกเป็นสัดส่วนชัดเจน:
   - Header / Brand Banner พร้อมแท็กสถานะเวอร์ชัน
   - Main Workspace / หมวดหมู่เครื่องมือพร้อมคำอธิบายแบบการ์ด
   - Footer Bar / แถบปุ่มลัดคำสั่งด่วน (Quick Actions: `[S] Check`, `[U] Update`, `[L] Lang`, `[0] Exit`)
3. รองรับการประมวลผล Virtual Terminal Processing บน Windows 10/11 อัตโนมัติ

## 4. Security & Installer Standards
- **No hardcoded secrets**: ห้ามเก็บ token, api key หรือ credentials ลงในโค้ดเด็ดขาด
- **SHA256 Verification**: ตัวติดตั้ง (`install.ps1`, `install.sh`) ต้องตรวจเช็ค checksum ก่อนแตกไฟล์เสมอ
- **Idempotency**: รองรับการติดตั้งซ้ำ/อัปเดตทับได้อย่างปลอดภัย ขยะ temp ต้องถูกลบทิ้ง 100%

## 5. Deploy & Release Workflow
- ทดสอบระบบผ่าน `python scripts/hub.py doctor`
- คอมมิตและพุชขึ้น `main`
- ติดแท็ก Semantic Version พร้อม Hash สั้น เช่น `git tag v0.0.1-<hash>` และพุชแท็ก
- GitHub Actions จะแพ็กเกจ `xtools.zip` พร้อม SHA256 และปล่อย GitHub Release อัตโนมัติ
