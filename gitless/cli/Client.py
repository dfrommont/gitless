import requests
import json
import hmac
import hashlib
import time
from fastapi import HTTPException

from . import pprint

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

    pprint.ok("Sending request to server...")

    try:
        response = requests.post(
            f"http://{server}:{port}/run",
            data=body,
            headers={
                "Content-Type": "application/json",
                "X-Signature": signature,
                "X-Timestamp": timestamp,
                "X-Client-ID": name
            },
            timeout=10
        )
    except HTTPException as e:
        pprint.err(f"Received a HTTP 400 exception from the server: {e}")
    except Exception as e:
        pprint.err(f"There has been an error! {e}")

    return response
    
def query(server: str, port: int, name: str) -> str:
    timestamp = str(int(time.time()))

    signature = hmac.new(
        SECRET_KEY,
        timestamp.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    pprint.ok("Sending query to server...")
    
    try:
        response = requests.post(
            f"http://{server}:{port}/status",
            headers={
                "Content-Type": "application/json",
                "X-Signature": signature,
                "X-Timestamp": timestamp,
                "X-Client-ID": name
            },
            timeout=10
        )
    except HTTPException as e:
        pprint.err(f"Received a HTTP 400 exception from the server: {e}")
    except Exception as e:
        pprint.err(f"There has been an error! {e}")

    return response

def abort(server: str, port: int, name: str) -> str:
    timestamp = str(int(time.time()))

    signature = hmac.new(
        SECRET_KEY,
        timestamp.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    pprint.ok("Sending abort request to server...")

    try:
        response = requests.post(
            f"http://{server}:{port}/abort",
            headers={
                "Content-Type": "application/json",
                "X-Signature": signature,
                "X-Timestamp": timestamp,
                "X-Client-ID": name
            },
            timeout=10
        )
    except HTTPException as e:
        pprint.err(f"Received a HTTP 400 exception from the server: {e}")
    except Exception as e:
        pprint.err(f"There has been an error! {e}")

    return response.json()