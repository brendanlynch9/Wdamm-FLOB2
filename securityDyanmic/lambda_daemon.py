#!/usr/bin/env python3
"""lambda_daemon.py
# WARNING: Proof-of-Concept Only

This software and documentation demonstrate the Complex-Gated Authentication (CGA) protocol. 

DO NOT USE IN PRODUCTION. All keys and code are for academic/testing purposes. 

Use at your own risk. No liability is assumed by the author.

Local daemon computing lambda2 and issuing AES-GCM tokens.

"""
import os
import json
import time
import struct
import socket
import threading
import math
import hashlib
from typing import Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import base64

# Local demo key/state files (placed in working dir)
KEY_FILE = "demo_key.bin"
STATE_FILE = "daemon_state.json"
HOST = "127.0.0.1"
PORT = 23456

# lambda2 mapping buckets (simple demo)
LAMBDA2_LOOKUP = {0:0.100,1:0.332,2:0.591,3:0.050,4:0.420,5:0.650}

def load_or_create_key(path: str) -> bytes:
    if os.path.exists(path):
        with open(path, "rb") as f:
            k = f.read()
            if len(k) not in (16,24,32):
                raise ValueError("Invalid key length in key file.")
            return k
    else:
        k = AESGCM.generate_key(bit_length=256)
        with open(path, "wb") as f:
            f.write(k)
        try:
            os.chmod(path, 0o600)
        except Exception:
            pass
        return k

def load_state(path: str):
    if not os.path.exists(path):
        state = {"counter": 0, "fail_count": 0, "backoff_until": 0.0}
        with open(path, "w") as f:
            json.dump(state, f)
        return state
    with open(path, "r") as f:
        return json.load(f)

def save_state(path: str, state):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f)
        f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)

def calculate_lambda2(payload: bytes) -> float:
    """
    O(1)-ish: compute floor(||x||_2) % 24 and map via a small mapping.
    """
    if not payload:
        return 0.0
    l2_sq = sum((b * b) for b in payload)
    l2_norm = math.sqrt(l2_sq)
    n_mod_24 = math.floor(l2_norm) % 24
    return LAMBDA2_LOOKUP[n_mod_24 % 6]

def make_token_aesgcm(aes_key: bytes, payload: bytes, lambda2: float, counter: int) -> dict:
    """
    Build a compact encrypted token: counter || lambda2 || payload_hash
    """
    aesgcm = AESGCM(aes_key)
    nonce = os.urandom(12)
    counter_bytes = struct.pack(">Q", counter)
    lambda_bytes = struct.pack(">f", float(lambda2))
    payload_hash = hashlib.sha256(payload).digest()[:8] # 8-byte truncated hash

    # Authenticated plaintext: counter || lambda || payload_hash
    plaintext = counter_bytes + lambda_bytes + payload_hash

    aad = b"lambda-daemon-v1" # Additional Authenticated Data (fixed)

    ct = aesgcm.encrypt(nonce, plaintext, aad)
    token = {
        "nonce": base64.b64encode(nonce).decode("ascii"),
        "ciphertext": base64.b64encode(ct).decode("ascii"),
        "aad": base64.b64encode(aad).decode("ascii"),
        "counter": counter,
    }
    return token

def handle_request(data_json: dict, key: bytes, state_path: str) -> dict:
    state = load_state(state_path)
    now = time.time()
    if now < state.get("backoff_until", 0.0):
        return {"ok": False, "reason": "rate_limited"}

    payload_b64 = data_json.get("payload_b64", "")
    try:
        payload = base64.b64decode(payload_b64)
    except Exception:
        return {"ok": False, "reason": "bad_payload_encoding"}

    # Stage 1: O(1) lambda2 check (Fast Filter)
    lambda2 = calculate_lambda2(payload)
    LMIN, LMAX = 0.30, 0.60
    if not (LMIN <= lambda2 <= LMAX):
        state["fail_count"] = state.get("fail_count", 0) + 1
        if state["fail_count"] >= 5:
            state["backoff_until"] = time.time() + 2.0
        save_state(state_path, state)
        return {"ok": False, "reason": "lambda2_out_of_range", "lambda2": lambda2}

    # Stage 2: produce encrypted token (Crypto Gate)
    state["counter"] = int(state.get("counter", 0)) + 1
    token = make_token_aesgcm(key, payload, lambda2, state["counter"])
    state["fail_count"] = 0
    state["backoff_until"] = 0.0
    save_state(state_path, state)
    return {"ok": True, "reason": "accepted", "token": token, "lambda2": lambda2}

def client_thread(conn, addr, key, state_path):
    try:
        with conn:
            raw = b""
            while True:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                raw += chunk
            try:
                req = json.loads(raw.decode("utf8"))
            except Exception:
                resp = {"ok": False, "reason": "invalid_json"}
                conn.sendall(json.dumps(resp).encode("utf8"))
                return
            resp = handle_request(req, key, state_path)
            conn.sendall(json.dumps(resp).encode("utf8"))
    except Exception as e:
        print("client error:", e)

def main():
    key = load_or_create_key(KEY_FILE)
    print(f"Lambda daemon listening on {HOST}:{PORT} (keyfile: {KEY_FILE})")
    load_state(STATE_FILE)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(5)
        while True:
            conn, addr = s.accept()
            t = threading.Thread(target=client_thread, args=(conn, addr, key, STATE_FILE), daemon=True)
            t.start()

if __name__ == "__main__":
    main()