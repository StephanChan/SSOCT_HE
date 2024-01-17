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
import os
import traceback

class GPUThread(QThread):
    def __init__(self):
        super().__init__()
        # self.ui = ui
        # self.queue = GPUQueue
        # self.displayQueue = DisplayQueue
        # TODO: write windowing and dispersion function
        self.test_message = 'GPU thread successfully exited'
        
        self.winfunc = cupy.ElementwiseKernel(
            'float32 x, float32 y',
            'float32 z',
            'z=x*y',
            'winfunc')
        
    def run(self):
        self.update_window()
        # self.update_FFTlength()
        self.QueueOut()
        
    def QueueOut(self):
        self.item = self.queue.get()
        while self.item.action != 'exit':
            start=time.time()
            try:
                if self.item.action == 'GPU':
                    self.cudaFFT(self.item.mode, self.item.memoryLoc, self.item.args)
                    
                elif self.item.action == 'CPU':
                    self.cpuFFT(self.item.mode, self.item.memoryLoc, self.item.args)
                elif self.item.action == 'Window':
                    self.update_window()
                else:
                    self.ui.statusbar.showMessage('GPU thread is doing something invalid '+self.item.action)
                if time.time()-start > 1:
                    print('an FFT action took ',time.time()-start,' seconds\n')
            except Exception as error:
                print("An error occurred:", error,' skip the FFT action\n')
                print(traceback.format_exc())
            self.item = self.queue.get()
        print(self.test_message)

    def cudaFFT(self, mode, memoryLoc, args):
        # get samples per Aline
        samples = self.ui.PreSamples.value()+self.ui.PostSamples.value()
        # get depth pixels after FFT
        Pixel_start = self.ui.DepthStart.value()
        Pixel_range = self.ui.DepthRange.value()
        # copy data from global memory
        data_CPU = self.Memory[memoryLoc].copy()
        # reshape data as [Alines, Samples]
        Alines =np.uint32((data_CPU.shape[1])/samples) * data_CPU.shape[0]
        data_CPU=data_CPU.reshape([Alines, samples])
        # rescale data to [0,1] range
        data_CPU=np.float32(data_CPU/65535-0.5)
        fftAxis = 1
        # # zero-padding data before FFT
        # if data_CPU.shape[1] != self.length_FFT:
        #     data_padded = np.zeros([Alines, self.length_FFT], dtype = np.float32)
        #     tmp = np.uint16((self.length_FFT-samples)/2)
        #     data_padded[:,tmp:samples+tmp] = data_CPU
        # else:
        #     data_padded = data_CPU
        # start = time.time()
        # transfer data to GPU
        data_GPU  = cupy.array(data_CPU)
        dispersion_GPU = cupy.array(self.dispersion)
        # window function and dispersion compensation
        data_GPU = self.winfunc(data_GPU, dispersion_GPU)
        # FFT
        data_GPU = cupy.fft.fft(data_GPU, axis=fftAxis)/samples
        # calculate absolute value and only keep depth range specified
        data_GPU = cupy.absolute(data_GPU[:,Pixel_start:Pixel_start+Pixel_range])
        # transfer data back to computer
        data_CPU = cupy.asnumpy(data_GPU)

        # print('FFT took ',time.time()-start,' seconds\n')
        # data_CPU = data_CPU.reshape([shape[0],Pixel_range * np.uint32(Alines/shape[0])])
        # display and save data
        an_action = DisplayAction(mode, data_CPU, args) # data in Memory[memoryLoc]
        self.displayQueue.put(an_action)
            
        
    def cpuFFT(self, mode, memoryLoc, args):

        samples = self.ui.PreSamples.value()+self.ui.PostSamples.value()
        Pixel_start = self.ui.DepthStart.value()
        Pixel_range = self.ui.DepthRange.value()
        data_CPU = self.Memory[memoryLoc].copy()
        
        Alines =np.uint32((data_CPU.shape[1])/samples) * data_CPU.shape[0]
        
        data_CPU=data_CPU.reshape([Alines, samples])
        data_CPU=np.float32(data_CPU)
        fftAxis = 1
        # if data_CPU.shape[1] != self.length_FFT:
        #     data_padded = np.zeros([Alines, self.length_FFT], dtype = np.float32)
        #     tmp = np.uint16((self.length_FFT-samples)/2)
        #     data_padded[:,tmp:samples+tmp] = data_CPU
        # else:
        #     data_padded = data_CPU
            
        data_CPU = data_CPU*self.dispersion
        data_CPU = np.abs(np.fft.fft(data_CPU, axis=fftAxis))/samples
        
        
        data_CPU = data_CPU[:,Pixel_start: Pixel_start+Pixel_range ]
        # data_CPU = data_CPU.reshape([shape[0],Pixel_range * np.uint32(Alines/shape[0])])
        an_action = DisplayAction(mode, data_CPU, args) # data in Memory[memoryLoc]
        self.displayQueue.put(an_action)
        
    def update_window(self):
        self.window = np.float32(np.hanning(self.ui.PreSamples.value()+self.ui.PostSamples.value()))
        # update dispersion and window
        dispersion_path = self.ui.Disp_DIR.toPlainText()
        if os.path.isfile(dispersion_path):
            with open(dispersion_path, "rb") as file: 
                self.dispersion = np.float32(file.read())
                file.close()
        else:
            self.dispersion = np.float32(np.ones(self.ui.PreSamples.value()+self.ui.PostSamples.value()))
            
        self.dispersion = self.dispersion * self.window
        # print('window updated\n')
        
    def update_FFTlength(self):
        self.length_FFT = 2
        while self.length_FFT < self.ui.PreSamples.value()+self.ui.PostSamples.value():
            self.length_FFT *=2
