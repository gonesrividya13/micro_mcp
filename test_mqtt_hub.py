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
