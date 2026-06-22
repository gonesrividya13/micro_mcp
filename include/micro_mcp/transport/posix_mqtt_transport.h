#pragma once
#include "micro_mcp/transport.h"
#include <string>
#include <vector>
#include <mutex>
#include <mosquitto.h>

namespace micro_mcp {

class PosixMqttTransport : public Transport {
public:
    PosixMqttTransport(const std::string& device_name, const std::string& broker_host = "localhost", int broker_port = 1883);
    virtual ~PosixMqttTransport();

    bool begin() override;
    bool send(const uint8_t* data, size_t length) override;
    size_t receive(uint8_t* buffer, size_t max_length) override;
    bool available() override;

private:
    std::string device_name_;
    std::string broker_host_;
    int broker_port_;
    
    std::string rx_topic_;
    std::string tx_topic_;

    struct mosquitto* mosq_;
    
    std::vector<uint8_t> rx_buffer_;
    std::mutex rx_mutex_;

    static void on_message(struct mosquitto *mosq, void *userdata, const struct mosquitto_message *message);
    static void on_connect(struct mosquitto *mosq, void *userdata, int rc);
};

} // namespace micro_mcp
