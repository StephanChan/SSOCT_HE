# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 16:35:04 2023

@author: admin
"""

from GUI import Ui_MainWindow
from PyQt5.QtWidgets import  QMainWindow
from PyQt5.QtGui import QPixmap

from matplotlib import pyplot as plt
from GalvoWaveform import GenGalvoWave

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
    def update_galvowaveform(self):
        # calculate the total X range
        Xrange=self.ui.Xsteps.value()*self.ui.XStepSize.value()/1000
        # update X range in lable
        self.ui.XrangeLabel.setText('X range(mm): '+str(Xrange))
        # generate waveform
        waveform, status = GenGalvoWave(self.ui.XStepSize.value(),\
                                        self.ui.Xsteps.value(),\
                                        self.ui.AlineAVG.value(),\
                                        self.ui.Bias.value(),\
                                        self.ui.Objective.currentText())
        # show generating waveform result
        self.ui.statusbar.showMessage(status)
        # clear content on plot
        plt.cla()
        # plot the new waveform
        plt.plot(range(len(waveform)),waveform)
        plt.ylim(-2,2)
        plt.ylabel('voltage(V)')
        plt.xticks(fontsize=15)
        plt.yticks(fontsize=15)
        plt.rcParams['savefig.dpi']=500
        # save plot as jpeg
        plt.savefig('galvo waveform.jpg')
        # load waveform image
        pixmap = QPixmap('galvo waveform.jpg')
        # clear content on the waveformLabel
        self.ui.waveformLabel.clear()
        # update iamge on the waveformLabel
        self.ui.waveformLabel.setPixmap(pixmap)
        
