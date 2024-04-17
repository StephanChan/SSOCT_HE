# -*- coding: utf-8 -*-
"""
Created on Fri Jan 26 10:38:52 2024

@author: admin
"""

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

with ni.Task('DO task') as DOtask, ni.Task('setting') as settingtask:
    settingtask.do_channels.add_do_chan(lines='AODO/port2/line0:1')
    direction = 0 # or 0
    enable = 0 # or 0
    settingtask.write(direction+enable, auto_start = True)
    # 25000 steps per revolve
    # 2mm per revolve
    distance = 5 # mm
    speed = 2 # mm/s
    DOwaveform = np.ones([25000//2*distance, 2],dtype = np.uint32)
    DOwaveform[:,1] = 0
    DOwaveform=DOwaveform.flatten()
    DOtask.do_channels.add_do_chan(lines='AODO/port0/line0:7')
    DOtask.timing.cfg_samp_clk_timing(rate=25000*2//2*speed, \
                                    # source='/AODO/InternalClock', \
                                        active_edge= Edge.FALLING,\
                                      sample_mode=Atype.FINITE,samps_per_chan=len(DOwaveform))
    # DOtask.triggers.sync_type.SLAVE = True
    # DOtask.triggers.start_trigger.cfg_dig_edge_start_trig("/AODO/PFI1")
    # DOwaveform = np.uint32(np.append(np.zeros(np.int32(len(AOwaveform)/2)),8*np.ones(np.int32(len(AOwaveform)/2))))

    DOtask.write(DOwaveform, auto_start = True)
    
    DOtask.wait_until_done(timeout =20)
        
    
    DOtask.stop()
    settingtask.write(1, auto_start = True)
    settingtask.stop()
    
    
    
