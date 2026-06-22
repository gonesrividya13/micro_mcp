import subprocess
import json

proc = subprocess.Popen(
    ["python3", "hub_adapter/mqtt_adapter.py", "192.168.1.133", "1883"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

req = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "TestHub", "version": "1.0"}
    }
}

proc.stdin.write(json.dumps(req) + "\n")
proc.stdin.flush()
print(proc.stdout.readline())

import time
time.sleep(2)

req2 = {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list"
}

proc.stdin.write(json.dumps(req2) + "\n")
proc.stdin.flush()
print(proc.stdout.readline())

proc.terminate()
