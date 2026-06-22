#include "micro_mcp/transport/posix_mqtt_transport.h"
#include <iostream>
#include <cstring>

namespace micro_mcp {

PosixMqttTransport::PosixMqttTransport(const std::string& device_name, const std::string& broker_host, int broker_port)
    : device_name_(device_name), broker_host_(broker_host), broker_port_(broker_port), mosq_(nullptr) {
    rx_topic_ = "mcp/" + device_name_ + "/rx";
    tx_topic_ = "mcp/" + device_name_ + "/tx";
}

PosixMqttTransport::~PosixMqttTransport() {
    if (mosq_) {
        mosquitto_disconnect(mosq_);
        mosquitto_loop_stop(mosq_, true);
        mosquitto_destroy(mosq_);
    }
    mosquitto_lib_cleanup();
}

void PosixMqttTransport::on_connect(struct mosquitto *mosq, void *userdata, int rc) {
    PosixMqttTransport* transport = static_cast<PosixMqttTransport*>(userdata);
    if (rc == 0) {
        mosquitto_subscribe(mosq, NULL, transport->rx_topic_.c_str(), 0);
        mosquitto_subscribe(mosq, NULL, "mcp/broadcast/rx", 0);
    } else {
        std::cerr << "MQTT connection failed: " << mosquitto_connack_string(rc) << std::endl;
    }
}

void PosixMqttTransport::on_message(struct mosquitto *mosq, void *userdata, const struct mosquitto_message *message) {
    PosixMqttTransport* transport = static_cast<PosixMqttTransport*>(userdata);
    
    std::lock_guard<std::mutex> lock(transport->rx_mutex_);
    const uint8_t* payload = static_cast<const uint8_t*>(message->payload);
    size_t len = message->payloadlen;
    
    // Inject 2-byte length header expected by Server::poll()
    uint8_t header[2];
    header[0] = (len >> 8) & 0xFF;
    header[1] = len & 0xFF;
    transport->rx_buffer_.insert(transport->rx_buffer_.end(), header, header + 2);
    transport->rx_buffer_.insert(transport->rx_buffer_.end(), payload, payload + len);
}

bool PosixMqttTransport::begin() {
    mosquitto_lib_init();

    mosq_ = mosquitto_new(device_name_.c_str(), true, this);
    if (!mosq_) {
        std::cerr << "Failed to create mosquitto instance." << std::endl;
        return false;
    }

    mosquitto_connect_callback_set(mosq_, on_connect);
    mosquitto_message_callback_set(mosq_, on_message);

    int rc = mosquitto_connect(mosq_, broker_host_.c_str(), broker_port_, 60);
    if (rc != MOSQ_ERR_SUCCESS) {
        std::cerr << "Failed to connect to MQTT broker: " << mosquitto_strerror(rc) << std::endl;
        return false;
    }

    mosquitto_loop_start(mosq_);
    return true;
}

bool PosixMqttTransport::send(const uint8_t* data, size_t length) {
    if (!mosq_ || length < 2) return false;
    
    // Strip the 2-byte length header added by Server::send_message()
    int rc = mosquitto_publish(mosq_, NULL, tx_topic_.c_str(), length - 2, data + 2, 0, false);
    return rc == MOSQ_ERR_SUCCESS;
}

size_t PosixMqttTransport::receive(uint8_t* buffer, size_t max_length) {
    std::lock_guard<std::mutex> lock(rx_mutex_);
    if (rx_buffer_.empty()) return 0;

    size_t to_read = std::min(max_length, rx_buffer_.size());
    std::memcpy(buffer, rx_buffer_.data(), to_read);
    
    rx_buffer_.erase(rx_buffer_.begin(), rx_buffer_.begin() + to_read);
    return to_read;
}

bool PosixMqttTransport::available() {
    std::lock_guard<std::mutex> lock(rx_mutex_);
    return !rx_buffer_.empty();
}

} // namespace micro_mcp
