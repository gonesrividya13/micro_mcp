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
#include <stdint.h>
#include <vector>

namespace micro_mcp {

class PosixTcpTransport : public Transport {
public:
    PosixTcpTransport(uint16_t port);
    ~PosixTcpTransport() override;

    bool begin() override;
    bool send(const uint8_t* data, size_t length) override;
    size_t receive(uint8_t* buffer, size_t max_length) override;
    bool available() override;

private:
    uint16_t port_;
    int server_fd_;
    int client_fd_;

    void accept_client();
};

} // namespace micro_mcp