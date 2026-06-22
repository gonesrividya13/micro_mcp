import paramiko
from scp import SCPClient
import sys
import os
import subprocess

host = "192.168.1.133"
user = "vidya"
password = "130699"

print("Creating local tarball...")
subprocess.run("tar --exclude='build' --exclude='__pycache__' --exclude='.git' -czf payload.tar.gz .", shell=True, check=True)

print("Connecting to Pi...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect(host, username=user, password=password, timeout=10)
except Exception as e:
    print(f"Failed to connect: {e}")
    sys.exit(1)

print("Creating directory...")
ssh.exec_command("mkdir -p ~/micro_mcp && pkill example_device")

print("Uploading files...")
with SCPClient(ssh.get_transport()) as scp:
    scp.put("payload.tar.gz", remote_path="~/micro_mcp/")

print("Extracting and building on Pi...")
cmd = f"""
cd ~/micro_mcp &&
tar -xzf payload.tar.gz &&
echo '{password}' | sudo -S apt-get update &&
echo '{password}' | sudo -S apt-get install -y cmake build-essential protobuf-compiler &&
rm -rf build && mkdir build && cd build &&
cmake .. && make -j4
"""
stdin, stdout, stderr = ssh.exec_command(cmd)

exit_status = stdout.channel.recv_exit_status()
if exit_status == 0:
    print("Build successful on Pi!")
else:
    print("Build failed!")
    print(stdout.read().decode())
    print(stderr.read().decode())
    sys.exit(1)

print("Starting example_device on Pi in the background...")
ssh.exec_command("cd ~/micro_mcp && nohup ./build/example_device > device.log 2>&1 &")

ssh.close()
print("Deployment and startup complete!")
