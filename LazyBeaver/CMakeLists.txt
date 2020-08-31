cmake_minimum_required(VERSION 3.12.2)

set(CMAKE_CXX_FLAGS "-O3")

file(GLOB SOURCES "*.cpp")

add_executable(lazy_beaver_enum ${SOURCES})

target_include_directories(lazy_beaver_enum PRIVATE $ENV{OPENMPI_INC})
