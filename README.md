<div align="center">

# ⚡ XTools

**Multi-Language Automation Platform & Developer CLI Hub**
ชุดเครื่องมือ Automation แบบโมดูลาร์ รองรับหลาย Runtime ติดตั้งง่ายในคำสั่งเดียว

[![Release](https://img.shields.io/github/v/release/ZXD44/XTools?style=flat-square&color=00b4d8)](https://github.com/ZXD44/XTools/releases)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-blue?style=flat-square)](https://github.com/ZXD44/XTools)

</div>

---

## 🎨 ภาพรวมดีไซน์และโครงสร้างใหม่ (Design & Architecture)

XTools ได้รับการรื้อโครงสร้าง UI และโค้ดใหม่ทั้งหมด โดยใช้สถาปัตยกรรม **Modular Clean Architecture**:
- **Cyber Terminal Bento Layout**: ดีไซน์หน้าต่างควบคุมสไตล์ Bento Box แบ่งแยกโซนหมวดหมู่การทำงานและแถบคำสั่งด่วนชัดเจน
- **Separation of Concerns**: แยกโฟลเดอร์ตามหน้าที่ (`config/`, `core/`, `ui/`) ไม่มีไฟล์ใดยาวเกิน 300 บรรทัด
- **Dual-Language & Persistent**: รองรับภาษาไทย (ค่าเริ่มต้น) และภาษาอังกฤษ สลับได้ทันทีและจำค่าไว้ถาวร

---

## 📁 แผนผังโครงสร้างโปรเจกต์ (New Directory Tree)

```text
XTools/
├── .agent/                    # กฎและมาตรฐานสถาปัตยกรรมโปรเจกต์
│   └── rules.md
├── assets/                    # ไอคอนและไฟล์กราฟิก
│   └── xtools.ico
├── bin/                       # ตัวเรียกคำสั่งหลักเข้าสู่ PATH
│   └── xtools.bat
├── docs/                      # เอกสารคู่มือและการพัฒนา
├── scripts/                   # โมดูลระบบ XTools Hub
│   ├── config/                # [1] การตั้งค่า สี และค่าคงที่
│   │   └── constants.py       # รวมตัวแปรพาธ, ANSI Colors, รายชื่อหมวดหมู่
│   ├── core/                  # [2] ลอจิกการทำงานเบื้องหลัง
│   │   ├── discovery.py       # ค้นหาไฟล์สคริปต์เดี่ยว และ manifest (tool.json)
│   │   ├── doctor.py          # เช็คความพร้อมของระบบ (Python, Git, Rust, Node)
│   │   └── runner.py          # ระบบรันคำสั่งหลายภาษา (Python, Bash, Batch, Bun)
│   ├── ui/                    # [3] ส่วนแสดงผลหน้าจอ
│   │   ├── banner.py          # อนิเมชั่น Cyber Glitch และแบนเนอร์
│   │   ├── i18n.py            # ดิกชันนารีภาษาและตัวจัดการคอนฟิก (TH / EN)
│   │   └── menu.py            # Bento Grid Layout และ Viewport เมนู
│   ├── dev/                   # หมวดหมู่เครื่องมือสำหรับนักพัฒนา
│   ├── media/                 # หมวดหมู่เครื่องมือจัดการไฟล์และสื่อ
│   ├── network/               # หมวดหมู่เครื่องมือเครือข่ายและความปลอดภัย
│   ├── system/                # หมวดหมู่เครื่องมือระบบและล้างไฟล์
│   └── hub.py                 # Main Entry Point เรียกใช้งานโมดูลทั้งหมด
├── install.ps1                # ตัวติดตั้งอัตโนมัติบน Windows (PowerShell)
├── install.sh                 # ตัวติดตั้งอัตโนมัติบน macOS / Linux (Bash)
└── README.md                  # คู่มือการใช้งานโปรเจกต์
```

---

## 📦 วิธีติดตั้งและรันโปรเจกต์ (Installation & Quickstart)

### 1. ติดตั้งด้วยคำสั่งเดียว (One-Liner)

**Windows (PowerShell):**
```powershell
irm 'https://raw.githubusercontent.com/ZXD44/XTools/main/install.ps1' | iex
```

**macOS / Linux:**
```bash
curl -fsSL https://raw.githubusercontent.com/ZXD44/XTools/main/install.sh | bash
```

### 2. วิธีเรียกใช้งาน
เมื่อติดตั้งแล้ว คุณสามารถเปิดใช้งานได้จากทุกที่:
- **ดับเบิลคลิก** ไอคอน `XTools` บน Desktop
- หรือพิมพ์คำสั่งผ่าน Terminal:

| คำสั่ง (Command) | การทำงาน (Action) |
|---|---|
| `xtools` | เปิดหน้าจอหลัก Interactive Hub (Bento Dashboard) |
| `xtools doctor` | ตรวจสอบสุขภาพระบบ (Python, Git, Rust, Node, PATH, Disk) |
| `xtools update` | ดาวน์โหลดและอัปเดต XTools เป็นเวอร์ชันล่าสุด |
| `xtools lang [th\|en]` | สลับภาษาการแสดงผลระหว่าง ไทย และ อังกฤษ |
| `xtools <ชื่อเครื่องมือ>` | สั่งรันเครื่องมือในหมวดหมู่ย่อยโดยตรงทันที |

---

## 🛠️ คู่มือสำหรับผู้เริ่มต้นในการแก้ไขโค้ด (Beginner's Guide)

- **อยากแก้คำแปล / เพิ่มข้อความภาษาไทย-อังกฤษ**:
  - ไปที่ [`scripts/ui/i18n.py`](scripts/ui/i18n.py) แล้วแก้ไขในตัวแปร `STRINGS`
- **อยากแก้หน้าตา Bento Box / ปรับโครงสร้างเมนู**:
  - ไปที่ [`scripts/ui/menu.py`](scripts/ui/menu.py) ในฟังก์ชัน `render_main_dashboard()`
- **อยากแก้สี / เปลี่ยนชื่อหมวดหมู่ / เพิ่มหมวดหมู่ใหม่**:
  - ไปที่ [`scripts/config/constants.py`](scripts/config/constants.py) ในตัวแปร `CATEGORIES`
- **อยากเพิ่มโปรเจกต์ย่อยเข้ามาใน XTools**:
  - สร้างโฟลเดอร์ใน `scripts/<หมวด>/<ชื่อโปรเจกต์>/` แล้ววางไฟล์ `tool.json`
  ```json
  {
    "name": "my-tool",
    "desc": "เครื่องมือตัวอย่าง",
    "entry": "main.py",
    "runtime": "python"
  }
  ```
  ระบบจะดึงขึ้นเมนู Bento Card ให้โดยอัตโนมัติ ไม่ต้องแก้โค้ดระบบเลย
