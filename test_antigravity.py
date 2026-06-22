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
