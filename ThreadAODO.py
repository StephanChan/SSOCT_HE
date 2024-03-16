# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 16:51:20 2023

@author: admin
"""
###########################################
# 25000 steps per revolve
global STEPS
STEPS = 25000
# 2mm per revolve
global DISTANCE
DISTANCE = 2

global Galvo_bias
Galvo_bias = 3

###########################################
from PyQt5.QtCore import  QThread
import nidaqmx as ni
from nidaqmx.constants import AcquisitionType as Atype
from nidaqmx.constants import Edge
from Generaic_functions import GenAODO
import time
import traceback
import numpy as np

# stage enable/disable digital value
# enable = 0
global XDISABLE
XDISABLE = 1
global YDISABLE
YDISABLE = 4
global ZDISABLE
ZDISABLE = 16

# stage forwared backward digital value
global XFORWARD
XFORWARD = 2
global YFORWARD
YFORWARD = 8
global ZFORWARD
ZFORWARD = 32
# backward = 0

# stage channel digital value
global XCH
XCH = 1
global YCH
YCH = 2
global ZCH
ZCH = 4

class AODOThread(QThread):
    def __init__(self):
        super().__init__()
        self.AOtask = None
        self.DOtask = None
    
    def run(self):
        self.Init_Stages()
        self.QueueOut()
        
    def QueueOut(self):
        self.item = self.queue.get()
        while self.item.action != 'exit':
            try:
                if self.item.action == 'Xmove2':
                    self.Move(axis = 'X')
                elif self.item.action == 'Ymove2':
                    self.Move(axis = 'Y')
                elif self.item.action == 'Zmove2':
                    self.Move(axis = 'Z')
                elif self.item.action == 'Init':
                    self.Init_Stages()
                elif self.item.action == 'ConfigAODO':
                    self.ConfigAODO()

                elif self.item.action == 'StartOnce':
                    self.StartOnce(self.item.direction)
                elif self.item.action == 'StartContinuous':
                    self.StartContinuous()
                elif self.item.action == 'WaitDone':
                    self.WaitDone()
                elif self.item.action == 'StopContinuous':
                    self.StopContinuous()
                elif self.item.action == 'CloseTask':
                    self.CloseTask()
                elif self.item.action == 'centergalvo':
                    self.centergalvo()
                else:
                    self.ui.statusbar.showMessage('AODO thread is doing something undefined: '+self.item.action)
            except Exception:
                self.ui.statusbar.showMessage("\nAn error occurred,"+" skip the AODO action\n")
                print(traceback.format_exc())
            self.item = self.queue.get()
        self.ui.statusbar.showMessage('AODO thread successfully exited')

    def Init_Stages(self):
        self.Xpos = self.ui.XPosition.value()
        self.Ypos = self.ui.YPosition.value()
        self.Zpos = self.ui.ZPosition.value()
        current_message = self.ui.statusbar.currentMessage()
        self.ui.statusbar.showMessage(current_message+"Stage position updated...")
        # print('X pos: ',self.Xpos)
        # print('Y pos: ',self.Ypos)
        # print('Z pos: ',self.Zpos)
        
    def ConfigAODO(self):
        if self.ui.Laser.currentText() == 'Axsun100k':
            self.Aline_freq = 100000
        else:
            return 'Laser invalid!'
        self.CloseTask()

        DOwaveform,AOwaveform,status = GenAODO(mode=self.ui.ACQMode.currentText(), \
                                               Aline_frq = self.Aline_freq, \
                                               XStepSize = self.ui.XStepSize.value(), \
                                               XSteps = self.ui.Xsteps.value(), \
                                               AVG = self.ui.AlineAVG.value(), \
                                               bias = self.ui.XBias.value(), \
                                               obj = self.ui.Objective.currentText(), \
                                               preclocks = self.ui.PreClock.value(), \
                                               postclocks = self.ui.PostClock.value(), \
                                               YStepSize = self.ui.YStepSize.value(), \
                                               YSteps =  self.ui.Ysteps.value(), \
                                               BVG = self.ui.BlineAVG.value())
        self.AOtask = ni.Task('AOtask')
        
        # Configure Analog output task for Galvo control
        self.AOtask.ao_channels.add_ao_voltage_chan(physical_channel='AODO/ao0', \
                                              min_val=- 5.0, max_val=5.0, \
                                              units=ni.constants.VoltageUnits.VOLTS)
        if self.ui.ACQMode.currentText() in ['RptBline', 'RptAline']:
            self.AOtask.timing.cfg_samp_clk_timing(rate=self.Aline_freq, \
                                            source=self.ui.ClockTerm.toPlainText(), \
                                                active_edge= Edge.FALLING,\
                                              sample_mode=Atype.CONTINUOUS,samps_per_chan=len(AOwaveform))
        else:
            self.AOtask.timing.cfg_samp_clk_timing(rate=self.Aline_freq, \
                                            source=self.ui.ClockTerm.toPlainText(), \
                                              sample_mode=Atype.FINITE,samps_per_chan=len(AOwaveform))
        if self.Digitizer == 'ATS9351':      
            self.AOtask.triggers.sync_type.MASTER = True
        elif self.Digitizer == 'ART8912':
            self.AOtask.triggers.start_trigger.cfg_dig_edge_start_trig("/AODO/PFI1")

        # print(len(DOwaveform))
            
        self.AOtask.write(AOwaveform, auto_start = False)
        # Confiture Digital output task for stage control and digitizer trigger enabling
        
        if self.ui.ACQMode.currentText() in ['SingleCscan','SurfScan','SurfScan+Slice'] or self.Digitizer == 'ATS9351':
            self.DOtask = ni.Task('DOtask')
            self.DOtask.do_channels.add_do_chan(lines='AODO/port0/line0:7')
            if self.ui.ACQMode.currentText() in ['RptBline', 'RptAline']:
                self.DOtask.timing.cfg_samp_clk_timing(rate=self.Aline_freq, \
                                                source=self.ui.ClockTerm.toPlainText(), \
                                                    active_edge= Edge.FALLING,\
                                                  sample_mode=Atype.CONTINUOUS,samps_per_chan=len(DOwaveform))
            else:
                self.DOtask.timing.cfg_samp_clk_timing(rate=self.Aline_freq, \
                                                source=self.ui.ClockTerm.toPlainText(), \
                                                  sample_mode=Atype.FINITE,samps_per_chan=len(DOwaveform))
           
            if self.Digitizer == 'ATS9351':      
                self.DOtask.triggers.sync_type.SLAVE = True
            elif self.Digitizer == 'ART8912':
                self.DOtask.triggers.start_trigger.cfg_dig_edge_start_trig("/AODO/PFI1")
            
            self.DOtask.write(DOwaveform, auto_start = False)
            # print(DOwaveform.shape)
            steps = np.sum(DOwaveform)/25000.0*2/pow(2,1)
            print('distance per Cscan: ',steps,'mm')
        return 'AODO configuration success'
    
            
    def StartOnce(self, direction):
        if self.ui.ACQMode.currentText() in ['SingleCscan','SurfScan','SurfScan+Slice'] or self.Digitizer == 'ATS9351':
            settingtask = ni.Task('setting')
            settingtask.do_channels.add_do_chan(lines='AODO/port2/line0:7')
            tmp = np.uint32(direction * YFORWARD + XDISABLE + ZDISABLE)
            settingtask.write(tmp, auto_start = True)
            self.DOtask.start()
        self.AOtask.start()
        # try:
        self.AOtask.wait_until_done(timeout = 60)
        self.AOtask.stop()
        if self.ui.ACQMode.currentText() in ['SingleCscan','SurfScan','SurfScan+Slice'] or self.Digitizer == 'ATS9351':
            self.DOtask.stop()
            settingtask.write(XDISABLE+ YDISABLE+ ZDISABLE, auto_start = True)
            settingtask.stop()
            settingtask.close()
            # update GUI Y stage position
            Ystep = self.ui.YStepSize.value()*self.ui.BlineAVG.value()*self.ui.Ysteps.value()/1000.0
            self.Ypos = self.Ypos+Ystep if direction == 1 else self.Ypos-Ystep
            self.ui.YPosition.setValue(self.Ypos)
            # print(self.Ypos)

            
    def StartContinuous(self):
        if self.AOtask.is_task_done():
            if self.Digitizer == 'ATS9351':   
                self.DOtask.start()
            self.AOtask.start()
        else:
            pass
        
    def WaitDone(self):
        self.AOtask.wait_until_done()
        
    def StopContinuous(self):
        self.AOtask.stop()
        if self.Digitizer == 'ATS9351':   
            self.DOtask.stop()
        
    def CloseTask(self):
        try:
            while not self.AOtask.is_task_done():
                time.sleep(0.5)
            self.AOtask.close()
            self.DOtask.close()
            
        except:
            pass
        return 'AODO write task done'
                
    def centergalvo(self):
        with ni.Task('AO task') as AOtask, ni.Task('DO task') as DOtask:
            AOtask.ao_channels.add_ao_voltage_chan(physical_channel='AODO/ao0', \
                                                  min_val=- 10.0, max_val=10.0, \
                                                  units=ni.constants.VoltageUnits.VOLTS)
            AOtask.write(Galvo_bias, auto_start = True)
            DOtask.do_channels.add_do_chan(lines='AODO/port0/line0:7')
            DOtask.write(0, auto_start = True)
            # AOtask.close()
    def stagewave_ramp(self, distance):
        # generate stage movement that ramps up and down speed so that motor won't miss signal at beginning and end
        # how to do that: motor is driving by low->high digital transition
        # ramping up: make the interval between two highs with long time at the beginning, then gradually goes down.vice versa for ramping down
        if np.abs(distance) > 0.05:
            max_interval = 1000
        else:
            max_interval = 5
        ramp_up_interval = np.arange(max_interval,0,-10)
        ramp_down_interval = np.arange(1,max_interval+1,10)
        ramping_highs = np.sum(len(ramp_down_interval)+len(ramp_up_interval)) # number steps used in ramping up and down process
        total_highs = np.uint32(STEPS//DISTANCE*np.abs(distance))
        
        # ramping up waveform generation
        ramp_up_waveform = np.zeros(np.sum(ramp_up_interval))
        time_lapse = -1
        for interval in ramp_up_interval:
            time_lapse = time_lapse + interval
            ramp_up_waveform[time_lapse] = 1

        # ramping down waveform generation
        ramp_down_waveform = np.zeros(np.sum(ramp_down_interval))
        time_lapse = -1
        for interval in ramp_down_interval:
            time_lapse = time_lapse + interval
            ramp_down_waveform[time_lapse] = 1
            
        # normal speed waveform
        DOwaveform = np.ones([total_highs - ramping_highs, 2],dtype = np.uint32)
        DOwaveform[:,1] = 0
        DOwaveform=DOwaveform.flatten()
        
        # append all arrays
        DOwaveform = np.append(ramp_up_waveform,DOwaveform)
        DOwaveform = np.append(DOwaveform,ramp_down_waveform)
        # print('total highs: ',np.sum(DOwaveform))
        # from matplotlib import pyplot as plt
        # plt.figure()
        # plt.plot(DOwaveform[0:5000])
        return DOwaveform
        
    def Move(self, axis = 'X'):
        ###########################
        # you can only move one axis at a time
        ###########################
        # X axis use port 2 line 0-1 for enable and direction, use port 0 line 0 for steps
        # Y axis use port 2 line 2-3 for enable and direction, use port 0 line 1 for steps
        # Z axis use port 2 line 4-5 for enable and direction, use port 0 line 2 for steps
        # enable low enables, enable high disables
        direction = 0
        if axis == 'X':
            line = XCH
            speed = self.ui.XSpeed.value()
            distance = self.ui.XPosition.value()-self.Xpos
            if distance > 0:
                direction = XFORWARD
            enable = YDISABLE + ZDISABLE
        elif axis == 'Y':
            line = YCH
            speed = self.ui.YSpeed.value()
            distance = self.ui.YPosition.value()-self.Ypos
            if distance > 0:
                direction = YFORWARD
            enable = XDISABLE + ZDISABLE
        elif axis == 'Z':
            line = ZCH
            speed = self.ui.ZSpeed.value()
            distance = self.ui.ZPosition.value()-self.Zpos
            if distance < 0:
                direction = ZFORWARD
            enable = XDISABLE + YDISABLE
            
        if np.abs(distance) < 0.001:
            self.StagebackQueue.put(0)
            return
        with ni.Task('Move task') as DOtask, ni.Task('setting') as settingtask:
            settingtask.do_channels.add_do_chan(lines='AODO/port2/line0:7')
            settingtask.write(direction + enable, auto_start = True)
            DOwaveform = self.stagewave_ramp(distance)
            DOwaveform = np.uint32(DOwaveform * line)
            DOtask.do_channels.add_do_chan(lines='AODO/port0/line0:7')
            DOtask.timing.cfg_samp_clk_timing(rate=STEPS*2//DISTANCE*speed, \
                                              active_edge= Edge.FALLING,\
                                              sample_mode=Atype.FINITE,samps_per_chan=len(DOwaveform))
            DOtask.write(DOwaveform, auto_start = True)
            print(axis,'real distance moved: ',np.sum(DOwaveform)/line/25000*1000*DISTANCE,'um')
            DOtask.wait_until_done(timeout =60)
                
            DOtask.stop()
            # DOtask.close()
            settingtask.write(XDISABLE + YDISABLE + ZDISABLE, auto_start = True)
            settingtask.stop()
            # settingtask.close()
            
        if axis == 'X':
            self.Xpos = self.Xpos+distance
            # self.ui.XPosition.setValue(self.Xpos)
        elif axis == 'Y':
            self.Ypos = self.Ypos+distance
            # self.ui.YPosition.setValue(self.Ypos)
        elif axis == 'Z':
            self.Zpos = self.Zpos+distance
            # self.ui.ZPosition.setValue(self.Zpos)
        self.StagebackQueue.put(0)