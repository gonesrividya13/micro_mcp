import asyncio
import sys
import threading
import struct
import socket
from zeroconf import Zeroconf, ServiceBrowser

import mcp_pb2
from mcp_aggregator import McpAggregator

class AsyncTcpAdapter:
    def __init__(self):
        self.aggregator = McpAggregator(self.send_to_device)
        self.connections = {} # device_id -> (reader, writer)
        self.stdin_queue = None

    async def send_to_device(self, device_id: str, msg: mcp_pb2.McpMessage):
        if device_id in self.connections:
            _, writer = self.connections[device_id]
            data = msg.SerializeToString()
            header = struct.pack('>H', len(data))
            writer.write(header + data)
            await writer.drain()

    async def device_reader_task(self, device_id: str, reader: asyncio.StreamReader):
        try:
            while True:
                header = await reader.readexactly(2)
                length = struct.unpack('>H', header)[0]
                data = await reader.readexactly(length)
                
                msg = mcp_pb2.McpMessage()
                msg.ParseFromString(data)
                self.aggregator.handle_device_message(device_id, msg)
        except (asyncio.IncompleteReadError, ConnectionError):
            print(f"TCP Adapter: Connection lost to {device_id}", file=sys.stderr)
            self.aggregator.remove_device(device_id)
            if device_id in self.connections:
                del self.connections[device_id]

    async def connect_to_device(self, ip: str, port: int, device_id: str):
        try:
            reader, writer = await asyncio.open_connection(ip, port)
            self.connections[device_id] = (reader, writer)
            await self.aggregator.add_device(device_id)
            asyncio.create_task(self.device_reader_task(device_id, reader))
        except Exception as e:
            print(f"TCP Adapter: Failed to connect to {device_id} ({ip}:{port}): {e}", file=sys.stderr)

    def on_mdns_discovery(self, zeroconf, service_type, name, state_change):
        if getattr(state_change, "value", 0) == 1 or getattr(state_change, "name", "") == "Added":
            info = zeroconf.get_service_info(service_type, name)
            if info and info.addresses:
                ip = socket.inet_ntoa(info.addresses[0])
                device_id = name.replace("._micro_mcp._tcp.local.", "")
                
                # Schedule connection in asyncio loop
                asyncio.run_coroutine_threadsafe(
                    self.connect_to_device(ip, info.port, device_id),
                    asyncio.get_running_loop()
                )

    def stdin_reader(self, loop):
        for line in sys.stdin:
            asyncio.run_coroutine_threadsafe(self.stdin_queue.put(line), loop)

    async def run(self):
        self.stdin_queue = asyncio.Queue()
        print("TCP Adapter: Starting mDNS discovery...", file=sys.stderr)
        zc = Zeroconf()
        browser = ServiceBrowser(zc, "_micro_mcp._tcp.local.", handlers=[self.on_mdns_discovery])

        # Start stdin reader thread
        threading.Thread(target=self.stdin_reader, args=(asyncio.get_running_loop(),), daemon=True).start()

        while True:
            line = await self.stdin_queue.get()
            await self.aggregator.handle_agent_message(line)

if __name__ == "__main__":
    adapter = AsyncTcpAdapter()
    try:
        asyncio.run(adapter.run())
    except KeyboardInterrupt:
        pass
