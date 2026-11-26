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

## 5. Rust-First Standard (บังคับใช้กับ**ทุก**โปรเจกต์)
ทุกโปรเจกต์ที่ XTools **รับเข้ามา** หรือ **สร้างใหม่** ต้องจบเป็น **Rust** โดยใช้
[`rust-anything`](https://github.com/erkamyaman/rust-anything) เป็นเครื่องมือมาตรฐาน
(บันทึกพฤติกรรมเดิม → เขียน Rust → ตรวจว่าเหมือนเดิมทุกเคส)

คุณสมบัติที่ต้องยืนยันได้ด้วยการวัดจริง ไม่ใช่คำโฆษณา:

| คุณสมบัติ | ต้องพิสูจน์ด้วย |
|---|---|
| **เบา** (light) | ไบนารีเดี่ยว ไม่ต้องมี runtime/node_modules/venv ติดไปด้วย |
| **เร็ว** (fast) | `rust-anything bench` แสดงว่าดีกว่าของเดิม (ถ้าไม่ดีขึ้น ให้รายงานตามจริง) |
| **ลื่น** (smooth) | เริ่มทำงานไว ไม่มี startup ค้าง, `--version`/`--help` ตอบทันที |
| **ประหยัดพื้นที่** (saves space) | รายงานขนาด artifact ก่อน/หลัง (release build + strip) |
| **เสถียร** (stable) | `diff` ผ่านทุกเคสที่บันทึกไว้ + `gate` ผ่าน + `fuzz` ไม่เจอความต่าง |

### 5.1 ลำดับงานบังคับ
```text
analyze → profile → bridge → record → diff → bench → gate
```
- ห้าม ship งานที่ยังไม่ผ่าน `gate`
- ห้ามปิดสวิตช์ด้วย `RUST_ANYTHING_MODE=old` หรือ fallback ไปโค้ดเดิมใน production build
- `diff` ต้องตรงทุกเคส; เคสที่ยังไม่ครอบคลุมให้ใช้ `fuzz` หาเพิ่ม ไม่ใช่ประกาศว่าผ่าน
- ผลที่ยังไม่ผ่าน ให้รายงานตามจริง ห้ามสรุปว่าเสร็จ

### 5.2 การเข้าถึงผ่าน XTools
- เมนู: `xtools` → หมวด `2` (Dev & Git) → `rust-anything`
- ตรง: `xtools rust-anything` หรือ `python scripts/dev/rust-anything/main.py <args>`
- ตัวเรียกเป็น thin wrapper เท่านั้น (ไม่ reimplement CLI) — argument ดิบส่งผ่านได้ทั้งหมด
- ติดตั้ง: `cargo install rust-anything` หรือ `npm install -g rust-anything` หรือ binary จาก Releases

### 5.3 ข้อยกเว้น
ส่วนที่เป็น UI/แพลตฟอร์มเฉพาะ (เช่น Activity บน Android, PowerShell ที่ผูก .NET type)
ให้อยู่ในภาษาเดิมได้ แต่ต้องมีเหตุผลเขียนกำกับ และ core logic ต้องเป็น Rust

---

## 6. Deploy & Release Workflow
- ตรวจ Rust-First: เครื่องมือใหม่/ที่ port ต้องผ่าน `rust-anything gate` ก่อน
- ทดสอบระบบผ่าน `python scripts/hub.py doctor`
- คอมมิตและพุชขึ้น `main`
- ติดแท็ก Semantic Version พร้อม Hash สั้น เช่น `git tag v0.0.1-<hash>` และพุชแท็ก
- GitHub Actions จะแพ็กเกจ `xtools.zip` พร้อม SHA256 และปล่อย GitHub Release อัตโนมัติ
