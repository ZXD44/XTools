"""
crypto.py — Phase 6
Encrypted backup: AES-256-GCM + PBKDF2-SHA256 และ SHA-256 integrity check

หมายเหตุความปลอดภัย:
- ไม่มี fallback แบบ XOR แล้ว ถ้าไม่มีแพ็กเกจ cryptography จะ raise ทันที
  (เพราะ XOR บนไฟล์ที่มี credential = obfuscation ไม่ใช่การเข้ารหัส)
- ตรวจ SHA-256 ช่วยจับไฟล์เสียหาย/ถูกแก้โดยอุบัติเหตุ ไม่ได้กันคนที่แก้ทั้ง .enc และ .sha256
- ไฟล์ backup ถูกตั้งสิทธิ์ 0600 บน POSIX
"""

import hashlib
import json
import os
import struct
from pathlib import Path

try:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    _CRYPTO_ERR: Exception | None = None
except ImportError as exc:  # pragma: no cover - ขึ้นกับสภาพเครื่อง
    AESGCM = None  # type: ignore[assignment]
    _CRYPTO_ERR = exc

BACKUP_FILE = Path.home() / ".xtools_agy_backup.enc"

MAGIC = b"XTBK1"
SALT_LEN = 32
NONCE_LEN = 12
MAX_SALT_LEN = 1024
PBKDF2_ITERATIONS = 200_000


def _require_crypto() -> None:
    if _CRYPTO_ERR is not None:
        raise RuntimeError(
            "ต้องติดตั้งแพ็กเกจ 'cryptography' ก่อนใช้ Backup: pip install cryptography "
            f"(ปิด fallback XOR เพื่อความปลอดภัย: {_CRYPTO_ERR})"
        )


def _derive_key(password: str, salt: bytes) -> bytes:
    _require_crypto()
    assert AESGCM is not None
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return kdf.derive(password.encode("utf-8"))


def _write_private(path: Path, data: bytes) -> None:
    """เขียนไฟล์และจำกัดสิทธิ์ให้เจ้าของเท่านั้น (POSIX)"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    if os.name != "nt":
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def encrypt_backup(data: dict, password: str) -> None:
    _require_crypto()
    if not password:
        raise ValueError("รหัสผ่านต้องไม่ว่าง")

    salt = os.urandom(SALT_LEN)
    nonce = os.urandom(NONCE_LEN)
    key = _derive_key(password, salt)
    plaintext = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, MAGIC)  # type: ignore[union-attr]

    blob = MAGIC + struct.pack(">I", SALT_LEN) + salt + nonce + ciphertext
    _write_private(BACKUP_FILE, blob)

    sidecar = BACKUP_FILE.with_suffix(".sha256")
    _write_private(sidecar, sha256_file(BACKUP_FILE).encode("utf-8"))


def decrypt_backup(password: str) -> dict:
    _require_crypto()
    if not BACKUP_FILE.exists():
        raise FileNotFoundError("ไม่พบไฟล์ backup")

    sha_file = BACKUP_FILE.with_suffix(".sha256")
    if sha_file.exists():
        expected = sha_file.read_text(encoding="utf-8").strip()
        if expected != sha256_file(BACKUP_FILE):
            raise ValueError("SHA-256 ไม่ตรง — ไฟล์ backup เสียหายหรือถูกแก้ไข")

    raw = BACKUP_FILE.read_bytes()
    if not raw.startswith(MAGIC):
        raise ValueError("ไฟล์ backup ไม่ถูกต้อง (header ไม่ใช่ XTBK1)")
    offset = len(MAGIC)
    if len(raw) < offset + 4:
        raise ValueError("ไฟล์ backup สั้นเกินไป")
    salt_len = struct.unpack(">I", raw[offset:offset + 4])[0]
    offset += 4
    if not 1 <= salt_len <= MAX_SALT_LEN:
        raise ValueError("ขนาด salt ในไฟล์ backup ไม่ถูกต้อง")
    if len(raw) < offset + salt_len + NONCE_LEN:
        raise ValueError("ไฟล์ backup สั้นเกินไป")

    salt = raw[offset:offset + salt_len]
    offset += salt_len
    nonce = raw[offset:offset + NONCE_LEN]
    offset += NONCE_LEN
    ciphertext = raw[offset:]

    key = _derive_key(password, salt)
    plaintext = AESGCM(key).decrypt(nonce, ciphertext, MAGIC)  # type: ignore[union-attr]
    return json.loads(plaintext.decode("utf-8"))


ZIP_BACKUP_FILE = Path.home() / ".xtools_agy_bundle.zip.enc"
ZIP_MAGIC = b"XTZP1"


def export_encrypted_zip(
    files: list[Path],
    password: str,
    out_path: Path | None = None,
) -> Path:
    """Phase 6.3: รวมไฟล์และโฟลเดอร์เป็น .zip แล้วเข้ารหัส AES-256-GCM (XTZP1) พร้อม .sha256"""
    import io
    import zipfile

    _require_crypto()
    if not password:
        raise ValueError("รหัสผ่านต้องไม่ว่าง")

    buf = io.BytesIO()
    added = 0
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for item in files:
            p = Path(item)
            if not p.exists():
                continue
            if p.is_file():
                zf.write(p, arcname=p.name)
                added += 1
            elif p.is_dir():
                for child in p.rglob("*"):
                    if child.is_file():
                        arc = Path(p.name) / child.relative_to(p)
                        zf.write(child, arcname=str(arc))
                        added += 1

    if added == 0:
        raise FileNotFoundError("ไม่พบไฟล์หรือโฟลเดอร์สำหรับสร้างชุดสำรอง")

    salt = os.urandom(SALT_LEN)
    nonce = os.urandom(NONCE_LEN)
    key = _derive_key(password, salt)
    ciphertext = AESGCM(key).encrypt(nonce, buf.getvalue(), ZIP_MAGIC)  # type: ignore[union-attr]

    dest = Path(out_path) if out_path else ZIP_BACKUP_FILE
    blob = ZIP_MAGIC + struct.pack(">I", SALT_LEN) + salt + nonce + ciphertext
    _write_private(dest, blob)

    sidecar = dest.with_suffix(".sha256")
    _write_private(sidecar, sha256_file(dest).encode("utf-8"))
    return dest
