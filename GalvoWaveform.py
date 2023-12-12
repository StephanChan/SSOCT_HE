# -*- coding: utf-8 -*-
"""
Created on Mon Dec 11 19:41:46 2023

@author: admin
"""

# Generating Galvo X direction waveforms based on step size, Xsteps, Aline averages and objective
# StepSize in unit of um
# bias in unit of mm
    
import numpy as np

def GenGalvoWave(StepSize = 1, Steps = 1000, AVG = 1, bias = 0, obj = 'OptoSigma5X'):

    # total number of steps is the product of steps and aline average number
    Steps = Steps*AVG
    # use different angle to mm ratio for different objective
    if obj == 'OptoSigma5X':
        angle2mmratio = 2.094/1.5
    elif obj == 'OptoSigma10X':
        angle2mmratio = 2.094/1.5
    else:
        status = 'objective not calibrated, abort generating Galvo waveform'
        return None, status
    # X range is product of steps and step size
    Xrange = StepSize*Steps/1000
    # max voltage is converted from half of max X range plus bias divided by angle2mm ratio
    # extra division by 2 is because galvo angle change is only half of beam deviation angle
    Vmax = (Xrange/2+bias)/angle2mmratio/2
    Vmin = (-Xrange/2+bias)/angle2mmratio/2
    # step size of voltage
    stepsize = (Vmax-Vmin)/Steps
    # ramping up and down time in unit of clocks, i.e., A-lines
    steps1=50
    # fly-back time in unit of clocks
    steps2=200
    # linear waveform
    waveform=np.arange(Vmin, Vmax, (Vmax-Vmin)/Steps)
    # ramping up  waveform, change amplitude to match the slop with linear waveform
    Prewave = stepsize*steps1/np.pi*np.cos(np.arange(np.pi,3*np.pi/2,np.pi/steps1))+Vmin
    # ramping down wavefor, change amplitude to match the slop with linear waveform
    Postwave1 = stepsize*steps1/np.pi*np.sin(np.arange(0,np.pi/2,np.pi/steps1))+Vmax
    # fly-back waveform
    Postwave2 = (Vmax-Vmin+stepsize*steps1*2/np.pi)/2*np.cos(np.arange(0,np.pi,np.pi/steps2))+(Vmax+Vmin)/2
    # append all waveforms together
    waveform = np.append(Prewave, waveform)
    waveform = np.append(waveform, Postwave1)
    waveform = np.append(waveform, Postwave2)
    
    status = 'waveform updated'
    return waveform, status
    
    
    
    
    