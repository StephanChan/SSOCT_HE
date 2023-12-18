# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 16:49:35 2023

@author: admin
"""
from PyQt5.QtCore import  QThread
import time
import numpy as np
from Generaic_functions import *
from Actions import DisplayAction, SaveAction, GPUAction

class ACQThread(QThread):
    def __init__(self, ui, AcqQueue, DisplayQueue, SaveQueue, GPUQueue):
        super().__init__()
        self.ui = ui
        self.queue = AcqQueue
        self.displayQueue = DisplayQueue
        self.SaveQueue = SaveQueue
        self.GPUQueue = GPUQueue
        
    def run(self):
        self.QueueOut()
        
    def QueueOut(self):
        self.item = self.queue.get()
        while self.item.action != 'exit':
            self.ui.statusbar.showMessage('ACQ thread is doing: '+self.item.action)
            if self.item.action == 'RptBline':
                self.RptBline()
            
            elif self.item.action == 'RptAline':
                self.RptAline()
                
            elif self.item.action == 'RptCscan':
                self.RptCscan()
            elif self.item.action == 'SingleBline':
                self.RptBline()
            
            elif self.item.action == 'SingleAline':
                self.RptAline()
                
            elif self.item.action == 'SingleCscan':
                self.RptCscan()
                
            else:
                self.ui.statusbar.showMessage('ACQ thread is doing something invalid: '+self.item.action)
            
            self.item = self.queue.get()
            
    def RptBline(self):
        # ready DO for enabling trigger
        # ready digitizer
        # start digitizer
        # start DO 
        
        buffer = np.random.randint(0, 255, [1000, 1000], np.uint8)
        # need to pass pointer, otherwise the buffer gets duplicated
        an_action = DisplayAction('Bline', data = buffer)
        self.displayQueue.put(an_action)
        an_action = SaveAction('Save', data = buffer, filename = 'data.dat')
        self.SaveQueue.put(an_action)
        
    def RptAline(self):
        # ready DO for enabling trigger
        # ready digitizer
        # start digitizer
        # start DO 
        
        buffer = np.random.randint(0, 255, [1, 1000], np.uint8)
        # need to pass pointer, otherwise the buffer gets duplicated
        an_action = DisplayAction('Aline',data = buffer)
        self.displayQueue.put(an_action)
        
    def RptCscan(self):
        # ready DO for enabling trigger
        # ready digitizer
        # start digitizer
        # start DO 
        
        buffer = np.random.randint(0, 255, [1000, 1000, 1000], np.uint8)
        # need to pass pointer, otherwise the buffer gets duplicated
        an_action = DisplayAction('Cscan', data = buffer)
        self.displayQueue.put(an_action)
        an_action = SaveAction('Save', data = buffer, filename = 'data.dat')
        self.SaveQueue.put(an_action)
            
                
