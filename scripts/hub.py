#!/usr/bin/env python3
"""XTools Interactive CLI Hub — Multi-runtime, plugin auto-discovery, doctor & direct CLI."""

import json
import os
import random
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path

# Enable ANSI escape sequences on Windows 10/11
if os.name == "nt":
    os.system("")

VERSION = "0.0.1"
BUILD = "374b5ab"
REPO = "ZXD44/XTools"

CYAN = "\033[96m"
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[90m"
RESET = "\033[0m"

ROOT_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT_DIR / "scripts"
CONFIG_PATH = Path.home() / ".xtools_config.json"

CATEGORIES = [
    ("1", "System & Cleanup", "ระบบและล้างไฟล์", "system", "System info, temp cleanup, startup & env tools", "ข้อมูลระบบ ล้างไฟล์ขยะ และตั้งค่า"),
    ("2", "Dev & Git", "พัฒนาและ Git", "dev", "Repo utilities, formatters, environment helpers", "เครื่องมือจัดการ repo และสภาพแวดล้อม"),
    ("3", "Network & Security", "เครือข่ายและความปลอดภัย", "network", "Diagnostics, port checks, hash & audit tools", "ตรวจสอบพอร์ต เครือข่าย และความปลอดภัย"),
    ("4", "Media & Files", "มีเดียและไฟล์", "media", "Batch rename, image/icon converters, archivers", "เปลี่ยนชื่อไฟล์ แปลงรูป/ไอคอน และบีบอัด"),
]

STRINGS = {
    "en": {
        "select_cat": "Select Category:",
        "sys_check": "System Check",
        "sys_check_desc": "Check runtimes, PATH, disk & GitHub API",
        "update": "Update XTools",
        "update_desc": "Re-run installer from GitHub",
        "lang_label": "Language",
        "lang_desc": "Switch EN / TH (saved)",
        "exit": "Exit",
        "bye": "Bye.",
        "no_tools": "(No tools in scripts/{folder}/ yet)",
        "back": "Back",
        "select": "Select",
        "press_enter": "Press Enter to return...",
        "press_cont": "Press Enter to continue...",
        "running": "Running",
        "interrupted": "Interrupted.",
        "doctor_title": "=== XTools System & Env Check (Doctor) ===",
    },
    "th": {
        "select_cat": "เลือกหมวดหมู่:",
        "sys_check": "ตรวจสอบระบบ",
        "sys_check_desc": "เช็ค Python, Git, Rust, Node, PATH และเน็ต",
        "update": "อัปเดต XTools",
        "update_desc": "อัปเดตเวอร์ชันล่าสุดจาก GitHub",
        "lang_label": "ภาษา / Language",
        "lang_desc": "สลับ EN / TH (บันทึกอัตโนมัติ)",
        "exit": "ออก",
        "bye": "ลาก่อน",
        "no_tools": "(ยังไม่มีเครื่องมือใน scripts/{folder}/)",
        "back": "กลับ",
        "select": "เลือก",
        "press_enter": "กด Enter เพื่อกลับ...",
        "press_cont": "กด Enter เพื่อดำเนินการต่อ...",
        "running": "กำลังรัน",
        "interrupted": "ถูกยกเลิก",
        "doctor_title": "=== ตรวจสอบระบบและสภาพแวดล้อม (Doctor) ===",
    },
}


def load_lang() -> str:
    try:
        if CONFIG_PATH.is_file():
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            if data.get("lang") in ("en", "th"):
                return data["lang"]
    except Exception:
        pass
    return "en"


def save_lang(lang: str) -> None:
    try:
        data = {}
        if CONFIG_PATH.is_file():
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        data["lang"] = lang
        CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass


_lang = load_lang()


def t(key: str) -> str:
    return STRINGS.get(_lang, STRINGS["en"]).get(key, key)

SUPPORTED_EXTS = {".py", ".bat", ".ps1", ".sh", ".js", ".ts", ".exe"}

_latest_version: str | None = None


@dataclass
class ToolEntry:
    name: str
    desc: str
    entry: Path
    runtime: str
    cwd: Path


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def check_latest_version_bg() -> None:
    """Non-blocking check for newer GitHub release."""
    global _latest_version
    try:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{REPO}/releases/latest",
            headers={"User-Agent": "XTools-Hub"},
        )
        with urllib.request.urlopen(req, timeout=2.5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            tag = data.get("tag_name", "").lstrip("v")
            if tag and tag != VERSION:
                _latest_version = tag
    except Exception:
        pass


BANNER_LINES = [
    r" __  _______ ___   ___  _     ____  ",
    r" \ \/ /_   _/ _ \ / _ \| |   / ___| ",
    r"  \  /  | || | | | | | | |   \___ \ ",
    r"  /  \  | || |_| | |_| | |___ ___) |",
    r" /_/\_\ |_| \___/ \___/|_____|____/ ",
]
NEON_PALETTE = ["\033[96m", "\033[36m", "\033[94m", "\033[97m", "\033[96m"]


def get_build_id() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(ROOT_DIR),
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=1,
        ).strip()
        if out:
            return out
    except Exception:
        pass
    return BUILD


def subtitle_line() -> str:
    update_badge = (
        f"  {YELLOW}[UPDATE AVAILABLE: v{_latest_version} — press U]{RESET}"
        if _latest_version
        else ""
    )
    return (
        f"  {CYAN}XTools Hub v{VERSION} {DIM}({get_build_id()}){RESET} {DIM}|{RESET} "
        f"{RED}{BOLD}ZXD44{RESET}{DIM}/XTools{RESET} {DIM}|{RESET} "
        f"{BLUE}Python {sys.version.split()[0]}{RESET}{update_badge}\n"
    )


def animate_banner() -> None:
    """Cyber glitch decode + neon gradient wave (runs once on startup)."""
    if os.environ.get("XTOOLS_NO_ANIM") == "1":
        print_banner()
        return

    glyphs = "#@%&$*+=-:/\\|"
    width = max(len(line) for line in BANNER_LINES)
    frames = 10

    sys.stdout.write("\033[?25l")  # hide cursor
    try:
        for step in range(frames + 1):
            locked_cols = int((step / frames) * width)
            out_lines = []
            for r_idx, line in enumerate(BANNER_LINES):
                buf = []
                for c_idx, ch in enumerate(line):
                    if ch == " ":
                        buf.append(" ")
                    elif c_idx <= locked_cols:
                        color = NEON_PALETTE[(c_idx // 4 + step + r_idx) % len(NEON_PALETTE)]
                        buf.append(f"{color}{BOLD}{ch}{RESET}")
                    else:
                        buf.append(f"{DIM}{random.choice(glyphs)}{RESET}")
                out_lines.append("".join(buf))
            if step > 0:
                sys.stdout.write(f"\033[{len(BANNER_LINES)}A")
            sys.stdout.write("\n".join(out_lines) + "\n")
            sys.stdout.flush()
            time.sleep(0.032)
    finally:
        sys.stdout.write("\033[?25h")  # restore cursor

    print(subtitle_line())


def print_banner() -> None:
    art = "\n".join(BANNER_LINES)
    print(f"{CYAN}{BOLD}\n{art}\n{RESET}{subtitle_line()}")


def discover_tools(folder: str) -> list[ToolEntry]:
    """Discover standalone scripts and tool.json plugin folders."""
    target = SCRIPTS_DIR / folder
    if not target.exists():
        return []

    tools: list[ToolEntry] = []
    for item in sorted(target.iterdir()):
        if item.is_file() and item.suffix.lower() in SUPPORTED_EXTS:
            tools.append(
                ToolEntry(
                    name=item.stem,
                    desc=f"{item.suffix.lstrip('.').upper()} script",
                    entry=item,
                    runtime="auto",
                    cwd=item.parent,
                )
            )
        elif item.is_dir():
            manifest = item / "tool.json"
            if manifest.is_file():
                try:
                    meta = json.loads(manifest.read_text(encoding="utf-8"))
                    entry_path = item / meta["entry"]
                    if entry_path.exists():
                        tools.append(
                            ToolEntry(
                                name=meta.get("name", item.name),
                                desc=meta.get("desc", ""),
                                entry=entry_path,
                                runtime=meta.get("runtime", "auto"),
                                cwd=item,
                            )
                        )
                except Exception:
                    continue
    return tools


def discover_all_tools() -> list[ToolEntry]:
    all_tools: list[ToolEntry] = []
    for _, _, _, folder, _, _ in CATEGORIES:
        all_tools.extend(discover_tools(folder))
    return all_tools


def resolve_python(cwd: Path) -> str:
    """Prefer local .venv Python if present in the tool's folder."""
    candidates = [
        cwd / ".venv" / "Scripts" / "python.exe",
        cwd / ".venv" / "bin" / "python",
    ]
    for c in candidates:
        if c.is_file():
            return str(c)
    return sys.executable


def run_tool(tool: ToolEntry, extra_args: list[str] | None = None) -> None:
    args = extra_args or []
    ext = tool.entry.suffix.lower()
    rt = tool.runtime.lower()

    if rt == "auto":
        rt_map = {
            ".py": "python",
            ".bat": "bat",
            ".ps1": "powershell",
            ".sh": "bash",
            ".js": "node",
            ".ts": "bun",
            ".exe": "exe",
        }
        rt = rt_map.get(ext, "exe")

    cmd: list[str]
    if rt == "python":
        cmd = [resolve_python(tool.cwd), str(tool.entry), *args]
    elif rt == "bat":
        cmd = ["cmd", "/c", str(tool.entry), *args]
    elif rt == "powershell":
        cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(tool.entry), *args]
    elif rt == "bash":
        cmd = ["bash", str(tool.entry), *args]
    elif rt == "node":
        cmd = ["node", str(tool.entry), *args]
    elif rt == "bun":
        runner = "bun" if shutil.which("bun") else "npx"
        cmd = ["bun", "run", str(tool.entry), *args] if runner == "bun" else ["npx", "tsx", str(tool.entry), *args]
    else:
        cmd = [str(tool.entry), *args]

    print(f"\n{CYAN}[>]{RESET} Running {BOLD}{tool.name}{RESET} ({DIM}{rt}{RESET})...\n")
    try:
        subprocess.run(cmd, cwd=str(tool.cwd), check=False)
    except FileNotFoundError as e:
        print(f"{RED}[ERROR] Runtime not found: {e}{RESET}")
    except KeyboardInterrupt:
        print(f"\n{YELLOW}[!] Interrupted.{RESET}")


def run_doctor() -> None:
    """System & environment health check."""
    print(f"{BOLD}{BLUE}=== XTools System & Env Check (Doctor) ==={RESET}\n")
    print(f"  OS        : {os.name} / {sys.platform}")
    print(f"  Root      : {ROOT_DIR}")

    runtimes = [
        ("python", ["python", "--version"]),
        ("git", ["git", "--version"]),
        ("gh", ["gh", "--version"]),
        ("node", ["node", "--version"]),
        ("bun", ["bun", "--version"]),
        ("rustc", ["rustc", "--version"]),
        ("cargo", ["cargo", "--version"]),
        ("uv", ["uv", "--version"]),
        ("docker", ["docker", "--version"]),
    ]

    print(f"\n{BOLD}Runtimes:{RESET}")
    for name, ver_cmd in runtimes:
        if shutil.which(name):
            try:
                out = subprocess.check_output(ver_cmd, stderr=subprocess.STDOUT, text=True, timeout=3)
                first_line = out.strip().splitlines()[0] if out.strip() else "installed"
                print(f"  {GREEN}[OK]{RESET} {name:<8} {DIM}{first_line}{RESET}")
            except Exception:
                print(f"  {GREEN}[OK]{RESET} {name:<8} {DIM}found{RESET}")
        else:
            print(f"  {DIM}[--] {name:<8} not installed{RESET}")

    bin_dir = str(ROOT_DIR / "bin")
    in_path = bin_dir.lower() in os.environ.get("PATH", "").lower()
    path_status = f"{GREEN}[OK]{RESET} in PATH" if in_path else f"{YELLOW}[!] not in current PATH{RESET}"
    print(f"\n{BOLD}Environment:{RESET}")
    print(f"  XTools\\bin : {path_status}")

    usage = shutil.disk_usage(ROOT_DIR)
    free_gb = usage.free / (1024 ** 3)
    print(f"  Disk Free  : {free_gb:.1f} GB")

    try:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{REPO}/releases/latest",
            headers={"User-Agent": "XTools-Doctor"},
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            print(f"  GitHub API : {GREEN}[OK]{RESET} HTTP {resp.status}")
    except Exception as e:
        print(f"  GitHub API : {RED}[FAIL]{RESET} {e}")


def run_update() -> None:
    if os.name == "nt":
        subprocess.run([
            "powershell", "-NoProfile", "-Command",
            f"irm 'https://raw.githubusercontent.com/{REPO}/main/install.ps1' | iex"
        ], check=False)
    else:
        subprocess.run([
            "bash", "-c",
            f"curl -fsSL https://raw.githubusercontent.com/{REPO}/main/install.sh | bash"
        ], check=False)


def category_menu(title: str, folder: str) -> None:
    while True:
        clear_screen()
        print_banner()
        print(f"{BOLD}{BLUE}=== {title} ==={RESET}\n")
        tools = discover_tools(folder)
        if not tools:
            print(f"  {DIM}{t('no_tools').format(folder=folder)}{RESET}\n")
        else:
            for idx, item in enumerate(tools, 1):
                print(f"  {CYAN}[{idx}]{RESET} {BOLD}{item.name:<22}{RESET} {DIM}{item.desc}{RESET}")
            print()
        print(f"  {DIM}[0] {t('back')}{RESET}\n")
        choice = input(f"{BOLD}{t('select')} > {RESET}").strip()
        if choice == "0" or choice == "":
            return
        if choice.isdigit() and 1 <= int(choice) <= len(tools):
            run_tool(tools[int(choice) - 1])
            input(f"\n{DIM}{t('press_enter')}{RESET}")


def interactive_menu() -> None:
    global _lang
    threading.Thread(target=check_latest_version_bg, daemon=True).start()
    first_launch = True
    while True:
        clear_screen()
        if first_launch:
            animate_banner()
            first_launch = False
        else:
            print_banner()
        print(f"{BOLD}{t('select_cat')}{RESET}\n")
        for key, title_en, title_th, _, desc_en, desc_th in CATEGORIES:
            title = title_th if _lang == "th" else title_en
            desc = desc_th if _lang == "th" else desc_en
            print(f"  {CYAN}[{key}]{RESET} {BOLD}{title:<24}{RESET} {DIM}{desc}{RESET}")
        print(f"\n  {GREEN}[S]{RESET} {t('sys_check'):<24} {DIM}{t('sys_check_desc')}{RESET}")
        print(f"  {YELLOW}[U]{RESET} {t('update'):<24} {DIM}{t('update_desc')}{RESET}")
        print(f"  {CYAN}[L]{RESET} {t('lang_label'):<24} {DIM}[{_lang.upper()}] {t('lang_desc')}{RESET}")
        print(f"  {RED}[0]{RESET} {t('exit')}\n")

        choice = input(f"{BOLD}XTools > {RESET}").strip().lower()
        if choice in {"0", "q", "exit"}:
            print(f"{DIM}{t('bye')}{RESET}")
            break
        elif choice == "s":
            clear_screen()
            print_banner()
            run_doctor()
            input(f"\n{DIM}{t('press_enter')}{RESET}")
        elif choice == "u":
            run_update()
            input(f"\n{DIM}{t('press_cont')}{RESET}")
        elif choice == "l":
            _lang = "th" if _lang == "en" else "en"
            save_lang(_lang)
        else:
            matched = [c for c in CATEGORIES if c[0] == choice]
            if matched:
                _, title_en, title_th, folder, _, _ = matched[0]
                category_menu(title_th if _lang == "th" else title_en, folder)


def main() -> None:
    global _lang
    args = sys.argv[1:]
    if not args:
        interactive_menu()
        return

    cmd = args[0].lower()
    if cmd in {"doctor", "check", "env"}:
        run_doctor()
    elif cmd in {"update", "upgrade"}:
        run_update()
    elif cmd == "lang":
        if len(args) > 1 and args[1].lower() in {"en", "th"}:
            _lang = args[1].lower()
        else:
            _lang = "th" if _lang == "en" else "en"
        save_lang(_lang)
        print(f"Language set to: {_lang.upper()}")
    elif cmd in {"-v", "--version", "version"}:
        print(f"XTools v{VERSION}")
    else:
        for tool in discover_all_tools():
            if tool.name.lower() == cmd:
                run_tool(tool, args[1:])
                return
        print(f"{RED}[ERROR] Unknown command or tool: '{args[0]}'{RESET}")
        print(f"{DIM}Try: xtools doctor | xtools update | xtools --version{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()
