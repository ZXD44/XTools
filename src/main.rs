mod config;
mod banner;
mod discovery;
mod doctor;
mod i18n;
mod menu;
mod runner;

fn main() {
    config::enable_windows_vt();
    let args: Vec<String> = std::env::args().skip(1).collect();

    if args.is_empty() {
        menu::render_main_dashboard();
        return;
    }

    match args[0].to_lowercase().as_str() {
        "doctor" | "check" | "env" => doctor::run_system_doctor(),
        "update" | "upgrade" => {
            let ch = args.get(1).map(|s| s.as_str()).unwrap_or("stable");
            doctor::run_system_update(ch);
        }
        "lang" => {
            let target = args.get(1).map(|s| s.to_lowercase());
            let next = match target.as_deref() {
                Some("en") => "en",
                Some("th") => "th",
                _ => if i18n::get_lang() == "th" { "en" } else { "th" },
            };
            i18n::set_lang(next);
            println!("Language set to: {}", next.to_uppercase());
        }
        "-v" | "--version" | "version" => {
            println!("XTools v{}", config::VERSION);
        }
        cmd => {
            for tool in discovery::discover_all_workspace_tools() {
                if tool.name.eq_ignore_ascii_case(cmd) {
                    runner::execute_tool(&tool, &args[1..]);
                    return;
                }
            }
            eprintln!("{}[ERROR] Unknown command or tool: '{}'{}", config::RED, args[0], config::RESET);
            std::process::exit(1);
        }
    }
}
