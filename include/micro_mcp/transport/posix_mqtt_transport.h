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
