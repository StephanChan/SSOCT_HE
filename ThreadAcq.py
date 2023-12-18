# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 16:49:35 2023

@author: admin
"""
from PyQt5.QtCore import  QThread
import time
import numpy as np
from Generaic_functions import *
from Actions import DisplayAction, StageAction

class ACQThread(QThread):
    def __init__(self, ui, AcqQueue, DisplayQueue, StageQueue, PauseQueue):
        super().__init__()
        self.ui = ui
        self.queue = AcqQueue
        self.displayQueue = DisplayQueue
        self.StageQueue = StageQueue
        self.pauseQueue = PauseQueue
        self.sliceNum = 0
        self.tileNum = 0
        self.mosaic = None
        
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
                
            elif self.item.action == 'SurfScan':
                self.SurfScan()
                
            else:
                self.ui.statusbar.showMessage('ACQ thread is doing something invalid: '+self.item.action)
            
            self.item = self.queue.get()
            
    def RptBline(self):
        # ready DO for enabling trigger
        # ready digitizer
        # start digitizer
        # start DO 
        interrupt = None
        while True:
            try:
               interrupt = self.pauseQueue.get(timeout=0.01)  # time out 0.01 s
            except:
                buffer = np.random.randint(0, 255, [300, 1000], np.uint8)
                # need to pass pointer, otherwise the buffer gets duplicated
                an_action = DisplayAction('Bline', buffer)
                self.displayQueue.put(an_action)
                if self.ui.Save.isChecked():
                    self.WriteData(buffer, self.NextFilename())
            if interrupt == 'Pause':
                while interrupt == 'Pause':
                    time.sleep(0.2)
                    try:
                        interrupt = self.pauseQueue.get(timeout=0.01)  # time out 0.01 s
                    except:
                        pass
            if interrupt == 'Stop':
                # stop while loop
                break
       
        
    def RptAline(self):
        # ready DO for enabling trigger
        # ready digitizer
        # start digitizer
        # start DO 
        interrupt = None
        while True:
            try:
               interrupt = self.pauseQueue.get(timeout=0.01)  # time out 0.01 s
            except:
                buffer = np.random.randint(0, 255, 1000, np.uint8)
                # need to pass pointer, otherwise the buffer gets duplicated
                an_action = DisplayAction('Aline',buffer)
                self.displayQueue.put(an_action)
                time.sleep(0.3)
            if interrupt == 'Pause':
                while interrupt == 'Pause':
                    time.sleep(0.2)
                    try:
                        interrupt = self.pauseQueue.get(timeout=0.01)  # time out 0.01 s
                    except:
                        pass
            if interrupt == 'Stop':
                # stop while loop
                break
        
        
    def RptCscan(self):
        # ready DO for enabling trigger
        # ready digitizer
        # start digitizer
        # start DO 
        interrupt = None
        while True:
            try:
               interrupt = self.pauseQueue.get(timeout=0.01)  # time out 0.01 s
            except:
                buffer = np.random.randint(0, 255, [300, 1000, 1000], np.uint8)
                # need to pass pointer, otherwise the buffer gets duplicated
                an_action = DisplayAction('Cscan', buffer)
                self.displayQueue.put(an_action)
                if self.ui.Save.isChecked():
                    self.WriteData(buffer, self.NextFilename())
            if interrupt == 'Pause':
                while interrupt == 'Pause':
                    time.sleep(0.2)
                    try:
                        interrupt = self.pauseQueue.get(timeout=0.01)  # time out 0.01 s
                    except:
                        pass
            if interrupt == 'Stop':
                # stop while loop
                break
        
            
    def WriteData(self, data, filename):
        filePath = self.ui.DIR.toPlainText()
        filePath = filePath + "\\" + filename
        # print(filePath)
        with open(filePath, "wb") as file:
            file.write(data)
            file.close()
            
    def SurfScan(self):
        interrupt = None
        # generate Mosaic pattern
        self.Mosaic, status = GenMosaic(self.ui.XStart.value(),\
                                        self.ui.XStop.value(),\
                                        self.ui.YStart.value(),\
                                        self.ui.YStop.value(),\
                                        self.ui.FOV.value(),\
                                        self.ui.Overlap.value())
        self.Mosaic = self.Mosaic[0]
        # ready DO for enabling trigger
        # ready digitizer
        # start digitizer
        # start DO 
        while np.any(self.Mosaic):
            try:
               interrupt = self.pauseQueue.get(timeout=0.01)  # time out 0.01 s
            except:
                # normally, acquiring next Cscan
                buffer = np.random.randint(0, 255, [300, 1000, 1000], np.uint8)
                # need to pass pointer, otherwise the buffer gets duplicated
                an_action = DisplayAction('Cscan', buffer)
                self.displayQueue.put(an_action)
                if self.ui.Save.isChecked():
                    self.WriteData(buffer, self.NextFilename())
                self.Mosaic = self.Mosaic[1:]
            if interrupt == 'Pause':
                while interrupt == 'Pause':
                    time.sleep(0.2)
                    try:
                        interrupt = self.pauseQueue.get(timeout=0.01)  # time out 0.01 s
                    except:
                        pass
            if interrupt == 'Stop':
                # stop while loop
                break
            
    def NextFilename(self):
        return 'slice-'+str(self.sliceNum)+'tile-'+str(self.tileNum)+'.dat'
        