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
sys.path.append('c:\\alazartech\\ats-sdk\\7.2.3\\samples_python\\ats9350\\npt\\../..\\Library')
import atsapi as ats
from Actions import Board2ACQAction
import traceback

class ATS9350(QThread):
    def __init__(self):
        super().__init__()
        # self.ui = ui
        # self.queue = BoardQueue

        # self.Board2ACQQueue = Board2ACQQueue
        self.board = ats.Board()
        

        self.test_message = 'Board thread successfully exited'

        
    def run(self):
        if self.ui.ClockFreq.currentText() == '500MHz':
            self.samplesPerSec = 500000000.0
        elif self.ui.ClockFreq.currentText() == '250MHz':
            self.samplesPerSec = 250000000.0
        elif self.ui.ClockFreq.currentText() == '125MHz':
            self.samplesPerSec = 125000000.0
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
                    self.ui.statusbar.showMessage('Board thread is doing something invalid: '+self.item.action)
            except Exception as error:
                print("\nAn error occurred:", error,' skip the Board action\n')
                print(traceback.format_exc())
            self.item = self.queue.get()
        print(self.test_message)
            
    # Configures a board for acquisition
    def ConfigureBoard(self):
        # TODO: Select clock parameters as required to generate this
        # sample rate
        #
        # For example: if samplesPerSec is 100e6 (100 MS/s), then you can
        # either:
        #  - select clock source INTERNAL_CLOCK and sample rate
        #    SAMPLE_RATE_100MSPS
        #  - or select clock source FAST_EXTERNAL_CLOCK, sample rate
        #    SAMPLE_RATE_USER_DEF, and connect a 100MHz signal to the
        #    EXT CLK BNC connector
        if self.ui.ClockFreq.currentText() == '500MHz':
            SAMPLE_RATE = ats.SAMPLE_RATE_500MSPS
        elif self.ui.ClockFreq.currentText() == '250MHz':
            SAMPLE_RATE = ats.SAMPLE_RATE_250MSPS
        elif self.ui.ClockFreq.currentText() == '125MHz':
            SAMPLE_RATE = ats.SAMPLE_RATE_125MSPS
        
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
        if self.ui.ACQMode.currentText() in ['RptAline','SingleAline']:
            self.recordsPerBuffer = 3000
        else:
            self.recordsPerBuffer = self.ui.Xsteps.value() * self.ui.AlineAVG.value()
    
        # TODO: Select the number of buffers per acquisition.
        # how many Blines per Acquisition
        if self.ui.ACQMode.currentText() in ['RptAline','SingleAline']:
            self.buffersPerAcquisition = self.ui.BlineAVG.value()
        elif self.ui.ACQMode.currentText() in ['RptBline','SingleBline']:
            self.buffersPerAcquisition = self.ui.BlineAVG.value()
        elif self.ui.ACQMode.currentText() in ['RptCscan','SingleCscan', 'SurfScan','SurfScan+Slice']:
            self.buffersPerAcquisition = self.ui.Ysteps.value() * self.ui.BlineAVG.value()
        
        # TODO: Select the active channels.
        self.channels = ats.CHANNEL_A | ats.CHANNEL_B
        self.channelCount = 0
        for c in ats.channels:
            self.channelCount += (c & self.channels == c)
    
        # TODO: Should data be saved to file?
        # saveData = False
        # dataFile = None
        # if saveData:
        #     dataFile = open(os.path.join(os.path.dirname(__file__),
                                         # "data.bin"), 'wb')
    
        # Compute the number of bytes per record and per buffer
        memorySize_samples, bitsPerSample = self.board.getChannelInfo()
        bytesPerSample = (bitsPerSample.value + 7) // 8
        self.samplesPerRecord = self.preTriggerSamples + self.postTriggerSamples
        self.bytesPerRecord = bytesPerSample * self.samplesPerRecord
        self.bytesPerBuffer = self.bytesPerRecord * self.recordsPerBuffer * self.channelCount
    
        # Init Cscan memory buffers for temporary copying Blines
        self.memoryCount = 2
        for ii in range(self.memoryCount):
            self.Memory[ii]=np.zeros([self.buffersPerAcquisition,self.bytesPerBuffer], dtype = np.uint16)
            
        self.MemoryLoc = 0
        # Allocate DMA buffers
    
        self.sample_type = ctypes.c_uint8
        if bytesPerSample > 1:
            self.sample_type = ctypes.c_uint16
            
        # TODO: Select number of DMA buffers to allocate
        self.bufferCount = 4
        
        self.buffers = []
        for i in range(self.bufferCount):
            self.buffers.append(ats.DMABuffer(self.board.handle, self.sample_type, self.bytesPerBuffer))
        
        # Set the record size
        self.board.setRecordSize(self.preTriggerSamples, self.postTriggerSamples)
    
        recordsPerAcquisition = self.recordsPerBuffer * self.buffersPerAcquisition
    
        # Configure the board to make an NPT AutoDMA acquisition
        self.board.beforeAsyncRead(self.channels,
                              -self.preTriggerSamples,
                              self.samplesPerRecord,
                              self.recordsPerBuffer,
                              recordsPerAcquisition,
                              ats.ADMA_EXTERNAL_STARTCAPTURE | ats.ADMA_NPT)
        
    
    
        # Post DMA buffers to board
        for buffer in self.buffers:
            self.board.postAsyncBuffer(buffer.addr, buffer.size_bytes)
    
        self.NAcquisitions = 1
    
    def StartAcquire(self):
        self.board.startCapture() # Start the acquisition
        


        buffersCompleted = 0
        # bytesTransferred = 0
        nacqusition = 0
        # TODO: how to pause and stop acquisition for continuous mode?
        while nacqusition < self.NAcquisitions:
            while (buffersCompleted < self.buffersPerAcquisition): # and not ats.enter_pressed()):
                   
                # Wait for the buffer at the head of the list of available
                # buffers to be filled by the board.
                buffer = self.buffers[buffersCompleted % len(self.buffers)]
                try:
                    self.board.waitAsyncBufferComplete(buffer.addr, timeout_ms=200) 
                except:
                    # TODO: if timeout, break this inner while loop
                    break
                

                
                # bytesTransferred += buffer.size_bytes
    
                #TODO: select which way to do FFT
                # 1. run GPU FFT for each buffer, one buffer can take 100ms to acquire
                # --inplausible, processing takes longer time, need at least 200k Alines to be twice speed of acquisition
                # 2. copy each buffer to a memory location, queue in memory location to a thread, then perform FFT on one memory for a time
                # -- copy is fast, queue in is negligible, queue out is slow, only twice faster than acquisition
                # 3. queue in buffer to a different thread, when memory location is filled up, run GPU FFT
                # -- slow, not surprising
    
                self.Memory[self.MemoryLoc][buffersCompleted][:] = buffer.buffer
                buffersCompleted += 1
                # Add the buffer to the end of the list of available buffers.
                self.board.postAsyncBuffer(buffer.addr, buffer.size_bytes)
            
            if buffersCompleted == self.buffersPerAcquisition:
                an_action = Board2ACQAction(self.MemoryLoc)
                self.Board2ACQQueue.put(an_action)
                nacqusition+=1 
                self.MemoryLoc = (self.MemoryLoc+1) % 2
            else:
                self.board.abortAsyncRead()
                break
            
            
    def StopAcquire(self):
        self.board.abortAsyncRead()
            
    