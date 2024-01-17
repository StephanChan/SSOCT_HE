# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 18:26:44 2023

@author: admin
"""

from PyQt5.QtCore import  QThread
from Generaic_functions import LinePlot, ImagePlot
import numpy as np
import traceback

class DSPThread(QThread):
    def __init__(self, ui, DspQueue):
        super().__init__()
        self.queue = DspQueue
        self.ui = ui
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
                    
                    self.Display_aline(self.item.data, self.item.args)
                
                elif self.item.action in ['SingleBline','RptBline']:
                    self.Display_bline(self.item.data)
                    
                elif self.item.action in ['SingleCscan','RptCscan']:
                    self.Display_Cscan(self.item.data)
                elif self.item.action == 'SurfScan':
                    self.Display_SurfScan(self.item.data, self.item.args)
                
                elif self.item.action == 'Clear':
                    self.surf = []
                    
                else:
                    self.ui.statusbar.showMessage('Display thread is doing something invalid' + self.item.action)
            except Exception as error:
                print("\nAn error occurred:", error,' skip the display action\n')
                print(traceback.format_exc())
            self.item = self.queue.get()
        print('Display Thread successfully exited')
            

    def Display_aline(self, data, raw = False):
        #data = ctypes.cast(data_address, ctypes.py_object).value 
        # TODO: make sure fft is shifted
        if not raw:
            Zpixels = self.ui.DepthRange.value()
        else:
            Zpixels = self.ui.PreSamples.value() + self.ui.PostSamples.value()
        Xpixels = 100
        Yrpt = self.ui.BlineAVG.value()
        data = data.reshape([Yrpt,Xpixels,Zpixels])
        
        data = np.mean(data,0)
        data = data[0,:]
        if not raw:
            data=np.log10(data)
        else:
            data = data/pow(2,16)
        pixmap = LinePlot(data, [], self.ui.MinContrast.value(), self.ui.MaxContrast.value())
        # clear content on the waveformLabel
        self.ui.XYplane.clear()
        # update iamge on the waveformLabel
        self.ui.XYplane.setPixmap(pixmap)
    
    def Display_bline(self, data):
        Zpixels = self.ui.DepthRange.value()
        Xpixels = self.ui.Xsteps.value()*self.ui.AlineAVG.value()
        Yrpt = self.ui.BlineAVG.value()
        
        data = data.reshape([Yrpt,Xpixels,Zpixels])
        # if Yrpt > 1:
        data = np.mean(data,0)
        
        # data = data[0,:,:]
        data = np.transpose(data).copy()
        # print(data.shape)
        # print(data[0,0])
        
        pixmap = ImagePlot(data, self.ui.MinContrast.value(), self.ui.MaxContrast.value())
        # clear content on the waveformLabel
        self.ui.XYplane.clear()
        # update iamge on the waveformLabel
        self.ui.XYplane.setPixmap(pixmap)
        
        if self.ui.Save.isChecked():
            self.WriteData(data, self.BlineFilename([Yrpt,Xpixels,Zpixels]))
        
    def Display_Cscan(self, data):
        Zpixels = self.ui.DepthRange.value()
        Xpixels = self.ui.Xsteps.value()*self.ui.AlineAVG.value()
        Ypixels = self.ui.Ysteps.value()*self.ui.BlineAVG.value()
        data = data.reshape([Ypixels,Xpixels,Zpixels])
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
            self.WriteData(data, self.CscanFilename([Ypixels,Xpixels,Zpixels]))
        
    def Display_SurfScan(self, data, args):
        Zpixels = self.ui.DepthRange.value()
        Xpixels = self.ui.Xsteps.value()*self.ui.AlineAVG.value()
        Ypixels = self.ui.Ysteps.value()*self.ui.BlineAVG.value()
        data = data.reshape([Ypixels,Xpixels,Zpixels])
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
            self.WriteData(data, self.SurfFilename([Ypixels*20,Xpixels*20,Zpixels]))
            
    def SurfFilename(self, shape):
        if self.tileNum <= self.totalTiles:
            filename = 'slice-'+str(self.sliceNum)+'-tile-'+str(self.tileNum)+'-Y'+str(shape[0])+'-X'+str(shape[1])+'-Z'+str(shape[2])+'.dat'
            self.tileNum = self.tileNum + 1
        else:
            self.sliceNum = self.sliceNum + 1
            self.tileNum = 1
            filename = 'slice-'+str(self.sliceNum)+'-tile-'+str(self.tileNum)+'-Y'+str(shape[0])+'-X'+str(shape[1])+'-Z'+str(shape[2])+'.dat'
        return filename
    
    def CscanFilename(self, shape):
        filename = 'Cscan-'+str(self.CscanNum)+'-Y'+str(shape[0])+'-X'+str(shape[1])+'-Z'+str(shape[2])+'.dat'
        self.CscanNum = self.CscanNum + 1
        return filename
    
    def BlineFilename(self, shape):
        filename = 'Bline-'+str(self.BlineNum)+'-Yrpt'+str(shape[0])+'-X'+str(shape[1])+'-Z'+str(shape[2])+'.dat'
        self.BlineNum = self.BlineNum + 1
        return filename
        
    def WriteData(self, data, filename):
        filePath = self.ui.DIR.toPlainText()
        filePath = filePath + "\\" + filename
        # print(filePath)
        with open(filePath, "wb") as file:
            file.write(data)
            file.close()