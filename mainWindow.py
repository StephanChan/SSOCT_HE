# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 16:35:04 2023

@author: admin
"""

from GUI import Ui_MainWindow
from PyQt5.QtWidgets import  QMainWindow
import numpy as np
from Actions import *
from Generaic_functions import *

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.Update_laser()
        self.update_galvoXwaveform()
        self.update_Mosaic()
        
        self.connectActions()
        
    def connectActions(self):
        self.ui.Xsteps.valueChanged.connect(self.update_galvoXwaveform)
        self.ui.XStepSize.valueChanged.connect(self.update_galvoXwaveform)
        self.ui.AlineAVG.valueChanged.connect(self.update_galvoXwaveform)
        self.ui.XBias.valueChanged.connect(self.update_galvoXwaveform)
        self.ui.Objective.currentTextChanged.connect(self.update_galvoXwaveform)
        self.ui.PreClock.valueChanged.connect(self.update_galvoXwaveform)
        self.ui.PostClock.valueChanged.connect(self.update_galvoXwaveform)
        # self.ui.Ysteps.valueChanged.connect(self.update_galvoYwaveform)
        # self.ui.YStepSize.valueChanged.connect(self.update_galvoYwaveform)
        # self.ui.BlineAVG.valueChanged.connect(self.update_galvoYwaveform)
        # self.ui.YBias.valueChanged.connect(self.update_galvoYwaveform)
        # self.ui.Objective.currentTextChanged.connect(self.update_galvoYwaveform)
        
        self.ui.XStart.valueChanged.connect(self.update_Mosaic)
        self.ui.XStop.valueChanged.connect(self.update_Mosaic)
        self.ui.YStart.valueChanged.connect(self.update_Mosaic)
        self.ui.YStop.valueChanged.connect(self.update_Mosaic)
        self.ui.Overlap.valueChanged.connect(self.update_Mosaic)
        self.ui.FOV.textChanged.connect(self.update_Mosaic)
        
        self.ui.ImageZStart.valueChanged.connect(self.Calculate_ImageDepth)
        self.ui.ImageZDepth.valueChanged.connect(self.Calculate_ImageDepth)
        self.ui.ImageZnumber.valueChanged.connect(self.Calculate_ImageDepth)
        
        self.ui.SliceZStart.valueChanged.connect(self.Calculate_SliceDepth)
        self.ui.SliceZDepth.valueChanged.connect(self.Calculate_SliceDepth)
        self.ui.SliceZnumber.valueChanged.connect(self.Calculate_SliceDepth)
        # change brigtness and contrast
        self.ui.ACQMode.currentIndexChanged.connect(self.Adjust_contrast)
        self.ui.FFTDevice.currentIndexChanged.connect(self.Adjust_contrast)

        # update laser model
        self.ui.Laser.currentIndexChanged.connect(self.Update_laser)
        
        
    def update_galvoXwaveform(self):
        # calculate the total X range
        Xrange=self.ui.Xsteps.value()*self.ui.XStepSize.value()/1000
        # update X range in lable
        self.ui.XrangeLabel.setText('X(mm): '+str(Xrange))
        self.ui.FOV.setText('XFOV(mm): '+str(Xrange))
        # generate waveform
        DOwaveform, AOwaveform, status = GenAODO(mode='RptBline', \
                                                 Aline_frq = self.Aline_frq, \
                                                 XStepSize = self.ui.XStepSize.value(), \
                                                 XSteps = self.ui.Xsteps.value(), \
                                                 AVG = self.ui.AlineAVG.value(), \
                                                 bias = self.ui.XBias.value(), \
                                                 obj = self.ui.Objective.currentText(),\
                                                 preclocks = self.ui.PreClock.value(),\
                                                 postclocks = self.ui.PostClock.value())
        # show generating waveform result
        #print(self.Xwaveform)
        self.ui.statusbar.showMessage(status)
        if len(AOwaveform) > 0:
            pixmap = LinePlot(AOwaveform, DOwaveform)
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
        self.Mosaic, status = GenMosaic_XGalvo(self.ui.XStart.value(),\
                                        self.ui.XStop.value(),\
                                        self.ui.YStart.value(),\
                                        self.ui.YStop.value(),\
                                        self.ui.Xsteps.value()*self.ui.XStepSize.value()/1000,\
                                        self.ui.Overlap.value())
        self.ui.statusbar.showMessage(status)
        if self.Mosaic is not None:
            mosaic=np.zeros([2,len(self.Mosaic)*2])
            for ii, element in enumerate(self.Mosaic):
                mosaic[0,ii*2] = element.x
                mosaic[1,ii*2] = element.ystart
                mosaic[0,ii*2+1] = element.x
                mosaic[1,ii*2+1] = element.ystop
                
            pixmap = ScatterPlot(mosaic)
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
        
    def Adjust_contrast(self):
        if self.ui.ACQMode.currentText() in ['SingleAline', 'RptAline']:
            if self.ui.FFTDevice.currentText() == 'None':
                self.ui.MinContrast.setValue(0)
                self.ui.MaxContrast.setValue(1)
            else:
                self.ui.MinContrast.setValue(-7)
                self.ui.MaxContrast.setValue(-2)
        elif self.ui.ACQMode.currentText() in ['SingleBline', 'RptBline','SingleCscan', 'SurfScan', 'SurfScan+Slice']:
            self.ui.MinContrast.setValue(0)
            self.ui.MaxContrast.setValue(0.01)
        

        
    def Update_laser(self):
        if self.ui.Laser.currentText() == 'Axsun100k':
            self.Aline_frq = 100000
        elif self.ui.Laser.currentText() == 'Thorlabs200k':
            self.Aline_frq = 200000
        else:
            self.ui.statusbar.showMessage('Laser invalid!!!')