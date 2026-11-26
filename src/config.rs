use std::path::PathBuf;

pub const VERSION: &str = "0.0.2";
pub const BUILD: &str = "dev";
pub const REPO: &str = "ZXD44/XTools";

pub const CYAN: &str = "\x1b[96m";
pub const BLUE: &str = "\x1b[94m";
pub const GREEN: &str = "\x1b[92m";
pub const YELLOW: &str = "\x1b[93m";
pub const RED: &str = "\x1b[91m";
pub const MAGENTA: &str = "\x1b[95m";
pub const BOLD: &str = "\x1b[1m";
pub const DIM: &str = "\x1b[90m";
pub const RESET: &str = "\x1b[0m";

pub const CATEGORIES: &[(&str, &str, &str, &str, &str, &str)] = &[
    ("1", "System & Cleanup", "ระบบและล้างไฟล์", "system", "System info, temp cleanup, startup & env tools", "ข้อมูลระบบ ล้างไฟล์ขยะ และตั้งค่าเครื่อง"),
    ("2", "Dev & Git", "พัฒนาและ Git", "dev", "Repo utilities, formatters, environment helpers", "เครื่องมือจัดการ repo สภาพแวดล้อม และโค้ด"),
    ("3", "Network & Security", "เครือข่ายและความปลอดภัย", "network", "Diagnostics, port checks, hash & audit tools", "ตรวจสอบพอร์ต สแกนเครือข่าย และความปลอดภัย"),
    ("4", "Media & Files", "มีเดียและไฟล์", "media", "Batch rename, image/icon converters, archivers", "เปลี่ยนชื่อไฟล์ แปลงรูป/ไอคอน และบีบอัดไฟล์"),
];

pub fn root_dir() -> PathBuf {
    if let Ok(exe) = std::env::current_exe() {
        // target/release/xtools.exe -> repo root, or bin/xtools.exe -> install root
        for anc in exe.ancestors().skip(1) {
            if anc.join("scripts").is_dir() {
                return anc.to_path_buf();
            }
        }
    }
    std::env::current_dir().unwrap_or_else(|_| PathBuf::from("."))
}

pub fn config_path() -> PathBuf {
    let home = std::env::var_os("USERPROFILE")
        .or_else(|| std::env::var_os("HOME"))
        .map(PathBuf::from)
        .unwrap_or_else(|| PathBuf::from("."));
    home.join(".xtools_config.json")
}

#[cfg(windows)]
pub fn enable_windows_vt() {
    extern "system" {
        fn GetStdHandle(nStdHandle: i32) -> isize;
        fn GetConsoleMode(hConsoleHandle: isize, lpMode: *mut u32) -> i32;
        fn SetConsoleMode(hConsoleHandle: isize, dwMode: u32) -> i32;
        fn SetConsoleOutputCP(wCodePageID: u32) -> i32;
    }
    unsafe {
        SetConsoleOutputCP(65001);
        let h = GetStdHandle(-11);
        let mut mode: u32 = 0;
        if GetConsoleMode(h, &mut mode) != 0 {
            SetConsoleMode(h, mode | 0x0004 | 0x0001);
        }
    }
}

#[cfg(not(windows))]
pub fn enable_windows_vt() {}
