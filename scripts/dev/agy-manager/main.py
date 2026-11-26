"""
main.py — AGY Manager TUI (All Phases)
XTools Dev → agy-manager
"""

import getpass
import os
import sys
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.config.constants import (
    BLUE, BOLD, CYAN, DIM, GREEN, MAGENTA, RED, RESET, YELLOW,
    enable_windows_vt,
)
from scripts.ui.banner import wave_input
from agy_config import (
    load_accounts, switch_account, get_active_account,
    add_binding, remove_binding, detect_binding, AgyAccount,
    ACCOUNTS_FILE, XTOOLS_CONFIG, PROFILE_DIR,
)
from quota import (
    compute_badge, format_badge, record_switch, get_next_account, set_cooldown,
)
from session_lock import acquire_lock, release_lock, heartbeat_lock, get_lock_owner
from crypto import (
    encrypt_backup, decrypt_backup, BACKUP_FILE,
    export_encrypted_zip, ZIP_BACKUP_FILE,
)

enable_windows_vt()


def clear() -> None:
    os.system("cls" if os.name == "nt" else "clear")


_BOX_W = 56


def _h(title: str) -> None:
    head = f"── [ AGY Manager — {title} ] "
    print(f"{BOLD}{CYAN}┌{head}{'─' * max(0, _BOX_W - len(head))}┐{RESET}")


def _sep(label: str = "") -> None:
    head = f"├── {label} "
    print(f"{BOLD}{CYAN}{head}{'─' * max(0, _BOX_W - len(head) + 1)}┤{RESET}")


def _f() -> None:
    print(f"{BOLD}{CYAN}└{'─' * _BOX_W}┘{RESET}\n")


def _ask_password(prompt: str) -> str:
    """อ่านรหัสผ่านแบบไม่แสดงผล

    getpass บน Windows จะค้างตลอดกาลถ้า stdin ไม่ใช่ terminal (pipe/รีไดเรกต์)
    จึงถอยไปอ่านจาก stdin ตรง ๆ ในกรณีนั้น (แบบเดียวกับ wave_input)
    """
    if sys.stdin is not None and sys.stdin.isatty():
        return getpass.getpass(prompt)
    print(f"{DIM}{prompt}(อ่านจาก stdin){RESET}", end="", flush=True)
    line = sys.stdin.readline()
    if not line:
        raise KeyboardInterrupt
    return line.rstrip("\r\n")


def _acc_row(idx: int, acc: AgyAccount) -> None:
    ab = f"{GREEN}{BOLD}[●]{RESET}" if acc.is_active else f"{DIM}[ ]{RESET}"
    bk, col, cd = compute_badge(acc.email)
    name = f"{BOLD}{acc.email}{RESET}" if acc.is_active else acc.email
    binds = f" {DIM}[{len(acc.bindings)} binding]{RESET}" if acc.bindings else ""
    print(f"  {ab} {CYAN}[{idx}]{RESET} {name}{binds}")
    print(f"       {format_badge(bk, col, cd)}")
    if acc.last_used:
        print(f"       {DIM}ใช้ล่าสุด: {acc.last_used[:19].replace('T', ' ')} UTC{RESET}")
    print()


def main_menu() -> None:
    while True:
        clear()
        accounts = load_accounts()
        _h("Dashboard")
        print()

        if not accounts:
            print(f"  {RED}ไม่พบบัญชี AGY — ลงชื่อเข้าใช้ด้วย AGY ก่อน{RESET}\n")
        else:
            for i, acc in enumerate(accounts, 1):
                _acc_row(i, acc)

        # auto-detect binding
        suggested = detect_binding()
        active = get_active_account()
        if suggested and suggested != active:
            print(f"  {YELLOW}[แนะนำ] Project นี้ผูกกับ: {suggested}{RESET}\n")

        # session lock status
        lock_owner = get_lock_owner()
        if lock_owner:
            print(f"  {MAGENTA}[SESSION LOCK] '{lock_owner}' กำลังถูกใช้งาน{RESET}\n")

        n = len(accounts)
        _sep("คำสั่ง")
        print(f"  {CYAN}[1-{n}]{RESET} สลับบัญชี")
        print(f"  {GREEN}[N]{RESET} หมุนบัญชีถัดไปอัตโนมัติ  {DIM}(ข้าม cooldown){RESET}")
        print(f"  {BLUE}[P]{RESET} Profile Binding           {DIM}ผูกบัญชีกับ project{RESET}")
        print(f"  {YELLOW}[L]{RESET} Session Lock / Unlock")
        print(f"  {MAGENTA}[B]{RESET} Backup / Restore          {DIM}AES-GCM + SHA-256{RESET}")
        print(f"  {YELLOW}[C]{RESET} ติด Cooldown ให้บัญชี     {DIM}กันหมุนไปใช้บัญชีที่หมดแล้ว{RESET}")
        print(f"  {RED}[0]{RESET} ออก")
        _f()

        choice = wave_input(f"  {BOLD}AGY > {RESET}").strip().lower()

        if choice in ("0", "q"):
            release_lock()
            break
        if not choice:
            continue  # กด Enter = รีเฟรชหน้า ไม่ใช่่ออก
        elif choice.isdigit() and 1 <= int(choice) <= n:
            _switch(accounts, accounts[int(choice) - 1].email)
        elif choice == "n":
            _rotate(accounts)
        elif choice == "p":
            _binding_menu(accounts)
        elif choice == "l":
            _session_lock_menu(accounts)
        elif choice == "b":
            _backup_menu()
        elif choice == "c":
            _cooldown_menu(accounts)


def _switch(accounts: list[AgyAccount], email: str) -> None:
    ok = switch_account(email, accounts)
    if ok:
        record_switch(email)
        print(f"\n  {GREEN}[OK] สลับเป็น {BOLD}{email}{RESET}")
    else:
        print(f"\n  {RED}[ผิดพลาด] สลับบัญชีไม่สำเร็จ{RESET}")
    time.sleep(1.2)


def _rotate(accounts: list[AgyAccount]) -> None:
    nxt = get_next_account(accounts)
    if nxt:
        _switch(accounts, nxt)
    else:
        print(f"\n  {YELLOW}ไม่มีบัญชีที่พร้อมใช้งาน (ติด cooldown หรือสลับบ่อยจนหมดแล้ว){RESET}")
        time.sleep(1.5)


def _cooldown_menu(accounts: list[AgyAccount]) -> None:
    clear()
    _h("Cooldown")
    print()
    for i, acc in enumerate(accounts, 1):
        print(f"  {CYAN}[{i}]{RESET} {acc.email}")
    print(f"\n  {DIM}[0]{RESET} กลับ")
    _f()

    choice = wave_input("  บัญชี [1-{}] (เว้นว่าง = บัญชีที่ใช้อยู่): ".format(len(accounts))).strip()
    if choice in ("0", "q"):
        return
    if not choice:
        email = get_active_account()
        if not email:
            print(f"  {RED}[ผิดพลาด] ไม่พบบัญชีที่ใช้งานอยู่{RESET}")
            time.sleep(1.5)
            return
    elif choice.isdigit() and 1 <= int(choice) <= len(accounts):
        email = accounts[int(choice) - 1].email
    else:
        print(f"  {RED}[ผิดพลาด] เลือกบัญชีไม่ถูกต้อง{RESET}")
        time.sleep(1.5)
        return

    raw = wave_input("  ระยะเวลา cooldown (ชั่วโมง, Enter = 5): ").strip()
    hours = 5.0
    if raw:
        try:
            hours = float(raw)
        except ValueError:
            print(f"  {RED}[ผิดพลาด] ต้องเป็นตัวเลข{RESET}")
            time.sleep(1.5)
            return
    if hours <= 0:
        print(f"  {RED}[ผิดพลาด] ต้องมากกว่า 0 ชั่วโมง{RESET}")
        time.sleep(1.5)
        return

    set_cooldown(email, hours)
    until = datetime.now(timezone.utc) + timedelta(hours=hours)
    local = until.astimezone().strftime("%Y-%m-%d %H:%M")
    print(f"  {GREEN}[OK] {email} ติด cooldown ถึง {local} ({hours:g} ชม.){RESET}")
    time.sleep(1.8)


def _binding_menu(accounts: list[AgyAccount]) -> None:
    clear()
    _h("Profile Binding")
    print()
    for i, acc in enumerate(accounts, 1):
        print(f"  {CYAN}[{i}]{RESET} {acc.email}")
        for b in acc.bindings:
            print(f"       {DIM}→ {b}{RESET}")
    print(f"\n  {GREEN}[A]{RESET} เพิ่ม Binding  {RED}[R]{RESET} ลบ  {DIM}[0]{RESET} กลับ")
    _f()
    choice = wave_input(f"  Binding > ").strip().lower()
    n = len(accounts)
    if choice == "a":
        idx = wave_input(f"  เลือกบัญชี [1-{n}]: ").strip()
        if idx.isdigit() and 1 <= int(idx) <= n:
            path = wave_input(f"  Path (เว้นว่าง = ปัจจุบัน): ").strip() or "."
            add_binding(accounts[int(idx) - 1].email, path)
            print(f"  {GREEN}[OK]{RESET}")
            time.sleep(1.0)
    elif choice == "r":
        idx = wave_input(f"  เลือกบัญชี [1-{n}]: ").strip()
        path = wave_input(f"  Path ที่ต้องการลบ: ").strip()
        if idx.isdigit() and 1 <= int(idx) <= n and path:
            remove_binding(accounts[int(idx) - 1].email, path)
            print(f"  {YELLOW}[OK] ลบแล้ว{RESET}")
            time.sleep(1.0)
        else:
            print(f"  {RED}[ผิดพลาด] ต้องระบุ path ให้ชัดเจน{RESET}")
            time.sleep(1.2)


def _heartbeat_loop(email: str) -> None:
    """ต่ออายุ lock ทุก 5 วินาที จนกว่าจะเสีย lock ไป"""
    while heartbeat_lock(email):
        time.sleep(5)


def _session_lock_menu(accounts: list[AgyAccount]) -> None:
    owner = get_lock_owner()
    if owner:
        print(f"\n  {MAGENTA}[LOCK] '{owner}' ถูก lock อยู่{RESET}")
        if wave_input("  Unlock? [y/N]: ").strip().lower() == "y":
            release_lock()
            print(f"  {GREEN}[OK] ปล่อย lock แล้ว{RESET}")
    else:
        idx = wave_input(f"  Lock บัญชี [1-{len(accounts)}]: ").strip()
        if idx.isdigit() and 1 <= int(idx) <= len(accounts):
            email = accounts[int(idx) - 1].email
            if acquire_lock(email):
                print(f"  {GREEN}[LOCKED] '{email}'{RESET}")
                threading.Thread(target=_heartbeat_loop, args=(email,), daemon=True).start()
            else:
                print(f"  {RED}[ผิดพลาด] Terminal อื่นถือ lock อยู่{RESET}")
    time.sleep(1.5)


def _backup_menu() -> None:
    clear()
    _h("Backup & Restore")
    print(f"\n  {GREEN}[1]{RESET} สำรองข้อมูล (AES-GCM)")
    if BACKUP_FILE.exists():
        print(f"  {BLUE}[2]{RESET} กู้คืน (SHA-256 verify)")
    print(f"  {YELLOW}[3]{RESET} Export ทั้งชุดเป็น .zip เข้ารหัส  {DIM}(config + profiles){RESET}")
    print(f"  {DIM}[0]{RESET} กลับ")
    _f()
    choice = wave_input("  Backup > ").strip()
    if choice == "1":
        import json
        data = {}
        try:
            data["accounts"] = json.loads(ACCOUNTS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
        try:
            data["xtools"] = json.loads(XTOOLS_CONFIG.read_text(encoding="utf-8"))
        except Exception:
            pass
        pwd = _ask_password("  รหัสผ่าน (ไม่แสดงผล): ")
        try:
            encrypt_backup(data, pwd)
            print(f"  {GREEN}[OK] บันทึกที่ {BACKUP_FILE}{RESET}")
        except Exception as e:
            print(f"  {RED}[ผิดพลาด] {e}{RESET}")
        time.sleep(1.5)
    elif choice == "2" and BACKUP_FILE.exists():
        pwd = _ask_password("  รหัสผ่าน (ไม่แสดงผล): ")
        try:
            data = decrypt_backup(pwd)
            print(f"  {GREEN}[OK] ถอดรหัสสำเร็จ{RESET}")
            if wave_input("  ยืนยันกู้คืน? [y/N]: ").strip().lower() == "y":
                from agy_config import _atomic_write
                stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                for path, key in ((ACCOUNTS_FILE, "accounts"), (XTOOLS_CONFIG, "xtools")):
                    if key not in data:
                        continue
                    # เก็บของเดิมไว้ก่อนทับ เพื่อไม่ให้ config ที่ใหม่กว่าหาย
                    if path.exists():
                        safe = path.with_name(f"{path.name}.pre-restore-{stamp}")
                        safe.write_bytes(path.read_bytes())
                        print(f"  {DIM}สำรองเดิม: {safe}{RESET}")
                    _atomic_write(path, data[key])
                print(f"  {GREEN}[OK] กู้คืนแล้ว{RESET}")
        except Exception as e:
            print(f"  {RED}[ผิดพลาด] {e}{RESET}")
        time.sleep(1.5)
    elif choice == "3":
        print(f"  {DIM}ปลายทางเริ่มต้น: {ZIP_BACKUP_FILE}{RESET}")
        pwd = _ask_password("  รหัสผ่าน (ไม่แสดงผล): ").strip()
        if not pwd:
            print(f"  {RED}[ผิดพลาด] รหัสผ่านต้องไม่ว่าง{RESET}")
            time.sleep(1.5)
            return
        if _ask_password("  ยืนยันรหัสผ่าน: ").strip() != pwd:
            print(f"  {RED}[ผิดพลาด] รหัสผ่านไม่ตรงกัน{RESET}")
            time.sleep(1.5)
            return
        try:
            dest = export_encrypted_zip([ACCOUNTS_FILE, XTOOLS_CONFIG, PROFILE_DIR], pwd)
            print(f"  {GREEN}[OK] บันทึกที่ {dest}{RESET}")
        except Exception as e:
            print(f"  {RED}[ผิดพลาด] {e}{RESET}")
        time.sleep(1.8)


if __name__ == "__main__":
    main_menu()
