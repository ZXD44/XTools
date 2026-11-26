"""
ระบบสแกนและค้นพบโปรเจกต์ย่อย/ปลั๊กอินอัตโนมัติ (Plugin & Script Discovery)
"""

import json
from dataclasses import dataclass
from pathlib import Path
from scripts.config.constants import CATEGORIES, SCRIPTS_DIR, SUPPORTED_EXTS
from scripts.ui.i18n import t


@dataclass
class ToolEntry:
    name: str
    desc: str
    entry: Path
    runtime: str
    cwd: Path


def discover_category_tools(folder: str) -> list[ToolEntry]:
    """ค้นหาไฟล์สคริปต์เดี่ยว หรือโฟลเดอร์ที่มี tool.json ภายในหมวดหมู่ที่กำหนด"""
    target = SCRIPTS_DIR / folder
    if not target.exists():
        return []

    tools: list[ToolEntry] = []
    for item in sorted(target.iterdir()):
        # 1. ตรวจพบไฟล์สคริปต์เดี่ยว (.py, .bat, .ps1, .sh, .js, .ts, .exe)
        if item.is_file() and item.suffix.lower() in SUPPORTED_EXTS:
            tools.append(
                ToolEntry(
                    name=item.stem,
                    desc=t("script_exec").format(ext=item.suffix.lstrip(".").upper()),
                    entry=item,
                    runtime="auto",
                    cwd=item.parent,
                )
            )
        # 2. ตรวจพบโฟลเดอร์โปรเจกต์ย่อยที่มี manifest (tool.json)
        elif item.is_dir():
            manifest = item / "tool.json"
            if manifest.is_file():
                try:
                    meta = json.loads(manifest.read_text(encoding="utf-8"))
                    entry_path = item / meta.get("entry", "")
                    if entry_path.exists():
                        tools.append(
                            ToolEntry(
                                name=meta.get("name", item.name),
                                desc=meta.get("desc", t("plugin_mod")),
                                entry=entry_path,
                                runtime=meta.get("runtime", "auto"),
                                cwd=item,
                            )
                        )
                except Exception:
                    continue
    return tools


def discover_all_workspace_tools() -> list[ToolEntry]:
    """สแกนเครื่องมือทั้งหมดจากทุกหมวดหมู่"""
    all_tools: list[ToolEntry] = []
    for _, _, _, folder, _, _ in CATEGORIES:
        all_tools.extend(discover_category_tools(folder))
    return all_tools
