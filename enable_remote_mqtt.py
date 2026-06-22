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

import paramiko
import sys

host = "192.168.1.133"
user = "vidya"
password = "130699"

print("Connecting to Pi to enable remote MQTT...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(host, username=user, password=password, timeout=10)
except Exception as e:
    print(f"Failed to connect: {e}")
    sys.exit(1)

conf = """
listener 1883 0.0.0.0
allow_anonymous true
"""

cmd = f"""
echo '{password}' | sudo -S sh -c "echo '{conf}' > /etc/mosquitto/conf.d/remote.conf"
echo '{password}' | sudo -S systemctl restart mosquitto
"""
stdin, stdout, stderr = ssh.exec_command(cmd)
exit_status = stdout.channel.recv_exit_status()

if exit_status == 0:
    print("Successfully configured Mosquitto to accept remote connections!")
else:
    print("Failed to configure Mosquitto:")
    print(stderr.read().decode())

ssh.close()
