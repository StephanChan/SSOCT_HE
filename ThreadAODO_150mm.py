# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 16:51:20 2023

@author: admin
"""
###########################################

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


# stage forwared backward digital value
global XFORWARD
XFORWARD = pow(2,1) # port 2 line 1
global YFORWARD
YFORWARD = pow(2,3) # port 2 line 3
global ZFORWARD
ZFORWARD = 0 # port 2 line 5, but reverse

global XBACKWARD
XBACKWARD = 0
global YBACKWARD
YBACKWARD = 0
global ZBACKWARD
ZBACKWARD = pow(2,5) # port 2 line 5
# backward = 0
# stage channel digital value
global XCH
XCH = pow(2,0) # port 0 line 0
global YCH
YCH = pow(2,1) # port 0 line 1
global ZCH
ZCH = pow(2,2) # port 0 line2

class AODOThread(QThread):
    def __init__(self):
        super().__init__()
        self.AOtask = None
        self.DOtask = None
        
    
    def run(self):
        self.Init_all_termial()
        self.StagebackQueue.get()
        self.QueueOut()
        
    def QueueOut(self):
        self.item = self.queue.get()
        while self.item.action != 'exit':
            
            try:
                if self.item.action == 'Xmove2':
                    self.DirectMove(axis = 'X')
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
                    self.Init_all_termial()
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

    def Init_all_termial(self):
        # Galvo terminal
        self.GalvoAO = self.ui.AODOboard.toPlainText()+'/'+self.ui.GalvoAO.currentText()
        # laser
        if self.ui.Laser.currentText() == 'Axsun100k':
            self.Aline_frq = 100000
        elif self.ui.Laser.currentText() == 'Thorlabs200k':
            self.Aline_frq = 200000
        else:
            self.ui.statusbar.showMessage('Laser invalid!!!')
        # Stage steps
        self.StageSteps = self.ui.AODOboard.toPlainText()+'/port0/line0:7'
        # stage direction and enables
        self.StageDnE = self.ui.AODOboard.toPlainText()+'/port2/line0:7'
        # Aline trigger terminal
        self.ClockTerm = '/'+self.ui.AODOboard.toPlainText()+'/'+self.ui.ClockTerm.currentText()
        # Galvo&Stage trigger termial
        self.AODOTrig = '/'+self.ui.AODOboard.toPlainText()+'/'+self.ui.AODOTrig.currentText()
        # vibratome enable terminal
        self.VibEnable = '/'+self.ui.AODOboard.toPlainText()+'/'+self.ui.VibEnable.currentText()

        self.ui.Xcurrent.setValue(self.ui.XPosition.value())
        self.ui.Ycurrent.setValue(self.ui.YPosition.value())
        self.ui.Zcurrent.setValue(self.ui.ZPosition.value())
        message = "Stage position updated..."

        self.ui.statusbar.showMessage(message)
        # self.ui.PrintOut.append(message)
        self.log.write(message)
        print(message)
        self.StagebackQueue.put(0)
    
    def Uninit(self):
        if not (SIM or self.SIM):
            settingtask = ni.Task('setting')
            settingtask.do_channels.add_do_chan(lines=self.StageDnE)
            tmp = np.uint32(YDISABLE + XDISABLE + ZDISABLE)
            settingtask.write(tmp, auto_start = True)
            settingtask.stop()
            settingtask.close()
        self.StagebackQueue.put(0)
        
    def ConfigTask(self, direction = 1):
        if not (SIM or self.SIM): # if not running simulation mode
            # Generate waveform
            if self.ui.YScanDIM.currentText() == 'YStage':
                ScanDIM = pow(2,1)
                _DISTANCE = self.ui.Ymm.value()
                _STEPS = self.ui.Ydevides.value()
            elif self.ui.YScanDIM.currentText() == 'XStage':
                ScanDIM = pow(2,0)
                _DISTANCE = self.ui.Xmm.value()
                _STEPS = self.ui.Xdevides.value()
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
                                                   BVG = self.ui.BlineAVG.value(),\
                                                   CSCAN_AXIS = ScanDIM,\
                                                   Galvo_bias = self.ui.GalvoBias.value(),\
                                                   DISTANCE = _DISTANCE, \
                                                   STEPS = _STEPS)
            ######################################################################################
            # init AO task
            self.AOtask = ni.Task('AOtask')
            # Config channel and vertical
            self.AOtask.ao_channels.add_ao_voltage_chan(physical_channel=self.GalvoAO, \
                                                  min_val=- 5.0, max_val=5.0, \
                                                  units=ni.constants.VoltageUnits.VOLTS)
            # depending on whether continuous or finite, config clock and mode
            mode =  Atype.FINITE
            self.AOtask.timing.cfg_samp_clk_timing(rate=self.Aline_freq, \
                                                   source=self.ClockTerm, \
                                                   active_edge= Edge.FALLING,\
                                                   sample_mode=mode,samps_per_chan=len(AOwaveform))
            # Config start mode
            if self.Digitizer == 'Alazar':      
                self.AOtask.triggers.sync_type.MASTER = True
            elif self.Digitizer == 'ART':
                # pass
                self.AOtask.triggers.start_trigger.cfg_dig_edge_start_trig(self.AODOTrig)
            # write waveform and start
            self.AOtask.write(AOwaveform, auto_start = False)
            # self.AOtask.start()
            
            #################################################################################
            # only use DO in Cscan acquisition or if digitizer is Alazar board
            if self.ui.ACQMode.currentText() in ['SingleCscan','Mosaic','Mosaic+Cut']:
                # before move stage, configure direction and enable stage using port 2 first
                # direction = 0 means backward
                # direction = 1 means forward
                stageEnabletask = ni.Task('stageEnable')
                stageEnabletask.do_channels.add_do_chan(lines=self.StageDnE)
                tmp = np.uint32(direction * YFORWARD)# + XDISABLE + ZDISABLE)
                stageEnabletask.write(tmp, auto_start = True)
                stageEnabletask.wait_until_done(timeout = 1)
                stageEnabletask.stop()
                stageEnabletask.close()
                # config DO task
                self.DOtask = ni.Task('DOtask')
                self.DOtask.do_channels.add_do_chan(lines=self.StageSteps)
                self.DOtask.timing.cfg_samp_clk_timing(rate=self.Aline_freq, \
                                                       source=self.ClockTerm, \
                                                       active_edge= Edge.FALLING,\
                                                       sample_mode=mode,samps_per_chan=len(DOwaveform))
               

                self.DOtask.triggers.start_trigger.cfg_dig_edge_start_trig(self.AODOTrig)
                
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
            if self.ui.ACQMode.currentText() in ['SingleCscan','Mosaic','Mosaic+Cut'] or self.Digitizer == 'Alazar':
                self.DOtask.start()
        self.StagebackQueue.put(0)
            

            
    def StopTask(self, direction = 1):
        if not (SIM or self.SIM):
            self.AOtask.wait_until_done(timeout = 60)
            self.AOtask.stop()
            # self.AOtask.close()
            # print(self.ui.ACQMode.currentText())
            if self.ui.ACQMode.currentText() in ['SingleCscan','Mosaic','Mosaic+Cut'] or self.Digitizer == 'Alazar':
                self.DOtask.stop()
                # self.DOtask.close()
                # settingtask.write(XDISABLE+ YDISABLE+ ZDISABLE, auto_start = True)
                # update GUI Y stage position
        if self.ui.ACQMode.currentText() in ['SingleCscan','Mosaic','Mosaic+Cut']:
            Ystep = self.ui.YStepSize.value()*self.ui.Ysteps.value()/1000.0
            currentpos = self.ui.Ycurrent.value()+Ystep if direction == 1 else self.ui.Ycurrent.value()-Ystep
            self.ui.Ycurrent.setValue(currentpos)
            self.ui.YPosition.setValue(currentpos)

    
    def CloseTask(self):
        if not (SIM or self.SIM):
            self.AOtask.close()
            if self.ui.ACQMode.currentText() in ['SingleCscan','Mosaic','Mosaic+Cut'] or self.Digitizer == 'Alazar':
                self.DOtask.close()
            message = 'cscan X :'+str(round(self.ui.Xcurrent.value(),2))+' Y :'+str(round(self.ui.Ycurrent.value(),2))+' Z :'+str(round(self.ui.Zcurrent.value(),3))
            print(message)
            self.log.write(message)
        self.StagebackQueue.put(0)

    def startVibratome(self):
        if not (SIM or self.SIM):
            settingtask = ni.Task('vibratome')
            settingtask.do_channels.add_do_chan(lines=self.VibEnable)
            settingtask.write(True, auto_start = True)
            settingtask.wait_until_done(timeout = 1)
            settingtask.stop()
            settingtask.close()
        self.StagebackQueue.put(0)
        
    def stopVibratome(self):
        if not (SIM or self.SIM):
            settingtask = ni.Task('vibratome')
            settingtask.do_channels.add_do_chan(lines=self.VibEnable)
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
                if self.Digitizer == 'Alazar':   
                    self.DOtask.stop()
                    self.DOtask.close()
            else:
                print('continuous acquisition already stopped...')
                
    def centergalvo(self):
        if not (SIM or self.SIM):
            with ni.Task('AO task') as AOtask:
                AOtask.ao_channels.add_ao_voltage_chan(physical_channel=self.GalvoAO, \
                                                      min_val=- 10.0, max_val=10.0, \
                                                      units=ni.constants.VoltageUnits.VOLTS)
                AOtask.write(self.GalvoBias, auto_start = True)
                AOtask.wait_until_done(timeout = 1)
                AOtask.stop()

    def stagewave_ramp(self, distance, DISTANCE, STEPS):
        # generate stage movement that ramps up and down speed so that motor won't miss signal at beginning and end
        # how to do that: motor is driving by low->high digital transition
        # ramping up: make the interval between two highs LONG at the beginning, then gradually shorten. vice versa for ramping down
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
        time_lapse = -1
        for interval in ramp_down_interval:
            time_lapse = time_lapse + interval
            ramp_down_waveform[time_lapse] = 1
        if any(ramp_down_waveform):
            ramp_down_waveform[0] = 1
            
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
            DISTANCE = self.ui.Xmm.value()
            STEPS = self.ui.Xdevides.value()
            speed = self.ui.XSpeed.value()
            pos = self.ui.XPosition.value()
            if pos>self.ui.Xmax.value()or pos<self.ui.Xmin.value():
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
        elif axis == 'Y':
            line = YCH
            DISTANCE = self.ui.Ymm.value()
            STEPS = self.ui.Ydevides.value()
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
            DISTANCE = self.ui.Zmm.value()
            STEPS = self.ui.Zdevides.value()
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
                stageEnabletask.do_channels.add_do_chan(lines=self.StageDnE)
                stageEnabletask.write(direction + enable, auto_start = True)
                stageEnabletask.wait_until_done(timeout = 1)
                stageEnabletask.stop()
                time.sleep(0.1)
                # configure DO task 
                DOwaveform = self.stagewave_ramp(distance, DISTANCE, STEPS)
                DOwaveform = np.uint32(DOwaveform * line)
                message = axis+' moving: '+str(round(np.sum(DOwaveform)/line/25000*DISTANCE*sign,3))+'mm'+' target pos: '+str(pos)
                print(message)
                # self.ui.PrintOut.append(message)
                self.log.write(message)
                
                DOtask.do_channels.add_do_chan(lines=self.StageSteps)
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
            self.Move(axis)
            self.StagebackQueue.put(0)
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
            