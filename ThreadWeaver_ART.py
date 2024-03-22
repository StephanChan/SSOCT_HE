# -*- coding: utf-8 -*-
"""
Created on Wed Jan 24 11:10:17 2024

@author: admin
"""

#################################################################
# THIS KING THREAD IS USING ART8912, WHICH IS MASTER AND the AODO board WILL BE SLAVE
from PyQt5.QtCore import  QThread
import time
import numpy as np
from Generaic_functions import *
from Actions import DnSAction, AODOAction, GPUAction, DAction
import traceback

import matplotlib.pyplot as plt
from scipy.signal import hilbert
import datetime

global ZPIXELSIZE
ZPIXELSIZE = 5 # um, axial pixel size

class WeaverThread(QThread):
    def __init__(self):
        super().__init__()
        self.mosaic = None
        self.exit_message = 'ACQ thread successfully exited'
        
    def run(self):
        self.QueueOut()
        
    def QueueOut(self):
        self.item = self.queue.get()
        while self.item.action != 'exit':
            # self.ui.statusbar.showMessage('King thread is doing: '+self.item.action)
            current_message = self.ui.statusbar.currentMessage()
            try:
                if self.item.action in ['RptAline','RptBline','RptCscan']:
                    message = self.RptScan(self.item.action)
                    self.ui.statusbar.showMessage(message)
                    self.ui.PrintOut.append(message)
                    self.log.write(message)
    
                    
                elif self.item.action in ['SingleBline', 'SingleAline', 'SingleCscan']:
                    message = self.SingleScan(self.item.action)
                    self.ui.statusbar.showMessage(message)
                    self.ui.PrintOut.append(message)
                    self.log.write(message)
                    
                elif self.item.action == 'SurfScan':
                    interrupt, status = self.SurfScan()
                    self.ui.statusbar.showMessage(status)
                    self.ui.PrintOut.append(status)
                    self.log.write(status)
                    
                elif self.item.action == 'SurfScan+Slice':
                    message = self.SurfSlice()
                    self.ui.statusbar.showMessage(message)
                    self.ui.PrintOut.append(message)
                    self.log.write(message)
                elif self.item.action == 'Gotozero':
                    message = self.Gotozero()
                    self.ui.statusbar.showMessage(message)
                    self.ui.PrintOut.append(message)
                    self.log.write(message)
                elif self.item.action == 'ZstageRepeatibility':
                    message = self.ZstageRepeatibility()
                    self.ui.statusbar.showMessage(message)
                    self.ui.PrintOut.append(message)
                    self.log.write(message)
                elif self.item.action == 'ZstageRepeatibility2':
                    message = self.ZstageRepeatibility2()
                    self.ui.statusbar.showMessage(message)
                    self.ui.PrintOut.append(message)
                    self.log.write(message)
                elif self.item.action == 'dispersion_compensation':
                    message = self.dispersion_compensation()
                    self.ui.statusbar.showMessage(message)
                    self.ui.PrintOut.append(message)
                    self.log.write(message)
                elif self.item.action == 'get_background':
                    message = self.get_background()
                    self.ui.statusbar.showMessage(message)
                    self.ui.PrintOut.append(message)
                    self.log.write(message)
                else:
                    message = 'King thread is doing something invalid: '+self.item.action
                    self.ui.statusbar.showMessage(message)
                    self.ui.PrintOut.append(message)
                    self.log.write(message)
            except Exception as error:
                message = "An error occurred,"+"skip the acquisition action\n"
                self.ui.statusbar.showMessage(message)
                self.ui.PrintOut.append(message)
                self.log.write(message)
                print(traceback.format_exc())
            self.item = self.queue.get()
            
        self.ui.statusbar.showMessage(self.exit_message)
            
    def SingleScan(self, mode):
        # ready digitizer
        an_action = DAction('ConfigureBoard')
        self.DQueue.put(an_action)
        time.sleep(0.5) # first configuration takes about half second
        # ready AODO 
        an_action = AODOAction('ConfigAODO')
        self.AODOQueue.put(an_action)
        # start AODO
        an_action = AODOAction('StartOnce')
        self.AODOQueue.put(an_action)
        time.sleep(0.1) # starting acquire takes less than 0.1 second, this is to make sure board started before AODO started
        # start digitizer
        an_action = DAction('StartAcquire')
        self.DQueue.put(an_action)

        ######################################### collect data
        # collect data from digitizer, data format: [Y pixels, X*Z pixels]
        an_action = self.DbackQueue.get() # never time out
        memoryLoc = an_action.action
        ############################################### display and save data
        self.data = self.Memory[memoryLoc].copy()
        if np.sum(self.data)<10:
            print('spectral data all zeros!')
            self.ui.PrintOut.append('spectral data all zeros!')
            self.log.write('spectral data all zeros!')
            an_action = AODOAction('CloseTask')
            self.AODOQueue.put(an_action)
            an_action = DAction('CloseTask')
            self.DQueue.put(an_action)
            return mode + " got all zeros..."
        if self.ui.FFTDevice.currentText() in ['None']:
            # In None mode, directly do display and save

            an_action = DnSAction(mode, self.data, raw=True) # data in Memory[memoryLoc]
            self.DnSQueue.put(an_action)
            
        elif self.ui.FFTDevice.currentText() in ['Alazar']:
            # in Alazar mode, directly do display and save
            # self.data = self.Memory[memoryLoc].copy()
            # TODO: fix this
            # samples = self.ui.PreSamples.value()+self.ui.PostSamples.value()
            # Alines =np.uint32((data.shape[1])/samples) * data.shape[0]
            # data=data.reshape([Alines, samples])
            an_action = DnSAction(mode, self.data) # data in Memory[memoryLoc]
            self.DnSQueue.put(an_action)
        else:
            # In other modes, do FFT first
            an_action = GPUAction(self.ui.FFTDevice.currentText(), mode, memoryLoc)
            self.GPUQueue.put(an_action)
        
        # AODO stop automatically, but need close() explicitely
        an_action = AODOAction('CloseTask')
        self.AODOQueue.put(an_action)
        an_action = DAction('CloseTask')
        self.DQueue.put(an_action)
        return mode + " successfully finished..."
            
    
    def RptScan(self, mode):
        # clear display windows
        an_action = DnSAction('Clear')
        self.DnSQueue.put(an_action)
        # ready digitizer
        an_action = DAction('ConfigureBoard')
        self.DQueue.put(an_action)
        # time.sleep(0.5) # wait 0.5 seconds to make sure board configuration finished before AODO start
        # ready AODO for continuous measurement
        an_action = AODOAction('ConfigAODO')
        self.AODOQueue.put(an_action)
        # start AODO
        an_action = AODOAction('StartContinuous')
        self.AODOQueue.put(an_action)
        time.sleep(0.1) # starting acquire takes less than 0.1 second, this is to make sure board started before AODO started
        # start digitizer
        an_action = DAction('StartAcquire')
        self.DQueue.put(an_action)
        
        interrupt = None
        data_backs = 0 # count number of data backs
        ######################################################### repeat acquisition until Stop button is clicked
        while interrupt != 'Stop':
            ######################################### collect data
            # wait for data collection done for one measurement in the Board_thread
            an_action = self.DbackQueue.get() # never time out
            memoryLoc = an_action.action
            # print(memoryLoc)
            data_backs += 1
            ######################################### display data
            if self.ui.FFTDevice.currentText() in ['None']:
                # In None mode, directly do display and save
                data = self.Memory[memoryLoc].copy()
                an_action = DnSAction(mode, data, raw=True) # data in Memory[memoryLoc]
                self.DnSQueue.put(an_action)
                
            elif self.ui.FFTDevice.currentText() in ['Alazar']:
                # in Alazar mode, directly do display and save
                data = self.Memory[memoryLoc].copy()
                # TODO: fix this
                # samples = self.ui.PreSamples.value()+self.ui.PostSamples.value()
                # Alines =np.uint32((data.shape[1])/samples) * data.shape[0]
                # data=data.reshape([Alines, samples])
                an_action = DnSAction(mode, data) # data in Memory[memoryLoc]
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
                   # self.ui.PauseButton.setChecked(True)
                   self.ui.PauseButton.setText('Unpause')
                   # pause AODO
                   an_action = AODOAction('StopContinuous')
                   self.AODOQueue.put(an_action)
                   # stop Board with any input
                   self.StopDQueue.put(0)
                   
                   # wait until unpause button or stop button is clicked
                   interrupt = self.PauseQueue.get()  # never time out
                   # if unpause button is clicked        
                   if interrupt == 'unPause':
                        # self.ui.PauseButton.setChecked(False)
                        self.ui.PauseButton.setText('Pause')
                        interrupt = None
                        # restart AODO for continuous acquisition
                        an_action = AODOAction('StartContinuous')
                        self.AODOQueue.put(an_action)
                        # restart ART8912 for continuous acquisition
                        an_action = DAction('ConfigureBoard')
                        self.DQueue.put(an_action)
                        an_action = DAction('StartAcquire')
                        self.DQueue.put(an_action)
                        

               elif interrupt == 'Stop':
                    # stop AODO 
                    an_action = AODOAction('StopContinuous')
                    self.AODOQueue.put(an_action)
                    # stop Board with any input
                    self.StopDQueue.put(0)
                    an_action = AODOAction('CloseTask')
                    self.AODOQueue.put(an_action)
                    
                    message = str(data_backs)+ ' data received by weaver'
                    self.ui.PrintOut.append(message)
                    self.log.write(message)
                    an_action = GPUAction('display_FFT_actions')
                    self.GPUQueue.put(an_action)
                    an_action = DnSAction('display_counts')
                    self.DnSQueue.put(an_action)
            except:
                pass

        self.ui.PauseButton.setChecked(False)
        self.ui.PauseButton.setText('Pause')
        return mode + ' successfully finished...'

            
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
        Ystep = self.ui.YStepSize.value()*self.ui.BlineAVG.value()*self.ui.Ysteps.value()
        CscansPerStripe = np.int16((self.ui.YStop.value()-self.ui.YStart.value())*1000\
            /(self.ui.YStepSize.value()*self.ui.BlineAVG.value()*self.ui.Ysteps.value()))
        if CscansPerStripe <=0:
            return 'invalid Mosaic positions, abort aquisition...'
        # calculate the total number of tiles per slice
        self.totalTiles = CscansPerStripe*len(self.Mosaic)
        if self.totalTiles <=0:
            return 'invalid Mosaic positions, abort aquisition...'

        # configure digitizer for one Cscan
        # an_action = DAction('ConfigureBoard')
        # self.DQueue.put(an_action)

        interrupt = None
        stripes = 1
        # stage move to start of this stripe
        self.ui.XPosition.setValue(self.Mosaic[0].x)
        self.ui.YPosition.setValue(self.Mosaic[0].ystart)
        an_action = AODOAction('Xmove2')
        self.AODOQueue.put(an_action)
        self.StagebackQueue.get()
        an_action = AODOAction('Ymove2')
        self.AODOQueue.put(an_action)
        #TODO: stage back queue tell weaver stage is done moving
        self.StagebackQueue.get()
        scan_direction = 0 # init scan direction to be backward
        ############################################################# Iterate through strips for one surfscan
        while np.any(self.Mosaic) and interrupt != 'Stop': 
            files = 0
            # stage move to start of this stripe
            self.ui.XPosition.setValue(self.Mosaic[0].x)
            an_action = AODOAction('Xmove2')
            self.AODOQueue.put(an_action)
            self.StagebackQueue.get()
            # configure AODO
            an_action = AODOAction('ConfigAODO')
            self.AODOQueue.put(an_action)
            # print('start acquiring\n')
            scan_direction = np.uint32(np.mod(scan_direction+1,2))
            ############################################################  iterate through Cscans in one stripe
            while files < CscansPerStripe and interrupt != 'Stop': 
                ###################################### start one Cscan
                # start AODO for one Cscan acquisition

                an_action = AODOAction('StartOnce', scan_direction)
                self.AODOQueue.put(an_action)
                # time.sleep(0.1) # wait 0.1 seconds to make sure board started before ART8912 start
                
                # start ATS9351 for one Cscan acquisition
                an_action = DAction('ConfigureBoard')
                self.DQueue.put(an_action)
                an_action = DAction('StartAcquire')
                self.DQueue.put(an_action)
                an_action = DAction('CloseTask')
                self.DQueue.put(an_action)
                
                ###################################### collecting data
                # collect data from digitizer
                an_action = self.DbackQueue.get() # never time out
                memoryLoc = an_action.action
                self.ui.YPosition.setValue(self.ui.YPosition.value()+Ystep/1000.0)
                ####################################### display data 
                if self.ui.FFTDevice.currentText() in ['Alazar', 'None']:
                    # directly do display and save
                    # args = [files, stripes], [total scans per stripe, total tiles], [X pixels, Z pixels]
                    args = [[files, stripes], [CscansPerStripe, self.totalTiles],[self.ui.Xsteps.value()*self.ui.AlineAVG.value(),self.ui.DepthRange.value()]]
                    data = self.Memory[memoryLoc].copy()
                    
                    # samples = self.ui.PreSamples.value()+self.ui.PostSamples.value()
                    # Alines =np.uint32((data.shape[1])/samples) * data.shape[0]
                    # data=data.reshape([Alines, samples])
                    
                    an_action = DnSAction('SurfScan', data, args=args) # data in Memory[memoryLoc]
                    self.DnSQueue.put(an_action)
                else:
                    # need to do FFT before display and save
                    args = [[files, stripes], [CscansPerStripe, self.totalTiles],[self.ui.Xsteps.value()*self.ui.AlineAVG.value(),self.ui.PreSamples.value()+self.ui.PostSamples.value()]]
                    an_action = GPUAction(self.ui.FFTDevice.currentText(), 'SurfScan', memoryLoc, args=args)
                    self.GPUQueue.put(an_action)
                # increment files imaged
                files +=1
                self.ui.statusbar.showMessage('Imaging '+str(stripes)+'th strip, '+str(files+1)+'th Cscan ')
                ######################################## check if Pause button is clicked
                try:
                    # check if Pause button is clicked
                   interrupt = self.PauseQueue.get(timeout=0.05)  # time out 0.001 s
                   # print(interrupt)
                   ##################################### if Pause button is clicked
                   if interrupt == 'Pause':
                       # self.ui.PauseButton.setChecked(True)
                       self.ui.PauseButton.setText('unPause')
                       # wait until unpause button or stop button is clicked
                       interrupt = self.PauseQueue.get()  # never time out
                       # print('queue output:',interrupt)
                       # if unpause button is clicked        
                       if interrupt == 'unPause':
                           # self.ui.PauseButton.setChecked(False)
                           self.ui.PauseButton.setText('Pause')
                           interrupt = None
                except:
                    pass
            # close AODO tasks
            an_action = AODOAction('CloseTask')
            self.AODOQueue.put(an_action)
            # finishing this stripe, delete one MOSAIC object from the mosaic pattern
            self.Mosaic = np.delete(self.Mosaic, 0)
            stripes = stripes + 1
            
        # close AODO tasks
        an_action = AODOAction('CloseTask')
        self.AODOQueue.put(an_action)
        # an_action = DAction('CloseTask')
        # self.DQueue.put(an_action)
        # reset RUN button
        self.ui.RunButton.setChecked(False)
        self.ui.RunButton.setText('Run')
        self.ui.PauseButton.setChecked(False)
        self.ui.PauseButton.setText('Pause')
        return interrupt, 'SurfScan successfully finished...'
        
    def SurfSlice(self):
        # cut one slice
        # do surf
        for islice in range(3):
            interrupt, status = self.SurfScan()
            if interrupt == 'Stop':
                break
        self.ui.RunButton.setChecked(False)
        self.ui.RunButton.setText('Run')
        
    def Gotozero(self):
        mode = self.ui.ACQMode.currentText()
        device = self.ui.FFTDevice.currentText()
        self.ui.ACQMode.setCurrentText('SingleAline')
        self.ui.FFTDevice.setCurrentText('GPU')
        # what pixel depth I want the glass signal be at in the Aline image
        target_depth = self.ui.KnownDepth.value()
        # move to defined zero
        self.ui.ZPosition.setValue(self.ui.definedZero.value())
        an_action = AODOAction('Zmove2')
        self.AODOQueue.put(an_action)
        self.StagebackQueue.get()
        # move to defined X position for measuring defined zero
        self.ui.XPosition.setValue(self.ui.XdefinedZero.value())
        an_action = AODOAction('Xmove2')
        self.AODOQueue.put(an_action)
        self.StagebackQueue.get()
        # move to defined Y position for measuring defined zero
        self.ui.YPosition.setValue(self.ui.YdefinedZero.value())
        an_action = AODOAction('Ymove2')
        self.AODOQueue.put(an_action)
        self.StagebackQueue.get()
        
        # check OCT ALine if stage is really at defined zero. error range set to be +-17 pixels
        z=-100 # init peak depth
        total_distance = 0 # init total distance moved in this process
        while np.abs(z-target_depth) > self.ui.DefinedZeroRange.value() and self.ui.Gotozero.isChecked() and np.abs(total_distance)<1: # unit mm
            # do a SingleAline measurement
            message = self.SingleScan(self.ui.ACQMode.currentText())
            self.log.write(message)
            while message != self.ui.ACQMode.currentText()+" successfully finished...":
                message = self.SingleScan(self.ui.ACQMode.currentText())
                self.log.write(message)
                time.sleep(1)
            time.sleep(0.1)
            # get Aline data
            data =self.GPU2weaverQueue.get()
            # average all Alines
            Aline = np.float32(np.mean(data,0))

            # define start pixel depth for finding peak in the Aline
            if self.ui.DepthStart.value() < self.ui.AlineCleanTop.value():
                start_depth = self.ui.AlineCleanTop.value()-self.ui.DepthStart.value()
            else:
                start_depth = 0
            # define end pixel depth for finding peak in the Aline
            if self.ui.DepthRange.value() + self.ui.DepthStart.value()< self.ui.AlineCleanBot.value(): 
                end_depth = self.ui.DepthRange.value()
            else:
                end_depth = self.ui.AlineCleanBot.value()-self.ui.DepthStart.value()
            # find peak depth in the Aline just measured
            z = np.argmax(Aline[start_depth:end_depth])+start_depth+self.ui.DepthStart.value()
            m = np.max(Aline[start_depth:end_depth])
            message = 'peak at:'+str(z)+ ' pixel, m='+str(m)+ ' '+str(z-target_depth)+' pixels away'
            print(message)
            self.ui.PrintOut.append(message)
            self.log.write(message)
            # handle error condistions
            if m < self.ui.AlinePeakMin.value():
                message = 'peak height='+str(m)+ ' peak too small, abort...'
                print(message)
                self.ui.PrintOut.append(message)
                self.log.write(message)
                return ' peak too small, abort...'
            elif m>=self.ui.AlinePeakMax.value():
                message = 'peak height='+str(m)+' this means spectral samples are all 0s, increase XforAline, abort...'
                print(message)
                self.ui.PrintOut.append(message)
                self.log.write(message)
                return ' peak too large, abort...'
            # no error do this
            if z > target_depth and np.abs(z-target_depth)>self.ui.DefinedZeroRange.value(): # this means glass is at lower position
                distance = (z-target_depth) * ZPIXELSIZE/1000
                total_distance += distance
                # move Z stage up by half this distance
                self.ui.ZPosition.setValue(self.ui.ZPosition.value()+distance)
                an_action = AODOAction('Zmove2')
                self.AODOQueue.put(an_action)
                self.StagebackQueue.get()
            elif z < target_depth and np.abs(z-target_depth)>self.ui.DefinedZeroRange.value():  # this means glass is at higher position
                distance = (z-target_depth) * ZPIXELSIZE/1000
                total_distance += distance
                # move Z stage down by double this distance
                self.ui.ZPosition.setValue(self.ui.ZPosition.value()+distance)
                an_action = AODOAction('Zmove2')
                self.AODOQueue.put(an_action)
                self.StagebackQueue.get()
            else:
                break
        
        if np.abs(total_distance) > 1: 
            message='total distance > 1mm, something is wrong...'
        elif not self.ui.Gotozero.isChecked():
            message='gotozero abored by user...'
        else:
            message = 'gotozero success...'
            
        if message == 'gotozero success...':
            self.ui.ZPosition.setValue(self.ui.definedZero.value())
            an_action = AODOAction('Init')
            self.AODOQueue.put(an_action)
            self.StagebackQueue.get()
        self.ui.ACQMode.setCurrentText(mode)
        self.ui.FFTDevice.setCurrentText(device)
        self.ui.Gotozero.setChecked(False)
        return message
        
    def ZstageRepeatibility(self):
        mode = self.ui.ACQMode.currentText()
        device = self.ui.FFTDevice.currentText()
        self.ui.ACQMode.setCurrentText('SingleAline')
        self.ui.FFTDevice.setCurrentText('GPU')
        current_position = self.ui.ZPosition.value()
        iteration = 5
        for i in range(iteration):
            if not self.ui.ZstageTest.isChecked():
                break
            # measure ALine
            self.SingleScan(self.ui.ACQMode.currentText())
            time.sleep(1)
            # move Z stage down
            self.ui.ZPosition.setValue(13)
            an_action = AODOAction('Zmove2')
            self.AODOQueue.put(an_action)
            self.StagebackQueue.get()
            
            self.ui.ZPosition.setValue(8)
            an_action = AODOAction('Zmove2')
            self.AODOQueue.put(an_action)
            self.StagebackQueue.get()
            
            self.ui.ZPosition.setValue(5)
            an_action = AODOAction('Zmove2')
            self.AODOQueue.put(an_action)
            self.StagebackQueue.get()
            
            self.ui.ZPosition.setValue(3)
            an_action = AODOAction('Zmove2')
            self.AODOQueue.put(an_action)
            self.StagebackQueue.get()
            
            # move Z stage up
            self.ui.ZPosition.setValue(current_position)
            an_action = AODOAction('Zmove2')
            self.AODOQueue.put(an_action)
            self.StagebackQueue.get()
            
        self.ui.ZstageTest.setChecked(False)
        # self.weaverBackQueue.put(0)
        self.ui.ACQMode.setCurrentText(mode)
        self.ui.FFTDevice.setCurrentText(device)
        
    def ZstageRepeatibility2(self):
        mode = self.ui.ACQMode.currentText()
        device = self.ui.FFTDevice.currentText()
        self.ui.FFTDevice.setCurrentText('GPU')
        self.ui.ACQMode.setCurrentText('SingleAline')
        current_position = self.ui.ZPosition.value() # this is the target Z pos in this test
        iteration = 100
        for i in range(iteration):
            if not self.ui.ZstageTest2.isChecked():
                break
            # measure ALine
            message = self.SingleScan(self.ui.ACQMode.currentText())
            self.log.write(message)
            while message != self.ui.ACQMode.currentText()+" successfully finished...":
                message = self.SingleScan(self.ui.ACQMode.currentText())
                self.log.write(message)
                self.ui.PrintOut.append(message)
                time.sleep(1)
            time.sleep(0.1) # let GUI update Aline 
            # move Z stage down
            
            self.ui.ZPosition.setValue(3)
            an_action = AODOAction('Zmove2')
            self.AODOQueue.put(an_action)
            self.StagebackQueue.get()
            
            self.ui.XPosition.setValue(70)
            an_action = AODOAction('Xmove2')
            self.AODOQueue.put(an_action)
            self.StagebackQueue.get()
            self.ui.YPosition.setValue(20)
            an_action = AODOAction('Ymove2')
            self.AODOQueue.put(an_action)
            self.StagebackQueue.get()
            # remeasure background
            self.get_background()
            
            self.ui.ZPosition.setValue(15)
            an_action = AODOAction('Zmove2')
            self.AODOQueue.put(an_action)
            self.StagebackQueue.get()
            
            # go to defined zero
            self.ui.Gotozero.setChecked(True)
            message = self.Gotozero()
            self.ui.statusbar.showMessage(message)
            if message != 'gotozero success...':
                message = 'go to zero failed, abort test...'
                print(message)
                self.ui.PrintOut.append(message)
                self.log.write(message)
                break
            else:
                # move to target height
                self.ui.ZPosition.setValue(current_position)
                an_action = AODOAction('Zmove2')
                self.AODOQueue.put(an_action)
                self.StagebackQueue.get()
            self.ui.ACQMode.setCurrentText('SingleAline')
            self.ui.FFTDevice.setCurrentText('GPU')
            
            
        self.ui.ZstageTest2.setChecked(False)
        # self.weaverBackQueue.put(0)
        self.ui.ACQMode.setCurrentText(mode)
        self.ui.FFTDevice.setCurrentText(device)

    def dispersion_compensation(self):
        mode = self.ui.ACQMode.currentText()
        device = self.ui.FFTDevice.currentText()
        self.ui.ACQMode.setCurrentText('SingleAline')
        self.ui.FFTDevice.setCurrentText('None')
        ############################# measure an Aline
        self.SingleScan('SingleAline')
        time.sleep(0.1)
        #################################################################### do dispersion compenstation
        Xpixels = self.ui.XforAline.value()
        Yrpt = self.ui.BlineAVG.value()
        ALINE = self.data.reshape([Xpixels*Yrpt,self.ui.PostSamples_2.value()])
        ALINE = ALINE[:,self.ui.DelaySamples.value():self.ui.PostSamples_2.value()-self.ui.TrimSamples.value()]
        Aline = np.float32(ALINE[0,:])-2048

        plt.figure()
        plt.plot(np.abs(Aline))
        
        L=len(Aline)
        fR=np.fft.fft(Aline)/L # FFT of interference signal

        plt.figure()
        plt.plot(np.abs(fR[20:]))
        
        z = np.argmax(np.abs(fR[50:300]))+50
        low_position = max(10,z-75)
        high_position = min(L//2,z+75)

        fR[0:low_position]=0
        fR[high_position:L-high_position]=0
        fR[L-low_position:]=0
        
        plt.figure()
        plt.plot(np.abs(fR))
        
        Aline = np.fft.ifft(fR)

        hR=hilbert(np.real(Aline))
        hR_phi=np.unwrap(np.angle(hR))
        
        phi_delta=np.linspace(hR_phi[0],hR_phi[L-1],L)
        phi_diff=np.float32(phi_delta-hR_phi)
        ALINE = ALINE*np.exp(1j*phi_diff)
        
        plt.figure()
        plt.plot(phi_diff)
        # plt.figure()
        message = 'max phase difference is: '+str(np.max(np.abs(phi_diff)))+'\n'
        self.ui.PrintOut.append(message)
        self.log.write(message)
        # fR = np.fft.fft(ALINE, axis=1)/L

        # fR = np.abs(fR[:,self.ui.DepthStart.value():self.ui.DepthStart.value()+self.ui.DepthRange.value()])
        # # self.ui.MaxContrast.setValue(0.1)
        # self.Display_aline(fR, raw = False)
        
        filePath = self.ui.DIR.toPlainText()

        current_time = datetime.datetime.now()
        filePath = filePath + "/" + 'dispersion_compensation_'+\
            str(current_time.year)+'-'+\
            str(current_time.month)+'-'+\
            str(current_time.day)+'-'+\
            str(current_time.hour)+'-'+\
            str(current_time.minute)+\
            '.bin'
        fp = open(filePath, 'wb')
        phi_diff.tofile(fp)
        fp.close()
        self.ui.Disp_DIR.setText(filePath)
        self.ui.ACQMode.setCurrentText(mode)
        self.ui.FFTDevice.setCurrentText(device)
        return 'dispersion compensasion success...'
        
    def get_background(self):
        mode = self.ui.ACQMode.currentText()
        device = self.ui.FFTDevice.currentText()
        self.ui.ACQMode.setCurrentText('SingleAline')
        self.ui.FFTDevice.setCurrentText('None')
        ############################# measure an Aline
        self.SingleScan('SingleAline')
        time.sleep(0.1)
        #######################################################################
        Xpixels = self.ui.XforAline.value()
        Yrpt = self.ui.BlineAVG.value()
        ALINE = self.data.reshape([Xpixels*Yrpt,self.ui.PostSamples_2.value()])
        ALINE = ALINE[:,self.ui.DelaySamples.value():self.ui.PostSamples_2.value()-self.ui.TrimSamples.value()]
        
        background = np.float32(np.mean(ALINE,0))
        # print(background.shape)
        filePath = self.ui.DIR.toPlainText()
        current_time = datetime.datetime.now()
        filePath = filePath + "/" + 'background_'+\
            str(current_time.year)+'-'+\
            str(current_time.month)+'-'+\
            str(current_time.day)+'-'+\
            str(current_time.hour)+'-'+\
            str(current_time.minute)+'-'+\
            str(current_time.second)+\
            '.bin'
        fp = open(filePath, 'wb')
        background.tofile(fp)
        fp.close()
        
        self.ui.BG_DIR.setText(filePath)
        self.ui.ACQMode.setCurrentText(mode)
        self.ui.FFTDevice.setCurrentText(device)
        return 'background measruement success...'
    