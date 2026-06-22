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