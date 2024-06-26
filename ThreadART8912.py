# -*- coding: utf-8 -*-
"""
Created on Wed Jan 24 10:45:08 2024

@author: admin
"""
from PyQt5.QtCore import  QThread
import time
import ctypes
import sys
import numpy as np

from Actions import DbackAction
import traceback

global CONTINUOUS

CONTINUOUS = 0x7FFFFFFF

sys.path.append(r"C:\\Program Files (x86)\\ART Technology\\ArtScope\\Samples\\Python\\")

from ART_SCOPE_Lib.functions import Functions
from ART_SCOPE_Lib.constants import *
from ART_SCOPE_Lib.lib import *
from ART_SCOPE_Lib.errors import check_for_error, ArtScopeError


class ART8912(QThread):
    def __init__(self):
        super().__init__()
        self.MemoryLoc = 0
        self.exit_message = 'Digitizer thread successfully exited'
        self.InitBoard()
        
        
        
    def run(self):
        self.QueueOut()
        
    def QueueOut(self):
        self.item = self.queue.get()
        # start = time.time()
        while self.item.action != 'exit':
            try:
                if self.item.action == 'ConfigureBoard':
                    self.ConfigureBoard()
                elif self.item.action == 'StartAcquire':
                    self.StartAcquire()
                elif self.item.action == 'atomBoard':
                    self.atomBoard()
                elif self.item.action == 'UninitBoard':
                    self.UninitBoard()
                elif self.item.action == 'InitBoard':
                    self.InitBoard()
                elif self.item.action == 'simData':
                    self.simData()
                    
                else:
                    self.ui.statusbar.showMessage('Digitizer thread is doing something invalid: '+self.item.action)
                    self.ui.PrintOut.append('Digitizer thread is doing something invalid: '+self.item.action)
            except Exception as error:
                self.ui.statusbar.showMessage("\nAn error occurred:"+" skip the Digitizer action\n")
                self.ui.PrintOut.append("\nAn error occurred:"+" skip the Digitizer action\n")
                print(traceback.format_exc())
            # message = 'DIGITIZER spent: '+ str(round(time.time()-start,3))+'s'
            # self.ui.PrintOut.append(message)
            # print(message)
            # self.log.write(message)
            self.item = self.queue.get()
            # start = time.time()
        self.UninitBoard()
        print(self.exit_message)
        
    def InitBoard(self):
        taskName = "ART8912M"  # 设备名 DMC管理器里面的名称
        self.taskHandle = lib_importer.task_handle(0)                # 设备句柄
        # print('Gen handle')
        #创建任务
        error_code = Functions.ArtScope_init(taskName, self.taskHandle)
        if error_code < 0:
            check_for_error(error_code)
            message = 'Init digitizer failed'
        else:
            message = 'Init digitizer success'
        # self.ui.PrintOut.append(message)
        print(message)
        # self.log.write(message)
        
    def ConfigureBoard(self):
        
        #配置采集模式
        acquisitionMode = SampleMode.FINITE                     # 采集模式 连续采集模式
        error_code = Functions.ArtScope_ConfigureAcquisitionMode(self.taskHandle, acquisitionMode)
        
        #配置垂直参数
        if self.ui.Benable_2.currentText() == 'Disable':
            channelName = '0'                                     # 通道名称
        else:
            channelName = '0,1' 
            
        if self.ui.AInputRange_2.currentText() == '2V':
            verticalRange = InputRange.RANGE_2VPP   
        elif self.ui.AInputRange_2.currentText() == '10V':
            verticalRange = InputRange.RANGE_10VPP     
                       # 通道量程
        verticalOffset = 0                                      # 通道偏置
        verticalCoupling = CouplingType.DC                      # 通道耦合
        probeAttenuation = 1                                    # 探头衰减 暂时无效
        enabled = 1                                             # 通道使能
        error_code = Functions.ArtScope_ConfigureVertical(self.taskHandle, channelName, verticalRange, verticalOffset, verticalCoupling, probeAttenuation, enabled)
        if error_code < 0:
            Functions.ArtScope_Close(self.taskHandle)
            check_for_error(error_code)
            return 'D vertical failed'
        
        #配置水平参数
        if self.ui.ClockFreq_2.currentText() == '250MHz':
            minSampleRate = 250000000.0  
        elif self.ui.ClockFreq.currentText() == '125MHz':
            minSampleRate = 125000000.0  
                                    # 采样率
        minRecordLength = self.ui.PostSamples_2.value()           # 最小采样长度
        refPosition = 0                                         # 触发位置 0-后触发 100-预触发 0~100-中间触发
        error_code = Functions.ArtScope_ConfigureHorizontalTiming(self.taskHandle, minSampleRate, minRecordLength, refPosition)
        if error_code < 0:
            Functions.ArtScope_Close(self.taskHandle)
            check_for_error(error_code)
            return 'D Horizontal failed'
        
        #配置边沿触发
        triggerSource = TriggerSource.TRIGSRC_DTR               # 触发源
        if self.ui.Edge_2.currentText() == 'Rising':
            triggerSlope = TriggerSlope.TRIGDIR_POSITIVE
        else:
            triggerSlope = TriggerSlope.TRIGDIR_NEGATIVE
                    # 触发方向
            
        triggerCount = 0                               # infinite触发次数
        triggerSensitivity = self.ui.TrigDura.value()               # 触发灵敏度 单位：ns
        error_code = Functions.ArtScope_ConfigureTriggerDigital(self.taskHandle, triggerSource, triggerSlope, triggerCount, triggerSensitivity)
        if error_code < 0:
            Functions.ArtScope_Close(self.taskHandle)
            check_for_error(error_code)
            return 'D trigger failed'
        
        #配置触发输出
        if self.ui.AUXIO_2.currentText() == 'ENABLE':
            triggerOutWidth = self.ui.TrigOutDura.value()       # 触发输出脉冲宽度 单位：ns
            if self.ui.AUXEDGE_2.currentText() == 'Rising':
                triggerOutPolarity = TriggerOutPolarity.TRIGOUT_POLAR_POSITIVE  # 触发输出极性
            else:
                triggerOutPolarity = TriggerOutPolarity.TRIGOUT_POLAR_NEGATIVE  # 触发输出极性
            error_code = Functions.ArtScope_ExportTrigger(self.taskHandle, triggerOutWidth, triggerOutPolarity)
            if error_code < 0:
                Functions.ArtScope_Close(self.taskHandle)
                check_for_error(error_code)
                return 'D export trigger failed'
        return 'D config success'
        
        
    def StartAcquire(self):
        #获取实际使能的通道个数
        numWfms = ctypes.c_uint32(0)                            # 返回的实际参与采集的通道个数
        error_code = Functions.ArtScope_ActualNumWfms(self.taskHandle, numWfms)
        if error_code < 0:
            Functions.ArtScope_Close(self.taskHandle)
            check_for_error(error_code)
            print( 'D get channels failed')
        
        #初始化采集任务
        error_code = Functions.ArtScope_InitiateAcquisition(self.taskHandle)
        if error_code < 0:
            Functions.ArtScope_Close(self.taskHandle)
            check_for_error(error_code)
            print( 'D Init acquire failed')
        # print('Init acqui')
        #获取实际采集长度 这个长度用于读取数据时开辟数据缓冲区时使用
        #读取的数据长度可以大于或小于或等于此长度
        #当读取的数据长度小于此长度时，实际读取的个数是读取的长度
        #当读取的数据长度等于此长度时，实际读取的个数是读取的长度
        #当读取的数据长度大于此长度时，实际读取的个数是实际采样长度
        actualRecordLength = ctypes.c_uint32(0)                  # 返回的实际每通道采集数据长度
        error_code = Functions.ArtScope_ActualRecordLength(self.taskHandle, actualRecordLength)
        # print('actual samples: ', actualRecordLength.value)
        if error_code < 0:
            Functions.ArtScope_Close(self.taskHandle)
            check_for_error(error_code)
            rprint( 'D get Aline samples failed')
        # get how many Alines per Bline
        if self.ui.ACQMode.currentText() in ['SingleAline', 'RptAline']:
            if self.ui.Laser.currentText() == 'Axsun100k':
                self.Aline_frq = 100000
                # total Alines to be acquired per scan
                AlinesPerBline = np.int32(self.Aline_frq/self.ui.FPSAline.value())
                # number Alines * total samples * channels
            else:
                return ' laser invalid, kill console to restart'
            # self.usefulLength = self.ui.XforAline.value() * actualRecordLength.value * numWfms.value
        else:
            # total ALines to be acquired per Bline, this include galvo fly-backs
            AlinesPerBline = self.ui.AlineAVG.value()*self.ui.Xsteps.value()+self.ui.PreClock.value()*2+self.ui.PostClock.value()
            # from total Alines remove Galvo fly-backs. This is (Alines per bline * Aline rpt + 100) * total samples * channels
            # self.usefulLength = (self.ui.AlineAVG.value()*self.ui.Xsteps.value()+self.ui.PreClock.value()*2) * actualRecordLength.value * numWfms.value
                
        # all samples in all Alines, include galvo fly-backs
        sumLength = actualRecordLength.value * AlinesPerBline * numWfms.value
        # self.waveformPtr = np.zeros(self.sumLength, dtype=np.uint16)
        
        for ii in range(self.memoryCount):
              if self.ui.ACQMode.currentText() in ['SingleBline', 'SingleAline']:
                  NBlines = self.ui.BlineAVG.value()
                  # self.Memory[ii]=np.zeros([self.NBlines, self.usefulLength], dtype = np.uint16)
              if self.ui.ACQMode.currentText() in ['RptBline', 'RptAline']:
                  NBlines = CONTINUOUS
                  # self.Memory[ii]=np.zeros([self.ui.BlineAVG.value(), self.usefulLength], dtype = np.uint16)
              elif self.ui.ACQMode.currentText() in ['SingleCscan', 'SurfScan','SurfScan+Slice']:
                  NBlines = self.ui.BlineAVG.value() * self.ui.Ysteps.value()
                  # self.Memory[ii]=np.zeros([self.NBlines, self.usefulLength], dtype = np.uint16)
                 

        # print('configure ART8912 success\n')
        
        data_packages = 1 # number data packages returned from digitizer
        timeout = self.ui.TriggerTimeout_2.value()              # 数据读取超时时间 单位：s
        readLength = sumLength                         # 数据读取长度
        # usefulLength = self.usefulLength
        wfmInfo = ArtScope_wfmInfo()                            # 返回的包含实际读取长度和原码值转电压值相关参数的结构体
        # wfmInfo.actualSamples = 0
        # wfmInfo.pAvailSampsPoints = 0
        # print('get wfminfo')
        blinesCompleted = 0 # number Blines read
        NACQ = NBlines if NBlines != CONTINUOUS else self.ui.BlineAVG.value() # total number of Blines to be read per data_package
        #开始采集任务
        error_code = Functions.ArtScope_StartAcquisition(self.taskHandle)
        message = 'D using memory loc: '+ str(self.MemoryLoc)
        print(message)
        self.ui.PrintOut.append(message)
        self.log.write(message)
        while blinesCompleted < NBlines:
            # 8位的卡需要调用ArtScope_FetchBinary8，同时定义数据缓冲区数据类型为无符号8位数据
            # start = time.time()
            try:
                error_code = Functions.ArtScope_FetchBinary16(self.taskHandle, timeout, readLength, self.Memory[self.MemoryLoc][blinesCompleted % NACQ], wfmInfo)
            except Exception as error:
                message = 'Blines collected: '+str( blinesCompleted)+ \
                      'Blines configured: '+str( NACQ)+ \
                      '\n'+ error+ '\nstopping acquisition for Digitizer\n'
                print(message)
                self.ui.PrintOut.append(message)
                self.log.write(message)
                break
            
            # if error_code < 0:
            #     Functions.ArtScope_StopAcquisition(self.taskHandle)
            #     Functions.ArtScope_Close(self.taskHandle)
            #     check_for_error(error_code)
            #     return 'D fetch Bline failed'
            blinesCompleted+=1
            
            if blinesCompleted % NACQ ==0:
                # print('sending data back', num)
                data_packages+=1
                an_action = DbackAction(self.MemoryLoc)
                self.DbackQueue.put(an_action)
                self.MemoryLoc = (self.MemoryLoc+1) % self.memoryCount
            # check if user stopped acquisition
            try:
                self.StopDQueue.get_nowait()
                self.ui.statusbar.showMessage('successfully stopped Digitizer...')
                self.ui.PrintOut.append('successfully stopped Digitizer...')
                self.log.write('successfully stopped Digitizer...')
                # self.CloseTask()
                message = str( data_packages)+ ' data packages returned by digitizer\n'
                print(message)
                self.ui.PrintOut.append(message)
                self.log.write(message)
                break
            except:
                pass
            # print(round(time.time()-start,4))
        print('finish acquiring')
        self.ui.PrintOut.append('finish acquiring')
        self.log.write('finish acquiring')
        #停止采集任务
        error_code = Functions.ArtScope_StopAcquisition(self.taskHandle)
        # if error_code < 0:
        #     Functions.ArtScope_ReleaseAcquisition(self.taskHandle)
        #     Functions.ArtScope_Close(self.taskHandle)
        #     return 'D stop acquire failed'
    
        #释放采集任务
        error_code = Functions.ArtScope_ReleaseAcquisition(self.taskHandle)
        if error_code < 0:
            Functions.ArtScope_Close(self.taskHandle)
            return 'D release acquire failed'
            
    def UninitBoard(self):
        #释放设备
        error_code = Functions.ArtScope_Close(self.taskHandle)
        print('closed digitizer')
        
    def atomBoard(self):
        # print('start')
        self.InitBoard()
        # print('Init')
        self.ConfigureBoard()
        # print('config')
        self.StartAcquire()
        # print('start')
        self.UninitBoard()
        # print('uninit')
        
    def simData(self):
        if self.ui.ACQMode.currentText() in ['SingleAline', 'RptAline']:
            if self.ui.Laser.currentText() == 'Axsun100k':
                self.Aline_frq = 100000
                # total Alines to be acquired per scan
                AlinesPerBline = np.int32(self.Aline_frq/self.ui.FPSAline.value())
                # number Alines * total samples * channels
            self.usefulLength = self.ui.XforAline.value() * self.ui.PostSamples_2.value() * 1
        else:
            # total ALines to be acquired per Bline, this include galvo fly-backs
            AlinesPerBline = self.ui.AlineAVG.value()*self.ui.Xsteps.value()+self.ui.PreClock.value()*2+self.ui.PostClock.value()
            # from total Alines remove Galvo fly-backs. This is (Alines per bline * Aline rpt + 100) * total samples * channels
            self.usefulLength = (self.ui.AlineAVG.value()*self.ui.Xsteps.value()+self.ui.PreClock.value()*2) * self.ui.PostSamples_2.value() * 1
                
        # all samples in all Alines, include galvo fly-backs
        self.sumLength = self.ui.PostSamples_2.value() * AlinesPerBline * 1
        self.waveformPtr = np.zeros(self.sumLength, dtype=np.uint16)
        
        for ii in range(self.memoryCount):
              if self.ui.ACQMode.currentText() in ['SingleBline', 'SingleAline']:
                  self.NBlines = self.ui.BlineAVG.value()
                  # self.Memory[ii]=np.zeros([self.NBlines, self.usefulLength], dtype = np.uint16)
              if self.ui.ACQMode.currentText() in ['RptBline', 'RptAline']:
                  self.NBlines = CONTINUOUS
                  # self.Memory[ii]=np.zeros([self.ui.BlineAVG.value(), self.usefulLength], dtype = np.uint16)
              elif self.ui.ACQMode.currentText() in ['SingleCscan', 'SurfScan','SurfScan+Slice']:
                  self.NBlines = self.ui.BlineAVG.value() * self.ui.Ysteps.value()
                  # self.Memory[ii]=np.zeros([self.NBlines, self.usefulLength], dtype = np.uint16)
                 
        blinesCompleted = 0
        NACQ = self.NBlines if self.NBlines != CONTINUOUS else self.ui.BlineAVG.value()
        num = 1
        print('D using memory loc: ',self.MemoryLoc)
        # print(self.Memory[self.MemoryLoc].shape)
        self.waveformPtr = np.random.random(self.sumLength)*2000
        while blinesCompleted < self.NBlines:
            # 8位的卡需要调用ArtScope_FetchBinary8，同时定义数据缓冲区数据类型为无符号8位数据
            # start = time.time()
            # self.waveformPtr = np.random.random(self.sumLength)*2000
        # 
            
            
            self.Memory[self.MemoryLoc][blinesCompleted % NACQ] = self.waveformPtr
            blinesCompleted+=1
            
            if blinesCompleted % NACQ ==0:
                # print('sending data back', num)
                num+=1
                an_action = DbackAction(self.MemoryLoc)
                self.DbackQueue.put(an_action)
                self.MemoryLoc = (self.MemoryLoc+1) % self.memoryCount
            # get stop commend from BONE thread
            try:
                self.StopDQueue.get(timeout=0.001)
                self.ui.statusbar.showMessage('successfully stopped Digitizer...')
                self.ui.PrintOut.append('successfully stopped Digitizer...')
                self.log.write('successfully stopped Digitizer...')
                # self.CloseTask()
                message = str( num)+ ' data packages returned by digitizer\n'
                print(message)
                self.ui.PrintOut.append(message)
                self.log.write(message)
                break
            except:
                pass
            # print(round(time.time()-start,4))
        print('finish acquiring')
        self.ui.PrintOut.append('finish acquiring')
        self.log.write('finish acquiring')