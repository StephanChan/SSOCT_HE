# -*- coding: utf-8 -*-
"""
Created on Sat Jan 11 15:40:12 2025

@author: admin
"""

import numpy as np
import time
from time import process_time
import cupy as cp
import matplotlib.pyplot as plt

# read interpolation configs
def find_interp_indice(x,xp):
    indice=np.zeros([len(x),2], dtype = np.uint16)
    # for x that is ramping up, interpolate from first to last element of xp
    if x[-1]>x[0]:
        start = 0
        stride = 1
        end_= len(x)
    # for x that is ramping down, interpolate from last to first element of xp
    else:
        start=len(x)-1
        stride = -1
        end_= 0
    # if the first x value is unchanged
    if xp[start]<=x[start]:
        indice[start,0] = start+stride
        indice[start,1] = start
        start = start+stride
    # do interpolation
    for ii in np.arange(start, end_, stride):
        xt = xp[ii]
        while xt>x[start]:
            start=start+stride
        indice[ii,0] = start-stride
        indice[ii,1] = start
    return indice

# define interpolation kernel
interp_kernel = cp.RawKernel(r'''
extern "C" __global__
void interp1d(long long NAlines, long long NSamples, float* x, float* xp, float* y, unsigned short* indice1, unsigned short* indice2, float* yp){
    const int blockID = blockIdx.x + blockIdx.y * gridDim.x;
    const int threadID = blockID * (blockDim.x * blockDim.y) + threadIdx.y * blockDim.x + threadIdx.x;
    const int numThreads = blockDim.x * blockDim.y * gridDim.x * gridDim.y;
    
    long long int i;
    for(i=threadID; i<NAlines * NSamples; i += numThreads){
            int sampx = i%NSamples;
            long long int sampy0 = i / NSamples * NSamples;
            float xt = xp[sampx];
            float x0 = x[indice1[sampx]];
            float x1 = x[indice2[sampx]];
            float y0 = y[sampy0+indice1[sampx]];
            float y1 = y[sampy0+indice2[sampx]];
            //if (i==100000){
            //        printf("sampx is %d, sampy0 is %llu\n",sampx, sampy0);
            //        printf("indice1 is %hu, indice2 is %hu\n", indice1[sampx], indice2[sampx]);    
            //        printf("xt: %.5f, x0: %.5f, x1: %.5f, y0: %.5f, y1: %.5f\n",xt,x0,x1,y0,y1);
            //        }

            yp[i] = y0+(xt-x0)*(y1-y0)/(x1-x0);
            }
    }
''','interp1d')

#%%
# init X
nSamp = 1024
nFFT = 500*1200
intDk = -0.31
# init raw data
k = np.linspace(1+intDk/2, 1-intDk/2, nSamp);
x = 1./np.fliplr(k.reshape(1,nSamp))
x=x.reshape(nSamp)
x=x.astype(np.float32)
xp = np.linspace(np.min(x), np.max(x),nSamp).astype(np.float32)
indice = find_interp_indice(x, xp)

# init Y
y = np.float32(np.sin(200*np.pi*x))
y = np.float32(np.tile(y,[nFFT,1]))
noise = np.random.rand(nFFT,nSamp)*0.1
y0 = np.float32(y + noise)
#%%
# pass data to GPU
t1=time.time()
# y=y0-np.mean(y0,0)
y = y0
y = y.reshape([nFFT*nSamp])

x_gpu  = cp.array(x)
xp_gpu  = cp.array(xp)
y_gpu  = cp.array(y)
indice1 = cp.array(indice[:,0])
indice2 = cp.array(indice[:,1])
yp_gpu = cp.zeros(y.shape, dtype = cp.float32)
print('data to gpu takes ', round(time.time()-t1,3))

# interpolation
t2 = time.time() 
interp_kernel((8,8),(16,16), (nFFT, nSamp, x_gpu, xp_gpu, y_gpu, indice1, indice2, yp_gpu))
print('time for interpolation: ', round(time.time()-t2,5))
# yp = cp.asnumpy(yp_gpu)
# yp=yp.reshape([nFFT, nSamp])
# plt.figure()
# plt.plot(x,y[0:nSamp],xp,yp[0,:])
################################################################################# FFT
t3=time.time()
data_gpu  = cp.fft.fft(cp.reshape(yp_gpu,[nFFT, nSamp]), axis=1)
data_gpu = cp.absolute(data_gpu[:,0:300])
results = cp.asnumpy(data_gpu)
print('time for FFT: ', round(time.time()-t3,5))
# yp = cp.asnumpy(data_gpu)
print('total time: ', round(time.time()-t1,5))

# plt.figure()
# plt.plot(results[0,:])