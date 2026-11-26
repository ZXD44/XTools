//! The Rust port of `scripts/ui/`.
//!
//! Ported unit: `t` (`scripts/ui/i18n.py:109`). Everything else in this unit stays in Python
//! (terminal rendering, stdin, file I/O on user config) and is re-exported by the shadow module.
//!
//! Behavior kept exactly from the original:
//! - language comes from `~/.xtools_config.json` key `lang` (`en` | `th`), default `th`
//! - an unknown key returns the key itself, in both languages
//! - the lookup is the same `STRINGS[lang]` table, no cross-language fallback

#![forbid(unsafe_code)]

use std::path::PathBuf;
use std::sync::OnceLock;

const EN: &[(&str, &str)] = &[
    ("select_cat", "Select Category Workspace"),
    ("quick_actions", "Quick Actions"),
    ("sys_check", "System Check"),
    ("sys_check_desc", "Check runtimes, PATH, disk & GitHub API"),
    ("update", "Update XTools"),
    ("update_desc", "Re-run installer from GitHub"),
    ("update_badge", "[UPDATE: {old} -> {new} — press U]"),
    ("lang_label", "Language"),
    ("lang_desc", "Switch EN / TH (Saved permanently)"),
    ("exit", "Exit"),
    ("bye", "Session closed. See you next time."),
    ("no_tools", "(No tools found in scripts/{folder}/ yet)"),
    ("back", "Back to Main Hub"),
    ("select", "Choose Option"),
    ("press_enter", "Press Enter to return..."),
    ("press_cont", "Press Enter to continue..."),
    ("running", "Launching"),
    ("interrupted", "Execution cancelled by user."),
    ("runtime_not_found", "[ERROR] Runtime not found: {err}"),
    ("script_exec", "{ext} executable"),
    ("plugin_mod", "Plugin module"),
    (
        "doctor_title",
        "=== XTools System & Environment Diagnostics ===",
    ),
    ("runtimes_header", "Runtimes & Compilers:"),
    ("not_installed", "not installed"),
    ("env_header", "Environment Integration:"),
    ("in_path", "in PATH"),
    ("not_in_path", "not in current PATH session"),
    ("disk_free", "Disk Free  :"),
];

const TH: &[(&str, &str)] = &[
    ("select_cat", "เลือกหมวดหมู่เครื่องมือการทำงาน"),
    ("quick_actions", "คำสั่งระบบและตั้งค่า"),
    ("sys_check", "ตรวจสอบระบบ"),
    (
        "sys_check_desc",
        "เช็ค Python, Git, Rust, Node, PATH และสถานะเครื่อง",
    ),
    ("update", "อัปเดต XTools"),
    ("update_desc", "ดาวน์โหลดและอัปเดตเวอร์ชันล่าสุดจาก GitHub"),
    ("update_badge", "[มีอัปเดตใหม่: {old} -> {new} — กด U]"),
    ("lang_label", "ภาษา"),
    ("lang_desc", "สลับภาษา ไทย / อังกฤษ (บันทึกค่าอัตโนมัติ)"),
    ("exit", "ออกจากโปรแกรม"),
    ("bye", "ปิดการทำงานเรียบร้อย แล้วพบกันใหม่"),
    ("no_tools", "(ยังไม่มีไฟล์สคริปต์ใน scripts/{folder}/)"),
    ("back", "ย้อนกลับหน้าหลัก"),
    ("select", "เลือกหมายเลข"),
    ("press_enter", "กดปุ่ม Enter เพื่อกลับหน้าหลัก..."),
    ("press_cont", "กดปุ่ม Enter เพื่อดำเนินการต่อ..."),
    ("running", "กำลังเปิดใช้งาน"),
    ("interrupted", "ยกเลิกการทำงาน"),
    ("runtime_not_found", "[ผิดพลาด] ไม่พบรันไทม์: {err}"),
    ("script_exec", "สคริปต์ {ext}"),
    ("plugin_mod", "โมดูลปลั๊กอิน"),
    (
        "doctor_title",
        "=== ตรวจสอบความพร้อมของระบบและสภาพแวดล้อม ===",
    ),
    ("runtimes_header", "รันไทม์และคอมไพเลอร์:"),
    ("not_installed", "ยังไม่ได้ติดตั้ง"),
    ("env_header", "การเชื่อมต่อระบบ:"),
    ("in_path", "พร้อมใช้งานใน PATH"),
    ("not_in_path", "ยังไม่อยู่ใน PATH ปัจจุบัน"),
    ("disk_free", "พื้นที่ว่าง :"),
];

/// `Path.home()` ของ Python: `USERPROFILE` บน Windows, `HOME` บน POSIX
fn home_dir() -> Option<PathBuf> {
    #[cfg(windows)]
    let var = std::env::var_os("USERPROFILE");
    #[cfg(not(windows))]
    let var = std::env::var_os("HOME");
    var.map(PathBuf::from).filter(|p| !p.as_os_str().is_empty())
}

/// อ่าน `lang` จาก `~/.xtools_config.json` ครั้งเดียวแล้วจำไว้ (แบบเดียวกับที่ Python โหลดตอน import)
fn current_lang() -> &'static str {
    static LANG: OnceLock<String> = OnceLock::new();
    LANG.get_or_init(|| {
        let Some(path) = home_dir().map(|h| h.join(".xtools_config.json")) else {
            return "th".to_string();
        };
        let Ok(text) = std::fs::read_to_string(path) else {
            return "th".to_string();
        };
        let Ok(value) = serde_json::from_str::<serde_json::Value>(&text) else {
            return "th".to_string();
        };
        match value.get("lang").and_then(|v| v.as_str()) {
            Some("en") => "en".to_string(),
            _ => "th".to_string(),
        }
    })
}

/// Port of `t` (`scripts/ui/i18n.py:109`).
pub fn t(key: String) -> Result<String, String> {
    let table: &[(&str, &str)] = if current_lang() == "en" { EN } else { TH };
    match table.iter().find(|(k, _)| *k == key) {
        Some((_, text)) => Ok((*text).to_string()),
        None => Ok(key),
    }
}
