#!/usr/bin/env python3
"""
Antigravity Usage Monitor & Prompt Lite - Unified Single-File Tool
Diagnostic/repair utility for Antigravity IDE + zero-dependency Thai -> Compressed English (;;) auto-translator.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import json
import os
import platform
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

__version__ = "1.0.0"

if os.name == "nt":
    import winsound

# Paths & Environment
REPO_URL = "https://github.com/Lavich99/antigravity-usage-monitor-th.git"
USER_HOME = Path.home()
GEMINI_DIR = USER_HOME / ".gemini"
CONFIG_FILE = GEMINI_DIR / "config" / "config.json"
PLUGIN_DIR = GEMINI_DIR / "config" / "plugins" / "usage-monitor"
PROMPT_CFG_PATH = GEMINI_DIR / "prompt_lite.json"
PROMPT_STATS_PATH = GEMINI_DIR / "prompt_lite_stats.json"
SELF_PATH = Path(__file__).resolve()

APPDATA_DIR = Path(os.environ.get("APPDATA", str(USER_HOME / "AppData" / "Roaming")))
LOCALAPPDATA_DIR = Path(os.environ.get("LOCALAPPDATA", str(USER_HOME / "AppData" / "Local")))

IDE_USER_ARGV = USER_HOME / ".antigravity-ide" / "argv.json"
IDE_ROAMING_ARGV = APPDATA_DIR / "Antigravity IDE" / "argv.json"
IDE_LOCAL_ARGV = LOCALAPPDATA_DIR / "Antigravity IDE" / "argv.json"

DEVTOOLS_PORTS = [
    APPDATA_DIR / "Antigravity IDE" / "DevToolsActivePort",
    LOCALAPPDATA_DIR / "Antigravity IDE" / "DevToolsActivePort",
    APPDATA_DIR / "Antigravity" / "DevToolsActivePort",
    LOCALAPPDATA_DIR / "Antigravity" / "DevToolsActivePort",
]

IDE_EXE_CANDIDATES = [
    LOCALAPPDATA_DIR / "Programs" / "Antigravity IDE" / "Antigravity IDE.exe",
    APPDATA_DIR / "Local" / "Programs" / "Antigravity IDE" / "Antigravity IDE.exe",
    Path("C:/Program Files/Antigravity IDE/Antigravity IDE.exe"),
]

# ANSI Colors
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_RED = "\033[91m"
C_CYAN = "\033[96m"
C_GRAY = "\033[90m"

# ==============================================================================
# Prompt Lite Engine (Thai -> Compressed English)
# ==============================================================================

DEFAULT_PROMPT_CONFIG = {
    "enabled": True,
    "backend": "auto",  # "auto" | "google" | "ollama" | "openai_compat" | "gemini" | "rules"
    "trigger": ";;",
    "ollama": {
        "url": "http://127.0.0.1:11434/api/generate",
        "model": "qwen2.5:1.5b",
        "keep_alive": -1,
    },
    "openai_compat": {
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "api_key": "",
        "model": "llama-3.1-8b-instant",
    },
    "gemini": {
        "api_key": "",
        "model": "gemini-flash-lite-latest",
    },
    "timeout_sec": 8.0,
    "restore_clipboard": True,
    "beep": True,
}

SYSTEM_PROMPT_BASE = (
    "Translate Thai to minimal imperative English for a coding AI. "
    "Strip all politeness, greetings, and filler words. "
    "Output ONLY the compressed English prompt, no quotes, no explanation."
)
SYSTEM_PROMPT_KEEP = (
    SYSTEM_PROMPT_BASE
    + " Keep placeholders like __K0__, __K1__ exact and untouched."
)

_FILLER_RE = re.compile(
    r"(?:ครับ|ค่ะ|นะ|นะครับ|นะคะ|หน่อย|ให้หน่อย|ให้ที|ที|ได้ไหม|ด้วย|ช่วย|รบกวน|"
    r"อยากได้|แบบว่า|ประมาณว่า|คือว่า|อันนี้|ตรงนี้|เลยครับ|เลยค่ะ|สิ|จ้า)"
)
_VERB_MAP = [
    (re.compile(r"ตรวจสอบ|เช็ค|เช็ก"), "Check"),
    (re.compile(r"แก้ไขบั๊ก|แก้บั๊ก|ซ่อม"), "Fix bug in"),
    (re.compile(r"แก้ไข|แก้"), "Fix"),
    (re.compile(r"สร้าง|ทำ"), "Create"),
    (re.compile(r"เพิ่ม"), "Add"),
    (re.compile(r"ลบ|เอาออก"), "Remove"),
    (re.compile(r"ย้าย"), "Move"),
    (re.compile(r"เปลี่ยน"), "Change"),
    (re.compile(r"อัปเดต|อัพเดต"), "Update"),
    (re.compile(r"อธิบาย"), "Explain"),
    (re.compile(r"เปรียบเทียบ"), "Compare"),
    (re.compile(r"ปรับปรุง|เพิ่มประสิทธิภาพ"), "Optimize"),
    (re.compile(r"รีแฟกเตอร์"), "Refactor"),
    (re.compile(r"เขียนโค้ด|เขียน"), "Write"),
    (re.compile(r"ทดสอบ|เทส"), "Test"),
    (re.compile(r"ค้นหา|หา"), "Find"),
    (re.compile(r"ไม่ทำงาน|พัง"), "broken"),
    (re.compile(r"อัตโนมัติ"), "automatically"),
    (re.compile(r"ไฟล์"), "file"),
    (re.compile(r"ฟังก์ชัน"), "function"),
    (re.compile(r"ระบบ"), "system"),
    (re.compile(r"ฐานข้อมูล"), "database"),
    (re.compile(r"หน้าต่าง|หน้า"), "page"),
    (re.compile(r"ปุ่ม"), "button"),
    (re.compile(r"ทั้งหมด"), "all"),
    (re.compile(r"ให้เร็วที่สุด|เน้นเร็ว|เร็ว"), "fast"),
    (re.compile(r"เน้นเบาที่สุด|เน้นเบา|เบา"), "lightweight"),
]

_SHIELD_RE = re.compile(
    r"```[\s\S]*?```"
    r"|`[^`\n]+`"
    r"|https?://[^\s]+"
    r"|[A-Za-z]:\\[^\s\"'<>|]+"
    r"|\b[A-Za-z0-9_.-]+\.(?:py|js|ts|tsx|jsx|mjs|cjs|json|md|lua|luau|ps1|sh|yaml|yml|toml|html|css)\b"
)


def load_prompt_config() -> dict:
    if not PROMPT_CFG_PATH.exists():
        PROMPT_CFG_PATH.parent.mkdir(parents=True, exist_ok=True)
        PROMPT_CFG_PATH.write_text(json.dumps(DEFAULT_PROMPT_CONFIG, indent=2) + "\n", encoding="utf-8")
        return json.loads(json.dumps(DEFAULT_PROMPT_CONFIG))
    try:
        user_cfg = json.loads(PROMPT_CFG_PATH.read_text(encoding="utf-8"))
        merged = json.loads(json.dumps(DEFAULT_PROMPT_CONFIG))
        for k, v in user_cfg.items():
            if isinstance(v, dict) and isinstance(merged.get(k), dict):
                merged[k].update(v)
            else:
                merged[k] = v
        return merged
    except Exception:
        return json.loads(json.dumps(DEFAULT_PROMPT_CONFIG))


def shield_text(text: str) -> tuple[str, list[str]]:
    kept: list[str] = []

    def _repl(match: re.Match[str]) -> str:
        idx = len(kept)
        kept.append(match.group(0))
        return f"__K{idx}__"

    return _SHIELD_RE.sub(_repl, text), kept


def unshield_text(text: str, kept: list[str]) -> str:
    for idx, val in enumerate(kept):
        text = text.replace(f"__K{idx}__", val)
    return text.strip()


def estimate_tokens(text: str) -> int:
    thai_chars = sum(1 for ch in text if "\u0e00" <= ch <= "\u0e7f")
    other_chars = len(text) - thai_chars
    return max(1, round(thai_chars * 1.15 + other_chars * 0.25))


def record_stats(t_in: int, t_out: int) -> None:
    saved = max(0, t_in - t_out)
    data = {"prompts": 0, "tokens_in": 0, "tokens_out": 0, "tokens_saved": 0}
    if PROMPT_STATS_PATH.exists():
        try:
            loaded = json.loads(PROMPT_STATS_PATH.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                data.update({k: int(loaded.get(k, 0)) for k in data})
        except Exception:
            pass
    data["prompts"] += 1
    data["tokens_in"] += t_in
    data["tokens_out"] += t_out
    data["tokens_saved"] += saved
    try:
        PROMPT_STATS_PATH.parent.mkdir(parents=True, exist_ok=True)
        PROMPT_STATS_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    except Exception:
        pass


def rules_compress(text: str) -> str:
    out = _FILLER_RE.sub(" ", text)
    for pat, rep in _VERB_MAP:
        out = pat.sub(f" {rep} ", out)
    return re.sub(r"\s+", " ", out).strip()


def _http_post_json(url: str, payload: dict, headers: dict[str, str], timeout: float) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", **headers}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _call_ollama(prompt: str, cfg: dict, sys_prompt: str = SYSTEM_PROMPT_BASE) -> str:
    o = cfg["ollama"]
    data = _http_post_json(
        o["url"],
        {
            "model": o["model"],
            "system": sys_prompt,
            "prompt": prompt,
            "stream": False,
            "keep_alive": o.get("keep_alive", -1),
            "options": {"temperature": 0.1, "num_predict": 256},
        },
        {},
        cfg["timeout_sec"],
    )
    return data.get("response", "").strip()


def _call_openai_compat(prompt: str, cfg: dict, sys_prompt: str = SYSTEM_PROMPT_BASE) -> str:
    c = cfg["openai_compat"]
    key = c.get("api_key") or os.environ.get("GROQ_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
    if not key:
        raise RuntimeError("Missing openai_compat api_key")
    data = _http_post_json(
        c["url"],
        {
            "model": c["model"],
            "messages": [{"role": "system", "content": sys_prompt}, {"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 256,
        },
        {"Authorization": f"Bearer {key}"},
        cfg["timeout_sec"],
    )
    return data["choices"][0]["message"]["content"].strip()


def _call_gemini(prompt: str, cfg: dict, sys_prompt: str = SYSTEM_PROMPT_BASE) -> str:
    g = cfg["gemini"]
    key = g.get("api_key") or os.environ.get("GEMINI_API_KEY", "")
    if not key:
        raise RuntimeError("Missing gemini api_key")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{g['model']}:generateContent?key={key}"
    data = _http_post_json(
        url,
        {
            "systemInstruction": {"parts": [{"text": sys_prompt}]},
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 256},
        },
        {},
        cfg["timeout_sec"],
    )
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()


def _call_google_translate(prompt: str, cfg: dict) -> str:
    import urllib.parse

    cleaned = re.sub(r"\s+", " ", _FILLER_RE.sub(" ", prompt)).strip() or prompt
    q = urllib.parse.quote(cleaned)

    try:
        url1 = f"https://clients5.google.com/translate_a/t?client=dict-chrome-ex&sl=th&tl=en&q={q}"
        req1 = urllib.request.Request(url1, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req1, timeout=cfg["timeout_sec"]) as resp1:
            d1 = json.loads(resp1.read().decode("utf-8"))
        raw = (d1[0][0] if isinstance(d1[0], list) else d1[0]) if d1 else ""
        out1 = str(raw or "").strip()
        if out1:
            return re.sub(r"__\s*[Kk]\s*(\d+)\s*__", r"__K\1__", out1)
    except Exception:
        pass

    for client in ("gtx", "tw-ob"):
        try:
            url2 = f"https://translate.googleapis.com/translate_a/single?client={client}&sl=th&tl=en&dt=t&q={q}"
            req2 = urllib.request.Request(url2, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req2, timeout=cfg["timeout_sec"]) as resp2:
                data = json.loads(resp2.read().decode("utf-8"))
            out = "".join(seg[0] for seg in data[0] if seg and seg[0]).strip()
            if out:
                return re.sub(r"__\s*[Kk]\s*(\d+)\s*__", r"__K\1__", out)
        except Exception:
            continue

    url3 = f"https://lingva.ml/api/v1/th/en/{q}"
    req3 = urllib.request.Request(url3, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req3, timeout=cfg["timeout_sec"]) as resp3:
        d3 = json.loads(resp3.read().decode("utf-8"))
    out3 = str(d3.get("translation", "")).strip()
    return re.sub(r"__\s*[Kk]\s*(\d+)\s*__", r"__K\1__", out3)


def translate_prompt(raw_text: str, cfg: dict) -> tuple[str, str]:
    if not raw_text.strip():
        return raw_text, "empty"
    if not any("\u0e00" <= ch <= "\u0e7f" for ch in raw_text):
        return raw_text, "passthrough"

    shielded, kept = shield_text(raw_text)
    sys_prompt = SYSTEM_PROMPT_KEEP if kept else SYSTEM_PROMPT_BASE
    backend = cfg.get("backend", "auto")
    order = ["google", "gemini", "openai_compat", "ollama", "rules"] if backend == "auto" else [backend, "rules"]

    for eng in order:
        try:
            if eng == "ollama":
                res = _call_ollama(shielded, cfg, sys_prompt)
            elif eng == "openai_compat":
                res = _call_openai_compat(shielded, cfg, sys_prompt)
            elif eng == "gemini":
                res = _call_gemini(shielded, cfg, sys_prompt)
            elif eng == "google":
                res = _call_google_translate(shielded, cfg)
            elif eng == "rules":
                res = rules_compress(shielded)
            else:
                continue
            if res:
                return unshield_text(res, kept), eng
        except Exception:
            continue
    return raw_text, "unchanged"


# --- Win32 Native Clipboard & Low-Level Keyboard Hook (64-bit safe) ---
if os.name == "nt":
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    CF_UNICODETEXT = 13
    GMEM_MOVEABLE = 0x0002
    WH_KEYBOARD_LL = 13
    WM_KEYDOWN = 0x0100
    WM_SYSKEYDOWN = 0x0104
    INPUT_KEYBOARD = 1
    KEYEVENTF_KEYUP = 0x0002
    ERROR_ALREADY_EXISTS = 183

    VK_BACK = 0x08
    VK_SHIFT = 0x10
    VK_CONTROL = 0x11
    VK_LCONTROL = 0xA2
    VK_MENU = 0x12
    VK_RETURN = 0x0D
    VK_ESCAPE = 0x1B
    VK_END = 0x23
    VK_HOME = 0x24
    VK_LEFT = 0x25
    VK_UP = 0x26
    VK_RIGHT = 0x27
    VK_DOWN = 0x28
    VK_A = 0x41
    VK_C = 0x43
    VK_T = 0x54
    VK_V = 0x56
    VK_F8 = 0x77
    VK_PACKET = 0xE7
    LRESULT = ctypes.c_ssize_t

    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalUnlock.restype = wintypes.BOOL
    kernel32.GlobalFree.argtypes = [ctypes.c_void_p]
    kernel32.GlobalFree.restype = ctypes.c_void_p
    kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
    kernel32.CreateMutexW.restype = ctypes.c_void_p
    kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
    kernel32.GetModuleHandleW.restype = ctypes.c_void_p
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel32.CloseHandle.restype = wintypes.BOOL

    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.OpenClipboard.restype = wintypes.BOOL
    user32.EmptyClipboard.argtypes = []
    user32.EmptyClipboard.restype = wintypes.BOOL
    user32.GetClipboardData.argtypes = [wintypes.UINT]
    user32.GetClipboardData.restype = ctypes.c_void_p
    user32.SetClipboardData.argtypes = [wintypes.UINT, ctypes.c_void_p]
    user32.SetClipboardData.restype = ctypes.c_void_p
    user32.CloseClipboard.argtypes = []
    user32.CloseClipboard.restype = wintypes.BOOL
    user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
    user32.GetAsyncKeyState.restype = wintypes.SHORT
    user32.GetForegroundWindow.argtypes = []
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.GetKeyboardLayout.argtypes = [wintypes.DWORD]
    user32.GetKeyboardLayout.restype = ctypes.c_void_p
    user32.ToUnicodeEx.argtypes = [
        wintypes.UINT, wintypes.UINT, ctypes.POINTER(ctypes.c_ubyte),
        wintypes.LPWSTR, ctypes.c_int, wintypes.UINT, ctypes.c_void_p,
    ]
    user32.ToUnicodeEx.restype = ctypes.c_int

    class KBDLLHOOKSTRUCT(ctypes.Structure):
        _fields_ = [
            ("vkCode", wintypes.DWORD),
            ("scanCode", wintypes.DWORD),
            ("flags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ctypes.c_size_t),
        ]

    HOOKPROC = ctypes.WINFUNCTYPE(LRESULT, ctypes.c_int, wintypes.WPARAM, ctypes.POINTER(KBDLLHOOKSTRUCT))
    user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, ctypes.c_void_p, wintypes.DWORD]
    user32.SetWindowsHookExW.restype = ctypes.c_void_p
    user32.CallNextHookEx.argtypes = [ctypes.c_void_p, ctypes.c_int, wintypes.WPARAM, ctypes.POINTER(KBDLLHOOKSTRUCT)]
    user32.CallNextHookEx.restype = LRESULT
    user32.UnhookWindowsHookEx.argtypes = [ctypes.c_void_p]
    user32.UnhookWindowsHookEx.restype = wintypes.BOOL

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [
            ("wVk", wintypes.WORD),
            ("wScan", wintypes.WORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ctypes.c_size_t),
        ]

    class _INPUT_UNION(ctypes.Union):
        _fields_ = [("ki", KEYBDINPUT), ("_pad", ctypes.c_byte * 32)]

    class INPUT(ctypes.Structure):
        _fields_ = [("type", wintypes.DWORD), ("u", _INPUT_UNION)]

    user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
    user32.SendInput.restype = wintypes.UINT
    user32.MapVirtualKeyW.argtypes = [wintypes.UINT, wintypes.UINT]
    user32.MapVirtualKeyW.restype = wintypes.UINT

    def _send_key(vk: int, up: bool = False) -> None:
        scan = user32.MapVirtualKeyW(vk, 0)
        flags = KEYEVENTF_KEYUP if up else 0
        inp = INPUT(type=INPUT_KEYBOARD)
        inp.u.ki = KEYBDINPUT(wVk=vk, wScan=scan, dwFlags=flags, time=0, dwExtraInfo=0)
        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

    def _send_combo(*vks: int) -> None:
        for vk in vks:
            _send_key(vk, up=False)
            time.sleep(0.015)
        for vk in reversed(vks):
            _send_key(vk, up=True)
            time.sleep(0.015)

    def get_clipboard_text() -> str:
        for _ in range(5):
            if user32.OpenClipboard(None):
                try:
                    handle = user32.GetClipboardData(CF_UNICODETEXT)
                    if not handle:
                        return ""
                    ptr = kernel32.GlobalLock(handle)
                    if not ptr:
                        return ""
                    try:
                        return ctypes.wstring_at(ptr)
                    finally:
                        kernel32.GlobalUnlock(handle)
                finally:
                    user32.CloseClipboard()
            time.sleep(0.02)
        return ""

    def set_clipboard_text(text: str) -> bool:
        encoded = (text + "\0").encode("utf-16-le")
        for _ in range(5):
            if user32.OpenClipboard(None):
                try:
                    user32.EmptyClipboard()
                    hmem = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(encoded))
                    if not hmem:
                        return False
                    ptr = kernel32.GlobalLock(hmem)
                    if not ptr:
                        kernel32.GlobalFree(hmem)
                        return False
                    ctypes.memmove(ptr, encoded, len(encoded))
                    kernel32.GlobalUnlock(hmem)
                    if not user32.SetClipboardData(CF_UNICODETEXT, hmem):
                        kernel32.GlobalFree(hmem)
                        return False
                    return True
                finally:
                    user32.CloseClipboard()
            time.sleep(0.02)
        return False

    def _beep_async(freq: int, ms: int, enabled: bool) -> None:
        if enabled:
            threading.Thread(target=winsound.Beep, args=(freq, ms), daemon=True).start()

    class GUITHREADINFO(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("flags", wintypes.DWORD),
            ("hwndActive", wintypes.HWND),
            ("hwndFocus", wintypes.HWND),
            ("hwndCapture", wintypes.HWND),
            ("hwndMenuOwner", wintypes.HWND),
            ("hwndMoveSize", wintypes.HWND),
            ("hwndCaret", wintypes.HWND),
            ("rcCaret", wintypes.RECT),
        ]

    user32.GetGUIThreadInfo.argtypes = [wintypes.DWORD, ctypes.POINTER(GUITHREADINFO)]
    user32.GetGUIThreadInfo.restype = wintypes.BOOL

    def _get_active_hkl() -> ctypes.c_void_p:
        gti = GUITHREADINFO(cbSize=ctypes.sizeof(GUITHREADINFO))
        hwnd = None
        if user32.GetGUIThreadInfo(0, ctypes.byref(gti)):
            hwnd = gti.hwndFocus or gti.hwndActive
        if not hwnd:
            hwnd = user32.GetForegroundWindow()
        tid = user32.GetWindowThreadProcessId(hwnd, None) if hwnd else 0
        return user32.GetKeyboardLayout(tid)

    def _vk_to_char(vk: int, scan: int) -> str:
        hkl = _get_active_hkl()
        state = (ctypes.c_ubyte * 256)()
        if user32.GetAsyncKeyState(VK_SHIFT) & 0x8000:
            state[VK_SHIFT] = 0x80
        buf = ctypes.create_unicode_buffer(8)
        n = user32.ToUnicodeEx(vk, scan, state, buf, 8, 0, hkl)
        return buf.value[:n] if n > 0 else ""


def run_prompt_daemon() -> None:
    if os.name != "nt":
        print("Daemon mode requires Windows.")
        sys.exit(1)

    mutex = kernel32.CreateMutexW(None, False, "Global\\AgyMonPromptLiteMutex")
    if ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
        if mutex:
            kernel32.CloseHandle(mutex)
        print("Prompt Lite daemon is already running.")
        return

    cfg = load_prompt_config()
    enabled = bool(cfg.get("enabled", True))
    trigger_seq = cfg.get("trigger", ";;") or ";;"
    last_cfg_mtime = PROMPT_CFG_PATH.stat().st_mtime if PROMPT_CFG_PATH.exists() else 0.0
    recent_chars = ""
    injecting = threading.Event()
    worker_busy = threading.Event()
    trigger_q: queue.SimpleQueue[str] = queue.SimpleQueue()

    log_path = GEMINI_DIR / "prompt_lite_daemon.log"

    def _dlog(msg: str) -> None:
        try:
            ts = time.strftime("%H:%M:%S")
            if log_path.exists() and log_path.stat().st_size > 65536:
                log_path.write_text("", encoding="utf-8")
            with log_path.open("a", encoding="utf-8") as f:
                f.write(f"[{ts}] {msg}\n")
        except Exception:
            pass

    def _desktop_name() -> str:
        try:
            u = user32
            u.GetProcessWindowStation.restype = ctypes.c_void_p
            u.GetThreadDesktop.restype = ctypes.c_void_p
            u.GetUserObjectInformationW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
            buf = ctypes.create_unicode_buffer(256)
            need = wintypes.DWORD()
            hdesk = u.GetThreadDesktop(kernel32.GetCurrentThreadId())
            u.GetUserObjectInformationW(hdesk, 2, buf, 512, ctypes.byref(need))
            return buf.value
        except Exception:
            return "?"

    _dlog(f"daemon started pid={os.getpid()} trigger={trigger_seq!r} enabled={enabled} desk={_desktop_name()!r}")

    def _check_paste_trigger() -> None:
        nonlocal recent_chars
        try:
            clip = (get_clipboard_text() or "").rstrip()
            if clip.endswith(trigger_seq):
                recent_chars = trigger_seq
        except Exception:
            pass

    def _worker() -> None:
        nonlocal enabled, trigger_seq, last_cfg_mtime
        while True:
            try:
                mode = trigger_q.get(timeout=5.0)
            except queue.Empty:
                try:
                    if PROMPT_CFG_PATH.exists():
                        mtime = PROMPT_CFG_PATH.stat().st_mtime
                        if mtime != last_cfg_mtime:
                            last_cfg_mtime = mtime
                            new_cfg = load_prompt_config()
                            enabled = bool(new_cfg.get("enabled", True))
                            new_trig = new_cfg.get("trigger", ";;") or ";;"
                            if new_trig != trigger_seq:
                                trigger_seq = new_trig
                except Exception:
                    pass
                continue

            worker_busy.set()
            if mode == "preview":
                for _ in range(16):
                    if not (user32.GetAsyncKeyState(VK_MENU) & 0x8000):
                        break
                    time.sleep(0.015)
            time.sleep(0.04)

            pasted = False
            prev_clip = ""
            restore_clip = False
            try:
                local_cfg = load_prompt_config()
                enabled = bool(local_cfg.get("enabled", True))
                trig = local_cfg.get("trigger", ";;") or ";;"
                trigger_seq = trig
                if not enabled:
                    if mode == "submit":
                        injecting.set()
                        try:
                            _send_combo(VK_RETURN)
                        finally:
                            injecting.clear()
                    continue
                restore_clip = bool(local_cfg.get("restore_clipboard", True))
                prev_clip = get_clipboard_text() if restore_clip else ""

                injecting.set()
                try:
                    set_clipboard_text("")
                    _send_combo(VK_LCONTROL, VK_A)
                    time.sleep(0.06)
                    _send_combo(VK_LCONTROL, VK_C)
                finally:
                    injecting.clear()

                src = ""
                for _ in range(14):
                    time.sleep(0.025)
                    src = get_clipboard_text()
                    if src:
                        break
                stripped = src.rstrip()
                _dlog(f"worker mode={mode} src_len={len(src)} ends_trig={stripped.endswith(trig)}")
                if mode == "submit":
                    if stripped.endswith(trig):
                        body = stripped[: -len(trig)].rstrip()
                    else:
                        body = ""
                else:
                    body = stripped[: -len(trig)].rstrip() if stripped.endswith(trig) else stripped

                if body and any("\u0e00" <= c <= "\u0e7f" for c in body):
                    out, _eng = translate_prompt(body, local_cfg)
                    _dlog(f"translated eng={_eng} body_len={len(body)} out_len={len(out or '')}")
                    if out and out != body:
                        injecting.set()
                        try:
                            set_clipboard_text(out)
                            _send_combo(VK_LCONTROL, VK_A)
                            time.sleep(0.03)
                            _send_combo(VK_LCONTROL, VK_V)
                            pasted = True
                        finally:
                            injecting.clear()

                        _beep_async(1250, 45, local_cfg.get("beep", True))

                        t_in, t_out = estimate_tokens(body), estimate_tokens(out)
                        record_stats(t_in, t_out)
                    else:
                        _beep_async(500, 70, local_cfg.get("beep", True))

                if mode == "submit":
                    time.sleep(0.06 if pasted else 0.03)
                    injecting.set()
                    try:
                        _send_combo(VK_RETURN)
                    finally:
                        injecting.clear()
            except Exception as ex:
                _dlog(f"worker error: {ex!r}")
            finally:
                worker_busy.clear()
                if restore_clip and prev_clip:
                    if pasted:
                        time.sleep(0.15)
                    set_clipboard_text(prev_clip)

    threading.Thread(target=_worker, daemon=True).start()

    first_key_logged = False

    @HOOKPROC
    def _ll_kb_proc(nCode: int, wParam: wintypes.WPARAM, lParam: ctypes.POINTER(KBDLLHOOKSTRUCT)) -> int:
        nonlocal recent_chars, first_key_logged
        try:
            if nCode >= 0 and enabled and not injecting.is_set() and wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
                kb = lParam.contents
                if not first_key_logged:
                    first_key_logged = True
                    _dlog(f"hook alive first vk={hex(kb.vkCode)} flags={hex(kb.flags)}")
                if not (kb.flags & 0x10):
                    if worker_busy.is_set() and kb.vkCode == VK_RETURN:
                        return 1
                    ctrl = bool(user32.GetAsyncKeyState(VK_CONTROL) & 0x8000)
                    alt = bool(user32.GetAsyncKeyState(VK_MENU) & 0x8000)
                    shift = bool(user32.GetAsyncKeyState(VK_SHIFT) & 0x8000)
                    if (alt and not ctrl and kb.vkCode == VK_T) or (not alt and not ctrl and not shift and kb.vkCode == VK_F8):
                        if worker_busy.is_set():
                            return 1
                        recent_chars = ""
                        if alt:
                            injecting.set()
                            try:
                                _send_key(VK_LCONTROL, up=False)
                                _send_key(VK_LCONTROL, up=True)
                            finally:
                                injecting.clear()
                        trigger_q.put("preview")
                        return 1
                    if ctrl and not alt and kb.vkCode == VK_V:
                        recent_chars = ""
                        threading.Thread(target=_check_paste_trigger, daemon=True).start()
                    elif ctrl or alt:
                        recent_chars = ""
                    elif kb.vkCode == VK_BACK:
                        recent_chars = recent_chars[:-1]
                    elif kb.vkCode in (VK_ESCAPE, VK_LEFT, VK_RIGHT, VK_UP, VK_DOWN, VK_HOME, VK_END):
                        recent_chars = ""
                    elif kb.vkCode == VK_RETURN and not shift:
                        if recent_chars.endswith(trigger_seq):
                            _dlog(f"hook trigger submit recent={recent_chars!r}")
                            recent_chars = ""
                            trigger_q.put("submit")
                            return 1
                        _dlog(f"enter skip recent={recent_chars!r}")
                        recent_chars = ""
                    else:
                        if kb.vkCode == VK_PACKET:
                            ch = chr(kb.scanCode) if kb.scanCode else ""
                        else:
                            ch = _vk_to_char(kb.vkCode, kb.scanCode)
                        if ch:
                            recent_chars = (recent_chars + ch)[-len(trigger_seq) :]
        except Exception as ex:
            _dlog(f"hook error: {ex!r}")
        return user32.CallNextHookEx(None, nCode, wParam, lParam)

    hmod = kernel32.GetModuleHandleW(None)
    hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, _ll_kb_proc, hmod, 0)
    _dlog(f"SetWindowsHookExW hook={hook} err={ctypes.get_last_error()}")
    if not hook:
        if mutex:
            kernel32.CloseHandle(mutex)
        sys.exit(1)

    msg = wintypes.MSG()
    try:
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
    except KeyboardInterrupt:
        pass
    finally:
        user32.UnhookWindowsHookEx(hook)
        if mutex:
            kernel32.CloseHandle(mutex)


# ==============================================================================
# Antigravity Usage Monitor & IDE Tools
# ==============================================================================

def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def run_cmd(cmd: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            check=False,
            encoding="utf-8",
            errors="replace"
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except Exception as ex:
        return 1, "", str(ex)


def pause() -> None:
    print(f"\n{C_GRAY}กด Enter เพื่อกลับไปเมนูหลัก...{C_RESET}", end="", flush=True)
    try:
        input()
    except (KeyboardInterrupt, EOFError):
        pass


def get_ide_executable() -> Path | None:
    for exe in IDE_EXE_CANDIDATES:
        if exe.exists():
            return exe
    which_exe = shutil.which("Antigravity IDE") or shutil.which("antigravity-ide")
    return Path(which_exe) if which_exe else None


def _get_pythonw_executable() -> str:
    candidate = Path(sys.executable).with_name("pythonw.exe")
    if candidate.exists():
        return str(candidate)
    return shutil.which("pythonw") or sys.executable


def get_prompt_daemon_pids(only_legacy: bool = False) -> list[int]:
    if only_legacy:
        flt = "$_.CommandLine -like '*agy_mon.py*daemon*' -or $_.CommandLine -like '*prompt_lite.py*'"
    else:
        flt = "$_.CommandLine -like '*agyx.py*daemon*' -or $_.CommandLine -like '*agy_mon.py*daemon*' -or $_.CommandLine -like '*prompt_lite.py*'"
    code, out, _ = run_cmd([
        "powershell", "-NoProfile", "-Command",
        "Get-CimInstance Win32_Process -Filter \"Name='pythonw.exe' OR Name='python.exe'\" | "
        f"Where-Object {{ {flt} }} | "
        "Select-Object -ExpandProperty ProcessId"
    ])
    if code != 0 or not out:
        return []
    return [int(line.strip()) for line in out.splitlines() if line.strip().isdigit()]


def ensure_plugin_enabled_in_config() -> bool:
    if not CONFIG_FILE.exists():
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = {"plugins": {}}
    else:
        try:
            content = CONFIG_FILE.read_text(encoding="utf-8").strip()
            data = json.loads(content) if content else {"plugins": {}}
        except Exception:
            data = {"plugins": {}}

    plugins = data.setdefault("plugins", {})
    if plugins.get("usage-monitor", {}).get("enabled") is True:
        return True

    plugins["usage-monitor"] = {"enabled": True}
    try:
        CONFIG_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return True
    except Exception:
        return False


def patch_argv_file(target_path: Path) -> bool:
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        data: dict = {}
        if target_path.exists():
            raw = target_path.read_text(encoding="utf-8")
            clean_raw = re.sub(
                r'"(?:\\.|[^"\\])*"|//[^\n]*|/\*[\s\S]*?\*/',
                lambda m: m.group(0) if m.group(0).startswith('"') else "",
                raw,
            ).strip()
            if clean_raw:
                try:
                    data = json.loads(clean_raw)
                except Exception as ex:
                    print(f"  {C_RED}[ERR]{C_RESET} {target_path.name} JSON ไม่ถูกต้อง (ข้ามเพื่อไม่ให้ทับค่าเดิม): {ex}")
                    return False

        if data.get("remote-debugging-port") == "0":
            print(f"  {C_GREEN}[OK]{C_RESET} {target_path.parent.name}/{target_path.name} ตั้งค่า port 0 เรียบร้อยแล้ว")
            return True

        data["remote-debugging-port"] = "0"
        target_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        print(f"  {C_GREEN}[OK]{C_RESET} อัปเดต {target_path.parent.name}/{target_path.name} (remote-debugging-port: 0)")
        return True
    except Exception as ex:
        print(f"  {C_RED}[ERR]{C_RESET} {target_path.name}: {ex}")
        return False


def patch_shortcuts() -> None:
    if platform.system() != "Windows":
        return

    candidates = [
        APPDATA_DIR / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Antigravity.lnk",
        APPDATA_DIR / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Antigravity IDE" / "Antigravity IDE.lnk",
        USER_HOME / "Desktop" / "Antigravity.lnk",
        USER_HOME / "Desktop" / "Antigravity IDE.lnk",
        Path(os.environ.get("PUBLIC", "C:/Users/Public")) / "Desktop" / "Antigravity IDE.lnk",
    ]

    valid_paths = [f"'{str(p)}'" for p in candidates if p.exists()]
    if not valid_paths:
        return

    ps_script = """
    $sh = New-Object -ComObject WScript.Shell
    $paths = @({paths})
    foreach ($p in $paths) {
        if (Test-Path $p) {
            try {
                $lnk = $sh.CreateShortcut($p)
                if ($lnk.Arguments -notmatch '--remote-debugging-port=0') {
                    $lnk.Arguments = ($lnk.Arguments + ' --remote-debugging-port=0').Trim()
                    $lnk.Save()
                    Write-Output "UPDATED: $p"
                } else {
                    Write-Output "OK: $p"
                }
            } catch {
                Write-Output "FAIL: $p"
            }
        }
    }
    """
    _, out, _ = run_cmd(["powershell", "-NoProfile", "-Command", ps_script.replace("{paths}", ", ".join(valid_paths))])
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("UPDATED:"):
            print(f"  {C_GREEN}[OK]{C_RESET} อัปเดต Flag ทางลัด: {Path(line[8:].strip()).name}")
        elif line.startswith("OK:"):
            print(f"  {C_GREEN}[OK]{C_RESET} ทางลัดมี Flag พร้อมแล้ว: {Path(line[3:].strip()).name}")


def get_active_cdp_port() -> tuple[int | None, str | None]:
    for port_file in DEVTOOLS_PORTS:
        if port_file.exists():
            try:
                lines = port_file.read_text(encoding="utf-8").splitlines()
                if lines and lines[0].strip().isdigit():
                    pnum = int(lines[0].strip())
                    ws_path = lines[1].strip() if len(lines) > 1 else ""
                    return pnum, ws_path
            except Exception:
                continue
    return None, None


def verify_cdp_connection(port: int) -> dict | None:
    try:
        url = f"http://127.0.0.1:{port}/json/version"
        req = urllib.request.Request(url, headers={"User-Agent": "Antigravity-Mon"})
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode("utf-8"))
    except Exception:
        pass
    return None


def action_check() -> None:
    print(f"\n{C_BOLD}{C_CYAN}=== ตรวจสอบสถานะระบบ (Diagnostics) ==={C_RESET}")

    if PLUGIN_DIR.exists():
        plugin_json = PLUGIN_DIR / "plugin.json"
        ver = "unknown"
        if plugin_json.exists():
            try:
                ver = json.loads(plugin_json.read_text(encoding="utf-8")).get("version", ver)
            except Exception:
                pass
        print(f"สถานะปลั๊กอิน:      {C_GREEN}ติดตั้งแล้ว (v{ver}){C_RESET}")
        print(f"ตำแหน่ง:            {PLUGIN_DIR}")
    else:
        print(f"สถานะปลั๊กอิน:      {C_RED}ยังไม่ติดตั้ง{C_RESET}")

    cfg_ok = False
    if CONFIG_FILE.exists():
        try:
            cfg_ok = json.loads(CONFIG_FILE.read_text(encoding="utf-8")).get("plugins", {}).get("usage-monitor", {}).get("enabled") is True
        except Exception:
            pass
    print(f"เปิดใน config.json: {C_GREEN}เปิดใช้งานแล้ว{C_RESET}" if cfg_ok else f"เปิดใน config.json: {C_YELLOW}ยังไม่เปิด{C_RESET}")

    argv_candidates = [IDE_USER_ARGV, IDE_ROAMING_ARGV, IDE_LOCAL_ARGV]
    configured_argvs = []
    for argv_f in argv_candidates:
        if argv_f.exists():
            try:
                if "remote-debugging-port" in argv_f.read_text(encoding="utf-8"):
                    configured_argvs.append(argv_f.parent.name)
            except Exception:
                pass
    if configured_argvs:
        print(f"พอร์ต Debug ใน IDE: {C_GREEN}ตั้งค่าแล้ว ({', '.join(configured_argvs)}){C_RESET}")
    else:
        print(f"พอร์ต Debug ใน IDE: {C_YELLOW}ยังไม่ตั้งค่า (กดเมนู 2 เพื่อแพตช์){C_RESET}")

    code, ps_out, _ = run_cmd([
        "powershell", "-NoProfile", "-Command",
        "(Get-Process -Name 'Antigravity IDE' -ErrorAction SilentlyContinue).Count"
    ])
    count = int(ps_out.strip()) if code == 0 and ps_out.strip().isdigit() else 0
    if count > 0:
        print(f"โปรเซส Antigravity: {C_CYAN}กำลังรัน ({count} processes){C_RESET}")
    else:
        print(f"โปรเซส Antigravity: {C_GRAY}ไม่ได้เปิดอยู่{C_RESET}")

    port, _ = get_active_cdp_port()
    if port:
        cdp_meta = verify_cdp_connection(port)
        if cdp_meta:
            browser_ver = cdp_meta.get("Browser", "Active")
            print(f"CDP Debug Port:     {C_GREEN}{port} [Connected - {browser_ver}]{C_RESET}")
        else:
            print(f"CDP Debug Port:     {C_YELLOW}{port} [Port found but not responding]{C_RESET}")
    else:
        print(f"CDP Debug Port:     {C_GRAY}ไม่มีพอร์ตค้าง (ระบบจะสร้างเมื่อเปิด IDE ด้วย Flag Debug){C_RESET}")

    pl_pids = get_prompt_daemon_pids()
    if pl_pids:
        print(f"Prompt Lite (;;):   {C_GREEN}กำลังทำงาน (PID {', '.join(map(str, pl_pids))}){C_RESET}")
    else:
        print(f"Prompt Lite (;;):   {C_YELLOW}ปิดอยู่ (กดเมนู 5 เพื่อเปิด){C_RESET}")

    if PROMPT_STATS_PATH.exists():
        try:
            st = json.loads(PROMPT_STATS_PATH.read_text(encoding="utf-8"))
            print(f"ประหยัด Token สะสม: {C_CYAN}{st.get('tokens_saved', 0):,} tokens ({st.get('prompts', 0):,} prompts){C_RESET}")
        except Exception:
            pass


def action_patch() -> None:
    print(f"\n{C_BOLD}{C_CYAN}=== ปรับแต่งความเข้ากันได้กับ IDE (Patch) ==={C_RESET}")
    patch_argv_file(IDE_USER_ARGV)
    patch_argv_file(IDE_ROAMING_ARGV)
    patch_argv_file(IDE_LOCAL_ARGV)
    patch_shortcuts()

    wb_file = PLUGIN_DIR / "sidecars" / "panel" / "backend" / "window-bridge.mjs"
    if wb_file.exists():
        try:
            wb_code = wb_file.read_text(encoding="utf-8")
            target_str = "join(appData, 'Antigravity IDE', 'DevToolsActivePort'),"
            if target_str not in wb_code:
                old_anchor = "join(localAppData, 'Antigravity', 'DevToolsActivePort'),"
                replacement = (
                    old_anchor + "\n"
                    "      join(appData, 'Antigravity IDE', 'DevToolsActivePort'),\n"
                    "      join(localAppData, 'Antigravity IDE', 'DevToolsActivePort'),"
                )
                if old_anchor in wb_code:
                    wb_code = wb_code.replace(old_anchor, replacement, 1)
                    wb_file.write_text(wb_code, encoding="utf-8")
                    print(f"  {C_GREEN}[OK]{C_RESET} เพิ่มพอร์ตค้นหา IDE ใน window-bridge.mjs")
            else:
                print(f"  {C_GREEN}[OK]{C_RESET} window-bridge.mjs รองรับพอร์ต IDE แล้ว")
        except Exception as ex:
            print(f"  {C_RED}[ERR]{C_RESET} window-bridge.mjs: {ex}")

    wos_patched = False
    tb_file = PLUGIN_DIR / "sidecars" / "panel" / "backend" / "telemetry-builder.mjs"
    if tb_file.exists():
        try:
            tb_code = tb_file.read_text(encoding="utf-8")
            if "prompt_lite_stats.json" not in tb_code:
                imp_anchor = "import { isDeepStrictEqual } from 'node:util';"
                imp_repl = (
                    imp_anchor + "\n"
                    "import { readFileSync as _plReadFileSync } from 'node:fs';\n"
                    "import { homedir as _plHomedir } from 'node:os';\n"
                    "import { join as _plJoin } from 'node:path';"
                )
                ret_anchor = "  return finalPayload;"
                ret_repl = (
                    "  let _plStats = { prompts: 0, tokens_in: 0, tokens_out: 0, tokens_saved: 0 };\n"
                    "  try {\n"
                    "    const _plRaw = _plReadFileSync(_plJoin(_plHomedir(), '.gemini', 'prompt_lite_stats.json'), 'utf8');\n"
                    "    const parsedStats = JSON.parse(_plRaw);\n"
                    "    if (parsedStats && typeof parsedStats === 'object') {\n"
                    "      _plStats = { ..._plStats, ...parsedStats };\n"
                    "    }\n"
                    "  } catch {}\n"
                    "  let _plEnabled = true;\n"
                    "  let _plAutoEnter = true;\n"
                    "  let _plBackend = 'auto';\n"
                    "  try {\n"
                    "    const _plCfgRaw = _plReadFileSync(_plJoin(_plHomedir(), '.gemini', 'prompt_lite.json'), 'utf8');\n"
                    "    const _plCfg = JSON.parse(_plCfgRaw);\n"
                    "    if (_plCfg && typeof _plCfg === 'object') {\n"
                    "      if (typeof _plCfg.enabled === 'boolean') _plEnabled = _plCfg.enabled;\n"
                    "      if (typeof _plCfg.auto_enter === 'boolean') _plAutoEnter = _plCfg.auto_enter;\n"
                    "      if (typeof _plCfg.backend === 'string') _plBackend = _plCfg.backend;\n"
                    "    }\n"
                    "  } catch {}\n"
                    "  finalPayload.promptLite = { ..._plStats, enabled: _plEnabled, auto_enter: _plAutoEnter, backend: _plBackend };\n"
                    "  return finalPayload;"
                )
                if imp_anchor in tb_code and ret_anchor in tb_code:
                    tb_code = tb_code.replace(imp_anchor, imp_repl, 1).replace(ret_anchor, ret_repl, 1)
                    tb_file.write_text(tb_code, encoding="utf-8")
                    print(f"  {C_GREEN}[OK]{C_RESET} เชื่อม Prompt Lite stats ใน telemetry-builder.mjs")
            else:
                print(f"  {C_GREEN}[OK]{C_RESET} telemetry-builder.mjs เชื่อม Prompt Lite stats แล้ว")
        except Exception as ex:
            print(f"  {C_RED}[ERR]{C_RESET} telemetry-builder.mjs: {ex}")

    aa_file = PLUGIN_DIR / "sidecars" / "panel" / "backend" / "api-actions.mjs"
    if aa_file.exists():
        try:
            aa_code = aa_file.read_text(encoding="utf-8")
            if "/api/prompt-lite/toggle" not in aa_code:
                fs_anchor = "import { readFileSync, promises as fsPromises } from 'node:fs';"
                fs_repl = (
                    "import { readFileSync, writeFileSync, mkdirSync, promises as fsPromises } from 'node:fs';\n"
                    "import { execFile } from 'node:child_process';\n"
                    "import { homedir as _plApiHomedir } from 'node:os';"
                )
                disp_anchor = "export async function dispatchBridgeApiRequest(pathname, method, data, opts = undefined) {"
                disp_repl = (
                    "export function executePromptLiteToggleAction(data) {\n"
                    "  const cfgPath = join(_plApiHomedir(), '.gemini', 'prompt_lite.json');\n"
                    "  let cfg = {};\n"
                    "  try {\n"
                    "    cfg = JSON.parse(readFileSync(cfgPath, 'utf8'));\n"
                    "    if (!cfg || typeof cfg !== 'object') cfg = {};\n"
                    "  } catch {\n"
                    "    cfg = {};\n"
                    "  }\n"
                    "  const nextEnabled = typeof data?.enabled === 'boolean' ? data.enabled : (typeof cfg.enabled === 'boolean' ? cfg.enabled : true);\n"
                    "  if (typeof data?.enabled === 'boolean' || (data?.enabled === undefined && data?.auto_enter === undefined && !data?.backend)) {\n"
                    "    cfg.enabled = typeof data?.enabled === 'boolean' ? data.enabled : !(cfg.enabled !== false);\n"
                    "  } else {\n"
                    "    cfg.enabled = nextEnabled;\n"
                    "  }\n"
                    "  if (typeof data?.auto_enter === 'boolean') cfg.auto_enter = data.auto_enter;\n"
                    "  if (typeof data?.backend === 'string' && data.backend) cfg.backend = data.backend;\n"
                    "  try {\n"
                    "    mkdirSync(join(_plApiHomedir(), '.gemini'), { recursive: true });\n"
                    "    writeFileSync(cfgPath, JSON.stringify(cfg, null, 2) + '\\n', 'utf8');\n"
                    "  } catch (err) {\n"
                    "    return {\n"
                    "      status: 500,\n"
                    "      contentType: 'application/json',\n"
                    "      body: JSON.stringify({ error: String(err?.message || err) }),\n"
                    "    };\n"
                    "  }\n"
                    "  return {\n"
                    "    status: 200,\n"
                    "    contentType: 'application/json',\n"
                    "    body: JSON.stringify({ ok: true, enabled: cfg.enabled !== false, auto_enter: cfg.auto_enter !== false, backend: cfg.backend || 'auto' }),\n"
                    "  };\n"
                    "}\n\n"
                    "export function executePromptLiteTranslateAction(data) {\n"
                    "  const text = String(data?.text || '').trim();\n"
                    "  if (!text) {\n"
                    "    return Promise.resolve({ status: 400, contentType: 'application/json', body: JSON.stringify({ error: 'Empty text' }) });\n"
                    "  }\n"
                    "  const agyxPath = join(_plApiHomedir(), 'Downloads', 'agyx.py');\n"
                    "  return new Promise((resolve) => {\n"
                    "    execFile('python', [agyxPath, 'translate', text], { timeout: 12000, windowsHide: true }, (err, stdout, stderr) => {\n"
                    "      if (err) {\n"
                    "        resolve({ status: 500, contentType: 'application/json', body: JSON.stringify({ error: String(stderr || err.message || err) }) });\n"
                    "        return;\n"
                    "      }\n"
                    "      const lines = String(stdout || '').replace(/\\r\\n/g, '\\n').split('\\n');\n"
                    "      const header = lines.shift() || '';\n"
                    "      const out = lines.join('\\n').trim();\n"
                    "      resolve({ status: 200, contentType: 'application/json', body: JSON.stringify({ ok: true, meta: header, out }) });\n"
                    "    });\n"
                    "  });\n"
                    "}\n\n"
                    "export async function dispatchBridgeApiRequest(pathname, method, data, opts = undefined) {\n"
                    "  if (pathname === '/api/prompt-lite/toggle' && method === 'POST') {\n"
                    "    return executePromptLiteToggleAction(data);\n"
                    "  }\n"
                    "  if (pathname === '/api/prompt-lite/translate' && method === 'POST') {\n"
                    "    return executePromptLiteTranslateAction(data);\n"
                    "  }"
                )
                if fs_anchor in aa_code and disp_anchor in aa_code:
                    aa_code = aa_code.replace(fs_anchor, fs_repl, 1).replace(disp_anchor, disp_repl, 1)
                    aa_file.write_text(aa_code, encoding="utf-8")
                    print(f"  {C_GREEN}[OK]{C_RESET} เพิ่ม /api/prompt-lite/toggle ใน api-actions.mjs")
            else:
                print(f"  {C_GREEN}[OK]{C_RESET} api-actions.mjs รองรับ /api/prompt-lite/toggle แล้ว")
        except Exception as ex:
            print(f"  {C_RED}[ERR]{C_RESET} api-actions.mjs: {ex}")

    wos_file = PLUGIN_DIR / "sidecars" / "panel" / "src" / "components" / "layout" / "WindowOverlayShell.js"
    if wos_file.exists():
        try:
            wos_code = wos_file.read_text(encoding="utf-8")
            if "const ideTarget = findIdeWorkbenchTitlebar();" not in wos_code:
                anchor = "const titlebar = findHostTitlebar();"
                if anchor in wos_code:
                    replacement = "const ideTarget = findIdeWorkbenchTitlebar();\n  if (ideTarget) return ideTarget;\n  " + anchor
                    wos_code = wos_code.replace(anchor, replacement, 1)
                    wos_patched = True
                    print(f"  {C_GREEN}[OK]{C_RESET} เชื่อมต่อ Titlebar hook บน Monaco Workbench")
            else:
                print(f"  {C_GREEN}[OK]{C_RESET} WindowOverlayShell.js รองรับ Titlebar ของ IDE แล้ว")

            if "surface.promptLiteBadge" not in wos_code:
                imp_http_old = "import { deliverCdpBridgeResponses, getWindowBridgeConfig } from '../../core/httpClient.js';"
                imp_http_new = "import { callSidecarApi, deliverCdpBridgeResponses, getWindowBridgeConfig } from '../../core/httpClient.js';"
                if imp_http_old in wos_code:
                    wos_code = wos_code.replace(imp_http_old, imp_http_new, 1)
                dom_anchor = "    shadow.appendChild(uBtn);"
                dom_repl = (
                    "    shadow.appendChild(uBtn);\n"
                    "    const compactCss = document.createElement('style');\n"
                    "    compactCss.textContent = `\n"
                    "      :host { opacity: 0.6; transition: opacity 180ms ease; }\n"
                    "      :host(:hover), :host(:focus-within) { opacity: 1; }\n"
                    "      .wm-capsule-btn { min-height: 18px !important; height: 18px !important; padding: 0 6px !important; font-size: 10px !important; gap: 4px !important; }\n"
                    "      .wm-multi-btn { min-height: 18px !important; height: 18px !important; padding: 0 5px !important; font-size: 10px !important; }\n"
                    "      .wm-prompt-lite-badge { opacity: 0.85; -webkit-app-region: no-drag; pointer-events: auto; transition: opacity 180ms ease, transform 220ms ease, color 220ms ease, border-color 220ms ease, background 220ms ease; }\n"
                    "      .wm-prompt-lite-badge:hover { opacity: 1; }\n"
                    "    `;\n"
                    "    shadow.appendChild(compactCss);\n"
                    "    const plText = h('span', { style: 'font-variant-numeric:tabular-nums;pointer-events:none;' });\n"
                    "    const plBadge = h('button', {\n"
                    "      type: 'button',\n"
                    "      className: 'wm-prompt-lite-badge wm-prompt-lite-v2',\n"
                    "      hidden: true,\n"
                    "      style: 'display:inline-flex;align-items:center;height:18px;padding:0 6px;margin-left:4px;border-radius:999px;font-size:9.5px;font-weight:600;line-height:1;font-family:var(--ag-host-font-family,inherit);backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);background:rgba(16,185,129,0.14);color:#34d399;border:1px solid rgba(52,211,153,0.40);white-space:nowrap;user-select:none;cursor:pointer;-webkit-app-region:no-drag;pointer-events:auto;',\n"
                    "      onMousedown: (e) => {\n"
                    "        e.stopPropagation();\n"
                    "      },\n"
                    "      onClick: async (e) => {\n"
                    "        e.preventDefault();\n"
                    "        e.stopPropagation();\n"
                    "        const curEnabled = telemetryStore.getState().telemetry?.promptLite?.enabled !== false;\n"
                    "        const nextEnabled = !curEnabled;\n"
                    "        plBadge.style.color = nextEnabled ? '#34d399' : '#f87171';\n"
                    "        plBadge.style.borderColor = nextEnabled ? 'rgba(52,211,153,0.40)' : 'rgba(248,113,113,0.42)';\n"
                    "        plBadge.style.background = nextEnabled ? 'rgba(16,185,129,0.14)' : 'rgba(239,68,68,0.14)';\n"
                    "        const st0 = telemetryStore.getState();\n"
                    "        if (st0?.telemetry) {\n"
                    "          telemetryStore.setState({ telemetry: { ...st0.telemetry, promptLite: { ...(st0.telemetry.promptLite || {}), enabled: nextEnabled } } });\n"
                    "        }\n"
                    "        try {\n"
                    "          await callSidecarApi('/api/prompt-lite/toggle', { method: 'POST', body: { enabled: nextEnabled } });\n"
                    "          fetchTelemetry().catch(() => {});\n"
                    "        } catch {}\n"
                    "      },\n"
                    "    }, [plText]);\n"
                    "    plBadge._plText = plText;\n"
                    "    plBadge._plLastSaved = -1;\n"
                    "    shadow.appendChild(plBadge);"
                )
                surf_anchor = "    surface.updateDot = uDot;"
                surf_repl = "    surface.updateDot = uDot;\n    surface.promptLiteBadge = plBadge;"
                upd_anchor = "    const showUpdatePrompt ="
                upd_repl = (
                    "    const _plStats = telemetry?.promptLite;\n"
                    "    const _plEnabled = _plStats?.enabled !== false;\n"
                    "    const _plIn = Number(_plStats?.tokens_in || 0);\n"
                    "    const _plSaved = Number(_plStats?.tokens_saved || 0);\n"
                    "    const _plPrompts = Number(_plStats?.prompts || 0);\n"
                    "    const _plPct = _plIn > 0 ? Math.round((_plSaved / _plIn) * 100) : 0;\n"
                    "    const _plTier = !_plEnabled\n"
                    "      ? { c: '#f87171', b: 'rgba(248,113,113,0.42)', bg: 'rgba(239,68,68,0.14)', g: 'rgba(239,68,68,0.24)' }\n"
                    "      : { c: '#34d399', b: 'rgba(52,211,153,0.40)', bg: 'rgba(16,185,129,0.14)', g: 'rgba(16,185,129,0.24)' };\n"
                    "    for (const s of getAllCapsuleSurfaces()) {\n"
                    "      const b = s.promptLiteBadge;\n"
                    "      if (b) {\n"
                    "        patchAttr(b, 'hidden', !_plStats);\n"
                    "        if (_plStats) {\n"
                    "          const label = _plSaved > 0 ? `-${_plPct}%` : '0%';\n"
                    "          patchText(b._plText || b, label);\n"
                    "          patchAttr(\n"
                    "            b,\n"
                    "            'title',\n"
                    "            !_plEnabled\n"
                    "              ? `Prompt Lite ปิดอยู่ (คลิกเพื่อเปิด)\\nประหยัดสะสม ${_plPct}% (-${_plSaved.toLocaleString()} tok)`\n"
                    "              : `Prompt Lite เปิดอยู่ (คลิกเพื่อปิด)\\nประหยัด ${_plPct}% (-${_plSaved.toLocaleString()} tok / ${_plPrompts} ครั้ง)\\nพิมพ์ไทย + กด Enter เพื่อแปลอัตโนมัติ`\n"
                    "          );\n"
                    "          b.style.color = _plTier.c;\n"
                    "          b.style.borderColor = _plTier.b;\n"
                    "          b.style.background = _plTier.bg;\n"
                    "          if (_plEnabled && b._plLastSaved >= 0 && _plSaved > b._plLastSaved) {\n"
                    "            b.style.transform = 'scale(1.05)';\n"
                    "            b.style.opacity = '1';\n"
                    "            setTimeout(() => {\n"
                    "              b.style.transform = 'scale(1)';\n"
                    "              b.style.opacity = '';\n"
                    "            }, 900);\n"
                    "          }\n"
                    "          b._plLastSaved = _plSaved;\n"
                    "        }\n"
                    "      }\n"
                    "    }\n"
                    "    const showUpdatePrompt ="
                )
                if dom_anchor in wos_code and surf_anchor in wos_code and upd_anchor in wos_code:
                    wos_code = (
                        wos_code.replace(dom_anchor, dom_repl, 1)
                        .replace(surf_anchor, surf_repl, 1)
                        .replace(upd_anchor, upd_repl, 1)
                    )
                    wos_patched = True
                    print(f"  {C_GREEN}[OK]{C_RESET} เพิ่ม Prompt Lite Badge บน Capsule ใน WindowOverlayShell.js")
            else:
                print(f"  {C_GREEN}[OK]{C_RESET} WindowOverlayShell.js มี Prompt Lite Badge แล้ว")

            if wos_patched:
                wos_file.write_text(wos_code, encoding="utf-8")
                build_script = PLUGIN_DIR / "sidecars" / "panel" / "scripts" / "build-bundle.mjs"
                if build_script.exists():
                    b_code, _, b_err = run_cmd(["node", str(build_script)])
                    if b_code == 0:
                        print(f"  {C_GREEN}[OK]{C_RESET} รีบิลด์ Web bundle สำเร็จ")
                    else:
                        print(f"  {C_RED}[ERR]{C_RESET} รีบิลด์ Web bundle ล้มเหลว: {b_err}")
        except Exception as ex:
            print(f"  {C_RED}[ERR]{C_RESET} WindowOverlayShell.js: {ex}")

    ensure_plugin_enabled_in_config()
    print(f"\n{C_GREEN}การแพตช์เสร็จสมบูรณ์!{C_RESET}")


def action_update() -> None:
    print(f"\n{C_BOLD}{C_CYAN}=== อัปเดตปลั๊กอินจาก GitHub ==={C_RESET}")
    if not PLUGIN_DIR.exists():
        print("กำลัง Clone ปลั๊กอิน...")
        code, _, err = run_cmd(["git", "clone", REPO_URL, str(PLUGIN_DIR)])
        if code == 0:
            print(f"{C_GREEN}[OK] ติดตั้งปลั๊กอินเรียบร้อย{C_RESET}")
        else:
            print(f"{C_RED}[ERR] Clone ล้มเหลว: {err}{C_RESET}")
            return
    else:
        print("กำลังเคลียร์การแก้ไขชั่วคราวและดึง Git Pull ล่าสุด...")
        run_cmd(["git", "-C", str(PLUGIN_DIR), "stash"])
        code, out, err = run_cmd(["git", "-C", str(PLUGIN_DIR), "pull"])
        if code == 0:
            print(f"{C_GREEN}[OK] {out}{C_RESET}")
        else:
            print(f"{C_RED}[ERR] Pull ล้มเหลว: {err}{C_RESET}")
            return

    action_patch()


def action_restart_ide(skip_patch: bool = False) -> None:
    print(f"\n{C_BOLD}{C_CYAN}=== เปิด/รีสตาร์ต Antigravity IDE พร้อม Capsule ==={C_RESET}")
    if not skip_patch:
        action_patch()

    print("กำลังปิดโปรเซส IDE เดิม...")
    run_cmd(["powershell", "-NoProfile", "-Command", "Stop-Process -Name 'Antigravity IDE' -Force -ErrorAction SilentlyContinue"])
    time.sleep(1.5)

    exe = get_ide_executable()
    if exe and exe.exists():
        print(f"กำลังเปิด: {exe} พร้อม --remote-debugging-port=0")
        flags = 0x00000008 | 0x00000200 if os.name == "nt" else 0
        subprocess.Popen([str(exe), "--remote-debugging-port=0"], shell=False, creationflags=flags)
        print(f"{C_GREEN}[OK] เปิด Antigravity IDE สำเร็จแล้ว! (Capsule จะแสดงผลใน IDE ทันที){C_RESET}")
    else:
        print(f"{C_RED}[ERR] ไม่พบไฟล์โปรแกรม Antigravity IDE ในระบบ{C_RESET}")


def action_toggle_prompt_lite() -> None:
    print(f"\n{C_BOLD}{C_CYAN}=== จัดการ Prompt Lite (;; Auto-Translate) ==={C_RESET}")
    pids = get_prompt_daemon_pids()
    if pids:
        for pid in pids:
            run_cmd(["powershell", "-NoProfile", "-Command", f"Stop-Process -Id {pid} -Force -ErrorAction SilentlyContinue"])
        print(f"{C_YELLOW}[OK] ปิด Prompt Lite เรียบร้อย{C_RESET}")
        return

    pyw = _get_pythonw_executable()
    flags = 0x00000008 | 0x00000200 if os.name == "nt" else 0
    subprocess.Popen([pyw, str(SELF_PATH), "daemon"], cwd=str(SELF_PATH.parent), creationflags=flags)
    print(f"{C_GREEN}[OK] เปิด Prompt Lite เบื้องหลังแล้ว (พิมพ์ลงท้าย ;; เพื่อแปลอัตโนมัติ){C_RESET}")


def ensure_prompt_autostart_and_running() -> None:
    if platform.system() == "Windows":
        pyw = _get_pythonw_executable()
        ps = (
            "$sh = New-Object -ComObject WScript.Shell; "
            "$lnk = $sh.CreateShortcut(([Environment]::GetFolderPath('Startup')) + '\\PromptLite.lnk'); "
            f"$lnk.TargetPath = '{pyw}'; "
            f"$lnk.Arguments = '\"{SELF_PATH}\" daemon'; "
            f"$lnk.WorkingDirectory = '{SELF_PATH.parent}'; "
            "$lnk.WindowStyle = 7; "
            "$lnk.Save()"
        )
        run_cmd(["powershell", "-NoProfile", "-Command", ps])
        print(f"  {C_GREEN}[OK]{C_RESET} ตั้งค่าเปิด Prompt Lite (;; ) อัตโนมัติตอนเปิดเครื่องแล้ว")

    for old_pid in get_prompt_daemon_pids(only_legacy=True):
        run_cmd(["powershell", "-NoProfile", "-Command", f"Stop-Process -Id {old_pid} -Force -ErrorAction SilentlyContinue"])

    if not get_prompt_daemon_pids():
        pyw = _get_pythonw_executable()
        flags = 0x00000008 | 0x00000200 if os.name == "nt" else 0
        subprocess.Popen([pyw, str(SELF_PATH), "daemon"], cwd=str(SELF_PATH.parent), creationflags=flags)
        print(f"  {C_GREEN}[OK]{C_RESET} เปิด Prompt Lite (;; ) เบื้องหลังแล้ว")
    else:
        print(f"  {C_GREEN}[OK]{C_RESET} Prompt Lite (;; ) กำลังทำงานอยู่แล้ว")


def action_all_in_one() -> None:
    print(f"\n{C_BOLD}{C_CYAN}=== ทำงานครบจบในปุ่มเดียว (All-in-One) ==={C_RESET}")
    action_update()
    ensure_prompt_autostart_and_running()
    action_restart_ide(skip_patch=True)
    time.sleep(1.0)
    action_check()
    print(f"\n{C_GREEN}{C_BOLD}[DONE] ครบจบทุกอย่างพร้อมใช้งาน! (Update + Patch + Autostart + ;; + IDE + Check){C_RESET}")


def main_menu() -> None:
    while True:
        clear_screen()
        print(f"{C_BOLD}{C_CYAN}===================================================={C_RESET}")
        print(f"{C_BOLD}   📊 AGYX v{__version__} — USAGE MONITOR + PROMPT LITE {C_RESET}")
        print(f"{C_BOLD}{C_CYAN}===================================================={C_RESET}")
        print(f"  {C_BOLD}[1]{C_RESET} 🔍 ตรวจสอบสถานะระบบ (Check Status)")
        print(f"  {C_BOLD}[2]{C_RESET} 🛠️  แพตช์รองรับ IDE (Patch argv & Titlebar)")
        print(f"  {C_BOLD}[3]{C_RESET} 🚀 เปิด/รีสตาร์ต IDE พร้อม Capsule (Launch with Flag)")
        print(f"  {C_BOLD}[4]{C_RESET} ⬇️  อัปเดตปลั๊กอินจาก GitHub (Git Pull & Rebuild)")
        print(f"  {C_BOLD}[5]{C_RESET} ⚡ เปิด/ปิด Prompt Lite (;; Auto-Translate)")
        print(f"  {C_BOLD}[6]{C_RESET} 🔥 ครบจบในปุ่มเดียว (Update + Patch + Autostart + ;; + IDE)")
        print(f"  {C_BOLD}[0]{C_RESET} ❌ ออกจากโปรแกรม (Exit)")
        print(f"{C_CYAN}----------------------------------------------------{C_RESET}")

        try:
            choice = input(f"{C_BOLD}เลือกเมนู [0-6]: {C_RESET}").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n")
            break

        if choice == "1":
            action_check()
            pause()
        elif choice == "2":
            action_patch()
            pause()
        elif choice == "3":
            action_restart_ide()
            pause()
        elif choice == "4":
            action_update()
            pause()
        elif choice == "5":
            action_toggle_prompt_lite()
            pause()
        elif choice == "6":
            action_all_in_one()
            pause()
        elif choice in ("0", "q", "exit"):
            print(f"\n{C_GRAY}ออกจากโปรแกรมเรียบร้อย{C_RESET}")
            break
        else:
            print(f"{C_YELLOW}กรุณาเลือกตัวเลข 0 ถึง 6{C_RESET}")
            time.sleep(1)


if __name__ == "__main__":
    if os.name == "nt":
        os.system("")
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ("check", "-c"):
            action_check()
        elif arg in ("patch", "-p"):
            action_patch()
        elif arg in ("restart", "launch", "-r"):
            action_restart_ide()
        elif arg in ("update", "-u"):
            action_update()
        elif arg in ("all", "-a"):
            action_all_in_one()
        elif arg in ("daemon", "-d"):
            run_prompt_daemon()
        elif arg in ("version", "-v", "--version"):
            print(f"agyx v{__version__}")
        elif arg in ("translate", "-t") and len(sys.argv) > 2:
            text_in = " ".join(sys.argv[2:]).strip()
            cfg = load_prompt_config()
            out, eng = translate_prompt(text_in, cfg)
            if os.name == "nt":
                set_clipboard_text(out)
            t_in, t_out = estimate_tokens(text_in), estimate_tokens(out)
            if eng not in ("empty", "passthrough", "unchanged"):
                record_stats(t_in, t_out)
            print(f"[{eng}] {t_in} -> {t_out} tok\n{out}")
        else:
            print(f"Unknown argument: {arg}")
    else:
        main_menu()
