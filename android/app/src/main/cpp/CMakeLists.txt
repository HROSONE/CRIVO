# Motor do CRIVO em C (motor_crivo.c): a mesma conta do NumPy, com os pesos em int8 na memória e vários núcleos.
cmake_minimum_required(VERSION 3.22.1)
project(crivo_motor C)
add_library(crivo_motor SHARED motor_crivo.c)
target_compile_options(crivo_motor PRIVATE -O3 -fopenmp)
# OpenMP estático: o app não depende de nenhuma biblioteca extra no aparelho.
target_link_options(crivo_motor PRIVATE -fopenmp -static-openmp)
target_link_libraries(crivo_motor m)
