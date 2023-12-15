# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 16:49:35 2023

@author: admin
"""
from PyQt5.QtCore import  QThread
import time
import numpy as np
from Generaic_functions import *
from Actions import *

class ACQThread(QThread):
    def __init__(self, AcqQueue, DisplayQueue):
        super().__init__()
        self.buffer1 = None
        self.buffer2 = None
        self.queue = AcqQueue
        self.displayQueue = DisplayQueue
        
    def run(self):
        self.QueueOut()
        
    def QueueOut(self):
        self.item = self.queue.get()
        while self.item.action != 'exit':
            if self.item.action == 'Initmemory':
                print('ACQ thread is doing ',self.item.action)
                self.Init2MemoryBuffers(self.item.args)
            
            elif self.item.action == 'GenAODO':
                print('ACQ thread is doing ',self.item.action)
                # self.DOwaveform, self.AOwaveform, status = GenAODO(self.item.args)
                
            elif self.item.action == 'StartACQ':
                if self.item.args == 'RptBline':
                    self.RptBline()
                
            else:
                print('invalid action!')
            
            self.item = self.queue.get()
        del self.buffer1
        del self.buffer2
            
    def RptBline(self):
        size = self.buffer1.shape
        # ready DO for enabling trigger
        # ready digitizer
        # start digitizer
        # start DO 
        # data into memory space 1
        bline=0
        while bline < size[0]:
            self.buffer1[bline,:] = np.random.random(size[1])
            bline=bline+1
        
        # need to pass pointer, otherwise the buffer gets duplicated
        display_action = Displayaction('Bline', args = self.buffer1)
        self.displayQueue.put(display_action)
            
    def Init2MemoryBuffers(self, args):
        mode = args[0]
        FFTsamples = args[1]
        Xsteps = args[2]
        avg = args[3]
        if mode in  ['RptAline', 'SingleAline']:
            self.buffer1 = np.zeros([1,np.uint32(FFTsamples/2*1000)],dtype=np.uint16)
            self.buffer2 = np.zeros([1,np.uint32(FFTsamples/2*1000)],dtype=np.uint16)
        elif mode in ['RptBline', 'SingleBline']:
            self.buffer1 = np.zeros([1000,np.uint32(FFTsamples/2*Xsteps*avg)],dtype=np.uint16)
            self.buffer2 = np.zeros([1000,np.uint32(FFTsamples/2*Xsteps*avg)],dtype=np.uint16)
                
