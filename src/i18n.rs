use std::sync::Mutex;
use crate::config::config_path;

static LANG: Mutex<Option<String>> = Mutex::new(None);

pub fn get_lang() -> String {
    let mut guard = LANG.lock().unwrap();
    if let Some(ref l) = *guard {
        return l.clone();
    }
    let loaded = std::fs::read_to_string(config_path())
        .ok()
        .and_then(|s| serde_json::from_str::<serde_json::Value>(&s).ok())
        .and_then(|v| v.get("lang").and_then(|x| x.as_str()).map(|s| s.to_string()))
        .filter(|s| s == "en" || s == "th")
        .unwrap_or_else(|| "th".to_string());
    *guard = Some(loaded.clone());
    loaded
}

pub fn set_lang(lang: &str) {
    {
        let mut guard = LANG.lock().unwrap();
        *guard = Some(lang.to_string());
    }
    let path = config_path();
    let mut obj = std::fs::read_to_string(&path)
        .ok()
        .and_then(|s| serde_json::from_str::<serde_json::Value>(&s).ok())
        .and_then(|v| v.as_object().cloned())
        .unwrap_or_default();
    obj.insert("lang".to_string(), serde_json::Value::String(lang.to_string()));
    let _ = std::fs::write(path, serde_json::to_string_pretty(&obj).unwrap_or_default());
}

pub fn t(key: &str) -> &'static str {
    let th = get_lang() == "th";
    match (th, key) {
        (true, "select_cat") => "เลือกหมวดหมู่เครื่องมือการทำงาน",
        (false, "select_cat") => "Select Category Workspace",
        (true, "quick_actions") => "คำสั่งระบบและตั้งค่า",
        (false, "quick_actions") => "Quick Actions",
        (true, "sys_check") => "ตรวจสอบระบบ",
        (false, "sys_check") => "System Check",
        (true, "sys_check_desc") => "เช็ค Python, Git, Rust, Node, PATH และสถานะเครื่อง",
        (false, "sys_check_desc") => "Check runtimes, PATH, disk & GitHub API",
        (true, "update") => "อัปเดต XTools",
        (false, "update") => "Update XTools",
        (true, "update_desc") => "ดาวน์โหลดและอัปเดตเวอร์ชันล่าสุดจาก GitHub",
        (false, "update_desc") => "Re-run installer from GitHub",
        (true, "lang_label") => "ภาษา",
        (false, "lang_label") => "Language",
        (true, "lang_desc") => "สลับภาษา ไทย / อังกฤษ (บันทึกค่าอัตโนมัติ)",
        (false, "lang_desc") => "Switch EN / TH (Saved permanently)",
        (true, "exit") => "ออกจากโปรแกรม",
        (false, "exit") => "Exit",
        (true, "bye") => "ปิดการทำงานเรียบร้อย แล้วพบกันใหม่",
        (false, "bye") => "Session closed. See you next time.",
        (true, "back") => "ย้อนกลับหน้าหลัก",
        (false, "back") => "Back to Main Hub",
        (true, "select") => "เลือกหมายเลข",
        (false, "select") => "Choose Option",
        (true, "press_enter") => "กดปุ่ม Enter เพื่อกลับหน้าหลัก...",
        (false, "press_enter") => "Press Enter to return...",
        (true, "press_cont") => "กดปุ่ม Enter เพื่อดำเนินการต่อ...",
        (false, "press_cont") => "Press Enter to continue...",
        (true, "running") => "กำลังเปิดใช้งาน",
        (false, "running") => "Launching",
        (true, "doctor_title") => "=== ตรวจสอบความพร้อมของระบบและสภาพแวดล้อม ===",
        (false, "doctor_title") => "=== XTools System & Environment Diagnostics ===",
        (true, "runtimes_header") => "รันไทม์และคอมไพเลอร์:",
        (false, "runtimes_header") => "Runtimes & Compilers:",
        (true, "not_installed") => "ยังไม่ได้ติดตั้ง",
        (false, "not_installed") => "not installed",
        (true, "env_header") => "การเชื่อมต่อระบบ:",
        (false, "env_header") => "Environment Integration:",
        (true, "in_path") => "พร้อมใช้งานใน PATH",
        (false, "in_path") => "in PATH",
        (true, "not_in_path") => "ยังไม่อยู่ใน PATH ปัจจุบัน",
        (false, "not_in_path") => "not in current PATH session",
        _ => "",
    }
}
