# -*- coding: utf-8 -*-
"""
Created on Thu Jan  4 14:14:57 2024

@author: admin
"""

import ctypes
import sys
import os
import numpy as np
from numpy.ctypeslib import ndpointer
# os.add_dll_directory('C:\\Users\\admin\\source\\repos\\Project1\\x64\\Debug')
# os.add_dll_directory('C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v12.3\\include')
sys.path.append('C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v12.3\\include')
sys.path.append('D:\\SSOCT_HE\\CUDA_code\\CUDA_OCT_1Ch_amp\\x64\\Debug')
sys.path.append('D:\\SSOCT_HE\\cuda-samples\\cuda-samples-master\\Common')
CFFT = ctypes.cdll.LoadLibrary("D:\\SSOCT_HE\\CUDA_code\\CUDA_OCT_1Ch_amp\\x64\\Debug\\CUDA_OCT_1Ch_amp.dll")


CFFT.OCT_FFT.argtypes = [ndpointer(dtype=ctypes.c_uint16), \
                         ndpointer(dtype=ctypes.c_uint16), \
                         ndpointer(dtype=ctypes.c_float), \
                         ndpointer(dtype=ctypes.c_float), \
                          ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32
                          ]

data = np.zeros(1000*1024,dtype = np.uint16)
for i in range(1000):
	for j in range(1024):
		data[i*1024 + j] = (np.sin(2 * np.pi * 100 * j / 1024 + np.pi/ 6) + 1) / 2 * 65535

processed_data = np.zeros(1000*1024,dtype = np.uint16)

dispersion = np.ones(2048,dtype = np.float32)
hann = np.ones(1024,dtype = np.float32)
z0=ctypes.c_uint32(1)
Depth = ctypes.c_uint32(200)
NALINES = ctypes.c_uint32(1000)
SAMPLES = ctypes.c_uint32(1024)

print(CFFT.OCT_FFT(data,processed_data,dispersion,hann,z0, Depth, NALINES,SAMPLES))
