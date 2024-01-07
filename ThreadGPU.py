# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 16:50:25 2023

@author: admin
"""
from PyQt5.QtCore import  QThread
import time
import cupy
import numpy as np
from Actions import DisplayAction

class GPUThread(QThread):
    def __init__(self):
        super().__init__()
        # self.ui = ui
        # self.queue = GPUQueue
        # self.displayQueue = DisplayQueue
        self.test_message = 'GPU thread successfully exited'
        
    def run(self):
        self.QueueOut()
        
    def QueueOut(self):
        self.item = self.queue.get()
        while self.item.action != 'exit':
            start=time.time()
            if self.item.action == 'GPU':
                self.cudaFFT(self.item.mode, self.item.memoryLoc, self.item.args)
                
            elif self.item.action == 'CPU':
                self.cpuFFT(self.item.mode, self.item.memoryLoc, self.item.args)
            else:
                self.ui.statusbar.showMessage('GPU thread is doing something invalid '+self.item.action)
            print('an FFT action took ',time.time()-start,' seconds\n')
            self.item = self.queue.get()
        print(self.test_message)

    def cudaFFT(self, mode, memoryLoc, args):
        samples = self.ui.PreSamples.value()+self.ui.PostSamples.value()
        Pixel_start = self.ui.DepthStart.value()
        Pixel_range = self.ui.DepthRange.value()
        
        Alines =np.uint32((self.Memory[memoryLoc].shape[1])/samples) * self.Memory[memoryLoc].shape[0]
        data_CPU = self.Memory[memoryLoc].copy()
        shape = np.array(data_CPU.shape)
        data_CPU=data_CPU.reshape([Alines, samples])
        data_CPU=np.float32(data_CPU)
        fftAxis = 1
        # print('data size: ',data_CPU.shape)
        
        # start = time.time()
        data_GPU  = cupy.array(data_CPU)
        try:
            data_GPU = cupy.fft.fft(data_GPU, axis=fftAxis)
    
            data_GPU = cupy.absolute(data_GPU[:,Pixel_start:Pixel_start+Pixel_range])
            data_CPU = cupy.asnumpy(data_GPU)
            # print('FFT took ',time.time()-start,' seconds\n')
            data_CPU = data_CPU.reshape([shape[0],Pixel_range * np.uint32(Alines/shape[0])])
            an_action = DisplayAction(mode, data_CPU, args) # data in Memory[memoryLoc]
            self.displayQueue.put(an_action)
        except:
            self.ui.statusbar.showMessage('GPU memory overflow, kill current console to restart')
            
        
    def cpuFFT(self, mode, memoryLoc, args):

        samples = self.ui.PreSamples.value()+self.ui.PostSamples.value()
        Pixel_start = self.ui.DepthStart.value()
        Pixel_range = self.ui.DepthRange.value()
        
        Alines =np.uint32((self.Memory[memoryLoc].shape[1])/samples) * self.Memory[memoryLoc].shape[0]
        data_CPU = self.Memory[memoryLoc].copy()
        shape = np.array(data_CPU.shape)
        data_CPU=data_CPU.reshape([Alines, samples])
        data_CPU=np.float32(data_CPU)
        fftAxis = 1
        data_CPU = np.abs(np.fft.fft(data_CPU, axis=fftAxis))
        
        
        data_CPU = data_CPU[:,Pixel_start: Pixel_start+Pixel_range ]
        data_CPU = data_CPU.reshape([shape[0],Pixel_range * np.uint32(Alines/shape[0])])
        an_action = DisplayAction(mode, data_CPU, args) # data in Memory[memoryLoc]
        self.displayQueue.put(an_action)