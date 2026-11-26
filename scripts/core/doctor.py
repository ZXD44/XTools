"""
ระบบตรวจสอบสุขภาพของระบบและสภาพแวดล้อม (System & Health Diagnostics)
"""

import json
import os
import shutil
import subprocess
import sys
import urllib.request
from scripts.config.constants import (
    BLUE,
    BOLD,
    DIM,
    GREEN,
    RED,
    REPO,
    RESET,
    ROOT_DIR,
    VERSION,
    BUILD,
    YELLOW,
)
from scripts.ui.banner import set_latest_version
from scripts.ui.i18n import t


def check_latest_release_bg() -> None:
    """ตรวจเช็คเวอร์ชันใหม่จาก GitHub Releases ในพื้นหลัง (Non-blocking)"""
    try:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{REPO}/releases/latest",
            headers={"User-Agent": "XTools-Hub"},
        )
        with urllib.request.urlopen(req, timeout=2.5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            tag = data.get("tag_name", "").lstrip("v")
            current_full = f"{VERSION}-{BUILD}" if BUILD else VERSION
            if tag and tag != current_full and tag != VERSION:
                set_latest_version(tag)
    except Exception:
        pass


def run_system_doctor() -> None:
    """วินิจฉัยสภาพแวดล้อม เครื่องมือที่ติดตั้ง และความพร้อมใช้งาน"""
    print(f"{BOLD}{BLUE}{t('doctor_title')}{RESET}\n")
    print(f"  OS        : {os.name} / {sys.platform}")
    print(f"  Root Dir  : {ROOT_DIR}")

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

    print(f"\n{BOLD}{t('runtimes_header')}{RESET}")
    for name, ver_cmd in runtimes:
        if shutil.which(name):
            try:
                out = subprocess.check_output(ver_cmd, stderr=subprocess.STDOUT, text=True, timeout=3)
                first_line = out.strip().splitlines()[0] if out.strip() else "OK"
                print(f"  {GREEN}[OK]{RESET} {name:<8} {DIM}{first_line}{RESET}")
            except Exception:
                print(f"  {GREEN}[OK]{RESET} {name:<8} {DIM}OK{RESET}")
        else:
            print(f"  {DIM}[--] {name:<8} {t('not_installed')}{RESET}")

    bin_dir = str(ROOT_DIR / "bin")
    in_path = bin_dir.lower() in os.environ.get("PATH", "").lower()
    path_status = f"{GREEN}[OK]{RESET} {t('in_path')}" if in_path else f"{YELLOW}[!] {t('not_in_path')}{RESET}"
    print(f"\n{BOLD}{t('env_header')}{RESET}")
    print(f"  XTools\\bin : {path_status}")

    try:
        usage = shutil.disk_usage(ROOT_DIR)
        free_gb = usage.free / (1024 ** 3)
        print(f"  {t('disk_free')} {free_gb:.1f} GB")
    except Exception:
        pass

    try:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{REPO}/releases/latest",
            headers={"User-Agent": "XTools-Doctor"},
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            print(f"  GitHub API : {GREEN}[OK]{RESET} HTTP {resp.status}")
    except Exception as e:
        print(f"  GitHub API : {RED}[FAIL]{RESET} {e}")


def run_system_update() -> None:
    """สั่งดาวน์โหลดและติดตั้งตัวอัปเดตเวอร์ชันล่าสุด"""
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
