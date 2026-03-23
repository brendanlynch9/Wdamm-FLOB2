#!/usr/bin/env python3
"""
secure_precheck.py

A self-contained demonstration of a secure, low-latency payload authentication
pre-check suitable for constrained environments.

Features:
- HMAC-SHA256 truncated tag (configurable tag length)
- Counter semantics: time-step or monotonic (configurable)
- Persistent state file for last_accepted_counter (atomic writes)
- Key manager: create/load key with versioning; rotate safely
- Replay protection, inclusive window semantics
- Simple rate-limiter with exponential backoff on repeated failures
- Demo flow showing accept, replay reject, and out-of-window reject

Usage:
    python secure_precheck.py
"""

import os
import hmac
import hashlib
import struct
import time
import json
import secrets
import threading
from typing import Tuple

# -------------------------
# Configuration parameters
# -------------------------
KEY_DIR = "./keystore"                 # directory for keys
KEY_FILE = os.path.join(KEY_DIR, "key_v1.json")
STATE_DIR = "./state"
STATE_FILE = os.path.join(STATE_DIR, "device_state.json")
LOG_FILE = "./secure_precheck.log"

DEFAULT_TAG_LEN = 8                    # bytes (64 bits). Use >=8; 12-16 is safer.
TIME_STEP_SECONDS = 5                  # resolution for time-step counter mode
WINDOW = 1                             # allowed inclusive window: [last+1, last+WINDOW]
RATE_LIMIT_MAX_FAILS = 5               # failures before backoff
RATE_LIMIT_BASE_BACKOFF = 2.0          # seconds (exponential base)
KEY_BYTES = 32                         # key length in bytes

# -------------------------
# Utilities: logging
# -------------------------
def log(msg: str) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    line = f"{ts} | {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        # Do not crash on logging failure
        pass

# -------------------------
# Key management (simple)
# -------------------------
class KeyManager:
    """
    Simple key manager storing key material in a JSON file.
    In production use a secure element / HSM instead.
    """
    def __init__(self, key_file: str, key_bytes: int = KEY_BYTES):
        self.key_file = key_file
        self.key_bytes = key_bytes
        os.makedirs(os.path.dirname(self.key_file), exist_ok=True)

    def generate_key(self, version: int = 1) -> dict:
        key = secrets.token_bytes(self.key_bytes)
        meta = {
            "version": version,
            "key": key.hex(),
            "created": int(time.time())
        }
        self._atomic_write_json(self.key_file, meta)
        log(f"Generated new key version {version} and stored in {self.key_file}")
        return meta

    def load_key(self) -> dict:
        if not os.path.exists(self.key_file):
            return self.generate_key(version=1)
        with open(self.key_file, "r", encoding="utf-8") as f:
            meta = json.load(f)
        # convert hex string to bytes for runtime use
        meta["key_bytes"] = bytes.fromhex(meta["key"])
        return meta

    def rotate_key(self, new_version: int = None) -> dict:
        meta = self.load_key()
        if new_version is None:
            new_version = meta.get("version", 1) + 1
        return self.generate_key(version=new_version)

    @staticmethod
    def _atomic_write_json(path: str, obj: dict) -> None:
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(obj, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)

# -------------------------
# Persistent state manager
# -------------------------
class StateManager:
    """
    Persists last_accepted_counter and rate-limiter state atomically in JSON.
    """
    def __init__(self, state_file: str):
        self.state_file = state_file
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        # initialize if missing
        if not os.path.exists(self.state_file):
            self._write_state({
                "last_accepted_counter": 0,
                "fail_count": 0,
                "backoff_until": 0.0
            })

    def read_state(self) -> dict:
        with open(self.state_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_state(self, state: dict) -> None:
        tmp = self.state_file + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, self.state_file)

    def get_last_counter(self) -> int:
        return int(self.read_state().get("last_accepted_counter", 0))

    def update_last_counter(self, new_counter: int) -> None:
        s = self.read_state()
        s["last_accepted_counter"] = int(new_counter)
        # reset fail counters on success
        s["fail_count"] = 0
        s["backoff_until"] = 0.0
        self._write_state(s)
        log(f"Persisted last_accepted_counter = {new_counter}")

    def record_failure(self) -> None:
        s = self.read_state()
        s["fail_count"] = int(s.get("fail_count", 0)) + 1
        # exponential backoff
        exponent = max(0, s["fail_count"] - RATE_LIMIT_MAX_FAILS + 1)
        backoff = (RATE_LIMIT_BASE_BACKOFF ** exponent) if exponent > 0 else 0.0
        s["backoff_until"] = time.time() + backoff if backoff > 0 else 0.0
        self._write_state(s)
        log(f"Recorded failure #{s['fail_count']}; backoff_until={s['backoff_until']}")

    def is_rate_limited(self) -> Tuple[bool, float]:
        s = self.read_state()
        now = time.time()
        until = float(s.get("backoff_until", 0.0))
        if now < until:
            return True, until - now
        return False, 0.0

# -------------------------
# Core tag functions
# -------------------------
def make_tag(key: bytes, payload: bytes, counter: int, tag_len: int = DEFAULT_TAG_LEN) -> bytes:
    """
    Compute HMAC-SHA256 over payload || 8-byte big-endian counter then truncate.
    """
    counter_bytes = struct.pack(">Q", counter)
    mac = hmac.new(key, payload + counter_bytes, hashlib.sha256).digest()
    return mac[:tag_len]

def verify_tag(key: bytes,
               payload: bytes,
               counter: int,
               tag: bytes,
               state_mgr: StateManager,
               window: int = WINDOW,
               tag_len: int = DEFAULT_TAG_LEN) -> Tuple[bool, int, str]:
    """
    Verify the received tag.

    Returns (accepted: bool, new_last_counter: int, reason: str)

    Semantics:
      - Accept counters in inclusive range [last_accepted_counter + 1, last_accepted_counter + window]
      - On success update last_accepted_counter to counter (via state_mgr.update_last_counter)
      - On failure record failure for rate-limiting
    """
    # Rate-limit check
    limited, secs = state_mgr.is_rate_limited()
    if limited:
        return False, state_mgr.get_last_counter(), f"rate_limited ({secs:.1f}s remaining)"

    last = state_mgr.get_last_counter()
    min_allowed = last + 1
    max_allowed = last + window

    # Range check
    if not (min_allowed <= counter <= max_allowed):
        # out-of-window or replay
        state_mgr.record_failure()
        return False, last, f"counter_out_of_window (allowed [{min_allowed},{max_allowed}], got {counter})"

    # Verify tag for that received counter (efficient)
    expected = make_tag(key, payload, counter, tag_len=tag_len)
    if hmac.compare_digest(expected, tag):
        # Accept & persist state
        state_mgr.update_last_counter(counter)
        return True, counter, "accepted"
    else:
        state_mgr.record_failure()
        return False, last, "tag_mismatch"

# -------------------------
# Demo: sender + receiver
# -------------------------
def current_time_counter(step_seconds: int = TIME_STEP_SECONDS) -> int:
    """Time-step counter based on epoch divided by step_seconds."""
    return int(time.time() // step_seconds)

def demo_flow():
    log("=== Demo start ===")
    # Setup managers
    km = KeyManager(KEY_FILE)
    keymeta = km.load_key()
    key_bytes = keymeta.get("key_bytes") if "key_bytes" in keymeta else bytes.fromhex(keymeta["key"])

    state_mgr = StateManager(STATE_FILE)

    log(f"Loaded key version {keymeta.get('version')} (key file: {KEY_FILE})")
    log(f"Initial last_accepted_counter = {state_mgr.get_last_counter()}")

    # Sender: craft payload and tag
    payload = b"PLC_CMD:SET VAL=42"
    # choose counter mode: time-step
    counter = current_time_counter()
    tag = make_tag(key_bytes, payload, counter, tag_len=DEFAULT_TAG_LEN)
    log(f"Sender created counter={counter} tag_len={DEFAULT_TAG_LEN}")

    # Receiver: attempt to verify (expected success)
    accepted, new_last, reason = verify_tag(key_bytes, payload, counter, tag, state_mgr, window=WINDOW, tag_len=DEFAULT_TAG_LEN)
    log(f"Verify attempt 1 -> accepted={accepted}, reason={reason}, new_last={new_last}")

    # Replay attempt: same payload & tag (should be rejected as replay)
    accepted2, new_last2, reason2 = verify_tag(key_bytes, payload, counter, tag, state_mgr, window=WINDOW, tag_len=DEFAULT_TAG_LEN)
    log(f"Replay attempt -> accepted={accepted2}, reason={reason2}, last={new_last2}")

    # Out-of-window attempt: use an old counter (too old)
    old_counter = counter - 10
    old_tag = make_tag(key_bytes, payload, old_counter, tag_len=DEFAULT_TAG_LEN)
    accepted3, new_last3, reason3 = verify_tag(key_bytes, payload, old_counter, old_tag, state_mgr, window=WINDOW, tag_len=DEFAULT_TAG_LEN)
    log(f"Old-counter attempt -> accepted={accepted3}, reason={reason3}, last={new_last3}")

    # Tampered tag attempt: same counter but different payload or modified tag
    tampered_payload = b"PLC_CMD:SET VAL=99"
    tampered_tag = make_tag(key_bytes, tampered_payload, counter, tag_len=DEFAULT_TAG_LEN)  # tag matches tampered payload
    # But we send tampered_payload with original tag (mismatch)
    accepted4, new_last4, reason4 = verify_tag(key_bytes, tampered_payload, counter, tag, state_mgr, window=WINDOW, tag_len=DEFAULT_TAG_LEN)
    log(f"Tampered attempt -> accepted={accepted4}, reason={reason4}, last={new_last4}")

    # Demonstrate rate-limiting: rapidly cause failures
    log("Generating rapid failures to trigger rate limiting (may back off)...")
    for i in range(RATE_LIMIT_MAX_FAILS + 2):
        bad_tag = secrets.token_bytes(DEFAULT_TAG_LEN)
        acc, nl, r = verify_tag(key_bytes, payload, counter + 999 + i, bad_tag, state_mgr, window=WINDOW, tag_len=DEFAULT_TAG_LEN)
        log(f"Rapid failure #{i+1}: accepted={acc}, reason={r}")

    log("=== Demo end ===")

# -------------------------
# Main
# -------------------------
if __name__ == "__main__":
    # Ensure directories exist
    os.makedirs(KEY_DIR, exist_ok=True)
    os.makedirs(STATE_DIR, exist_ok=True)

    demo_flow()
