import requests
import json
import hmac
import hashlib
import time
from . import pprint

SECRET_KEY = b"your_secret_key"

def run(server: str, port: int, repo: str, commit: str, name: str) -> str:
    pprint.ok(f"Sending run request to {server}:{port}")
    payload = {
        "repo": repo,
        "commit": commit,
    }

    body = json.dumps(payload).encode('utf-8')
    timestamp = str(int(time.time()))

    signature = hmac.new(
        SECRET_KEY,
        body + timestamp.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    response = requests.post(
        f"http://{server}:{port}/run",
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Signature": signature,
            "X-Timestamp": timestamp,
            "X-Client-ID": name
        }
    )
    pprint.ok("Received response from server")
    return response
    
def query(server: str, port: int, name: str) -> str:
    pprint.ok(f"Sending query request to {server}:{port}")
    timestamp = str(int(time.time()))

    signature = hmac.new(
        SECRET_KEY,
        timestamp.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    response = requests.post(
        f"http://{server}:{port}/status",
        headers={
            "Content-Type": "application/json",
            "X-Signature": signature,
            "X-Timestamp": timestamp,
            "X-Client-ID": name
        }
    )

    pprint.ok("Received response from server")
    return response

def abort(server: str, port: int, name: str) -> str:
    pprint.ok(f"Sending abort request to {server}:{port}")
    timestamp = str(int(time.time()))

    signature = hmac.new(
        SECRET_KEY,
        timestamp.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    response = requests.post(
        f"http://{server}:{port}/abort",
        headers={
            "Content-Type": "application/json",
            "X-Signature": signature,
            "X-Timestamp": timestamp,
            "X-Client-ID": name
        }
    )

    pprint.ok("Received response from server")
    return response.json()