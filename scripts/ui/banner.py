"""
แบนเนอร์และอนิเมชั่นแสดงผลหน้าตาคอนโซล (Banner & Continuous Water Wave Animation)
"""

import math
import os
import random
import subprocess
import sys
import threading
import time
from scripts.config.constants import (
    BLUE,
    BOLD,
    BUILD,
    CYAN,
    DIM,
    NEON_PALETTE,
    RED,
    RESET,
    ROOT_DIR,
    VERSION,
    YELLOW,
)
from scripts.ui.i18n import t

BANNER_ART = [
    r" __  _______ ___   ___  _     ____  ",
    r" \ \/ /_   _/ _ \ / _ \| |   / ___| ",
    r"  \  /  | || | | | | | | |   \___ \ ",
    r"  /  \  | || |_| | |_| | |___ ___) |",
    r" /_/\_\ |_| \___/ \___/|_____|____/ ",
]

_latest_version: str | None = None
_render_lock = threading.Lock()
_wave_phase: float = 0.0


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
    build_id = get_build_id()
    current_ver = f"v{VERSION}-{build_id}"
    update_badge = (
        f"  {YELLOW}{t('update_badge').format(old=current_ver, new=f'v{_latest_version}')}{RESET}"
        if _latest_version
        else ""
    )
    return (
        f"  {CYAN}XTools Hub v{VERSION} {DIM}({build_id}){RESET} {DIM}|{RESET} "
        f"{RED}{BOLD}ZXD44{RESET}{DIM}/XTools{RESET} {DIM}|{RESET} "
        f"{BLUE}Python {sys.version.split()[0]}{RESET}{update_badge}\n"
    )


def _water_rgb(col: int, row: int, phase: float) -> tuple[int, int, int]:
    """คำนวณสีคลื่นน้ำแบบ Dual-Harmonic Sine Wave 2D (น้ำเงินเข้ม -> ฟ้า -> อควา -> ฟองคลื่นขาว)"""
    w1 = math.sin(col * 0.22 - phase + row * 0.65)
    w2 = math.sin(col * 0.11 + phase * 0.6 - row * 0.40) * 0.35
    val = max(0.0, min(1.0, (w1 + w2 + 1.35) / 2.7))
    crest = val ** 2.4
    r = int(8 + crest * 205)
    g = int(85 + val * 155 + crest * 15)
    b = int(175 + val * 80)
    return min(r, 255), min(g, 255), min(b, 255)


def render_wave_frame(phase: float = 0.0) -> str:
    """สร้างเฟรมแบนเนอร์คลื่นน้ำ 1 เฟรม"""
    lines = []
    for r_idx, line in enumerate(BANNER_ART):
        buf = []
        for c_idx, ch in enumerate(line):
            if ch == " ":
                buf.append(" ")
            else:
                r, g, b = _water_rgb(c_idx, r_idx, phase)
                buf.append(f"\033[38;2;{r};{g};{b}m{BOLD}{ch}")
        buf.append(RESET)
        lines.append("".join(buf))
    return "\n".join(lines)


def animate_startup_banner() -> None:
    """อนิเมชั่น Cyber Glitch Decode ก่อนเข้าสู่คลื่นน้ำ"""
    if os.environ.get("XTOOLS_NO_ANIM") == "1" or not sys.stdout.isatty():
        render_static_banner()
        return

    glyphs = "#@%&$*+=-:/\\|"
    width = max(len(line) for line in BANNER_ART)
    frames = 8

    sys.stdout.write("\033[?25l")
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
                        r, g, b = _water_rgb(c_idx, r_idx, step * 0.35)
                        buf.append(f"\033[38;2;{r};{g};{b}m{BOLD}{ch}")
                    else:
                        color = NEON_PALETTE[(c_idx + step) % len(NEON_PALETTE)]
                        buf.append(f"{color}{DIM}{random.choice(glyphs)}{RESET}")
                buf.append(RESET)
                out_lines.append("".join(buf))
            if step > 0:
                sys.stdout.write(f"\033[{len(BANNER_ART)}A")
            sys.stdout.write("\n".join(out_lines) + "\n")
            sys.stdout.flush()
            time.sleep(0.03)
    finally:
        sys.stdout.write("\033[?25h")

    print(get_subtitle_line())


def render_static_banner() -> None:
    """แสดงแบนเนอร์คลื่นน้ำเฟรมปัจจุบัน"""
    print(f"{render_wave_frame(_wave_phase)}\n{get_subtitle_line()}")


def wave_input(prompt: str) -> str:
    """รับค่าจากผู้ใช้พร้อมขยับแบนเนอร์เป็นคลื่นน้ำตลอดเวลา"""
    if os.environ.get("XTOOLS_NO_ANIM") == "1" or not (sys.stdout.isatty() and sys.stdin.isatty()):
        return input(prompt)

    stop_event = threading.Event()

    def _wave_worker() -> None:
        global _wave_phase
        last_ver = _latest_version
        while not stop_event.is_set():
            frame = render_wave_frame(_wave_phase)
            curr_ver = _latest_version
            sub_patch = ""
            if curr_ver != last_ver:
                last_ver = curr_ver
                sub_patch = f"\033[6;1H\033[2K{get_subtitle_line().rstrip(chr(10))}"
            with _render_lock:
                if stop_event.is_set():
                    break
                sys.stdout.write(f"\033[s\033[?25l\033[1;1H{frame}{sub_patch}\033[u\033[?25h")
                sys.stdout.flush()
            _wave_phase += 0.26
            stop_event.wait(0.055)

    sys.stdout.write(prompt)
    sys.stdout.flush()

    worker = threading.Thread(target=_wave_worker, daemon=True)
    worker.start()

    try:
        if os.name == "nt":
            import msvcrt

            buf: list[str] = []
            while True:
                ch = msvcrt.getwch()
                if ch in ("\r", "\n"):
                    with _render_lock:
                        sys.stdout.write("\n")
                        sys.stdout.flush()
                    return "".join(buf)
                elif ch == "\x03":
                    raise KeyboardInterrupt
                elif ch in ("\x08", "\x7f"):
                    if buf:
                        buf.pop()
                        with _render_lock:
                            sys.stdout.write("\b \b")
                            sys.stdout.flush()
                elif ch in ("\x00", "\xe0"):
                    msvcrt.getwch()
                elif ch >= " ":
                    buf.append(ch)
                    with _render_lock:
                        sys.stdout.write(ch)
                        sys.stdout.flush()
        else:
            return input("")
    finally:
        stop_event.set()
        worker.join(timeout=0.2)
