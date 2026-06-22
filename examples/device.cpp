/*
 * Copyright 2024 The micro_mcp Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include <micro_mcp/server.h>
#include <micro_mcp/transport/posix_tcp_transport.h>
#include <iostream>
#include <unistd.h>

using namespace micro_mcp;

bool led_state = false;

std::string toggle_led(const std::string& args_json) {
    led_state = !led_state;
    std::cout << "[HARDWARE] LED is now " << (led_state ? "ON" : "OFF") << std::endl;
    return "{\"status\": \"success\", \"led_state\": " + std::string(led_state ? "true" : "false") + "}";
}

std::string read_temperature() {
    return "23.5"; // Fake temperature in Celsius
}

int main() {
    Server server("smart-bulb", "1.0.0");
    PosixTcpTransport transport(5000);

    if (!transport.begin()) {
        std::cerr << "Failed to start transport on port 5000" << std::endl;
        return 1;
    }

    server.set_transport(&transport);

    // ---------------------------------------------------------
    // NOTE FOR IOT BOARDS (e.g., ESP32 / Arduino):
    // To allow the Hub Adapter to automatically find this device,
    // you should broadcast mDNS using your platform's native library.
    // 
    // Example for ESP32:
    // #include <ESPmDNS.h>
    // MDNS.begin("smart-bulb");
    // MDNS.addService("micro_mcp", "tcp", 5000);
    // ---------------------------------------------------------

    server.register_tool(
        "toggle_led",
        "Toggles the smart bulb on or off",
        "{\"type\": \"object\", \"properties\": {}}",
        toggle_led
    );

    server.register_resource(
        "sensor://temperature",
        "Temperature Sensor",
        "Reads the ambient temperature",
        "text/plain",
        read_temperature
    );

    std::cout << "Device listening on port 5000" << std::endl;

    while (true) {
        server.poll();
        usleep(10000); // 10ms sleep
    }

    return 0;
}