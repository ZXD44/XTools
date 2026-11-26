"""
quota.py — Phase 2
ติดตามสถานะการใช้งานบัญชีจากข้อมูลที่ agy-manager เก็บเองได้จริง
(agy ไม่มี API ให้อ่าน quota จริง จึงนับ "จำนวนครั้งที่สลับมาใช้บัญชีนี้" ต่อวัน)

Badge: READY / LOW / LIMITED / VERIFY
"""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

from agy_config import XTOOLS_CONFIG, _atomic_write

_G = "\033[92m"; _Y = "\033[93m"; _R = "\033[91m"
_B = "\033[94m"; _D = "\033[90m"; _W = "\033[97m"; _X = "\033[0m"

# เกณฑ์นับจำนวนครั้งที่สลับมาใช้บัญชีต่อวัน
SWITCH_LOW = 10
SWITCH_HARD = 20


def _load_quota_cache(email: str) -> dict:
    try:
        if XTOOLS_CONFIG.exists():
            data = json.loads(XTOOLS_CONFIG.read_text(encoding="utf-8"))
            return data.get("agy_accounts", {}).get(email, {}).get("quota", {})
    except Exception:
        pass
    return {}


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def compute_badge(email: str) -> tuple[str, str, str]:
    """คำนวณ badge สถานะ (badge_key, color, countdown_str)"""
    cache = _load_quota_cache(email)
    now = _now_utc()

    # cooldown ที่ตั้งไว้ (จาก set_cooldown หรือ error 429 ที่ผู้ใช้บันทึกเอง)
    cooldown_str = cache.get("cooldown_until", "")
    if cooldown_str:
        try:
            cooldown_dt = datetime.fromisoformat(cooldown_str)
            if cooldown_dt > now:
                remaining = cooldown_dt - now
                h, m = divmod(int(remaining.total_seconds() // 60), 60)
                return "LIMITED", _R, f"รีเซตใน {h}ชม. {m}น."
        except Exception:
            pass

    if not cache:
        return "VERIFY", _D, "ยังไม่มีข้อมูลการใช้งาน"

    switches = int(cache.get("switches_today", 0))
    today = now.date().isoformat()
    if cache.get("last_used_date") != today:
        return "READY", _G, "พร้อมใช้งาน"
    if switches < SWITCH_LOW:
        return "READY", _G, f"สลับมาใช้ {switches} ครั้งวันนี้"
    if switches < SWITCH_HARD:
        return "LOW", _Y, f"สลับบ่อย ({switches} ครั้งวันนี้)"
    return "LIMITED", _R, f"สลับบ่อยมาก ({switches} ครั้งวันนี้)"


def format_badge(badge_key: str, color: str, countdown: str) -> str:
    badges = {"READY": "🟢", "LOW": "🟡", "LIMITED": "🔴", "VERIFY": "⚫"}
    emoji = badges.get(badge_key, "?")
    return f"{color}{emoji} {badge_key}{_X}  {_D}{countdown}{_X}"


def record_switch(email: str) -> None:
    """นับการสลับมาใช้บัญชีนี้ (ไม่ใช่จำนวน request ที่ agy เรียกจริง)"""
    data = {}
    try:
        if XTOOLS_CONFIG.exists():
            data = json.loads(XTOOLS_CONFIG.read_text(encoding="utf-8"))
    except Exception:
        pass
    quota = data.setdefault("agy_accounts", {}).setdefault(email, {}).setdefault("quota", {})
    today = _now_utc().date().isoformat()
    if quota.get("last_used_date") != today:
        quota["switches_today"] = 0
        quota["last_used_date"] = today
    quota["switches_today"] = int(quota.get("switches_today", 0)) + 1
    quota["last_used_time"] = _now_utc().isoformat()
    _atomic_write(XTOOLS_CONFIG, data)


def set_cooldown(email: str, hours: float = 5.0) -> None:
    data = {}
    try:
        if XTOOLS_CONFIG.exists():
            data = json.loads(XTOOLS_CONFIG.read_text(encoding="utf-8"))
    except Exception:
        pass
    cooldown_until = (_now_utc() + timedelta(hours=hours)).isoformat()
    data.setdefault("agy_accounts", {}).setdefault(email, {}).setdefault("quota", {})[
        "cooldown_until"
    ] = cooldown_until
    _atomic_write(XTOOLS_CONFIG, data)


def _in_cooldown(email: str) -> bool:
    cache = _load_quota_cache(email)
    cooldown_str = cache.get("cooldown_until", "")
    if not cooldown_str:
        return False
    try:
        return datetime.fromisoformat(cooldown_str) > _now_utc()
    except Exception:
        return False


def get_next_account(accounts: list) -> str | None:
    """เลือกบัญชีถัดไปที่ยังใช้ได้ — ข้ามบัญชีที่ติด cooldown หรือสลับบ่อยจนหมดแล้ว

    ไล่จากบัญชีที่ badge ดีที่สุด (READY/VERIFY → LOW) ไม่เลือก LIMITED
    """
    ready: list[str] = []
    low: list[str] = []
    for acc in accounts:
        if acc.is_active or _in_cooldown(acc.email):
            continue
        badge_key, _, _ = compute_badge(acc.email)
        if badge_key == "LIMITED":
            continue
        if badge_key == "LOW":
            low.append(acc.email)
        else:
            ready.append(acc.email)
    if ready:
        return ready[0]
    if low:
        return low[0]
    return None
