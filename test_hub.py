# Copyright 2024 The micro_mcp Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
