# -*- coding: utf-8 -*-
"""
Created on Tue Jan  2 17:31:52 2024

@author: admin
"""

# test which way is faster:
# 1. copy each buffer to a memory location, perform FFT on the current thread
# 2. copy each buffer to a memory location, queue in memory location to a thread, then perform FFT on one memory for a time
# 3. queue in buffer to a different thread, when memory location is filled up, run GPU FFT
import multiprocessing as mp
import numpy as np
import time

SAMPLES = 2048
NALINES = 2000
NBLINES = 100
a_queue = mp.Queue()

bline = np.zeros(SAMPLES * NALINES, dtype=np.uint16)
buffer = np.zeros(len(bline)*NBLINES, dtype=np.uint16)
for ii in range(NALINES):
    for jj in range(SAMPLES):
        bline[ii*SAMPLES+jj] = np.uint16((np.sin(2*np.pi*200*jj/SAMPLES)+1)/2*65535)
        
print('start copying')
start = time.time()
for ii in range(NBLINES):
    buffer[ii*SAMPLES*NALINES:(ii+1)*SAMPLES*NALINES]=bline
    
print('time elapsed for copying 200k Alines: ', time.time()-start)

print('start queue in')
start = time.time()
a_queue.put(buffer)
# buffer2 = a_queue.get()
print('time elapsed for queue in buffer: ', time.time()-start)

print('start queue out')
start = time.time()
# a_queue.put(buffer)
buffer2 = a_queue.get()
print('time elapsed for queue out buffer: ', time.time()-start)

# copy in the current thread is more than 10 times faster than acquisition, and it doesn't matter much how large is the bline
# queue in a large memory chunk is super fast
# queue out a large memory chunk is slow, only twice faster than acquisition

print('start method 3')
start = time.time()
for ii in range(NBLINES):
    a_queue.put(bline)
    bline2 = a_queue.get()
    buffer[ii*SAMPLES*NALINES:(ii+1)*SAMPLES*NALINES]=bline2
    
print('time elapsed for queue in&out 200k Alines: ', time.time()-start)

# queue in and out each bline is, not suprisingly, slow

# method 1 is best choice