# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 18:26:44 2023

@author: admin
"""

from PyQt5.QtCore import  QThread
from Generaic_functions import ScatterPlot, LinePlot, ImagePlot
import numpy as np

class DSPThread(QThread):
    def __init__(self, ui, DspQueue):
        super().__init__()
        self.queue = DspQueue
        self.ui = ui
        self.surf = []
        
    def run(self):
        self.QueueOut()
        
    def QueueOut(self):
        self.item = self.queue.get()
        while self.item.action != 'exit':
            #self.ui.statusbar.showMessage('Display thread is doing ' + self.item.action)
            if self.item.action == 'Aline':
                
                self.Display_aline(self.item.data)
            
            elif self.item.action == 'Bline':
                self.Display_bline(self.item.data)
                
            elif self.item.action == 'Cscan':
                self.Display_Cscan(self.item.data)
            elif self.item.action == 'SurfScan':
                self.Display_SurfScan(self.item.data, self.item.args)
            
            elif self.item.action == 'Clear':
                self.surf = []
                
            else:
                self.ui.statusbar.showMessage('Display thread is doing something invalid' + self.item.action)
            
            self.item = self.queue.get()
            

    def Display_aline(self, data):
        #data = ctypes.cast(data_address, ctypes.py_object).value 
        pixmap = LinePlot(data)
        # clear content on the waveformLabel
        self.ui.XYplane.clear()
        # update iamge on the waveformLabel
        self.ui.XYplane.setPixmap(pixmap)
    
    def Display_bline(self, data):
        #data = ctypes.cast(data_address, ctypes.py_object).value 
        pixmap = ImagePlot(data)
        # clear content on the waveformLabel
        self.ui.XYplane.clear()
        # update iamge on the waveformLabel
        self.ui.XYplane.setPixmap(pixmap)
        
    def Display_Cscan(self, data):
        plane = np.transpose(data[:,1,:]).copy()
        pixmap = ImagePlot(plane)
        # clear content on the waveformLabel
        self.ui.YZplane.clear()
        # update iamge on the waveformLabel
        self.ui.YZplane.setPixmap(pixmap)
        
        plane = np.transpose(data[:,:,1]).copy()
        pixmap = ImagePlot(plane)
        # clear content on the waveformLabel
        self.ui.XZplane.clear()
        # update iamge on the waveformLabel
        self.ui.XZplane.setPixmap(pixmap)
        
        #data = ctypes.cast(data_address, ctypes.py_object).value 
        plane = np.transpose(data[1,:,:]).copy()# has to be first index, otherwise the memory space is not continuous
        pixmap = ImagePlot(plane)
        # clear content on the waveformLabel
        self.ui.XYplane.clear()
        # update iamge on the waveformLabel
        self.ui.XYplane.setPixmap(pixmap)
        
    def Display_SurfScan(self, data, args):

        plane = np.transpose(data[:,:,1]).copy()
        pixmap = ImagePlot(plane)
        # clear content on the waveformLabel
        self.ui.YZplane.clear()
        # update iamge on the waveformLabel
        self.ui.YZplane.setPixmap(pixmap)
        
        plane = np.transpose(data[:,1,:]).copy()
        pixmap = ImagePlot(plane)
        # clear content on the waveformLabel
        self.ui.XZplane.clear()
        # update iamge on the waveformLabel
        self.ui.XZplane.setPixmap(pixmap)
        
        #data = ctypes.cast(data_address, ctypes.py_object).value 
        plane = np.transpose(data[1,:,:]).copy()# has to be first index, otherwise the memory space is not continuous
        pixmap = ImagePlot(plane)
        # clear content on the waveformLabel
        self.ui.XYplane.clear()
        # update iamge on the waveformLabel
        self.ui.XYplane.setPixmap(pixmap)
        
        if np.any(args):
            fileX = args[0][0]
            fileY = args[0][1]-1
            surfX = args[1][0]
            surfY = np.int32(args[1][1]/args[1][0])
            CscanX = np.int32(args[2][0]/10)
            CscanY = np.int32(args[2][1]/10)
            if np.any(self.surf):
                self.surf[CscanY*fileX:CscanY*(fileX+1),CscanX*fileY:CscanX*(fileY+1)] = np.resize(plane,[CscanY,CscanX])
                pixmap = ImagePlot(self.surf)
                # clear content on the waveformLabel
                self.ui.SampleMosaic.clear()
                # update iamge on the waveformLabel
                self.ui.SampleMosaic.setPixmap(pixmap)
            else:
                self.surf = np.zeros([ surfX*CscanY,surfY*CscanX],dtype = np.uint8)
                self.surf[CscanY*fileX:CscanY*(fileX+1),CscanX*fileY:CscanX*(fileY+1)] = np.resize(plane,[CscanY,CscanX])
                pixmap = ImagePlot(self.surf)
                # clear content on the waveformLabel
                self.ui.SampleMosaic.clear()
                # update iamge on the waveformLabel
                self.ui.SampleMosaic.setPixmap(pixmap)
            
        
        