# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 16:50:25 2023

@author: admin
"""
from PyQt5.QtCore import  QThread
import time
global SIM
SIM = False

try:
    import cupy
    SIM = True
except:
    SIM = True
import numpy as np
from Actions import DnSAction
import os
import traceback


class GPUThread(QThread):
    def __init__(self):
        super().__init__()
        # TODO: write windowing and dispersion function
        self.exit_message = 'GPU thread successfully exited\n'
        self.FFT_actions = 0 # count how many FFT actions have taken place
        
    def defwin(self):
        if not (SIM or self.SIM):
            self.winfunc = cupy.ElementwiseKernel(
                'float32 x, complex64 y',
                'complex64 z',
                'z=x*y',
                'winfunc')
    
    def definterp(self):
        if not (SIM or self.SIM):
            # define interpolation kernel
            self.interp_kernel = cupy.RawKernel(r'''
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
    
    def run(self):
        self.defwin()
        self.definterp()
        self.update_Dispersion()
        self.update_background()
        self.update_intDk()
        # self.update_FFTlength()
        self.QueueOut()
        
    def QueueOut(self):
        self.item = self.queue.get()
        while self.item.action != 'exit':
            start=time.time()
            try:
                if self.item.action == 'GPU':
                    if self.ui.UseSDOCTbackground.isChecked():
                        self.interp_FFT_gpu(self.item.mode, self.item.memoryLoc, self.item.args)
                    else:
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
                elif self.item.action == 'update_intDk':
                    self.update_intDk()
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
        if self.Digitizer == 'Alazar':
            samples = self.ui.PreSamples.value()+self.ui.PostSamples.value()
        elif self.Digitizer == 'ART':
            samples = self.ui.PostSamples_2.value()# - self.ui.DelaySamples.value()
        # get depth pixels after FFT
        Pixel_start = self.ui.DepthStart.value()
        Pixel_range = self.ui.DepthRange.value()
        if not (SIM or self.SIM):
            self.data_CPU = np.float32(self.Memory[memoryLoc].copy())
            Alines =self.data_CPU.shape[0]*self.data_CPU.shape[1]//samples
            self.data_CPU=self.data_CPU.reshape([Alines, samples])
            # subtract background and remove first 100 samples
            if self.Digitizer == 'ART':
                self.data_CPU = self.data_CPU[:,self.ui.DelaySamples.value():self.ui.PostSamples_2.value()-self.ui.TrimSamples.value()]-self.background
                samples = self.ui.PostSamples_2.value() - self.ui.DelaySamples.value()-self.ui.TrimSamples.value()
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
            data_GPU  = cupy.array(self.data_CPU)
            dispersion_GPU = cupy.array(self.dispersion)
            # window function and dispersion compensation
            t = time.time()
            data_GPU = self.winfunc(data_GPU, dispersion_GPU)
            print('windowing takes ', time.time()-t)
            # FFT
            t = time.time()
            data_GPU = cupy.fft.fft(data_GPU, axis=fftAxis)/samples
            print('fft takes ', time.time()-t)
            # calculate absolute value and only keep depth range specified
            data_GPU = cupy.absolute(data_GPU[:,Pixel_start:Pixel_start+Pixel_range])
            # transfer data back to computer
            self.data_CPU = cupy.asnumpy(data_GPU)*self.AMPLIFICATION
            # display and save data, data type is float32
            an_action = DnSAction(mode, data = self.data_CPU, raw = False, args = args) # data in Memory[memoryLoc]
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
            elif self.ui.ACQMode.currentText() in ['SingleCscan', 'Mosaic','Mosaic+Cut']:
                self.triggerCount = self.ui.BlineAVG.value() * self.ui.Ysteps.value() * self.AlinesPerBline
            data_CPU = 100*np.random.random([self.triggerCount, Pixel_range])
            an_action = DnSAction(mode, data = data_CPU, raw = False, args = args) # data in Memory[memoryLoc]
            self.DnSQueue.put(an_action)
            # print('send for display')
            if self.ui.Gotozero.isChecked() and self.ui.ACQMode.currentText() == 'SingleAline':
                self.GPU2weaverQueue.put(data_CPU)
            # print(self.ui.DSing.isChecked())
            if self.ui.DSing.isChecked():
                self.GPU2weaverQueue.put(data_CPU)
                # print('GPU data to weaver')
            # print('GPU finish')
            
            
    def cpuFFT(self, mode, memoryLoc, args):
        # get samples per Aline
        if self.Digitizer == 'Alazar':
            samples = self.ui.PreSamples.value()+self.ui.PostSamples.value()
        elif self.Digitizer == 'ART':
            samples = self.ui.PostSamples_2.value()# - self.ui.DelaySamples.value()
        # get depth pixels after FFT
        Pixel_start = self.ui.DepthStart.value()
        Pixel_range = self.ui.DepthRange.value()
        if not (SIM or self.SIM):
            self.data_CPU = np.float32(self.Memory[memoryLoc].copy())
            Alines =self.data_CPU.shape[0]*self.data_CPU.shape[1]//samples
            self.data_CPU=self.data_CPU.reshape([Alines, samples])
            # subtract background and remove first 100 samples
            if self.Digitizer == 'ART':
                self.data_CPU = self.data_CPU[:,self.ui.DelaySamples.value():self.ui.PostSamples_2.value()-self.ui.TrimSamples.value()]-self.background
                samples = self.ui.PostSamples_2.value() - self.ui.DelaySamples.value()-self.ui.TrimSamples.value()
            fftAxis = 1
            # # zero-padding data before FFT
            # if data_CPU.shape[1] != self.length_FFT:
            #     data_padded = np.zeros([Alines, self.length_FFT], dtype = np.float32)
            #     tmp = np.uint16((self.length_FFT-samples)/2)
            #     data_padded[:,tmp:samples+tmp] = data_CPU
            # else:
            #     data_padded = data_CPU
            
            self.data_CPU = self.data_CPU*self.dispersion
            self.data_CPU = np.abs(np.fft.fft(self.data_CPU, axis=fftAxis))/samples
            
            
            self.data_CPU = self.data_CPU[:,Pixel_start: Pixel_start+Pixel_range ]
            # data_CPU = data_CPU.reshape([shape[0],Pixel_range * np.uint32(Alines/shape[0])])
            an_action = DnSAction(mode, self.data_CPU, False, args) # data in Memory[memoryLoc]
            self.DnSQueue.put(an_action)
            if self.ui.Gotozero.isChecked() and self.ui.ACQMode.currentText() == 'SingleAline':
                self.GPU2weaverQueue.put(self.data_CPU)
            if self.ui.DSing.isChecked():
                self.GPU2weaverQueue.put(self.data_CPU)
                # print('GPU data to weaver')
        else:
            self.AlinesPerBline = self.ui.AlineAVG.value()*self.ui.Xsteps.value()+self.ui.PreClock.value()*2+self.ui.PostClock.value()
            if self.ui.ACQMode.currentText() in ['SingleBline', 'SingleAline','RptBline', 'RptAline']:
                self.triggerCount = self.ui.BlineAVG.value() * self.AlinesPerBline
            elif self.ui.ACQMode.currentText() in ['SingleCscan', 'Mosaic','Mosaic+Cut']:
                self.triggerCount = self.ui.BlineAVG.value() * self.ui.Ysteps.value() * self.AlinesPerBline
            data_CPU = 100*np.random.random([self.triggerCount, Pixel_range])
            an_action = DnSAction(mode, data = data_CPU, raw = False, args = args) # data in Memory[memoryLoc]
            self.DnSQueue.put(an_action)
            # print('send for display')
            if self.ui.Gotozero.isChecked() and self.ui.ACQMode.currentText() == 'SingleAline':
                self.GPU2weaverQueue.put(data_CPU)
            # print(self.ui.DSing.isChecked())
            if self.ui.DSing.isChecked():
                self.GPU2weaverQueue.put(data_CPU)
                # print('GPU data to weaver')
            # print('GPU finish')
            
    def interp_FFT_gpu(self, mode, memoryLoc, args):
        # get samples per Aline
        if self.Digitizer == 'Alazar':
            samples = self.ui.PreSamples.value()+self.ui.PostSamples.value()
        elif self.Digitizer == 'ART':
            samples = self.ui.PostSamples_2.value()# - self.ui.DelaySamples.value()
        elif self.Digitizer == 'CXP':
            samples = self.ui.PostSamples_2.value()
        # get depth pixels after FFT
        Pixel_start = self.ui.DepthStart.value()
        Pixel_range = self.ui.DepthRange.value()
        if not (SIM or self.SIM):
            self.data_CPU = np.float32(self.Memory[memoryLoc].copy())
            Alines =self.data_CPU.shape[0]*self.data_CPU.shape[1]//samples
            self.data_CPU=self.data_CPU.reshape([Alines, samples])
            
            t1=time.time()
            # y=y0-np.mean(y0,0)
            self.data_CPU = self.data_CPU-np.mean(self.data_CPU,0)
            self.data_CPU = self.data_CPU.reshape(Alines * samples)
    
            x_gpu  = cupy.array(self.x)
            xp_gpu  = cupy.array(self.xp)
            y_gpu  = cupy.array(self.data_CPU)
            indice1 = cupy.array(self.indice[:,0])
            indice2 = cupy.array(self.indice[:,1])
            yp_gpu = cupy.zeros(self.data_CPU.shape, dtype = cupy.float32)
            print('data to gpu takes ', round(time.time()-t1,3))
    
            # interpolation
            t2 = time.time() 
            self.interp_kernel((8,8),(16,16), (Alines, samples, x_gpu, xp_gpu, y_gpu, indice1, indice2, yp_gpu))
            print('time for interpolation: ', round(time.time()-t2,5))
            # yp = cp.asnumpy(yp_gpu)
            # yp_gpu=yp_gpu.reshape([Alines, samples])
            # plt.figure()
            # plt.plot(x,y[0:nSamp],xp,yp[0,:])
            ################################################################################# FFT
            t3=time.time()
            data_gpu  = cupy.fft.fft(cupy.reshape(yp_gpu,[Alines, samples]), axis=1)
            data_gpu = cupy.absolute(data_gpu[:,self.ui.DepthStart.value():self.ui.DepthStart.value() + self.ui.DepthRange.value()])
            self.data_CPU = cupy.asnumpy(data_gpu)*self.AMPLIFICATION
            print('time for FFT: ', round(time.time()-t3,5))
            # yp = cp.asnumpy(data_gpu)
            print('total time: ', round(time.time()-t1,5))
            
            # display and save data, data type is float32
            an_action = DnSAction(mode, data = self.data_CPU, raw = False, args = args) # data in Memory[memoryLoc]
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
            elif self.ui.ACQMode.currentText() in ['SingleCscan', 'Mosaic','Mosaic+Cut']:
                self.triggerCount = self.ui.BlineAVG.value() * self.ui.Ysteps.value() * self.AlinesPerBline
            data_CPU = 100*np.random.random([self.triggerCount, Pixel_range])
            an_action = DnSAction(mode, data = data_CPU, raw = False, args = args) # data in Memory[memoryLoc]
            self.DnSQueue.put(an_action)
            # print('send for display')
            if self.ui.Gotozero.isChecked() and self.ui.ACQMode.currentText() == 'SingleAline':
                self.GPU2weaverQueue.put(data_CPU)
            # print(self.ui.DSing.isChecked())
            if self.ui.DSing.isChecked():
                self.GPU2weaverQueue.put(data_CPU)
                # print('GPU data to weaver')
            # print('GPU finish')
    # read interpolation configs
    def find_interp_indice(self):
        intDk = self.ui.intDk.value()
        k = np.linspace(1+intDk/2, 1-intDk/2, self.ui.PostSamples_2.value());
        self.x = 1./np.fliplr(k.reshape(1,self.ui.PostSamples_2.value()))
        self.x=self.x.reshape(self.ui.PostSamples_2.value())
        self.x=self.x.astype(np.float32)
        self.indice=np.zeros([len(self.x),2], dtype = np.uint16)
        # for x that is ramping up, interpolate from first to last element of xp
        if self.x[-1]>self.x[0]:
            self.xp = np.linspace(np.min(self.x), np.max(self.x),self.ui.PostSamples_2.value()).astype(np.float32)
            start = 0
            stride = 1
            end_= len(self.x)
        # for x that is ramping down, interpolate from last to first element of xp
        else:
            self.xp = np.linspace(np.max(self.x), np.min(self.x),self.ui.PostSamples_2.value()).astype(np.float32)
            start=len(self.x)-1
            stride = -1
            end_= 0
        # if the first x value is unchanged
        if self.xp[start]<=self.x[start]:
            self.indice[start,0] = start+stride
            self.indice[start,1] = start
            start = start+stride
        # do interpolation
        for ii in np.arange(start, end_, stride):
            xt = self.xp[ii]
            while xt>self.x[start]:
                start=start+stride
            self.indice[ii,0] = start-stride
            self.indice[ii,1] = start
        print('interpolation indices generated using intDk: ', intDk)
            
    def update_Dispersion(self):
        if self.Digitizer == 'Alazar':
            samples = self.ui.PreSamples.value()+self.ui.PostSamples.value()
        elif self.Digitizer == 'ART':
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
        if self.Digitizer == 'Alazar':
            samples = self.ui.PreSamples.value()+self.ui.PostSamples.value()
        elif self.Digitizer == 'ART':
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
            pass
            # message = 'using background subtraction...'
            # print(message)
            # self.ui.PrintOut.append(message)
            # self.log.write(message)
        else:
            self.ui.statusbar.showMessage('however, background length unmatch sample size, no background used...')
            # self.ui.PrintOut.append('however, background length unmatch sample size, no background used...')
            self.log.write('however, background length unmatch sample size, no background used...')
            print('however, background length unmatch sample size, no background used...')
            self.background = np.float32(np.ones(samples)*2048)
        
    def update_FFTlength(self):
        self.length_FFT = 2
        if self.Digitizer == 'Alazar':
            samples = self.ui.PreSamples.value()+self.ui.PostSamples.value()
        elif self.Digitizer == 'ART':
            samples = self.ui.PostSamples_2.value()-self.ui.DelaySamples.value()-self.ui.TrimSamples.value()
        while self.length_FFT < samples:
            self.length_FFT *=2

    def display_FFT_actions(self):
        message = str(self.FFT_actions)+ ' FFT actions taken place\n'
        # self.ui.PrintOut.append(message)
        self.log.write(message)
        self.FFT_actions = 0
        
    def update_intDk(self):
        self.find_interp_indice()