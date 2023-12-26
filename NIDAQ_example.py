# -*- coding: utf-8 -*-
"""
Created on Tue Dec 26 10:40:19 2023

@author: admin
"""
import nidaqmx as ni
from nidaqmx.constants import AcquisitionType as Atype
# from nidaqmx.constants import RegenerationMode as Rmode
# from nidaqmx.constants import Edge as Edge
# from nidaqmx.errors import DaqWarning as warnings
import time
import numpy as np

with ni.Task('AO task') as AOtask, ni.Task('DO task') as DOtask:

    AOtask.ao_channels.add_ao_voltage_chan(physical_channel='AODO/ao0', \
                                          min_val=- 10.0, max_val=10.0, \
                                          units=ni.constants.VoltageUnits.VOLTS)

    AOtask.timing.cfg_samp_clk_timing(rate=100000, \
                                    source='/AODO/PFI0', \
                                      sample_mode=Atype.CONTINUOUS)
    AOtask.triggers.sync_type.MASTER = True
    # task.triggers.start_trigger.cfg_dig_edge_start_trig(trigger_source='/AODO/PFI0', \
    #                                                     trigger_edge=Edge.RISING)
    AOtask.write(np.arange(-1,1,0.01), auto_start = False)

    DOtask.do_channels.add_do_chan(lines='AODO/port0/line0:2')
    DOtask.timing.cfg_samp_clk_timing(rate=100000, \
                                    source='/AODO/PFI0', \
                                      sample_mode=Atype.CONTINUOUS)
    DOtask.triggers.sync_type.SLAVE = True
    DOtask.write([0,1,0,1,2,1,0,1,0], auto_start = False)
    
    DOtask.start()
    AOtask.start()
    ii=0
    while not AOtask.is_task_done() and ii < 10:
        ii+=1
        time.sleep(1)

    AOtask.stop()
    DOtask.stop()
    
