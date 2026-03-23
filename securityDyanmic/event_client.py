#!/usr/bin/env python3
"""event_client.py
# WARNING: Proof-of-Concept Only

This software and documentation demonstrate the Complex-Gated Authentication (CGA) protocol. 

DO NOT USE IN PRODUCTION. All keys and code are for academic/testing purposes. 

Use at your own risk. No liability is assumed by the author.

Send an event to the local lambda daemon and print the response token.
Usage: python event_client.py <event_type> <payload string>
"""
import sys, json, socket, base64
HOST = "127.0.0.1"
PORT = 23456

def send_event(event_type: str, payload_bytes: bytes):
    payload_b64 = base64.b64encode(payload_bytes).decode("ascii")
    req = {"event_type": event_type, "payload_b64": payload_b64}
    data = json.dumps(req).encode("utf8")
    with socket.create_connection((HOST, PORT), timeout=2) as s:
        s.sendall(data)
        
        # <<< FIX IS HERE: Signal that we are done sending data >>>
        s.shutdown(socket.SHUT_WR) 
        
        # read response
        resp_raw = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            resp_raw += chunk
    resp = json.loads(resp_raw.decode("utf8"))
    return resp

def demo():
    if len(sys.argv) < 3:
        print("Usage: python event_client.py <event_type> <payload string>")
        return
    event_type = sys.argv[1]
    payload = sys.argv[2].encode("utf8")
    resp = send_event(event_type, payload)
    print("Daemon response:")
    print(json.dumps(resp, indent=2))

if __name__ == "__main__":
    demo()