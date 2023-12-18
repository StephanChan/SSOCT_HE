# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 18:26:44 2023

@author: admin
"""

from PyQt5.QtCore import  QThread
from Generaic_functions import ScatterPlot, LinePlot, ImagePlot
import numpy as np

class DSPThread(QThread):
    def __init__(self, DspQueue, ui):
        super().__init__()
        self.queue = DspQueue
        self.ui = ui
        
    def run(self):
        self.QueueOut()
        
    def QueueOut(self):
        self.item = self.queue.get()
        while self.item.action != 'exit':
            self.ui.statusbar.showMessage('Display thread is doing ' + self.item.action)
            if self.item.action == 'Aline':
                
                self.Display_aline(self.item.data)
            
            elif self.item.action == 'Bline':
                self.Display_bline(self.item.data)
                
            elif self.item.action == 'Cscan':
                self.Display_Cscan(self.item.data)
                
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
        #data = ctypes.cast(data_address, ctypes.py_object).value 
        plane = data[1,:,:] # has to be first index, otherwise the memory space is not continuous
        pixmap = ImagePlot(plane)
        # clear content on the waveformLabel
        self.ui.XYplane.clear()
        # update iamge on the waveformLabel
        self.ui.XYplane.setPixmap(pixmap)
        
        # plane1 = data[:,:,1].T
        plane = np.transpose(data[:,:,1]).copy()
        pixmap = ImagePlot(plane)
        # clear content on the waveformLabel
        self.ui.YZplane.clear()
        # update iamge on the waveformLabel
        self.ui.YZplane.setPixmap(pixmap)