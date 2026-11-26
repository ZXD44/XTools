# Prompt Lite

Lightweight Thai → compressed English prompt translator for Antigravity IDE (`usage-monitor` capsule integration).

## Files
- `src/main.rs` / `Cargo.toml` — Native Rust CLI (`prompt-lite.exe`), zero runtime deps
- `prompt-lite.exe` — Prebuilt release binary (`opt-level = "z"`, LTO, stripped)
- `agyx.py` — Python diagnostic/patcher utility for `usage-monitor`

## Build
```powershell
cargo build --release
Copy-Item target\release\prompt-lite.exe prompt-lite.exe -Force
```

## Test
```powershell
.\prompt-lite.exe translate "ตรวจสอบไฟล์นี้ให้หน่อย"
```

## Runtime Config & Stats (in `~/.gemini/`)
- `~/.gemini/prompt_lite.json` — Backend & model config (`auto` → `gemini` → `google` → `openai_compat` → `ollama` → `rules`)
- `~/.gemini/prompt_lite_stats.json` — Token savings counter read by `usage-monitor`
