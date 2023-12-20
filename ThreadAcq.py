# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 16:49:35 2023

@author: admin
"""
from PyQt5.QtCore import  QThread
import time
import numpy as np
from Generaic_functions import *
from Actions import DisplayAction, StageAction, SaveAction

class ACQThread(QThread):
    def __init__(self, ui, AcqQueue, DisplayQueue, StageQueue, PauseQueue, SaveQueue, Ynum):
        super().__init__()
        self.ui = ui
        self.queue = AcqQueue
        self.displayQueue = DisplayQueue
        self.StageQueue = StageQueue
        self.pauseQueue = PauseQueue
        self.SaveQueue = SaveQueue
        self.sliceNum = 1
        self.tileNum = 1
        self.mosaic = None
        self.Ynum = Ynum
        self.totalTiles = 0
        
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
                self.SingleBline()
            
            elif self.item.action == 'SingleAline':
                self.SingleAline()
                
            elif self.item.action == 'SingleCscan':
                self.SingleCscan()
                
            elif self.item.action == 'SurfScan':
                self.SurfScan()
                
            elif self.item.action == 'SurfScan+Slice':
                self.SurfSlice()
                
            else:
                self.ui.statusbar.showMessage('ACQ thread is doing something invalid: '+self.item.action)
            
            self.item = self.queue.get()
            
    def SingleBline(self):
        buffer = np.random.randint(0, 255, [500, 1000], np.uint8)
        # need to pass pointer, otherwise the buffer gets duplicated
        an_action = DisplayAction('Bline', buffer)
        self.displayQueue.put(an_action)
        if self.ui.Save.isChecked():
            an_action = SaveAction('Save', buffer, 'Bline.dat')
            self.SaveQueue.put(an_action)
            
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
                self.SingleBline()
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
       
    def SingleAline(self):
        buffer = np.random.randint(0, 255, 1000, np.uint8)
        # need to pass pointer, otherwise the buffer gets duplicated
        an_action = DisplayAction('Aline',buffer)
        self.displayQueue.put(an_action)
        time.sleep(0.3)
        
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
                self.SingleAline()
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

    def SingleCscan(self):
        # ready DO for enabling trigger
        # ready digitizer
        # start digitizer
        # start DO 
        buffer = np.random.randint(0, 255, [500, 1000, self.Ynum], np.uint8)
        # need to pass pointer, otherwise the buffer gets duplicated
        an_action = DisplayAction('Cscan', buffer)
        self.displayQueue.put(an_action)
        if self.ui.Save.isChecked():
            an_action = SaveAction('Save', buffer, self.NextFilename())
            self.SaveQueue.put(an_action)
        
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
                self.SingleCscan()
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
        
            
            
    def SurfScan(self):
        interrupt = None
        # generate Mosaic pattern
        self.Mosaic, status = GenMosaic_XGalvo(self.ui.XStart.value(),\
                                        self.ui.XStop.value(),\
                                        self.ui.YStart.value(),\
                                        self.ui.YStop.value(),\
                                        self.ui.Xsteps.value()*self.ui.XStepSize.value()/1000,\
                                        self.ui.Overlap.value())
        # ready DO for enabling trigger
        # ready digitizer
        # start digitizer
        # start DO 
        # calculate the number of Cscans per stripe
        CscansPerStrip = np.int16((self.ui.YStop.value()-self.ui.YStart.value())*1000\
            /(self.ui.YStepSize.value()/self.ui.BlineAVG.value()*self.Ynum))
        # calculate the total number of tiles per slice
        self.totalTiles = CscansPerStrip*len(self.Mosaic)
        ############################################################# Iterate through strips in one slice
        stripes = 1
        while np.any(self.Mosaic): 
            # move to start
            files = 0
            ############################################################  iterate through Cscans in one stripe
            while files < CscansPerStrip: 
                try:
                   interrupt = self.pauseQueue.get(timeout=0.01)  # time out 0.01 s
                except:
                    # normally, acquiring next Cscan
                    buffer = np.random.randint(0, 255, [500, 1000, self.Ynum], np.uint8)
                    time.sleep(0.5)
                    args = [[files, stripes], [CscansPerStrip, self.totalTiles],[1000,self.Ynum]]
                    an_action = DisplayAction('SurfScan', buffer, args)
                    self.displayQueue.put(an_action)
                    if self.ui.Save.isChecked():
                        an_action = SaveAction('Save', buffer, self.NextFilename())
                        self.SaveQueue.put(an_action)
                    files = files+1
                    self.ui.statusbar.showMessage('Imaging '+str(stripes)+'th strip, '+str(files+1)+'th Cscan ')
                # if pause is cliced, pause acquisition
                if interrupt == 'Pause':
                    while interrupt == 'Pause':
                        time.sleep(0.2)
                        try:
                            interrupt = self.pauseQueue.get(timeout=0.01)  # time out 0.01 s
                        except:
                            pass
                # if stop is clicked, stop acquisition
                if interrupt == 'Stop':
                    # stop while loop
                    self.Mosaic = [self.Mosaic[-1]]
                    break
            self.Mosaic = np.delete(self.Mosaic, 0)
            stripes = stripes + 1
            
        an_action = DisplayAction('Clear')
        self.displayQueue.put(an_action)
        self.ui.RunButton.setChecked(False)
        self.ui.RunButton.setText('Run')
        
    def SurfSlice(self):
        # cut one slice
        # do surf
        for islice in range(3):
            self.SurfScan()
        self.ui.RunButton.setChecked(False)
        self.ui.RunButton.setText('Run')
        
    def NextFilename(self):
        if self.tileNum <= self.totalTiles:
            filename = 'slice-'+str(self.sliceNum)+'-tile-'+str(self.tileNum)+'.dat'
            self.tileNum = self.tileNum + 1
        else:
            self.sliceNum = self.sliceNum + 1
            self.tileNum = 1
            filename = 'slice-'+str(self.sliceNum)+'-tile-'+str(self.tileNum)+'.dat'
        return filename