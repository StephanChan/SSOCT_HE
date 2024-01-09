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

import time
import sys
from multiprocessing import Queue
from PyQt5.QtWidgets import QApplication
from mainWindow import MainWindow
from Actions import ACQAction, EXIT, AODOAction
from ThreadAcq import ACQThread
from ThreadAODO import AODOThread
from ThreadDisplay import DSPThread


global AODOQueue
global AcqQueue
global DisplayQueue
global PauseQueue


AODOQueue = Queue()
AcqQueue = Queue()
DisplayQueue = Queue()
PauseQueue = Queue()

class GUI(MainWindow):
    def __init__(self):
        super().__init__()


        self.Init_allThreads()
        self.ui.RunButton.clicked.connect(self.run_task)
        self.ui.PauseButton.clicked.connect(self.Pause_task)
        self.ui.Xmove2.clicked.connect(self.Xmove2)
        self.ui.Ymove2.clicked.connect(self.Ymove2)
        self.ui.Zmove2.clicked.connect(self.Zmove2)
        self.ui.CenterGalvo.clicked.connect(self.CenterGalvo)
    
    def Init_allThreads(self):
        self.ACQ_thread=ACQThread(self.ui, AcqQueue, DisplayQueue, AODOQueue, PauseQueue)
        self.AODO_thread = AODOThread(self.ui, AODOQueue, PauseQueue)
        self.Display_thread = DSPThread(self.ui, DisplayQueue)
        
        self.ACQ_thread.start()
        self.AODO_thread.start()
        self.Display_thread.start()
            
    def Stop_allThreads(self):
        exit_element=EXIT()
        AcqQueue.put(exit_element)
        AODOQueue.put(exit_element)
        DisplayQueue.put(exit_element)
        
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
                an_action = ACQAction(self.ui.ACQMode.currentText())
                AcqQueue.put(an_action)
            else:
                self.ui.RunButton.setText('Run')
                self.Stop_task()
        elif self.ui.ACQMode.currentText() in ['SingleAline','SingleBline','SingleCscan']:
            an_action = ACQAction(self.ui.ACQMode.currentText())
            AcqQueue.put(an_action)
            self.ui.RunButton.setChecked(False)
            self.ui.RunButton.setText('Run')
        else:
            self.Slice()

        
    def Xmove2(self):
        an_action = AODOAction('Xmove2')
        AODOQueue.put(an_action)
        
    def Ymove2(self):
        an_action = AODOAction('Ymove2')
        AODOQueue.put(an_action)
        
    def Zmove2(self):
        an_action = AODOAction('Zmove2')
        AODOQueue.put(an_action)
        
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
        
    def closeEvent(self, event):
        self.ui.statusbar.showMessage('Exiting all threads')
        self.Stop_allThreads()
        if self.Display_thread.isFinished:
            event.accept()
        else:
            event.ignore()
        

                

if __name__ == '__main__':
    app = QApplication(sys.argv)
    example = GUI()
    example.show()
    sys.exit(app.exec_())

    