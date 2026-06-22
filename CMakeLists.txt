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

option(USE_MOSQUITTO "Build POSIX MQTT transport using libmosquitto" OFF)

set(SRC_FILES
    src/server.cpp
    src/posix_tcp_transport.cpp
    src/mcp.pb.c
)

if(USE_MOSQUITTO)
    list(APPEND SRC_FILES src/posix_mqtt_transport.cpp)
endif()

add_library(micro_mcp STATIC ${SRC_FILES})
target_link_libraries(micro_mcp protobuf-nanopb-static)

if(USE_MOSQUITTO)
    find_package(PkgConfig REQUIRED)
    pkg_check_modules(MOSQUITTO REQUIRED libmosquitto)
    target_include_directories(micro_mcp PRIVATE ${MOSQUITTO_INCLUDE_DIRS})
    target_link_libraries(micro_mcp ${MOSQUITTO_LIBRARIES})
    
    add_executable(example_device_mqtt examples/device_mqtt.cpp)
    target_link_libraries(example_device_mqtt micro_mcp)
endif()

add_executable(example_device examples/device.cpp)
target_link_libraries(example_device micro_mcp)
