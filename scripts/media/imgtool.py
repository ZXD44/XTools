#!/usr/bin/env python3
"""XTools Media & Files — Batch Rename & Image/Icon Helper"""

from pathlib import Path

CYAN, GREEN, YELLOW, DIM, BOLD, RESET = "\033[96m", "\033[92m", "\033[93m", "\033[90m", "\033[1m", "\033[0m"


def main() -> None:
    print(f"{BOLD}{CYAN}┌── [ Media & Files — จัดการไฟล์และรูปภาพ ] ────────────┐{RESET}")
    folder = input("  ระบุโฟลเดอร์เป้าหมาย (เว้นว่าง = ปัจจุบัน): ").strip() or "."
    target = Path(folder)
    if not target.is_dir():
        print(f"  {YELLOW}ไม่พบโฟลเดอร์ {target}{RESET}")
        return
    prefix = input("  คำนำหน้าชื่อใหม่ (เช่น img_): ").strip()
    if not prefix:
        print(f"  {DIM}ยกเลิกการทำงาน{RESET}")
        return
    files = sorted(p for p in target.iterdir() if p.is_file())
    for idx, f in enumerate(files, 1):
        new_name = target / f"{prefix}{idx:03d}{f.suffix}"
        f.rename(new_name)
    print(f"  {GREEN}[OK]{RESET} เปลี่ยนชื่อไฟล์แล้ว {len(files)} ไฟล์")


if __name__ == "__main__":
    main()
