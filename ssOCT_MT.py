
# -*- coding: utf-8 -*-
"""
Created on Sun Dec 10 20:14:40 2023

@author: Shuaibin Chang
"""
############################################################################################################ SOFTWARE STRUCTURE
# using QThread of PYQT to do multi-threading control of data acquisition, scanning, data processing, display&saving
# using Queue to organize threads
# spectral domain data are stored in global memory, and memory location (pointers) are shared between threads using Queue
############################################################################################################ HARDWARE STRUCTURE
# using swept source Aline trigger as trigger for digitizer, clock source can be external k-clock or internal clock 
# using swept source Aline trigger as clock for Galvo&stage board, using digitizer output trigger as trigger for Galvo&stage board
# scanning regime: X galvo scan in X dimension, Y stage scan in Y dimension. 
# Stages are controlled with a single DIRECTIONAL digital signal (non-buffered) and an array of STEP digital signal (buffered)

# Queue functions:
# maxsize – Number of items allowed in the queue.
# empty() – Return True if the queue is empty, False otherwise.
# full() – Return True if there are maxsize items in the queue. If the queue was initialized with maxsize=0 (the default), then full() never returns True.
# get() – Remove and return an item from the queue. If queue is empty, wait until an item is available.
# get_nowait() – Return an item if one is immediately available, else raise QueueEmpty.
# put(item) – Put an item into the queue. If the queue is full, wait until a free slot is available before adding the item.
# put_nowait(item) – Put an item into the queue without blocking. If no free slot is immediately available, raise QueueFull.
# qsize() – Return the number of items in the queue.

import sys
import numpy as np
from queue import Queue
from PyQt5.QtWidgets import QApplication
from Dialogs import BlineDialog, StageDialog
from PyQt5 import QtWidgets as QW
import PyQt5.QtCore as qc
from mainWindow import MainWindow
from Actions import *
from Generaic_functions import LOG
import time
# init global memory for temporary storage of generated raw data, make it more than 2 for parallel acquisition and processing
global memoryCount
memoryCount = 5

global Memory
Memory = list(range(memoryCount))

####################### select which digitizer to use, ART or Alazar
global Digitizer
Digitizer = 'ART'

# simulation switch, set it to be True for simulation
global SIM
SIM = False
# 3D visualization switch, set it to be True for mayavi 3D visulization (may need debug, haven't used it for a while)
global use_maya
use_maya = False

# Combine threads together for specific functionality, such as Mosaic scan, that is the so-called "weaver"
WeaverQueue = Queue(maxsize = 0)
# Queue for scanning thread
AODOQueue = Queue(maxsize = 0)
# Queue for scanning thread report back to weaver
StagebackQueue = Queue(maxsize = 0)
# Queue for display and saving thread
DnSQueue = Queue(maxsize = 0)
# Queue for FFT thread
GPUQueue = Queue(maxsize = 0)
# Queue for FFT thread report back to weaver
GPU2weaverQueue = Queue(maxsize = 0)
# Queue for digitizer thread
DQueue = Queue(maxsize = 0)
# Queue for digitizer report back to weaver
DbackQueue = Queue(maxsize = 0)
# Queue for pausing or stopping a task
PauseQueue = Queue(maxsize = 0)  

        
# wrap digitzer thread with global queues and Memory and ui and log function
if Digitizer == 'Alazar':
    # ATS9351 outputs 16bit data range
    AMPLIFICATION = 1*5
    from ThreadATS9351_finiteTrigger import ATS9351
    class Digitizer_2(ATS9351):
        def __init__(self, ui, log):
            super().__init__()
            global Memory
            self.memoryCount = memoryCount
            self.Memory = Memory
            self.ui = ui
            self.queue = DQueue
            self.DbackQueue = DbackQueue
            self.log = log
            self.SIM = SIM    
            
elif Digitizer == 'ART':
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
            self.log = log
            self.SIM = SIM

from ThreadWeaver import WeaverThread
class WeaverThread_2(WeaverThread):
    def __init__(self, ui, log):
        super().__init__()
        global Memory
        self.Memory = Memory
        self.memoryCount = memoryCount
        self.ui = ui
        self.Digitizer = Digitizer
        self.queue = WeaverQueue
        self.DnSQueue = DnSQueue
        self.AODOQueue = AODOQueue
        self.StagebackQueue = StagebackQueue
        self.PauseQueue = PauseQueue
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
            self.SIM = SIM
            self.AMPLIFICATION = AMPLIFICATION
            
# wrap Galvo&Stage control thread with queues
from ThreadAODO_150mm import AODOThread
class AODOThread_2(AODOThread):
    def __init__(self, ui, log):
        super().__init__()
        self.ui = ui
        self.queue = AODOQueue
        self.Digitizer = Digitizer
        self.StagebackQueue = StagebackQueue
        self.log = log
        self.SIM = SIM

# wrap Display and save thread with queues   
from ThreadDnS import DnSThread
class DnSThread_2(DnSThread):
    def __init__(self, ui, log):
        super().__init__()
        self.ui = ui
        self.queue = DnSQueue
        self.Digitizer = Digitizer
        self.log = log
        self.use_maya = use_maya
        

# wrap MainWindow object with queues and threads   
class GUI(MainWindow):
    def __init__(self):
        super().__init__()
        if use_maya:
            self.addMaya()
        self.log = LOG(self.ui)
        self.ui.RunButton.clicked.connect(self.run_task)
        self.ui.PauseButton.clicked.connect(self.Pause_task)
        self.ui.CenterGalvo.clicked.connect(self.CenterGalvo)
        
        # set window length for FFT
        self.ui.PostSamples.valueChanged.connect(self.update_Dispersion)
        self.ui.PreSamples.valueChanged.connect(self.update_Dispersion)
        self.ui.PostSamples_2.valueChanged.connect(self.update_Dispersion)
        self.ui.DelaySamples.valueChanged.connect(self.update_Dispersion)
        self.ui.TrimSamples.valueChanged.connect(self.update_Dispersion)
        # set stage boundary
        self.ui.XYmax.valueChanged.connect(self.Update_contrast_XY)
        self.ui.XYmin.valueChanged.connect(self.Update_contrast_XY)
        # self.ui.XYZmax.valueChanged.connect(self.Update_contrast_XYZ)
        # self.ui.XYZmin.valueChanged.connect(self.Update_contrast_XYZ)
        self.ui.Surfmax.valueChanged.connect(self.Update_contrast_Surf)
        self.ui.Surfmin.valueChanged.connect(self.Update_contrast_Surf)
        # connect buttons to functionalities
        # self.ui.RedoDC.clicked.connect(self.redo_dispersion_compensation)
        # self.ui.redoBG.clicked.connect(self.redo_background)
        self.ui.redoSurf.clicked.connect(self.redo_surface)
        # self.ui.BG_DIR.textChanged.connect(self.update_background)
        self.ui.InD_DIR.textChanged.connect(self.update_Dispersion)
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
        self.ui.SliceDir.clicked.connect(self.SliceDirection)
        self.ui.VibEnabled.clicked.connect(self.Vibratome)
        self.ui.SliceN.valueChanged.connect(self.change_slice_number)
        # Init all threads
        self.Init_allThreads()
        
        # testing buttons
        self.ui.TestButten1.clicked.connect(self.TestButton1Func)
        self.ui.TestButten2.clicked.connect(self.TestButton2Func)
        self.ui.TestButten3.clicked.connect(self.TestButton3Func)
        
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
        # RptAline and SingleAline is for checking Aline profile, we don't need to capture each Aline, only acquire and display ~30 Alines per second
        
        # RptBline and SingleBline is for checking Bline profile, we don't need to capture each Bline, only acquire and display ~30 Blines per second.
        # To capture and save each Bline, recommend using the Bline average parameter, or using Cscan mode but set Y stepsize to 0
        
        # Mosaic is for imaging the sample surface
        
        # Mosaic + Cut is for serial sectioning imaging
        
        # SingleCut is for cutting one slice only
        
        # RptCut is for cutting several slices as per defined in Vibratome panel
        
        if self.ui.ACQMode.currentText() in ['RptAline','RptBline','RptCscan','Mosaic','Mosaic+Cut','RptCut']:
            if self.ui.RunButton.isChecked():
                self.ui.RunButton.setText('Stop')
                # for surfScan and SurfSlice, popup a dialog to double check stage position
                if self.ui.ACQMode.currentText() in ['Mosaic','Mosaic+Cut','RptCut']:
                    dlg = StageDialog( self.ui.XPosition.value(), self.ui.YPosition.value(), self.ui.ZPosition.value())
                    dlg.setWindowTitle("double-check stage position")
                    if dlg.exec():
                        an_action = WeaverAction(self.ui.ACQMode.currentText())
                        WeaverQueue.put(an_action)
                    else:
                        # reset RUN button
                        self.ui.RunButton.setChecked(False)
                        self.ui.RunButton.setText('Go')
                        self.ui.PauseButton.setChecked(False)
                        self.ui.PauseButton.setText('Pause')
                        print('user aborted due to stage position incorrect...')
                else:
                    # for other actions, directly do the task
                    an_action = WeaverAction(self.ui.ACQMode.currentText())
                    WeaverQueue.put(an_action)
            else:
                self.Stop_task()
        elif self.ui.ACQMode.currentText() in ['SingleAline','SingleBline','SingleCscan','SingleCut']:
            if self.ui.RunButton.isChecked():
                self.ui.RunButton.setText('Stop')
                an_action = WeaverAction(self.ui.ACQMode.currentText())
                WeaverQueue.put(an_action)
        
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
            self.ui.SliceDir.setText('Forward')
        else:
            self.ui.SliceDir.setText('Backward')
            
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
            self.ui.PauseButton.setText('Resume')
            self.ui.statusbar.showMessage('acquisition paused...')
        else:
            PauseQueue.put('Resume')
            self.ui.PauseButton.setText('Pause')
            self.ui.statusbar.showMessage('acquisition resumed...')
      
    def Stop_task(self):
        PauseQueue.put('Stop')
        self.ui.statusbar.showMessage('acquisition stopped...')
        
    def update_Dispersion(self):
        an_action = GPUAction('update_Dispersion')
        GPUQueue.put(an_action)
        # self.update_background()
        
    # def update_background(self):
    #     an_action = GPUAction('update_background')
    #     GPUQueue.put(an_action)
        
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
        
    def redo_surface(self):
        an_action = WeaverAction('get_surface')
        WeaverQueue.put(an_action)
        
    def update_intDk(self):
        self.ui.intDk.setValue(self.ui.intDkSlider.value()/100)
        an_action = GPUAction('update_intDk')
        GPUQueue.put(an_action)
        
    def UninitBoard(self):
        an_action = DAction('UninitBoard')
        DQueue.put(an_action)
    
    def TestButton1Func(self):
        args = [[0, 0], [10, 100]]
        an_action = DnSAction('Init_Mosaic', data = None, args = args)
        DnSQueue.put(an_action)
        
    def TestButton2Func(self):
        args = [[1, 1], [10, 100]]
        an_action = DnSAction('Mosaic', data = np.ones([300*1700,150],dtype=np.float32)*50, args = args)
        DnSQueue.put(an_action)
    
    def TestButton3Func(self):
        an_action = DnSAction('display_mosaic') # data in Memory[memoryLoc]
        DnSQueue.put(an_action)
        
    def closeEvent(self, event):
        print('Exiting all threads')
        self.Stop_allThreads()
        settings = qc.QSettings("config.ini", qc.QSettings.IniFormat)
        self.SaveSettings()
        while not self.DnS_thread.isFinished:
            event.ignore()
        event.accept()

                

if __name__ == '__main__':
    app = QApplication(sys.argv)
    example = GUI()
    example.show()
    sys.exit(app.exec_())

    