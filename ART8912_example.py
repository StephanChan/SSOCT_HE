# -*- coding: utf-8 -*-
"""
Created on Tue Jan 23 17:06:32 2024

@author: admin
"""
import sys
import numpy as np
sys.path.append(r"C:\\Program Files (x86)\\ART Technology\\ArtScope\\Samples\\Python\\")

from ART_SCOPE_Lib.functions import Functions
from ART_SCOPE_Lib.constants import *
from ART_SCOPE_Lib.lib import *
from ART_SCOPE_Lib.errors import check_for_error, ArtScopeError


class ART8912():
    def __init__(self):
        super().__init__()

        self.exit_message = 'Digitizer thread successfully exited'

        
    def ConfigureBoard(self):
        taskName = "ART8912"  # 设备名 DMC管理器里面的名称
        self.taskHandle = lib_importer.task_handle(0)                # 设备句柄
        #创建任务
        error_code = Functions.ArtScope_init(taskName, self.taskHandle)
        if error_code < 0:
            print('init failed\n')
            check_for_error(error_code)
        
        #配置采集模式
        acquisitionMode = SampleMode.CONTINUOUS                     # 采集模式 连续采集模式
        error_code = Functions.ArtScope_ConfigureAcquisitionMode(self.taskHandle, acquisitionMode)
        
        #配置垂直参数

        channelName = '0' 
            
        verticalRange = InputRange.RANGE_2VPP       
                       # 通道量程
        verticalOffset = 0                                      # 通道偏置
        verticalCoupling = CouplingType.DC                      # 通道耦合
        probeAttenuation = 1                                    # 探头衰减 暂时无效
        enabled = 1                                             # 通道使能
        error_code = Functions.ArtScope_ConfigureVertical(self.taskHandle, channelName, verticalRange, verticalOffset, verticalCoupling, probeAttenuation, enabled)
        if error_code < 0:
            print('config vertical failed\n')
            Functions.ArtScope_Close(self.taskHandle)
            check_for_error(error_code)
        
        #配置水平参数

        minSampleRate = 250000000.0  
                                    # 采样率
        minRecordLength = 1536           # 最小采样长度
        refPosition = 0                                         # 触发位置 0-后触发 100-预触发 0~100-中间触发
        error_code = Functions.ArtScope_ConfigureHorizontalTiming(self.taskHandle, minSampleRate, minRecordLength, refPosition)
        if error_code < 0:
            print('config horizontal failed\n')
            Functions.ArtScope_Close(self.taskHandle)
            check_for_error(error_code)
        
        #配置边沿触发
        triggerSource = TriggerSource.TRIGSRC_DTR               # 触发源

        triggerSlope = TriggerSlope.TRIGDIR_NEGATIVE
                    # 触发方向
        AlinesPerBline = 1000
        
        triggerCount = 0                               # infinite触发次数
        triggerSensitivity = 50               # 触发灵敏度 单位：ns
        error_code = Functions.ArtScope_ConfigureTriggerDigital(self.taskHandle, triggerSource,  triggerSlope, triggerCount, triggerSensitivity)
        if error_code < 0:
            print('config trigger failed\n')
            Functions.ArtScope_Close(self.taskHandle)
            check_for_error(error_code)
        
        #配置触发输出
        if True:
            triggerOutWidth = 100       # 触发输出脉冲宽度 单位：ns

            triggerOutPolarity = TriggerOutPolarity.TRIGOUT_POLAR_POSITIVE  # 触发输出极性

            error_code = Functions.ArtScope_ExportTrigger(self.taskHandle, triggerOutWidth, triggerOutPolarity)
            if error_code < 0:
                print('config trigger output failed\n')
                Functions.ArtScope_Close(self.taskHandle)
                check_for_error(error_code)
        
        #获取实际使能的通道个数
        numWfms = ctypes.c_uint32(0)                            # 返回的实际参与采集的通道个数
        error_code = Functions.ArtScope_ActualNumWfms(self.taskHandle, numWfms)
        print('channels configed: ',numWfms.value)
        if error_code < 0:
            print('get channels failed\n')
            Functions.ArtScope_Close(self.taskHandle)
            check_for_error(error_code)
        
        #初始化采集任务
        error_code = Functions.ArtScope_InitiateAcquisition(self.taskHandle)
        if error_code < 0:
            print('Init acquisition failed\n')
            Functions.ArtScope_Close(self.taskHandle)
            check_for_error(error_code)
        
        #获取实际采集长度 这个长度用于读取数据时开辟数据缓冲区时使用
        #读取的数据长度可以大于或小于或等于此长度
        #当读取的数据长度小于此长度时，实际读取的个数是读取的长度
        #当读取的数据长度等于此长度时，实际读取的个数是读取的长度
        #当读取的数据长度大于此长度时，实际读取的个数是实际采样长度
        self.actualRecordLength = ctypes.c_uint32(0)                  # 返回的实际每通道采集数据长度
        error_code = Functions.ArtScope_ActualRecordLength(self.taskHandle, self.actualRecordLength)
        print('actual record length: ',self.actualRecordLength.value)
        if error_code < 0:
            print('get record length failed\n')
            Functions.ArtScope_Close(self.taskHandle)
            check_for_error(error_code)
        
        #开辟数据存储空间
        self.sumLength = self.actualRecordLength.value * AlinesPerBline * numWfms.value
        self.waveformPtr = np.zeros(self.sumLength, dtype=np.uint16)
        
        self.memoryCount = 2
        self.Memory = list(range(self.memoryCount))
        for ii in range(self.memoryCount):

                 self.NBlines = 200
                 self.Memory[ii]=np.zeros([self.NBlines, self.sumLength], dtype = np.uint16)
                 
        self.MemoryLoc = 0
        
    def StartAcquire(self):
        #开始采集任务
        error_code = Functions.ArtScope_StartAcquisition(self.taskHandle)
    
        timeout = 1              # 数据读取超时时间 单位：s
        readLength = self.sumLength                        # 数据读取长度
        wfmInfo = ArtScope_wfmInfo()                            # 返回的包含实际读取长度和原码值转电压值相关参数的结构体
        wfmInfo.actualSamples = 0
        wfmInfo.pAvailSampsPoints = 0
        
        blinesCompleted = 0
        NACQ = self.NBlines
        
        while blinesCompleted < NACQ:
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
                print('fetch data failed\n')
                Functions.ArtScope_StopAcquisition(self.taskHandle)
                Functions.ArtScope_Close(self.taskHandle)
                check_for_error(error_code)
                
            self.Memory[self.MemoryLoc][blinesCompleted % NACQ][:] = self.waveformPtr
            blinesCompleted+=1
            
            if blinesCompleted % NACQ ==0:
                # print('sending data back')
                # an_action = DbackAction(self.MemoryLoc)
                # self.DbackQueue.put(an_action)
                print(self.Memory[self.MemoryLoc].shape)
                print(self.Memory[self.MemoryLoc][0,:])
                self.MemoryLoc = (self.MemoryLoc+1) % self.memoryCount

            
            
        #停止采集任务
        error_code = Functions.ArtScope_StopAcquisition(self.taskHandle)
        if error_code < 0:
            print('stop acquisition failed\n')
            Functions.ArtScope_ReleaseAcquisition(self.taskHandle)
            Functions.ArtScope_Close(self.taskHandle)
            
    def StopAcquire(self):
        #释放采集任务
        error_code = Functions.ArtScope_ReleaseAcquisition(self.taskHandle)
        if error_code < 0:
            Functions.ArtScope_Close(self.taskHandle)
        
        #释放设备
        error_code = Functions.ArtScope_Close(self.taskHandle)
        

if __name__ == "__main__":

    example = ART8912()
    example.ConfigureBoard()
    example.StartAcquire()
    example.StopAcquire()