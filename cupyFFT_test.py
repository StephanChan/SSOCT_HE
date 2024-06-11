# -*- coding: utf-8 -*-
"""
Created on Sun Jan  7 15:35:03 2024

@author: admin
"""
import numpy as np
import time
from time import process_time
import cupy as cp
import matplotlib.pyplot as plt

# define number of samples per FFT and total number of FFTs
nSamp = 1440
nFFT = 300000
# init raw data
data = np.sin(2*np.pi*np.random.randint(10,90)*np.arange(nSamp)/nSamp)
data = np.float32(np.tile(data,[nFFT,1]))
window = np.complex64(np.hanning(nSamp))
# define CUDA kernel that calculate the product of two arrays
winfunc = cp.ElementwiseKernel(
    'float32 x, complex64 y',
    'complex64 z',
    'z=x*y',
    'winfunc')

fftAxis = 1

# calculate and time NumPy FFT, i.e., performming FFT using CPU
t1 = time.time()
data_cpu     = np.fft.fft(data, axis=fftAxis)
t2 = time.time()
print('\n CPU NumPy time is: ',t2-t1)

# calculate and time GPU FFT
start = time.time()
# t1 = process_time()
# transfer input data to Device
# mempool= cp.get_default_memory_pool()
data_gpu  = cp.array(data)
window_gpu = cp.array(window)
# calculate array product
data_gpu = winfunc(data_gpu, window_gpu)
# results = cp.asnumpy(data_gpu)
# results_CPU = data*window
# data_o_gpu = cp.ndarray([data.shape[0], data.shape[1]], dtype=np.complex64)
# data_o_gpu2 = cp.ndarray([data.shape[0], 200], dtype=np.complex64)
# data_o_gpu3 = cp.ndarray([data.shape[0], 200], dtype=np.float32)
# print(mempool.used_bytes())

# cache = cp.fft.config.get_plan_cache()
# cache.set_size(4)
# t2 = process_time()
# print('\n host to device time is: ',(t2-t1)/1.0)
# t3 = process_time()

# performing FFT on GPU
try:
    data_gpu  = cp.fft.fft(data_gpu, axis=fftAxis)
except:
    print('memory overflow, restart program')
# calculate absolute value of the complex FFT results, and only save the first 200 elements
data_gpu = cp.absolute(data_gpu[:,0:200])
# data_o_gpu.astype(cp.float32)

# t4 = process_time()
# print('\n fft time is: ',(t4-t3)/1.0)
# cp.cuda.Device().synchronize()
# t5 = process_time()
# transfer data back from GPU to CPU
results = cp.asnumpy(data_gpu)
# t6 = process_time()
# print('\n device to host time is: ',(t6-t5)/1.0)
# cache.clear()
print('\n GPU total time is: ',time.time()-start)
# plt.figure()
# plt.plot(results[1][:])
# print(mempool.used_bytes())