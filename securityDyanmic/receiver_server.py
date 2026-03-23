#!/usr/bin/env python3
"""receiver_server.py
# WARNING: Proof-of-Concept Only

This software and documentation demonstrate the Complex-Gated Authentication (CGA) protocol. 

DO NOT USE IN PRODUCTION. All keys and code are for academic/testing purposes. 

Use at your own risk. No liability is assumed by the author.

Simple receiver that decrypts tokens produced by the daemon and verifies counter/payload hash.
Run alongside lambda_daemon.py to test end-to-end.
"""
import os, json, struct, hashlib, base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

KEY_FILE = "demo_key.bin"
RECV_STATE = "receiver_state.json"

def load_key(path):
    if not os.path.exists(path):
        # NOTE: In a real environment, this key would be provisioned securely, not read from a file.
        raise FileNotFoundError("Key file not found. Run lambda_daemon.py to create it.")
    with open(path, "rb") as f:
        return f.read()

def load_state():
    """Load the state (simulating reading from the secured USB/HSM)."""
    if not os.path.exists(RECV_STATE):
        state = {"last_counter": 0}
        with open(RECV_STATE, "w") as f:
            json.dump(state, f)
        return state
    with open(RECV_STATE, "r") as f:
        return json.load(f)

def save_state(s):
    """Save the state (simulating writing to the secured USB/HSM)."""
    tmp = RECV_STATE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(s, f)
        f.flush(); os.fsync(f.fileno())
    os.replace(tmp, RECV_STATE)

def verify_token(key, token, expected_payload: bytes):
    aesgcm = AESGCM(key)
    # 1. Decode token components
    nonce = base64.b64decode(token['nonce'])
    ct = base64.b64decode(token['ciphertext'])
    aad = base64.b64decode(token['aad'])

    # 2. Cryptographic Gate: Decrypt and verify integrity tag
    try:
        pt = aesgcm.decrypt(nonce, ct, aad)
    except Exception as e:
        return False, f"decrypt_failed (AES-GCM integrity check failed): {e}"

    if len(pt) != 8+4+8:
        return False, "invalid_plaintext_length"

    # 3. Extract components: counter (Q), lambda2 (f), hash (8 bytes)
    counter = struct.unpack(">Q", pt[:8])[0]
    lambda_f = struct.unpack(">f", pt[8:12])[0]
    payload_hash = pt[12:20]

    # 4. Payload Binding Check
    if hashlib.sha256(expected_payload).digest()[:8] != payload_hash:
        return False, "payload_hash_mismatch (Token generated for a different payload)"

    # 5. Anti-Replay Gate: Check counter monotonicity
    s = load_state()
    last = s.get("last_counter", 0)
    if counter <= last:
        return False, "replay_or_out_of_order"

    # 6. Success: Update state and accept
    s['last_counter'] = counter
    save_state(s)
    return True, {"counter": counter, "lambda2": lambda_f}

def demo():
    print("Receiver ready. This demo expects the daemon to have created 'demo_key.bin'.")
    try:
        key = load_key(KEY_FILE)
    except FileNotFoundError as e:
        print(f"ERROR: {e}"); return

    # For manual testing you can paste token JSON here. For demo, prompt:
    print("Paste token JSON (as produced by event_client) and the original payload string.")
    
    while True:
        try:
            tok_json = input("Token JSON: ")
            payload = input("Payload string: ").encode('utf8')
            token = json.loads(tok_json)
        except KeyboardInterrupt:
            print("\nExiting receiver.")
            break
        except Exception as e:
            print("Invalid input:", e); continue
            
        ok, info = verify_token(key, token, payload)
        
        if ok:
            print(f"\n[VERIFIED] Token Accepted! Counter: {info['counter']}, Lambda2: {info['lambda2']}\n")
        else:
            print(f"\n[REJECTED] Reason: {info}\n")

if __name__ == '__main__':
    demo()