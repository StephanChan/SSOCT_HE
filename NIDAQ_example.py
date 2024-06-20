# -*- coding: utf-8 -*-
"""
Created on Tue Dec 26 10:40:19 2023

@author: admin
"""
import nidaqmx as ni
from nidaqmx.constants import AcquisitionType as Atype
from nidaqmx.constants import Edge
# from nidaqmx.constants import RegenerationMode as Rmode
# from nidaqmx.constants import Edge as Edge
# from nidaqmx.errors import DaqWarning as warnings
import time
import numpy as np

class AODO(object):
    def __init__(self):
        super().__init__()
        self.AOtask = None
        self.DOtask = None
        
    def config(self):
        self.AOtask = ni.Task('AO task') 
        self.DOtask = ni.Task('DO task')
        AOwaveform1 = np.arange(0,0.2,0.000001)
        AOwaveform2 = np.arange(0.2,0,0.000001)
        AOwaveform = np.append(AOwaveform1,AOwaveform2)
        self.AOtask.ao_channels.add_ao_voltage_chan(physical_channel='AODO/ao1', \
                                              min_val=- 10.0, max_val=10.0, \
                                              units=ni.constants.VoltageUnits.VOLTS)
        self.AOtask.timing.cfg_samp_clk_timing(rate=100000, \
                                        source='/AODO/PFI0', \
                                            active_edge= Edge.FALLING,\
                                          sample_mode=Atype.FINITE,samps_per_chan=len(AOwaveform))
        # AOtask.triggers.sync_type.MASTER = True
        # self.AOtask.triggers.start_trigger.cfg_dig_edge_start_trig("/AODO/PFI1")
    

    
        self.DOtask.do_channels.add_do_chan(lines='AODO/port0/line0:7')
        self.DOtask.timing.cfg_samp_clk_timing(rate=100000, \
                                        source='/AODO/PFI0', \
                                            active_edge= Edge.FALLING,\
                                          sample_mode=Atype.FINITE,samps_per_chan=len(AOwaveform))
        # DOtask.triggers.sync_type.SLAVE = True
        # self.DOtask.triggers.start_trigger.cfg_dig_edge_start_trig("/AODO/PFI1")
        # DOwaveform = np.uint32(np.append(np.zeros(np.int32(len(AOwaveform)/2)),8*np.ones(np.int32(len(AOwaveform)/2))))
        DOwaveform = np.zeros(len(AOwaveform), dtype = np.uint32)
        self.DOtask.write(DOwaveform, auto_start = False)
        self.AOtask.write(AOwaveform, auto_start = False)
    def start(self):
        self.DOtask.start()
        self.AOtask.start()
    def stop(self):
        self.AOtask.wait_until_done(timeout = 5)
        self.AOtask.stop()
        self.DOtask.stop()
    def close(self):
        self.AOtask.close()
        self.DOtask.close()
    
    
# settingtask = ni.Task('vibratome')
# settingtask.do_channels.add_do_chan(lines='AODO/PFI2')
# settingtask.write(True, auto_start = True)
# time.sleep(0.1)
# settingtask.stop()
# settingtask.close()
if __name__ == '__main__':
    func = AODO()
    func.config()
    for ii in range(2):
        start = time.time()
        
        
        # func.stop()
        func.start()
        func.stop() # you can stop myltiple times, it's ok
        print('time elapsed: ',round(time.time()-start,3))
    
    func.close()
    
