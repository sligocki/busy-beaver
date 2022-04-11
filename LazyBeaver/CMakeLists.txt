cmake_minimum_required(VERSION 3.10.2)

project(LazyBeaver)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)
set(CMAKE_CXX_FLAGS "-O3 -Wall -g")

# Libraries
add_library(all_libs util.cpp turing_machine.cpp enumeration.cpp)

# Executables
add_executable(lazy_beaver_enum lazy_beaver_enum.cpp)
target_link_libraries(lazy_beaver_enum PUBLIC all_libs)
target_include_directories(lazy_beaver_enum PRIVATE $ENV{MPI_INC})

add_executable(continue_enum continue_enum.cpp)
target_link_libraries(continue_enum PUBLIC all_libs)

add_executable(direct_sim direct_sim.cpp)
target_link_libraries(direct_sim PUBLIC all_libs)
