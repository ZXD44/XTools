#!/usr/bin/env python3
"""XTools Interactive CLI Hub."""

import os
import subprocess
import sys
from pathlib import Path

# Enable ANSI escape sequences on Windows 10/11
if os.name == "nt":
    os.system("")

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


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def print_banner() -> None:
    print(f"""{CYAN}{BOLD}
 __  _______ ___   ___  _     ____  
 \ \/ /_   _/ _ \ / _ \| |   / ___| 
  \  /  | || | | | | | | |   \___ \ 
  /  \  | || |_| | |_| | |___ ___) |
 /_/\_\ |_| \___/ \___/|_____|____/ 
{RESET}{DIM}  XTools Hub | ZXD44/XTools | Python {sys.version.split()[0]}{RESET}
""")


def list_category_scripts(folder: str) -> list[Path]:
    target = SCRIPTS_DIR / folder
    if not target.exists():
        return []
    return sorted(
        p for p in target.iterdir()
        if p.is_file() and p.suffix in {".py", ".bat", ".ps1", ".sh"}
    )


def run_script(path: Path) -> None:
    print(f"\n{CYAN}[>]{RESET} Running {BOLD}{path.name}{RESET}...\n")
    try:
        if path.suffix == ".py":
            subprocess.run([sys.executable, str(path)], check=False)
        elif path.suffix == ".bat":
            subprocess.run(["cmd", "/c", str(path)], check=False)
        elif path.suffix == ".ps1":
            subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", str(path)], check=False)
        elif path.suffix == ".sh":
            subprocess.run(["bash", str(path)], check=False)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}[!] Interrupted.{RESET}")
    input(f"\n{DIM}Press Enter to return...{RESET}")


def category_menu(title: str, folder: str) -> None:
    while True:
        clear_screen()
        print_banner()
        print(f"{BOLD}{BLUE}=== {title} ==={RESET}\n")
        scripts = list_category_scripts(folder)
        if not scripts:
            print(f"  {DIM}(No scripts in scripts/{folder}/ yet){RESET}\n")
        else:
            for idx, s in enumerate(scripts, 1):
                print(f"  {CYAN}[{idx}]{RESET} {s.name}")
            print()
        print(f"  {DIM}[0] Back{RESET}\n")
        choice = input(f"{BOLD}Select > {RESET}").strip()
        if choice == "0" or choice == "":
            return
        if choice.isdigit() and 1 <= int(choice) <= len(scripts):
            run_script(scripts[int(choice) - 1])


def main() -> None:
    while True:
        clear_screen()
        print_banner()
        print(f"{BOLD}Select Category:{RESET}\n")
        for key, title, _, desc in CATEGORIES:
            print(f"  {CYAN}[{key}]{RESET} {BOLD}{title:<20}{RESET} {DIM}{desc}{RESET}")
        print(f"\n  {YELLOW}[U]{RESET} Update XTools        {DIM}Re-run installer from GitHub{RESET}")
        print(f"  {RED}[0]{RESET} Exit\n")

        choice = input(f"{BOLD}XTools > {RESET}").strip().lower()
        if choice == "0" or choice == "q":
            print(f"{DIM}Bye.{RESET}")
            break
        elif choice == "u":
            if os.name == "nt":
                subprocess.run([
                    "powershell", "-NoProfile", "-Command",
                    "irm 'https://raw.githubusercontent.com/ZXD44/XTools/main/install.ps1' | iex"
                ], check=False)
            else:
                subprocess.run([
                    "bash", "-c",
                    "curl -fsSL https://raw.githubusercontent.com/ZXD44/XTools/main/install.sh | bash"
                ], check=False)
            input(f"\n{DIM}Press Enter to continue...{RESET}")
        else:
            matched = [c for c in CATEGORIES if c[0] == choice]
            if matched:
                _, title, folder, _ = matched[0]
                category_menu(title, folder)


if __name__ == "__main__":
    main()
