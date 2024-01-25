# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 18:26:44 2023

@author: admin
"""

from PyQt5.QtCore import  QThread
from Generaic_functions import LinePlot, ImagePlot
import numpy as np
import traceback
global SCALE
SCALE =0.2

class DnSThread(QThread):
    def __init__(self):
        super().__init__()
        self.surf = []
        self.sliceNum = 1
        self.tileNum = 1
        self.BlineNum = 1
        self.CscanNum = 1
        self.totalTiles = 0
        
    def run(self):
        self.QueueOut()
        
    def QueueOut(self):
        self.item = self.queue.get()
        while self.item.action != 'exit':
            #self.ui.statusbar.showMessage('Display thread is doing ' + self.item.action)
            try:
                if self.item.action in ['SingleAline','RptAline']:
                    
                    self.Display_aline(self.item.data, self.item.raw)
                
                elif self.item.action in ['SingleBline','RptBline']:
                    self.Display_bline(self.item.data, self.item.raw)
                    
                elif self.item.action in ['SingleCscan','RptCscan']:
                    self.Display_Cscan(self.item.data, self.item.raw)
                elif self.item.action == 'SurfScan':
                    self.Display_SurfScan(self.item.data, self.item.raw, self.item.args)
                
                elif self.item.action == 'Clear':
                    self.surf = []
                elif self.item.action == 'UpdateContrast':
                    self.Update_contrast()
                elif self.item.action == 'dispersionCompensation':
                    self.dispersion_compensation()
                    
                else:
                    self.ui.statusbar.showMessage('Display and save thread is doing something invalid' + self.item.action)
            except Exception as error:
                print("\nAn error occurred:", error,' skip the display and save action\n')
                print(traceback.format_exc())
            self.item = self.queue.get()
        print('Display and save Thread successfully exited')
            

    def Display_aline(self, data, raw = False):
        #data = ctypes.cast(data_address, ctypes.py_object).value 
        # TODO: make sure fft is shifted
        # check if displaying before FFT
        if not raw:
            Zpixels = self.ui.DepthRange.value()
        else:
            if self.Digitizer == 'ATS9351':
                Zpixels = self.ui.PreSamples.value()+self.ui.PostSamples.value()
                data = np.float32(data/pow(2,16))
            elif self.Digitizer == 'ART8912':
                Zpixels = self.ui.PostSamples_2.value()
                data = np.float32(data/pow(2,12))
        Xpixels = 10
        Yrpt = self.ui.BlineAVG.value()
        data = data.reshape([Yrpt,Xpixels,Zpixels])
        # data in original state
        self.Aline = data
        
        data = np.float32(np.mean(data,0))
        data = data[1,:]
        # data = data.reshape(Xpixels*Zpixels)
        # print(data.shape)
        # print(data)
        # check if displaying in log scale
        if self.ui.LOG.currentText() == '10log10':
            data=np.float32(10*np.log10(data+0.000001))
        # float32 data type
        pixmap = LinePlot(data, [], self.ui.MinContrast.value(), self.ui.MaxContrast.value())
        # clear content on the waveformLabel
        self.ui.XYplane.clear()
        # update iamge on the waveformLabel
        self.ui.XYplane.setPixmap(pixmap)
    
    def Display_bline(self, data, raw = False):
        if not raw:
            Zpixels = self.ui.DepthRange.value()
        else:
            if self.Digitizer == 'ATS9351':
                Zpixels = self.ui.PreSamples.value()+self.ui.PostSamples.value()
                data = np.float32(data/pow(2,16))
            elif self.Digitizer == 'ART8912':
                Zpixels = self.ui.PostSamples_2.value()
                data = np.float32(data/pow(2,12))
        Xpixels = self.ui.Xsteps.value()*self.ui.AlineAVG.value()
        if self.Digitizer == 'ART8912':
            Xpixels = Xpixels + self.ui.PreClock.value()
        Yrpt = self.ui.BlineAVG.value()
        
        data = data.reshape([Yrpt,Xpixels,Zpixels])
        # data in original state
        self.Bline = data
        data = np.float32(np.mean(data,0))
        data = np.transpose(data).copy()
        # data = np.flip(data, 1).copy()
        if self.ui.LOG.currentText() == '10log10':
            data=np.float32(10*np.log10(data+0.000001))

        pixmap = ImagePlot(data, self.ui.MinContrast.value(), self.ui.MaxContrast.value())
        # clear content on the waveformLabel
        self.ui.XYplane.clear()
        # update iamge on the waveformLabel
        self.ui.XYplane.setPixmap(pixmap)
        
        if self.ui.Save.isChecked():
            if raw:
                data = np.uint16(self.Bline*65535)
            else:
                data = np.uint16(self.Bline/SCALE*65535)
            self.WriteData(data, self.BlineFilename([Yrpt,Xpixels,Zpixels]))
        
    def Display_Cscan(self, data, raw = False):
        if not raw:
            Zpixels = self.ui.DepthRange.value()
        else:
            if self.Digitizer == 'ATS9351':
                Zpixels = self.ui.PreSamples.value()+self.ui.PostSamples.value()
                data = np.float32(data/pow(2,16))
            elif self.Digitizer == 'ART8912':
                Zpixels = self.ui.PostSamples_2.value()
                data = np.float32(data/pow(2,12))
        Xpixels = self.ui.Xsteps.value()*self.ui.AlineAVG.value()
        if self.Digitizer == 'ART8912':
            Xpixels = Xpixels + self.ui.PreClock.value()
        Ypixels = self.ui.Ysteps.value()*self.ui.BlineAVG.value()
        data = data.reshape([Ypixels,Xpixels,Zpixels])
        # data in original state
        self.Cscan = data
        
        if self.ui.LOG.currentText() == '10log10':
            data=np.float32(10*np.log10(data+0.000001))

        plane = (data[:,1,:]).copy()
        pixmap = ImagePlot(plane, self.ui.MinContrast.value(), self.ui.MaxContrast.value())
        # clear content on the waveformLabel
        self.ui.YZplane.clear()
        # update iamge on the waveformLabel
        self.ui.YZplane.setPixmap(pixmap)
        
        plane = np.transpose(data[1,:,:]).copy()
        pixmap = ImagePlot(plane, self.ui.MinContrast.value(), self.ui.MaxContrast.value())
        # clear content on the waveformLabel
        self.ui.XZplane.clear()
        # update iamge on the waveformLabel
        self.ui.XZplane.setPixmap(pixmap)
        
        #data = ctypes.cast(data_address, ctypes.py_object).value 
        plane = np.mean(data,2)# has to be first index, otherwise the memory space is not continuous
        pixmap = ImagePlot(plane, self.ui.MinContrast.value(), self.ui.MaxContrast.value()/4)
        # clear content on the waveformLabel
        self.ui.XYplane.clear()
        # update image on the waveformLabel
        self.ui.XYplane.setPixmap(pixmap)
        
        if self.ui.Save.isChecked():
            if raw:
                data = np.uint16(self.Cscan*65535)
            else:
                data = np.uint16(self.Cscan/SCALE*65535)
            self.WriteData(self.Cscan, self.CscanFilename([Ypixels,Xpixels,Zpixels]))

        
    def Display_SurfScan(self, data, raw = False, args = []):
        if not raw:
            Zpixels = self.ui.DepthRange.value()
        else:
            if self.Digitizer == 'ATS9351':
                Zpixels = self.ui.PreSamples.value()+self.ui.PostSamples.value()
                data = np.float32(data/pow(2,16))
            elif self.Digitizer == 'ART8912':
                Zpixels = self.ui.PostSamples_2.value()
                data = np.float32(data/pow(2,12))
        Xpixels = self.ui.Xsteps.value()*self.ui.AlineAVG.value()
        if self.Digitizer == 'ART8912':
            Xpixels = Xpixels + self.ui.PreClock.value()
        Ypixels = self.ui.Ysteps.value()*self.ui.BlineAVG.value()
        data = data.reshape([Ypixels,Xpixels,Zpixels])
        self.Cscan = data
        if self.ui.LOG.currentText() == '10log10':
            data=np.float32(10*np.log10(data+0.000001))

        plane = (data[:,1,:]).copy()
        pixmap = ImagePlot(plane, self.ui.MinContrast.value(), self.ui.MaxContrast.value())
        # clear content on the waveformLabel
        self.ui.YZplane.clear()
        # update iamge on the waveformLabel
        self.ui.YZplane.setPixmap(pixmap)
        
        plane = np.transpose(data[1,:,:]).copy()
        pixmap = ImagePlot(plane, self.ui.MinContrast.value(), self.ui.MaxContrast.value())
        # clear content on the waveformLabel
        self.ui.XZplane.clear()
        # update iamge on the waveformLabel
        self.ui.XZplane.setPixmap(pixmap)
        
        #data = ctypes.cast(data_address, ctypes.py_object).value 
        plane = np.mean(data,2)
        pixmap = ImagePlot(plane, self.ui.MinContrast.value(), self.ui.MaxContrast.value()/4)
        # clear content on the waveformLabel
        self.ui.XYplane.clear()
        # update iamge on the waveformLabel
        self.ui.XYplane.setPixmap(pixmap)
        
        fileX = args[0][0]
        fileY = args[0][1]-1
        surfX = args[1][0]
        surfY = np.int32(args[1][1]/args[1][0])
        self.totalTiles = args[1][1]
        Xpixels = np.uint16(Xpixels/20)
        Ypixels = np.uint16(Ypixels/20)
        if not np.any(self.surf):
            self.surf = np.zeros([ surfX*Ypixels,surfY*Xpixels],dtype = np.float32)
            
        self.surf[Ypixels*fileX:Ypixels*(fileX+1),Xpixels*fileY:Xpixels*(fileY+1)] = np.resize(plane,[Ypixels,Xpixels])
        pixmap = ImagePlot(self.surf, self.ui.MinContrast.value(), self.ui.MaxContrast.value()/10)
        # clear content on the waveformLabel
        self.ui.SampleMosaic.clear()
        # update iamge on the waveformLabel
        self.ui.SampleMosaic.setPixmap(pixmap)
        if self.ui.Save.isChecked():
            if raw:
                data = np.uint16(self.Cscan*65535)
            else:
                data = np.uint16(self.Cscan/SCALE*65535)
            self.WriteData(self.Cscan, self.SurfFilename([Ypixels*20,Xpixels*20,Zpixels]))

            
    def Update_contrast(self):
        if self.ui.ACQMode.currentText() in ['SingleAline', 'RptAline']:
            data = np.float32(np.mean(self.Aline,0))
            data = data[0,:]
            if self.ui.LOG.currentText() == '10log10':
                data=10*np.log10(data+0.000001)
            pixmap = LinePlot(data, [], self.ui.MinContrast.value(), self.ui.MaxContrast.value())
            # clear content on the waveformLabel
            self.ui.XYplane.clear()
            # update iamge on the waveformLabel
            self.ui.XYplane.setPixmap(pixmap)
        elif self.ui.ACQMode.currentText() in ['SingleBline', 'RptBline']:
            data = np.float32(np.mean(self.Bline,0))
            data = np.transpose(data).copy()
            # data = np.flip(data, 1).copy()
            if self.ui.LOG.currentText() == '10log10':
                data=np.float32(10*np.log10(data+0.000001))
            pixmap = ImagePlot(data, self.ui.MinContrast.value(), self.ui.MaxContrast.value())
            # clear content on the waveformLabel
            self.ui.XYplane.clear()
            # update iamge on the waveformLabel
            self.ui.XYplane.setPixmap(pixmap)
        elif self.ui.ACQMode.currentText() in ['SurfScan','SurfScan+Slice', 'SingleCscan']:
            if self.ui.LOG.currentText() == '10log10':
                data=10*np.log10(self.Cscan+0.000001)
            else:
                data = self.Cscan
            plane = (data[:,1,:]).copy()
            pixmap = ImagePlot(plane, self.ui.MinContrast.value(), self.ui.MaxContrast.value())
            # clear content on the waveformLabel
            self.ui.YZplane.clear()
            # update iamge on the waveformLabel
            self.ui.YZplane.setPixmap(pixmap)
            
            plane = np.transpose(data[1,:,:]).copy()
            pixmap = ImagePlot(plane, self.ui.MinContrast.value(), self.ui.MaxContrast.value())
            # clear content on the waveformLabel
            self.ui.XZplane.clear()
            # update iamge on the waveformLabel
            self.ui.XZplane.setPixmap(pixmap)
            
            #data = ctypes.cast(data_address, ctypes.py_object).value 
            plane = np.mean(data,2)# has to be first index, otherwise the memory space is not continuous
            pixmap = ImagePlot(plane, self.ui.MinContrast.value(), self.ui.MaxContrast.value()/4)
            # clear content on the waveformLabel
            self.ui.XYplane.clear()
            # update image on the waveformLabel
            self.ui.XYplane.setPixmap(pixmap)
            
            
    def SurfFilename(self, shape):
        if self.tileNum <= self.totalTiles:
            filename = 'slice-'+str(self.sliceNum)+'-tile-'+str(self.tileNum)+'-Y'+str(shape[0])+'-X'+str(shape[1])+'-Z'+str(shape[2])+'.bin'
            self.tileNum = self.tileNum + 1
        else:
            self.sliceNum = self.sliceNum + 1
            self.tileNum = 1
            filename = 'slice-'+str(self.sliceNum)+'-tile-'+str(self.tileNum)+'-Y'+str(shape[0])+'-X'+str(shape[1])+'-Z'+str(shape[2])+'.bin'
        return filename
    
    def CscanFilename(self, shape):
        filename = 'Cscan-'+str(self.CscanNum)+'-Y'+str(shape[0])+'-X'+str(shape[1])+'-Z'+str(shape[2])+'.bin'
        self.CscanNum = self.CscanNum + 1
        return filename
    
    def BlineFilename(self, shape):
        filename = 'Bline-'+str(self.BlineNum)+'-Yrpt'+str(shape[0])+'-X'+str(shape[1])+'-Z'+str(shape[2])+'.bin'
        self.BlineNum = self.BlineNum + 1
        return filename

    def WriteData(self, data, filename):
        filePath = self.ui.DIR.toPlainText()
        filePath = filePath + "/" + filename
        # print(filePath)
        import time
        start = time.time()
        fp = open(filePath, 'wb')
        data.tofile(fp)
        fp.close()
        print('time for saving: ', time.time()-start)
        
    def dispersion_compensation(self):
        S = self.Aline.shape
        ALINE = self.Aline.reshape([S[0]*S[1],S[2]])-0.5

        Aline = ALINE[0,:]
        L=len(Aline)
        fR=np.fft.fft(Aline)/L # FFT of interference signal
        import matplotlib.pyplot as plt
        # plt.figure()
        # plt.plot(range(L),np.abs(fR))
        z = np.argmax(np.abs(fR[20:L//2-20]))
        low_position = max(10,z-100)
        high_position = min(L//2,z+100)
        fR[0:low_position]=0
        fR[high_position:L-high_position]=0
        fR[L-low_position:-1]=0
        
        Aline = np.fft.ifft(fR)
        from scipy.signal import hilbert
        hR=hilbert(np.real(Aline))
        hR_phi=np.unwrap(np.angle(hR))
        
        phi_delta=np.linspace(hR_phi[0],hR_phi[L-1],L)
        phi_diff=np.float32(phi_delta-hR_phi)
        ALINE = ALINE*np.exp(1j*phi_diff)
 
        fR = np.fft.fft(ALINE, axis=1)/L

        fR = np.abs(fR[:,self.ui.DepthStart.value():self.ui.DepthStart.value()+self.ui.DepthRange.value()])
        self.ui.MaxContrast.setValue(0.1)
        self.Display_aline(fR, raw = False)
        
        filePath = self.ui.DIR.toPlainText()
        import datetime
        current_time = datetime.datetime.now()
        filePath = filePath + "/" + 'dispersion_compensation_'+\
            str(current_time.year)+'-'+\
            str(current_time.month)+'-'+\
            str(current_time.day)+'-'+\
            str(current_time.hour)+'-'+\
            str(current_time.minute)+\
            '.bin'
        fp = open(filePath, 'wb')
        phi_diff.tofile(fp)
        fp.close()
        
        self.ui.Disp_DIR.setText(filePath)
        