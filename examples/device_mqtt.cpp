#include <micro_mcp/server.h>
#include <micro_mcp/transport/posix_mqtt_transport.h>
#include <iostream>
#include <unistd.h>

using namespace micro_mcp;

bool led_state = false;
float temperature = 22.0;

std::string toggle_led(const std::string& args_json) {
    led_state = !led_state;
    std::cout << "[Device] toggle_led invoked! New state: " << (led_state ? "ON" : "OFF") << std::endl;
    return "{\"status\": \"success\", \"state\": " + std::to_string(led_state) + "}";
}

std::string get_temperature() {
    temperature += 0.1;
    std::cout << "[Device] get_temperature invoked! Returning: " << temperature << "C" << std::endl;
    return "{\"temperature\": " + std::to_string(temperature) + ", \"unit\": \"C\"}";
}

int main(int argc, char* argv[]) {
    std::string device_name = "smart-sensor-mqtt";
    if (argc > 1) {
        device_name = argv[1];
    }

    std::cout << "Starting MQTT MCP Device: " << device_name << std::endl;

    // Provide a unique device name and connect to local mosquitto broker
    Server server(device_name, "1.0.0");
    PosixMqttTransport transport(device_name, "localhost", 1883);

    if (!transport.begin()) {
        std::cerr << "Failed to initialize MQTT transport" << std::endl;
        return 1;
    }

    server.set_transport(&transport);

    server.register_tool(
        "toggle_led", 
        "Toggles the smart bulb on or off", 
        "{\"type\": \"object\", \"properties\": {}}", 
        toggle_led
    );

    server.register_resource(
        "iot://sensors/temperature",
        "Temperature Sensor",
        "Reads the current temperature",
        "application/json",
        get_temperature
    );

    std::cout << "MQTT device running. Press Ctrl+C to stop." << std::endl;
    while (true) {
        server.poll();
        usleep(10000); // 10ms sleep
    }

    return 0;
}
