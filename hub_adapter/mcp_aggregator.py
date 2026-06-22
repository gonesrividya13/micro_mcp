import json
import sys
import asyncio
from typing import Dict, Any, Callable, Awaitable
import mcp_pb2
import time

class DeviceInfo:
    def __init__(self, device_id: str):
        self.device_id = device_id
        self.tools = []
        self.resources = []
        self.initialized = False
        self.last_seen = time.time()

class McpAggregator:
    def __init__(self, send_protobuf_cb: Callable[[str, mcp_pb2.McpMessage], Awaitable[None]]):
        self.send_protobuf_cb = send_protobuf_cb
        self.devices: Dict[str, DeviceInfo] = {}
        
        # We track requests sent to devices to route their responses back to the Agent
        # req_id -> (device_id, original_agent_id)
        self.pending_requests = {}
        self.internal_req_counter = 1000000

    def send_to_agent(self, resp: dict):
        print(json.dumps(resp), flush=True)

    async def add_device(self, device_id: str):
        if device_id not in self.devices:
            self.devices[device_id] = DeviceInfo(device_id)
            print(f"Aggregator: Discovered new device '{device_id}'. Fetching capabilities...", file=sys.stderr)
            
            # Send init
            msg = mcp_pb2.McpMessage()
            msg.id = self.internal_req_counter
            self.internal_req_counter += 1
            msg.init_req.protocol_version = "2024-11-05"
            msg.init_req.client_name = "HubAggregator"
            msg.init_req.client_version = "1.0"
            await self.send_protobuf_cb(device_id, msg)

            # Send tools/list
            msg_tools = mcp_pb2.McpMessage()
            msg_tools.id = self.internal_req_counter
            self.internal_req_counter += 1
            msg_tools.list_tools_req = True
            await self.send_protobuf_cb(device_id, msg_tools)

            # Send resources/list
            msg_res = mcp_pb2.McpMessage()
            msg_res.id = self.internal_req_counter
            self.internal_req_counter += 1
            msg_res.list_resources_req = True
            await self.send_protobuf_cb(device_id, msg_res)

    def remove_device(self, device_id: str):
        if device_id in self.devices:
            del self.devices[device_id]
            print(f"Aggregator: Removed device '{device_id}'", file=sys.stderr)
            
            # Notify the MCP client (Antigravity/Claude) that the tools list has changed
            notification = {
                "jsonrpc": "2.0",
                "method": "notifications/tools/list_changed"
            }
            print(json.dumps(notification), flush=True)

    async def prune_stale_devices(self):
        while True:
            await asyncio.sleep(5)
            now = time.time()
            stale_devices = []
            for device_id, dev in self.devices.items():
                if now - dev.last_seen > 25:
                    stale_devices.append(device_id)
            
            for device_id in stale_devices:
                print(f"Aggregator: Device '{device_id}' missed heartbeats. Pruning...", file=sys.stderr)
                self.remove_device(device_id)

    def handle_device_message(self, device_id: str, res_msg: mcp_pb2.McpMessage):
        if device_id not in self.devices:
            return
            
        dev = self.devices[device_id]
        dev.last_seen = time.time()
        which = res_msg.WhichOneof("message_type")
        
        # Check if this was an internal request (id >= 1000000)
        if res_msg.id >= 1000000:
            if which == "init_res":
                dev.initialized = True
            elif which == "list_tools_res":
                dev.tools = []
                for t in res_msg.list_tools_res.tools:
                    dev.tools.append({
                        "name": f"{device_id}_{t.name}",
                        "description": t.description,
                        "inputSchema": json.loads(t.input_schema_json) if t.input_schema_json else {"type": "object", "properties": {}}
                    })
                # Notify the MCP client (Antigravity/Claude) that the tools list has changed
                notification = {
                    "jsonrpc": "2.0",
                    "method": "notifications/tools/list_changed"
                }
                print(json.dumps(notification), flush=True)
            elif which == "list_resources_res":
                dev.resources = []
                for r in res_msg.list_resources_res.resources:
                    dev.resources.append({
                        "uri": f"iot://{device_id}/{r.uri}",
                        "name": r.name,
                        "description": r.description,
                        "mimeType": r.mime_type
                    })
            return

        # Otherwise, this is a response to the AI Agent
        req_info = self.pending_requests.pop(res_msg.id, None)
        if not req_info:
            return # Unknown request ID
        
        _, original_agent_id = req_info
        resp = {"jsonrpc": "2.0", "id": original_agent_id}

        if which == "call_tool_res":
            print(f"Aggregator: Received response from device '{device_id}' for tool call.", file=sys.stderr)
            resp["result"] = {
                "isError": res_msg.call_tool_res.is_error,
                "content": [{"type": "text", "text": res_msg.call_tool_res.content_text}]
            }
        elif which == "read_resource_res":
            # We don't track the original URI here easily, but the Agent knows what it requested.
            # Ideally we should send the URI back in the response.
            resp["result"] = {
                "contents": [{"uri": "unknown", "mimeType": "text/plain", "text": res_msg.read_resource_res.contents_text}]
            }
        elif which == "error_message":
            resp["error"] = {"code": -32000, "message": res_msg.error_message}

        self.send_to_agent(resp)

    async def handle_agent_message(self, line: str):
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            return

        method = req.get("method")
        req_id = req.get("id")

        if method == "initialize":
            resp = {
                "jsonrpc": "2.0", 
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}, "resources": {}},
                    "serverInfo": {"name": "micro_mcp_hub", "version": "1.0"}
                }
            }
            self.send_to_agent(resp)
            
        elif method == "notifications/initialized":
            pass

        elif method == "tools/list":
            all_tools = []
            for dev in self.devices.values():
                all_tools.extend(dev.tools)
            resp = {"jsonrpc": "2.0", "id": req_id, "result": {"tools": all_tools}}
            self.send_to_agent(resp)

        elif method == "resources/list":
            all_res = []
            for dev in self.devices.values():
                all_res.extend(dev.resources)
            resp = {"jsonrpc": "2.0", "id": req_id, "result": {"resources": all_res}}
            self.send_to_agent(resp)

        elif method == "tools/call":
            tool_name = req["params"]["name"]
            # tool name is formatted as {device_id}_{actual_tool}
            parts = tool_name.split("_", 1)
            if len(parts) != 2 or parts[0] not in self.devices:
                self.send_to_agent({"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Tool not found: {tool_name}"}})
                return
            
            device_id, actual_tool = parts[0], parts[1]
            
            print(f"Aggregator: Routing tool call '{actual_tool}' to device '{device_id}'...", file=sys.stderr)
            
            # Route to device
            msg = mcp_pb2.McpMessage()
            msg.id = hash(str(req_id)) % 1000000 # keep below internal counter
            msg.call_tool_req.name = actual_tool
            msg.call_tool_req.arguments_json = json.dumps(req["params"].get("arguments", {}))
            
            self.pending_requests[msg.id] = (device_id, req_id)
            await self.send_protobuf_cb(device_id, msg)

        elif method == "resources/read":
            uri = req["params"]["uri"]
            # uri is formatted as iot://{device_id}/{actual_uri}
            if not uri.startswith("iot://"):
                self.send_to_agent({"jsonrpc": "2.0", "id": req_id, "error": {"code": -32602, "message": "Invalid URI schema"}})
                return
                
            parts = uri[6:].split("/", 1)
            if len(parts) != 2 or parts[0] not in self.devices:
                self.send_to_agent({"jsonrpc": "2.0", "id": req_id, "error": {"code": -32602, "message": f"Device not found for URI: {uri}"}})
                return
                
            device_id, actual_uri = parts[0], parts[1]
            
            msg = mcp_pb2.McpMessage()
            msg.id = hash(str(req_id)) % 1000000
            msg.read_resource_req.uri = actual_uri
            
            self.pending_requests[msg.id] = (device_id, req_id)
            await self.send_protobuf_cb(device_id, msg)
        else:
            if req_id is not None:
                self.send_to_agent({"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}})
