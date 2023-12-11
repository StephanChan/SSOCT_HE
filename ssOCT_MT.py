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
from GUI import Ui_MainWindow
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import  QThread

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

class moveto():
    def __init__(self, direction, destination):
        super().__init__()
        self.action='move to'
        self.direction=direction
        self.destination=destination
        
class setSpeed():
    def __init__(self, direction, speed):
        super().__init__()
        self.action='set speed'
        self.direction=direction
        self.speed=speed
        
class save():
    def __init__(self):
        super().__init__()
        self.action='save'
        
class process():
    def __init__(self):
        super().__init__()
        self.action='process'

class ACQ():
    def __init__(self, mode):
        super().__init__()
        self.action='acquire'
        self.mode=mode
        
class EXIT():
    def __init__(self):
        super().__init__()
        self.action='exit'
        
class SaveThread(QThread):
    def __init__(self, work):
        super().__init__()
        self.work = work
        self.queue = SaveQueue
        
    # run 
    def run(self):
        self.QueueOut()
        
    def QueueOut(self):
        self.item = self.queue.get()
        while self.item.action != 'exit':
            print('Save thread is doing ',self.item.action)
            time.sleep(self.work)
            self.item = self.queue.get()
        print('Save process is exiting')
            
class ACQThread(QThread):
    def __init__(self, work):
        super().__init__()
        self.work = work
        self.queue = AcqQueue
        
    def run(self):
        self.QueueOut()
        
    def QueueOut(self):
        self.item = self.queue.get()
        while self.item.action != 'exit':
            print('ACQ thread is doing ',self.item.action)
            time.sleep(self.work) 
            self.item = self.queue.get()
        print('ACQ process is exiting')
            
class GPUThread(QThread):
    def __init__(self, work):
        super().__init__()
        self.work = work
        self.queue = GPUQueue
        
    def run(self):
        self.QueueOut()
        
    def QueueOut(self):
        self.item = self.queue.get()
        while self.item.action != 'exit':
            print('GPU thread is doing ',self.item.action)
            time.sleep(self.work)
            self.item = self.queue.get()
        print('GPU process is exiting')

class XstageProcess(QThread):
    def __init__(self, work):
        super().__init__()
        self.work = work
        self.queue = XstageQueue
    
    def run(self):
        self.QueueOut()
        
    def QueueOut(self):
        self.item = self.queue.get()
        while self.item.action != 'exit':
            print('X stage process is doing ',self.item.action)
            time.sleep(self.work)
            self.item = self.queue.get()
        print('X stage process is exiting')

class YstageProcess(QThread):
    def __init__(self, work):
        super().__init__()
        self.work = work
        self.queue = YstageQueue
        
    def run(self):
        self.QueueOut()
        
    def QueueOut(self):
        self.item = self.queue.get()
        while self.item.action != 'exit':
            print('Y stage process is doing ',self.item.action)
            time.sleep(self.work)
            self.item = self.queue.get()
        print('Y stage process is exiting')

class mainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.Save_thread=SaveThread(5)
        self.ACQ_thread=ACQThread(10)
        self.GPU_thread=GPUThread(8)
        self.Xstage_process = XstageProcess(0.5)
        self.Ystage_process = YstageProcess(0.6)
        self.connectActions()
    
    def connectActions(self):
        self.ui.RunButton.clicked.connect(self.run_tasks)
        self.ui.StopButton.clicked.connect(self.finish_tasks)
        
    def run_tasks(self):
        # start all threads
        self.Save_thread.start()
        self.ACQ_thread.start()
        self.GPU_thread.start()
        self.Xstage_process.start()
        self.Ystage_process.start()
        ii=0
        while ii<5:
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
        

        
if __name__ == '__main__':
    # assign sleep time to each hardware thread to simulate hardware working time
    app = QApplication(sys.argv)
    example = mainWindow()
    example.show()
    sys.exit(app.exec_())
    
    # put actions into the each queue
    
    
            
    


# In[ ]: