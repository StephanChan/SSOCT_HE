# -*- coding: utf-8 -*-
"""
Created on Tue Jan  2 14:04:49 2024

@author: admin
"""

from __future__ import division
import ctypes
import numpy as np
import os
import signal
import sys
import time
global Memory
Memory = list(range(2))
from matplotlib import pyplot as plt
# sys.path.append(os.path.join(os.path.dirname(__file__), '../..', 'Library'))
import atsapi as ats

class ATS9350():
    def __init__(self):
        super().__init__()
        self.board = ats.Board(systemId = 1, boardId = 1)
        self.samplesPerSec = 250000000.0
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
        
        self.board.setCaptureClock(ats.INTERNAL_CLOCK,
                              ats.SAMPLE_RATE_250MSPS,
                              ats.CLOCK_EDGE_RISING,
                              0)
        
        # TODO: Select channel A input parameters as required.
        self.board.inputControlEx(ats.CHANNEL_A,
                             ats.DC_COUPLING,
                             ats.INPUT_RANGE_PM_400_MV,
                             ats.IMPEDANCE_50_OHM)
        
        # TODO: Select channel A bandwidth limit as required.
        self.board.setBWLimit(ats.CHANNEL_A, 0)
        
        
        # TODO: Select channel B input parameters as required.
        self.board.inputControlEx(ats.CHANNEL_B,
                             ats.DC_COUPLING,
                             ats.INPUT_RANGE_PM_400_MV,
                             ats.IMPEDANCE_50_OHM)
        
        # TODO: Select channel B bandwidth limit as required.
        self.board.setBWLimit(ats.CHANNEL_B, 0)
        
        # TODO: Select trigger inputs and levels as required.
        self.board.setTriggerOperation(ats.TRIG_ENGINE_OP_J,
                                  ats.TRIG_ENGINE_J,
                                  ats.TRIG_EXTERNAL,
                                  ats.TRIGGER_SLOPE_POSITIVE,
                                  150,
                                  ats.TRIG_ENGINE_K,
                                  ats.TRIG_DISABLE,
                                  ats.TRIGGER_SLOPE_POSITIVE,
                                  128)
    
        # TODO: Select external trigger parameters as required.
        self.board.setExternalTrigger(ats.DC_COUPLING,
                                 ats.ETR_TTL)
    
        # TODO: Set trigger delay as required.
        triggerDelay_sec = 0
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
        # self.board.configureAuxIO(ats.AUX_IN_TRIGGER_ENABLE,
        #                      ats.TRIGGER_SLOPE_POSITIVE)
        self.board.configureAuxIO(ats.AUX_IN_TRIGGER_ENABLE,
                              ats.TRIGGER_SLOPE_POSITIVE)
    
        # No pre-trigger samples in NPT mode
        self.preTriggerSamples = 0
    
        # TODO: Select the number of samples per record.
        self.postTriggerSamples = 1024
    
        # TODO: Select the number of records per DMA buffer.
        self.recordsPerBuffer = 3000
    
        # TODO: Select the number of buffers per acquisition.
        self.buffersPerAcquisition = 100
        
        # TODO: Select the active channels.
        self.channels = ats.CHANNEL_B# | ats.CHANNEL_B
        self.channelCount = 1
        # for c in ats.channels:
        #     self.channelCount += (c & self.channels == c)
        # print(self.channelCount)
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
        self.samplesPerBuffer = self.samplesPerRecord * self.recordsPerBuffer * self.channelCount
        # print(self.bytesPerBuffer)
    
        # Init Cscan memory buffers for temporary copying Blines
        self.memoryCount = 2
        global Memory
        for ii in range(self.memoryCount):
                Memory[ii]=np.zeros([self.buffersPerAcquisition,self.samplesPerBuffer], dtype = np.uint16)
           
        # print(Memory[0].shape)
    
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

    def AcquireData(self):
        
        global Memory
        self.MemoryLoc = 0
        

        recordsPerAcquisition = self.recordsPerBuffer * self.buffersPerAcquisition
        # Configure the board to make an NPT AutoDMA acquisition
        self.board.beforeAsyncRead(self.channels,
                              -self.preTriggerSamples,
                              self.samplesPerRecord,
                              self.recordsPerBuffer,
                              # 0x7FFFFFFF,
                               recordsPerAcquisition,
                              ats.ADMA_EXTERNAL_STARTCAPTURE | ats.ADMA_NPT)
        # Post DMA buffers to board
        for buffer in self.buffers:
            self.board.postAsyncBuffer(buffer.addr, buffer.size_bytes)
        self.board.startCapture() # Start the acquisition
        # print("Capturing %d buffers. Press <enter> to abort" %
              # self.buffersPerAcquisition)


        buffersCompleted = 0
        # bytesTransferred = 0
        # TODO: how to pause and stop acquisition for continuous mode?
        while (buffersCompleted < self.buffersPerAcquisition): # and not ats.enter_pressed()):
               
            # Wait for the buffer at the head of the list of available
            # buffers to be filled by the board.
            buffer = self.buffers[buffersCompleted % self.bufferCount]
            # print('board waiting...\n')
            try:
                self.board.waitAsyncBufferComplete(buffer.addr, timeout_ms=5000) 
            except Exception as error:
                # TODO: if timeout, break this inner while loop
                print(error)
                break

            # bytesTransferred += buffer.size_bytes

            #TODO: select which way to do FFT
            # 1. run GPU FFT for each buffer, one buffer can take 100ms to acquire
            # --inplausible, processing takes longer time, need at least 200k Alines to be twice speed of acquisition
            # 2. copy each buffer to a global memory, queue in memory address, when memory is filled up, perform FFT on a separate thread
            # -- doable, copy is fast, queue in/out memory address is fast, reading global memory is slow, but still twice faster than acquisition
            # 3. copy each buffer to a local memory, queue in local memory, queue out local memory on a separate thread and perform FFT
            # -- queue in/out is very slow, not surprising
            Memory[self.MemoryLoc][buffersCompleted][:] = buffer.buffer
            buffersCompleted += 1
            print(buffersCompleted)
            # Add the buffer to the end of the list of available buffers.
            self.board.postAsyncBuffer(buffer.addr, buffer.size_bytes)

        self.MemoryLoc = (self.MemoryLoc+1) % 2
            
        self.board.abortAsyncRead()

if __name__ == "__main__":

    example = ATS9350()
    example.ConfigureBoard()
    example.AcquireData()
    example.AcquireData()