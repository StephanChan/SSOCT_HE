# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 16:46:01 2023

@author: admin
"""
# Save thread class handles all saving-related actions
from PyQt5.QtCore import  QThread
import time
import ctypes
import sys
import numpy as np
global SIM
SIM = False


try:
    sys.path.append('c:\\alazartech\\ats-sdk\\7.2.3\\samples_python\\ats9350\\npt\\../..\\Library')
    import atsapi as ats
except:
    ats = None
    SIM = True
from Actions import DbackAction
import traceback

class ATS9351(QThread):
    def __init__(self):
        super().__init__()
        self.MemoryLoc = 0
        if not SIM:
            self.board = ats.Board()
        self.exit_message = 'Digitizer thread successfully exited'

        
    def run(self):
        self.QueueOut()
        
    def QueueOut(self):
        self.item = self.queue.get()
        while self.item.action != 'exit':
            try:
                if self.item.action == 'ConfigureBoard':
                    self.ConfigureBoard()
                elif self.item.action == 'StartAcquire':
                    self.StartAcquire()
                elif self.item.action == 'StopAcquire':
                    self.StopAcquire()
                    
                else:
                    self.ui.statusbar.showMessage('Digitizer thread is doing something invalid: '+self.item.action)
            except Exception as error:
                print("\nAn error occurred:", error,' skip the Digitizer action\n')
                print(traceback.format_exc())
            self.item = self.queue.get()
        print(self.exit_message)
            
    # Configures a board for acquisition
            
    def ConfigureBoard(self):
        if self.ui.ClockFreq.currentText() == '500MHz':
            SAMPLE_RATE = ats.SAMPLE_RATE_500MSPS
            self.samplesPerSec = 500000000.0
        elif self.ui.ClockFreq.currentText() == '250MHz':
            SAMPLE_RATE = ats.SAMPLE_RATE_250MSPS
            self.samplesPerSec = 250000000.0
        elif self.ui.ClockFreq.currentText() == '125MHz':
            SAMPLE_RATE = ats.SAMPLE_RATE_125MSPS
            self.samplesPerSec = 125000000.0
        
        if self.ui.ClockSource.currentText() == 'Internal Clock':
            CLOCK_SOURCE = ats.INTERNAL_CLOCK
        elif self.ui.ClockSource.currentText() == 'External Clock':
            CLOCK_SOURCE = ats.EXTERNAL_CLOCK
            
        self.board.setCaptureClock(CLOCK_SOURCE,
                              SAMPLE_RATE,
                              ats.CLOCK_EDGE_RISING,
                              0)
        
        # TODO: Select channel A input parameters as required.
        if self.ui.AInputRange.currentText() == '2V':
            ARANGE = ats.INPUT_RANGE_PM_2_V
        elif self.ui.AInputRange.currentText() == '1V':
            ARANGE = ats.INPUT_RANGE_PM_1_V
        elif self.ui.AInputRange.currentText() == '400mV':
            ARANGE = ats.INPUT_RANGE_PM_400_MV
        elif self.ui.AInputRange.currentText() == '200mV':
            ARANGE = ats.INPUT_RANGE_PM_200_MV
        elif self.ui.AInputRange.currentText() == '100mV':
            ARANGE = ats.INPUT_RANGE_PM_100_MV
            
            
        self.board.inputControlEx(ats.CHANNEL_A,
                             ats.DC_COUPLING,
                             ARANGE,
                             ats.IMPEDANCE_50_OHM)
        
        # TODO: Select channel A bandwidth limit as required.
        self.board.setBWLimit(ats.CHANNEL_A, 0)
        
        
        # TODO: Select channel B input parameters as required.
        if self.ui.BInputRange.currentText() == '2V':
            BRANGE = ats.INPUT_RANGE_PM_2_V
        elif self.ui.BInputRange.currentText() == '1V':
            BRANGE = ats.INPUT_RANGE_PM_1_V
        elif self.ui.BInputRange.currentText() == '400mV':
            BRANGE = ats.INPUT_RANGE_PM_400_MV
        elif self.ui.BInputRange.currentText() == '200mV':
            BRANGE = ats.INPUT_RANGE_PM_200_MV
        elif self.ui.BInputRange.currentText() == '100mV':
            BRANGE = ats.INPUT_RANGE_PM_100_MV
            
        self.board.inputControlEx(ats.CHANNEL_B,
                             ats.DC_COUPLING,
                             BRANGE,
                             ats.IMPEDANCE_50_OHM)
        
        # TODO: Select channel B bandwidth limit as required.
        self.board.setBWLimit(ats.CHANNEL_B, 0)
        
        # TODO: Select trigger inputs and levels as required.
        if self.ui.JEdge.currentText() == 'Rising':
            JEDGE = ats.TRIGGER_SLOPE_POSITIVE
        else:
            JEDGE = ats.TRIGGER_SLOPE_NEGATIVE
            
        if self.ui.KEdge.currentText() == 'Rising':
            KEDGE = ats.TRIGGER_SLOPE_POSITIVE
        else:
            KEDGE = ats.TRIGGER_SLOPE_NEGATIVE
            
        self.board.setTriggerOperation(ats.TRIG_ENGINE_OP_J,
                                  ats.TRIG_ENGINE_J,
                                  ats.TRIG_EXTERNAL,
                                  JEDGE,
                                  self.ui.JLevel.value(),
                                  ats.TRIG_ENGINE_K,
                                  ats.TRIG_DISABLE,
                                  KEDGE,
                                  self.ui.KLevel.value())
    
        # TODO: Select external trigger parameters as required.
        
        if self.ui.TriggerCoupling.currentText() == 'DC coupling':
            TRIGGERCOUPLING = ats.DC_COUPLING
        else:
            TRIGGERCOUPLING = ats.AC_COUPLING
        
        if self.ui.TriggerType.currentText() == 'TTL':
            TRIGGERTYPE = ats.ETR_TTL
        elif self.ui.TriggerType.currentText() == '5V':
            TRIGGERTYPE = ats.ETR_5V
        elif self.ui.TriggerType.currentText() == '1V':
            TRIGGERTYPE = ats.ETR_1V
            
        self.board.setExternalTrigger(TRIGGERCOUPLING,
                                 TRIGGERTYPE)
    
        # TODO: Set trigger delay as required.
        triggerDelay_sec = self.ui.TriggerDelay.value()
        triggerDelay_samples = int(triggerDelay_sec * self.samplesPerSec + 0.5)
        self.board.setTriggerDelay(triggerDelay_samples)
    
        # TODO: Set trigger timeout as required.
        #
        # NOTE: The board will wait for a for this amount of time for a
        # trigger event.  If a trigger event does not arrive, then the
        # board will automatically trigger. Set the trigger timeout value
        # to 0 to force the board to wait forever for a trigger event.
        #
        # IMPORTANT: The trigger timeout value should be set to zero after
        # appropriate trigger parameters have been determined, otherwise
        # the board may trigger if the timeout interval expires before a
        # hardware trigger event arrives.
        triggerTimeout_sec = 0
        triggerTimeout_clocks = int(triggerTimeout_sec / 10e-6 + 0.5)
        self.board.setTriggerTimeOut(triggerTimeout_clocks)
    
        # Configure AUX I/O connector as required
        if self.ui.AUXIO.currentText() == 'IN_TRIGGER_ENABLE':
            AUXIO = ats.AUX_IN_TRIGGER_ENABLE
        elif self.ui.AUXIO.currentText() == 'OUT_TRIGGER':
            AUXIO = ats.AUX_OUT_TRIGGER
        elif self.ui.AUXIO.currentText() == 'OUT_PACER':
            AUXIO = ats.AUX_OUT_PACER
        elif self.ui.AUXIO.currentText() == 'IN_AUXILIARY':
            AUXIO = ats.AUX_IN_AUXILIARY
        elif self.ui.AUXIO.currentText() == 'OUT_SERIAL_DATA':
            AUXIO = ats.OUT_SERIAL_DATA
            
        if self.ui.AUXEDGE.currentText() == 'Rising':
            AUXEDGE = ats.TRIGGER_SLOPE_POSITIVE
        else:
            AUXEDGE = ats.TRIGGER_SLOPE_NEGATIVE
            
        self.board.configureAuxIO(AUXIO,
                             AUXEDGE)
    
        # No pre-trigger samples in NPT mode
        self.preTriggerSamples = self.ui.PreSamples.value()
    
        # TODO: Select the number of samples per record.
        self.postTriggerSamples = self.ui.PostSamples.value()
    
        # TODO: Select the number of records per DMA buffer.
        # how many X pixels in one Bline
        self.AlinesPerBline = self.ui.AlineAVG.value()*self.ui.Xsteps.value()+self.ui.PreClock.value()*2+self.ui.PostClock.value()
        if self.ui.ACQMode.currentText() in ['SingleBline', 'SingleAline','RptBline', 'RptAline']:
            self.triggerPerBline = self.ui.BlineAVG.value() * self.AlinesPerBline
            self.BlinesPerAcquisition = 1
        elif self.ui.ACQMode.currentText() in ['SingleCscan', 'Mosaic','Mosaic+Cut']:
            self.triggerPerBline = self.ui.BlineAVG.value() * self.AlinesPerBline
            self.BlinesPerAcquisition = self.ui.Ysteps.value()

        # print(self.buffersPerAcquisition)
        # TODO: Select the active channels.
        # self.channels = ats.CHANNEL_A | ats.CHANNEL_B
        if self.ui.Aenable.currentText() == 'Enable':
            if self.ui.Benable.currentText() == 'Enable':
                self.channels = ats.CHANNEL_A | ats.CHANNEL_B # 3
                self.channelCount = 2
            else:
                self.channels = ats.CHANNEL_A # 1
                self.channelCount = 1
        elif self.ui.Benable.currentText() == 'Enable':
            self.channels = ats.CHANNEL_B # 2
            self.channelCount = 1
    
        # Compute the number of bytes per record and per buffer
        memorySize_samples, bitsPerSample = self.board.getChannelInfo()
        bytesPerSample = (bitsPerSample.value + 7) // 8
        samplesPerAline = self.preTriggerSamples + self.postTriggerSamples                            # Record is an Aline
        bytesPerAline = bytesPerSample * samplesPerAline                                        # 
        bytesPerBline = bytesPerAline * self.triggerPerBline * self.channelCount               # Buffer is a Bline
        samplesPerBline = samplesPerAline * self.triggerPerBline * self.channelCount
        # print(self.samplesPerBuffer)
        # Init Cscan memory buffers for temporary copying Blines

        # Allocate DMA buffers
    
        self.sample_type = ctypes.c_uint8
        if bytesPerSample > 1:
            self.sample_type = ctypes.c_uint16
            
        # TODO: Select number of DMA buffers to allocate
        self.BlineBufferCount = 4
        
        self.BlineBuffers = []
        for i in range(self.BlineBufferCount):
            self.BlineBuffers.append(ats.DMABuffer(self.board.handle, self.sample_type, bytesPerBline))
        # print(self.bytesPerBuffer)
        # Set the record size
        self.board.setRecordSize(self.preTriggerSamples, self.postTriggerSamples)
    
        # Post DMA buffers to board
        for buffer in self.BlineBuffers:
            self.board.postAsyncBuffer(buffer.addr, buffer.size_bytes)
    
        # Configure the board to make an NPT AutoDMA acquisition
        self.board.beforeAsyncRead(self.channels,
                              -self.preTriggerSamples,
                              samplesPerAline,
                              self.triggerPerBline * self.channelCount,
                              self.triggerPerBline * self.channelCount * self.BlinesPerAcquisition,
                              ats.ADMA_EXTERNAL_STARTCAPTURE | ats.ADMA_NPT)
        
        
    def StartAcquire(self):
                                                                                                           # Acquisition is a Bline or Cscan
        self.board.startCapture() # Start the acquisition
        BlinesCompleted = 0
        # an_action = DbackAction(self.MemoryLoc)
        # self.DbackQueue.put(an_action)
        # print('start board', self.buffersPerAcquisition)
        while BlinesCompleted < self.BlinesPerAcquisition:
            buffer = self.BlineBuffers[BlinesCompleted % self.BlineBufferCount]
            try:
                self.board.waitAsyncBufferComplete(buffer.addr, timeout_ms=1000) 
            except Exception as error:
                # TODO: if timeout, break this inner while loop
                print('Blines collected: ', BlinesCompleted, \
                      'Blines configured: ', self.buffersPerAcquisition, \
                      '\n', error, '\nstopping acquisition for Digitizer\n')
                break
            
            # bytesTransferred += buffer.size_bytes
            
            self.Memory[self.MemoryLoc][BlinesCompleted][:] = buffer.buffer
            BlinesCompleted += 1
            # print(buffersCompleted, NACQ)
            # print(buffersCompleted)
            # Add the buffer to the end of the list of available buffers.
            self.board.postAsyncBuffer(buffer.addr, buffer.size_bytes)
            
        an_action = DbackAction(self.MemoryLoc)
        self.DbackQueue.put(an_action)
        self.MemoryLoc = (self.MemoryLoc+1) % self.memoryCount
        
        self.board.abortAsyncRead()
            
            
    def StopAcquire(self):
        self.board.abortAsyncRead()
            
