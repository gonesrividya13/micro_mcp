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

#include "micro_mcp/server.h"
#include <pb_encode.h>
#include <pb_decode.h>
#include <iostream>
#include <string.h>

namespace micro_mcp {

Server::Server(const std::string& name, const std::string& version) 
    : name_(name), version_(version), transport_(nullptr) {}

void Server::set_transport(Transport* transport) {
    transport_ = transport;
}

void Server::register_tool(const std::string& name, const std::string& description, const std::string& input_schema_json, std::function<std::string(const std::string&)> handler) {
    tools_.push_back({name, description, input_schema_json, handler});
}

void Server::register_resource(const std::string& uri, const std::string& name, const std::string& description, const std::string& mime_type, std::function<std::string()> handler) {
    resources_.push_back({uri, name, description, mime_type, handler});
}

void Server::poll() {
    if (!transport_ || !transport_->available()) return;

    uint8_t buf[256];
    size_t bytes = transport_->receive(buf, sizeof(buf));
    if (bytes > 0) {
        rx_buffer_.insert(rx_buffer_.end(), buf, buf + bytes);
    }

    // Process framed messages (2-byte length prefix)
    while (rx_buffer_.size() >= 2) {
        uint16_t length = (rx_buffer_[0] << 8) | rx_buffer_[1];
        if (rx_buffer_.size() >= 2 + length) {
            // We have a full message
            micro_mcp_McpMessage msg = micro_mcp_McpMessage_init_zero;
            pb_istream_t stream = pb_istream_from_buffer(rx_buffer_.data() + 2, length);
            
            if (pb_decode(&stream, micro_mcp_McpMessage_fields, &msg)) {
                process_message(msg);
            } else {
                std::cerr << "Failed to decode protobuf message" << std::endl;
            }

            // Erase processed message
            rx_buffer_.erase(rx_buffer_.begin(), rx_buffer_.begin() + 2 + length);
        } else {
            break; // Not enough data
        }
    }
}

void Server::send_message(const micro_mcp_McpMessage& msg) {
    if (!transport_) return;

    uint8_t buffer[512];
    pb_ostream_t stream = pb_ostream_from_buffer(buffer + 2, sizeof(buffer) - 2);
    
    if (!pb_encode(&stream, micro_mcp_McpMessage_fields, &msg)) {
        std::cerr << "Failed to encode protobuf message" << std::endl;
        return;
    }

    size_t length = stream.bytes_written;
    buffer[0] = (length >> 8) & 0xFF;
    buffer[1] = length & 0xFF;

    transport_->send(buffer, length + 2);
}

void Server::send_error(int32_t id, const std::string& message) {
    micro_mcp_McpMessage res = micro_mcp_McpMessage_init_zero;
    res.id = id;
    res.which_message_type = micro_mcp_McpMessage_error_message_tag;
    strncpy(res.message_type.error_message, message.c_str(), sizeof(res.message_type.error_message) - 1);
    send_message(res);
}

void Server::process_message(const micro_mcp_McpMessage& msg) {
    switch (msg.which_message_type) {
        case micro_mcp_McpMessage_init_req_tag:
            handle_init(msg);
            break;
        case micro_mcp_McpMessage_list_tools_req_tag:
            handle_list_tools(msg);
            break;
        case micro_mcp_McpMessage_call_tool_req_tag:
            handle_call_tool(msg);
            break;
        case micro_mcp_McpMessage_list_resources_req_tag:
            handle_list_resources(msg);
            break;
        case micro_mcp_McpMessage_read_resource_req_tag:
            handle_read_resource(msg);
            break;
        default:
            send_error(msg.id, "Unsupported message type");
            break;
    }
}

void Server::handle_init(const micro_mcp_McpMessage& req) {
    micro_mcp_McpMessage res = micro_mcp_McpMessage_init_zero;
    res.id = req.id;
    res.which_message_type = micro_mcp_McpMessage_init_res_tag;
    strncpy(res.message_type.init_res.protocol_version, req.message_type.init_req.protocol_version, sizeof(res.message_type.init_res.protocol_version) - 1);
    strncpy(res.message_type.init_res.server_name, name_.c_str(), sizeof(res.message_type.init_res.server_name) - 1);
    strncpy(res.message_type.init_res.server_version, version_.c_str(), sizeof(res.message_type.init_res.server_version) - 1);
    send_message(res);
}

void Server::handle_list_tools(const micro_mcp_McpMessage& req) {
    micro_mcp_McpMessage res = micro_mcp_McpMessage_init_zero;
    res.id = req.id;
    res.which_message_type = micro_mcp_McpMessage_list_tools_res_tag;
    
    res.message_type.list_tools_res.tools_count = std::min(tools_.size(), (size_t)10);
    for (size_t i = 0; i < res.message_type.list_tools_res.tools_count; ++i) {
        strncpy(res.message_type.list_tools_res.tools[i].name, tools_[i].name.c_str(), sizeof(res.message_type.list_tools_res.tools[i].name) - 1);
        strncpy(res.message_type.list_tools_res.tools[i].description, tools_[i].description.c_str(), sizeof(res.message_type.list_tools_res.tools[i].description) - 1);
        strncpy(res.message_type.list_tools_res.tools[i].input_schema_json, tools_[i].input_schema_json.c_str(), sizeof(res.message_type.list_tools_res.tools[i].input_schema_json) - 1);
    }
    
    send_message(res);
}

void Server::handle_call_tool(const micro_mcp_McpMessage& req) {
    std::string target_name = req.message_type.call_tool_req.name;
    
    for (const auto& tool : tools_) {
        if (tool.name == target_name) {
            std::string result = tool.handler(req.message_type.call_tool_req.arguments_json);
            
            micro_mcp_McpMessage res = micro_mcp_McpMessage_init_zero;
            res.id = req.id;
            res.which_message_type = micro_mcp_McpMessage_call_tool_res_tag;
            res.message_type.call_tool_res.is_error = false;
            strncpy(res.message_type.call_tool_res.content_text, result.c_str(), sizeof(res.message_type.call_tool_res.content_text) - 1);
            
            send_message(res);
            return;
        }
    }
    
    send_error(req.id, "Tool not found");
}

void Server::handle_list_resources(const micro_mcp_McpMessage& req) {
    micro_mcp_McpMessage res = micro_mcp_McpMessage_init_zero;
    res.id = req.id;
    res.which_message_type = micro_mcp_McpMessage_list_resources_res_tag;
    
    res.message_type.list_resources_res.resources_count = std::min(resources_.size(), (size_t)10);
    for (size_t i = 0; i < res.message_type.list_resources_res.resources_count; ++i) {
        strncpy(res.message_type.list_resources_res.resources[i].uri, resources_[i].uri.c_str(), sizeof(res.message_type.list_resources_res.resources[i].uri) - 1);
        strncpy(res.message_type.list_resources_res.resources[i].name, resources_[i].name.c_str(), sizeof(res.message_type.list_resources_res.resources[i].name) - 1);
        strncpy(res.message_type.list_resources_res.resources[i].description, resources_[i].description.c_str(), sizeof(res.message_type.list_resources_res.resources[i].description) - 1);
        strncpy(res.message_type.list_resources_res.resources[i].mime_type, resources_[i].mime_type.c_str(), sizeof(res.message_type.list_resources_res.resources[i].mime_type) - 1);
    }
    
    send_message(res);
}

void Server::handle_read_resource(const micro_mcp_McpMessage& req) {
    std::string target_uri = req.message_type.read_resource_req.uri;
    
    for (const auto& res_def : resources_) {
        if (res_def.uri == target_uri) {
            std::string content = res_def.handler();
            
            micro_mcp_McpMessage res = micro_mcp_McpMessage_init_zero;
            res.id = req.id;
            res.which_message_type = micro_mcp_McpMessage_read_resource_res_tag;
            strncpy(res.message_type.read_resource_res.contents_text, content.c_str(), sizeof(res.message_type.read_resource_res.contents_text) - 1);
            
            send_message(res);
            return;
        }
    }
    
    send_error(req.id, "Resource not found");
}

} // namespace micro_mcp
