# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 16:51:20 2023

@author: admin
"""
from PyQt5.QtCore import  QThread

class StageThread(QThread):
    def __init__(self, ui, stageQueue):
        super().__init__()
        self.ui = ui
        self.queue = stageQueue
    
    def run(self):
        self.QueueOut()
        
    def QueueOut(self):
        self.item = self.queue.get()
        while self.item.action != 'exit':
            if self.item.action == 'Xmove2':
                #print('X stage thread is doing ',self.item.action)
                self.ui.statusbar.showMessage('X stage moving to position: '+ str(self.ui.XPosition.value()))
            elif self.item.action == 'Ymove2':
                #print('Y stage thread is doing ',self.item.action)
                self.ui.statusbar.showMessage('Y stage moving to position: '+ str(self.ui.YPosition.value()))
            elif self.item.action == 'Zmove2':
                #print('Z stage thread is doing ',self.item.action)
                self.ui.statusbar.showMessage('Z stage moving to position: '+ str(self.ui.ZPosition.value()))
            else:
                self.ui.statusbar.showMessage('stage thread is doing something undefined: '+self.item.action)
            self.item = self.queue.get()