#!/usr/bin/env python3
"""
XTools Interactive CLI Hub — Main Entry Point
สถาปัตยกรรมโมดูลาร์ สะอาด แยกส่วนการทำงาน และเป็นมิตรกับผู้เริ่มต้น
"""

import sys
import threading
from pathlib import Path

# ผูก Root เข้ากับ sys.path เพื่อให้ import submodule ได้แม่นยำ
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.config.constants import (
    DIM,
    RED,
    RESET,
    VERSION,
    enable_windows_vt,
)
from scripts.core.discovery import discover_all_workspace_tools
from scripts.core.doctor import check_latest_release_bg, run_system_doctor, run_system_update
from scripts.core.runner import execute_tool
from scripts.ui.i18n import get_current_lang, set_current_lang
from scripts.ui.menu import render_main_dashboard


def main() -> None:
    # 1. เริ่มต้น Virtual Terminal สำหรับ Windows Console
    enable_windows_vt()

    # 2. เริ่มตรวจสอบเวอร์ชันใหม่ในเบื้องหลังแบบ non-blocking
    threading.Thread(target=check_latest_release_bg, daemon=True).start()

    args = sys.argv[1:]

    # โหมด Interactive (เปิด Dashboard UI) เมื่อไม่มี arguments ส่งมา
    if not args:
        render_main_dashboard()
        return

    # โหมด Direct CLI Commands
    cmd = args[0].lower()

    if cmd in ("doctor", "check", "env"):
        run_system_doctor()
    elif cmd in ("update", "upgrade"):
        run_system_update()
    elif cmd == "lang":
        if len(args) > 1 and args[1].lower() in ("en", "th"):
            set_current_lang(args[1].lower())
        else:
            new_lang = "en" if get_current_lang() == "th" else "th"
            set_current_lang(new_lang)
        print(f"Language set to: {get_current_lang().upper()}")
    elif cmd in ("-v", "--version", "version"):
        print(f"XTools v{VERSION}")
    else:
        # ค้นหาเครื่องมือที่มีชื่อตรงกับคำสั่ง
        for tool in discover_all_workspace_tools():
            if tool.name.lower() == cmd:
                execute_tool(tool, args[1:])
                return

        print(f"{RED}[ERROR] Unknown command or tool: '{args[0]}'{RESET}")
        print(f"{DIM}Available shortcuts: xtools doctor | xtools update | xtools lang | xtools --version{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()
