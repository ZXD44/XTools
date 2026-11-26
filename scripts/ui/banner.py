"""
แบนเนอร์และอนิเมชั่นแสดงผลหน้าตาคอนโซล (Banner & Visual Animation)
"""

import os
import random
import subprocess
import sys
import time
from scripts.config.constants import (
    BOLD,
    CYAN,
    DIM,
    NEON_PALETTE,
    RED,
    RESET,
    ROOT_DIR,
    VERSION,
    BUILD,
    BLUE,
    YELLOW,
)

BANNER_ART = [
    r" __  _______ ___   ___  _     ____  ",
    r" \ \/ /_   _/ _ \ / _ \| |   / ___| ",
    r"  \  /  | || | | | | | | |   \___ \ ",
    r"  /  \  | || |_| | |_| | |___ ___) |",
    r" /_/\_\ |_| \___/ \___/|_____|____/ ",
]

_latest_version: str | None = None


def set_latest_version(ver: str | None) -> None:
    global _latest_version
    _latest_version = ver


def get_latest_version() -> str | None:
    return _latest_version


def get_build_id() -> str:
    """ดึงเลข Git Commit Hash สั้น"""
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


def get_subtitle_line() -> str:
    """เรนเดอร์แท็กสถานะระบบและผู้สร้าง"""
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


def animate_startup_banner() -> None:
    """อนิเมชั่น Cyber Glitch Decode + Neon Gradient Wave เมื่อเปิด Hub ครั้งแรก"""
    if os.environ.get("XTOOLS_NO_ANIM") == "1":
        render_static_banner()
        return

    glyphs = "#@%&$*+=-:/\\|"
    width = max(len(line) for line in BANNER_ART)
    frames = 10

    sys.stdout.write("\033[?25l")  # ซ่อนเคอร์เซอร์
    try:
        for step in range(frames + 1):
            locked_cols = int((step / frames) * width)
            out_lines = []
            for r_idx, line in enumerate(BANNER_ART):
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
                sys.stdout.write(f"\033[{len(BANNER_ART)}A")
            sys.stdout.write("\n".join(out_lines) + "\n")
            sys.stdout.flush()
            time.sleep(0.032)
    finally:
        sys.stdout.write("\033[?25h")  # คืนค่าเคอร์เซอร์

    print(get_subtitle_line())


def render_static_banner() -> None:
    """แสดงแบนเนอร์แบบคงที่สำหรับหน้าเมนูย่อย"""
    art = "\n".join(BANNER_ART)
    print(f"{CYAN}{BOLD}\n{art}\n{RESET}{get_subtitle_line()}")
