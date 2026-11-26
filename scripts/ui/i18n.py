"""
ระบบภาษาและการตั้งค่าผู้ใช้ (Localization & Persistence)
"""

import json
from scripts.config.constants import CONFIG_PATH

STRINGS = {
    "en": {
        "select_cat": "Select Category Workspace",
        "sys_check": "System Check",
        "sys_check_desc": "Check runtimes, PATH, disk & GitHub API",
        "update": "Update XTools",
        "update_desc": "Re-run installer from GitHub",
        "lang_label": "Language",
        "lang_desc": "Switch EN / TH (Saved permanently)",
        "exit": "Exit",
        "bye": "Session closed. See you next time.",
        "no_tools": "(No tools found in scripts/{folder}/ yet)",
        "back": "Back to Main Hub",
        "select": "Choose Option",
        "press_enter": "Press Enter to return...",
        "press_cont": "Press Enter to continue...",
        "running": "Launching",
        "interrupted": "Execution cancelled by user.",
        "doctor_title": "=== XTools System & Environment Diagnostics ===",
    },
    "th": {
        "select_cat": "เลือกหมวดหมู่เครื่องมือการทำงาน",
        "sys_check": "ตรวจสอบระบบ",
        "sys_check_desc": "เช็ค Python, Git, Rust, Node, PATH และสถานะเครื่อง",
        "update": "อัปเดต XTools",
        "update_desc": "ดาวน์โหลดและอัปเดตเวอร์ชันล่าสุดจาก GitHub",
        "lang_label": "ภาษา / Language",
        "lang_desc": "สลับภาษา EN / TH (บันทึกค่าอัตโนมัติ)",
        "exit": "ออกจากโปรแกรม",
        "bye": "ปิดการทำงานเรียบร้อย แล้วพบกันใหม่",
        "no_tools": "(ยังไม่มีไฟล์สคริปต์ใน scripts/{folder}/)",
        "back": "ย้อนกลับหน้าหลัก",
        "select": "เลือกหมายเลข",
        "press_enter": "กดปุ่ม Enter เพื่อกลับหน้าหลัก...",
        "press_cont": "กดปุ่ม Enter เพื่อดำเนินการต่อ...",
        "running": "กำลังเปิดใช้งาน",
        "interrupted": "ยกเลิกการทำงาน",
        "doctor_title": "=== ตรวจสอบความพร้อมของระบบและสภาพแวดล้อม (Doctor) ===",
    },
}


def load_lang() -> str:
    """โหลดภาษาที่บันทึกไว้ (ค่าเริ่มต้น: th)"""
    try:
        if CONFIG_PATH.is_file():
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            if data.get("lang") in ("en", "th"):
                return data["lang"]
    except Exception:
        pass
    return "th"


def save_lang(lang: str) -> None:
    """บันทึกภาษาลงไฟล์คอนฟิกในเครื่อง"""
    try:
        data = {}
        if CONFIG_PATH.is_file():
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        data["lang"] = lang
        CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass


_current_lang = load_lang()


def get_current_lang() -> str:
    return _current_lang


def set_current_lang(lang: str) -> None:
    global _current_lang
    _current_lang = lang
    save_lang(lang)


def t(key: str) -> str:
    """ดึงข้อความตามภาษาปัจจุบัน"""
    return STRINGS.get(_current_lang, STRINGS["th"]).get(key, key)
