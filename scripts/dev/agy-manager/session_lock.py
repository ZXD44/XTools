"""
session_lock.py — Phase 3
ระบบ Session Lock ป้องกัน Terminal หลายตัวแย่ง agy token กัน
"""

import json
import os
import sys
import time
from pathlib import Path
from agy_config import LOCKFILE

LOCK_TIMEOUT = 30  # วินาที — ถ้าไม่มีการ refresh เกินนี้ถือว่า lock หมดอายุ
HEARTBEAT_INTERVAL = 5  # วินาที


def _read_lock() -> dict:
    try:
        if LOCKFILE.exists():
            return json.loads(LOCKFILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _write_lock(data: dict) -> None:
    try:
        LOCKFILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass


def _pid_alive(pid: int) -> bool:
    """ตรวจว่า process ยังมีชีวิตอยู่ (รองรับทั้ง Windows และ POSIX โดยไม่กระทบ process)"""
    if pid <= 0:
        return False
    if os.name == "nt":
        import ctypes
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        STILL_ACTIVE = 259
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, int(pid))
        if not handle:
            return False
        try:
            exit_code = ctypes.c_ulong()
            if kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                return exit_code.value == STILL_ACTIVE
            return False
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False


def _lock_is_live(data: dict, now: float | None = None) -> bool:
    """lock ยังถือว่าถูกครอบครองอยู่ไหม (มี pid ที่ยังรัน + ยังไม่หมดอายุ)"""
    pid = data.get("pid")
    ts = data.get("timestamp")
    if not pid or not ts:
        return False
    now = time.time() if now is None else now
    if now - float(ts) >= LOCK_TIMEOUT:
        return False
    return _pid_alive(int(pid))


def acquire_lock(email: str) -> bool:
    """
    พยายาม acquire lock สำหรับ terminal นี้
    คืน True ถ้าได้ lock, False ถ้า terminal อื่นถือ lock อยู่
    """
    for _ in range(3):
        existing = _read_lock()
        if _lock_is_live(existing) and existing.get("pid") != os.getpid():
            return False  # มี terminal อื่นถืออยู่จริง

        # lock หมดอายุ / เป็นของตัวเอง / ไม่มี → ล้างแล้วสร้างแบบ exclusive
        try:
            LOCKFILE.unlink(missing_ok=True)
        except Exception:
            pass

        try:
            fd = os.open(str(LOCKFILE), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            # แข่งกันเขียน — มีคนชนะไปแล้ว วนตรวจใหม่
            time.sleep(0.1)
            continue
        except OSError:
            return False

        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump({"pid": os.getpid(), "email": email, "timestamp": time.time()}, fh, indent=2)
        return True

    return False


def release_lock() -> None:
    """ปล่อย lock เมื่อเสร็จงาน — เฉพาะเมื่อ lock เป็นของ process นี้"""
    data = _read_lock()
    if data.get("pid") and data.get("pid") != os.getpid():
        return  # lock ของ terminal อื่น ห้ามลบ
    try:
        LOCKFILE.unlink(missing_ok=True)
    except Exception:
        pass


def heartbeat_lock(email: str) -> bool:
    """อัปเดต timestamp ใน lockfile — คืน False ถ้าไม่ได้ถือ lock นี้แล้วหรือถูกปลดไปแล้ว"""
    data = _read_lock()
    if not data or data.get("pid") != os.getpid():
        return False
    _write_lock({
        "pid": os.getpid(),
        "email": email,
        "timestamp": time.time(),
    })
    return True


def get_lock_owner() -> str | None:
    """ดูว่า terminal ไหนถือ lock อยู่"""
    data = _read_lock()
    if _lock_is_live(data):
        return data.get("email")
    return None
