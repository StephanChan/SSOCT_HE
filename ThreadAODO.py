# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 16:51:20 2023

@author: admin
"""
from PyQt5.QtCore import  QThread
import nidaqmx as ni
from nidaqmx.constants import AcquisitionType as Atype
from nidaqmx.constants import Edge
# from nidaqmx.constants import RegenerationMode as Rmode
# from nidaqmx.constants import Edge as Edge
# from nidaqmx.errors import DaqWarning as warnings
from Generaic_functions import GenAODO
import time
import traceback
global Galvo_bias
Galvo_bias = 3

class AODOThread(QThread):
    def __init__(self):
        super().__init__()
        self.AOtask = None
        self.DOtask = None
    
    def run(self):
        self.QueueOut()
        
    def QueueOut(self):
        self.item = self.queue.get()
        while self.item.action != 'exit':
            try:
                if self.item.action == 'Xmove2':
                    #print('X stage thread is doing ',self.item.action)
                    self.ui.statusbar.showMessage('X stage moving to position: '+ str(self.ui.XPosition.value()))
                elif self.item.action == 'Ymove2':
                    #print('Y stage thread is doing ',self.item.action)
                    self.ui.statusbar.showMessage('Y stage moving to position: '+ str(self.ui.YPosition.value()))
                elif self.item.action == 'Zmove2':
                    #print('Z stage thread is doing ',self.item.action)
                    self.ui.statusbar.showMessage('Z stage moving to position: '+ str(self.ui.ZPosition.value()))
                    
                elif self.item.action == 'ConfigAODO':
                    self.ui.statusbar.showMessage(self.ConfigAODO())
                elif self.item.action == 'StartOnce':
                    self.StartOnce()
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
            except Exception as error:
                print("\nAn error occurred:", error,' skip the AODO action\n')
                print(traceback.format_exc())
            self.item = self.queue.get()
        print('AODO thread successfully exited')

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
        self.DOtask = ni.Task('DOtask')
        # Configure Analog output task for Galvo control
        self.AOtask.ao_channels.add_ao_voltage_chan(physical_channel='AODO/ao0', \
                                              min_val=- 5.0, max_val=5.0, \
                                              units=ni.constants.VoltageUnits.VOLTS)
        if self.ui.ACQMode.currentText() in ['RptBline', 'RptAline','RptCscan']:
            self.AOtask.timing.cfg_samp_clk_timing(rate=self.Aline_freq, \
                                            source=self.ui.ClockTerm.toPlainText(), \
                                                active_edge= Edge.FALLING,\
                                              sample_mode=Atype.CONTINUOUS,samps_per_chan=len(AOwaveform))
        else:
            self.AOtask.timing.cfg_samp_clk_timing(rate=self.Aline_freq, \
                                            source=self.ui.ClockTerm.toPlainText(), \
                                              sample_mode=Atype.FINITE,samps_per_chan=len(AOwaveform))
                
        self.AOtask.triggers.sync_type.MASTER = True

        # print(len(DOwaveform))
            
        self.AOtask.write(AOwaveform, auto_start = False)
        # Confiture Digital output task for stage control and digitizer trigger enabling
         
        self.DOtask.do_channels.add_do_chan(lines='AODO/port0/line0:3')
        if self.ui.ACQMode.currentText() in ['RptBline', 'RptAline','RptCscan']:
            self.DOtask.timing.cfg_samp_clk_timing(rate=self.Aline_freq, \
                                            source=self.ui.ClockTerm.toPlainText(), \
                                                active_edge= Edge.FALLING,\
                                              sample_mode=Atype.CONTINUOUS,samps_per_chan=len(DOwaveform))
        else:
            self.DOtask.timing.cfg_samp_clk_timing(rate=self.Aline_freq, \
                                            source=self.ui.ClockTerm.toPlainText(), \
                                              sample_mode=Atype.FINITE,samps_per_chan=len(DOwaveform))
       
        self.DOtask.triggers.sync_type.SLAVE = True
        
        self.DOtask.write(DOwaveform, auto_start = False)
        return 'AODO configuration success'
            
    def StartOnce(self):
        self.DOtask.start()
        self.AOtask.start()
        # try:
        self.AOtask.wait_until_done(timeout = 60)
        self.AOtask.stop()
        self.DOtask.stop()
        # except:

        # print('AODO write task done')
        
            
    def StartContinuous(self):
        if self.AOtask.is_task_done():
            self.DOtask.start()
            self.AOtask.start()
        else:
            pass
        
    def WaitDone(self):
        self.AOtask.wait_until_done()
        
    def StopContinuous(self):
        self.AOtask.stop()
        self.DOtask.stop()
        
    def CloseTask(self):
        try:
            while not self.AOtask.is_task_done():
                time.sleep(0.5)
            self.DOtask.close()
            self.AOtask.close()
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
            