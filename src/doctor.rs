use std::process::{Command, Stdio};
use crate::config::{root_dir, BLUE, BOLD, DIM, GREEN, REPO, RESET, YELLOW};
use crate::i18n::t;

pub fn run_system_doctor() {
    let root = root_dir();
    println!("{BOLD}{BLUE}{}{RESET}\n", t("doctor_title"));
    println!("  OS        : {} / {}", std::env::consts::OS, std::env::consts::ARCH);
    println!("  Root Dir  : {}", root.display());

    let runtimes = ["python", "git", "gh", "node", "bun", "rustc", "cargo", "uv", "docker"];
    println!("\n{BOLD}{}{RESET}", t("runtimes_header"));
    for rt in runtimes {
        match Command::new(rt).arg("--version").stdout(Stdio::piped()).stderr(Stdio::piped()).output() {
            Ok(out) if out.status.success() => {
                let s = String::from_utf8_lossy(&out.stdout);
                let line = s.lines().next().unwrap_or("OK").trim();
                println!("  {GREEN}[OK]{RESET} {rt:<8} {DIM}{line}{RESET}");
            }
            _ => println!("  {DIM}[--] {rt:<8} {}{RESET}", t("not_installed")),
        }
    }

    let bin_dir = root.join("bin").to_string_lossy().to_lowercase();
    let path_env = std::env::var("PATH").unwrap_or_default().to_lowercase();
    let path_status = if path_env.contains(&bin_dir) {
        format!("{GREEN}[OK]{RESET} {}", t("in_path"))
    } else {
        format!("{YELLOW}[!] {}{RESET}", t("not_in_path"))
    };
    println!("\n{BOLD}{}{RESET}", t("env_header"));
    println!("  XTools\\bin : {path_status}");
}

pub fn run_system_update(channel: &str) {
    let prefix = if channel == "dev" { "$env:XTOOLS_CHANNEL='dev'; " } else { "" };
    let script = format!("{prefix}irm 'https://raw.githubusercontent.com/{REPO}/main/install.ps1' | iex");
    let _ = Command::new("powershell").args(["-NoProfile", "-Command", &script]).status();
}
