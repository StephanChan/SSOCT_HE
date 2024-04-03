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

# with ni.Task('AO task') as AOtask, ni.Task('DO task') as DOtask:
#     AOwaveform1 = np.arange(0,1,0.0001)
#     AOwaveform2 = np.arange(1,0,0.0001)
#     AOwaveform = np.append(AOwaveform1,AOwaveform2)
#     AOtask.ao_channels.add_ao_voltage_chan(physical_channel='AODO/ao1', \
#                                           min_val=- 10.0, max_val=10.0, \
#                                           units=ni.constants.VoltageUnits.VOLTS)
#     AOtask.timing.cfg_samp_clk_timing(rate=100000, \
#                                     source='/AODO/PFI0', \
#                                         active_edge= Edge.FALLING,\
#                                       sample_mode=Atype.CONTINUOUS,samps_per_chan=len(AOwaveform))
#     # AOtask.triggers.sync_type.MASTER = True
#     AOtask.triggers.start_trigger.cfg_dig_edge_start_trig("/AODO/PFI1")

#     AOtask.write(AOwaveform, auto_start = False)

#     DOtask.do_channels.add_do_chan(lines='AODO/port0/line0:7')
#     DOtask.timing.cfg_samp_clk_timing(rate=100000, \
#                                     source='/AODO/PFI0', \
#                                         active_edge= Edge.FALLING,\
#                                       sample_mode=Atype.CONTINUOUS,samps_per_chan=len(AOwaveform))
#     # DOtask.triggers.sync_type.SLAVE = True
#     DOtask.triggers.start_trigger.cfg_dig_edge_start_trig("/AODO/PFI1")
#     # DOwaveform = np.uint32(np.append(np.zeros(np.int32(len(AOwaveform)/2)),8*np.ones(np.int32(len(AOwaveform)/2))))
#     DOwaveform = [0,0,0,0,0,0,0,0,0,0,8,8,8,8,8,8,8,8,8]
#     DOtask.write(DOwaveform, auto_start = False)
    
#     DOtask.start()
#     AOtask.start()
#     time.sleep(5)
#     # AOtask.wait_until_done(timeout =21)
        
    
#     DOtask.stop()
#     AOtask.stop()
    
    
settingtask = ni.Task('vibratome')
settingtask.do_channels.add_do_chan(lines='AODO/PFI2')
settingtask.write(True, auto_start = True)
time.sleep(0.1)
settingtask.stop()
settingtask.close()
