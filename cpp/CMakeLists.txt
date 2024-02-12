cmake_minimum_required(VERSION 3.10)
project(StockFormulaCalculator)

set(CMAKE_CXX_STANDARD 14)

find_package(Boost 1.58.0 REQUIRED COMPONENTS system)

include_directories(${Boost_INCLUDE_DIRS})

add_executable(StockFormulaCalculator main.cpp)

target_link_libraries(StockFormulaCalculator ${Boost_LIBRARIES})
