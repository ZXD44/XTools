"""
ระบบรันคำสั่งหลาย Runtime และโปรเจกต์ภายนอก (Multi-Runtime Runner)
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from scripts.config.constants import BOLD, CYAN, DIM, RED, RESET, YELLOW
from scripts.core.discovery import ToolEntry
from scripts.ui.i18n import t


def resolve_python_runtime(cwd: Path) -> str:
    """ตรวจสอบว่าโปรเจกต์ย่อยมี Virtual Environment (.venv) เฉพาะตัวหรือไม่"""
    candidates = [
        cwd / ".venv" / "Scripts" / "python.exe",
        cwd / ".venv" / "bin" / "python",
    ]
    for c in candidates:
        if c.is_file():
            return str(c)
    return sys.executable


def execute_tool(tool: ToolEntry, extra_args: list[str] | None = None) -> None:
    """สั่งรันเครื่องมือตามประเภท Runtime ที่ระบุ"""
    args = extra_args or []
    ext = tool.entry.suffix.lower()
    rt = tool.runtime.lower()

    # ตรวจสอบ Runtime อัตโนมัติจากนามสกุลไฟล์
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

    # กำหนดคำสั่งรันตาม Runtime
    if rt == "python":
        cmd = [resolve_python_runtime(tool.cwd), str(tool.entry), *args]
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

    print(f"\n{CYAN}[>]{RESET} {t('running')} {BOLD}{tool.name}{RESET} ({DIM}{rt}{RESET})...\n")
    try:
        subprocess.run(cmd, cwd=str(tool.cwd), check=False)
    except FileNotFoundError as e:
        print(f"{RED}[ERROR] Runtime not found: {e}{RESET}")
    except KeyboardInterrupt:
        print(f"\n{YELLOW}[!] {t('interrupted')}{RESET}")
