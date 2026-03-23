import requests
import json
import hmac
import hashlib
import time

SECRET_KEY = b"your_secret_key"

def run(server: str, port: int, repo: str, commit: str, name: str) -> str:
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
    return response
    
def query(server: str, port: int, name: str) -> str:
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

def abort(server: str, port: int, name: str) -> str:
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

    return response.json()