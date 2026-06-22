import asyncio
import os
import sys

# Ensure the antigravity SDK can find its credentials
if "GEMINI_API_KEY" not in os.environ:
    print("WARNING: GEMINI_API_KEY not found. Antigravity requires an API key.", file=sys.stderr)

from google.antigravity import Agent, LocalAgentConfig, types

async def main():
    print("Setting up Antigravity Agent with the MQTT MCP Hub Adapter...")
    
    # Configure the MCP server to point to our new mqtt_adapter.py
    # We pass the Pi's IP address and port 1883
    mcp_servers = [
        types.McpStdioServer(
            command="python3",
            args=["hub_adapter/mqtt_adapter.py", "192.168.1.133", "1883"],
        )
    ]
    
    config = LocalAgentConfig(mcp_servers=mcp_servers)
    
    async with Agent(config) as agent:
        print("\n🤖 [Agent initialized and connected to the IoT Hub!]")
        
        prompt = "Hello! Please list all the tools you have available. Then, use the appropriate tool to toggle the LED on the smart-sensor-mqtt device. Finally, tell me the current state of the LED based on the tool's response."
        print(f"\nUser: {prompt}\n")
        
        response = await agent.chat(prompt)
        print(f"Agent: {await response.text()}\n")

if __name__ == "__main__":
    asyncio.run(main())
