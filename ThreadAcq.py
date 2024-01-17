# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 16:49:35 2023

@author: admin
"""
from PyQt5.QtCore import  QThread
import time
import numpy as np
from Generaic_functions import *
from Actions import DisplayAction, AODOAction, GPUAction, BoardAction
from multiprocessing import Queue
import traceback


global memoryCount
memoryCount = 2

global Memory
Memory = list(range(memoryCount))

from ThreadGPU import GPUThread
class GPUThread2(GPUThread):
    def __init__(self, ui, GPUQueue, DisplayQueue):
            super().__init__()
            global Memory
            self.Memory = Memory
            self.ui = ui
            self.queue = GPUQueue
            self.displayQueue = DisplayQueue
            
            
from ThreadBoard import ATS9350
class ATS9350_2(ATS9350):
    def __init__(self, ui, BoardQueue, Board2ACQQueue, StopQueue):
        super().__init__()
        global Memory
        self.Memory = Memory
        self.ui = ui
        self.queue = BoardQueue
        self.Board2ACQQueue = Board2ACQQueue
        self.StopQueue = StopQueue

            
class ACQThread(QThread):
    def __init__(self, ui, AcqQueue, DisplayQueue, AODOQueue, PauseQueue):
        super().__init__()
        self.ui = ui
        self.queue = AcqQueue
        self.displayQueue = DisplayQueue
        self.AODOQueue = AODOQueue
        self.pauseQueue = PauseQueue
        self.mosaic = None
        
        global Memory
        self.Memory = Memory
        
        self.GPUQueue = Queue()
        self.BoardQueue = Queue()
        self.Board2ACQQueue = Queue()
        self.BoardStopQueue = Queue()
        
        self.GPU_thread = GPUThread2(self.ui, self.GPUQueue, self.displayQueue)
        self.GPU_thread.start()

        self.Board_thread = ATS9350_2(self.ui, self.BoardQueue, self.Board2ACQQueue, self.BoardStopQueue)
        self.Board_thread.start()
        self.exit_message = 'ACQ thread successfully exited'
        
    def run(self):
        self.QueueOut()
        
    def QueueOut(self):
        self.item = self.queue.get()
        while self.item.action != 'exit':
            self.ui.statusbar.showMessage('ACQ thread is doing: '+self.item.action)
            try:
                if self.item.action in ['RptAline','RptBline','RptCscan']:
                    self.ui.statusbar.showMessage(self.RptScan(self.item.action))
    
                    
                elif self.item.action in ['SingleBline', 'SingleAline', 'SingleCscan']:
                    self.ui.statusbar.showMessage(self.SingleScan(self.item.action))
                
                elif self.item.action == 'SurfScan':
                    interrupt, status = self.SurfScan()
                    self.ui.statusbar.showMessage(status)
                    
                elif self.item.action == 'SurfScan+Slice':
                    self.ui.statusbar.showMessage(self.SurfSlice())
                elif self.item.action == 'Window':
                    an_action = GPUAction(self.item.action)
                    self.GPUQueue.put(an_action)
                else:
                    self.ui.statusbar.showMessage('ACQ thread is doing something invalid: '+self.item.action)
            except Exception as error:
                print("An error occurred:", error,'\n skip the acquisition action\n')

                print(traceback.format_exc())
            self.item = self.queue.get()
        # stop GPU and board thread before exit
        an_action = GPUAction('exit')
        self.GPUQueue.put(an_action)
        an_action = BoardAction('exit')
        self.BoardQueue.put(an_action)
        time.sleep(0.1)
        print(self.exit_message)
            
    def SingleScan(self, mode):
        if not self.ui.SimulateBox.isChecked():
        # ready digitizer
            an_action = BoardAction('ConfigureBoard')
            self.BoardQueue.put(an_action)
            time.sleep(0.5) # first configuration takes about half second
        # ready AODO 
        an_action = AODOAction('ConfigAODO')
        self.AODOQueue.put(an_action)
        if not self.ui.SimulateBox.isChecked():
            # start digitizer
            an_action = BoardAction('StartAcquire')
            self.BoardQueue.put(an_action)
            time.sleep(0.1) # starting acquire takes less than 0.1 second, this is to make sure board started before AODO started
        # start AODO
        an_action = AODOAction('StartOnce')
        self.AODOQueue.put(an_action)
        
        if not self.ui.SimulateBox.isChecked():
            # collect data from digitizer, data format: [Y pixels, X*Z pixels]
            an_action = self.Board2ACQQueue.get() # never time out
            memoryLoc = an_action.action
        else:
            # simulate data
            memoryLoc = 0
            nSamp = (self.ui.PreSamples.value()+self.ui.PostSamples.value())
            tmp = 65535*np.random.rand()*np.sin(2*np.pi*np.random.randint(10,90)*np.arange(nSamp)/nSamp)
            if mode == 'SingleAline':
                self.Memory[memoryLoc] = np.tile(tmp,[100,1])
                time.sleep(0.1)
            elif mode == 'SingleBline':
                self.Memory[memoryLoc] = np.tile(tmp,[self.ui.BlineAVG.value(), \
                                                 self.ui.Xsteps.value()*self.ui.AlineAVG.value()])
                time.sleep(0.2)
            elif mode == 'SingleCscan':
                self.Memory[memoryLoc] = np.tile(tmp,[self.ui.Ysteps.value()*self.ui.BlineAVG.value(), \
                                                 self.ui.Xsteps.value()*self.ui.AlineAVG.value()])
                time.sleep(4)
            
        if self.ui.FFTDevice.currentText() in ['Alazar', 'None']:
            # in Alazar and None mode, directly do display and save
            data = self.Memory[memoryLoc].copy()
            
            # samples = self.ui.PreSamples.value()+self.ui.PostSamples.value()
            # Alines =np.uint32((data.shape[1])/samples) * data.shape[0]
            # data=data.reshape([Alines, samples])
            
            an_action = DisplayAction(mode, data, args=True) # data in Memory[memoryLoc]
            self.displayQueue.put(an_action)
        else:
            # In other modes, do FFT first
            an_action = GPUAction(self.ui.FFTDevice.currentText(), mode, memoryLoc)
            self.GPUQueue.put(an_action)
        
        # AODO stop automatically, but need close() explicitely
        an_action = AODOAction('CloseTask')
        self.AODOQueue.put(an_action)
        # ATS9351 will stop automatically
        return mode + ' successfully finished'
            
    
    
    def RptScan(self, mode):
        if not self.ui.SimulateBox.isChecked():
        # ready digitizer
            an_action = BoardAction('ConfigureBoard')
            self.BoardQueue.put(an_action)
            time.sleep(0.5) # wait 0.5 seconds to make sure board configuration finished before AODO start
        # ready AODO for continuous measurement
        an_action = AODOAction('ConfigAODO')
        self.AODOQueue.put(an_action)
        if not self.ui.SimulateBox.isChecked():
            # start digitizer
            an_action = BoardAction('StartAcquire')
            self.BoardQueue.put(an_action)
            time.sleep(0.1) # starting acquire takes less than 0.1 second, this is to make sure board started before AODO started
        # start AODO
        an_action = AODOAction('StartContinuous')
        self.AODOQueue.put(an_action)
        interrupt = None
        ######################################################### repeat acquisition until Stop button is clicked
        while interrupt != 'Stop':
            ######################################### collect data
            if not self.ui.SimulateBox.isChecked():
                # wait for data collection done for one measurement in the Board_thread
                an_action = self.Board2ACQQueue.get() # never time out
                memoryLoc = an_action.action
                # print(memoryLoc)
            else:
                # simulate data
                memoryLoc = 0
                nSamp = (self.ui.PreSamples.value()+self.ui.PostSamples.value())
                tmp = 65535*np.random.rand()*np.sin(2*np.pi*np.random.randint(10,90)*np.arange(nSamp)/nSamp)
                if mode == 'RptAline':
                    self.Memory[memoryLoc] = np.tile(tmp,[100,1])
                    time.sleep(0.1)
                elif mode == 'RptBline':
                    self.Memory[memoryLoc] = np.tile(tmp,[self.ui.BlineAVG.value(), \
                                                     self.ui.Xsteps.value()*self.ui.AlineAVG.value()])
                    time.sleep(0.2)
                elif mode == 'RptCscan':
                    self.Memory[memoryLoc] = np.tile(tmp,[self.ui.Ysteps.value()*self.ui.BlineAVG.value(), \
                                                     self.ui.Xsteps.value()*self.ui.AlineAVG.value()])
                    time.sleep(4)
            ######################################### display data
            if self.ui.FFTDevice.currentText() in ['Alazar', 'None']:
                # directly go to display and save
                data = self.Memory[memoryLoc].copy()
                
                # samples = self.ui.PreSamples.value()+self.ui.PostSamples.value()
                # Alines =np.uint32((data.shape[1])/samples) * data.shape[0]
                # data=data.reshape([Alines, samples])
                
                an_action = DisplayAction(mode, data, args = True) # data in Memory[memoryLoc]
                self.displayQueue.put(an_action)
            else:
                # data needs to perform FFT before display and save
                an_action = GPUAction(self.ui.FFTDevice.currentText(), mode, memoryLoc)
                self.GPUQueue.put(an_action)
            ######################################## check if Pause button is clicked
            try:
               interrupt = self.pauseQueue.get(timeout=0.001)  # time out 0.01 s
               # print(interrupt)
               # if Pause button is clicked
               if interrupt == 'Pause':
                   self.ui.PauseButton.setChecked(True)
                   self.ui.PauseButton.setText('Unpause')
                   # stop Board with any input
                   self.BoardStopQueue.put(0)
                   time.sleep(0.2) # make sure board stops first and AODO stops next
                   # pause AODO
                   an_action = AODOAction('StopContinuous')
                   self.AODOQueue.put(an_action)
                   # wait until unpause button or stop button is clicked
                   interrupt = self.pauseQueue.get()  # never time out
                   # if unpause button is clicked        
                   if interrupt == 'unPause':
                       self.ui.PauseButton.setChecked(False)
                       self.ui.PauseButton.setText('Pause')
                       interrupt = None
                       if not self.ui.SimulateBox.isChecked():
                           # restart ATS9351 for continuous acquisition
                           an_action = BoardAction('StartAcquire')
                           self.BoardQueue.put(an_action)
                           time.sleep(0.1) # starting acquire takes less than 0.1 second, this is to make sure board started before AODO started
                       # restart AODO for continuous acquisition
                       an_action = AODOAction('StartContinuous')
                       self.AODOQueue.put(an_action)
                   elif interrupt == 'Stop':
                       pass
               elif interrupt == 'Stop':
                    # stop Board with any input
                    self.BoardStopQueue.put(0)
                    time.sleep(0.2)
                    # stop AODO 
                    an_action = AODOAction('StopContinuous')
                    self.AODOQueue.put(an_action)
                    an_action = AODOAction('CloseTask')
                    self.AODOQueue.put(an_action)
            except:
                pass

        self.ui.PauseButton.setChecked(False)
        self.ui.PauseButton.setText('Pause')
        return mode + ' successfully finished'

            
    def SurfScan(self):
        # clear display windows
        an_action = DisplayAction('Clear')
        self.displayQueue.put(an_action)
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

        if not self.ui.SimulateBox.isChecked():
            # configure digitizer for one Cscan
            an_action = BoardAction('ConfigureBoard')
            self.BoardQueue.put(an_action)
            time.sleep(0.5) # wait 0.5 seconds to make sure board configuration finished before AODO start
        # configure AODO
        an_action = AODOAction('ConfigAODO')
        self.AODOQueue.put(an_action)
        
        interrupt = None
        stripes = 1
        ############################################################# Iterate through strips for one surfscan
        while np.any(self.Mosaic) and interrupt != 'Stop': 
            # stage move to start of this stripe
            files = 0
            if not self.ui.SimulateBox.isChecked():
                # start ATS9351 for one Cscan acquisition
                an_action = BoardAction('StartAcquire')
                self.BoardQueue.put(an_action)
                time.sleep(0.1) # wait 0.1 seconds to make sure board started before AODO start
            # start AODO for one Cscan acquisition
            an_action = AODOAction('StartOnce')
            self.AODOQueue.put(an_action)
            ############################################################  iterate through Cscans in one stripe
            while files < CscansPerStripe and interrupt != 'Stop': 
                ###################################### collecting data
                if not self.ui.SimulateBox.isChecked():
                    # collect data from digitizer
                    an_action = self.Board2ACQQueue.get() # never time out
                    memoryLoc = an_action.action
                else:
                    # simulate data
                   memoryLoc = 0
                   nSamp = (self.ui.PreSamples.value()+self.ui.PostSamples.value())
                   tmp = 65535* np.random.rand()*np.sin(2*np.pi*np.random.randint(10,90)*np.arange(nSamp)/nSamp)
                   
                   self.Memory[memoryLoc] = np.tile(tmp,[self.ui.Ysteps.value()*self.ui.BlineAVG.value(), \
                                                     self.ui.Xsteps.value()*self.ui.AlineAVG.value()])
                   time.sleep(4)
                
                ####################################### display data 
                if self.ui.FFTDevice.currentText() in ['Alazar', 'None']:
                    # directly do display and save
                    # args = [files, stripes], [total scans per stripe, total tiles], [X pixels, Z pixels]
                    args = [[files, stripes], [CscansPerStripe, self.totalTiles],[self.ui.Xsteps.value()*self.ui.AlineAVG.value(),self.ui.DepthRange.value()]]
                    data = self.Memory[memoryLoc].copy()
                    
                    # samples = self.ui.PreSamples.value()+self.ui.PostSamples.value()
                    # Alines =np.uint32((data.shape[1])/samples) * data.shape[0]
                    # data=data.reshape([Alines, samples])
                    
                    an_action = DisplayAction('SurfScan', data, args) # data in Memory[memoryLoc]
                    self.displayQueue.put(an_action)
                else:
                    # need to do FFT before display and save
                    args = [[files, stripes], [CscansPerStripe, self.totalTiles],[self.ui.Xsteps.value()*self.ui.AlineAVG.value(),self.ui.PreSamples.value()+self.ui.PostSamples.value()]]
                    an_action = GPUAction(self.ui.FFTDevice.currentText(), 'SurfScan', memoryLoc, args)
                    self.GPUQueue.put(an_action)
                # increment files imaged
                files +=1
                self.ui.statusbar.showMessage('Imaging '+str(stripes)+'th strip, '+str(files+1)+'th Cscan ')
                ######################################## check if Pause button is clicked
                try:
                    # check if Pause button is clicked
                   interrupt = self.pauseQueue.get(timeout=0.001)  # time out 0.001 s
                   ##################################### if Pause button is clicked
                   if interrupt == 'Pause':
                       # wait until unpause button or stop button is clicked
                       interrupt = self.pauseQueue.get()  # never time out
                   # if unpause button is clicked        
                   if interrupt == 'unPause':
                       self.ui.PauseButton.setChecked(False)
                       self.ui.PauseButton.setText('Pause')
                       interrupt = None
                       if files < CscansPerStripe: 
                           if not self.ui.SimulateBox.isChecked():
                               # TODO: check if ATS9350 can restart without change configurations -- yes
                               an_action = BoardAction('StartAcquire')
                               self.BoardQueue.put(an_action)
                               time.sleep(0.1) # wait 0.1 seconds to make sure board started before AODO start
                           an_action = AODOAction('StartOnce')
                           self.AODOQueue.put(an_action)
                except:
                    # acquisition not paused, start next Cscan
                    if not self.ui.SimulateBox.isChecked():
                        an_action = BoardAction('StartAcquire')
                        self.BoardQueue.put(an_action)
                        time.sleep(0.1) # wait 0.1 seconds to make sure board started before AODO start
                    an_action = AODOAction('StartOnce')
                    self.AODOQueue.put(an_action)
                
            # finishing this stripe, delete one MOSAIC object from the mosaic pattern
            self.Mosaic = np.delete(self.Mosaic, 0)
            stripes = stripes + 1
            
        # close AODO tasks
        an_action = AODOAction('CloseTask')
        self.AODOQueue.put(an_action)
        # reset RUN button
        self.ui.RunButton.setChecked(False)
        self.ui.RunButton.setText('Run')
        self.ui.PauseButton.setChecked(False)
        self.ui.PauseButton.setText('Pause')
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
        


        


        



