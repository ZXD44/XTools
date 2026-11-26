// Rust, prompt-lite.exe, Windows 11, Cargo release
use regex::Regex;
use serde::{Deserialize, Serialize};
use serde_json::{Value, json};
use std::env;
use std::fs;
use std::path::PathBuf;
use std::sync::OnceLock;
use std::time::Duration;

const SYSTEM_PROMPT_BASE: &str = "Translate Thai to minimal imperative English for a coding AI. \
Strip all politeness, greetings, and filler words. \
Output ONLY the compressed English prompt, no quotes, no explanation.";

const SYSTEM_PROMPT_KEEP: &str = "Translate Thai to minimal imperative English for a coding AI. \
Strip all politeness, greetings, and filler words. \
Keep placeholders like [[0]], [[1]] exact and untouched. \
Output ONLY the compressed English prompt, no quotes, no explanation.";

fn system_prompt(has_kept: bool) -> &'static str {
    if has_kept { SYSTEM_PROMPT_KEEP } else { SYSTEM_PROMPT_BASE }
}

#[derive(Debug, Deserialize, Default)]
#[serde(default)]
struct OllamaCfg {
    url: String,
    model: String,
    keep_alive: i64,
}

#[derive(Debug, Deserialize, Default)]
#[serde(default)]
struct OpenAiCfg {
    url: String,
    api_key: String,
    model: String,
}

#[derive(Debug, Deserialize, Default)]
#[serde(default)]
struct GeminiCfg {
    api_key: String,
    model: String,
}

#[derive(Debug, Deserialize)]
#[serde(default)]
struct Config {
    backend: String,
    ollama: OllamaCfg,
    openai_compat: OpenAiCfg,
    gemini: GeminiCfg,
    timeout_sec: f64,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            backend: "auto".into(),
            ollama: OllamaCfg {
                url: "http://127.0.0.1:11434/api/generate".into(),
                model: "qwen2.5:1.5b".into(),
                keep_alive: -1,
            },
            openai_compat: OpenAiCfg {
                url: "https://api.groq.com/openai/v1/chat/completions".into(),
                api_key: String::new(),
                model: "llama-3.1-8b-instant".into(),
            },
            gemini: GeminiCfg {
                api_key: String::new(),
                model: "gemini-flash-lite-latest".into(),
            },
            timeout_sec: 8.0,
        }
    }
}

#[derive(Debug, Serialize, Deserialize, Default)]
#[serde(default)]
struct Stats {
    prompts: u64,
    tokens_in: u64,
    tokens_out: u64,
    tokens_saved: u64,
}

fn gemini_dir() -> PathBuf {
    let home = env::var_os("USERPROFILE")
        .or_else(|| env::var_os("HOME"))
        .map(PathBuf::from)
        .unwrap_or_else(|| PathBuf::from("."));
    home.join(".gemini")
}

fn load_config() -> Config {
    let path = gemini_dir().join("prompt_lite.json");
    if let Ok(raw) = fs::read_to_string(&path)
        && let Ok(cfg) = serde_json::from_str::<Config>(&raw)
    {
        return cfg;
    }
    Config::default()
}

fn has_thai(s: &str) -> bool {
    s.chars().any(|c| ('\u{0e00}'..='\u{0e7f}').contains(&c))
}

fn estimate_tokens(s: &str) -> u64 {
    let mut thai = 0.0_f64;
    let mut other = 0.0_f64;
    for ch in s.chars() {
        if ('\u{0e00}'..='\u{0e7f}').contains(&ch) {
            thai += 1.0;
        } else {
            other += 1.0;
        }
    }
    (thai * 0.35 + other * 0.22).round().max(1.0) as u64
}

fn shield_re() -> &'static Regex {
    static RE: OnceLock<Regex> = OnceLock::new();
    RE.get_or_init(|| {
        Regex::new(
            r"```[\s\S]*?```|`[^`\n]+`|https?://[^\s]+|[A-Za-z]:\\[^\s\x22'<>|]+|[A-Za-z0-9_./\\-]+\.(?:py|js|ts|tsx|jsx|mjs|cjs|json|md|lua|luau|ps1|sh|yaml|yml|toml|html|css|rs)\b",
        )
        .unwrap()
    })
}

fn shield_text(text: &str) -> (String, Vec<String>) {
    let mut kept = Vec::new();
    let shielded = shield_re()
        .replace_all(text, |caps: &regex::Captures| {
            let idx = kept.len();
            kept.push(caps[0].to_string());
            format!("[[{idx}]]")
        })
        .into_owned();
    (shielded, kept)
}

fn unshield_text(mut text: String, kept: &[String]) -> String {
    for (idx, val) in kept.iter().enumerate() {
        text = text.replace(&format!("[[{idx}]]"), val);
    }
    text.trim().to_string()
}

fn filler_re() -> &'static Regex {
    static RE: OnceLock<Regex> = OnceLock::new();
    RE.get_or_init(|| {
        Regex::new(r"(?:ครับ|ค่ะ|นะ|นะครับ|นะคะ|หน่อย|ให้หน่อย|ให้ที|ที|ได้ไหม|ด้วย|ช่วย|รบกวน|อยากได้|แบบว่า|ประมาณว่า|คือว่า|อันนี้|ตรงนี้|เลยครับ|เลยค่ะ|สิ|จ้า)").unwrap()
    })
}

fn rules_compress(text: &str) -> String {
    let out = filler_re().replace_all(text, " ");
    let ws = Regex::new(r"\s+").unwrap();
    ws.replace_all(&out, " ").trim().to_string()
}

fn make_agent(timeout_sec: f64) -> ureq::Agent {
    let dur = Duration::from_secs_f64(timeout_sec.clamp(1.0, 30.0));
    ureq::AgentBuilder::new().timeout(dur).build()
}

fn call_gemini(agent: &ureq::Agent, prompt: &str, cfg: &Config, sys_prompt: &str) -> Option<String> {
    let key = if !cfg.gemini.api_key.is_empty() {
        cfg.gemini.api_key.clone()
    } else {
        env::var("GEMINI_API_KEY").ok()?
    };
    if key.is_empty() {
        return None;
    }
    let model = if cfg.gemini.model.is_empty() {
        "gemini-flash-lite-latest"
    } else {
        &cfg.gemini.model
    };
    let url = format!(
        "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    );
    let body = json!({
        "systemInstruction": { "parts": [{ "text": sys_prompt }] },
        "contents": [{ "parts": [{ "text": prompt }] }],
        "generationConfig": { "temperature": 0.1, "maxOutputTokens": 256 }
    });
    let resp: Value = agent.post(&url).send_json(body).ok()?.into_json().ok()?;
    resp["candidates"][0]["content"]["parts"][0]["text"]
        .as_str()
        .map(|s| s.trim().to_string())
        .filter(|s| !s.is_empty())
}

fn call_google(agent: &ureq::Agent, prompt: &str) -> Option<String> {
    let cleaned = rules_compress(prompt);
    let q = if cleaned.is_empty() { prompt } else { &cleaned };
    let fix_k = Regex::new(r"\[\[\s*(\d+)\s*\]\]").unwrap();

    // Primary free endpoint (dict-chrome-ex)
    if let Ok(r) = agent
        .get("https://clients5.google.com/translate_a/t")
        .query("client", "dict-chrome-ex")
        .query("sl", "th")
        .query("tl", "en")
        .query("q", q)
        .set("User-Agent", "Mozilla/5.0")
        .call()
        && let Ok(val) = r.into_json::<Value>()
    {
        let raw = val[0]
            .as_str()
            .or_else(|| val[0][0].as_str())
            .unwrap_or("")
            .trim();
        if !raw.is_empty() {
            return Some(fix_k.replace_all(raw, "[[$1]]").into_owned());
        }
    }

    // Secondary free endpoint (tw-ob)
    let resp: Value = agent
        .get("https://translate.googleapis.com/translate_a/single")
        .query("client", "tw-ob")
        .query("sl", "th")
        .query("tl", "en")
        .query("dt", "t")
        .query("q", q)
        .set("User-Agent", "Mozilla/5.0")
        .call()
        .ok()?
        .into_json()
        .ok()?;
    let mut out = String::new();
    if let Some(arr) = resp[0].as_array() {
        for seg in arr {
            if let Some(part) = seg[0].as_str() {
                out.push_str(part);
            }
        }
    }
    let fixed = fix_k.replace_all(out.trim(), "[[$1]]").into_owned();
    (!fixed.is_empty()).then_some(fixed)
}

fn call_openai_compat(agent: &ureq::Agent, prompt: &str, cfg: &Config, sys_prompt: &str) -> Option<String> {
    let key = if !cfg.openai_compat.api_key.is_empty() {
        cfg.openai_compat.api_key.clone()
    } else {
        env::var("GROQ_API_KEY")
            .or_else(|_| env::var("OPENAI_API_KEY"))
            .ok()?
    };
    if key.is_empty() {
        return None;
    }
    let resp: Value = agent
        .post(&cfg.openai_compat.url)
        .set("Authorization", &format!("Bearer {key}"))
        .send_json(json!({
            "model": cfg.openai_compat.model,
            "messages": [
                { "role": "system", "content": sys_prompt },
                { "role": "user", "content": prompt }
            ],
            "temperature": 0.1,
            "max_tokens": 256
        }))
        .ok()?
        .into_json()
        .ok()?;
    resp["choices"][0]["message"]["content"]
        .as_str()
        .map(|s| s.trim().to_string())
        .filter(|s| !s.is_empty())
}

fn call_ollama(agent: &ureq::Agent, prompt: &str, cfg: &Config, sys_prompt: &str) -> Option<String> {
    let resp: Value = agent
        .post(&cfg.ollama.url)
        .send_json(json!({
            "model": cfg.ollama.model,
            "system": sys_prompt,
            "prompt": prompt,
            "stream": false,
            "keep_alive": cfg.ollama.keep_alive,
            "options": { "temperature": 0.1, "num_predict": 256 }
        }))
        .ok()?
        .into_json()
        .ok()?;
    resp["response"]
        .as_str()
        .map(|s| s.trim().to_string())
        .filter(|s| !s.is_empty())
}

fn translate_prompt(raw: &str, cfg: &Config) -> (String, &'static str) {
    if raw.trim().is_empty() {
        return (raw.to_string(), "empty");
    }
    if !has_thai(raw) {
        return (raw.to_string(), "passthrough");
    }

    let (shielded, kept) = shield_text(raw);
    let sys_prompt = system_prompt(!kept.is_empty());
    let agent = make_agent(cfg.timeout_sec);
    let order: Vec<&str> = if cfg.backend == "auto" {
        vec!["google", "gemini", "openai_compat", "ollama", "rules"]
    } else {
        vec![cfg.backend.as_str(), "rules"]
    };

    for eng in order {
        let res = match eng {
            "gemini" => call_gemini(&agent, &shielded, cfg, sys_prompt).map(|r| (r, "gemini")),
            "google" => call_google(&agent, &shielded).map(|r| (r, "google")),
            "openai_compat" => call_openai_compat(&agent, &shielded, cfg, sys_prompt).map(|r| (r, "openai_compat")),
            "ollama" => call_ollama(&agent, &shielded, cfg, sys_prompt).map(|r| (r, "ollama")),
            "rules" => Some((rules_compress(&shielded), "rules")),
            _ => None,
        };
        if let Some((out, name)) = res {
            return (unshield_text(out, &kept), name);
        }
    }
    (raw.to_string(), "unchanged")
}

fn record_stats(t_in: u64, t_out: u64) {
    let path = gemini_dir().join("prompt_lite_stats.json");
    let mut stats = fs::read_to_string(&path)
        .ok()
        .and_then(|s| serde_json::from_str::<Stats>(&s).ok())
        .unwrap_or_default();
    stats.prompts += 1;
    stats.tokens_in += t_in;
    stats.tokens_out += t_out;
    stats.tokens_saved += t_in.saturating_sub(t_out);
    if let Ok(json_str) = serde_json::to_string_pretty(&stats) {
        let _ = fs::write(&path, format!("{json_str}\n"));
    }
}

fn main() {
    let args: Vec<String> = env::args().skip(1).collect();
    if args.is_empty() {
        eprintln!("Usage: prompt-lite translate <text>");
        std::process::exit(2);
    }
    let text = if matches!(args[0].as_str(), "translate" | "-t") {
        args[1..].join(" ")
    } else {
        args.join(" ")
    };
    let text = text.trim();
    if text.is_empty() {
        eprintln!("Empty text");
        std::process::exit(1);
    }
    let cfg = load_config();
    let (out, eng) = translate_prompt(text, &cfg);
    let t_in = estimate_tokens(text);
    let t_out = estimate_tokens(&out);
    if !matches!(eng, "empty" | "passthrough" | "unchanged") {
        record_stats(t_in, t_out);
    }
    println!("[{eng}] {t_in} -> {t_out} tok\n{out}");
}
