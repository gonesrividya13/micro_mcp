cmake_minimum_required(VERSION 3.10)
project(micro_mcp)

set(CMAKE_CXX_STANDARD 11)

include(FetchContent)
FetchContent_Declare(
    nanopb
    GIT_REPOSITORY https://github.com/nanopb/nanopb.git
    GIT_TAG        nanopb-0.4.8
)
FetchContent_MakeAvailable(nanopb)

include_directories(include)
include_directories(src)
include_directories(${nanopb_SOURCE_DIR})

add_library(micro_mcp STATIC
    src/server.cpp
    src/posix_tcp_transport.cpp
    src/mcp.pb.c
)

target_link_libraries(micro_mcp protobuf-nanopb-static)

add_executable(example_device examples/device.cpp)
target_link_libraries(example_device micro_mcp)
