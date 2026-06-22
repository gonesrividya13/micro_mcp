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
