# -*- coding: utf-8 -*-
"""
Created on Wed Jan 24 11:10:17 2024

@author: admin
"""

#################################################################
from PyQt5.QtCore import  QThread
import time
import numpy as np
from Generaic_functions import *
from Actions import DnSAction, AODOAction, GPUAction, DAction
import traceback
import os
import matplotlib.pyplot as plt
from scipy.signal import hilbert
import datetime

# axial pixel size, measure with a microscope glass slide
global ZPIXELSIZE
ZPIXELSIZE = 4.4 # unit: um

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
            try:
                if self.item.action in ['RptAline','RptBline','RptCscan']:
                    message = self.RptScan(self.item.action)
                    self.ui.statusbar.showMessage(message)
                    # self.ui.PrintOut.append(message)
                    self.log.write(message)
                    
                elif self.item.action in ['SingleBline', 'SingleAline', 'SingleCscan']:
                    message = self.SingleScan(self.item.action)
                    self.ui.statusbar.showMessage(message)
                    # self.ui.PrintOut.append(message)
                    self.log.write(message)

                elif self.item.action == 'Mosaic':
                    # make directories
                    if not os.path.exists(self.ui.DIR.toPlainText()+'/aip'):
                        os.mkdir(self.ui.DIR.toPlainText()+'/aip')
                    if not os.path.exists(self.ui.DIR.toPlainText()+'/surf'):
                        os.mkdir(self.ui.DIR.toPlainText()+'/surf')
                    if not os.path.exists(self.ui.DIR.toPlainText()+'/fitting'):
                        os.mkdir(self.ui.DIR.toPlainText()+'/fitting')
                    # do fast pre-scan to identify tissue area
                    interrupt, status= self.PreMosaic()
                    if interrupt == 'Stop' :
                        status = "action aborted by user..."
                    elif interrupt == 'Error':
                        pass
                    else:
                        interrupt, status = self.Mosaic()
                    # self.ui.PrintOut.append(status)
                    self.log.write(status)

                elif self.item.action == 'Mosaic+Cut':
                    # make directories
                    if not os.path.exists(self.ui.DIR.toPlainText()+'/aip'):
                        os.mkdir(self.ui.DIR.toPlainText()+'/aip')
                    if not os.path.exists(self.ui.DIR.toPlainText()+'/surf'):
                        os.mkdir(self.ui.DIR.toPlainText()+'/surf')
                    if not os.path.exists(self.ui.DIR.toPlainText()+'/fitting'):
                        os.mkdir(self.ui.DIR.toPlainText()+'/fitting')
                    # disable partial vibratome settings to avoid parameter change during experiment
                    self.ui.SMPthickness.setEnabled(False)
                    self.ui.SliceZDepth.setEnabled(False)
                    # self.ui.ImageZDepth.setEnabled(False)
                    self.ui.SMPthickness.setEnabled(False)
                    message = self.SurfSlice()
                    self.ui.statusbar.showMessage(message)
                    # self.ui.PrintOut.append(message)
                    self.log.write(message)
                    # re-enable settings
                    self.ui.SMPthickness.setEnabled(True)
                    self.ui.SliceZDepth.setEnabled(True)
                    # self.ui.ImageZDepth.setEnabled(True)
                    self.ui.SMPthickness.setEnabled(True)

                elif self.item.action == 'SingleCut':
                    message = self.SingleCut(self.ui.SliceZStart.value())
                    self.ui.statusbar.showMessage(message)
                    # self.ui.PrintOut.append(message)
                    self.log.write(message)

                elif self.item.action == 'RptCut':
                    self.ui.SMPthickness.setEnabled(False)
                    self.ui.SliceZDepth.setEnabled(False)
                    # self.ui.ImageZDepth.setEnabled(False)
                    self.ui.SMPthickness.setEnabled(False)
                    message = self.RptCut(self.ui.SliceZStart.value(), np.uint16(self.ui.SMPthickness.value()*1000/self.ui.SliceZDepth.value()))
                    self.ui.statusbar.showMessage(message)
                    # self.ui.PrintOut.append(message)
                    self.log.write(message)
                    self.ui.SMPthickness.setEnabled(True)
                    self.ui.SliceZDepth.setEnabled(True)
                    # self.ui.ImageZDepth.setEnabled(True)
                    self.ui.SMPthickness.setEnabled(True)
                    # self.ui.statusbar.showMessage(status)
                    
                elif self.item.action == 'Gotozero':
                    # message = self.Gotozero()
                    # self.ui.statusbar.showMessage(message)
                    # # self.ui.PrintOut.append(message)
                    # self.log.write(message)
                    pass
                
                elif self.item.action == 'ZstageRepeatibility':
                    message = self.ZstageRepeatibility()
                    self.ui.statusbar.showMessage(message)
                    # self.ui.PrintOut.append(message)
                    self.log.write(message)
                    
                elif self.item.action == 'ZstageRepeatibility2':
                    # message = self.ZstageRepeatibility2()
                    # self.ui.statusbar.showMessage(message)
                    # # self.ui.PrintOut.append(message)
                    # self.log.write(message)
                    pass
                
                elif self.item.action == 'dispersion_compensation':
                    message = self.dispersion_compensation()
                    self.ui.statusbar.showMessage(message)
                    # self.ui.PrintOut.append(message)
                    self.log.write(message)
                    
                elif self.item.action == 'get_background':
                    message = self.get_background()
                    self.ui.statusbar.showMessage(message)
                    # self.ui.PrintOut.append(message)
                    self.log.write(message)
                    
                elif self.item.action == 'get_surface':
                    message = self.get_surfCurve()
                    self.ui.statusbar.showMessage(message)
                    # self.ui.PrintOut.append(message)
                    self.log.write(message)
                    
                else:
                    message = 'Weaver thread is doing something invalid: '+self.item.action
                    self.ui.statusbar.showMessage(message)
                    # self.ui.PrintOut.append(message)
                    self.log.write(message)

            except Exception as error:
                message = "An error occurred,"+"skip the acquisition action\n"
                self.ui.statusbar.showMessage(message)
                # self.ui.PrintOut.append(message)
                self.log.write(message)
                print(traceback.format_exc())
            # reset RUN button
            self.ui.RunButton.setChecked(False)
            self.ui.RunButton.setText('Go')
            self.ui.PauseButton.setChecked(False)
            self.ui.PauseButton.setText('Pause')
            # wait for next command
            self.item = self.queue.get()
        # exit weaver thread
        self.ui.statusbar.showMessage(self.exit_message)
            
    def InitMemory(self):
        #################################################################
        # get number samplers per Aline
        if self.Digitizer == 'Alazar':
            samples = self.ui.PreSamples.value()+self.ui.PostSamples.value()
        elif self.Digitizer == 'ART':
            samples = self.ui.PostSamples_2.value()
        # get channel number
        if self.Digitizer == 'ART':
            if self.ui.Benable_2.currentText() == 'Disable':
                 nchannels = 1                                 
            else:
                nchannels = 2  
        elif self.Digitizer == 'Alazar':
            if self.ui.Aenable.currentText() == 'Enable':
                if self.ui.Benable.currentText() == 'Enable':
                    nchannels = 2
                else:
                    nchannels = 1
            elif self.ui.Benable.currentText() == 'Enable':
                nchannels = 1
            
        AlinesPerBline = self.ui.AlineAVG.value()*self.ui.Xsteps.value()+self.ui.PreClock.value()*2+self.ui.PostClock.value()
        sumLength = samples * AlinesPerBline * nchannels
        for ii in range(self.memoryCount):
             if self.ui.ACQMode.currentText() in ['RptBline', 'RptAline','SingleBline', 'SingleAline']:
                 self.Memory[ii]=np.zeros([self.ui.BlineAVG.value(), sumLength], dtype = np.uint16)
             elif self.ui.ACQMode.currentText() in ['SingleCscan','Mosaic','Mosaic+Cut']:
                 self.Memory[ii]=np.zeros([self.ui.BlineAVG.value()*self.ui.Ysteps.value(), sumLength], dtype = np.uint16)
        ###########################################################################################
        
    def SingleScan(self, mode):
        self.InitMemory()
        an_action = DAction('ConfigureBoard')
        self.DQueue.put(an_action)
        ###########################################################################################
        # start AODO 
        # print(self.ui.ACQMode.currentText())
        an_action = AODOAction('ConfigTask')
        self.AODOQueue.put(an_action)
        an_action = AODOAction('StartTask')
        self.AODOQueue.put(an_action)
        self.StagebackQueue.get()
        an_action = AODOAction('StopTask')
        self.AODOQueue.put(an_action)
        an_action = AODOAction('CloseTask')
        self.AODOQueue.put(an_action)

        # start digitizer, it will stop automatically when all Blines are acquired
        an_action = DAction('StartAcquire')
        self.DQueue.put(an_action)
        start = time.time()
        ######################################### collect data
        # collect data from digitizer, data format: [Y pixels, X*Z pixels]
        an_action = self.DbackQueue.get() # never time out
        print('time to fetch data: '+str(round(time.time()-start,3)))
        self.StagebackQueue.get() # wait for AODO CloseTask
        memoryLoc = an_action.action
        ############################################### display and save data
        if self.ui.FFTDevice.currentText() in ['None']:
            # put raw spectrum data into memory for dipersion compensation and background subtraction usage
            self.data = self.Memory[memoryLoc].copy()
            # In None mode, directly do display and save
            if np.sum(self.data)<10:
                print('spectral data all zeros!')
                # self.ui.PrintOut.append('spectral data all zeros!')
                self.log.write('spectral data all zeros!')
                return mode + " got all zeros..."
            an_action = DnSAction(mode, self.data, raw=True) # data in Memory[memoryLoc]
            self.DnSQueue.put(an_action)
        else:
            # In other modes, do FFT first
            an_action = GPUAction(self.ui.FFTDevice.currentText(), mode, memoryLoc)
            self.GPUQueue.put(an_action)
        return mode + " successfully finished..."
            
    def RptScan(self, mode):
        self.InitMemory()
        an_action = DAction('ConfigureBoard')
        self.DQueue.put(an_action)
        
        an_action = DnSAction('Clear')
        self.DnSQueue.put(an_action)
        # config AODO
        an_action = AODOAction('ConfigTask')
        self.AODOQueue.put(an_action)
        interrupt = None
        data_backs = 0 # count number of data backs
        ######################################################### repeat acquisition until Stop button is clicked
        while interrupt != 'Stop':
            # start AODO for one measurement
            an_action = AODOAction('StartTask')
            self.AODOQueue.put(an_action)
            self.StagebackQueue.get()
            an_action = AODOAction('StopTask')
            self.AODOQueue.put(an_action)
            
            # start digitizer for one acuquqisition
            an_action = DAction('StartAcquire')
            self.DQueue.put(an_action)
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
            else:
                # In other modes, do FFT first
                an_action = GPUAction(self.ui.FFTDevice.currentText(), mode, memoryLoc)
                self.GPUQueue.put(an_action)
            ######################################## check if Pause or Stop button is clicked
            interrupt = self.check_interrupt()
        
        # close AODO
        an_action = AODOAction('CloseTask')
        self.AODOQueue.put(an_action)
        self.StagebackQueue.get() # wait for AODO CloseTask
        # digitizer will close automatically
        message = str(data_backs)+ ' data received by weaver'
        # self.ui.PrintOut.append(message)
        self.log.write(message)
        an_action = GPUAction('display_FFT_actions')
        self.GPUQueue.put(an_action)
        an_action = DnSAction('display_counts')
        self.DnSQueue.put(an_action)
        return mode + ' successfully finished...'
  
    def Mosaic(self):
        # slice number increase, tile number restart from 1
        an_action = DnSAction('restart_tilenum') # data in Memory[memoryLoc]
        self.DnSQueue.put(an_action)

        # init memory space
        self.InitMemory()
        # configure digitizer for high res acquisition
        an_action = DAction('ConfigureBoard')
        self.DQueue.put(an_action)
        # clear all display windows
        an_action = DnSAction('Clear')
        self.DnSQueue.put(an_action)
        # generate Mosaic pattern, a Mosaic pattern consists of a list of MOSAIC object, 
        # each MOSAIC object defines a square of scanning area, which is defined by the X stage position, and Y stage start and stop position
        self.Mosaic_pattern, status = GenMosaic_XGalvo(self.ui.XStart.value(),\
                                        self.ui.XStop.value(),\
                                        self.ui.YStart.value(),\
                                        self.ui.YStop.value(),\
                                        self.ui.Xsteps.value()*self.ui.XStepSize.value()/1000,\
                                        self.ui.Overlap.value())
        if status != "Mosaic Generation success...":
            return 'Error', status
        # get total number of strips, i.e.，xstage positions
        total_stripes = len(self.Mosaic_pattern)
        # calculate the number of Cscans per stripe, i.e., Y stage positions
        Ystep = self.ui.YStepSize.value()*self.ui.Ysteps.value()
        CscansPerStripe = np.int16((self.ui.YStop.value()-self.ui.YStart.value())*1000/Ystep)
        self.totalTiles = CscansPerStripe * total_stripes
        # save the PreMosaic tile identification to disk
        an_action = DnSAction('WriteAgar', data = self.tile_flag, args = [ CscansPerStripe, total_stripes])
        self.DnSQueue.put(an_action)
        # init sample surface plot window
        args = [[0, 0], [CscansPerStripe, self.totalTiles]]
        an_action = DnSAction('Init_Mosaic', data = None, args = args) # data in Memory[memoryLoc]
        self.DnSQueue.put(an_action)
        
        # init local variables
        interrupt = None
        stripes = 1
        scan_direction = 1 # init scan direction to be backward
        agarTiles = 0
        
        # stage move to start XYZ position
        self.ui.XPosition.setValue(self.Mosaic_pattern[0].x)
        an_action = AODOAction('Xmove2')
        self.AODOQueue.put(an_action)
        self.StagebackQueue.get()
        self.ui.YPosition.setValue(self.Mosaic_pattern[0].ystop)
        an_action = AODOAction('Ymove2')
        self.AODOQueue.put(an_action)
        self.StagebackQueue.get()
        # adjust Z stage to put sample at focus
        # self.ui.ZPosition.setValue(initHeight + self.ui.ZIncrease.value())
        # an_action = AODOAction('Zmove2')
        # self.AODOQueue.put(an_action)
        # self.StagebackQueue.get()
        ############################################################# Iterate through strips for one Mosaic
        while np.any(self.Mosaic_pattern) and interrupt != 'Stop': 
            cscans = 0
            # stage move to X position of this stripe
            self.ui.XPosition.setValue(self.Mosaic_pattern[0].x)
            an_action = AODOAction('Xmove2')
            self.AODOQueue.put(an_action)
            self.StagebackQueue.get()
            
            # # adjust Z stage height according to the sample cutting slope 
            # Ztilt = (self.ui.XStopHeight.value()-self.ui.XStartHeight.value())/total_stripes
            # # print(Ztilt, self.ui.ZPosition.value(), self.ui.ZPosition.value()+Ztilt)
            # self.ui.ZPosition.setValue(self.ui.ZPosition.value()+Ztilt)
            # an_action = AODOAction('Zmove2')
            # self.AODOQueue.put(an_action)
            # self.StagebackQueue.get()
            #######################################################################
            # update scan direction and agarTiles at the start of each new strip
            scan_direction = np.uint32(np.mod(scan_direction+1,2))
            agarTiles = agarTiles * -1
            ############################################################  iterate through Cscans in one stripe
            while cscans < CscansPerStripe and interrupt != 'Stop': 
                if self.tile_flag[(stripes-1)][cscans] == 0: # next tile is agar
                    agarTiles += 1
                    cscans += 1
                else:
                    ###################################### 
                    # next tile is tissue, move to start of Y position
                    ydistance = self.ui.YPosition.value()+Ystep/1000.0 * agarTiles * (-1)**(scan_direction+1)
                    # message = 'agarTiles:'+str(agarTiles)+' ypos:'+str(round(ydistance,3))
                    # self.log.write(message)
                    # print(message)
                    self.ui.YPosition.setValue(ydistance)
                    an_action = AODOAction('Ymove2')
                    self.AODOQueue.put(an_action)
                    self.StagebackQueue.get()
                    
                    # reset agar tiles count
                    agarTiles = 0
                    ###################################### start one Cscan
                    # start AODO for one Cscan acquisition
                    an_action = AODOAction('ConfigTask', scan_direction)
                    self.AODOQueue.put(an_action)
                    an_action = AODOAction('StartTask')
                    self.AODOQueue.put(an_action)
                    self.StagebackQueue.get()
                    an_action = AODOAction('StopTask', scan_direction)
                    self.AODOQueue.put(an_action)
                    an_action = AODOAction('CloseTask')
                    self.AODOQueue.put(an_action)
                    
                    # start ATS9351 for one Cscan acquisition
                    an_action = DAction('StartAcquire')
                    self.DQueue.put(an_action)
                    
                    ###################################### collecting data
                    start = time.time()
                    # collect data from digitizer
                    an_action = self.DbackQueue.get() # never time out
                    
                    message = 'time to fetch data: '+str(round(time.time()-start,3))+'s'
                    # self.ui.PrintOut.append(message)
                    print(message)
                    self.log.write(message)
                    
                    
                    ####################################### if no FFT needed, directly display data 
                    # get data location in memory space
                    memoryLoc = an_action.action
                    
                    if self.ui.FFTDevice.currentText() in ['Alazar', 'None']:
                        # directly do display and save
                        args = [[cscans, stripes], [CscansPerStripe, self.totalTiles]]
                        data = self.Memory[memoryLoc].copy()
                        an_action = DnSAction('Mosaic', data, raw = True, args=args) 
                        self.DnSQueue.put(an_action)
                    else:
                        # need to do FFT before display and save
                        args = [[cscans, stripes], [CscansPerStripe, self.totalTiles]]
                        an_action = GPUAction(self.ui.FFTDevice.currentText(), 'Mosaic', memoryLoc, args=args)
                        self.GPUQueue.put(an_action)
                    # increment files imaged
                    cscans +=1
                    self.ui.statusbar.showMessage('Imaging '+str(stripes)+'th strip, '+str(cscans)+'th Cscan ')
                    # display sample surface. This will display last tile, not the current tile, because FFT is not done yet for the current tile
                    an_action = DnSAction('display_mosaic') 
                    self.DnSQueue.put(an_action)
                    
                    self.StagebackQueue.get() # wait for stage movement 
                    
                ############################ check user input
                interrupt = self.check_interrupt()
            
            # finishing this stripe, delete one MOSAIC object from the mosaic pattern
            self.Mosaic_pattern = np.delete(self.Mosaic_pattern, 0)
            stripes = stripes + 1
        # wait 6 seconds for FFT of last tile to finish
        time.sleep(6)
        an_action = DnSAction('display_mosaic') 
        self.DnSQueue.put(an_action)  
        an_action = DnSAction('Save_mosaic') 
        self.DnSQueue.put(an_action)
        return interrupt, 'Mosaic successfully finished...'
    
    def check_interrupt(self):
        interrupt = None
        try:
            # check if Pause button is clicked
           interrupt = self.PauseQueue.get_nowait()  # time out 0.001 s
           # print(interrupt)
           ##################################### if Pause button is clicked
           if interrupt == 'Pause':
               # wait until unpause button or stop button is clicked
               interrupt = self.PauseQueue.get()  # never time out
               # print('queue output:',interrupt)
               # if unpause button is clicked        
               if interrupt == 'Resume':
                   interrupt = None
        except:
            return interrupt
        return interrupt
        
    def PreMosaic(self):
        ######################### setting accellarated scan configs
        Yds = 30 # Y dimension scan speed accellaration scale for fast pre-scan
        while self.ui.Ysteps.value()%Yds:
            Yds -= 1
        message = '\n Y dimension scan speed accellaration scale for fast pre-scan is'+str(Yds)+'\n'
        print(message)
        self.log.write(message)
        ##################
        # clear display windows
        an_action = DnSAction('Clear')
        self.DnSQueue.put(an_action)
        # check downsampling status flag
        self.ui.DSing.setChecked(True)
        # save FOV settings
        Xsteps = self.ui.Xsteps.value()
        Ysteps = self.ui.Ysteps.value()
        XStepSize = self.ui.XStepSize.value()
        YStepSize = self.ui.YStepSize.value()
        AlineAVG = self.ui.AlineAVG.value()
        BlineAVG = self.ui.BlineAVG.value()
        save = self.ui.Save.isChecked()
        FFTDevice = self.ui.FFTDevice.currentText()
        scale = self.ui.scale.value()
        # Zpos = initHeight 

        # set downsampled FOV
        self.ui.Xsteps.setValue(Xsteps)
        self.ui.Ysteps.setValue(Ysteps//Yds)
        self.ui.XStepSize.setValue(XStepSize)
        self.ui.YStepSize.setValue(YStepSize*Yds)
        self.ui.AlineAVG.setValue(1)
        self.ui.BlineAVG.setValue(1)
        self.ui.Save.setChecked(False)
        self.ui.FFTDevice.setCurrentText('GPU')
        ############## adjust mosaic display scale
        scale_start = 5
        while Xsteps%scale_start or (Ysteps//Yds)%scale_start:
            scale_start -= 1
        self.ui.scale.setValue(scale_start)

        message = '\n fast pre-scan mosaic display scale is'+str(self.ui.scale.value())+'\n'
        print(message)
        self.log.write(message)
        
        
        self.InitMemory()
        # load surface profile
        if os.path.isfile(self.ui.Surf_DIR.text()):
            self.surfCurve = np.uint16(np.fromfile(self.ui.Surf_DIR.text(), dtype=np.uint16))
            if self.surfCurve.shape[0] != Xsteps:
                self.surfCurve = None
                print('surface data not match FOV setting, using all zeros')
        else:
            print('surface data not found, using all zeros')
            self.surfCurve = None

        # configure digitizer for low res acquisition
        an_action = DAction('ConfigureBoard')
        self.DQueue.put(an_action)
        # generate Mosaic pattern, a Mosaic pattern consists of a list of MOSAIC object, 
        # each MOSAIC object defines a stripe of scanning area, which is defined by the X stage position, and Y stage start and stop position
        self.Mosaic_pattern, status = GenMosaic_XGalvo(self.ui.XStart.value(),\
                                        self.ui.XStop.value(),\
                                        self.ui.YStart.value(),\
                                        self.ui.YStop.value(),\
                                        self.ui.Xsteps.value()*self.ui.XStepSize.value()/1000,\
                                        self.ui.Overlap.value())
        if status != "Mosaic Generation success...":
            self.ui.DSing.setChecked(False)
            # reset FOV
            self.ui.Xsteps.setValue(Xsteps)
            self.ui.Ysteps.setValue(Ysteps)
            self.ui.XStepSize.setValue(XStepSize)
            self.ui.YStepSize.setValue(YStepSize)
            self.ui.AlineAVG.setValue(AlineAVG)
            self.ui.BlineAVG.setValue(BlineAVG)
            self.ui.Save.setChecked(save)
            self.ui.FFTDevice.setCurrentText(FFTDevice)
            self.ui.scale.setValue(scale)
            return 'Error', status
        total_stripes = len(self.Mosaic_pattern)
        # calculate the number of Cscans per stripe
        Ystep = self.ui.YStepSize.value()*self.ui.Ysteps.value()
        CscansPerStripe = np.int16((self.ui.YStop.value()-self.ui.YStart.value())*1000/Ystep)
        self.totalTiles = CscansPerStripe * total_stripes
        # init sample surface window
        args = [[0, 0], [CscansPerStripe, self.totalTiles]]
        an_action = DnSAction('Init_Mosaic', data = None, args = args) 
        self.DnSQueue.put(an_action)
        
        # init tile profiling array
        # tile_flag: whether this tile is tissue or agar
        self.tile_flag = np.zeros((len(self.Mosaic_pattern),CscansPerStripe),dtype = np.uint8)
        # tmp_cscan: average of all tissue tiles
        self.tmp_cscan = np.zeros([self.ui.Ysteps.value()*self.ui.BlineAVG.value() * \
                                   (self.ui.Xsteps.value()*self.ui.AlineAVG.value()+ self.ui.PreClock.value()*2 + self.ui.PostClock.value()),\
                                                     self.ui.DepthRange.value()])
        interrupt = None
        stripes = 1
        scan_direction = 1 # init scan direction to be backward
        
        # stage move to start tile position
        self.ui.XPosition.setValue(self.Mosaic_pattern[0].x)
        self.ui.YPosition.setValue(self.Mosaic_pattern[0].ystop)
        # self.ui.ZPosition.setValue(Zpos)
        an_action = AODOAction('Xmove2')
        self.AODOQueue.put(an_action)
        self.StagebackQueue.get()
        an_action = AODOAction('Ymove2')
        self.AODOQueue.put(an_action)
        self.StagebackQueue.get()
        # an_action = AODOAction('Zmove2')
        # self.AODOQueue.put(an_action)
        # self.StagebackQueue.get()
        
        ############################################################# Iterate through strips for one Mosaic
        while np.any(self.Mosaic_pattern) and interrupt != 'Stop': 
            cscans = 0
            # stage move to start of this stripe
            self.ui.XPosition.setValue(self.Mosaic_pattern[0].x)
            an_action = AODOAction('Xmove2')
            self.AODOQueue.put(an_action)
            self.StagebackQueue.get()
            
            # # Auto adjust focus according to surface height in X min and X max
            # Ztilt = (self.ui.XStopHeight.value()-self.ui.XStartHeight.value())/total_stripes
            # # print(Ztilt, self.ui.ZPosition.value(), self.ui.ZPosition.value()+Ztilt)
            # self.ui.ZPosition.setValue(self.ui.ZPosition.value()+Ztilt)
            # an_action = AODOAction('Zmove2')
            # self.AODOQueue.put(an_action)
            # self.StagebackQueue.get()
            
            scan_direction = np.uint32(np.mod(scan_direction+1,2))
            # configure AODO
            an_action = AODOAction('ConfigTask', scan_direction)
            self.AODOQueue.put(an_action)
            ############################################################  iterate through Cscans in one stripe
            while cscans < CscansPerStripe and interrupt != 'Stop': 
                ###################################### start one Cscan
                # start AODO for one Cscan acquisition
                an_action = AODOAction('StartTask')
                self.AODOQueue.put(an_action)
                self.StagebackQueue.get()
                an_action = AODOAction('StopTask', scan_direction)
                self.AODOQueue.put(an_action)
                
                # start ATS9351 for one Cscan acquisition
                an_action = DAction('StartAcquire')
                self.DQueue.put(an_action)
                # start = time.time()
                ###################################### collecting data
                # collect data from digitizer
                an_action = self.DbackQueue.get() # never time out
                memoryLoc = an_action.action
                ####################################### display data 
                # need to do FFT before display and save
                args = [[cscans, stripes], [CscansPerStripe, self.totalTiles]]
                an_action = GPUAction(self.ui.FFTDevice.currentText(), 'Mosaic', memoryLoc, args=args)
                self.GPUQueue.put(an_action)
                # get cscan data
                while self.GPU2weaverQueue.qsize()>1:
                    cscan =self.GPU2weaverQueue.get()
                cscan = self.GPU2weaverQueue.get()
                # identify agar from tissue
                self.identify_agar(cscan, stripes, cscans)
                
                # increment files imaged
                cscans +=1
                self.ui.statusbar.showMessage('finished '+str(stripes)+'th strip, '+str(cscans)+'th Cscan ')
                
                ######################################## check if Pause button is clicked
                interrupt = self.check_interrupt()
                
            an_action = DnSAction('display_mosaic') # data in Memory[memoryLoc]
            self.DnSQueue.put(an_action)
            # print('finished this cycle for presurf')
            an_action = AODOAction('CloseTask')
            self.AODOQueue.put(an_action)
            self.StagebackQueue.get() # wait for AODO CloseTask
            # finishing this stripe, delete one MOSAIC object from the mosaic pattern
            self.Mosaic_pattern = np.delete(self.Mosaic_pattern, 0)
            stripes = stripes + 1
            
        # find slice surface
        self.Focusing(self.tmp_cscan)
        
        # wait one second for the last tile to be displayed
        time.sleep(1)
        self.ui.DSing.setChecked(False)
        # reset FOV
        self.ui.Xsteps.setValue(Xsteps)
        self.ui.Ysteps.setValue(Ysteps)
        self.ui.XStepSize.setValue(XStepSize)
        self.ui.YStepSize.setValue(YStepSize)
        self.ui.AlineAVG.setValue(AlineAVG)
        self.ui.BlineAVG.setValue(BlineAVG)
        self.ui.Save.setChecked(save)
        self.ui.FFTDevice.setCurrentText(FFTDevice)
        self.ui.scale.setValue(scale)
        
        return interrupt, status
    
    def identify_agar(self, cscan, stripes, cscans):
        value = np.mean(cscan,1)
        # reshape into Ypixels x Xpixels matrix
        value = value.reshape([self.ui.Ysteps.value()*self.ui.BlineAVG.value(),\
                               self.ui.Xsteps.value()*self.ui.AlineAVG.value()+ \
                               self.ui.PreClock.value()*2 + self.ui.PostClock.value()])
        # trim galvo fly-back data
        value = value[:,self.ui.PreClock.value():self.ui.PreClock.value()+\
                      self.ui.Xsteps.value()*self.ui.AlineAVG.value()]
        # # downsample X dimension
        # value = value.reshape([self.ui.Ysteps.value()*self.ui.BlineAVG.value(),\
        #                        self.ui.Xsteps.value()*self.ui.AlineAVG.value()//self.Yds,self.Yds]).mean(-1)
        self.ui.tileMean.setValue(np.mean(value))
        if np.sum(value > self.ui.AgarValue.value())>value.shape[1]*value.shape[0]*0.05: 
            self.tile_flag[stripes - 1][cscans] = 1
            self.ui.TissueRadio.setChecked(True)
            self.tmp_cscan = self.tmp_cscan + cscan/100.0
        else:
            self.ui.TissueRadio.setChecked(False)
            
    def Focusing(self, cscan):
        ######################################################### find average slice surface
        cscan = cscan.reshape([self.ui.Ysteps.value()*self.ui.BlineAVG.value(),\
                               self.ui.Xsteps.value()*self.ui.AlineAVG.value()+ self.ui.PreClock.value()*2 + self.ui.PostClock.value(),\
                               self.ui.DepthRange.value()])
        bscan = cscan.mean(0)
        # remove galvo flayback data
        bscan = bscan[self.ui.PreClock.value():self.ui.PreClock.value()+self.ui.Xsteps.value()*self.ui.AlineAVG.value(),:]
        # flatten surface
        if np.any(self.surfCurve):
            bscan_flatten = np.zeros(bscan.shape, dtype = np.float32)
            for xx in range(bscan_flatten.shape[0]):
                bscan_flatten[xx,0:bscan.shape[1]-self.surfCurve[xx]] = bscan[xx,self.surfCurve[xx]:]
            plt.figure()
            plt.imshow(bscan_flatten)
            plt.savefig('slice'+str(self.ui.CuSlice.value())+'surface.jpg')
            plt.close()
        else:
            bscan_flatten = bscan
        # find tile surface
        ascan = bscan_flatten.mean(0)
        
        surfHeight = findchangept(ascan,1)

        ##########################################################
        self.ui.SurfHeight.setValue(surfHeight)
        message = 'tile surf is:'+str(surfHeight)
        print(message)
        self.log.write(message)
        delta_z = (self.ui.SurfHeight.value()-self.ui.SurfSet.value())*ZPIXELSIZE/1000.0
        self.ui.ZIncrease.setValue(delta_z)
        
    def SurfSlice(self):
        # determine if one image per cut
        # if self.ui.ImageZDepth.value() - self.ui.SliceZDepth.value() >1: # unit: um
        #     message = ' imaging deeper than cutting, cut multiple times per image...'
        #     self.ui.statusbar.showMessage(message)
        #     # self.ui.PrintOut.append(message)
        #     self.log.write(message)
        #     message = self.MultiCutPerImage()
        #     self.ui.statusbar.showMessage(message)
        #     # self.ui.PrintOut.append(message)
        #     self.log.write(message)
            
            
        # elif self.ui.SliceZDepth.value() - self.ui.ImageZDepth.value() >1:
        #     message = ' slicing deeper than imaging, image multiple times per slice...'
        #     self.ui.statusbar.showMessage(message)
        #     # self.ui.PrintOut.append(message)
        #     self.log.write(message)
            
        #     message = ' this mode has not been configured, abort...'
        #     self.ui.statusbar.showMessage(message)
        #     # self.ui.PrintOut.append(message)
        #     self.log.write(message)
            
        # else:
        message = ' slicing and imaging depth same, one image per cut...'
        self.ui.statusbar.showMessage(message)
        # self.ui.PrintOut.append(message)
        self.log.write(message)
        message = self.OneImagePerCut()
        self.ui.statusbar.showMessage(message)
        # self.ui.PrintOut.append(message)
        self.log.write(message)
            
        self.ui.RunButton.setChecked(False)
        self.ui.RunButton.setText('Go')
        self.ui.PauseButton.setChecked(False)
        self.ui.PauseButton.setText('Pause')
        return message
    
    def OneImagePerCut(self):
        for ii in range(np.uint16(self.ui.SMPthickness.value()*1000//self.ui.ImageZDepth.value())):
            # cut one slice
            message = self.SingleCut(self.ui.SliceZStart.value()+ii*self.ui.SliceZDepth.value()/1000.0)
            print(message)
            if message != 'Slice success':
                return message
            message = '\nCUT HEIGHT:'+str(self.ui.SliceZStart.value()+ii*self.ui.SliceZDepth.value()/1000.0)+'\n'
            print(message)
            self.log.write(message)
            # remeasure background
            # if self.ui.auto_background.isChecked():
            #     self.get_background()
                # time.sleep(1)
            ##################################################
            interrupt = self.check_interrupt()
            if interrupt == 'Stop':
                message = 'user stopped acquisition...'
                return message
            ########################################################
            # # move to defined zero
            # self.ui.ZPosition.setValue(self.ui.definedZero.value())
            # an_action = AODOAction('Zmove2')
            # self.AODOQueue.put(an_action)
            # self.StagebackQueue.get()
            # ##################################################
            # interrupt = self.check_interrupt()
            # if interrupt == 'Stop':
            #     message = 'user stopped acquisition...'
            #     return message
            ########################################################
            # move to X Y Z
            self.ui.XPosition.setValue(self.ui.XStart.value())
            self.ui.YPosition.setValue(self.ui.YStart.value())
            an_action = AODOAction('Xmove2')
            self.AODOQueue.put(an_action)
            self.StagebackQueue.get()
            ##################################################
            interrupt = self.check_interrupt()
            if interrupt == 'Stop':
                message = 'user stopped acquisition...'
                return message
            ########################################################
            an_action = AODOAction('Ymove2')
            self.AODOQueue.put(an_action)
            self.StagebackQueue.get()
            ##################################################
            interrupt = self.check_interrupt()
            if interrupt == 'Stop':
                message = 'user stopped acquisition...'
                return message
            ########################################################
            # self.ui.ZPosition.setValue(self.ui.XStartHeight.value()+ii*self.ui.ImageZDepth.value()/1000.0)
            # an_action = AODOAction('Zmove2')
            # self.AODOQueue.put(an_action)
            # self.StagebackQueue.get()
            # message = '\nIMAGE HEIGHT:'+str(self.ui.XStartHeight.value()+ii*self.ui.ImageZDepth.value()/1000.0)+'\n'
            # print(message)
            # self.log.write(message)
            # ##################################################
            # interrupt = self.check_interrupt()
            # if interrupt == 'Stop':
            #     message = 'user stopped acquisition...'
            #     return message
            ########################################################
            # do surf
            if ii%self.ui.backReget.value() == 0:
                interrupt, status = self.PreMosaic()#self.ui.XStartHeight.value()+ii*self.ui.ImageZDepth.value()/1000.0)
                if interrupt == 'Stop':
                    return 'PreMosaic stopped by user...'
                elif interrupt == 'Error':
                    return status
                # if np.abs(self.ui.ZIncrease.value()) > 0.1:
                #     message= 'PreMosaic autofocus error...' + str(self.ui.ZIncrease.value())
                #     print(message)
                #     self.log.write(message)
                #     return message
                # # if focus adjustment is larger than 40 micron, redo PreMosaic
                # elif np.abs(self.ui.ZIncrease.value()) > 0.04:
                #     message= 'PreMosaic focus adjust ...' + str(self.ui.ZIncrease.value())
                #     print(message)
                #     self.log.write(message)

                #     delta_z = self.ui.ZIncrease.value()
                #     interrupt = self.PreMosaic(self.ui.XStartHeight.value()+ii*self.ui.ImageZDepth.value()/1000.0 + delta_z)
                #     if interrupt == 'Stop':
                #         return 'PreMosaic stopped by user...'
                #     if np.abs(self.ui.ZIncrease.value()) > 0.1:
                #         message= 'PreMosaic autofocus error...' + str(self.ui.ZIncrease.value())
                #         print(message)
                #         self.log.write(message)
                #         return message
                # else:
                #     delta_z = 0
            # else:
            #     delta_z = 0
            interrupt, status = self.Mosaic()#self.ui.XStartHeight.value()+ii*self.ui.ImageZDepth.value()/1000.0 + delta_z)
            if interrupt == 'Stop':
                return 'user stopped acquisition...'
            elif interrupt == 'Error':
                return status
        # LAST CUT 
        message = self.SingleCut(self.ui.SliceZStart.value()+(ii+1)*self.ui.SliceZDepth.value()/1000.0)
        if message != 'Slice success':
            return message
        return 'Mosaic+Cut successful...'
    
    def MultiCutPerImage(self):
        # cut first time
        message = self.SingleCut(self.ui.SliceZStart.value())
        print(message)
        if message != 'Slice success':
            return message
        for ii in range(np.int16(self.ui.SMPthickness.value()*1000//self.ui.ImageZDepth.value())):
            # remeasure background
            if ii%self.ui.backReget.value() == 0:
                self.get_background()
            ##################################################
            interrupt = self.check_interrupt()
            if interrupt == 'Stop':
                message = 'user stopped acquisition...'
                return message
            ########################################################
            # move to defined zero
            self.ui.ZPosition.setValue(self.ui.definedZero.value())
            an_action = AODOAction('Zmove2')
            self.AODOQueue.put(an_action)
            self.StagebackQueue.get()
            ##################################################
            interrupt = self.check_interrupt()
            if interrupt == 'Stop':
                message = 'user stopped acquisition...'
                return message
            ########################################################

            # move to X Y Z
            self.ui.XPosition.setValue(self.ui.XStart.value())
            self.ui.YPosition.setValue(self.ui.YStart.value())
            an_action = AODOAction('Xmove2')
            self.AODOQueue.put(an_action)
            self.StagebackQueue.get()
            ##################################################
            interrupt = self.check_interrupt()
            if interrupt == 'Stop':
                message = 'user stopped acquisition...'
                return message
            ########################################################
            an_action = AODOAction('Ymove2')
            self.AODOQueue.put(an_action)
            self.StagebackQueue.get()
            ##################################################
            interrupt = self.check_interrupt()
            if interrupt == 'Stop':
                message = 'user stopped acquisition...'
                return message
            ########################################################
            # move to next image height
            self.ui.ZPosition.setValue(self.ui.XStartHeight.value()+ii*self.ui.ImageZDepth.value()/1000.0)
            an_action = AODOAction('Zmove2')
            self.AODOQueue.put(an_action)
            self.StagebackQueue.get()
            ##################################################
            interrupt = self.check_interrupt()
            if interrupt == 'Stop':
                message = 'user stopped acquisition...'
                return message
            ########################################################
            # do surf
            if ii%self.ui.backReget.value() == 0:
                interrupt = self.PreMosaic()
                if interrupt == 'Stop':
                    return 'PreMosaic stopped by user...'
            interrupt, status = self.Mosaic()
            if interrupt == 'Stop':
                return 'user stopped acquisition...'
            
            ##################################################
            interrupt = self.check_interrupt()
            if interrupt == 'Stop':
                message = 'user stopped acquisition...'
                return message
            ########################################################
            # cut slices
            message = self.RptCut(self.ui.SliceZStart.value()+ii*self.ui.ImageZDepth.value()/1000.0+self.ui.SliceZDepth.value()/1000.0, \
                                    np.uint16(self.ui.ImageZDepth.value()//self.ui.SliceZDepth.value()))
            print(message)
            if message != 'Slice success':
                return message
        # LAST CUT 
        message = self.SingleCut(self.ui.SliceZStart.value()+(ii+1)*self.ui.SliceZDepth.value()/1000.0)
        if message != 'Slice success':
            return message
        return 'Mosaic+Cut successful...'
        
    def SingleCut(self, zpos):
        # # move to defined zero
        # self.ui.ZPosition.setValue(self.ui.definedZero.value())
        # an_action = AODOAction('Zmove2')
        # self.AODOQueue.put(an_action)
        # self.StagebackQueue.get()
        # ##################################################
        # interrupt = self.check_interrupt()
        # if interrupt == 'Stop':
        #     message = 'user stopped acquisition...'
        #     return message
        # ########################################################
        # self.ui.Gotozero.setChecked(True)
        # message = self.Gotozero()
        # if message != 'gotozero success...':
        #     return message
        # self.ui.statusbar.showMessage(message)
        
        # go to start Y
        self.ui.YPosition.setValue(self.ui.SliceY.value())
        an_action = AODOAction('Ymove2')
        self.AODOQueue.put(an_action)
        self.StagebackQueue.get()
        
        
        ##################################################
        interrupt = self.check_interrupt()
        if interrupt == 'Stop':
            message = 'user stopped acquisition...'
            return message
        
        # go to start X
       
        self.ui.XPosition.setValue(self.ui.SliceX.value())
        an_action = AODOAction('Xmove2')
        self.AODOQueue.put(an_action)
        self.StagebackQueue.get()
        
        ##################################################
        interrupt = self.check_interrupt()
        if interrupt == 'Stop':
            message = 'user stopped acquisition...'
            return message
        
        # start vibratome
        self.ui.VibEnabled.setText('Stop Vibratome')
        self.ui.VibEnabled.setChecked(True)
        an_action = AODOAction('startVibratome')
        self.AODOQueue.put(an_action)
        self.StagebackQueue.get()
        
        # go to start Z
        self.ui.ZPosition.setValue(zpos)
        an_action = AODOAction('Zmove2')
        self.AODOQueue.put(an_action)
        self.StagebackQueue.get()
        
        
        ##################################################
        ##################################################
        interrupt = self.check_interrupt()
        if interrupt == 'Stop':
            message = 'user stopped acquisition...'
        ########################################################
            # stop vibratome
            self.ui.VibEnabled.setText('Start Vibratome')
            self.ui.VibEnabled.setChecked(False)
            an_action = AODOAction('stopVibratome')
            self.AODOQueue.put(an_action)
            self.StagebackQueue.get()
            return message
        ########################################################
        # slicing
       
        if self.ui.SliceDir.isChecked():
            sign = 1
        else:
            sign = -1
        self.ui.YPosition.setValue(self.ui.SliceLength.value()*sign+self.ui.YPosition.value())
        speed = self.ui.YSpeed.value()
        self.ui.YSpeed.setValue(self.ui.SliceSpeed.value())
        an_action = AODOAction('Ymove2')
        self.AODOQueue.put(an_action)
        self.StagebackQueue.get()
        self.ui.YSpeed.setValue(speed)
        # stop vibratome
        self.ui.VibEnabled.setText('Start Vibratome')
        self.ui.VibEnabled.setChecked(False)
        an_action = AODOAction('stopVibratome')
        self.AODOQueue.put(an_action)
        self.StagebackQueue.get()
        return 'Slice success'
        
    def RptCut(self, start_height, cuts):
        # # move to defined zero
        # self.ui.ZPosition.setValue(self.ui.definedZero.value())
        # an_action = AODOAction('Zmove2')
        # self.AODOQueue.put(an_action)
        # self.StagebackQueue.get()
        # ##################################################
        # interrupt = self.check_interrupt()
        # if interrupt == 'Stop':
        #     message = 'user stopped acquisition...'
        #     return message
        
        # go to start Y
        self.ui.YPosition.setValue(self.ui.SliceY.value())
        an_action = AODOAction('Ymove2')
        self.AODOQueue.put(an_action)
        self.StagebackQueue.get()
        ##################################################
        interrupt = self.check_interrupt()
        if interrupt == 'Stop':
            message = 'user stopped acquisition...'
            return message
        # ########################################################
        ########################################################
        # go to start X
        self.ui.XPosition.setValue(self.ui.SliceX.value())
        an_action = AODOAction('Xmove2')
        self.AODOQueue.put(an_action)
        self.StagebackQueue.get()
        ##################################################
        interrupt = self.check_interrupt()
        if interrupt == 'Stop':
            message = 'user stopped acquisition...'
            return message
        ########################################################
        
        # # go to start Z
        # self.ui.ZPosition.setValue(start_height)
        # an_action = AODOAction('Zmove2')
        # self.AODOQueue.put(an_action)
        # self.StagebackQueue.get()
        # ##################################################
        # interrupt = self.check_interrupt()
        # if interrupt == 'Stop':
        #     message = 'user stopped acquisition...'
        #     return message
        # ########################################################
        # slicing
        # start vibratome
        self.ui.VibEnabled.setText('Stop Vibratome')
        self.ui.VibEnabled.setChecked(True)
        an_action = AODOAction('startVibratome')
        self.AODOQueue.put(an_action)
        self.StagebackQueue.get()
        for ii in range(cuts):
            # Z stage move up
            self.ui.ZPosition.setValue(start_height+self.ui.SliceZDepth.value()/1000.0*ii)
            an_action = AODOAction('Zmove2')
            self.AODOQueue.put(an_action)
            self.StagebackQueue.get()
            # Move Y stage slowly to cut
            if self.ui.SliceDir.isChecked():
                sign = 1
            else:
                sign = -1
            self.ui.YPosition.setValue(self.ui.SliceLength.value()*sign+self.ui.YPosition.value())
            speed = self.ui.YSpeed.value()
            self.ui.YSpeed.setValue(self.ui.SliceSpeed.value())
            an_action = AODOAction('Ymove2')
            self.AODOQueue.put(an_action)
            self.StagebackQueue.get()
            self.ui.YSpeed.setValue(speed)
            
            interrupt = self.check_interrupt()
            if interrupt == 'Stop':
                message = 'user stopped acquisition...'
                # stop vibratome
                self.ui.VibEnabled.setText('Start Vibratome')
                self.ui.VibEnabled.setChecked(False)
                an_action = AODOAction('stopVibratome')
                self.AODOQueue.put(an_action)
                self.StagebackQueue.get()
                return message
            # move Y stage back to position
            self.ui.YPosition.setValue(self.ui.SliceY.value())
            an_action = AODOAction('Ymove2')
            self.AODOQueue.put(an_action)
            self.StagebackQueue.get()
            
            interrupt = self.check_interrupt()
            if interrupt == 'Stop':
                message = 'user stopped acquisition...'
                # stop vibratome
                self.ui.VibEnabled.setText('Start Vibratome')
                self.ui.VibEnabled.setChecked(False)
                an_action = AODOAction('stopVibratome')
                self.AODOQueue.put(an_action)
                self.StagebackQueue.get()
                return message
            


        # stop vibratome
        self.ui.VibEnabled.setText('Start Vibratome')
        self.ui.VibEnabled.setChecked(False)
        an_action = AODOAction('stopVibratome')
        self.AODOQueue.put(an_action)
        self.StagebackQueue.get()
        self.ui.SliceZStart.setValue(self.ui.ZPosition.value())
        return 'Slice success'
        
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
            failed_times = 0
            while message != self.ui.ACQMode.currentText()+" successfully finished...":
                failed_times+=1
                if failed_times > 10:
                    self.ui.ACQMode.setCurrentText(mode)
                    self.ui.FFTDevice.setCurrentText(device)
                    self.ui.Gotozero.setChecked(False)
                    return message
                message = self.SingleScan(self.ui.ACQMode.currentText())
                self.log.write(message)
                time.sleep(1)
            time.sleep(0.1)
            # get Aline data
            # sometimes previous scan will put into queue, probably because gotozero didn't check off timely
            while self.GPU2weaverQueue.qsize()>1:
                data =self.GPU2weaverQueue.get()
            data =self.GPU2weaverQueue.get()
            print(data.shape, self.GPU2weaverQueue.qsize())
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
            # self.ui.PrintOut.append(message)
            self.log.write(message)
            # handle error condistions
            if m < self.ui.AlinePeakMin.value():
                message = 'peak height='+str(m)+ ' peak too small, abort...'
                print(message)
                # self.ui.PrintOut.append(message)
                self.log.write(message)
                message = 'start depth: '+str(start_depth)+ ' end depth: '+str( end_depth)
                print(message)
                # self.ui.PrintOut.append(message)
                self.log.write(message)
                self.ui.ACQMode.setCurrentText(mode)
                self.ui.FFTDevice.setCurrentText(device)
                self.ui.Gotozero.setChecked(False)
                
                fp = open('D:\SSOCT_HE\data\gotozerofail.txt', 'w')
                data = Aline[start_depth:end_depth]
                data.tofile(fp)
                fp.close()
                
                return ' peak too small, abort...'
            elif m>=self.ui.AlinePeakMax.value():
                message = 'peak height='+str(m)+' this means spectral samples are all 0s, increase XforAline, abort...'
                print(message)
                # self.ui.PrintOut.append(message)
                self.log.write(message)
                message = 'start depth: '+str(start_depth)+ ' end depth: '+str( end_depth)
                print(message)
                # self.ui.PrintOut.append(message)
                self.log.write(message)
                self.ui.ACQMode.setCurrentText(mode)
                self.ui.FFTDevice.setCurrentText(device)
                self.ui.Gotozero.setChecked(False)
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
        current_Xposition = self.ui.XPosition.value()
        current_Yposition = self.ui.YPosition.value()
        current_Zposition = self.ui.ZPosition.value()
        iteration = 50
        for i in range(iteration):
            if not self.ui.ZstageTest.isChecked():
                message = 'Stage test stopped by user...'
                break
            # measure ALine
            message = self.SingleScan(self.ui.ACQMode.currentText())
            self.log.write(message)
            # self.ui.PrintOut.append(message)
            failed_times = 0
            while message != self.ui.ACQMode.currentText()+" successfully finished...":
                failed_times+=1
                if failed_times > 10:
                    self.ui.ACQMode.setCurrentText(mode)
                    self.ui.FFTDevice.setCurrentText(device)
                    self.ui.Gotozero.setChecked(False)
                    return message
                message = self.SingleScan(self.ui.ACQMode.currentText())
                self.log.write(message)
                # self.ui.PrintOut.append(message)
                time.sleep(1)
            time.sleep(0.1)
            
            if not self.ui.ZstageTest.isChecked():
                message = 'Stage test stopped by user...'
                break
            self.ui.ZPosition.setValue(5)
            an_action = AODOAction('Zmove2')
            self.AODOQueue.put(an_action)
            self.StagebackQueue.get()
            if not self.ui.ZstageTest.isChecked():
                message = 'Stage test stopped by user...'
                break
            # move to clear XY position
            self.ui.XPosition.setValue(45)
            an_action = AODOAction('Xmove2')
            self.AODOQueue.put(an_action)
            self.StagebackQueue.get()
            if not self.ui.ZstageTest.isChecked():
                message = 'Stage test stopped by user...'
                break
            self.ui.YPosition.setValue(20)
            an_action = AODOAction('Ymove2')
            self.AODOQueue.put(an_action)
            self.StagebackQueue.get()
            if not self.ui.ZstageTest.isChecked():
                message = 'Stage test stopped by user...'
                break
            # move Z stage 
            self.ui.ZPosition.setValue(40)
            an_action = AODOAction('Zmove2')
            self.AODOQueue.put(an_action)
            self.StagebackQueue.get()
            
            self.ui.ZPosition.setValue(40.1)
            an_action = AODOAction('Zmove2')
            self.AODOQueue.put(an_action)
            self.StagebackQueue.get()
            
            self.ui.ZPosition.setValue(40.15)
            an_action = AODOAction('Zmove2')
            self.AODOQueue.put(an_action)
            self.StagebackQueue.get()
            if not self.ui.ZstageTest.isChecked():
                message = 'Stage test stopped by user...'
                break
            self.ui.ZPosition.setValue(5)
            an_action = AODOAction('Zmove2')
            self.AODOQueue.put(an_action)
            self.StagebackQueue.get()
            if not self.ui.ZstageTest.isChecked():
                message = 'Stage test stopped by user...'
                break
            # move to original XY position
            self.ui.XPosition.setValue(current_Xposition)
            an_action = AODOAction('Xmove2')
            self.AODOQueue.put(an_action)
            self.StagebackQueue.get()
            if not self.ui.ZstageTest.isChecked():
                message = 'Stage test stopped by user...'
                break
            self.ui.YPosition.setValue(current_Yposition)
            an_action = AODOAction('Ymove2')
            self.AODOQueue.put(an_action)
            self.StagebackQueue.get()
            if not self.ui.ZstageTest.isChecked():
                message = 'Stage test stopped by user...'
                break
            # move Z stage up
            self.ui.ZPosition.setValue(current_Zposition)
            an_action = AODOAction('Zmove2')
            self.AODOQueue.put(an_action)
            self.StagebackQueue.get()
            
        self.ui.ZstageTest.setChecked(False)
        # self.weaverBackQueue.put(0)
        self.ui.ACQMode.setCurrentText(mode)
        self.ui.FFTDevice.setCurrentText(device)
        return 'Stage test successfully finished...'
        
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
                # self.ui.PrintOut.append(message)
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
            
            self.ui.ZPosition.setValue(7)
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
                # self.ui.PrintOut.append(message)
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

    def read_background(self):
        if self.Digitizer == 'Alazar':
            samples = self.ui.PreSamples.value()+self.ui.PostSamples.value()
        elif self.Digitizer == 'ART':
            samples = self.ui.PostSamples_2.value() - self.ui.DelaySamples.value()-self.ui.TrimSamples.value()
        background_path = self.ui.BG_DIR.text()

        if os.path.isfile(background_path):
            self.background = np.fromfile(background_path, dtype=np.float32)
        else:
            self.background = np.float32(np.ones(samples)*2048)
            
        if not len(self.background) == samples:
            self.background = np.float32(np.ones(samples)*2048)
            
    def dispersion_compensation(self):
        mode = self.ui.ACQMode.currentText()
        device = self.ui.FFTDevice.currentText()
        self.ui.ACQMode.setCurrentText('SingleAline')
        self.ui.FFTDevice.setCurrentText('None')
        ############################# measure an Aline
        self.SingleScan('SingleAline')
        time.sleep(0.5)
        #################################################################### do dispersion compenstation
        Xpixels = self.ui.AlineAVG.value()*self.ui.Xsteps.value()+self.ui.PreClock.value()*2+self.ui.PostClock.value()
        Yrpt = self.ui.BlineAVG.value()
        ALINE = self.data.reshape([Xpixels*Yrpt,self.ui.PostSamples_2.value()])
        ALINE = ALINE[:,self.ui.DelaySamples.value():self.ui.PostSamples_2.value()-self.ui.TrimSamples.value()]
        self.read_background()
        Aline = np.float32(ALINE[Xpixels//2,:])-self.background

        plt.figure()
        plt.plot(Aline)
        plt.title('raw Aline w/o background')
        
        L=len(Aline)
        fR=np.fft.fft(Aline)/L # FFT of interference signal

        plt.figure()
        plt.plot(np.abs(fR[20:]))
        plt.title('Aline w/o compensation')
        
        z = np.argmax(np.abs(fR[50:300]))+50
        low_position = max(10,z-self.ui.PeakWindow.value())
        high_position = min(L//2,z+self.ui.PeakWindow.value())

        fR[0:low_position]=0
        fR[high_position:L-high_position]=0
        fR[L-low_position:]=0
        
        plt.figure()
        plt.plot(np.abs(fR))
        plt.title('Isolated peak')
        
        Aline = np.fft.ifft(fR)

        plt.figure()
        plt.plot(Aline)
        plt.title('Clean spectrum')
        
        hR=hilbert(np.real(Aline))
        hR_phi=np.unwrap(np.angle(hR))
        
        plt.figure()
        plt.plot(np.real(hR))
        plt.plot(np.imag(hR))
        plt.title('Hilbert transformation')
        
        phi_delta=np.linspace(hR_phi[0],hR_phi[L-1],L)
        phi_diff=np.float32(phi_delta-hR_phi)
        ALINE = ALINE*np.exp(1j*phi_diff)
        
        plt.figure()
        plt.plot(phi_delta)
        plt.plot(hR_phi)
        plt.title('Unwrapped phase')
        
        plt.figure()
        plt.plot(phi_diff)
        plt.title('Phase difference')
        # plt.figure()
        message = 'max phase difference is: '+str(np.max(np.abs(phi_diff)))+'\n'
        print(message)
        # self.ui.PrintOut.append(message)
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
            str(current_time.minute)+'-'+\
            str(current_time.second)+\
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
        time.sleep(0.5)
        #######################################################################
        Xpixels = self.ui.AlineAVG.value()*self.ui.Xsteps.value()+self.ui.PreClock.value()*2+self.ui.PostClock.value()
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
    
    def get_surfCurve(self):
        mode = self.ui.ACQMode.currentText()
        device = self.ui.FFTDevice.currentText()
        self.ui.ACQMode.setCurrentText('SingleCscan')
        self.ui.FFTDevice.setCurrentText('GPU')
        self.ui.DSing.setChecked(True)
        ############################# measure an Cscan
        self.SingleScan('SingleCscan')
        while self.GPU2weaverQueue.qsize()<1:
            time.sleep(1)
        cscan =self.GPU2weaverQueue.get()
  
        Zpixels = self.ui.DepthRange.value()
        # get number of X pixels
        Xpixels = self.ui.Xsteps.value()*self.ui.AlineAVG.value()
        if self.Digitizer == 'ART':
            Xpixels = Xpixels + self.ui.PreClock.value()*2 + self.ui.PostClock.value()
        # get number of Y pixels
        Ypixels = self.ui.Ysteps.value()*self.ui.BlineAVG.value()
        # reshape into Ypixels x Xpixels x Zpixels
        cscan = cscan.reshape([Ypixels,Xpixels,Zpixels])
        # trim fly-back pixels
        if self.Digitizer == 'ART':    
            cscan = cscan[:,self.ui.PreClock.value():self.ui.Xsteps.value()*self.ui.AlineAVG.value()+self.ui.PreClock.value()]
            Xpixels = self.ui.Xsteps.value()*self.ui.AlineAVG.value()
        
        Bline = np.float32(np.mean(cscan,0))
        surfCurve = np.zeros([Xpixels])
        import matplotlib.pyplot as plt
        plt.figure()
        plt.imshow(Bline)
        plt.title('Bline for finding surface')
        for xx in range(Xpixels):
            surfCurve[xx] = findchangept(Bline[xx,:],1)
        
        surfCurve = surfCurve - min(surfCurve)
        import matplotlib.pyplot as plt
        plt.figure()
        plt.plot(surfCurve)
        plt.title('surface')
        plt.figure()

        filePath = self.ui.DIR.toPlainText()
        filePath = filePath + "/" + 'surfCurve.bin'
        fp = open(filePath, 'wb')
        np.uint16(surfCurve).tofile(fp)
        fp.close()
        
        self.ui.Surf_DIR.setText(filePath)
        self.ui.ACQMode.setCurrentText(mode)
        self.ui.FFTDevice.setCurrentText(device)
        self.ui.DSing.setChecked(False)
        
        # load surface profile for high res imaging
        if os.path.isfile(self.ui.Surf_DIR.text()):
            self.surfCurve = np.uint16(np.fromfile(self.ui.Surf_DIR.text(), dtype=np.uint16))
            if self.surfCurve.shape[0] != Xpixels:
                self.surfCurve = np.zeros([Xpixels],dtype = np.uint16)
                print('surface data not match FOV setting, using all zeros')
                self.surfCurve = np.zeros([Xpixels],dtype = np.uint16)
        else:
            print('surface data not found, using all zeros')
            self.surfCurve = np.zeros([Xpixels],dtype = np.uint16)
        return 'surface measruement success...'
    