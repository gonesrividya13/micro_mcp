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
#include "micro_mcp/mcp.pb.h"
#include <string>
#include <vector>
#include <functional>

namespace micro_mcp {

struct ToolDefinition {
    std::string name;
    std::string description;
    std::string input_schema_json;
    std::function<std::string(const std::string&)> handler;
};

struct ResourceDefinition {
    std::string uri;
    std::string name;
    std::string description;
    std::string mime_type;
    std::function<std::string()> handler;
};

class Server {
public:
    Server(const std::string& name, const std::string& version);
    ~Server() = default;

    void set_transport(Transport* transport);
    
    void register_tool(const std::string& name, const std::string& description, const std::string& input_schema_json, std::function<std::string(const std::string&)> handler);
    void register_resource(const std::string& uri, const std::string& name, const std::string& description, const std::string& mime_type, std::function<std::string()> handler);

    void poll();

private:
    std::string name_;
    std::string version_;
    Transport* transport_;
    
    std::vector<ToolDefinition> tools_;
    std::vector<ResourceDefinition> resources_;

    std::vector<uint8_t> rx_buffer_;

    void process_message(const micro_mcp_McpMessage& msg);
    void send_message(const micro_mcp_McpMessage& msg);
    
    void handle_init(const micro_mcp_McpMessage& req);
    void handle_list_tools(const micro_mcp_McpMessage& req);
    void handle_call_tool(const micro_mcp_McpMessage& req);
    void handle_list_resources(const micro_mcp_McpMessage& req);
    void handle_read_resource(const micro_mcp_McpMessage& req);
    void send_error(int32_t id, const std::string& message);
};

} // namespace micro_mcp