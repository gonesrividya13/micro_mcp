# micro_mcp 🚀

`micro_mcp` is an extremely lightweight, memory-efficient C++ implementation of the **Model Context Protocol (MCP)** specifically designed for IoT devices and microcontrollers (like ESP32, Arduino, and Pico). 

It allows your local AI agents (e.g., Claude Desktop or custom agents) to seamlessly discover, read sensors from, and actuate your IoT devices over a local network.

---

## 🏗️ Architecture & Visual Connection

Because standard MCP relies on parsing bulky JSON strings over `stdio`, it can quickly exhaust the RAM of a tiny microcontroller. 

To solve this, `micro_mcp` uses **Protocol Buffers** to send highly compressed binary messages over a TCP socket. A lightweight Python **Hub Adapter** runs on your Agent Hub (your laptop or server) to automatically translate these binary messages back into standard JSON-RPC MCP that your AI agents understand.

```mermaid
graph LR
    subgraph "IoT Device (e.g., ESP32)"
        Sensors[Hardware Sensors/LEDs] <--> MicroServer(micro_mcp C++ Server)
        MicroServer -.->|Broadcasts| mDNS((mDNS _micro_mcp._tcp))
    end
    
    subgraph "Agent Hub (Laptop/Server)"
        Adapter(Hub Adapter proxy) <-->|JSON-RPC via stdio| Agent[AI Agent]
    end
    
    mDNS -.->|Autodiscovery| Adapter
    MicroServer <==>|Protobuf over TCP Socket| Adapter
```

---

## 🛠️ Features

- **Abstract Transports:** Pure virtual `Transport` interface so you can run it over Wi-Fi (TCP), Serial, or MQTT.
- **Zero JSON Parsing:** All serialization is done via statically allocated Protocol Buffers (`nanopb`), keeping memory usage tiny and predictable.
- **Automatic Network Discovery:** Built-in mDNS support means your Hub Adapter automatically finds devices on the network.
- **Full MCP Support:** Expose both **Tools** (actuators) and **Resources** (sensors).

---

## 🚀 Getting Started

### 1. Flash the IoT Device (C++)

Include the library in your C++ project. Here is how easy it is to expose a smart bulb to an AI agent:

```cpp
#include <micro_mcp/server.h>
#include <micro_mcp/transport/posix_tcp_transport.h>
#include <ESPmDNS.h> // Example for ESP32

using namespace micro_mcp;

bool led_state = false;

// 1. Define your hardware function
std::string toggle_led(const std::string& args_json) {
    led_state = !led_state;
    digitalWrite(LED_PIN, led_state ? HIGH : LOW);
    return "{\"status\": \"success\"}";
}

void setup() {
    // ... connect to WiFi ...

    // 2. Broadcast the device to the network
    MDNS.begin("smart-bulb");
    MDNS.addService("micro_mcp", "tcp", 5000);

    // 3. Start the Server and register tools
    static Server server("smart-bulb", "1.0.0");
    static PosixTcpTransport transport(5000);
    
    transport.begin();
    server.set_transport(&transport);

    server.register_tool(
        "toggle_led", 
        "Toggles the smart bulb on or off", 
        "{\"type\": \"object\", \"properties\": {}}", 
        toggle_led
    );
}

void loop() {
    server.poll(); // Keep the MCP connection alive
}
```

### 2. Run the Hub Adapter

On your local machine (where your AI agent lives), install the requirements for the bridge:

```bash
cd hub_adapter
pip install grpcio-tools protobuf zeroconf
```

### 3. Connect your AI Agent

Configure your AI Agent (like Claude Desktop) to use the Hub Adapter. 

If your IoT device is broadcasting mDNS (as shown in the code above), you don't even need to provide an IP address. Just run the adapter!

**`claude_desktop_config.json`:**
```json
{
  "mcpServers": {
    "iot-bulb": {
      "command": "python3",
      "args": [
        "/path/to/micro_mcp/hub_adapter/adapter.py"
      ]
    }
  }
}
```

If you aren't using mDNS, you can easily hardcode the IP and port:
```json
      "args": [
        "/path/to/micro_mcp/hub_adapter/adapter.py",
        "192.168.1.100",
        "5000"
      ]
```

---

## 📁 Directory Layout

- `/proto/`: Contains `mcp.proto`, the binary specification of the Model Context Protocol.
- `/include/micro_mcp/`: The public C++ headers.
- `/src/`: The C++ implementations and generated nanopb serialization code.
- `/hub_adapter/`: The Python proxy that bridges the IoT device to your AI Agent.
- `/examples/`: Simulated examples of how to run the library.