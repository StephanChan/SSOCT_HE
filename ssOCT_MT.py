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


import time
import sys
from multiprocessing import Queue
from PyQt5.QtWidgets import QApplication
from mainWindow import MainWindow
from Actions import *
from ThreadSave import SaveThread
from ThreadAcq import ACQThread
from ThreadGPU import GPUThread
from ThreadStage import StageThread


global XstageQueue
global YstageQueue
global AcqQueue
global GPUQueue
global SaveQueue

XstageQueue = Queue()
YstageQueue = Queue()
AcqQueue = Queue()
GPUQueue = Queue()
SaveQueue = Queue()

class GUI(MainWindow):
    def __init__(self):
        super().__init__()
        self.Save_thread=SaveThread(5, SaveQueue)
        self.ACQ_thread=ACQThread(10, AcqQueue)
        self.GPU_thread=GPUThread(8, GPUQueue)
        self.Xstage_thread = StageThread(0.5, XstageQueue)
        self.Ystage_thread = StageThread(0.6, YstageQueue)
        self.connectActions()
    
    def connectActions(self):
        self.ui.RunButton.clicked.connect(self.run_tasks)
        self.ui.StopButton.clicked.connect(self.finish_tasks)
        self.ui.Xsteps.valueChanged.connect(self.update_galvowaveform)
        self.ui.XStepSize.valueChanged.connect(self.update_galvowaveform)
        self.ui.AlineAVG.valueChanged.connect(self.update_galvowaveform)
        self.ui.Bias.valueChanged.connect(self.update_galvowaveform)
        self.ui.Objective.currentTextChanged.connect(self.update_galvowaveform)
        
        
    def run_tasks(self):
        # start all threads
        self.Save_thread.start()
        self.ACQ_thread.start()
        self.GPU_thread.start()
        self.Xstage_thread.start()
        self.Ystage_thread.start()
        ii=0
        while ii<2:
            an_element=save()
            SaveQueue.put(an_element)
            time.sleep(0.001)
            an_element=ACQ('single frame')
            AcqQueue.put(an_element)
            time.sleep(0.001)
            an_element=process()
            GPUQueue.put(an_element)
            time.sleep(0.001)
            an_element=moveto('up','10')
            XstageQueue.put(an_element)
            time.sleep(0.001)
            an_element=setSpeed('up','10')
            YstageQueue.put(an_element)
            time.sleep(0.001)
            ii+=1
            
    def finish_tasks(self):
        exit_elment=EXIT()
        SaveQueue.put(exit_elment)
        AcqQueue.put(exit_elment)
        GPUQueue.put(exit_elment)
        XstageQueue.put(exit_elment)
        YstageQueue.put(exit_elment)
        
        if self.Save_thread.isFinished:
            self.ui.statusbar.showMessage('Save process exited')
        

        
if __name__ == '__main__':
    # assign sleep time to each hardware thread to simulate hardware working time
    app = QApplication(sys.argv)
    example = GUI()
    example.show()
    sys.exit(app.exec_())
    
    # put actions into the each queue
    
    
            
    


# In[ ]: