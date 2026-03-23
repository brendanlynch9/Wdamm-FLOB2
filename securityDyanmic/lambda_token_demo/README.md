# Lambda Token Demo

This demo contains:
- lambda_daemon.py : local daemon computing lambda2 and issuing AES-GCM tokens
- event_client.py : example client that sends events to the daemon
- receiver_server.py : example receiver that verifies tokens (decrypts AES-GCM)
- requirements.txt : required Python packages

Usage:
1. Install requirements:
   python -m pip install -r requirements.txt

2. Start the daemon in one terminal:
   python lambda_daemon.py

3. Start the receiver (verifier) in another terminal:
   python receiver_server.py

4. Send an event from client:
   python event_client.py keyboard "hello world"

The demo uses a file-backed symmetric key `demo_key.bin` created by the daemon on first run.
Both daemon and receiver expect the key file in the current working directory.

Security notes:
- This demo intentionally does NOT capture OS-level keystrokes.
- Ensure you have consent for any event data sent.
- For production, use secure key storage (HSM) and secure IPC (unix socket with permissions).
