cmake_minimum_required(VERSION 3.10.2)

project(BusyBeaver)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)
set(CMAKE_CXX_FLAGS "-O3 -Wall -g -Wno-sign-compare")

find_package(Boost COMPONENTS iostreams)

if (Boost_FOUND)
  message("--   Compressing TM output will be available...")
  add_compile_options("-DBOOST_FOUND")
  include_directories(${Boost_INCLUDE_DIRS})
else()
  message("--   BOOST NOT FOUND - Compressing TM output won't be available...")
endif()

# Libraries
add_library(all_libs src/util.cpp src/turing_machine.cpp src/simulator.cpp
                     src/enumerator.cpp src/lin_recur.cpp
                     src/lin_recur_enumerator.cpp
                     src/lazy_beaver_enumerator.cpp)

# Executables
add_executable(direct_sim src/direct_sim.cpp)
target_link_libraries(direct_sim PUBLIC all_libs)

add_executable(direct_sim_all src/direct_sim_all.cpp)
target_link_libraries(direct_sim_all PUBLIC all_libs)

add_executable(lin_recur src/lin_recur_main.cpp)
target_link_libraries(lin_recur PUBLIC all_libs)

add_executable(lr_check src/lr_check_main.cpp)
target_link_libraries(lr_check PUBLIC all_libs)

add_executable(lr_enum src/lr_enum.cpp)
target_link_libraries(lr_enum PUBLIC all_libs ${Boost_LIBRARIES})

add_executable(lr_enum_continue src/lr_enum_continue.cpp)
target_link_libraries(lr_enum_continue PUBLIC all_libs ${Boost_LIBRARIES})

# Lazy Beaver
add_executable(lb_enum src/lb_enum.cpp)
target_link_libraries(lb_enum PUBLIC all_libs)
target_include_directories(lb_enum PRIVATE $ENV{MPI_INC})

add_executable(lb_enum_continue src/lb_enum_continue.cpp)
target_link_libraries(lb_enum_continue PUBLIC all_libs)
