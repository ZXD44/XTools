#!/usr/bin/env python3
"""XTools Interactive CLI Hub — Multi-runtime, plugin auto-discovery, doctor & direct CLI."""

import json
import os
import shutil
import subprocess
import sys
import threading
import urllib.request
from dataclasses import dataclass
from pathlib import Path

# Enable ANSI escape sequences on Windows 10/11
if os.name == "nt":
    os.system("")

VERSION = "1.0.0"
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

CATEGORIES = [
    ("1", "System & Cleanup", "system", "System info, temp cleanup, startup & env tools"),
    ("2", "Dev & Git", "dev", "Repo utilities, formatters, environment helpers"),
    ("3", "Network & Security", "network", "Diagnostics, port checks, hash & audit tools"),
    ("4", "Media & Files", "media", "Batch rename, image/icon converters, archivers"),
]

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


def print_banner() -> None:
    update_badge = (
        f"  {YELLOW}[UPDATE AVAILABLE: v{_latest_version} — press U]{RESET}"
        if _latest_version
        else ""
    )
    print(f"""{CYAN}{BOLD}
 __  _______ ___   ___  _     ____  
 \ \/ /_   _/ _ \ / _ \| |   / ___| 
  \  /  | || | | | | | | |   \___ \ 
  /  \  | || |_| | |_| | |___ ___) |
 /_/\_\ |_| \___/ \___/|_____|____/ 
{RESET}{DIM}  XTools Hub v{VERSION} | {REPO} | Python {sys.version.split()[0]}{RESET}{update_badge}
""")


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
    for _, _, folder, _ in CATEGORIES:
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
            print(f"  {DIM}(No tools in scripts/{folder}/ yet){RESET}\n")
        else:
            for idx, t in enumerate(tools, 1):
                print(f"  {CYAN}[{idx}]{RESET} {BOLD}{t.name:<22}{RESET} {DIM}{t.desc}{RESET}")
            print()
        print(f"  {DIM}[0] Back{RESET}\n")
        choice = input(f"{BOLD}Select > {RESET}").strip()
        if choice == "0" or choice == "":
            return
        if choice.isdigit() and 1 <= int(choice) <= len(tools):
            run_tool(tools[int(choice) - 1])
            input(f"\n{DIM}Press Enter to return...{RESET}")


def interactive_menu() -> None:
    threading.Thread(target=check_latest_version_bg, daemon=True).start()
    while True:
        clear_screen()
        print_banner()
        print(f"{BOLD}Select Category:{RESET}\n")
        for key, title, _, desc in CATEGORIES:
            print(f"  {CYAN}[{key}]{RESET} {BOLD}{title:<20}{RESET} {DIM}{desc}{RESET}")
        print(f"\n  {GREEN}[S]{RESET} System Check         {DIM}Check runtimes, PATH, disk & GitHub API{RESET}")
        print(f"  {YELLOW}[U]{RESET} Update XTools        {DIM}Re-run installer from GitHub{RESET}")
        print(f"  {RED}[0]{RESET} Exit\n")

        choice = input(f"{BOLD}XTools > {RESET}").strip().lower()
        if choice in {"0", "q", "exit"}:
            print(f"{DIM}Bye.{RESET}")
            break
        elif choice == "s":
            clear_screen()
            print_banner()
            run_doctor()
            input(f"\n{DIM}Press Enter to return...{RESET}")
        elif choice == "u":
            run_update()
            input(f"\n{DIM}Press Enter to continue...{RESET}")
        else:
            matched = [c for c in CATEGORIES if c[0] == choice]
            if matched:
                _, title, folder, _ = matched[0]
                category_menu(title, folder)


def main() -> None:
    args = sys.argv[1:]
    if not args:
        interactive_menu()
        return

    cmd = args[0].lower()
    if cmd in {"doctor", "check", "env"}:
        run_doctor()
    elif cmd in {"update", "upgrade"}:
        run_update()
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
