import paramiko
from scp import SCPClient
import sys
import os
import subprocess
import argparse

parser = argparse.ArgumentParser(description="Deploy micro_mcp to Raspberry Pi")
parser.add_argument("--mqtt", action="store_true", help="Compile and run the MQTT example instead of TCP")
args = parser.parse_args()

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
if args.mqtt:
    ssh.exec_command("pkill example_device_mqtt")

print("Uploading files...")
with SCPClient(ssh.get_transport()) as scp:
    scp.put("payload.tar.gz", remote_path="~/micro_mcp/")

print("Extracting and building on Pi...")
cmake_args = "-DUSE_MOSQUITTO=ON" if args.mqtt else ""
apt_deps = "cmake build-essential protobuf-compiler pkg-config"
if args.mqtt:
    apt_deps += " libmosquitto-dev mosquitto mosquitto-clients"

if args.mqtt:
    cmd = f"""
cd ~/micro_mcp &&
tar -xzf payload.tar.gz &&
echo '{password}' | sudo -S apt-get update &&
echo '{password}' | sudo -S apt-get install -y {apt_deps} &&
rm -rf build && mkdir build && cd build &&
cmake {cmake_args} .. && make -j4
killall example_device_mqtt 2>/dev/null || true
nohup ./example_device_mqtt livingroom-light > /dev/null 2>&1 &
nohup ./example_device_mqtt kitchen-thermostat > /dev/null 2>&1 &
nohup ./example_device_mqtt garage-door > /dev/null 2>&1 &
nohup ./example_device_mqtt front-door-lock > /dev/null 2>&1 &
nohup ./example_device_mqtt backyard-motion-sensor > /dev/null 2>&1 &
"""
else:
    cmd = f"""
cd ~/micro_mcp &&
tar -xzf payload.tar.gz &&
echo '{password}' | sudo -S apt-get update &&
echo '{password}' | sudo -S apt-get install -y {apt_deps} &&
rm -rf build && mkdir build && cd build &&
cmake {cmake_args} .. && make -j4
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

if not args.mqtt:
    binary_name = "example_device"
    print(f"Starting {binary_name} on Pi in the background...")
    ssh.exec_command(f"cd ~/micro_mcp && nohup ./build/{binary_name} > device.log 2>&1 &")

ssh.close()
print("Deployment and startup complete!")
