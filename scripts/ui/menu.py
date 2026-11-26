"""
คอมโพเนนต์เมนูการแสดงผลแบบ Bento Card UI (Interactive Menu & Viewports)
"""

import os
from scripts.config.constants import (
    BLUE,
    BOLD,
    CYAN,
    DIM,
    GREEN,
    RED,
    RESET,
    YELLOW,
    CATEGORIES,
)
from scripts.core.discovery import discover_category_tools
from scripts.core.doctor import run_system_doctor, run_system_update
from scripts.core.runner import execute_tool
from scripts.ui.banner import animate_startup_banner, render_static_banner, wave_input
from scripts.ui.i18n import get_current_lang, set_current_lang, t


def clear_console_viewport() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def render_category_viewport(title: str, folder: str) -> None:
    """แสดงรายการเครื่องมือภายในหมวดหมู่ในรูปแบบ Bento Card List"""
    while True:
        clear_console_viewport()
        render_static_banner()
        print(f"{BOLD}{BLUE}┌── [ {title} ] ─────────────────────────────────────────┐{RESET}\n")

        tools = discover_category_tools(folder)
        if not tools:
            print(f"   {DIM}{t('no_tools').format(folder=folder)}{RESET}\n")
        else:
            for idx, item in enumerate(tools, 1):
                badge = f"{DIM}[{item.runtime.upper()}]{RESET}"
                print(f"   {CYAN}▪ [{idx}]{RESET} {BOLD}{item.name:<22}{RESET} {badge} {DIM}─ {item.desc}{RESET}")
            print()

        print(f"{BOLD}{BLUE}└────────────────────────────────────────────────────────┘{RESET}")
        print(f"   {DIM}[0] {t('back')}{RESET}\n")

        choice = wave_input(f"   {BOLD}{t('select')} > {RESET}").strip()
        if choice in ("0", ""):
            return

        if choice.isdigit() and 1 <= int(choice) <= len(tools):
            execute_tool(tools[int(choice) - 1])
            input(f"\n   {DIM}{t('press_enter')}{RESET}")


def render_main_dashboard() -> None:
    """แสดงหน้าหลัก XTools Dashboard สไตล์ Cyber Bento Grid"""
    first_launch = True

    while True:
        clear_console_viewport()
        if first_launch:
            animate_startup_banner()
            first_launch = False
        else:
            render_static_banner()

        curr_lang = get_current_lang()

        # ส่วนที่ 1: หมวดหมู่เครื่องมือ (Workspaces)
        print(f"{BOLD}┌── {t('select_cat')} ───────────────────────────────┐{RESET}")
        for key, title_en, title_th, _, desc_en, desc_th in CATEGORIES:
            title = title_th if curr_lang == "th" else title_en
            desc = desc_th if curr_lang == "th" else desc_en
            print(f"│  {CYAN}[{key}]{RESET} {BOLD}{title:<26}{RESET} {DIM}{desc}{RESET}")
        print(f"{BOLD}├── {t('quick_actions')} ───────────────────────────────────────┤{RESET}")

        # ส่วนที่ 2: เมนูด่วน (Control Bar)
        print(f"│  {GREEN}[S]{RESET} {t('sys_check'):<26} {DIM}{t('sys_check_desc')}{RESET}")
        print(f"│  {YELLOW}[U]{RESET} {t('update'):<26} {DIM}{t('update_desc')}{RESET}")
        print(f"│  {CYAN}[L]{RESET} {t('lang_label'):<26} {DIM}[{curr_lang.upper()}] {t('lang_desc')}{RESET}")
        print(f"│  {RED}[0]{RESET} {t('exit'):<26}")
        print(f"{BOLD}└────────────────────────────────────────────────────────┘{RESET}\n")

        choice = wave_input(f"   {BOLD}XTools > {RESET}").strip().lower()

        if choice in ("0", "q", "exit"):
            print(f"\n   {DIM}{t('bye')}{RESET}\n")
            break
        elif choice == "s":
            clear_console_viewport()
            render_static_banner()
            run_system_doctor()
            input(f"\n   {DIM}{t('press_enter')}{RESET}")
        elif choice == "u":
            run_system_update()
            input(f"\n   {DIM}{t('press_cont')}{RESET}")
        elif choice == "l":
            new_lang = "en" if curr_lang == "th" else "th"
            set_current_lang(new_lang)
        else:
            matched = [c for c in CATEGORIES if c[0] == choice]
            if matched:
                _, title_en, title_th, folder, _, _ = matched[0]
                render_category_viewport(title_th if curr_lang == "th" else title_en, folder)
