# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 16:50:25 2023

@author: admin
"""
from PyQt5.QtCore import  QThread
import time

class GPUThread(QThread):
    def __init__(self, work, GPUQueue):
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