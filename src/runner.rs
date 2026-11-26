use std::process::Command;
use crate::config::{BOLD, CYAN, DIM, RED, RESET};
use crate::discovery::ToolEntry;
use crate::i18n::t;

pub fn execute_tool(tool: &ToolEntry, extra_args: &[String]) {
    let ext = tool.entry.extension().and_then(|s| s.to_str()).unwrap_or("").to_lowercase();
    let rt = if tool.runtime == "auto" {
        match ext.as_str() {
            "py" => "python",
            "bat" => "bat",
            "ps1" => "powershell",
            "sh" => "bash",
            "js" => "node",
            "ts" => "bun",
            _ => "exe",
        }
    } else {
        tool.runtime.as_str()
    };

    println!("\n{CYAN}[>]{RESET} {} {BOLD}{}{RESET} ({DIM}{rt}{RESET})...\n", t("running"), tool.name);

    let entry_str = tool.entry.to_string_lossy().to_string();
    let mut cmd = match rt {
        "python" => {
            let venv_win = tool.cwd.join(".venv").join("Scripts").join("python.exe");
            let venv_nix = tool.cwd.join(".venv").join("bin").join("python");
            let py = if venv_win.is_file() {
                venv_win.to_string_lossy().to_string()
            } else if venv_nix.is_file() {
                venv_nix.to_string_lossy().to_string()
            } else {
                "python".to_string()
            };
            let mut c = Command::new(py);
            c.arg(&entry_str);
            c
        }
        "bat" => {
            let mut c = Command::new("cmd");
            c.args(["/c", &entry_str]);
            c
        }
        "powershell" => {
            let mut c = Command::new("powershell");
            c.args(["-ExecutionPolicy", "Bypass", "-File", &entry_str]);
            c
        }
        "bash" => {
            let mut c = Command::new("bash");
            c.arg(&entry_str);
            c
        }
        "node" => {
            let mut c = Command::new("node");
            c.arg(&entry_str);
            c
        }
        "bun" => {
            let mut c = Command::new("bun");
            c.args(["run", &entry_str]);
            c
        }
        _ => Command::new(&entry_str),
    };

    cmd.args(extra_args).current_dir(&tool.cwd);
    match cmd.status() {
        Ok(_) => {}
        Err(e) => eprintln!("{RED}[ผิดพลาด] ไม่พบรันไทม์ ({rt}): {e}{RESET}"),
    }
}
