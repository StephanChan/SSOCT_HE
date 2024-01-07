# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 16:49:35 2023

@author: admin
"""
from PyQt5.QtCore import  QThread
import time
import numpy as np
from Generaic_functions import *
from Actions import DisplayAction, AODOAction, GPUAction, Board2ACQAction, BoardAction
from multiprocessing import Queue



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
            # self.test_message = 'Board thread successfully exited'
            
from ThreadBoard import ATS9350
class ATS9350_2(ATS9350):
    def __init__(self, ui, BoardQueue, Board2ACQQueue):
        super().__init__()
        global Memory
        self.Memory = Memory
        self.ui = ui
        self.queue = BoardQueue
        self.Board2ACQQueue = Board2ACQQueue
            
        # self.test_message = 'Board thread successfully exited'
            
class ACQThread(QThread):
    def __init__(self, ui, AcqQueue, DisplayQueue, AODOQueue, PauseQueue):
        super().__init__()
        self.ui = ui
        self.queue = AcqQueue
        self.displayQueue = DisplayQueue
        self.AODOQueue = AODOQueue
        self.pauseQueue = PauseQueue
        self.mosaic = None
        
        self.GPUQueue = Queue()

        self.BoardQueue = Queue()

        self.Board2ACQQueue = Queue()
        
        self.GPU_thread = GPUThread2(self.ui, self.GPUQueue, self.displayQueue)
        self.GPU_thread.start()

        self.Board_thread = ATS9350_2(self.ui, self.BoardQueue, self.Board2ACQQueue)
        self.Board_thread.start()
        self.exit_message = 'ACQ thread successfully exited'
        
    def run(self):
        self.QueueOut()
        
    def QueueOut(self):
        self.item = self.queue.get()
        while self.item.action != 'exit':
            self.ui.statusbar.showMessage('ACQ thread is doing: '+self.item.action)
            if self.item.action in ['RptAline','RptBline','RptCscan']:
                self.ui.statusbar.showMessage(self.RptScan(self.item.action))

                
            elif self.item.action in ['SingleBline', 'SingleAline', 'SingleCscan']:
                self.ui.statusbar.showMessage(self.SingleScan(self.item.action))
            
            elif self.item.action == 'SurfScan':
                interrupt, status = self.SurfScan()
                self.ui.statusbar.showMessage(status)
                
            elif self.item.action == 'SurfScan+Slice':
                self.ui.statusbar.showMessage(self.SurfSlice())
                
            else:
                self.ui.statusbar.showMessage('ACQ thread is doing something invalid: '+self.item.action)
            
            self.item = self.queue.get()
        an_action = GPUAction('exit', '', 0)
        self.GPUQueue.put(an_action)
        an_action = BoardAction('exit')
        self.BoardQueue.put(an_action)
        time.sleep(0.1)
        print(self.exit_message)
            
    def SingleScan(self, mode):
        global Memory
        if self.ui.FFTmode.currentText() != 'Simulate':
        # ready digitizer
            an_action = BoardAction('ConfigureBoard')
            self.BoardQueue.put(an_action)
        # ready AODO for 1 bline measurement and start
        an_action = AODOAction('ConfigAODO')
        self.AODOQueue.put(an_action)
        if self.ui.FFTmode.currentText() != 'Simulate':
            # start digitizer
            an_action = BoardAction('StartAcquire')
            self.BoardQueue.put(an_action)
        
        an_action = AODOAction('StartOnce')
        self.AODOQueue.put(an_action)
        if self.ui.FFTmode.currentText() != 'Simulate':
            # collect data from digitizer, data format: [X pixels, Z pixels]
            an_action = self.Board2ACQQueue.get() # never time out
            memoryLoc = an_action.action
        else:
            memoryLoc = 0
            nSamp = (self.ui.PreSamples.value()+self.ui.PostSamples.value())
            tmp = np.sin(2*np.pi*np.random.randint(0,100)*np.arange(nSamp)/nSamp)
            if mode == 'SingleAline':
                # Memory[memoryLoc] = np.random.randint(0, 255, [self.ui.BlineAVG.value(),100 * (self.ui.PreSamples.value()+self.ui.PostSamples.value())], np.uint8)
                Memory[memoryLoc] = np.tile(tmp,[100,1])
                time.sleep(0.1)
            elif mode == 'SingleBline':
                Memory[memoryLoc] = np.tile(tmp,[self.ui.BlineAVG.value(), \
                                                 self.ui.Xsteps.value()*self.ui.AlineAVG.value()])
                # Memory[memoryLoc] = np.random.randint(0, 255, [self.ui.BlineAVG.value() , \
                #                                       self.ui.Xsteps.value()*self.ui.AlineAVG.value() * \
                #                                       (self.ui.PreSamples.value()+self.ui.PostSamples.value())], np.uint8)
                time.sleep(0.2)
            elif mode == 'SingleCscan':
                Memory[memoryLoc] = np.tile(tmp,[self.ui.Ysteps.value()*self.ui.BlineAVG.value(), \
                                                 self.ui.Xsteps.value()*self.ui.AlineAVG.value()])
                # Memory[memoryLoc] = np.random.randint(0, 255, \
                #                                       [self.ui.Ysteps.value()*self.ui.BlineAVG.value(), \
                #                                        self.ui.Xsteps.value()*self.ui.AlineAVG.value() * \
                #                                            (self.ui.PreSamples.value()+self.ui.PostSamples.value())], np.uint8)
                time.sleep(4)
            
        # # display and save in ACQ_thread or GPU_thread
        if self.ui.FFTmode.currentText() in ['Alazar FFT']:#,'Simulate']:
            # display and save
            data = Memory[memoryLoc].copy()
            
            # samples = self.ui.PreSamples.value()+self.ui.PostSamples.value()
            # Alines =np.uint32((data.shape[1])/samples) * data.shape[0]
            # data=data.reshape([Alines, samples])
            
            an_action = DisplayAction(mode, data) # data in Memory[memoryLoc]
            self.displayQueue.put(an_action)
        else:
            # GPU thread start
            an_action = GPUAction('GPU', mode, memoryLoc)
            self.GPUQueue.put(an_action)
        an_action = AODOAction('CloseTask')
        self.AODOQueue.put(an_action)
        if self.ui.FFTmode.currentText() != 'Simulate':
            an_action = BoardAction('StopAcquire')
            self.BoardQueue.put(an_action)
        return mode + ' successfully finished'
            
    def RptScan(self, mode):
        if self.ui.FFTmode.currentText() != 'Simulate':
        # ready digitizer
            an_action = BoardAction('ConfigureBoard')
            self.BoardQueue.put(an_action)
        # ready AODO for continuous measurement
        an_action = AODOAction('ConfigAODO')
        self.AODOQueue.put(an_action)
        if self.ui.FFTmode.currentText() != 'Simulate':
            # start digitizer
            an_action = BoardAction('StartAcquire')
            self.BoardQueue.put(an_action)
        an_action = AODOAction('StartContinuous')
        self.AODOQueue.put(an_action)

        interrupt = None
        # repeat acquisition until Stop button is clicked
        while interrupt != 'Stop':
            try:
               interrupt = self.pauseQueue.get(timeout=0.01)  # time out 0.01 s
            except:
                if self.ui.FFTmode.currentText() != 'Simulate':
                    # wait for data collection done for one measurement in the Board_thread while loop
                    an_action = self.Board2ACQQueue.get() # never time out
                    memoryLoc = an_action.action
                else:
                    memoryLoc = 0
                    nSamp = (self.ui.PreSamples.value()+self.ui.PostSamples.value())
                    tmp = np.sin(2*np.pi*np.random.randint(0,100)*np.arange(nSamp)/nSamp)
                    if mode == 'SingleAline':
                        # Memory[memoryLoc] = np.random.randint(0, 255, [self.ui.BlineAVG.value(),100 * (self.ui.PreSamples.value()+self.ui.PostSamples.value())], np.uint8)
                        Memory[memoryLoc] = np.tile(tmp,[100,1])
                        time.sleep(0.1)
                    elif mode == 'SingleBline':
                        Memory[memoryLoc] = np.tile(tmp,[self.ui.BlineAVG.value(), \
                                                         self.ui.Xsteps.value()*self.ui.AlineAVG.value()])
                        # Memory[memoryLoc] = np.random.randint(0, 255, [self.ui.BlineAVG.value() , \
                        #                                       self.ui.Xsteps.value()*self.ui.AlineAVG.value() * \
                        #                                       (self.ui.PreSamples.value()+self.ui.PostSamples.value())], np.uint8)
                        time.sleep(0.2)
                    elif mode == 'SingleCscan':
                        Memory[memoryLoc] = np.tile(tmp,[self.ui.Ysteps.value()*self.ui.BlineAVG.value(), \
                                                         self.ui.Xsteps.value()*self.ui.AlineAVG.value()])
                        # Memory[memoryLoc] = np.random.randint(0, 255, \
                        #                                       [self.ui.Ysteps.value()*self.ui.BlineAVG.value(), \
                        #                                        self.ui.Xsteps.value()*self.ui.AlineAVG.value() * \
                        #                                            (self.ui.PreSamples.value()+self.ui.PostSamples.value())], np.uint8)
                        time.sleep(4)
                # display
                
                if self.ui.FFTmode.currentText() in ['Alazar FFT']:#,'Simulate']:
                    # display and save
                    data = Memory[memoryLoc].copy()
                    
                    # samples = self.ui.PreSamples.value()+self.ui.PostSamples.value()
                    # Alines =np.uint32((data.shape[1])/samples) * data.shape[0]
                    # data=data.reshape([Alines, samples])
                    
                    an_action = DisplayAction(mode, data) # data in Memory[memoryLoc]
                    self.displayQueue.put(an_action)
                else:
                    # GPU thread start
                    # self.ui.PreSamples.value()+self.ui.PostSamples.value()
                    an_action = GPUAction('GPU', mode, memoryLoc)
                    self.GPUQueue.put(an_action)
            # if Pause button is clicked
            if interrupt == 'Pause':
                # pause acquisition
                an_action = AODOAction('StopContinuous')
                self.AODOQueue.put(an_action)
                # digitizer will automatically stop
                # wait until unpause button or stop button is clicked
                interrupt = self.pauseQueue.get()  # never time out
            # if unpause button is clicked        
            if interrupt == 'unPause':
                interrupt == None
                if self.ui.FFTmode.currentText() != 'Simulate':
                    # start digitizer for one Cscan
                    an_action = BoardAction('StartAcquire')
                    self.BoardQueue.put(an_action)
                an_action = AODOAction('StartContinuous')
                self.AODOQueue.put(an_action)
                
        an_action = AODOAction('StopContinuous')
        self.AODOQueue.put(an_action)
        an_action = AODOAction('CloseTask')
        self.AODOQueue.put(an_action)
        # digitizer will automatically stop
            
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
        ############################################################# Iterate through strips for one surfscan
        if self.ui.FFTmode.currentText() != 'Simulate':
            # configure digitizer for one Cscan
            an_action = BoardAction('ConfigureBoard')
            self.BoardQueue.put(an_action)
        # configure AODO
        an_action = AODOAction('ConfigAODO')
        self.AODOQueue.put(an_action)
        
        interrupt = None
        stripes = 1
        while np.any(self.Mosaic) and interrupt != 'Stop': 
            # move to start of this stripe
            files = 0
            if self.ui.FFTmode.currentText() != 'Simulate':
                # configure digitizer for one Cscan
                an_action = BoardAction('StartAcquire')
                self.BoardQueue.put(an_action)
            # start AODO
            an_action = AODOAction('StartOnce')
            self.AODOQueue.put(an_action)
            ############################################################  iterate through Cscans in one stripe
            while files < CscansPerStripe and interrupt != 'Stop': 
                
                if self.ui.FFTmode.currentText() != 'Simulate':
                    # TODO: how to wait until done, maybe check if self.memoryLoc has changed? -- use a Board2Acq queue for signaling done acquisition
                    an_action = self.Board2ACQQueue.get() # never time out
                    memoryLoc = an_action.action
                else:
                   memoryLoc = 0
                   nSamp = (self.ui.PreSamples.value()+self.ui.PostSamples.value())
                   tmp = np.sin(2*np.pi*np.random.randint(0,100)*np.arange(nSamp)/nSamp)
                   
                   Memory[memoryLoc] = np.tile(tmp,[self.ui.Ysteps.value()*self.ui.BlineAVG.value(), \
                                                     self.ui.Xsteps.value()*self.ui.AlineAVG.value()])
                   time.sleep(4)
                try:
                    # check if acquisition has been paused
                   interrupt = self.pauseQueue.get(timeout=0.01)  # time out 0.01 s
                except:
                    # acquisition not paused, start next Cscan
                    if self.ui.FFTmode.currentText() != 'Simulate':
                        # TODO: how to wait until done, maybe check if self.memoryLoc has changed? -- use a Board2Acq queue for signaling done acquisition
                        an_action = BoardAction('StartAcquire')
                        self.BoardQueue.put(an_action)
                        # TODO: check if ATS9350 can restart without change configurations
                    an_action = AODOAction('StartOnce')
                    self.AODOQueue.put(an_action)

                # if use Onboard FFT, directly display and save
                
                if self.ui.FFTmode.currentText() in ['Alazar FFT']:#,'Simulate']:
                    # display and save
                    # args = [files, stripes], [total scans per stripe, total tiles], [X pixels, Z pixels]
                    args = [[files, stripes], [CscansPerStripe, self.totalTiles],[self.ui.Xsteps.value()*self.ui.AlineAVG.value(),self.ui.DepthRange.value()]]
                    data = Memory[memoryLoc].copy()
                    
                    # samples = self.ui.PreSamples.value()+self.ui.PostSamples.value()
                    # Alines =np.uint32((data.shape[1])/samples) * data.shape[0]
                    # data=data.reshape([Alines, samples])
                    
                    an_action = DisplayAction('SurfScan', data, args) # data in Memory[memoryLoc]
                    self.displayQueue.put(an_action)
                else:
                    # GPU thread start
                    args = [[files, stripes], [CscansPerStripe, self.totalTiles],[self.ui.Xsteps.value()*self.ui.AlineAVG.value(),self.ui.PreSamples.value()+self.ui.PostSamples.value()]]
                    an_action = GPUAction('GPU', 'SurfScan', memoryLoc, args)
                    self.GPUQueue.put(an_action)
                files +=1
                self.ui.statusbar.showMessage('Imaging '+str(stripes)+'th strip, '+str(files+1)+'th Cscan ')
                # if Pause button is clicked
                if interrupt == 'Pause':
                    # wait until unpause button or stop button is clicked
                    # TODO: check if ATS9350 can wait forever when data collection is done
                    if self.ui.FFTmode.currentText() != 'Simulate':
                        an_action = BoardAction('StopAcquire')
                        self.BoardQueue.put(an_action)
                    interrupt = self.pauseQueue.get()  # never time out
                # if unpause button is clicked        
                if interrupt == 'unPause':
                    if files < CscansPerStripe: 
                        if self.ui.FFTmode.currentText() != 'Simulate':
                            # TODO: check if ATS9350 can restart without change configurations
                            an_action = BoardAction('StartAcquire')
                            self.BoardQueue.put(an_action)
                        an_action = AODOAction('StartOnce')
                        self.AODOQueue.put(an_action)
            # finishing this stripe, delete one MOSAIC object from the mosaic pattern
            self.Mosaic = np.delete(self.Mosaic, 0)
            stripes = stripes + 1
            
        an_action = AODOAction('CloseTask')
        self.AODOQueue.put(an_action)
        if self.ui.FFTmode.currentText() != 'Simulate':
            an_action = BoardAction('StopAcquire')
            self.BoardQueue.put(an_action)

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
        


        


        



