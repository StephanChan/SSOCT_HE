# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 16:49:35 2023

@author: admin
"""
from PyQt5.QtCore import  QThread
import time
import numpy as np
from Generaic_functions import *
from Actions import DnSAction, AODOAction, GPUAction, DAction
import traceback

       
class KingThread(QThread):
    def __init__(self):
        super().__init__()
        self.mosaic = None
        self.exit_message = 'ACQ thread successfully exited'
        
    def run(self):
        self.QueueOut()
        
    def QueueOut(self):
        self.item = self.queue.get()
        while self.item.action != 'exit':
            self.ui.statusbar.showMessage('King thread is doing: '+self.item.action)
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
                else:
                    self.ui.statusbar.showMessage('King thread is doing something invalid: '+self.item.action)
            except Exception as error:
                print("An error occurred:", error,'\n skip the acquisition action\n')

                print(traceback.format_exc())
            self.item = self.queue.get()
            
        print(self.exit_message)
            
    def SingleScan(self, mode):
        # ready digitizer
        an_action = DAction('ConfigureBoard')
        self.DQueue.put(an_action)
        time.sleep(0.5) # first configuration takes about half second
        # ready AODO 
        an_action = AODOAction('ConfigAODO')
        self.AODOQueue.put(an_action)
        # start digitizer
        an_action = DAction('StartAcquire')
        self.DQueue.put(an_action)
        time.sleep(0.1) # starting acquire takes less than 0.1 second, this is to make sure board started before AODO started
        # start AODO
        an_action = AODOAction('StartOnce')
        self.AODOQueue.put(an_action)
        ######################################### collect data
        # collect data from digitizer, data format: [Y pixels, X*Z pixels]
        an_action = self.DbackQueue.get() # never time out
        memoryLoc = an_action.action
        ############################################### display and save data
        if self.ui.FFTDevice.currentText() in ['None']:
            # In None mode, directly do display and save
            data = self.Memory[memoryLoc].copy()
            an_action = DnSAction(mode, data, args=True) # data in Memory[memoryLoc]
            self.DnSQueue.put(an_action)
            
        elif self.ui.FFTDevice.currentText() in ['Alazar']:
            # in Alazar mode, directly do display and save
            data = self.Memory[memoryLoc].copy()
            # TODO: fix this
            # samples = self.ui.PreSamples.value()+self.ui.PostSamples.value()
            # Alines =np.uint32((data.shape[1])/samples) * data.shape[0]
            # data=data.reshape([Alines, samples])
            an_action = DnSAction(mode, data, args=False) # data in Memory[memoryLoc]
            self.DnSQueue.put(an_action)
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
        # clear display windows
        an_action = DnSAction('Clear')
        self.DnSQueue.put(an_action)
        # ready digitizer
        an_action = DAction('ConfigureBoard')
        self.DQueue.put(an_action)
        time.sleep(0.5) # wait 0.5 seconds to make sure board configuration finished before AODO start
        # ready AODO for continuous measurement
        an_action = AODOAction('ConfigAODO')
        self.AODOQueue.put(an_action)
        # start digitizer
        an_action = DAction('StartAcquire')
        self.DQueue.put(an_action)
        time.sleep(0.1) # starting acquire takes less than 0.1 second, this is to make sure board started before AODO started
        # start AODO
        an_action = AODOAction('StartContinuous')
        self.AODOQueue.put(an_action)
        interrupt = None
        ######################################################### repeat acquisition until Stop button is clicked
        while interrupt != 'Stop':
            ######################################### collect data
            # wait for data collection done for one measurement in the Board_thread
            an_action = self.DbackQueue.get() # never time out
            memoryLoc = an_action.action
            # print(memoryLoc)
            
            ######################################### display data
            if self.ui.FFTDevice.currentText() in ['None']:
                # In None mode, directly do display and save
                data = self.Memory[memoryLoc].copy()
                an_action = DnSAction(mode, data, args=True) # data in Memory[memoryLoc]
                self.DnSQueue.put(an_action)
                
            elif self.ui.FFTDevice.currentText() in ['Alazar']:
                # in Alazar mode, directly do display and save
                data = self.Memory[memoryLoc].copy()
                # TODO: fix this
                # samples = self.ui.PreSamples.value()+self.ui.PostSamples.value()
                # Alines =np.uint32((data.shape[1])/samples) * data.shape[0]
                # data=data.reshape([Alines, samples])
                an_action = DnSAction(mode, data, args=False) # data in Memory[memoryLoc]
                self.DnSQueue.put(an_action)
            else:
                # In other modes, do FFT first
                an_action = GPUAction(self.ui.FFTDevice.currentText(), mode, memoryLoc)
                self.GPUQueue.put(an_action)
            ######################################## check if Pause button is clicked
            try:
               interrupt = self.PauseQueue.get(timeout=0.001)  # time out 0.01 s
               # print(interrupt)
               # if Pause button is clicked
               if interrupt == 'Pause':
                   self.ui.PauseButton.setChecked(True)
                   self.ui.PauseButton.setText('Unpause')
                   # stop Board with any input
                   self.StopDQueue.put(0)
                   time.sleep(0.2) # make sure board stops first and AODO stops next
                   # pause AODO
                   an_action = AODOAction('StopContinuous')
                   self.AODOQueue.put(an_action)
                   # wait until unpause button or stop button is clicked
                   interrupt = self.PauseQueue.get()  # never time out
                   # if unpause button is clicked        
                   if interrupt == 'unPause':
                        self.ui.PauseButton.setChecked(False)
                        self.ui.PauseButton.setText('Pause')
                        interrupt = None
                        # restart ATS9351 for continuous acquisition
                        an_action = DAction('StartAcquire')
                        self.DQueue.put(an_action)
                        time.sleep(0.1) # starting acquire takes less than 0.1 second, this is to make sure board started before AODO started
                        # restart AODO for continuous acquisition
                        an_action = AODOAction('StartContinuous')
                        self.AODOQueue.put(an_action)

               elif interrupt == 'Stop':
                    # stop Board with any input
                    self.StopDQueue.put(0)
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
        an_action = DnSAction('Clear')
        self.DnSQueue.put(an_action)
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

        # configure digitizer for one Cscan
        an_action = DAction('ConfigureBoard')
        self.DQueue.put(an_action)
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
            
            # print('start acquiring\n')
            ############################################################  iterate through Cscans in one stripe
            while files < CscansPerStripe and interrupt != 'Stop': 
                ###################################### start one Cscan
                # start ATS9351 for one Cscan acquisition
                an_action = DAction('StartAcquire')
                self.DQueue.put(an_action)
                time.sleep(0.1) # wait 0.1 seconds to make sure board started before AODO start
                # start AODO for one Cscan acquisition
                an_action = AODOAction('StartOnce')
                self.AODOQueue.put(an_action)
                ###################################### collecting data
                # collect data from digitizer
                an_action = self.DbackQueue.get() # never time out
                memoryLoc = an_action.action
                
                ####################################### display data 
                if self.ui.FFTDevice.currentText() in ['Alazar', 'None']:
                    # directly do display and save
                    # args = [files, stripes], [total scans per stripe, total tiles], [X pixels, Z pixels]
                    args = [[files, stripes], [CscansPerStripe, self.totalTiles],[self.ui.Xsteps.value()*self.ui.AlineAVG.value(),self.ui.DepthRange.value()]]
                    data = self.Memory[memoryLoc].copy()
                    
                    # samples = self.ui.PreSamples.value()+self.ui.PostSamples.value()
                    # Alines =np.uint32((data.shape[1])/samples) * data.shape[0]
                    # data=data.reshape([Alines, samples])
                    
                    an_action = DnSAction('SurfScan', data, args) # data in Memory[memoryLoc]
                    self.DnSQueue.put(an_action)
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
                   interrupt = self.PauseQueue.get(timeout=0.001)  # time out 0.001 s
                   ##################################### if Pause button is clicked
                   if interrupt == 'Pause':
                       self.ui.PauseButton.setChecked(True)
                       self.ui.PauseButton.setText('unPause')
                       # wait until unpause button or stop button is clicked
                       interrupt = self.pauseQueue.get()  # never time out
                       # if unpause button is clicked        
                       if interrupt == 'unPause':
                           self.ui.PauseButton.setChecked(False)
                           self.ui.PauseButton.setText('Pause')
                           interrupt = None
                except:
                    pass
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
        


        


        



