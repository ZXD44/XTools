"""
agy_config.py — Phase 1 & 4
อ่านและเขียน config ไฟล์ agy ทุกชนิดที่ ~/.gemini/
รองรับ: google_accounts.json, settings.json, agycord.json, clicord.json, zircord.json
"""

import json
import os
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

AGY_DIR = Path.home() / ".gemini"
ACCOUNTS_FILE = AGY_DIR / "google_accounts.json"
SETTINGS_FILE = AGY_DIR / "settings.json"
AGYCORD_FILE = AGY_DIR / "agycord.json"
CLICORD_FILE = AGY_DIR / "clicord.json"
ZIRCORD_FILE = AGY_DIR / "zircord.json"
PROXY_TOKEN_FILE = AGY_DIR / "antigravity-proxy-token.json"
XTOOLS_CONFIG = Path.home() / ".xtools_config.json"
LOCKFILE = Path.home() / ".xtools_agy.lock"

# snapshot ของ state/settings แยกตามบัญชี (ใช้ตอนสลับบัญชีจริง)
PROFILE_DIR = AGY_DIR / "xtools_profiles"
PROFILE_FILES = ("settings.json", "state.json")


@dataclass
class AgyAccount:
    """ข้อมูลบัญชี agy หนึ่งรายการ"""
    email: str
    is_active: bool = False
    # ฟิลด์ขยายสำหรับ quota (Phase 2)
    quota_data: dict = field(default_factory=dict)
    last_used: str = ""
    cooldown_until: str = ""
    bindings: list[str] = field(default_factory=list)


def _atomic_write(path: Path, data: dict) -> None:
    """เขียน JSON แบบ atomic เพื่อป้องกัน config corruption"""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
        shutil.move(str(tmp), str(path))
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


def _profile_dir(email: str) -> Path:
    """แปลง email เป็นชื่อโฟลเดอร์ที่ปลอดภัย (กัน path traversal)"""
    safe = email.replace("/", "_").replace("\\", "_").replace(":", "_").strip(". ")
    if not safe or safe in {".", ".."}:
        raise ValueError(f"email ไม่ถูกต้องสำหรับใช้เป็นชื่อโฟลเดอร์: {email!r}")
    return PROFILE_DIR / safe


def snapshot_profile(email: str) -> bool:
    """เก็บ settings.json/state.json ของบัญชีนี้ไว้ก่อนสลับออก"""
    try:
        dest = _profile_dir(email)
        dest.mkdir(parents=True, exist_ok=True)
        saved = False
        for name in PROFILE_FILES:
            src = AGY_DIR / name
            if src.is_file():
                (dest / name).write_bytes(src.read_bytes())
                saved = True
        return saved
    except Exception:
        return False


def restore_profile(email: str) -> bool:
    """คืน settings.json/state.json ของบัญชีนี้กลับไปที่ ~/.gemini (ถ้าเคยเก็บไว้)"""
    try:
        src_dir = _profile_dir(email)
        if not src_dir.is_dir():
            return False
        restored = False
        for name in PROFILE_FILES:
            src = src_dir / name
            if src.is_file():
                (AGY_DIR / name).write_bytes(src.read_bytes())
                restored = True
        return restored
    except Exception:
        return False


def load_accounts() -> list[AgyAccount]:
    """โหลดรายชื่อบัญชีทั้งหมดจาก google_accounts.json + xtools meta"""
    accounts: list[AgyAccount] = []

    # โหลดจาก agy native config
    raw_active = None
    old_emails: list[str] = []
    if ACCOUNTS_FILE.exists():
        try:
            data = json.loads(ACCOUNTS_FILE.read_text(encoding="utf-8"))
            raw_active = data.get("active")
            old_emails = data.get("old", [])
        except Exception:
            pass

    # รวมรายชื่อ: active + old (ไม่ซ้ำ)
    all_emails: list[str] = []
    if raw_active and raw_active not in all_emails:
        all_emails.append(raw_active)
    for e in old_emails:
        if e and e not in all_emails:
            all_emails.append(e)

    # โหลด meta จาก xtools config (last_used, cooldown, bindings)
    xtools_meta: dict = {}
    if XTOOLS_CONFIG.exists():
        try:
            xtools_meta = json.loads(XTOOLS_CONFIG.read_text(encoding="utf-8")).get("agy_accounts", {})
        except Exception:
            pass

    for email in all_emails:
        meta = xtools_meta.get(email, {})
        quota_meta = meta.get("quota", {}) or {}
        accounts.append(AgyAccount(
            email=email,
            is_active=(email == raw_active),
            last_used=str(meta.get("last_used", "")),
            # cooldown ถูกเขียนไว้ที่ meta["quota"]["cooldown_until"] (ดู quota.set_cooldown)
            cooldown_until=quota_meta.get("cooldown_until", ""),
            bindings=list(meta.get("bindings", [])),
        ))

    return accounts


def switch_account(email: str, accounts: list[AgyAccount]) -> bool:
    """สลับบัญชี active — เก็บ snapshot บัญชีเดิม แล้วคืน state ของบัญชีใหม่

    ขั้นตอน:
      1. snapshot settings.json/state.json ของบัญชีที่ใช้อยู่ -> ~/.gemini/xtools_profiles/<email>/
      2. เขียน google_accounts.json (atomic) ให้ active = บัญชีใหม่
      3. restore settings.json/state.json ของบัญชีใหม่ (ถ้าเคยเก็บไว้)
    """
    if email not in [a.email for a in accounts]:
        return False

    if not ACCOUNTS_FILE.exists():
        return False

    try:
        data = json.loads(ACCOUNTS_FILE.read_text(encoding="utf-8"))
        prev = data.get("active")
        if prev and prev != email:
            snapshot_profile(prev)
        # ย้ายบัญชีเดิมออกไปที่ old ถ้ายังไม่มี
        if prev and prev != email and prev not in data.get("old", []):
            data.setdefault("old", []).append(prev)
        # ถอด email ใหม่จาก old list (ถ้ามี)
        data["old"] = [e for e in data.get("old", []) if e != email]
        data["active"] = email
        _atomic_write(ACCOUNTS_FILE, data)
        restore_profile(email)
        _update_xtools_meta(email)
        return True
    except Exception:
        return False


def _update_xtools_meta(email: str) -> None:
    """บันทึกเวลาล่าสุดที่ใช้บัญชีนี้"""
    from datetime import datetime, timezone
    data = {}
    if XTOOLS_CONFIG.exists():
        try:
            data = json.loads(XTOOLS_CONFIG.read_text(encoding="utf-8"))
        except Exception:
            pass
    accs = data.setdefault("agy_accounts", {})
    accs.setdefault(email, {})["last_used"] = datetime.now(timezone.utc).isoformat()
    _atomic_write(XTOOLS_CONFIG, data)


def get_active_account() -> str | None:
    """ดึงบัญชีที่ active อยู่ตอนนี้"""
    if not ACCOUNTS_FILE.exists():
        return None
    try:
        data = json.loads(ACCOUNTS_FILE.read_text(encoding="utf-8"))
        return data.get("active")
    except Exception:
        return None


def add_binding(email: str, project_path: str) -> None:
    """Phase 4: ผูกบัญชีกับ project path"""
    data = {}
    if XTOOLS_CONFIG.exists():
        try:
            data = json.loads(XTOOLS_CONFIG.read_text(encoding="utf-8"))
        except Exception:
            pass
    accs = data.setdefault("agy_accounts", {})
    binds = accs.setdefault(email, {}).setdefault("bindings", [])
    abs_path = str(Path(project_path).resolve())
    if abs_path not in binds:
        binds.append(abs_path)
    _atomic_write(XTOOLS_CONFIG, data)


def remove_binding(email: str, project_path: str) -> None:
    """ลบ binding ระหว่างบัญชีกับ path"""
    data = {}
    if XTOOLS_CONFIG.exists():
        try:
            data = json.loads(XTOOLS_CONFIG.read_text(encoding="utf-8"))
        except Exception:
            pass
    abs_path = str(Path(project_path).resolve())
    binds = data.get("agy_accounts", {}).get(email, {}).get("bindings", [])
    if abs_path in binds:
        binds.remove(abs_path)
        _atomic_write(XTOOLS_CONFIG, data)


def detect_binding(cwd: str | None = None) -> str | None:
    """Phase 4: ตรวจจับบัญชีที่ bind กับ path ปัจจุบัน

    exact match ชนะเสมอ ถ้าไม่มีให้ใช้ binding ที่ path ลึกที่สุด (ใกล้ที่สุด)
    """
    check = Path(cwd).resolve() if cwd else Path.cwd().resolve()
    if not XTOOLS_CONFIG.exists():
        return None
    best: tuple[int, str] | None = None
    try:
        data = json.loads(XTOOLS_CONFIG.read_text(encoding="utf-8"))
        for email, meta in data.get("agy_accounts", {}).items():
            for b in meta.get("bindings", []):
                try:
                    bound = Path(b).resolve()
                except Exception:
                    continue
                if check == bound:
                    return email
                try:
                    if check.is_relative_to(bound):
                        depth = len(bound.parts)
                        if best is None or depth > best[0]:
                            best = (depth, email)
                except Exception:
                    pass
    except Exception:
        pass
    return best[1] if best else None
