# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 16:35:04 2023

@author: admin
"""

from GUI import Ui_MainWindow
from PyQt5.QtWidgets import  QMainWindow
from PyQt5.QtGui import QPixmap
import numpy as np

from matplotlib import pyplot as plt
from Generaic_functions import *

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.Aline_frq = 100000
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.connectActions()
    
    def connectActions(self):
        self.ui.Xsteps.valueChanged.connect(self.update_galvoXwaveform)
        self.ui.XStepSize.valueChanged.connect(self.update_galvoXwaveform)
        self.ui.AlineAVG.valueChanged.connect(self.update_galvoXwaveform)
        self.ui.XBias.valueChanged.connect(self.update_galvoXwaveform)
        self.ui.Objective.currentTextChanged.connect(self.update_galvoXwaveform)
        
        # self.ui.Ysteps.valueChanged.connect(self.update_galvoYwaveform)
        # self.ui.YStepSize.valueChanged.connect(self.update_galvoYwaveform)
        # self.ui.BlineAVG.valueChanged.connect(self.update_galvoYwaveform)
        # self.ui.YBias.valueChanged.connect(self.update_galvoYwaveform)
        # self.ui.Objective.currentTextChanged.connect(self.update_galvoYwaveform)
        
        self.ui.XStart.valueChanged.connect(self.update_Mosaic)
        self.ui.XStop.valueChanged.connect(self.update_Mosaic)
        self.ui.YStart.valueChanged.connect(self.update_Mosaic)
        self.ui.YStop.valueChanged.connect(self.update_Mosaic)
        self.ui.FOV.valueChanged.connect(self.update_Mosaic)
        self.ui.Overlap.valueChanged.connect(self.update_Mosaic)
        
        self.ui.ImageZStart.valueChanged.connect(self.Calculate_ImageDepth)
        self.ui.ImageZDepth.valueChanged.connect(self.Calculate_ImageDepth)
        self.ui.ImageZnumber.valueChanged.connect(self.Calculate_ImageDepth)
        
        self.ui.SliceZStart.valueChanged.connect(self.Calculate_SliceDepth)
        self.ui.SliceZDepth.valueChanged.connect(self.Calculate_SliceDepth)
        self.ui.SliceZnumber.valueChanged.connect(self.Calculate_SliceDepth)
        
        
        
    def update_galvoXwaveform(self):
        # calculate the total X range
        Xrange=self.ui.Xsteps.value()*self.ui.XStepSize.value()/1000
        # update X range in lable
        self.ui.XrangeLabel.setText('X range(mm): '+str(Xrange))
        # generate waveform
        self.Xwaveform, status = GenGalvoWave(self.ui.XStepSize.value(),\
                                        self.ui.Xsteps.value(),\
                                        self.ui.AlineAVG.value(),\
                                        self.ui.XBias.value(),\
                                        self.ui.Objective.currentText(),\
                                        self.ui.PreClock.value(),\
                                        self.ui.PostClock.value())
        # show generating waveform result
        #print(self.Xwaveform)
        self.ui.statusbar.showMessage(status)
        if len(self.Xwaveform) > 0:
            pixmap = LinePlot(self.Xwaveform)
            # clear content on the waveformLabel
            self.ui.XwaveformLabel.clear()
            # update iamge on the waveformLabel
            self.ui.XwaveformLabel.setPixmap(pixmap)
        
    # def update_galvoYwaveform(self):
    #     # calculate the total X range
    #     Yrange=self.ui.Ysteps.value()*self.ui.YStepSize.value()/1000
    #     # update X range in lable
    #     self.ui.YrangeLabel.setText('Y range(mm): '+str(Yrange))
    #     # generate waveform
    #     self.Ywaveform, status = GenGalvoWave(self.ui.YStepSize.value(),\
    #                                     self.ui.Ysteps.value(),\
    #                                     self.ui.BlineAVG.value(),\
    #                                     self.ui.YBias.value(),\
    #                                     self.ui.Objective.currentText())
    #     # show generating waveform result
    #     self.ui.statusbar.showMessage(status)
    #     if self.Ywaveform != None:
    #         pixmap = LinePlot(self.Xwaveform)
    #         # clear content on the waveformLabel
    #         self.ui.YwaveformLabel.clear()
    #         # update iamge on the waveformLabel
    #         self.ui.YwaveformLabel.setPixmap(pixmap)
        
    def update_Mosaic(self):
        self.Mosaic, status = GenMosaic(self.ui.XStart.value(),\
                                        self.ui.XStop.value(),\
                                        self.ui.YStart.value(),\
                                        self.ui.YStop.value(),\
                                        self.ui.FOV.value(),\
                                        self.ui.Overlap.value())
        self.ui.statusbar.showMessage(status)
        if self.Mosaic is not None:
            pixmap = ScatterPlot(self.Mosaic)
            # clear content on the waveformLabel
            self.ui.MosaicLabel.clear()
            # update iamge on the waveformLabel
            self.ui.MosaicLabel.setPixmap(pixmap)
        
    def Calculate_ImageDepth(self):
        self.image_depths = GenHeights(self.ui.ImageZStart.value(),\
                                       self.ui.ImageZDepth.value(),\
                                       self.ui.ImageZnumber.value())
        #print(self.image_depths)
        #self.ui.statusbar.showMessage(self.image_depths)
            
    def Calculate_SliceDepth(self):
        self.slice_depths = GenHeights(self.ui.SliceZStart.value(),\
                                       self.ui.SliceZDepth.value(),\
                                       self.ui.SliceZnumber.value())
        #print(self.slice_depths)
        #self.ui.statusbar.showMessage(self.image_depths)
        

        
