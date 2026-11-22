# Motor do CRIVO em C (motor_crivo.c): a mesma conta do NumPy, com os pesos em int8 na memória e vários núcleos.
cmake_minimum_required(VERSION 3.22.1)
project(crivo_motor C)
add_library(crivo_motor SHARED motor_crivo.c)
# Threads simples do sistema (pthreads, que o Android já tem); -fopenmp-simd só vetoriza as somas, sem biblioteca
# de OpenMP: o OpenMP estático dentro de uma biblioteca aberta pelo Python é um gatilho conhecido de queda no Android.
target_compile_options(crivo_motor PRIVATE -O3 -fopenmp-simd)
target_link_libraries(crivo_motor m)
