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

nSamp = 1024
nAline = 2000

# data = np.zeros(nSamp,dtype = np.float32)
# for j in range(nSamp):
#     data[j] = np.sin(2 * np.pi * 110 * j / nSamp + np.pi/ 6) 

data = np.sin(2*np.pi*80*np.arange(nSamp)/nSamp)
data = np.tile(data,[nAline,1])
print(data.shape)

print('\nstart fft')
fftAxis = 1
# calculate and time NumPy FFT
# t1 = time.time()
# dataFft     = np.fft.fft(data, axis=fftAxis)
# t2 = time.time()
# print('\nCPU NumPy time is: ',t2-t1)

# calculate and time GPU FFT
start = time.time()
t1 = process_time()
# transfer input data to Device

# mempool= cp.get_default_memory_pool()
data_t_gpu  = cp.array(data)
# data_o_gpu = cp.ndarray([data.shape[0], data.shape[1]], dtype=np.complex64)
# data_o_gpu2 = cp.ndarray([data.shape[0], 200], dtype=np.complex64)
# data_o_gpu3 = cp.ndarray([data.shape[0], 200], dtype=np.float32)
# print(mempool.used_bytes())

# cache = cp.fft.config.get_plan_cache()
# cache.set_size(4)
# cp.cuda.set_allocator(None)
t2 = process_time()
print('\n host to device time is: ',(t2-t1)/1.0)

# data_o1_gpu  = cp.fft.fft(data_t_gpu, axis=fftAxis)
# cp.cuda.Device().synchronize()
t3 = process_time()

try:
    data_t_gpu  = cp.fft.fft(data_t_gpu, axis=fftAxis)
except:
    print('memory overflow, restart program')
# data_o_gpu2 = data_o_gpu[:,0:200]
# data_o_gpu3 = cp.absolute(data_o_gpu2)
# data_o_gpu3 = cp.absolute(data_o_gpu[:,0:200])
data_t_gpu = cp.absolute(data_t_gpu[:,0:200])
# data_o_gpu.astype(cp.float32)

t4 = process_time()
print('\n fft time is: ',(t4-t3)/1.0)
# cp.cuda.Device().synchronize()
t5 = process_time()

results = cp.asnumpy(data_t_gpu)
t6 = process_time()
print('\n device to host time is: ',(t6-t5)/1.0)
    # data_t_gpu = cp.ndarray([])
    # data_o_gpu = cp.ndarray([])
    # mempool.free_all_blocks()
# cache.clear()
print('\n total time is: ',time.time()-start)
plt.figure()
plt.plot(results[1][:])
# print(mempool.used_bytes())