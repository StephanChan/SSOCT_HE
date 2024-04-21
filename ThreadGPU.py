# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 16:50:25 2023

@author: admin
"""
from PyQt5.QtCore import  QThread
import time
global SIM
SIM = False
if not SIM:
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
        if not SIM:
            self.winfunc = cupy.ElementwiseKernel(
                'float32 x, complex64 y',
                'complex64 z',
                'z=x*y',
                'winfunc')
        self.FFT_actions = 0 # count how many FFT actions have taken place
        
    def run(self):
        self.update_Dispersion()
        self.update_background()
        # self.update_FFTlength()
        self.QueueOut()
        
    def QueueOut(self):
        self.item = self.queue.get()
        while self.item.action != 'exit':
            start=time.time()
            try:
                if self.item.action == 'GPU':
                    self.cudaFFT(self.item.mode, self.item.memoryLoc, self.item.args)
                    self.FFT_actions += 1
                elif self.item.action == 'CPU':
                    self.cpuFFT(self.item.mode, self.item.memoryLoc, self.item.args)
                    self.FFT_actions += 1
                elif self.item.action == 'update_Dispersion':
                    self.update_Dispersion()
                elif self.item.action == 'update_background':
                    self.update_background()
                elif self.item.action == 'display_FFT_actions':
                    self.display_FFT_actions()
                else:
                    self.ui.statusbar.showMessage('GPU thread is doing something invalid '+self.item.action)
                if time.time()-start > 1:
                    message = '\n an FFT action took '+str(round(time.time()-start,3))+' s\n'
                    print(message)
                    # self.ui.PrintOut.append(message)
                    self.log.write(message)
            except Exception as error:
                message = "An error occurred, skip the FFT action\n"
                self.ui.statusbar.showMessage(message)
                # self.ui.PrintOut.append(message)
                self.log.write(message)
                print(traceback.format_exc())
            self.item = self.queue.get()
        self.ui.statusbar.showMessage(self.exit_message)

    def cudaFFT(self, mode, memoryLoc, args):
        # get samples per Aline
        if self.Digitizer == 'ATS9351':
            samples = self.ui.PreSamples.value()+self.ui.PostSamples.value()
        elif self.Digitizer == 'ART8912':
            samples = self.ui.PostSamples_2.value()# - self.ui.DelaySamples.value()
        # get depth pixels after FFT
        Pixel_start = self.ui.DepthStart.value()
        Pixel_range = self.ui.DepthRange.value()
        # print(Pixel_start, Pixel_range)
        # copy data from global memory
        # print('GPU using memory loc: ',memoryLoc)
        # print(self.Memory[memoryLoc].shape)
        if not SIM:
            self.data_CPU = np.float32(self.Memory[memoryLoc].copy())
            # print('GPU finish copy data')
            # self.data_CPU = np.zeros()
            # reshape data as [Alines, Samples]
            # Alines =np.uint32((self.data_CPU.shape[1])/samples) * self.data_CPU.shape[0]
            Alines =len(self.data_CPU)//samples

            self.data_CPU=self.data_CPU.reshape([Alines, samples])
            # print('GPU finish reshape data')
            # subtract background and remove first 100 samples
            if self.Digitizer == 'ART8912':
                self.data_CPU = self.data_CPU[:,self.ui.DelaySamples.value():self.ui.PostSamples_2.value()-self.ui.TrimSamples.value()]-self.background
                samples = self.ui.PostSamples_2.value() - self.ui.DelaySamples.value()-self.ui.TrimSamples.value()
            fftAxis = 1
            # print(self.data_CPU[1:10,1:5])
            # print('GPU finish chop data')
            # # zero-padding data before FFT
            # if data_CPU.shape[1] != self.length_FFT:
            #     data_padded = np.zeros([Alines, self.length_FFT], dtype = np.float32)
            #     tmp = np.uint16((self.length_FFT-samples)/2)
            #     data_padded[:,tmp:samples+tmp] = data_CPU
            # else:
            #     data_padded = data_CPU
            # start = time.time()
            # transfer data to GPU
            data_GPU  = cupy.array(self.data_CPU)
            # print('GPU finish send data')
            dispersion_GPU = cupy.array(self.dispersion)
            # window function and dispersion compensation
            data_GPU = self.winfunc(data_GPU, dispersion_GPU)
            # print('GPU finish WINDOW data')
            # FFT
            data_GPU = cupy.fft.fft(data_GPU, axis=fftAxis)/samples
            # print('GPU finish FFT data')
            # calculate absolute value and only keep depth range specified
            data_GPU = cupy.absolute(data_GPU[:,Pixel_start:Pixel_start+Pixel_range])
            # print('GPU finish trim data')
            # transfer data back to computer
            self.data_CPU = cupy.asnumpy(data_GPU)*self.AMPLIFICATION
            # print(self.data_CPU.shape)
            # print('GPU finish receive data')
            # print('FFT took ',time.time()-start,' seconds\n')
            # data_CPU = data_CPU.reshape([shape[0],Pixel_range * np.uint32(Alines/shape[0])])
            # display and save data, data type is float32
            an_action = DnSAction(mode, data = self.data_CPU, args = args) # data in Memory[memoryLoc]
            self.DnSQueue.put(an_action)
            # print('send for display')
            if self.ui.Gotozero.isChecked() and self.ui.ACQMode.currentText() == 'SingleAline':
                self.GPU2weaverQueue.put(self.data_CPU)
            if self.ui.DSing.isChecked():
                self.GPU2weaverQueue.put(self.data_CPU)
                # print('GPU data to weaver')
        
        else:
            self.AlinesPerBline = self.ui.AlineAVG.value()*self.ui.Xsteps.value()+self.ui.PreClock.value()*2+self.ui.PostClock.value()
            if self.ui.ACQMode.currentText() in ['SingleBline', 'SingleAline','RptBline', 'RptAline']:
                self.triggerCount = self.ui.BlineAVG.value() * self.AlinesPerBline
            elif self.ui.ACQMode.currentText() in ['SingleCscan', 'SurfScan','SurfScan+Slice']:
                self.triggerCount = self.ui.BlineAVG.value() * self.ui.Ysteps.value() * self.AlinesPerBline
            data_CPU = 100*np.random.random([self.triggerCount, Pixel_range])
            an_action = DnSAction(mode, data = data_CPU, args = args) # data in Memory[memoryLoc]
            self.DnSQueue.put(an_action)
            # print('send for display')
            if self.ui.Gotozero.isChecked() and self.ui.ACQMode.currentText() == 'SingleAline':
                self.GPU2weaverQueue.put(data_CPU)
            if self.ui.DSing.isChecked():
                self.GPU2weaverQueue.put(data_CPU)
                # print('GPU data to weaver')
            print('GPU finish')
            
        
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
            samples = self.ui.PostSamples_2.value() - self.ui.DelaySamples.value()-self.ui.TrimSamples.value()
        # print('GPU dispersion samples: ',samples)
            
        self.window = np.float32(np.hanning(samples))
        # update dispersion and window
        dispersion_path = self.ui.Disp_DIR.text()
        # print(dispersion_path)
        if os.path.isfile(dispersion_path):
            self.dispersion = np.float32(np.fromfile(dispersion_path, dtype=np.float32))
            self.dispersion = np.complex64(np.exp(1j*self.dispersion))
            
            self.ui.statusbar.showMessage("load disperison compensation success...")
            # self.ui.PrintOut.append("load disperison compensation success...")
            self.log.write("load disperison compensation success...")
            print("load disperison compensation success...")
        else:
            self.dispersion = np.complex64(np.ones(samples))
            self.ui.statusbar.showMessage('no disperison compensation found...')
            # self.ui.PrintOut.append("no disperison compensation found...")
            self.log.write("no disperison compensation found...")
            print("no disperison compensation found...")
        if len(self.window) == len(self.dispersion):
            self.dispersion = np.complex64(self.dispersion * self.window)
            message = 'using dispersion compensation...'
            print(message)
            # self.ui.PrintOut.append(message)
            self.log.write(message)
        else:
            self.ui.statusbar.showMessage('however, dispersion length unmatch sample size, no dispersion compensation...')
            # self.ui.PrintOut.append('however, dispersion length unmatch sample size, no dispersion compensation...')
            self.log.write('however, dispersion length unmatch sample size, no dispersion compensation...')
            print('however, dispersion length unmatch sample size, no dispersion compensation...')
            self.dispersion = np.complex64(np.ones(samples))
            self.dispersion = np.complex64(self.dispersion * self.window)
        self.dispersion = self.dispersion.reshape([1,len(self.dispersion)])
        
    def update_background(self):
        if self.Digitizer == 'ATS9351':
            samples = self.ui.PreSamples.value()+self.ui.PostSamples.value()
        elif self.Digitizer == 'ART8912':
            samples = self.ui.PostSamples_2.value() - self.ui.DelaySamples.value()-self.ui.TrimSamples.value()
        background_path = self.ui.BG_DIR.text()

        if os.path.isfile(background_path):
            self.background = np.fromfile(background_path, dtype=np.float32)
            current_message = self.ui.statusbar.currentMessage()
            self.ui.statusbar.showMessage(current_message+"load background success...")
            # self.ui.PrintOut.append("load background success...")
            self.log.write("load background success...")
            print("load background success...")
        else:
            current_message = self.ui.statusbar.currentMessage()
            self.ui.statusbar.showMessage('using 2048 as background...')
            # self.ui.PrintOut.append('using 2048 as background...')
            self.log.write('using 2048 as background...')
            self.background = np.float32(np.ones(samples)*2048)
            print('using 2048 as background...')
            
        if  len(self.background) == samples:
            message = 'using background subtraction...'
            print(message)
            # self.ui.PrintOut.append(message)
            self.log.write(message)
        else:
            self.ui.statusbar.showMessage('however, background length unmatch sample size, no background used...')
            # self.ui.PrintOut.append('however, background length unmatch sample size, no background used...')
            self.log.write('however, background length unmatch sample size, no background used...')
            print('however, background length unmatch sample size, no background used...')
            self.background = np.float32(np.ones(samples)*2048)
        
    def update_FFTlength(self):
        self.length_FFT = 2
        if self.Digitizer == 'ATS9351':
            samples = self.ui.PreSamples.value()+self.ui.PostSamples.value()
        elif self.Digitizer == 'ART8912':
            samples = self.ui.PostSamples_2.value()-self.ui.DelaySamples.value()-self.ui.TrimSamples.value()
        while self.length_FFT < samples:
            self.length_FFT *=2

    def display_FFT_actions(self):
        message = str(self.FFT_actions)+ ' FFT actions taken place\n'
        # self.ui.PrintOut.append(message)
        self.log.write(message)
        self.FFT_actions = 0
        
   