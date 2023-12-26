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
from Generaic_functions import GenGalvoWave
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
            else:
                self.ui.statusbar.showMessage('stage thread is doing something undefined: '+self.item.action)
            self.item = self.queue.get()
            

    def ConfigONECscan(self, axis = 'X'):
        with ni.Task('AO task') as self.AOtask, ni.Task('DO task') as self.DOtask:
            # Configure Analog output task for Galvo control
            self.AOtask.ao_channels.add_ao_voltage_chan(physical_channel='AODO/ao0', \
                                                  min_val=- 5.0, max_val=5.0, \
                                                  units=ni.constants.VoltageUnits.VOLTS)

            self.AOtask.timing.cfg_samp_clk_timing(rate=100000, \
                                            source=self.ui.ClockTerm.currentText(), \
                                              sample_mode=Atype.FINITE)
            self.AOtask.triggers.sync_type.MASTER = True
            waveform,status = GenGalvoWave(self.ui.XStepSize.value(),\
                                            self.ui.Xsteps.value(),\
                                            self.ui.AlineAVG.value(),\
                                            self.ui.XBias.value(),\
                                            self.ui.Objective.currentText(),\
                                            self.ui.PreClock.value(),\
                                            self.ui.PostClock.value())
            self.AOtask.write(waveform, auto_start = False)
            # Confiture Digital output task for stage control and digitizer trigger enabling
             
            self.DOtask.do_channels.add_do_chan(lines='AODO/port0/line0:3')
            self.DOtask.timing.cfg_samp_clk_timing(rate=100000, \
                                            source=self.ui.ClockTerm.currentText(), \
                                              sample_mode=Atype.FINITE)
            self.DOtask.triggers.sync_type.SLAVE = True
            if axis == 'X':
                pass # generate X stage waveform as well as digitizer trigger enabling waveform
            elif axis == 'Y':
                pass # generate Y stage waveform as well as digitizer trigger enabling waveform
            self.DOtask.write([0,2,0,2,1,2,0,2,0], auto_start = False)
            
    def NextCscan(self):
            self.DOtask.start()
            self.AOtask.start()
            self.AOtask.wait_until_done(timeout = 60)
            self.AOtask.stop()
            self.DOtask.stop()
            