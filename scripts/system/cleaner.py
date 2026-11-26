#!/usr/bin/env python3
"""XTools System Cleaner — ล้างไฟล์ Temp, Recycle Bin และเช็คพื้นที่ดิสก์"""

import os
import shutil
import tempfile
from pathlib import Path

CYAN, GREEN, YELLOW, DIM, BOLD, RESET = "\033[96m", "\033[92m", "\033[93m", "\033[90m", "\033[1m", "\033[0m"


def clean_temp() -> tuple[int, int]:
    temp_dir = Path(tempfile.gettempdir())
    removed, freed = 0, 0
    for item in temp_dir.iterdir():
        try:
            size = item.stat().st_size if item.is_file() else 0
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
            removed += 1
            freed += size
        except Exception:
            pass
    return removed, freed


def main() -> None:
    print(f"{BOLD}{CYAN}┌── [ System Cleaner — ล้างไฟล์ขยะ ] ───────────────────┐{RESET}")
    usage = shutil.disk_usage(Path.home())
    print(f"  พื้นที่ว่างปัจจุบัน: {GREEN}{usage.free / (1024**3):.2f} GB{RESET}\n")
    ans = input("  ต้องการล้างไฟล์ Temp ทั้งหมดหรือไม่? [y/N]: ").strip().lower()
    if ans == "y":
        cnt, freed = clean_temp()
        print(f"  {GREEN}[OK]{RESET} ลบแล้ว {cnt} รายการ ({freed / (1024**2):.2f} MB)")
    else:
        print(f"  {DIM}ยกเลิกการทำงาน{RESET}")


if __name__ == "__main__":
    main()
