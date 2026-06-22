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
#include <stdint.h>
#include <stddef.h>
#include <vector>

namespace micro_mcp {

class Transport {
public:
    virtual ~Transport() = default;

    // Initialize the transport
    virtual bool begin() = 0;

    // Send data over the transport
    virtual bool send(const uint8_t* data, size_t length) = 0;

    // Receive data from the transport
    // Should return the number of bytes read, or 0 if no data
    virtual size_t receive(uint8_t* buffer, size_t max_length) = 0;

    // Check if there is data available to read
    virtual bool available() = 0;
};

} // namespace micro_mcp