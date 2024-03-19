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
from multiprocessing import Queue
from PyQt5.QtWidgets import QApplication
import PyQt5.QtCore as qc
from mainWindow import MainWindow
from Actions import *
import time
# init global memory for temporary storage of generated raw data
global memoryCount
memoryCount = 2

global Memory
Memory = list(range(memoryCount))

global Digitizer

Digitizer = 'ART8912'

# init all Queues as global variable
# for any queue, you can do queue-in at multiple places, but you can only do queue-out at one place
global AODOQueue # AODO stands for analog output and digital output
global StagebackQueue # stage finish moving report queue
global WeaverQueue # King of all threads, gives command to other threads
global DnSQueue # DnS stands for display and save
global PauseQueue 
global GPUQueue 
global DQueue # D stands for digitizer
global DbackQueue # Dback stands for digitizer respond back, digitizer respond back if data collection is done
global DnSbackQueue # display thread respond back to weaver thread
global StopDQueue # StopD stands for stop digitizer, for stopping digitizer in continuous acquisition
global GPU2weaverQueue

AODOQueue = Queue()
StagebackQueue = Queue()
WeaverQueue = Queue()
DnSQueue = Queue()
PauseQueue = Queue()
GPUQueue = Queue()
DQueue = Queue()
DbackQueue = Queue()
DnSbackQueue = Queue()
StopDQueue = Queue()
GPU2weaverQueue = Queue()

# wrap GPU thread with Queues and Memory
from ThreadGPU import GPUThread
class GPUThread_2(GPUThread):
    def __init__(self, ui):
            super().__init__()
            global Memory
            self.Memory = Memory
            self.ui = ui
            self.queue = GPUQueue
            self.DnSQueue = DnSQueue
            self.Digitizer = Digitizer
            self.GPU2weaverQueue = GPU2weaverQueue
            
# wrap digitzer thread with queues and Memory
if Digitizer == 'ATS9351':
    from ThreadATS9351 import ATS9351
    class Digitizer_2(ATS9351):
        def __init__(self, ui):
            super().__init__()
            global Memory
            self.memoryCount = memoryCount
            self.Memory = Memory
            self.ui = ui
            self.queue = DQueue
            self.DbackQueue = DbackQueue
            self.StopDQueue = StopDQueue
    
    from ThreadWeaver_ATS import WeaverThread
    class WeaverThread_2(WeaverThread):
        def __init__(self, ui):
            super().__init__()
            global Memory
            self.Memory = Memory
            self.ui = ui
            self.queue = WeaverQueue
            self.DnSQueue = DnSQueue
            self.AODOQueue = AODOQueue
            self.StagebackQueue = StagebackQueue
            self.PauseQueue = PauseQueue
            self.StopDQueue = StopDQueue
            self.DbackQueue = DbackQueue
            self.DnSbackQueue = DnSbackQueue
            self.GPUQueue = GPUQueue
            self.DQueue = DQueue
            self.GPU2weaverQueue = GPU2weaverQueue
            
            
elif Digitizer == 'ART8912':
    from ThreadART8912 import ART8912
    class Digitizer_2(ART8912):
        def __init__(self, ui):
            super().__init__()
            global Memory
            self.memoryCount = memoryCount
            self.Memory = Memory
            self.ui = ui
            self.queue = DQueue
            self.DbackQueue = DbackQueue
            self.StopDQueue = StopDQueue

    # since ART8912 is master, AODO is slave,we need a separate king thread to organize them
    from ThreadWeaver_ART import WeaverThread
    class WeaverThread_2(WeaverThread):
        def __init__(self, ui):
            super().__init__()
            global Memory
            self.Memory = Memory
            self.ui = ui
            self.queue = WeaverQueue
            self.DnSQueue = DnSQueue
            self.AODOQueue = AODOQueue
            self.StagebackQueue = StagebackQueue
            self.PauseQueue = PauseQueue
            self.StopDQueue = StopDQueue
            self.DbackQueue = DbackQueue
            self.DnSbackQueue = DnSbackQueue
            self.GPUQueue = GPUQueue
            self.DQueue = DQueue
            self.GPU2weaverQueue = GPU2weaverQueue

# wrap AODO thread with queue
from ThreadAODO import AODOThread
class AODOThread_2(AODOThread):
    def __init__(self, ui):
        super().__init__()
        self.ui = ui
        self.queue = AODOQueue
        self.Digitizer = Digitizer
        self.StagebackQueue = StagebackQueue

# wrap Display and save thread with queue        
from ThreadDnS import DnSThread
class DnSThread_2(DnSThread):
    def __init__(self, ui):
        super().__init__()
        self.ui = ui
        self.queue = DnSQueue
        self.Digitizer = Digitizer
        self.DnSbackQueue = DnSbackQueue
        
# wrap MainWindow object with queues and threads        
class GUI(MainWindow):
    def __init__(self):
        super().__init__()

        self.ui.RunButton.clicked.connect(self.run_task)
        self.ui.PauseButton.clicked.connect(self.Pause_task)
        
        self.ui.CenterGalvo.clicked.connect(self.CenterGalvo)
        
        # change window length for FFT
        self.ui.PostSamples.valueChanged.connect(self.update_Dispersion)
        self.ui.PreSamples.valueChanged.connect(self.update_Dispersion)
        self.ui.PostSamples_2.valueChanged.connect(self.update_Dispersion)
        self.ui.DelaySamples.valueChanged.connect(self.update_Dispersion)
        
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
        self.ui.ZstageTest.clicked.connect(self.ZstageTest)
        self.ui.Gotozero.stateChanged.connect(self.Gotozero)
        self.Init_allThreads()
        
    def Init_allThreads(self):
        self.Weaver_thread = WeaverThread_2(self.ui)
        self.AODO_thread = AODOThread_2(self.ui)
        self.DnS_thread = DnSThread_2(self.ui)
        self.GPU_thread = GPUThread_2(self.ui)
        self.D_thread = Digitizer_2(self.ui)
        
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
        # RptAline and SingleAline is for checking Aline profile, we don't need to capture each Aline, only display 30 Alines per second\
        
        # RptBline and SingleBline will collect each Bline, but FFT will be slow in this mode. To check image quality, recommend using Alazar FFT.
        # To capture and save each Bline, recommend increasing the Bline average, or using Cscan mode but set Y stepsize to 0
        
        # RptCscan is for acquiring Cscan at the same location repeatitively
        
        # SurfScan is for imaging the sample surface
        
        # SurfScan + Slice is for serial sectioning imaging
        
        # Slice is for cut one slice only

        if self.ui.ACQMode.currentText() in ['RptAline','RptBline','RptCscan','SurfScan','SurfScan+Slice']:
            if self.ui.RunButton.isChecked():
                self.ui.RunButton.setText('Stop')
                an_action = WeaverAction(self.ui.ACQMode.currentText())
                WeaverQueue.put(an_action)
            else:
                # time.sleep(0.5)
                self.ui.RunButton.setText('Run')
                self.Stop_task()
                
                # self.CenterGalvo()
        elif self.ui.ACQMode.currentText() in ['SingleAline','SingleBline','SingleCscan']:
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
        
    def ZstageTest(self):
        

        an_action = WeaverAction('ZstageRepeatibility')
        WeaverQueue.put(an_action)
        # wait until weaver done
        

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
            self.ui.statusbar.showMessage('acquisition paused...')
        else:
            PauseQueue.put('unPause')
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
        if not self.ui.RunButton.isChecked():
            an_action = DnSAction('UpdateContrastXY')
            DnSQueue.put(an_action)

    def Update_contrast_XYZ(self):
        if not self.ui.RunButton.isChecked():
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
        
    
    def closeEvent(self, event):
        self.ui.statusbar.showMessage('Exiting all threads')
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

    