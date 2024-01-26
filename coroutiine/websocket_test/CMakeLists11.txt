cmake_minimum_required(VERSION 3.10)
project(WebSocketCoroutine)

set(CMAKE_CXX_STANDARD 14)

find_package(Boost REQUIRED COMPONENTS coroutine system thread)
find_package(websocketpp CONFIG REQUIRED)

include_directories(${Boost_INCLUDE_DIRS})

add_executable(WebSocketCoroutine main.cpp)

target_link_libraries(WebSocketCoroutine PRIVATE websocketpp::websocketpp ${Boost_LIBRARIES})
