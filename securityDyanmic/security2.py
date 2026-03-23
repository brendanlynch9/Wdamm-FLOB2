import hmac
import hashlib
import struct
import time
from typing import Tuple

# Shared secret (in production, store in secure element/keystore)
SECRET_KEY = b'\x01'*32

TAG_LEN = 8  # bytes (64 bits); use >=8 if possible

def make_tag(key: bytes, payload: bytes, counter: int) -> bytes:
    # canonical encoding: payload || 8-byte big-endian counter
    counter_bytes = struct.pack(">Q", counter)
    mac = hmac.new(key, payload + counter_bytes, hashlib.sha256).digest()
    return mac[:TAG_LEN]

def verify_tag(key: bytes, payload: bytes, counter: int, tag: bytes,
               last_accepted_counter: int, window: int = 1) -> Tuple[bool, int]:
    """
    Verify tag within permissible counter window.
    Returns (accepted, new_last_accepted_counter)
    """
    # Accept counter in [last_accepted_counter+1, last_accepted_counter+1+window]
    
    # NOTE: The loop should check all counters in the window, including the received counter, 
    # but the primary check is against the received counter itself.
    
    # We check if the received counter is within the window first
    if counter <= last_accepted_counter or counter > last_accepted_counter + window + 1:
        # Received counter is old (replay) or too far in the future (desync/attack)
        return False, last_accepted_counter
        
    # Then check the specific tag for the received counter value
    expected = make_tag(key, payload, counter)
    # constant-time compare
    if hmac.compare_digest(expected, tag):
        # Only if the tag matches, we update the stored counter
        return True, counter
        
    return False, last_accepted_counter

# Example usage:
if __name__ == "__main__":
    # Sender
    payload = b"PLC_CMD:SET VAL=42"
    # Current counter (based on time)
    counter = int(time.time() // 5)
    tag = make_tag(SECRET_KEY, payload, counter)
    # send payload || counter || tag

    # Receiver
    # FIX: Initialize the stored_counter to one less than the current counter
    # This simulates a receiver that is synchronized and ready for the next valid packet.
    stored_counter = counter - 1 
    
    accepted, new_stored_counter = verify_tag(SECRET_KEY, payload, counter, tag, stored_counter, window=1)
    
    print("ACCEPTED" if accepted else "REJECTED")
    print(f"Old stored counter: {stored_counter}")
    print(f"New stored counter: {new_stored_counter}")

#     the output was:
#     (base) brendanlynch@Mac zzzzzzzhourglass % python security2.py
# ACCEPTED
# Old stored counter: 353075969
# New stored counter: 353075970
# (base) brendanlynch@Mac zzzzzzzhourglass % 