use std::io::{self, IsTerminal, Write};
use std::sync::{atomic::{AtomicBool, Ordering}, Arc, Mutex};
use std::time::Duration;
use crate::config::{BLUE, BOLD, BUILD, CYAN, DIM, RED, RESET, VERSION};

pub const BANNER_ART: &[&str] = &[
    r" __  _______ ___   ___  _     ____  ",
    r" \ \/ /_   _/ _ \ / _ \| |   / ___| ",
    r"  \  /  | || | | | | | | |   \___ \ ",
    r"  /  \  | || |_| | |_| | |___ ___) |",
    r" /_/\_\ |_| \___/ \___/|_____|____/ ",
];

static RENDER_LOCK: Mutex<()> = Mutex::new(());
static WAVE_PHASE: Mutex<f64> = Mutex::new(0.0);

fn water_rgb(col: usize, row: usize, phase: f64) -> (u8, u8, u8) {
    let w1 = (col as f64 * 0.22 - phase + row as f64 * 0.65).sin();
    let w2 = (col as f64 * 0.11 + phase * 0.6 - row as f64 * 0.40).sin() * 0.35;
    let val = ((w1 + w2 + 1.35) / 2.7).clamp(0.0, 1.0);
    let crest = val.powf(2.4);
    let r = (8.0 + crest * 205.0).min(255.0) as u8;
    let g = (85.0 + val * 155.0 + crest * 15.0).min(255.0) as u8;
    let b = (175.0 + val * 80.0).min(255.0) as u8;
    (r, g, b)
}

pub fn render_wave_frame(phase: f64) -> String {
    let mut out = String::with_capacity(2048);
    for (r_idx, line) in BANNER_ART.iter().enumerate() {
        if r_idx > 0 {
            out.push('\n');
        }
        for (c_idx, ch) in line.chars().enumerate() {
            if ch == ' ' {
                out.push(' ');
            } else {
                let (r, g, b) = water_rgb(c_idx, r_idx, phase);
                out.push_str(&format!("\x1b[38;2;{r};{g};{b}m{BOLD}{ch}"));
            }
        }
        out.push_str(RESET);
    }
    out
}

pub fn get_subtitle_line() -> String {
    format!(
        "  {CYAN}XTools Hub v{VERSION} {DIM}({BUILD}){RESET} {DIM}|{RESET} {RED}{BOLD}ZXD44{RESET}{DIM}/XTools{RESET} {DIM}|{RESET} {BLUE}Rust Native{RESET}\n"
    )
}

pub fn render_static_banner() {
    let phase = *WAVE_PHASE.lock().unwrap();
    println!("{}\n{}", render_wave_frame(phase), get_subtitle_line());
}

pub fn wave_input(prompt: &str) -> String {
    if std::env::var("XTOOLS_NO_ANIM").as_deref() == Ok("1")
        || !io::stdout().is_terminal()
        || !io::stdin().is_terminal()
    {
        print!("{prompt}");
        let _ = io::stdout().flush();
        let mut s = String::new();
        let _ = io::stdin().read_line(&mut s);
        return s.trim().to_string();
    }

    print!("{prompt}");
    let _ = io::stdout().flush();

    let stop = Arc::new(AtomicBool::new(false));
    let stop_clone = Arc::clone(&stop);

    let handle = std::thread::spawn(move || {
        while !stop_clone.load(Ordering::Relaxed) {
            let phase = {
                let mut p = WAVE_PHASE.lock().unwrap();
                *p += 0.26;
                *p
            };
            let frame = render_wave_frame(phase);
            if let Ok(_g) = RENDER_LOCK.lock() {
                if stop_clone.load(Ordering::Relaxed) {
                    break;
                }
                print!("\x1b[s\x1b[?25l\x1b[1;1H{frame}\x1b[u\x1b[?25h");
                let _ = io::stdout().flush();
            }
            std::thread::sleep(Duration::from_millis(55));
        }
    });

    let res = read_line_with_lock();
    stop.store(true, Ordering::Relaxed);
    let _ = handle.join();
    res
}

#[cfg(windows)]
fn read_line_with_lock() -> String {
    extern "C" {
        fn _getwch() -> u16;
    }
    let mut buf: Vec<u16> = Vec::new();
    loop {
        let ch = unsafe { _getwch() };
        match ch {
            13 | 10 => {
                let _g = RENDER_LOCK.lock();
                println!();
                return String::from_utf16_lossy(&buf);
            }
            3 => std::process::exit(0),
            8 | 127 => {
                if buf.pop().is_some() {
                    let _g = RENDER_LOCK.lock();
                    print!("\x08 \x08");
                    let _ = io::stdout().flush();
                }
            }
            0 | 0xE0 => {
                unsafe { _getwch(); }
            }
            c if c >= 32 => {
                buf.push(c);
                let _g = RENDER_LOCK.lock();
                print!("{}", String::from_utf16_lossy(&[c]));
                let _ = io::stdout().flush();
            }
            _ => {}
        }
    }
}

#[cfg(not(windows))]
fn read_line_with_lock() -> String {
    let mut s = String::new();
    let _ = io::stdin().read_line(&mut s);
    s.trim().to_string()
}
