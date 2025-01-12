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
nSamp = 2048
nFFT = 500*1000
# init raw data
x = 500*np.arange(nSamp)/nSamp
xp = np.arange(x[1],x[-1],(x[-1]-x[1])/nSamp)

data = np.sin(2*np.pi*x)
data = np.float32(np.tile(data,[nFFT,1]))
noise = np.random.rand(nFFT,nSamp)*0.1
data = np.float32(data + noise)

window = np.complex64(np.hanning(nSamp))
# define CUDA kernel that calculate the product of two arrays
winfunc = cp.ElementwiseKernel(
    'float32 x, complex64 y',
    'complex64 z',
    'z=x*y',
    'winfunc')

fftAxis = 1
from scipy.interpolate import interp1d

# calculate and time NumPy FFT, i.e., performming FFT using CPU
# t0 = time.time()
# data_cpu = data*np.transpose(window)
# t1 = time.time()
# f = interp1d(x,data_cpu,axis = 1)
# data2 = f(xp)
# t2 = time.time()
# data_cpu     = np.fft.fft(data, axis=fftAxis)
# t3 = time.time()
# print('\n CPU windowing time is: ',t1-t0)
# print('\n CPU interpolation time is: ',t2-t1)
# print('\n CPU FFT time is: ',t3-t2)

# calculate and time GPU FFT

##
data = np.float32(data + noise)
t1 = time.time()

# t1 = process_time()
# transfer input data to Device
# mempool= cp.get_default_memory_pool()
data_gpu  = cp.array(data)
window_gpu = cp.array(window)
# calculate array product
t2 = time.time()
tp1 = process_time()
data_gpu = winfunc(data_gpu, window_gpu)
tp2 = process_time()
t3 = time.time()

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
t4 = time.time()

# calculate absolute value of the complex FFT results, and only save the first 200 elements
data_gpu = cp.absolute(data_gpu[:,0:200])
# data_o_gpu.astype(cp.float32)

# t4 = process_time()
# print('\n fft time is: ',(t4-t3)/1.0)
# cp.cuda.Device().synchronize()
# t5 = process_time()
# transfer data back from GPU to CPU
results = cp.asnumpy(data_gpu)
t5 = time.time()
# t6 = process_time()
# print('\n device to host time is: ',(t6-t5)/1.0)
# cache.clear()
print('data 2 GPU takes  ',round(t2-t1,3),' sec')
print('windowing takes ',round(t3-t2,5),' sec')
print('windowing takes ',round(tp2-tp1,5),' sec')
print('FFT takes ',round(t4-t3,5),' sec')
print('data 2 CPU takes  ',round(t5-t4,3),' sec')
print('\n GPU total time is: ',t5-t1)
# plt.figure()
# plt.plot(results[1][:])
# print(mempool.used_bytes())