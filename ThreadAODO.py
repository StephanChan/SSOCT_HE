# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 16:51:20 2023

@author: admin
"""
from PyQt5.QtCore import  QThread
import nidaqmx as ni
from nidaqmx.constants import AcquisitionType as Atype
# from nidaqmx.constants import RegenerationMode as Rmode
# from nidaqmx.constants import Edge as Edge
# from nidaqmx.errors import DaqWarning as warnings
from Generaic_functions import GenAODO
import time
import numpy as np


class AODOThread(QThread):
    def __init__(self, ui, AODOQueue, PauseQueue):
        super().__init__()
        self.ui = ui
        self.queue = AODOQueue
        self.pauseQueue = PauseQueue
        self.AOtask = None
        self.DOtask = None
    
    def run(self):
        self.QueueOut()
        
    def QueueOut(self):
        self.item = self.queue.get()
        while self.item.action != 'exit':
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
            elif self.item.action == 'StopContinuous':
                self.StopContinuous()
            elif self.item.action == 'CloseTask':
                self.CloseTask()
            else:
                self.ui.statusbar.showMessage('AODO thread is doing something undefined: '+self.item.action)
            self.item = self.queue.get()
            

    def ConfigAODO(self):
        if self.ui.Laser.currentText() == 'Axsun100k':
            self.Aline_freq = 100000
        else:
            return 'Laser invalid!'
        if self.AOtask is not None:
            self.CloseTask()
            
        self.AOtask = ni.Task('AO task')
        self.DOtask = ni.Task('DO task')
        # Configure Analog output task for Galvo control
        self.AOtask.ao_channels.add_ao_voltage_chan(physical_channel='AODO/ao0', \
                                              min_val=- 5.0, max_val=5.0, \
                                              units=ni.constants.VoltageUnits.VOLTS)
        if self.ui.ACQMode.currentText() in ['RptBline', 'RptAline']:
            self.AOtask.timing.cfg_samp_clk_timing(rate=self.Aline_freq, \
                                            source=self.ui.ClockTerm.toPlainText(), \
                                              sample_mode=Atype.CONTINUOUS)
        else:
            self.AOtask.timing.cfg_samp_clk_timing(rate=self.Aline_freq, \
                                            source=self.ui.ClockTerm.toPlainText(), \
                                              sample_mode=Atype.FINITE)
                
        self.AOtask.triggers.sync_type.MASTER = True
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
            
        self.AOtask.write(AOwaveform, auto_start = False)
        # Confiture Digital output task for stage control and digitizer trigger enabling
         
        self.DOtask.do_channels.add_do_chan(lines='AODO/port0/line0:3')
        if self.ui.ACQMode.currentText() in ['RptBline', 'RptAline']:
            self.DOtask.timing.cfg_samp_clk_timing(rate=self.Aline_freq, \
                                            source=self.ui.ClockTerm.toPlainText(), \
                                              sample_mode=Atype.CONTINUOUS)
        else:
            self.DOtask.timing.cfg_samp_clk_timing(rate=self.Aline_freq, \
                                            source=self.ui.ClockTerm.toPlainText(), \
                                              sample_mode=Atype.FINITE)
       
        self.DOtask.triggers.sync_type.SLAVE = True
        
        self.DOtask.write(DOwaveform, auto_start = False)
        return 'AODO configuration done'
            
    def StartOnce(self):
        self.DOtask.start()
        self.AOtask.start()
        self.AOtask.wait_until_done(timeout = 60)
        self.AOtask.stop()
        self.DOtask.stop()
            
    def StartContinuous(self):
        self.DOtask.start()
        self.AOtask.start()

    def StopContinuous(self):
        self.AOtask.stop()
        self.DOtask.stop()
        
    def CloseTask(self):
        try:
            self.DOtask.close()
        except:
            pass
        try:
            self.AOtask.close()
        except:
            pass
            