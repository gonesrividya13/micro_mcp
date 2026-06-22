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

#include "micro_mcp/transport/posix_tcp_transport.h"
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <fcntl.h>
#include <iostream>
#include <string.h>

namespace micro_mcp {

PosixTcpTransport::PosixTcpTransport(uint16_t port) : port_(port), server_fd_(-1), client_fd_(-1) {}

PosixTcpTransport::~PosixTcpTransport() {
    if (client_fd_ != -1) close(client_fd_);
    if (server_fd_ != -1) close(server_fd_);
}

bool PosixTcpTransport::begin() {
    server_fd_ = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd_ < 0) return false;

    int opt = 1;
    setsockopt(server_fd_, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    struct sockaddr_in addr;
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port = htons(port_);

    if (bind(server_fd_, (struct sockaddr*)&addr, sizeof(addr)) < 0) return false;
    if (listen(server_fd_, 1) < 0) return false;

    // Set non-blocking
    int flags = fcntl(server_fd_, F_GETFL, 0);
    fcntl(server_fd_, F_SETFL, flags | O_NONBLOCK);

    return true;
}

void PosixTcpTransport::accept_client() {
    if (client_fd_ != -1) return; // Already connected

    struct sockaddr_in client_addr;
    socklen_t client_len = sizeof(client_addr);
    int fd = accept(server_fd_, (struct sockaddr*)&client_addr, &client_len);
    
    if (fd >= 0) {
        client_fd_ = fd;
        // Set non-blocking
        int flags = fcntl(client_fd_, F_GETFL, 0);
        fcntl(client_fd_, F_SETFL, flags | O_NONBLOCK);
    }
}

bool PosixTcpTransport::send(const uint8_t* data, size_t length) {
    if (client_fd_ == -1) return false;
    ssize_t sent = ::send(client_fd_, data, length, 0);
    if (sent < 0) {
        close(client_fd_);
        client_fd_ = -1;
        return false;
    }
    return true;
}

size_t PosixTcpTransport::receive(uint8_t* buffer, size_t max_length) {
    accept_client();
    if (client_fd_ == -1) return 0;

    ssize_t bytes = ::recv(client_fd_, buffer, max_length, 0);
    if (bytes > 0) {
        return bytes;
    } else if (bytes == 0) {
        // Disconnected
        close(client_fd_);
        client_fd_ = -1;
    }
    return 0;
}

bool PosixTcpTransport::available() {
    accept_client();
    if (client_fd_ == -1) return false;

    char buf;
    ssize_t bytes = ::recv(client_fd_, &buf, 1, MSG_PEEK);
    if (bytes > 0) return true;
    if (bytes == 0) {
        close(client_fd_);
        client_fd_ = -1;
    }
    return false;
}

} // namespace micro_mcp