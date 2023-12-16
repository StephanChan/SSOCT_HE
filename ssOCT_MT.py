# -*- coding: utf-8 -*-
"""
Created on Sun Dec 10 20:14:40 2023

@author: Shuaibin Chang
"""

# using QThread of PYQT to do multithreading control of acquiring, processing and saving
# multithreading is more appropriate only when not using PyQt, in other words, not GUI applications
# subclass QThread and overwrite run() with a while loop to wait for user import

# using Queue to init hardware threads

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
# define structure for queue element

# between threads, using Queue to pass variables, variables gets duplicated in memory when passed as arguments

import time
import sys
from multiprocessing import Queue
from PyQt5.QtWidgets import QApplication
from mainWindow import MainWindow
from Actions import ACQAction, EXIT, StageAction
from ThreadSave import SaveThread
from ThreadAcq import ACQThread
from ThreadGPU import GPUThread
from ThreadStage import StageThread
from ThreadDisplay import DSPThread


global StageQueue
global AcqQueue
global GPUQueue
global SaveQueue
global DisplayQueue


StageQueue = Queue()
AcqQueue = Queue()
GPUQueue = Queue()
SaveQueue = Queue()
DisplayQueue = Queue()

class GUI(MainWindow):
    def __init__(self):
        super().__init__()


        self.Init_allThreads()
        self.ui.RunButton.clicked.connect(self.run_task)
        # self.ui.StopButton.clicked.connect(self.Stop_task)
        self.ui.Xmove2.clicked.connect(self.Xmove2)
        self.ui.Ymove2.clicked.connect(self.Ymove2)
        self.ui.Zmove2.clicked.connect(self.Zmove2)
    
    def Init_allThreads(self):
        self.Save_thread=SaveThread(self.ui, SaveQueue)
        self.ACQ_thread=ACQThread(self.ui, AcqQueue, DisplayQueue, SaveQueue, DisplayQueue)
        self.GPU_thread=GPUThread(8, GPUQueue)
        self.Stage_thread = StageThread(self.ui, StageQueue)
        self.Display_thread = DSPThread(DisplayQueue, self.ui)
        
        self.Save_thread.start()
        self.ACQ_thread.start()
        self.GPU_thread.start()
        self.Stage_thread.start()
        self.Display_thread.start()
    
            
    def Stop_allThreads(self):
        exit_element=EXIT()
        SaveQueue.put(exit_element)
        AcqQueue.put(exit_element)
        GPUQueue.put(exit_element)
        StageQueue.put(exit_element)
        DisplayQueue.put(exit_element)
        
    def run_task(self):
        if self.ui.ACQMode.currentText() != 'Slice':
            # RptAline and SingleAline is for checking Aline profile, we don't need to capture each Aline, only display 30 Alines per second\
            # if one wants to capture each Aline, they can set X and Y step size to be 0 and capture Cscan instead
            
            
            # RptBline and SingleBline is for checking Bline profile, only display 30 Blines per second
            # if one wants to capture each Bline, they can set Y stepsize to be 0 and capture Cscan instead
            
            # RptCscan is for acquiring Cscan at the same location repeatitively
            
            an_action = ACQAction(self.ui.ACQMode.currentText())
            AcqQueue.put(an_action)
        else:
            self.Slice()
        
    def Xmove2(self):
        an_action = StageAction('Xmove2')
        StageQueue.put(an_action)
        
    def Ymove2(self):
        an_action = StageAction('Ymove2')
        StageQueue.put(an_action)
        
    def Zmove2(self):
        an_action = StageAction('Zmove2')
        StageQueue.put(an_action)
        
        
    def closeEvent(self, event):
        self.ui.statusbar.showMessage('Exiting all threads')
        self.Stop_allThreads()
        if self.Display_thread.isFinished:
            event.accept()
        else:
            event.ignore()
        

                

if __name__ == '__main__':
    # assign sleep time to each hardware thread to simulate hardware working time
    app = QApplication(sys.argv)
    example = GUI()
    example.show()
    sys.exit(app.exec_())

    