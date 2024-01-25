# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 16:50:25 2023

@author: admin
"""
from PyQt5.QtCore import  QThread
import time
import cupy
import numpy as np
from Actions import DnSAction
import os
import traceback

class GPUThread(QThread):
    def __init__(self):
        super().__init__()
        # self.ui = ui
        # self.queue = GPUQueue
        # self.displayQueue = DisplayQueue
        # TODO: write windowing and dispersion function
        self.exit_message = 'GPU thread successfully exited\n'
        
        self.winfunc = cupy.ElementwiseKernel(
            'float32 x, complex64 y',
            'complex64 z',
            'z=x*y',
            'winfunc')
        
    def run(self):
        self.update_Dispersion()
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
                elif self.item.action == 'update_Dispersion':
                    self.update_Dispersion()
                else:
                    self.ui.statusbar.showMessage('GPU thread is doing something invalid '+self.item.action)
                if time.time()-start > 1:
                    print('an FFT action took ',time.time()-start,' seconds\n')
            except Exception as error:
                print("An error occurred:", error,' skip the FFT action\n')
                print(traceback.format_exc())
            self.item = self.queue.get()
        print(self.exit_message)

    def cudaFFT(self, mode, memoryLoc, args):
        # get samples per Aline
        if self.Digitizer == 'ATS9351':
            samples = self.ui.PreSamples.value()+self.ui.PostSamples.value()
        elif self.Digitizer == 'ART8912':
            samples = self.ui.PostSamples_2.value()
        # get depth pixels after FFT
        Pixel_start = self.ui.DepthStart.value()
        Pixel_range = self.ui.DepthRange.value()
        # copy data from global memory
        data_CPU = self.Memory[memoryLoc].copy()
        # reshape data as [Alines, Samples]
        Alines =np.uint32((data_CPU.shape[1])/samples) * data_CPU.shape[0]
        data_CPU=data_CPU.reshape([Alines, samples])
        # rescale data to [0,1] range
        if self.Digitizer == 'ATS9351':
            data_CPU=np.float32(data_CPU/65535-0.5)
        elif self.Digitizer == 'ART8912':
            data_CPU=np.float32(data_CPU/4095-0.5)
        
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
        
        ############### debug dispersion compensation
        # data_CPU = cupy.asnumpy(data_GPU)
        # tmp = 
        
        
        # FFT
        data_GPU = cupy.fft.fft(data_GPU, axis=fftAxis)/samples
        # calculate absolute value and only keep depth range specified
        data_GPU = cupy.absolute(data_GPU[:,Pixel_start:Pixel_start+Pixel_range])
        # transfer data back to computer
        data_CPU = cupy.asnumpy(data_GPU)

        # print('FFT took ',time.time()-start,' seconds\n')
        # data_CPU = data_CPU.reshape([shape[0],Pixel_range * np.uint32(Alines/shape[0])])
        # display and save data, data type is float32
        an_action = DnSAction(mode, data = data_CPU, args = args) # data in Memory[memoryLoc]
        self.DnSQueue.put(an_action)
            
        
    def cpuFFT(self, mode, memoryLoc, args):

        if self.Digitizer == 'ATS9351':
            samples = self.ui.PreSamples.value()+self.ui.PostSamples.value()
        elif self.Digitizer == 'ART8912':
            samples = self.ui.PostSamples_2.value()
        Pixel_start = self.ui.DepthStart.value()
        Pixel_range = self.ui.DepthRange.value()
        data_CPU = self.Memory[memoryLoc].copy()
        
        Alines =np.uint32((data_CPU.shape[1])/samples) * data_CPU.shape[0]
        
        data_CPU=data_CPU.reshape([Alines, samples])
        if self.Digitizer == 'ATS9351':
            data_CPU=np.float32(data_CPU/65535-0.5)
        elif self.Digitizer == 'ART8912':
            data_CPU=np.float32(data_CPU/4095-0.5)
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
        an_action = DnSAction(mode, data_CPU, args) # data in Memory[memoryLoc]
        self.DnSQueue.put(an_action)
        
    def update_Dispersion(self):
        if self.Digitizer == 'ATS9351':
            samples = self.ui.PreSamples.value()+self.ui.PostSamples.value()
        elif self.Digitizer == 'ART8912':
            samples = self.ui.PostSamples_2.value()
        # print('GPU dispersion samples: ',samples)
            
        self.window = np.float32(np.hanning(samples))
        # update dispersion and window
        dispersion_path = self.ui.Disp_DIR.toPlainText()
        # print(dispersion_path)
        if os.path.isfile(dispersion_path):
            self.dispersion = np.float32(np.fromfile(dispersion_path, dtype=np.float32))
            self.dispersion = np.complex64(np.exp(1j*self.dispersion))
            print('using disperison compensation\n')
        else:
            self.dispersion = np.complex64(np.ones(samples))
            print('using no disperison compensation\n')
        if len(self.window) == len(self.dispersion):
            self.dispersion = np.complex64(self.dispersion * self.window)
        else:
            print('dispersion length unmatch current sample size, using no dispersion compensation\n')
            self.dispersion = np.complex64(np.ones(samples))
            self.dispersion = np.complex64(self.dispersion * self.window)
        self.dispersion = self.dispersion.reshape([1,len(self.dispersion)])
        
        
    def update_FFTlength(self):
        self.length_FFT = 2
        if self.Digitizer == 'ATS9351':
            samples = self.ui.PreSamples.value()+self.ui.PostSamples.value()
        elif self.Digitizer == 'ART8912':
            samples = self.ui.PostSamples_2.value()
        while self.length_FFT < samples:
            self.length_FFT *=2
