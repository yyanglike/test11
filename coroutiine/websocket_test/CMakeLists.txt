cmake_minimum_required(VERSION 3.10)
project(TcpClient)

set(CMAKE_CXX_STANDARD 14)

include(FetchContent)

FetchContent_Declare(
  libuv
  GIT_REPOSITORY https://github.com/libuv/libuv.git
  GIT_TAG        v1.x
)

FetchContent_GetProperties(libuv)
if(NOT libuv_POPULATED)
  FetchContent_Populate(libuv)
  add_subdirectory(${libuv_SOURCE_DIR} ${libuv_BINARY_DIR} EXCLUDE_FROM_ALL)
endif()

add_executable(TcpClient a.cpp)
target_link_libraries(TcpClient uv_a)

add_executable(s s.cpp)
target_link_libraries(s uv_a)