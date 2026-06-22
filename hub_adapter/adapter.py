import sys
import json
import socket
import struct
import mcp_pb2
import threading

found_device = None
found_event = threading.Event()

def on_service_state_change(zeroconf, service_type, name, state_change):
    global found_device
    # Note: ServiceStateChange enum values are accessed directly in newer zeroconf
    if state_change.name == "Added" or getattr(state_change, "value", 0) == 1: 
        info = zeroconf.get_service_info(service_type, name)
        if info and info.addresses:
            ip = socket.inet_ntoa(info.addresses[0])
            found_device = (ip, info.port)
            found_event.set()

def send_protobuf(sock, msg: mcp_pb2.McpMessage):
    data = msg.SerializeToString()
    # 16-bit length prefix
    header = struct.pack('>H', len(data))
    sock.sendall(header + data)

def recv_protobuf(sock):
    header = sock.recv(2)
    if not header or len(header) < 2:
        return None
    length = struct.unpack('>H', header)[0]
    
    data = b''
    while len(data) < length:
        chunk = sock.recv(length - len(data))
        if not chunk:
            return None
        data += chunk
        
    msg = mcp_pb2.McpMessage()
    msg.ParseFromString(data)
    return msg

def main():
    if len(sys.argv) < 3:
        print("No IP/port provided. Scanning network via mDNS for _micro_mcp._tcp.local. ...", file=sys.stderr)
        try:
            from zeroconf import Zeroconf, ServiceBrowser, ServiceStateChange
        except ImportError:
            print("Please install 'zeroconf' (pip install zeroconf) to use autodetection.", file=sys.stderr)
            sys.exit(1)
            
        zc = Zeroconf()
        # Use a small class to handle zeroconf callbacks
        class MyListener:
            def remove_service(self, zeroconf, type, name): pass
            def update_service(self, zeroconf, type, name): pass
            def add_service(self, zeroconf, type, name):
                global found_device
                info = zeroconf.get_service_info(type, name)
                if info and info.addresses:
                    ip = socket.inet_ntoa(info.addresses[0])
                    found_device = (ip, info.port)
                    found_event.set()
        
        listener = MyListener()
        browser = ServiceBrowser(zc, "_micro_mcp._tcp.local.", listener)
        if found_event.wait(timeout=10.0):
            ip, port = found_device
            print(f"Found micro_mcp device at {ip}:{port}", file=sys.stderr)
        else:
            print("No device found after 10 seconds.", file=sys.stderr)
            zc.close()
            sys.exit(1)
        zc.close()
    else:
        ip = sys.argv[1]
        port = int(sys.argv[2])
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((ip, port))
        print(f"Connected to IoT device at {ip}:{port}", file=sys.stderr)
    except Exception as e:
        print(f"Failed to connect: {e}", file=sys.stderr)
        sys.exit(1)
        
    while True:
        line = sys.stdin.readline()
        if not line:
            break
            
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
            
        msg = mcp_pb2.McpMessage()
        
        req_id = req.get("id", 1)
        if isinstance(req_id, str):
            msg.id = hash(req_id) % 2147483647
        else:
            msg.id = req_id

        method = req.get("method")
        
        if method == "initialize":
            msg.init_req.protocol_version = req.get("params", {}).get("protocolVersion", "2024-11-05")
            msg.init_req.client_name = req.get("params", {}).get("clientInfo", {}).get("name", "adapter")
            msg.init_req.client_version = req.get("params", {}).get("clientInfo", {}).get("version", "1.0")
        elif method == "tools/list":
            msg.list_tools_req = True
        elif method == "tools/call":
            msg.call_tool_req.name = req["params"]["name"]
            msg.call_tool_req.arguments_json = json.dumps(req["params"].get("arguments", {}))
        elif method == "resources/list":
            msg.list_resources_req = True
        elif method == "resources/read":
            msg.read_resource_req.uri = req["params"]["uri"]
        elif method == "notifications/initialized":
            continue # ignore
        else:
            if "id" in req:
                resp = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}}
                print(json.dumps(resp), flush=True)
            continue
            
        send_protobuf(sock, msg)
        
        res_msg = recv_protobuf(sock)
        if not res_msg:
            break
            
        resp = {"jsonrpc": "2.0", "id": req_id}
        
        which = res_msg.WhichOneof("message_type")
        if which == "init_res":
            resp["result"] = {
                "protocolVersion": res_msg.init_res.protocol_version,
                "capabilities": {"tools": {}, "resources": {}},
                "serverInfo": {
                    "name": res_msg.init_res.server_name,
                    "version": res_msg.init_res.server_version
                }
            }
        elif which == "list_tools_res":
            tools = []
            for t in res_msg.list_tools_res.tools:
                tools.append({
                    "name": t.name,
                    "description": t.description,
                    "inputSchema": json.loads(t.input_schema_json) if t.input_schema_json else {"type": "object", "properties": {}}
                })
            resp["result"] = {"tools": tools}
        elif which == "call_tool_res":
            resp["result"] = {
                "isError": res_msg.call_tool_res.is_error,
                "content": [{"type": "text", "text": res_msg.call_tool_res.content_text}]
            }
        elif which == "list_resources_res":
            resources = []
            for r in res_msg.list_resources_res.resources:
                resources.append({
                    "uri": r.uri,
                    "name": r.name,
                    "description": r.description,
                    "mimeType": r.mime_type
                })
            resp["result"] = {"resources": resources}
        elif which == "read_resource_res":
            resp["result"] = {
                "contents": [{"uri": req["params"]["uri"], "mimeType": "text/plain", "text": res_msg.read_resource_res.contents_text}]
            }
        elif which == "error_message":
            resp["error"] = {"code": -32000, "message": res_msg.error_message}
            
        print(json.dumps(resp), flush=True)

if __name__ == "__main__":
    main()