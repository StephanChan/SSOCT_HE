# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 16:35:04 2023

@author: admin
"""

from GUI import Ui_MainWindow
import os
from PyQt5.QtWidgets import  QMainWindow, QFileDialog
import PyQt5.QtCore as qc
import numpy as np
from Actions import *
from Generaic_functions import *
import traceback

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        settings = qc.QSettings("config.ini", qc.QSettings.IniFormat)
        
        try:
            self.load_settings(settings)
        except Exception as error:
            print('settings reload failed, using default settings')
            print(traceback.format_exc())
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
        # self.ui.ACQMode.currentIndexChanged.connect(self.Adjust_contrast)
        # self.ui.FFTDevice.currentIndexChanged.connect(self.Update_scale)

        # update laser model
        self.ui.Laser.currentIndexChanged.connect(self.Update_laser)
        self.ui.Save.stateChanged.connect(self.chooseDir)
        self.ui.LoadDispersion.clicked.connect(self.chooseCompenstaion)
        self.ui.LoadBG.clicked.connect(self.chooseBackground)
        

    def chooseDir(self):
        if self.ui.Save.isChecked():
            
             dir_choose = QFileDialog.getExistingDirectory(self,  
                                         "选取文件夹",  
                                         os.getcwd()) # 起始路径
        
             if dir_choose == "":
                 print("\n取消选择")
                 return
             self.ui.DIR.setText(dir_choose)
         
    def chooseCompenstaion(self):
         fileName_choose, filetype = QFileDialog.getOpenFileName(self,  
                                    "选取文件",  
                                    os.getcwd(), # 起始路径 
                                    "All Files (*);;Text Files (*.txt)")   # 设置文件扩展名过滤,用双分号间隔

         if fileName_choose == "":
            print("\n取消选择")
            return

         self.ui.Disp_DIR.setText(fileName_choose)
         # self.update_Dispersion()
        
    def chooseBackground(self):
        fileName_choose, filetype = QFileDialog.getOpenFileName(self,  
                                   "选取文件",  
                                   os.getcwd(), # 起始路径 
                                   "All Files (*);;Text Files (*.txt)")   # 设置文件扩展名过滤,用双分号间隔

        if fileName_choose == "":
           print("\n取消选择")
           return

        self.ui.BG_DIR.setText(fileName_choose)
        # self.update_background()
        
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
        current_message = self.ui.statusbar.currentMessage()
        self.ui.statusbar.showMessage(current_message+status)
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
        
    def Update_laser(self):
        if self.ui.Laser.currentText() == 'Axsun100k':
            self.Aline_frq = 100000
        elif self.ui.Laser.currentText() == 'Thorlabs200k':
            self.Aline_frq = 200000
        else:
            self.ui.statusbar.showMessage('Laser invalid!!!')
    
    
    def load_settings(self,settings):
        self.ui.FFTresults.setCurrentText(settings.value("FFTresults"))
        self.ui.Objective.setCurrentText(settings.value("Objective"))
        self.ui.Xsteps.setValue(np.int16(settings.value('Xsteps')))
        self.ui.XStepSize.setValue(np.float32(settings.value('XStepSize')))
        self.ui.XBias.setValue(np.float32(settings.value('XBias')))
        self.ui.AlineAVG.setValue(np.int16(settings.value('AlineAVG')))
        self.ui.Ysteps.setValue(np.int16(settings.value('Ysteps')))
        self.ui.YStepSize.setValue(np.float32(settings.value('YStepSize')))
        self.ui.BlineAVG.setValue(np.int16(settings.value('BlineAVG')))
        self.ui.DepthStart.setValue(np.int16(settings.value('DepthStart')))
        self.ui.DepthRange.setValue(np.int16(settings.value('DepthRange')))
        self.ui.PreClock.setValue(np.int16(settings.value('PreClock')))
        self.ui.PostClock.setValue(np.int16(settings.value('PostClock')))
        self.ui.XStart.setValue(np.float32(settings.value('XStart')))
        self.ui.XStop.setValue(np.float32(settings.value('XStop')))
        self.ui.YStart.setValue(np.float32(settings.value('YStart')))
        self.ui.YStop.setValue(np.float32(settings.value('YStop')))
        self.ui.Overlap.setValue(np.float32(settings.value('Overlap')))
        self.ui.ImageZStart.setValue(np.float32(settings.value('ImageZStart')))
        self.ui.ImageZDepth.setValue(np.float32(settings.value('ImageZDepth')))
        self.ui.ImageZnumber.setValue(np.int16(settings.value('ImageZnumber')))
        self.ui.SliceZStart.setValue(np.float32(settings.value('SliceZStart')))
        self.ui.SliceZDepth.setValue(np.float32(settings.value('SliceZDepth')))
        self.ui.SliceZnumber.setValue(np.int16(settings.value('SliceZnumber')))
        self.ui.PostSamples_2.setValue(np.int16(settings.value('PostSamples_2')))
        self.ui.TrigDura.setValue(np.int16(settings.value('TrigDura')))
        self.ui.TriggerTimeout_2.setValue(np.int16(settings.value('TriggerTimeout_2')))
        self.ui.Disp_DIR.setText(settings.value('Disp_DIR'))
        self.ui.DelaySamples.setValue(np.int16(settings.value('DelaySamples')))
        self.ui.XPosition.setValue(np.float32(settings.value('XPosition')))
        self.ui.YPosition.setValue(np.float32(settings.value('YPosition')))
        self.ui.ZPosition.setValue(np.float32(settings.value('ZPosition')))
        self.ui.BG_DIR.setText(settings.value('BG_DIR'))
        
    def save_settings(self,settings):
        settings.setValue("FFTresults",self.ui.FFTresults.currentText())
        settings.setValue("Objective",self.ui.Objective.currentText())
        settings.setValue("Xsteps",self.ui.Xsteps.value())
        settings.setValue("XStepSize",self.ui.XStepSize.value())
        settings.setValue("XBias",self.ui.XBias.value())
        settings.setValue("AlineAVG",self.ui.AlineAVG.value())
        settings.setValue("Ysteps",self.ui.Ysteps.value())
        settings.setValue("YStepSize",self.ui.YStepSize.value())
        settings.setValue("BlineAVG",self.ui.BlineAVG.value())
        settings.setValue("DepthStart",self.ui.DepthStart.value())
        settings.setValue("DepthRange",self.ui.DepthRange.value())
        settings.setValue("PreClock",self.ui.PreClock.value())
        settings.setValue("PostClock",self.ui.PostClock.value())
        settings.setValue("XStart",self.ui.XStart.value())
        settings.setValue("XStop",self.ui.XStop.value())
        settings.setValue("YStart",self.ui.YStart.value())
        settings.setValue("YStop",self.ui.YStop.value())
        settings.setValue("Overlap",self.ui.Overlap.value())
        settings.setValue("ImageZStart",self.ui.ImageZStart.value())
        settings.setValue("ImageZDepth",self.ui.ImageZDepth.value())
        settings.setValue("ImageZnumber",self.ui.ImageZnumber.value())
        settings.setValue("SliceZStart",self.ui.SliceZStart.value())
        settings.setValue("SliceZDepth",self.ui.SliceZDepth.value())
        settings.setValue("SliceZnumber",self.ui.SliceZnumber.value())
        settings.setValue("PostSamples_2",self.ui.PostSamples_2.value())
        settings.setValue("TrigDura",self.ui.TrigDura.value())
        settings.setValue("TriggerTimeout_2",self.ui.TriggerTimeout_2.value())
        settings.setValue("Disp_DIR",self.ui.Disp_DIR.text())
        settings.setValue("DelaySamples",self.ui.DelaySamples.value())
        settings.setValue("XPosition",self.ui.XPosition.value())
        settings.setValue("YPosition",self.ui.YPosition.value())
        settings.setValue("ZPosition",self.ui.ZPosition.value())
        settings.setValue("BG_DIR",self.ui.BG_DIR.text())
        

        
        
        
        
        