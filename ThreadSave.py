# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 16:46:01 2023

@author: admin
"""
# Save thread class handles all saving-related actions
from PyQt5.QtCore import  QThread
import time

class SaveThread(QThread):
    def __init__(self, ui, SaveQueue):
        super().__init__()
        self.ui = ui
        self.queue = SaveQueue
        
    # overwrite run function to de-queue
    def run(self):
        self.QueueOut()
    
    # while loop that awaits for actions
    def QueueOut(self):
        self.item = self.queue.get()
        while self.item.action != 'exit':
            if self.item.action == 'Save':
                self.ui.statusbar.showMessage('Save thread is doing '+self.item.action)
                start = time.time()
                self.WriteData(self.item.data, self.item.filename)
                self.ui.statusbar.showMessage('saving took '+str(time.time()-start)+' seconds')
            self.item = self.queue.get()
            
    def WriteData(self, data, filename):
        filePath = self.ui.DIR.toPlainText()
        filePath = filePath + "\\" + filename
        # print(filePath)
        with open(filePath, "wb") as file:
            file.write(data)
            file.close()
            
    