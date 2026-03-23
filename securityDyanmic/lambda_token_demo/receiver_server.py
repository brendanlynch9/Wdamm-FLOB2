#!/usr/bin/env python3
"""receiver_server.py
Simple receiver that decrypts tokens produced by the daemon and verifies counter/payload hash.
Run alongside lambda_daemon.py to test end-to-end.
"""
import os, json, struct, hashlib, base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

KEY_FILE = "demo_key.bin"
RECV_STATE = "receiver_state.json"

def load_key(path):
    if not os.path.exists(path):
        raise FileNotFoundError("Key file not found. Run lambda_daemon.py to create it.")
    with open(path, "rb") as f:
        return f.read()

def load_state():
    if not os.path.exists(RECV_STATE):
        state = {"last_counter": 0}
        with open(RECV_STATE, "w") as f:
            json.dump(state, f)
        return state
    with open(RECV_STATE, "r") as f:
        return json.load(f)

def save_state(s):
    tmp = RECV_STATE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(s, f)
        f.flush(); os.fsync(f.fileno())
    os.replace(tmp, RECV_STATE)

def verify_token(key, token, expected_payload: bytes):
    aesgcm = AESGCM(key)
    nonce = base64.b64decode(token['nonce'])
    ct = base64.b64decode(token['ciphertext'])
    aad = base64.b64decode(token['aad'])
    try:
        pt = aesgcm.decrypt(nonce, ct, aad)
    except Exception as e:
        return False, f"decrypt_failed: {e}"
    if len(pt) != 8+4+8:
        return False, "invalid_plaintext_length"
    counter = struct.unpack(">Q", pt[:8])[0]
    lambda_f = struct.unpack(">f", pt[8:12])[0]
    payload_hash = pt[12:20]
    # verify payload hash
    if hashlib.sha256(expected_payload).digest()[:8] != payload_hash:
        return False, "payload_hash_mismatch"
    # check counter monotonicity
    s = load_state()
    last = s.get("last_counter", 0)
    if counter <= last:
        return False, "replay_or_out_of_order"
    # all good; update state
    s['last_counter'] = counter
    save_state(s)
    return True, {"counter": counter, "lambda2": lambda_f}

def demo():
    print("Receiver ready. This demo expects the daemon to have created 'demo_key.bin'.")
    key = load_key(KEY_FILE)
    # For manual testing you can paste token JSON here. For demo, prompt:
    print("Paste token JSON (as produced by event_client) and the original payload string.")
    tok_json = input("Token JSON: ")
    payload = input("Payload string: ").encode('utf8')
    try:
        token = json.loads(tok_json)
    except Exception as e:
        print("Invalid token JSON:", e); return
    ok, info = verify_token(key, token, payload)
    print("Verification result:", ok, info)

if __name__ == '__main__':
    demo()
