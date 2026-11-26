"""
main.py — Rust-First Studio (rust-anything)
XTools Dev → rust-anything

มาตรฐาน XTools: ทุกโปรเจกต์ที่รับมาหรือสร้างใหม่ต้องจบเป็น Rust
                                               เบา · เร็ว · ลื่น · ประหยัดพื้นที่ · เสถียร

ตัวนี้เป็นเพียงตัวเรียกใช้ (thin wrapper) ของ CLI `rust-anything`
ไม่ได้ reimplement อะไร — ถ้าต้องการ argument ดิบให้ส่งผ่านบรรทัดคำสั่ง:
    python main.py analyze . --lang python
    python main.py diff rust/my-crate
"""

import os
import shutil
import subprocess
import sys
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

BIN_NAME = "rust-anything"
INSTALL_CARGO = ["cargo", "install", "rust-anything"]
INSTALL_NPM = ["npm", "install", "-g", "rust-anything"]
RELEASES_URL = "https://github.com/erkamyaman/rust-anything/releases"
DOCS_URL = "https://rust-anything.com/"
POLICY = f"{DIM}มาตรฐาน XTools: {RESET}{GREEN}เบา{RESET} · {GREEN}เร็ว{RESET} · {GREEN}ลื่น{RESET} · {GREEN}ประหยัดพื้นที่{RESET} · {GREEN}เสถียร{RESET}"

_BOX_W = 62

enable_windows_vt()


def clear() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def _h(title: str) -> None:
    head = f"── [ Rust-First Studio — {title} ] "
    print(f"{BOLD}{CYAN}┌{head}{'─' * max(0, _BOX_W - len(head))}┐{RESET}")


def _sep(label: str = "") -> None:
    head = f"├── {label} "
    print(f"{BOLD}{CYAN}{head}{'─' * max(0, _BOX_W - len(head) + 1)}┤{RESET}")


def _f() -> None:
    print(f"{BOLD}{CYAN}└{'─' * _BOX_W}┘{RESET}\n")


def find_binary() -> str | None:
    """หา rust-anything: PATH ก่อน แล้วค่อยเดาจาก cargo / npm global"""
    found = shutil.which(BIN_NAME)
    if found:
        return found
    exe = f"{BIN_NAME}.exe" if os.name == "nt" else BIN_NAME
    candidates = [
        Path.home() / ".cargo" / "bin" / exe,
        Path(os.environ.get("APPDATA", "")) / "npm" / f"{BIN_NAME}.cmd",
        Path("/usr/local/bin") / BIN_NAME,
        Path("/opt/homebrew/bin") / BIN_NAME,
    ]
    for c in candidates:
        if c.is_file():
            return str(c)
    return None


def _run(cmd: list[str], cwd: Path | None = None) -> int:
    print(f"{DIM}$ {' '.join(cmd)}{RESET}")
    if cwd:
        print(f"{DIM}  cwd: {cwd}{RESET}")
    print()
    try:
        return subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=False).returncode
    except FileNotFoundError as e:
        print(f"{RED}[ผิดพลาด] ไม่พบคำสั่ง: {e}{RESET}")
        return 127
    except KeyboardInterrupt:
        print(f"\n{YELLOW}[!] ยกเลิกโดยผู้ใช้{RESET}")
        return 130


def _pause(msg: str = "  กด Enter เพื่อกลับ...") -> None:
    wave_input(f"{DIM}{msg}{RESET}")


def _ask_path(label: str = "  โปรเจกต์ (Enter = โฟลเดอร์ปัจจุบัน): ") -> Path | None:
    raw = wave_input(label).strip() or "."
    p = Path(raw).expanduser()
    try:
        p = p.resolve()
    except OSError:
        pass
    if not p.is_dir():
        print(f"  {RED}[ผิดพลาด] ไม่พบโฟลเดอร์: {p}{RESET}")
        _pause()
        return None
    return p


def _ask_text(label: str) -> str:
    return wave_input(label).strip()


def status(binary: str | None) -> str:
    if not binary:
        return f"{RED}● ยังไม่ได้ติดตั้ง{RESET} {DIM}(แนะนำ: cargo install rust-anything){RESET}"
    try:
        out = subprocess.run(
            [binary, "--version"], capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=15, check=False,
        )
        ver = (out.stdout or out.stderr).strip().splitlines()[0] if (out.stdout or out.stderr).strip() else "OK"
    except Exception:
        ver = "OK"
    return f"{GREEN}● พร้อมใช้{RESET} {DIM}{ver} · {binary}{RESET}"


def _install_menu() -> None:
    clear()
    _h("ติดตั้ง")
    print(f"\n  {DIM}เลือกวิธีติดตั้ง (ใช้ครั้งเดียว) — ต้องมี cargo หรือ npm{RESET}\n")
    cargo_ok = shutil.which("cargo") is not None
    npm_ok = shutil.which("npm") is not None
    print(f"  {CYAN}[1]{RESET} cargo install rust-anything  {' ' + GREEN + 'พร้อม' + RESET if cargo_ok else ' ' + DIM + '(ไม่พบ cargo)' + RESET}")
    print(f"  {CYAN}[2]{RESET} npm install -g rust-anything  {' ' + GREEN + 'พร้อม' + RESET if npm_ok else ' ' + DIM + '(ไม่พบ npm)' + RESET}")
    print(f"  {CYAN}[3]{RESET} เปิดหน้าดาวน์โหลด binary สำเร็จรูป  {DIM}(Windows/macOS/Linux){RESET}")
    print(f"  {DIM}[0]{RESET} กลับ")
    _f()
    choice = wave_input(f"  {BOLD}ติดตั้ง > {RESET}").strip().lower()
    if choice == "1":
        _run(INSTALL_CARGO)
    elif choice == "2":
        _run(INSTALL_NPM)
    elif choice == "3":
        _open_url(RELEASES_URL)
        return
    else:
        return
    _pause()


def _open_url(url: str) -> None:
    try:
        if os.name == "nt":
            os.startfile(url)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", url], check=False)
        else:
            subprocess.run(["xdg-open", url], check=False)
        print(f"  {GREEN}[OK] เปิดเบราว์เซอร์: {url}{RESET}\n")
    except Exception:
        print(f"  {YELLOW}เปิดเองที่: {url}{RESET}\n")
    _pause()


def _step(binary: str, title: str, build) -> None:
    """เรียก build(args, cwd) แล้วรัน — ใช้ร่วมกันทุกเมนูเพื่อไม่ให้โค้ดซ้ำ"""
    clear()
    _h(title)
    print()
    plan = build()
    if plan is None:
        return
    args, cwd = plan
    _run([binary, *args], cwd)
    print()
    _pause()


def _plan_analyze() -> tuple[list[str], Path] | None:
    print(f"  {DIM}วิเคราะห์ภาษา โครงสร้าง และความเสี่ยงก่อน port{RESET}\n")
    p = _ask_path()
    if not p:
        return None
    lang = _ask_text("  บังคับภาษา (ว่าง = ตรวจจับเอง, เช่น python/ts/go): ")
    args = ["analyze", str(p)]
    if lang:
        args += ["--lang", lang]
    return args, p


def _plan_profile() -> tuple[list[str], Path] | None:
    print(f"  {DIM}หา hot path: ระบุคำสั่งที่ใช้รันโปรเจกต์ (เช่น 'python app.py'){RESET}\n")
    p = _ask_path()
    if not p:
        return None
    cmd = _ask_text("  คำสั่งรัน: ")
    if not cmd:
        print(f"  {RED}[ผิดพลาด] ต้องระบุคำสั่งรัน{RESET}")
        _pause()
        return None
    import shlex
    return ["profile", str(p), "--", *shlex.split(cmd)], p


def _plan_bridge() -> tuple[list[str], Path] | None:
    print(f"  {DIM}สร้าง crate Rust + wrapper ให้ API เดิมเรียกได้{RESET}\n")
    p = _ask_path()
    if not p:
        return None
    unit = _ask_text("  ไฟล์/โฟลเดอร์ที่จะ port (เช่น src/fuzzy.ts): ")
    if not unit:
        print(f"  {RED}[ผิดพลาด] ต้องระบุ unit{RESET}")
        _pause()
        return None
    args = ["bridge", str(p), unit]
    batch = _ask_text("  batch (ว่าง = ไม่ใช้, เช่น fuzzyScore:text): ")
    if batch:
        args += ["--batch", batch]
    return args, p


def _plan_crate(action: str, hint: str) -> "callable":
    def build():
        print(f"  {DIM}{hint}{RESET}\n")
        crate = _ask_text("  crate Rust (เช่น rust/my-crate): ")
        if not crate:
            print(f"  {RED}[ผิดพลาด] ต้องระบุ crate{RESET}")
            _pause()
            return None
        c = Path(crate).expanduser()
        args = [action, str(c)]
        if action in ("diff", "gate", "fuzz"):
            time_s = _ask_text("  เวลาสุ่มเพิ่ม (วินาที, ว่าง = ค่าเริ่มต้น): ")
            if time_s.isdigit():
                args += ["--time", time_s]
        return args, _ROOT
    return build


def menu(binary: str) -> None:
    while True:
        clear()
        _h("Dashboard")
        print(f"\n  สถานะ: {status(binary)}\n")
        print(f"  {POLICY}\n")
        _sep("ลำดับงานมาตรฐาน")
        print(f"  {DIM}analyze → profile → bridge → record → diff → bench → gate{RESET}\n")
        _sep("คำสั่ง")
        print(f"  {CYAN}[1]{RESET} Analyze   วิเคราะห์โปรเจกต์ก่อน port")
        print(f"  {CYAN}[2]{RESET} Profile   หา hot path ที่คุ้มย้าย")
        print(f"  {CYAN}[3]{RESET} Bridge    สร้าง crate + wrapper")
        print(f"  {CYAN}[4]{RESET} Record    บันทึกพฤติกรรมเดิมเป็นชุดทดสอบ")
        print(f"  {CYAN}[5]{RESET} Diff      เทียบ port กับของเดิมทุกเคส")
        print(f"  {CYAN}[6]{RESET} Bench     วัดความเร็ว/ขนาดจริง")
        print(f"  {CYAN}[7]{RESET} Gate      ประตูปิดงาน (ต้องผ่านก่อน ship)")
        print(f"  {CYAN}[8]{RESET} Build     คอมไพล์ crate")
        print(f"  {CYAN}[9]{RESET} Fuzz      ยิงอินพุตใหม่หาจุดที่ recording พลาด")
        print(f"  {GREEN}[S]{RESET} Setup     ลงทะเบียนกับ Claude Code / Codex / Cursor / Gemini")
        print(f"  {BLUE}[D]{RESET} Docs      เปิดเอกสาร rust-anything")
        print(f"  {DIM}[0]{RESET} ออก")
        _f()

        choice = wave_input(f"  {BOLD}Rust > {RESET}").strip().lower()

        if choice in ("0", "q"):
            break
        if not choice:
            continue

        if binary is None:
            if choice in ("1", "2", "3", "s", "d"):
                if choice == "1" or choice == "2":
                    _install_menu()
                elif choice == "3":
                    _open_url(RELEASES_URL)
                elif choice == "s":
                    print(f"\n  {YELLOW}ต้องติดตั้ง rust-anything ก่อน{RESET}")
                    _pause()
                else:
                    _open_url(DOCS_URL)
            else:
                print(f"\n  {RED}ต้องติดตั้ง rust-anything ก่อน (กด [1] หรือ [2]){RESET}")
                _pause()
            continue

        if choice == "1":
            _step(binary, "Analyze", _plan_analyze)
        elif choice == "2":
            _step(binary, "Profile", _plan_profile)
        elif choice == "3":
            _step(binary, "Bridge", _plan_bridge)
        elif choice == "4":
            _step(binary, "Record", _plan_crate("record", "บันทึกพฤติกรรมของ original (ต้องมี crate จาก bridge ก่อน)"))
        elif choice == "5":
            _step(binary, "Diff", _plan_crate("diff", "เทียบทุกเคสที่บันทึกไว้ — ต้องตรงทั้งหมด"))
        elif choice == "6":
            _step(binary, "Bench", _plan_crate("bench", "วัดว่าเร็วขึ้นจริงไหม (ไม่เดา)"))
        elif choice == "7":
            _step(binary, "Gate", _plan_crate("gate", "ปิดงานเมื่อ diff ผ่านและไม่มี fallback"))
        elif choice == "8":
            _step(binary, "Build", _plan_crate("build", "คอมไพล์ crate"))
        elif choice == "9":
            _step(binary, "Fuzz", _plan_crate("fuzz", "ยิงอินพุตใหม่ หาเคสที่ recording ไม่ครอบคลุม"))
        elif choice == "s":
            clear()
            _h("Setup")
            _run([binary, "setup"])
            print()
            _pause()
        elif choice == "d":
            _open_url(DOCS_URL)


def main() -> int:
    args = sys.argv[1:]
    binary = find_binary()

    # โหมดส่งผ่านคำสั่งตรง ๆ (ให้ XTools เรียกใช้แบบ scriptable ได้)
    if args:
        if binary is None:
            print(f"{RED}[ผิดพลาด] ยังไม่ได้ติดตั้ง rust-anything{RESET}")
            print(f"{DIM}ติดตั้ง: cargo install rust-anything  ({RELEASES_URL}){RESET}")
            return 1
        return _run([binary, *args])

    if binary is None:
        print(f"{YELLOW}[!] ยังไม่พบ rust-anything ในเครื่อง{RESET}")
        print(f"{DIM}    เปิดเมนูติดตั้งให้อัตโนมัติ...{RESET}\n")

    menu(binary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
