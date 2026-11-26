"""
การตั้งค่า ค่าคงที่ พาธ และระบบสีสำหรับ XTools
Config, Constants, Paths and ANSI Styles
"""

import os
import sys
from pathlib import Path

# ข้อมูลเวอร์ชันและ Repo
VERSION = "0.0.1"
BUILD = "dfc9e4a"
REPO = "ZXD44/XTools"

# พาธหลักของโปรเจกต์
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = ROOT_DIR / "scripts"
CONFIG_PATH = Path.home() / ".xtools_config.json"

# ANSI Escape Colors & Styles
CYAN = "\033[96m"
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
WHITE = "\033[97m"
BOLD = "\033[1m"
DIM = "\033[90m"
RESET = "\033[0m"

# Cyber Neon Color Palette สำหรับอนิเมชั่น
NEON_PALETTE = ["\033[96m", "\033[36m", "\033[94m", "\033[97m", "\033[96m"]

# นามสกุลไฟล์สคริปต์ที่ระบบรองรับ
SUPPORTED_EXTS = {".py", ".bat", ".ps1", ".sh", ".js", ".ts", ".exe"}

# รายการหมวดหมู่หลัก (ID, EN Title, TH Title, Folder, EN Desc, TH Desc)
CATEGORIES = [
    ("1", "System & Cleanup", "ระบบและล้างไฟล์", "system", "System info, temp cleanup, startup & env tools", "ข้อมูลระบบ ล้างไฟล์ขยะ และตั้งค่าเครื่อง"),
    ("2", "Dev & Git", "พัฒนาและ Git", "dev", "Repo utilities, formatters, environment helpers", "เครื่องมือจัดการ repo สภาพแวดล้อม และโค้ด"),
    ("3", "Network & Security", "เครือข่ายและความปลอดภัย", "network", "Diagnostics, port checks, hash & audit tools", "ตรวจสอบพอร์ต สแกนเครือข่าย และความปลอดภัย"),
    ("4", "Media & Files", "มีเดียและไฟล์", "media", "Batch rename, image/icon converters, archivers", "เปลี่ยนชื่อไฟล์ แปลงรูป/ไอคอน และบีบอัดไฟล์"),
]


def enable_windows_vt() -> None:
    """เปิดใช้งาน ANSI Escape Codes (Virtual Terminal Processing) บน Windows"""
    if os.name == "nt":
        import ctypes
        try:
            kernel32 = ctypes.windll.kernel32
            h_out = kernel32.GetStdHandle(-11)
            mode = ctypes.c_ulong()
            if kernel32.GetConsoleMode(h_out, ctypes.byref(mode)):
                kernel32.SetConsoleMode(h_out, mode.value | 0x0004 | 0x0001)
        except Exception:
            pass
        os.system("")
