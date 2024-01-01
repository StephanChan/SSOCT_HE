# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 16:49:35 2023

@author: admin
"""
from PyQt5.QtCore import  QThread
import time
import numpy as np
from Generaic_functions import *
from Actions import DisplayAction, AODOAction, SaveAction

class ACQThread(QThread):
    def __init__(self, ui, AcqQueue, DisplayQueue, AODOQueue, PauseQueue):
        super().__init__()
        self.ui = ui
        self.queue = AcqQueue
        self.displayQueue = DisplayQueue
        self.AODOQueue = AODOQueue
        self.pauseQueue = PauseQueue

        self.mosaic = None

        
    def run(self):
        self.QueueOut()
        
    def QueueOut(self):
        self.item = self.queue.get()
        while self.item.action != 'exit':
            self.ui.statusbar.showMessage('ACQ thread is doing: '+self.item.action)
            if self.item.action == 'RptBline':
                self.ui.statusbar.showMessage(self.RptBline())
            
            elif self.item.action == 'RptAline':
                self.ui.statusbar.showMessage(self.RptAline())
                
            elif self.item.action == 'RptCscan':
                self.ui.statusbar.showMessage(self.RptCscan())
                
            elif self.item.action == 'SingleBline':
                self.ui.statusbar.showMessage(self.SingleBline())
            
            elif self.item.action == 'SingleAline':
                self.ui.statusbar.showMessage(self.SingleAline())
                
            elif self.item.action == 'SingleCscan':
                self.ui.statusbar.showMessage(self.SingleCscan())
                
            elif self.item.action == 'SurfScan':
                interrupt, status = self.SurfScan()
                self.ui.statusbar.showMessage(status)
                
            elif self.item.action == 'SurfScan+Slice':
                self.ui.statusbar.showMessage(self.SurfSlice())
                
            else:
                self.ui.statusbar.showMessage('ACQ thread is doing something invalid: '+self.item.action)
            
            self.item = self.queue.get()
            
    def SingleBline(self):
        # ready digitizer
        # start digitizer
        # ready AODO for 1 bline measurement and start
        an_action = AODOAction('ConfigAODO')
        self.AODOQueue.put(an_action)
        an_action = AODOAction('StartOnce')
        self.AODOQueue.put(an_action)
        # collect data from digitizer, data format: [X pixels, Z pixels]
        buffer = np.random.randint(0, 255, [self.ui.Xsteps.value()*self.ui.AlineAVG.value(), 200], np.uint8)
        # display and save
        an_action = DisplayAction('Bline', buffer)
        self.displayQueue.put(an_action)
        an_action = AODOAction('CloseTask')
        self.AODOQueue.put(an_action)
        return 'SingleBline successfully finished'
            
    def RptBline(self):
        # ready digitizer
        # start digitizer
        # start DO 
        an_action = AODOAction('ConfigAODO')
        self.AODOQueue.put(an_action)
        an_action = AODOAction('StartContinuous')
        self.AODOQueue.put(an_action)
        self.PauseUnpause('Bline')
        return 'RptBline successfully stopped'
       
    def SingleAline(self):
        # ready digitizer
        # start digitizer
        an_action = AODOAction('ConfigAODO')
        self.AODOQueue.put(an_action)
        an_action = AODOAction('StartOnce')
        self.AODOQueue.put(an_action)
        # collect data from digitizer
        buffer = np.random.randint(0, 255, 1000, np.uint8)
        # display aline
        an_action = DisplayAction('Aline', buffer)
        self.displayQueue.put(an_action)
        an_action = AODOAction('CloseTask')
        self.AODOQueue.put(an_action)
        return 'SingleAline successfully finished'
        
    def RptAline(self):
        # ready digitizer
        # start digitizer
        # start DO 
        an_action = AODOAction('ConfigAODO')
        self.AODOQueue.put(an_action)
        an_action = AODOAction('StartContinuous')
        self.AODOQueue.put(an_action)
        self.PauseUnpause('Aline')
        return 'RptAline successfully stopped'

    def SingleCscan(self):
        # ready digitizer
        # start digitizer
        # ready AODO for 1 bline measurement and start
        an_action = AODOAction('ConfigAODO')
        self.AODOQueue.put(an_action)
        an_action = AODOAction('StartOnce')
        self.AODOQueue.put(an_action)
        # collect data from digitizer, data format: [Y pixels, X pixels, Z pixels]
        buffer = np.random.randint(0, 255, [self.ui.Ysteps.value()*self.ui.BlineAVG.value(), self.ui.Xsteps.value()*self.ui.AlineAVG.value(), 200], np.uint8)
        # display and save
        an_action = DisplayAction('Cscan', buffer)
        self.displayQueue.put(an_action)
        an_action = AODOAction('CloseTask')
        self.AODOQueue.put(an_action)
        return 'SingleCscan successfully finished'
        
    def RptCscan(self):
        # ready digitizer
        # start digitizer
        # start DO 
        an_action = AODOAction('ConfigAODO')
        self.AODOQueue.put(an_action)
        an_action = AODOAction('StartContinuous')
        self.AODOQueue.put(an_action)
        self.PauseUnpause('Cscan')
        return 'RptCscan successfully stopped'
        
            
            
    def SurfScan(self):
        # generate Mosaic pattern, a Mosaic pattern consists of a list of MOSAIC object, 
        # each MOSAIC object defines a stripe of scanning area, which is defined by the X stage position, and Y stage start and stop position
        self.Mosaic, status = GenMosaic_XGalvo(self.ui.XStart.value(),\
                                        self.ui.XStop.value(),\
                                        self.ui.YStart.value(),\
                                        self.ui.YStop.value(),\
                                        self.ui.Xsteps.value()*self.ui.XStepSize.value()/1000,\
                                        self.ui.Overlap.value())

        # calculate the number of Cscans per stripe
        CscansPerStripe = np.int16((self.ui.YStop.value()-self.ui.YStart.value())*1000\
            /(self.ui.YStepSize.value()*self.ui.BlineAVG.value()*self.ui.Ysteps.value()))
        if CscansPerStripe <=0:
            return 'invalid Mosaic positions, abort aquisition'
        # calculate the total number of tiles per slice
        self.totalTiles = CscansPerStripe*len(self.Mosaic)
        if self.totalTiles <=0:
            return 'invalid Mosaic positions, abort aquisition'
        ############################################################# Iterate through strips for one surfscan
        # ready digitizer
        # start digitizer
        # configure AODO
        an_action = AODOAction('ConfigAODO')
        self.AODOQueue.put(an_action)
        
        interrupt = None
        stripes = 1
        while np.any(self.Mosaic): 
            # move to start of this stripe
            files = 0
            an_action = AODOAction('StartOnce')
            self.AODOQueue.put(an_action)
            ############################################################  iterate through Cscans in one stripe
            while files < CscansPerStripe: 
                # collect next Cscan data
                buffer = np.random.randint(0, 255, [self.ui.Ysteps.value()*self.ui.BlineAVG.value(), self.ui.Xsteps.value()*self.ui.AlineAVG.value(), 200], np.uint8)
                time.sleep(3)
                try:
                    # check is acquisition has been paused
                   interrupt = self.pauseQueue.get(timeout=0.01)  # time out 0.01 s
                except:
                    # acquisition not paused, start next Cscan
                    an_action = AODOAction('StartOnce')
                    self.AODOQueue.put(an_action)
            # process this Cscan data
                # FFT using GPU
                time.sleep(1)
                # display and save
                # args = [files, stripes], [total scans per stripe, total tiles], [X pixels, Y pixels]
                args = [[files, stripes], [CscansPerStripe, self.totalTiles],[self.ui.Xsteps.value()*self.ui.AlineAVG.value(),self.ui.Ysteps.value()*self.ui.BlineAVG.value()]]
                an_action = DisplayAction('SurfScan', buffer, args)
                self.displayQueue.put(an_action)
                files +=1
                self.ui.statusbar.showMessage('Imaging '+str(stripes)+'th strip, '+str(files+1)+'th Cscan ')
                # if Pause button is clicked
                if interrupt == 'Pause':
                    # wait until unpause button or stop button is clicked
                    while interrupt == 'Pause':
                        time.sleep(0.2)
                        try:
                            interrupt = self.pauseQueue.get()  # never time out
                        except:
                            pass
                # if Stop button is clicked
                if interrupt == 'Stop':
                    # stop while loop
                    an_action = AODOAction('CloseTask')
                    self.AODOQueue.put(an_action)
                    self.Mosaic = [self.Mosaic[-1]]
                    break
                # if unpause button is clicked        
                if interrupt == 'unPause':
                    if files < CscansPerStripe: 
                        an_action = AODOAction('StartOnce')
                        self.AODOQueue.put(an_action)
            # finishing this stripe, delete one MOSAIC object from the mosaic pattern
            self.Mosaic = np.delete(self.Mosaic, 0)
            stripes = stripes + 1
        # # clear display windows
        # an_action = DisplayAction('Clear')
        # self.displayQueue.put(an_action)
        # reset RUN button
        self.ui.RunButton.setChecked(False)
        self.ui.RunButton.setText('Run')
        return interrupt, 'SurfScan successfully finished'
        
    def SurfSlice(self):
        # cut one slice
        # do surf
        for islice in range(3):
            interrupt, status = self.SurfScan()
            if interrupt == 'Stop':
                break
        self.ui.RunButton.setChecked(False)
        self.ui.RunButton.setText('Run')
        
    def PauseUnpause(self, mode):
        interrupt = None
        # repeat acquisition until Stop button is clicked
        while True:
            try:
               interrupt = self.pauseQueue.get(timeout=0.01)  # time out 0.01 s
            except:
                # collect data from digitizer
                if mode == 'Aline':
                    buffer = np.random.randint(0, 255, 1000, np.uint8)
                    time.sleep(0.3)
                elif mode == 'Bline':
                    buffer = np.random.randint(0, 255, [self.ui.Xsteps.value()*self.ui.AlineAVG.value(),200], np.uint8)
                elif mode == 'Cscan':
                    buffer = np.random.randint(0, 255, [self.ui.Ysteps.value()*self.ui.BlineAVG.value(), self.ui.Xsteps.value()*self.ui.AlineAVG.value(), 200], np.uint8)
                    time.sleep(2)
                # display
                an_action = DisplayAction(mode, buffer)
                self.displayQueue.put(an_action)
            # if Pause button is clicked
            if interrupt == 'Pause':
                # pause acquisition
                an_action = AODOAction('StopContinuous')
                self.AODOQueue.put(an_action)
                # wait until unpause button or stop button is clicked
                while interrupt == 'Pause':
                    time.sleep(0.2)
                    try:
                        interrupt = self.pauseQueue.get()  # never time out
                        print(interrupt)
                    except:
                        pass
            # if Stop button is clicked
            if interrupt == 'Stop':
                # stop while loop
                an_action = AODOAction('StopContinuous')
                self.AODOQueue.put(an_action)
                an_action = AODOAction('CloseTask')
                self.AODOQueue.put(an_action)
                break
            # if unpause button is clicked        
            if interrupt == 'unPause':
                interrupt == None
                an_action = AODOAction('StartContinuous')
                self.AODOQueue.put(an_action)