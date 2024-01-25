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

        self.exit_message = 'Digitizer thread successfully exited'

        
    def run(self):
        self.QueueOut()
        
    def QueueOut(self):
        self.item = self.queue.get()
        while self.item.action != 'exit':
            try:
                if self.item.action == 'ConfigureBoard':
                    self.ConfigureBoard()
                elif self.item.action == 'StartAcquire':
                    self.StartAcquire()
                elif self.item.action == 'CloseTask':
                    self.CloseTask()
                    
                else:
                    self.ui.statusbar.showMessage('Digitizer thread is doing something invalid: '+self.item.action)
            except Exception as error:
                print("\nAn error occurred:", error,' skip the Digitizer action\n')
                print(traceback.format_exc())
            self.item = self.queue.get()
        print(self.exit_message)
        
    def ConfigureBoard(self):
        taskName = "ART8912"  # 设备名 DMC管理器里面的名称
        self.taskHandle = lib_importer.task_handle(0)                # 设备句柄
        #创建任务
        error_code = Functions.ArtScope_init(taskName, self.taskHandle)
        if error_code < 0:
            check_for_error(error_code)
        
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
        
        #获取实际使能的通道个数
        numWfms = ctypes.c_uint32(0)                            # 返回的实际参与采集的通道个数
        error_code = Functions.ArtScope_ActualNumWfms(self.taskHandle, numWfms)
        if error_code < 0:
            Functions.ArtScope_Close(self.taskHandle)
            check_for_error(error_code)
        
        #初始化采集任务
        error_code = Functions.ArtScope_InitiateAcquisition(self.taskHandle)
        if error_code < 0:
            Functions.ArtScope_Close(self.taskHandle)
            check_for_error(error_code)
        
        #获取实际采集长度 这个长度用于读取数据时开辟数据缓冲区时使用
        #读取的数据长度可以大于或小于或等于此长度
        #当读取的数据长度小于此长度时，实际读取的个数是读取的长度
        #当读取的数据长度等于此长度时，实际读取的个数是读取的长度
        #当读取的数据长度大于此长度时，实际读取的个数是实际采样长度
        actualRecordLength = ctypes.c_uint32(0)                  # 返回的实际每通道采集数据长度
        error_code = Functions.ArtScope_ActualRecordLength(self.taskHandle, actualRecordLength)
        print('actual samples: ', actualRecordLength.value)
        if error_code < 0:
            Functions.ArtScope_Close(self.taskHandle)
            check_for_error(error_code)
        self.ui.PostSamples_2.setValue(actualRecordLength.value)
        
        #开辟数据存储空间
        if self.ui.ACQMode.currentText() in ['SingleAline', 'RptAline']:
            if self.ui.Laser.currentText() == 'Axsun100k':
                self.Aline_frq = 100000
                AlinesPerBline = np.int32(self.Aline_frq*0.1)
            self.usefulLength = 10 * actualRecordLength.value * numWfms.value
        else:
            AlinesPerBline = self.ui.AlineAVG.value()*self.ui.Xsteps.value()+self.ui.PreClock.value()*2+self.ui.PostClock.value()
            self.usefulLength = (self.ui.AlineAVG.value()*self.ui.Xsteps.value()+self.ui.PreClock.value()) * actualRecordLength.value * numWfms.value
                
        
        self.sumLength = actualRecordLength.value * AlinesPerBline * numWfms.value
        self.waveformPtr = np.zeros(self.sumLength, dtype=np.uint16)
        
        
        for ii in range(self.memoryCount):
             if self.ui.ACQMode.currentText() in ['SingleBline', 'SingleAline']:
                 self.NBlines = self.ui.BlineAVG.value()
                 self.Memory[ii]=np.zeros([self.NBlines, self.usefulLength], dtype = np.uint16)
             if self.ui.ACQMode.currentText() in ['RptBline', 'RptAline']:
                 self.NBlines = CONTINUOUS
                 self.Memory[ii]=np.zeros([self.ui.BlineAVG.value(), self.usefulLength], dtype = np.uint16)
             elif self.ui.ACQMode.currentText() in ['SingleCscan', 'SurfScan','SurfScan+Slice']:
                 self.NBlines = self.ui.BlineAVG.value() * self.ui.Ysteps.value()
                 self.Memory[ii]=np.zeros([self.NBlines, self.usefulLength], dtype = np.uint16)
                 
        self.MemoryLoc = 0
        print('configure ART8912 success\n')
        
    def StartAcquire(self):

        timeout = self.ui.TriggerTimeout_2.value()              # 数据读取超时时间 单位：s
        readLength = self.sumLength                         # 数据读取长度
        usefulLength = self.usefulLength
        wfmInfo = ArtScope_wfmInfo()                            # 返回的包含实际读取长度和原码值转电压值相关参数的结构体
        wfmInfo.actualSamples = 0
        wfmInfo.pAvailSampsPoints = 0
        
        blinesCompleted = 0
        NACQ = self.NBlines if self.NBlines != CONTINUOUS else self.ui.BlineAVG.value()
        #开始采集任务
        error_code = Functions.ArtScope_StartAcquisition(self.taskHandle)
        while blinesCompleted < self.NBlines:
            # 8位的卡需要调用ArtScope_FetchBinary8，同时定义数据缓冲区数据类型为无符号8位数据
            try:
                error_code = Functions.ArtScope_FetchBinary16(self.taskHandle, timeout, readLength, self.waveformPtr, wfmInfo)
            except Exception as error:
                # TODO: if timeout, break this inner while loop
                print('Blines collected: ', blinesCompleted, \
                      'Blines configured: ', NACQ, \
                      '\n', error, '\nstopping acquisition for Digitizer\n')
                break
            
            if error_code < 0:
                Functions.ArtScope_StopAcquisition(self.taskHandle)
                Functions.ArtScope_Close(self.taskHandle)
                check_for_error(error_code)
                
            self.Memory[self.MemoryLoc][blinesCompleted % NACQ][:] = self.waveformPtr[0:usefulLength]
            blinesCompleted+=1
            
            if blinesCompleted % NACQ ==0:
                # print('sending data back')
                an_action = DbackAction(self.MemoryLoc)
                self.DbackQueue.put(an_action)
                self.MemoryLoc = (self.MemoryLoc+1) % self.memoryCount

            # get stop commend from BONE thread
            try:
                self.StopDQueue.get(timeout=0.001)
                print('\nsuccessfully caught that stop signal for Digitizer\n')
                break
            except:
                pass
            
        #停止采集任务
        error_code = Functions.ArtScope_StopAcquisition(self.taskHandle)
        if error_code < 0:
            Functions.ArtScope_ReleaseAcquisition(self.taskHandle)
            Functions.ArtScope_Close(self.taskHandle)
            
    def CloseTask(self):
        #释放采集任务
        error_code = Functions.ArtScope_ReleaseAcquisition(self.taskHandle)
        if error_code < 0:
            Functions.ArtScope_Close(self.taskHandle)
        
        #释放设备
        error_code = Functions.ArtScope_Close(self.taskHandle)
        