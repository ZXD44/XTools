use std::io::{self, Write};
use std::process::Command;
use crate::banner::{render_static_banner, wave_input};
use crate::config::{root_dir, BLUE, BOLD, CATEGORIES, CYAN, DIM, GREEN, MAGENTA, RED, RESET, YELLOW};
use crate::discovery::{discover_all_workspace_tools, discover_category_tools};
use crate::doctor::{run_system_doctor, run_system_update};
use crate::i18n::{get_lang, set_lang, t};
use crate::runner::execute_tool;

fn clear_screen() {
    print!("\x1b[2J\x1b[1;1H");
    let _ = io::stdout().flush();
}

fn pause(msg: &str) {
    print!("\n   {DIM}{msg}{RESET}");
    let _ = io::stdout().flush();
    let mut s = String::new();
    let _ = io::stdin().read_line(&mut s);
}

fn render_category_viewport(title: &str, folder: &str) {
    loop {
        clear_screen();
        render_static_banner();
        println!("{BOLD}{BLUE}┌── [ {title} ] ─────────────────────────────────────────┐{RESET}\n");

        let tools = discover_category_tools(folder);
        if tools.is_empty() {
            println!("   {DIM}(ยังไม่มีไฟล์สคริปต์ใน scripts/{folder}/){RESET}\n");
        } else {
            for (idx, item) in tools.iter().enumerate() {
                println!(
                    "   {CYAN}▪ [{}]{RESET} {BOLD}{:<22}{RESET} {DIM}[{}] ─ {}{RESET}",
                    idx + 1, item.name, item.runtime.to_uppercase(), item.desc
                );
            }
            println!();
        }

        println!("{BOLD}{BLUE}└────────────────────────────────────────────────────────┘{RESET}");
        println!("   {DIM}[0] {}{RESET}\n", t("back"));

        let choice = wave_input(&format!("   {BOLD}{} > {RESET}", t("select")));
        let choice = choice.trim();
        if choice == "0" || choice.is_empty() {
            return;
        }
        if let Ok(idx) = choice.parse::<usize>() {
            if idx >= 1 && idx <= tools.len() {
                execute_tool(&tools[idx - 1], &[]);
                pause(t("press_enter"));
            }
        }
    }
}

pub fn render_main_dashboard() {
    loop {
        clear_screen();
        render_static_banner();
        let th = get_lang() == "th";

        println!("{BOLD}┌── {} ───────────────────────────────┐{RESET}", t("select_cat"));
        for &(key, t_en, t_th, _, d_en, d_th) in CATEGORIES {
            let title = if th { t_th } else { t_en };
            let desc = if th { d_th } else { d_en };
            println!("│  {CYAN}[{key}]{RESET} {BOLD}{title:<26}{RESET} {DIM}{desc}{RESET}");
        }
        println!("{BOLD}├── {} ───────────────────────────────────────┤{RESET}", t("quick_actions"));
        println!("│  {MAGENTA}[A]{RESET} {:<26} {DIM}Multi-Account, Quota & Profile Binding{RESET}", "AGY Manager");
        println!("│  {GREEN}[S]{RESET} {:<26} {DIM}{}{RESET}", t("sys_check"), t("sys_check_desc"));
        println!("│  {YELLOW}[U]{RESET} {:<26} {DIM}{}{RESET}", t("update"), t("update_desc"));
        let lang_code = if th { "TH" } else { "EN" };
        println!("│  {CYAN}[L]{RESET} {:<26} {DIM}[{lang_code}] {}{RESET}", t("lang_label"), t("lang_desc"));
        println!("│  {RED}[0]{RESET} {:<26}", t("exit"));
        println!("{BOLD}└────────────────────────────────────────────────────────┘{RESET}\n");

        let choice = wave_input(&format!("   {BOLD}XTools > {RESET}")).trim().to_lowercase();
        match choice.as_str() {
            "0" | "q" | "exit" => {
                println!("\n   {DIM}{}{RESET}\n", t("bye"));
                break;
            }
            "a" => {
                let agy = root_dir().join("scripts").join("dev").join("agy-manager").join("main.py");
                if agy.is_file() {
                    let _ = Command::new("python").arg(agy).status();
                } else {
                    println!("\n   {RED}[!] ไม่พบ scripts/dev/agy-manager/main.py{RESET}");
                    pause(t("press_enter"));
                }
            }
            "s" => {
                clear_screen();
                render_static_banner();
                run_system_doctor();
                pause(t("press_enter"));
            }
            "u" => {
                run_system_update("stable");
                pause(t("press_cont"));
            }
            "l" => {
                set_lang(if th { "en" } else { "th" });
            }
            other => {
                if let Some(&(_, t_en, t_th, folder, _, _)) = CATEGORIES.iter().find(|c| c.0 == other) {
                    render_category_viewport(if th { t_th } else { t_en }, folder);
                } else if !other.is_empty() {
                    let q = other.trim_start_matches('/');
                    let matches: Vec<_> = discover_all_workspace_tools()
                        .into_iter()
                        .filter(|t| t.name.to_lowercase().contains(q))
                        .collect();
                    if matches.len() == 1 {
                        execute_tool(&matches[0], &[]);
                        pause(t("press_enter"));
                    } else if !matches.is_empty() {
                        println!("\n   {CYAN}ผลการค้นหา '{q}':{RESET}");
                        for (i, m) in matches.iter().enumerate() {
                            println!("   {CYAN}[{}]{RESET} {BOLD}{}{RESET} {DIM}─ {}{RESET}", i + 1, m.name, m.desc);
                        }
                        let pick = wave_input(&format!("\n   {BOLD}{} > {RESET}", t("select")));
                        if let Ok(idx) = pick.trim().parse::<usize>() {
                            if idx >= 1 && idx <= matches.len() {
                                execute_tool(&matches[idx - 1], &[]);
                                pause(t("press_enter"));
                            }
                        }
                    }
                }
            }
        }
    }
}
