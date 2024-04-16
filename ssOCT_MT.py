# -*- coding: utf-8 -*-
"""
Created on Sun Dec 10 20:14:40 2023

@author: Shuaibin Chang
"""

# using QThread of PYQT to do multithreading control of acquiring, processing and saving and synchonize numerous hardwares
# multithreading is more appropriate only when not using PyQt, in other words, not GUI applications
# subclass QThread and overwrite run() with a while loop to wait for Queued actions

# using Queue to initiate hardware actions

# Queue functions:
# maxsize – Number of items allowed in the queue.
# empty() – Return True if the queue is empty, False otherwise.
# full() – Return True if there are maxsize items in the queue. If the queue was initialized with maxsize=0 (the default), then full() never returns True.
# get() – Remove and return an item from the queue. If queue is empty, wait until an item is available.
# get_nowait() – Return an item if one is immediately available, else raise QueueEmpty.
# put(item) – Put an item into the queue. If the queue is full, wait until a free slot is available before adding the item.
# put_nowait(item) – Put an item into the queue without blocking. If no free slot is immediately available, raise QueueFull.
# qsize() – Return the number of items in the queue.

# '__main__' using the main thread, every hardware has its own thread
# GUI input triggers in-queue action to the specified queue

# between threads, using Queue to pass variables, variables gets duplicated in memory when passed as arguments

import sys
import numpy as np
from queue import Queue
from PyQt5.QtWidgets import QApplication
from PyQt5 import QtWidgets as QW
import PyQt5.QtCore as qc
from mainWindow import MainWindow
from Actions import *
from Generaic_functions import LOG
import time
# init global memory for temporary storage of generated raw data
global memoryCount
memoryCount = 3

global Memory
Memory = list(range(memoryCount))

global Digitizer

Digitizer = 'ART8912'

# init all Queues as global variable
# for any queue, you can do queue-in at multiple places, but you can only do queue-out at one place
# global AODOQueue # AODO stands for analog output and digital output
# global StagebackQueue # stage finish moving report queue
# global WeaverQueue # King of all threads, gives command to other threads
# global DnSQueue # DnS stands for display and save
# global PauseQueue 
# global GPUQueue 
# global DQueue # D stands for digitizer
# global DbackQueue # Dback stands for digitizer respond back, digitizer respond back if data collection is done
# global StopDQueue # StopD stands for stop digitizer, for stopping digitizer in continuous acquisition
# global GPU2weaverQueue

AODOQueue = Queue(maxsize = 0)
StagebackQueue = Queue(maxsize = 0)
WeaverQueue = Queue(maxsize = 0)
DnSQueue = Queue(maxsize = 0)
PauseQueue = Queue(maxsize = 0)
GPUQueue = Queue(maxsize = 0)
DQueue = Queue(maxsize = 0)
DbackQueue = Queue(maxsize = 0)
StopDQueue = Queue(maxsize = 0)
GPU2weaverQueue = Queue(maxsize = 0)
     
# wrap digitzer thread with queues and Memory
if Digitizer == 'ATS9351':
    # ATS9351 outputs 16bit data range
    AMPLIFICATION = 1*5
    from ThreadATS9351 import ATS9351
    class Digitizer_2(ATS9351):
        def __init__(self, ui, log):
            super().__init__()
            global Memory
            self.memoryCount = memoryCount
            self.Memory = Memory
            self.ui = ui
            self.queue = DQueue
            self.DbackQueue = DbackQueue
            self.StopDQueue = StopDQueue
            self.log = log
    
    from ThreadWeaver_ATS import WeaverThread
    class WeaverThread_2(WeaverThread):
        def __init__(self, ui, log):
            super().__init__()
            global Memory
            self.Memory = Memory
            self.memoryCount = memoryCount
            self.ui = ui
            self.queue = WeaverQueue
            self.DnSQueue = DnSQueue
            self.AODOQueue = AODOQueue
            self.StagebackQueue = StagebackQueue
            self.PauseQueue = PauseQueue
            self.StopDQueue = StopDQueue
            self.DbackQueue = DbackQueue
            self.GPUQueue = GPUQueue
            self.DQueue = DQueue
            self.GPU2weaverQueue = GPU2weaverQueue
            self.log = log
            
            
elif Digitizer == 'ART8912':
    # ART8912 outputs 12bit data range
    AMPLIFICATION = 16*5
    from ThreadART8912_finiteTrigger import ART8912_finiteTrigger as ART8912
    class Digitizer_2(ART8912):
        def __init__(self, ui, log):
            super().__init__()
            global Memory
            self.memoryCount = memoryCount
            self.Memory = Memory
            self.ui = ui
            self.queue = DQueue
            self.DbackQueue = DbackQueue
            self.StopDQueue = StopDQueue
            self.log = log

    # since ART8912 is master, AODO is slave,we need a separate king thread to organize them
    from ThreadWeaver_ART import WeaverThread
    class WeaverThread_2(WeaverThread):
        def __init__(self, ui, log):
            super().__init__()
            global Memory
            self.Memory = Memory
            self.memoryCount = memoryCount
            self.ui = ui
            self.queue = WeaverQueue
            self.DnSQueue = DnSQueue
            self.AODOQueue = AODOQueue
            self.StagebackQueue = StagebackQueue
            self.PauseQueue = PauseQueue
            self.StopDQueue = StopDQueue
            self.DbackQueue = DbackQueue
            self.GPUQueue = GPUQueue
            self.DQueue = DQueue
            self.GPU2weaverQueue = GPU2weaverQueue
            self.log = log

# wrap GPU thread with Queues and Memory
from ThreadGPU import GPUThread
class GPUThread_2(GPUThread):
    def __init__(self, ui, log):
            super().__init__()
            global Memory
            self.Memory = Memory
            self.ui = ui
            self.queue = GPUQueue
            self.DnSQueue = DnSQueue
            self.Digitizer = Digitizer
            self.GPU2weaverQueue = GPU2weaverQueue
            self.log = log
            self.AMPLIFICATION = AMPLIFICATION
# wrap AODO thread with queue
from ThreadAODO import AODOThread
class AODOThread_2(AODOThread):
    def __init__(self, ui, log):
        super().__init__()
        self.ui = ui
        self.queue = AODOQueue
        self.Digitizer = Digitizer
        self.StagebackQueue = StagebackQueue
        self.log = log

# wrap Display and save thread with queue        
from ThreadDnS import DnSThread
class DnSThread_2(DnSThread):
    def __init__(self, ui, log):
        super().__init__()
        self.ui = ui
        self.queue = DnSQueue
        self.Digitizer = Digitizer
        self.log = log
        
# wrap MainWindow object with queues and threads   
     
class GUI(MainWindow):
    def __init__(self):
        super().__init__()
        # print(dir(self.ui))
        # print(self.ui.__dict__)
        # aa=self.ui.__getattribute__('ACQMode')
        # if type(aa) == QW.QComboBox:
        #     print(1)
        # print(aa.currentText())
        self.log = LOG(self.ui)
        self.ui.RunButton.clicked.connect(self.run_task)
        self.ui.PauseButton.clicked.connect(self.Pause_task)
        
        self.ui.CenterGalvo.clicked.connect(self.CenterGalvo)
        
        # change window length for FFT
        self.ui.PostSamples.valueChanged.connect(self.update_Dispersion)
        self.ui.PreSamples.valueChanged.connect(self.update_Dispersion)
        self.ui.PostSamples_2.valueChanged.connect(self.update_Dispersion)
        self.ui.DelaySamples.valueChanged.connect(self.update_Dispersion)
        self.ui.TrimSamples.valueChanged.connect(self.update_Dispersion)
        
        self.ui.XYmax.valueChanged.connect(self.Update_contrast_XY)
        self.ui.XYmin.valueChanged.connect(self.Update_contrast_XY)
        self.ui.XYZmax.valueChanged.connect(self.Update_contrast_XYZ)
        self.ui.XYZmin.valueChanged.connect(self.Update_contrast_XYZ)
        self.ui.Surfmax.valueChanged.connect(self.Update_contrast_Surf)
        self.ui.Surfmin.valueChanged.connect(self.Update_contrast_Surf)
        
        self.ui.RedoDC.clicked.connect(self.redo_dispersion_compensation)
        self.ui.redoBG.clicked.connect(self.redo_background)
        self.ui.BG_DIR.textChanged.connect(self.update_background)
        self.ui.Disp_DIR.textChanged.connect(self.update_Dispersion)
        self.ui.Xmove2.clicked.connect(self.Xmove2)
        self.ui.Ymove2.clicked.connect(self.Ymove2)
        self.ui.Zmove2.clicked.connect(self.Zmove2)
        self.ui.XUP.clicked.connect(self.XUP)
        self.ui.YUP.clicked.connect(self.YUP)
        self.ui.ZUP.clicked.connect(self.ZUP)
        self.ui.XDOWN.clicked.connect(self.XDOWN)
        self.ui.YDOWN.clicked.connect(self.YDOWN)
        self.ui.ZDOWN.clicked.connect(self.ZDOWN)
        self.ui.InitStageButton.clicked.connect(self.InitStages)
        self.ui.StageUninit.clicked.connect(self.Uninit)
        self.ui.RepTest.clicked.connect(self.RepTest)
        self.ui.RepTest2.clicked.connect(self.RepTest2)
        self.ui.SliceDir.clicked.connect(self.SliceDirection)
        self.ui.VibEnabled.clicked.connect(self.Vibratome)
        self.ui.SliceN.valueChanged.connect(self.change_slice_number)
        # self.ui.Gotozero.stateChanged.connect(self.Gotozero)
        self.Init_allThreads()
        # configure digitizer with inital settings from GUI
        self.ConfigureD()
        
    def Init_allThreads(self):
        self.Weaver_thread = WeaverThread_2(self.ui, self.log)
        self.AODO_thread = AODOThread_2(self.ui, self.log)
        self.DnS_thread = DnSThread_2(self.ui, self.log)
        self.GPU_thread = GPUThread_2(self.ui, self.log)
        self.D_thread = Digitizer_2(self.ui, self.log)
        
        self.D_thread.start()
        self.GPU_thread.start()
        self.Weaver_thread.start()
        self.AODO_thread.start()
        self.DnS_thread.start()
            
    def Stop_allThreads(self):
        exit_element=EXIT()
        WeaverQueue.put(exit_element)
        AODOQueue.put(exit_element)
        DnSQueue.put(exit_element)
        GPUQueue.put(exit_element)
        DQueue.put(exit_element)
        
    def run_task(self):
        while PauseQueue.qsize()>0:
            PauseQueue.get()
        # self.ui.PrintOut.append('Pause Queue inited...')
        # RptAline and SingleAline is for checking Aline profile, we don't need to capture each Aline, only display 30 Alines per second\
        
        # RptBline and SingleBline will collect each Bline, but FFT will be slow in this mode. To check image quality, recommend using Alazar FFT.
        # To capture and save each Bline, recommend increasing the Bline average, or using Cscan mode but set Y stepsize to 0
        
        # RptCscan is for acquiring Cscan at the same location repeatitively
        
        # SurfScan is for imaging the sample surface
        
        # SurfScan + Slice is for serial sectioning imaging
        
        # Slice is for cut one slice only
        
        if self.ui.ACQMode.currentText() in ['RptAline','RptBline','RptCscan','SurfScan','SurfScan+Slice','RptSlice']:
            if self.ui.RunButton.isChecked():
                self.ui.RunButton.setText('Stop')
                
                an_action = WeaverAction(self.ui.ACQMode.currentText())
                WeaverQueue.put(an_action)
            else:
                # time.sleep(0.5)
                self.ui.RunButton.setText('Run')
                self.Stop_task()
                
                # self.CenterGalvo()
        elif self.ui.ACQMode.currentText() in ['SingleAline','SingleBline','SingleCscan','SingleSlice']:
            an_action = WeaverAction(self.ui.ACQMode.currentText())
            WeaverQueue.put(an_action)
            # time.sleep(0.5)
            self.ui.RunButton.setChecked(False)
            self.ui.RunButton.setText('Run')
            # self.CenterGalvo()
        else:
            self.Slice()

    def InitStages(self):
        an_action = AODOAction('Init')
        AODOQueue.put(an_action)
        StagebackQueue.get()
        
    def Uninit(self):
        an_action = AODOAction('Uninit')
        AODOQueue.put(an_action)
        StagebackQueue.get()
        
    def Xmove2(self):
        an_action = AODOAction('Xmove2')
        AODOQueue.put(an_action)
        StagebackQueue.get()
        
    def Ymove2(self):
        an_action = AODOAction('Ymove2')
        AODOQueue.put(an_action)
        StagebackQueue.get()
        
    def Zmove2(self):
        an_action = AODOAction('Zmove2')
        AODOQueue.put(an_action)
        StagebackQueue.get()
        
    def XUP(self):
        an_action = AODOAction('XUP')
        AODOQueue.put(an_action)
        
        StagebackQueue.get()
    def YUP(self):
        an_action = AODOAction('YUP')
        AODOQueue.put(an_action)
        StagebackQueue.get()
    def ZUP(self):
        an_action = AODOAction('ZUP')
        AODOQueue.put(an_action)
        StagebackQueue.get()
        
    def XDOWN(self):
        an_action = AODOAction('XDOWN')
        AODOQueue.put(an_action)
        StagebackQueue.get()
    def YDOWN(self):
        an_action = AODOAction('YDOWN')
        AODOQueue.put(an_action)
        StagebackQueue.get()
    def ZDOWN(self):
        an_action = AODOAction('ZDOWN')
        AODOQueue.put(an_action)
        StagebackQueue.get()
        
    def Vibratome(self):
        if self.ui.VibEnabled.isChecked():
            self.ui.VibEnabled.setText('Stop Vibratome')
            an_action = AODOAction('startVibratome')
            AODOQueue.put(an_action)
            StagebackQueue.get()
        else:
            self.ui.VibEnabled.setText('Start Vibratome')
            an_action = AODOAction('stopVibratome')
            AODOQueue.put(an_action)
            StagebackQueue.get()
        
    def SliceDirection(self):
        if self.ui.SliceDir.isChecked():
            self.ui.SliceDir.setText('Backward')
        else:
            self.ui.SliceDir.setText('Forward')
            
    def change_slice_number(self):
        an_action = DnSAction('change_slice_number')
        DnSQueue.put(an_action)
        
    def RepTest(self):
        if self.ui.ZstageTest.isChecked():
            an_action = WeaverAction('ZstageRepeatibility')
            WeaverQueue.put(an_action)
        # wait until weaver done
        
    def RepTest2(self):
        if self.ui.ZstageTest2.isChecked():
            an_action = WeaverAction('ZstageRepeatibility2')
            WeaverQueue.put(an_action)

    def Gotozero(self):
        if self.ui.Gotozero.isChecked():
            an_action = WeaverAction('Gotozero')
            WeaverQueue.put(an_action)

        
    def CenterGalvo(self):
        an_action = AODOAction('centergalvo')
        AODOQueue.put(an_action)
        
    def Pause_task(self):
        if self.ui.PauseButton.isChecked():
            PauseQueue.put('Pause')
            self.ui.PauseButton.setText('Unpause')
            self.ui.statusbar.showMessage('acquisition paused...')
        else:
            PauseQueue.put('unPause')
            self.ui.PauseButton.setText('Pause')
            self.ui.statusbar.showMessage('acquisition resumed...')
      
    def Stop_task(self):
        PauseQueue.put('Stop')
        self.ui.statusbar.showMessage('acquisition stopped...')
        
    def update_Dispersion(self):
        an_action = GPUAction('update_Dispersion')
        GPUQueue.put(an_action)
        
    def update_background(self):
        an_action = GPUAction('update_background')
        GPUQueue.put(an_action)
        
    def Update_contrast_XY(self):
        # if not self.ui.RunButton.isChecked():
            an_action = DnSAction('UpdateContrastXY')
            DnSQueue.put(an_action)

    def Update_contrast_XYZ(self):
        # if not self.ui.RunButton.isChecked():
            an_action = DnSAction('UpdateContrastXYZ')
            DnSQueue.put(an_action)
            
    def Update_contrast_Surf(self):
        an_action = DnSAction('UpdateContrastSurf')
        DnSQueue.put(an_action)
        
    def redo_dispersion_compensation(self):
        an_action = WeaverAction('dispersion_compensation')
        WeaverQueue.put(an_action)
        
            
    def redo_background(self):
        an_action = WeaverAction('get_background')
        WeaverQueue.put(an_action)
        
    def ConfigureD(self):
        an_action = DAction('ConfigureBoard')
        DQueue.put(an_action)
        
    def UninitBoard(self):
        an_action = DAction('UninitBoard')
        DQueue.put(an_action)
    
    def closeEvent(self, event):
        print('Exiting all threads')
        self.Stop_allThreads()
        settings = qc.QSettings("config.ini", qc.QSettings.IniFormat)
        self.save_settings(settings )
        if self.DnS_thread.isFinished:
            event.accept()
        else:
            event.ignore()
        

                

if __name__ == '__main__':
    app = QApplication(sys.argv)
    example = GUI()
    example.show()
    sys.exit(app.exec_())

    