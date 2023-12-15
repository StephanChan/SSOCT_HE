# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 18:26:44 2023

@author: admin
"""

from PyQt5.QtCore import  QThread
from PyQt5.QtGui import QPixmap
import time
from matplotlib import pyplot as plt

class DSPThread(QThread):
    def __init__(self, DspQueue, ui):
        super().__init__()
        self.queue = DspQueue
        self.ui = ui
        
    def run(self):
        self.QueueOut()
        
    def QueueOut(self):
        self.item = self.queue.get()
        while self.item.action != 'exit':
            if self.item.action == 'Aline':
                print('Display thread is doing ',self.item.action)
                self.Display_aline(self.item.args)
            
            elif self.item.action == 'Bline':
                print('Display thread is doing ',self.item.action)
                self.Display_bline(self.item.args)
                
            elif self.item.action == 'Cscan':
                print('Display thread is doing ',self.item.action)
                self.Display_Cscan(self.item.args)
                
            else:
                print('invalid action!')
            
            self.item = self.queue.get()
            
    def Display_aline(self,buffer):
        pass
    
    def Display_bline(self, buffer):
        # clear content on plot
        plt.cla()
        # plot the new waveform
        plt.imshow(buffer[0:1000,0:1000])
        # plt.ylim(-2,2)
        # plt.ylabel('voltage(V)')
        # plt.xticks(fontsize=15)
        # plt.yticks(fontsize=15)
        plt.rcParams['savefig.dpi']=500
        # save plot as jpeg
        plt.savefig('Bline.jpg')
        # load waveform image
        pixmap = QPixmap('Bline.jpg')
        # clear content on the waveformLabel
        self.ui.XYplane.clear()
        # update iamge on the waveformLabel
        self.ui.XYplane.setPixmap(pixmap)