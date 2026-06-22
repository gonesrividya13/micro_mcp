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

import paho.mqtt.client as mqtt
import mcp_pb2
import time

def on_connect(client, userdata, flags, rc, properties=None):
    print(f"Connected with result code {rc}")
    client.subscribe("mcp/#")
    
    print("Publishing broadcast ping...")
    ping = mcp_pb2.McpMessage()
    ping.id = 999999
    ping.list_tools_req = True
    client.publish("mcp/broadcast/rx", ping.SerializeToString(), qos=0)

def on_message(client, userdata, msg):
    print(f"Received message on topic {msg.topic} with payload length {len(msg.payload)}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

print("Connecting to Pi broker...")
client.connect("192.168.1.133", 1883, 60)
client.loop_forever()
