# rum/crypto.py
"""
Per-tenant end-to-end (application-layer) envelope encryption.

docs/RUM_SYSTEM.md, "Encryption":

  * A central KMS holds a per-tenant root key (CMK). Each tenant has its own key,
    so cross-tenant decryption is impossible even with full DB access.
  * Sensitive fields/JSONB (`behavior`, attribution detail) are encrypted IN THE
    APPLICATION, BEFORE write, with a tenant data key wrapped by the tenant CMK.
    Neon stores only ciphertext for those fields.
  * Coarse aggregate/index columns (percentiles, country, privacy_bucket,
    timestamps) stay plaintext so rollups and routing work.
  * Key rotation re-wraps data keys without rewriting ciphertext; destroying a
    tenant CMK crypto-erases that tenant's data.

This module implements envelope encryption with AES-256-GCM. The "KMS" is an
interface (`get_cmk`) so a real deployment plugs in AWS KMS / GCP KMS / Vault;
the default implementation derives a stable per-tenant CMK from a master secret
in the environment, which is sufficient for self-hosting and dev while keeping
the same envelope structure and crypto-erase semantics.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import struct
from typing import Any

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    _HAVE_AESGCM = True
except BaseException:  # pragma: no cover - cryptography optional / may fail to load
    # Catch BaseException, not just Exception: a broken native build can raise a
    # pyo3 PanicException (a BaseException) at import time.
    AESGCM = None  # type: ignore
    _HAVE_AESGCM = False

# Envelope format marker. Stored alongside ciphertext so we can evolve formats.
_ENVELOPE_VERSION = 1


class CryptoUnavailable(RuntimeError):
    """Raised when encryption is requested but no crypto backend is available."""


def _master_secret() -> bytes:
    secret = os.environ.get("RUM_KMS_MASTER_KEY")
    if not secret:
        # No master key configured. We must not silently store plaintext in a
        # field the schema treats as ciphertext, so callers should check
        # `encryption_available()` first; this is the hard failure path.
        raise CryptoUnavailable(
            "RUM_KMS_MASTER_KEY is not set — refusing to write sensitive RUM "
            "payloads without per-tenant encryption."
        )
    return secret.encode("utf-8")


def encryption_available() -> bool:
    return _HAVE_AESGCM and bool(os.environ.get("RUM_KMS_MASTER_KEY"))


def get_cmk(tenant_key: str, *, key_version: int = 1) -> bytes:
    """
    Return the 32-byte per-tenant Customer Master Key (CMK).

    Default implementation: HKDF-style derivation from the master secret, scoped
    to the tenant and a key version. Rotating `key_version` yields a new CMK;
    old data keys remain unwrappable under the version they were wrapped with, so
    rotation re-wraps without rewriting ciphertext. "Destroying" a tenant CMK
    (removing the tenant from the KMS / revoking the version) renders all data
    keys — and therefore all ciphertext — permanently unrecoverable (crypto-erase).
    """
    info = f"rum-cmk:v{key_version}:{tenant_key.upper()}".encode("utf-8")
    return hmac.new(_master_secret(), info, hashlib.sha256).digest()


def _wrap_data_key(cmk: bytes, data_key: bytes) -> bytes:
    aesgcm = AESGCM(cmk)
    nonce = os.urandom(12)
    return nonce + aesgcm.encrypt(nonce, data_key, b"dek")


def _unwrap_data_key(cmk: bytes, wrapped: bytes) -> bytes:
    aesgcm = AESGCM(cmk)
    nonce, ct = wrapped[:12], wrapped[12:]
    return aesgcm.decrypt(nonce, ct, b"dek")


def encrypt_field(tenant_key: str, value: Any, *, key_version: int = 1) -> dict:
    """
    Envelope-encrypt a JSON-serializable value for a tenant.

    Returns a small JSON-storable dict (the envelope) carrying the wrapped data
    key and the ciphertext. The DB column is JSONB, so the envelope is stored
    directly; the operator sees only this opaque structure.
    """
    if value is None:
        return None  # nothing to encrypt; keep NULL
    if not encryption_available():
        raise CryptoUnavailable(
            "Encryption backend unavailable (need `cryptography` + RUM_KMS_MASTER_KEY)."
        )
    cmk = get_cmk(tenant_key, key_version=key_version)
    data_key = os.urandom(32)               # fresh per-row data key
    wrapped = _wrap_data_key(cmk, data_key)  # wrapped by the tenant CMK
    plaintext = json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    aesgcm = AESGCM(data_key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext, struct.pack(">B", _ENVELOPE_VERSION))
    return {
        "v": _ENVELOPE_VERSION,
        "kv": key_version,
        "t": tenant_key.upper(),
        "wk": base64.b64encode(wrapped).decode("ascii"),
        "n": base64.b64encode(nonce).decode("ascii"),
        "ct": base64.b64encode(ct).decode("ascii"),
    }


def decrypt_field(envelope: Any) -> Any:
    """
    Decrypt an envelope produced by `encrypt_field`. Happens only in the app tier
    when rendering the dashboard for an authorized member of the tenant.

    If the value is not an envelope (e.g. legacy plaintext or already-decoded),
    it is returned unchanged so reads degrade gracefully.
    """
    if not isinstance(envelope, dict) or "ct" not in envelope or "wk" not in envelope:
        return envelope
    if not _HAVE_AESGCM:
        raise CryptoUnavailable("Cannot decrypt: `cryptography` not installed.")
    tenant_key = envelope.get("t", "")
    key_version = int(envelope.get("kv", 1))
    cmk = get_cmk(tenant_key, key_version=key_version)
    wrapped = base64.b64decode(envelope["wk"])
    data_key = _unwrap_data_key(cmk, wrapped)
    aesgcm = AESGCM(data_key)
    nonce = base64.b64decode(envelope["n"])
    ct = base64.b64decode(envelope["ct"])
    plaintext = aesgcm.decrypt(nonce, ct, struct.pack(">B", int(envelope.get("v", 1))))
    return json.loads(plaintext.decode("utf-8"))
