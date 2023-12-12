# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 16:46:01 2023

@author: admin
"""
# Save thread class handles all saving-related actions
from PyQt5.QtCore import  QThread
import time

class SaveThread(QThread):
    def __init__(self, work, SaveQueue):
        super().__init__()
        self.work = work
        self.queue = SaveQueue
        
    # overwrite run function to de-queue
    def run(self):
        self.QueueOut()
    
    # while loop that awaits for actions
    def QueueOut(self):
        self.item = self.queue.get()
        while self.item.action != 'exit':
            print('Save thread is doing ',self.item.action, '\n')
            time.sleep(self.work)
            self.item = self.queue.get()
            
    def WriteData(self, filePath, data):
        with open(filePath, "wb") as file:
            file.write(data)
            file.close()
            
    