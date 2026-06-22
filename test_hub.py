import subprocess
import json
import time

proc = subprocess.Popen(
    ["python3", "hub_adapter/adapter.py", "192.168.1.133", "5000"],
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

print("Sending 'initialize' through Hub adapter to Raspberry Pi...")
proc.stdin.write(json.dumps(req) + "\n")
proc.stdin.flush()

res = proc.stdout.readline()
print("Received back from Pi:")
print(json.dumps(json.loads(res), indent=2))

req2 = {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list"
}
print("\nSending 'tools/list' through Hub adapter to Raspberry Pi...")
proc.stdin.write(json.dumps(req2) + "\n")
proc.stdin.flush()

res2 = proc.stdout.readline()
print("Received back from Pi:")
print(json.dumps(json.loads(res2), indent=2))

proc.terminate()
