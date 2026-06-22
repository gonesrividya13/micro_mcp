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

import asyncio
import sys
import threading
import paho.mqtt.client as mqtt

import mcp_pb2
from mcp_aggregator import McpAggregator

class MqttAdapter:
    def __init__(self, broker_host="localhost", broker_port=1883):
        self.aggregator = McpAggregator(self.send_to_device)
        self.broker_host = broker_host
        self.broker_port = broker_port
        
        # Use new Paho MQTT v2 API
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
        self.stdin_queue = None
        self.loop = None

    def on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            print("MQTT Adapter: Connected to broker. Subscribing to wildcard 'mcp/+/tx'...", file=sys.stderr)
            self.client.subscribe("mcp/+/tx")
            
            # Broadcast a ping to wake up all devices and trigger discovery
            ping = mcp_pb2.McpMessage()
            ping.id = 999999
            ping.list_tools_req = True
            self.client.publish("mcp/broadcast/rx", ping.SerializeToString(), qos=0)
        else:
            print(f"MQTT Adapter: Failed to connect, return code {rc}", file=sys.stderr)

    def on_message(self, client, userdata, msg):
        # Topic format: mcp/{device_id}/tx
        parts = msg.topic.split("/")
        if len(parts) == 3 and parts[0] == "mcp" and parts[2] == "tx":
            device_id = parts[1]
            
            try:
                mcp_msg = mcp_pb2.McpMessage()
                mcp_msg.ParseFromString(msg.payload)
                
                # If we've never seen this device, add it!
                if device_id not in self.aggregator.devices and self.loop is not None:
                    asyncio.run_coroutine_threadsafe(self.aggregator.add_device(device_id), self.loop)
                
                # Process the message in the main asyncio loop
                if self.loop is not None:
                    self.loop.call_soon_threadsafe(self.aggregator.handle_device_message, device_id, mcp_msg)
            except Exception as e:
                print(f"MQTT Adapter: Failed to parse message from {device_id}: {e}", file=sys.stderr)

    async def send_to_device(self, device_id: str, msg: mcp_pb2.McpMessage):
        data = msg.SerializeToString()
        topic = f"mcp/{device_id}/rx"
        self.client.publish(topic, data, qos=0)

    async def broadcast_heartbeat(self):
        while True:
            await asyncio.sleep(10)
            ping = mcp_pb2.McpMessage()
            ping.id = 999999
            ping.init_req.protocol_version = "2024-11-05"
            ping.init_req.client_name = "HubHeartbeat"
            ping.init_req.client_version = "1.0"
            self.client.publish("mcp/broadcast/rx", ping.SerializeToString(), qos=0)

    def stdin_reader(self):
        for line in sys.stdin:
            if self.loop is not None:
                asyncio.run_coroutine_threadsafe(self.stdin_queue.put(line), self.loop)

    async def run(self):
        self.loop = asyncio.get_running_loop()
        self.stdin_queue = asyncio.Queue()
        
        try:
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
        except Exception as e:
            print(f"MQTT Adapter: Failed to connect to broker {self.broker_host}: {e}", file=sys.stderr)
            sys.exit(1)

        # Start stdin reader thread
        threading.Thread(target=self.stdin_reader, daemon=True).start()

        # Start heartbeat and pruning loops
        asyncio.create_task(self.broadcast_heartbeat())
        asyncio.create_task(self.aggregator.prune_stale_devices())

        while True:
            line = await self.stdin_queue.get()
            await self.aggregator.handle_agent_message(line)

if __name__ == "__main__":
    broker = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 1883
    
    adapter = MqttAdapter(broker, port)
    try:
        asyncio.run(adapter.run())
    except KeyboardInterrupt:
        pass
