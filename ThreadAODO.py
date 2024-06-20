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

global SIM
SIM = False
###########################################
from PyQt5.QtCore import  QThread

try:
    import nidaqmx as ni
    from nidaqmx.constants import AcquisitionType as Atype
    from nidaqmx.constants import Edge
except:
    SIM = True
    
from Generaic_functions import GenAODO
import time
import traceback
import numpy as np

# stage enable/disable digital value
# enable = 0
global XDISABLE
XDISABLE = pow(2,0) # port 2 line 0
global YDISABLE
YDISABLE = pow(2,2) # port 2 line 2
global ZDISABLE
ZDISABLE = pow(2,4) # port 2 line 4
global X0DISABLE
X0DISABLE = pow(2,6) # port 2 line 6

# stage forwared backward digital value
global XFORWARD
XFORWARD = pow(2,1) # port 2 line 1
global YFORWARD
YFORWARD = pow(2,3) # port 2 line 3
global ZFORWARD
ZFORWARD = 0 # port 2 line 5, but reverse
global X0FORWARD
X0FORWARD = pow(2,7) # port 2 line 7

global XBACKWARD
XBACKWARD = 0
global YBACKWARD
YBACKWARD = 0
global ZBACKWARD
ZBACKWARD = pow(2,5) # port 2 line 5
# backward = 0
global X0BACKWARD
X0BACKWARD = 0

# stage channel digital value
global XCH
XCH = pow(2,0) # port 0 line 0
global YCH
YCH = pow(2,1) # port 0 line 1
global ZCH
ZCH = pow(2,2) # port 0 line2
global X0CH
X0CH = pow(2,3) # port 0 line 3

class AODOThread(QThread):
    def __init__(self):
        super().__init__()
        self.AOtask = None
        self.DOtask = None
    
    def run(self):
        self.Init_Stages()
        self.StagebackQueue.get()
        self.QueueOut()
        
    def QueueOut(self):
        self.item = self.queue.get()
        while self.item.action != 'exit':
            try:
                if self.item.action == 'Xmove2':
                    self.XMove(axis = 'X')
                elif self.item.action == 'Ymove2':
                    self.DirectMove(axis = 'Y')
                elif self.item.action == 'Zmove2':
                    self.DirectMove(axis = 'Z')
                elif self.item.action == 'XUP':
                    self.StepMove(axis = 'X', Direction = 'UP')
                elif self.item.action == 'YUP':
                    self.StepMove(axis = 'Y', Direction = 'UP')
                elif self.item.action == 'ZUP':
                    self.StepMove(axis = 'Z', Direction = 'UP')
                elif self.item.action == 'XDOWN':
                    self.StepMove(axis = 'X', Direction = 'DOWN')
                elif self.item.action == 'YDOWN':
                    self.StepMove(axis = 'Y', Direction = 'DOWN')
                elif self.item.action == 'ZDOWN':
                    self.StepMove(axis = 'Z', Direction = 'DOWN')
                    
                elif self.item.action == 'Init':
                    self.Init_Stages()
                elif self.item.action == 'Uninit':
                    self.Uninit()
                elif self.item.action == 'ConfigTask':
                    self.ConfigTask(self.item.direction)
                elif self.item.action == 'StartTask':
                    self.StartTask()
                elif self.item.action == 'StopTask':
                    self.StopTask(self.item.direction)
                elif self.item.action == 'CloseTask':
                    self.CloseTask()
                    
                elif self.item.action == 'startVibratome':
                    self.startVibratome()
                elif self.item.action == 'stopVibratome':
                    self.stopVibratome()

                elif self.item.action == 'StopNClose_Continuous':
                    self.StopNClose_Continuous()
                
                elif self.item.action == 'centergalvo':
                    self.centergalvo()
                elif self.item.action == 'CscanDistance':
                    self.CscanDistance()
                else:
                    message = 'AODO thread is doing something undefined: '+self.item.action
                    self.ui.statusbar.showMessage(message)
                    print(message)
                    # self.ui.PrintOut.append(message)
                    self.log.write(message)
            except Exception:
                message = "\nAn error occurred,"+" skip the AODO action\n"
                print(message)
                self.ui.statusbar.showMessage(message)
                # self.ui.PrintOut.append(message)
                self.log.write(message)
                print(traceback.format_exc())
            self.item = self.queue.get()
        self.ui.statusbar.showMessage('AODO thread successfully exited')

    def Init_Stages(self):
        # self.Xpos = self.ui.XPosition.value()
        # self.Ypos = self.ui.YPosition.value()
        # self.Zpos = self.ui.ZPosition.value()
        self.ui.Xcurrent.setValue(self.ui.XPosition.value())
        self.ui.Ycurrent.setValue(self.ui.YPosition.value())
        self.ui.Zcurrent.setValue(self.ui.ZPosition.value())
        
        message = "Stage position updated..."
        self.ui.statusbar.showMessage(message)
        # self.ui.PrintOut.append(message)
        self.log.write(message)
        print(message)
        self.StagebackQueue.put(0)
        # print('X pos: ',self.Xpos)
        # print('Y pos: ',self.Ypos)
        # print('Z pos: ',self.Zpos)
    
    def Uninit(self):
        if not (SIM or self.SIM):
            settingtask = ni.Task('setting')
            settingtask.do_channels.add_do_chan(lines='AODO/port2/line0:7')
            tmp = np.uint32(YDISABLE + XDISABLE + ZDISABLE + X0DISABLE)
            settingtask.write(tmp, auto_start = True)
            settingtask.stop()
            settingtask.close()
        self.StagebackQueue.put(0)
        
    def ConfigTask(self, direction = 1):
        if self.ui.Laser.currentText() == 'Axsun100k':
            self.Aline_freq = 100000
        else:
            return 'Laser invalid!'
        # self.CloseTask()
        
        if not (SIM or self.SIM): # if not running simulation mode
            # Generate waveform
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
            ######################################################################################
            # init AO task
            self.AOtask = ni.Task('AOtask')
            # Config channel and vertical
            self.AOtask.ao_channels.add_ao_voltage_chan(physical_channel='AODO/ao0', \
                                                  min_val=- 5.0, max_val=5.0, \
                                                  units=ni.constants.VoltageUnits.VOLTS)
            # depending on whether continuous or finite, config clock and mode
            mode =  Atype.FINITE
            self.AOtask.timing.cfg_samp_clk_timing(rate=self.Aline_freq, \
                                                   source=self.ui.ClockTerm.toPlainText(), \
                                                   active_edge= Edge.FALLING,\
                                                   sample_mode=mode,samps_per_chan=len(AOwaveform))
            # Config start mode
            if self.Digitizer == 'ATS9351':      
                self.AOtask.triggers.sync_type.MASTER = True
            elif self.Digitizer == 'ART8912':
                # pass
                self.AOtask.triggers.start_trigger.cfg_dig_edge_start_trig("/AODO/PFI1")
            # write waveform and start
            self.AOtask.write(AOwaveform, auto_start = False)
            # self.AOtask.start()
            
            #################################################################################
            # only use DO in Cscan acquisition or if digitizer is Alazar board
            if self.ui.ACQMode.currentText() in ['SingleCscan','SurfScan','SurfScan+Slice'] or self.Digitizer == 'ATS9351':
                # before move stage, configure direction and enable stage using port 2 first
                # direction = 0 means backward
                # direction = 1 means forward
                stageEnabletask = ni.Task('stageEnable')
                stageEnabletask.do_channels.add_do_chan(lines='AODO/port2/line0:7')
                tmp = np.uint32(direction * YFORWARD)# + XDISABLE + ZDISABLE)
                stageEnabletask.write(tmp, auto_start = True)
                stageEnabletask.wait_until_done(timeout = 1)
                stageEnabletask.stop()
                stageEnabletask.close()
                # config DO task
                self.DOtask = ni.Task('DOtask')
                self.DOtask.do_channels.add_do_chan(lines='AODO/port0/line0:7')
                self.DOtask.timing.cfg_samp_clk_timing(rate=self.Aline_freq, \
                                                       source=self.ui.ClockTerm.toPlainText(), \
                                                       active_edge= Edge.FALLING,\
                                                       sample_mode=mode,samps_per_chan=len(DOwaveform))
               
                if self.Digitizer == 'ATS9351':      
                    self.DOtask.triggers.sync_type.SLAVE = True
                elif self.Digitizer == 'ART8912':
                    # pass
                    self.DOtask.triggers.start_trigger.cfg_dig_edge_start_trig("/AODO/PFI1")
                
                self.DOtask.write(DOwaveform, auto_start = False)
                # self.DOtask.start()
                # print(DOwaveform.shape)
                # steps = np.sum(DOwaveform)/25000.0*2/pow(2,1)
                # message = 'distance per Cscan: '+str(steps)+'mm'
                # # self.ui.PrintOut.append(message)
                # print(message)
                # self.log.write(message)
        return 'AODO configuration success'
        
    def StartTask(self):
        if not (SIM or self.SIM):
            self.AOtask.start()
            if self.ui.ACQMode.currentText() in ['SingleCscan','SurfScan','SurfScan+Slice'] or self.Digitizer == 'ATS9351':
                self.DOtask.start()
        self.StagebackQueue.put(0)
            

            
    def StopTask(self, direction = 1):
        if not (SIM or self.SIM):
            self.AOtask.wait_until_done(timeout = 60)
            self.AOtask.stop()
            # self.AOtask.close()
            # print(self.ui.ACQMode.currentText())
            if self.ui.ACQMode.currentText() in ['SingleCscan','SurfScan','SurfScan+Slice'] or self.Digitizer == 'ATS9351':
                self.DOtask.stop()
                # self.DOtask.close()
                # settingtask.write(XDISABLE+ YDISABLE+ ZDISABLE, auto_start = True)
                # update GUI Y stage position
        Ystep = self.ui.YStepSize.value()*self.ui.Ysteps.value()/1000.0
        currentpos = self.ui.Ycurrent.value()+Ystep if direction == 1 else self.ui.Ycurrent.value()-Ystep
        self.ui.Ycurrent.setValue(currentpos)
        self.ui.YPosition.setValue(currentpos)
    
    def CloseTask(self):
        if not (SIM or self.SIM):
            self.AOtask.close()
            if self.ui.ACQMode.currentText() in ['SingleCscan','SurfScan','SurfScan+Slice'] or self.Digitizer == 'ATS9351':
                self.DOtask.close()
            message = 'cscan X :'+str(round(self.Xpos,2))+' Y :'+str(round(self.Ypos,2))+' Z :'+str(round(self.Zpos,3))
            print(message)
            self.log.write(message)
        self.StagebackQueue.put(0)

    def startVibratome(self):
        if not (SIM or self.SIM):
            settingtask = ni.Task('vibratome')
            settingtask.do_channels.add_do_chan(lines='AODO/PFI2')
            settingtask.write(True, auto_start = True)
            settingtask.wait_until_done(timeout = 1)
            settingtask.stop()
            settingtask.close()
        self.StagebackQueue.put(0)
        
    def stopVibratome(self):
        if not (SIM or self.SIM):
            settingtask = ni.Task('vibratome')
            settingtask.do_channels.add_do_chan(lines='AODO/PFI2')
            settingtask.write(False, auto_start = True)
            settingtask.wait_until_done(timeout = 1)
            settingtask.stop()
            settingtask.close()
        self.StagebackQueue.put(0)
        
    def StopNClose_Continuous(self):
        if not (SIM or self.SIM):
            if self.AOtask:
                self.AOtask.stop()
                self.AOtask.close()
                if self.Digitizer == 'ATS9351':   
                    self.DOtask.stop()
                    self.DOtask.close()
            else:
                print('continuous acquisition already stopped...')
                
    def centergalvo(self):
        if not (SIM or self.SIM):
            with ni.Task('AO task') as AOtask:
                AOtask.ao_channels.add_ao_voltage_chan(physical_channel='AODO/ao0', \
                                                      min_val=- 10.0, max_val=10.0, \
                                                      units=ni.constants.VoltageUnits.VOLTS)
                AOtask.write(Galvo_bias, auto_start = True)
                AOtask.wait_until_done(timeout = 1)
                AOtask.stop()

    def stagewave_ramp(self, distance):
        # generate stage movement that ramps up and down speed so that motor won't miss signal at beginning and end
        # how to do that: motor is driving by low->high digital transition
        # ramping up: make the interval between two highs with long time at the beginning, then gradually goes down.vice versa for ramping down
        if np.abs(distance) > 0.02:
            max_interval = 100
        elif np.abs(distance) > 0.01:
            max_interval = 40
        elif np.abs(distance) > 0.003:
            max_interval = 10
        else:
            max_interval = 0
        ramp_up_interval = np.arange(max_interval,0,-2)
        ramp_down_interval = np.arange(1,max_interval+1,2)
        ramping_highs = np.sum(len(ramp_down_interval)+len(ramp_up_interval)) # number steps used in ramping up and down process
        total_highs = np.uint32(STEPS//DISTANCE*np.abs(distance))
        
        # ramping up waveform generation
        ramp_up_waveform = np.zeros(np.sum(ramp_up_interval))
        if any(ramp_up_waveform):
            ramp_up_waveform[0] = 1
        time_lapse = -1
        for interval in ramp_up_interval:
            time_lapse = time_lapse + interval
            ramp_up_waveform[time_lapse] = 1

        # ramping down waveform generation
        ramp_down_waveform = np.zeros(np.sum(ramp_down_interval))
        if any(ramp_down_waveform):
            ramp_down_waveform[0] = 1
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
        if axis == 'X':
            line = XCH
            speed = self.ui.XSpeed.value()
            pos = self.ui.XPosition.value()
            if pos>self.ui.X1max.value()+self.ui.X0max.value()+1e-5 or pos<self.ui.X1min.value() + self.ui.X0min.value()-1e-5:
                message = 'X target postion invalid, abort...'
                # self.ui.PrintOut.append(message)
                self.log.write(message)
                print(message)
                return message
            distance = self.ui.XPosition.value()-self.ui.Xcurrent.value()
            if distance > 0:
                direction = XFORWARD
                sign = 1
            else:
                direction = XBACKWARD
                sign = -1
            enable = 0#YDISABLE + ZDISABLE
            
        elif axis == 'X0':
            line = X0CH
            speed = self.ui.XSpeed.value()
            pos = self.ui.XPosition.value()
            if pos>self.ui.X0max.value() + self.ui.X1min.value()+1e-5 or pos<self.ui.X0min.value()-1e-5:
                message = 'X0 target postion invalid, abort...'
                # self.ui.PrintOut.append(message)
                self.log.write(message)
                print(message)
                return message
            distance = self.ui.XPosition.value()-self.ui.Xcurrent.value()
            if distance > 0:
                direction = X0FORWARD
                sign = 1
            else:
                direction = X0BACKWARD
                sign = -1
            enable = 0#YDISABLE + ZDISABLE
        elif axis == 'Y':
            line = YCH
            speed = self.ui.YSpeed.value()
            pos = self.ui.YPosition.value()
            if pos>self.ui.Ymax.value() or pos<self.ui.Ymin.value():
                message = 'Y target postion invalid, abort...'
                # self.ui.PrintOut.append(message)
                self.log.write(message)
                print(message)
                return message
            distance = self.ui.YPosition.value()-self.ui.Ycurrent.value()
            if distance > 0:
                direction = YFORWARD
                sign = 1
            else:
                direction = YBACKWARD
                sign = -1
            enable = 0#XDISABLE + ZDISABLE
        elif axis == 'Z':
            line = ZCH
            speed = self.ui.ZSpeed.value()
            pos = self.ui.ZPosition.value()
            if pos>self.ui.Zmax.value() or pos<self.ui.Zmin.value():
                message = 'Z target postion invalid, abort...'
                # self.ui.PrintOut.append(message)
                self.log.write(message)
                print(message)
                return message
            distance = self.ui.ZPosition.value()-self.ui.Zcurrent.value()
            if distance > 0:
                direction = ZFORWARD
                sign = 1
            else:
                direction = ZBACKWARD
                sign = -1
            enable = 0#XDISABLE + YDISABLE
            
        if np.abs(distance) < 0.003:
            message = axis + ' move2 action aborted'
            # self.ui.PrintOut.append(message)
            print(message)
            self.log.write(message)
            return 0
        if not (SIM or self.SIM):
            with ni.Task('Move task') as DOtask, ni.Task('stageEnable') as stageEnabletask:
                # configure stage direction and enable
                stageEnabletask.do_channels.add_do_chan(lines='AODO/port2/line0:7')
                stageEnabletask.write(direction + enable, auto_start = True)
                stageEnabletask.wait_until_done(timeout = 1)
                stageEnabletask.stop()
                time.sleep(0.1)
                # configure DO task 
                DOwaveform = self.stagewave_ramp(distance)
                DOwaveform = np.uint32(DOwaveform * line)
                message = axis+' moving: '+str(round(np.sum(DOwaveform)/line/25000*DISTANCE*sign,3))+'mm'+' target pos: '+str(pos)
                print(message)
                # self.ui.PrintOut.append(message)
                self.log.write(message)
                
                DOtask.do_channels.add_do_chan(lines='AODO/port0/line0:7')
                DOtask.timing.cfg_samp_clk_timing(rate=STEPS*2//DISTANCE*round(speed,2), \
                                                  active_edge= Edge.FALLING,\
                                                  sample_mode=Atype.FINITE,samps_per_chan=len(DOwaveform))
                DOtask.write(DOwaveform, auto_start = False)
                DOtask.start()
                DOtask.wait_until_done(timeout =300)
                DOtask.stop()
                # message = axis+' current pos: '+str(pos)
                # print(message)
                # # self.ui.PrintOut.append(message)
                # self.log.write(message)
                # settingtask.write(XDISABLE + YDISABLE + ZDISABLE, auto_start = True)
                
        if axis == 'X':
            self.ui.Xcurrent.setValue(self.ui.Xcurrent.value()+distance)
            # self.ui.XPosition.setValue(self.Xpos)
        elif axis == 'X0':
            self.ui.Xcurrent.setValue(self.ui.Xcurrent.value()+distance)
            # self.ui.XPosition.setValue(self.Xpos)
        elif axis == 'Y':
            self.ui.Ycurrent.setValue(self.ui.Ycurrent.value()+distance)
            # self.ui.YPosition.setValue(self.Ypos)
        elif axis == 'Z':
            self.ui.Zcurrent.setValue(self.ui.Zcurrent.value()+distance)
            # self.ui.ZPosition.setValue(self.Zpos)
        message = 'X :'+str(self.ui.Xcurrent.value())+' Y :'+str(round(self.ui.Ycurrent.value(),2))+' Z :'+str(self.ui.Zcurrent.value())
        print(message)
        self.log.write(message)
        
    def DirectMove(self, axis):
        self.Move(axis)
        self.StagebackQueue.put(0)
        
    def StepMove(self, axis, Direction):
        if axis == 'X':
            distance = self.ui.Xstagestepsize.value() if Direction == 'UP' else -self.ui.Xstagestepsize.value() 
            self.ui.XPosition.setValue(self.ui.Xcurrent.value()+distance)
            self.XMove()
        elif axis == 'Y':
            distance = self.ui.Ystagestepsize.value() if Direction == 'UP' else -self.ui.Ystagestepsize.value() 
            self.ui.YPosition.setValue(self.ui.Ycurrent.value()+distance)
            self.Move(axis)
            self.StagebackQueue.put(0)
        elif axis == 'Z':
            distance = self.ui.Zstagestepsize.value() if Direction == 'UP' else -self.ui.Zstagestepsize.value() 
            self.ui.ZPosition.setValue(self.ui.Zcurrent.value()+distance)
            self.Move(axis)
            self.StagebackQueue.put(0)
            
    def XMove(self, axis = 'X'):
        # enable low enables, enable high disables
        current_pos = self.ui.Xcurrent.value()
        target_pos = self.ui.XPosition.value()
        
        if target_pos>self.ui.X1max.value()+self.ui.X0max.value()+1e-5 or target_pos<self.ui.X1min.value()+self.ui.X0min.value()-1e-5:
            message = 'X target postion invalid, abort...'
            # self.ui.PrintOut.append(message)
            self.log.write(message)
            print(message)
            self.StagebackQueue.put(0)
            return message
        
        # determine which stage to move
        if current_pos <= self.ui.X0max.value(): # this means X1 stage is at min position
            if target_pos <= self.ui.X0max.value(): # this means only X0 stage will move
                # TODO: move X0 distance
                self.Move('X0')
            else: # this means X0 stage will move to max and X1 stage will move afterwards
                # TODO: move X0 to midpoint 
                self.ui.XPosition.setValue(self.ui.X0max.value()+self.ui.X1min.value())
                self.Move('X0')
                # self.Xpos = self.ui.X0max.value()
                # TODO: move X1 abs(distance) - (self.ui.X0max.value() - current_pos)
                self.ui.XPosition.setValue(target_pos)
                self.Move('X')
        else: # this means X0 stage is at max position
            if target_pos <= self.ui.X0max.value(): # this means X1 stage will move to min and X0 stage will move afterwards
                # TODO: move X1 to midpoint
                self.ui.XPosition.setValue(self.ui.X0max.value()+self.ui.X1min.value())
                self.Move('X')
                # self.Xpos = self.ui.X0max.value()
                # TODO: move X0 abs(distance) - (current_pos - self.ui.X0max.value())
                self.ui.XPosition.setValue(target_pos)
                self.Move('X0')
            else: # this means only X1 stage will move
                # TODO: move X1 distance
                self.Move('X')
        self.StagebackQueue.put(0)