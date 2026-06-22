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