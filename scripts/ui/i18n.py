"""
ระบบภาษาและการตั้งค่าผู้ใช้ (Localization & Persistence)
"""

import json
from scripts.config.constants import CONFIG_PATH

STRINGS = {
    "en": {
        "select_cat": "Select Category Workspace",
        "quick_actions": "Quick Actions",
        "sys_check": "System Check",
        "sys_check_desc": "Check runtimes, PATH, disk & GitHub API",
        "update": "Update XTools",
        "update_desc": "Re-run installer from GitHub",
        "update_badge": "[UPDATE: {old} -> {new} — press U]",
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
        "runtime_not_found": "[ERROR] Runtime not found: {err}",
        "script_exec": "{ext} executable",
        "plugin_mod": "Plugin module",
        "doctor_title": "=== XTools System & Environment Diagnostics ===",
        "runtimes_header": "Runtimes & Compilers:",
        "not_installed": "not installed",
        "env_header": "Environment Integration:",
        "in_path": "in PATH",
        "not_in_path": "not in current PATH session",
        "disk_free": "Disk Free  :",
    },
    "th": {
        "select_cat": "เลือกหมวดหมู่เครื่องมือการทำงาน",
        "quick_actions": "คำสั่งระบบและตั้งค่า",
        "sys_check": "ตรวจสอบระบบ",
        "sys_check_desc": "เช็ค Python, Git, Rust, Node, PATH และสถานะเครื่อง",
        "update": "อัปเดต XTools",
        "update_desc": "ดาวน์โหลดและอัปเดตเวอร์ชันล่าสุดจาก GitHub",
        "update_badge": "[มีอัปเดตใหม่: {old} -> {new} — กด U]",
        "lang_label": "ภาษา",
        "lang_desc": "สลับภาษา ไทย / อังกฤษ (บันทึกค่าอัตโนมัติ)",
        "exit": "ออกจากโปรแกรม",
        "bye": "ปิดการทำงานเรียบร้อย แล้วพบกันใหม่",
        "no_tools": "(ยังไม่มีไฟล์สคริปต์ใน scripts/{folder}/)",
        "back": "ย้อนกลับหน้าหลัก",
        "select": "เลือกหมายเลข",
        "press_enter": "กดปุ่ม Enter เพื่อกลับหน้าหลัก...",
        "press_cont": "กดปุ่ม Enter เพื่อดำเนินการต่อ...",
        "running": "กำลังเปิดใช้งาน",
        "interrupted": "ยกเลิกการทำงาน",
        "runtime_not_found": "[ผิดพลาด] ไม่พบรันไทม์: {err}",
        "script_exec": "สคริปต์ {ext}",
        "plugin_mod": "โมดูลปลั๊กอิน",
        "doctor_title": "=== ตรวจสอบความพร้อมของระบบและสภาพแวดล้อม ===",
        "runtimes_header": "รันไทม์และคอมไพเลอร์:",
        "not_installed": "ยังไม่ได้ติดตั้ง",
        "env_header": "การเชื่อมต่อระบบ:",
        "in_path": "พร้อมใช้งานใน PATH",
        "not_in_path": "ยังไม่อยู่ใน PATH ปัจจุบัน",
        "disk_free": "พื้นที่ว่าง :",
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
