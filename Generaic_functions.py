# -*- coding: utf-8 -*-
"""
Created on Mon Dec 11 19:41:46 2023

@author: admin
"""
# DO configure: port0 line 0 for X stage, port0 line 1 for Y stage, port 0 line 2 for Z stage, port 0 line 3 for Digitizer enable

# Generating Galvo X direction waveforms based on step size, Xsteps, Aline averages and objective
# StepSize in unit of um
# bias in unit of mm

import numpy as np
import os

class LOG():
    def __init__(self, ui):
        super().__init__()
        import datetime
        current_time = datetime.datetime.now()
        self.dir = os.getcwd() + '/log_files'
        if not os.path.exists(self.dir):
            os.makedirs(self.dir)
        self.filePath = self.dir +  "/" + 'log_'+\
            str(current_time.year)+'-'+\
            str(current_time.month)+'-'+\
            str(current_time.day)+'-'+\
            str(current_time.hour)+'-'+\
            str(current_time.minute)+'-'+\
            str(current_time.second)+'.txt'
    def write(self, message):
        fp = open(self.filePath, 'a')
        fp.write(message+'\n')
        fp.close()
        # return 0


def GenGalvoWave(StepSize = 1, Steps = 1000, AVG = 1, bias = 0, obj = 'OptoSigma5X', preclocks = 50, postclocks = 200, Galvo_bias = 3):
    
    # total number of steps is the product of steps and aline average number
    # use different angle to mm ratio for different objective
    if obj == 'OptoSigma5X':
        angle2mmratio = 2.094/1.19
    elif obj == 'OptoSigma10X':
        angle2mmratio = 2.094/2/1.19
    elif obj == 'OptoSigma20X':
        angle2mmratio = 2.094/1.19/4
        
    else:
        status = 'objective not calibrated, abort generating Galvo waveform'
        return None, status
    # X range is product of steps and step size
    Xrange = StepSize*Steps/1000
    # max voltage is converted from half of max X range plus bias divided by angle2mm ratio
    # extra division by 2 is because galvo angle change is only half of beam deviation angle
    Vmax = (Xrange/2+bias)/angle2mmratio/2+Galvo_bias
    Vmin = (-Xrange/2+bias)/angle2mmratio/2+Galvo_bias
    # step size of voltage
    stepsize = (Vmax-Vmin)/Steps/AVG
    # ramping up and down time in unit of clocks, i.e., A-lines
    steps1=preclocks
    # fly-back time in unit of clocks
    steps2=postclocks
    # linear waveform
    waveform=np.linspace(Vmin, Vmax, Steps*AVG)
    # print(len(waveform))
    # ramping up  waveform, change amplitude to match the slop with linear waveform
    Prewave = stepsize*steps1/np.pi*np.cos(np.arange(np.pi,3*np.pi/2,np.pi/2/steps1))+Vmin
    # ramping down wavefor, change amplitude to match the slop with linear waveform
    Postwave1 = stepsize*steps1/np.pi*np.sin(np.arange(0,np.pi/2,np.pi/2/steps1))+Vmax
    # fly-back waveform
    Postwave2 = (Vmax-Vmin+stepsize*steps1*2/np.pi)/2*np.cos(np.arange(0,np.pi,np.pi/steps2))+(Vmax+Vmin)/2
    # append all waveforms together
    waveform = np.append(Prewave, waveform)
    waveform = np.append(waveform, Postwave1)
    waveform = np.append(waveform, Postwave2)
    
    status = 'waveform updated'
    return waveform, status

def GenStageWave_ramp(distance, AlineTriggers, DISTANCE, STEPS):
    # distance: stage movement per Cscan , mm/s
    # edges: Aline triggers
    # how many motor steps to reach that distance
    steps = (distance/DISTANCE*STEPS)
    # how many Aline triggers per motor step
    clocks_per_motor_step = np.int16(AlineTriggers/steps)
    if clocks_per_motor_step < 2:
        clocks_per_motor_step = 2
    # print('clocks per motor step: ',clocks_per_motor_step)
    # generate stage movement that ramps up and down speed so that motor won't miss signal at beginning and end
    # ramping up: the interval between two steps should be 100 clocks at the beginning, then gradually decrease.vice versa for ramping down
    if np.abs(distance) > 0.01:
        max_interval = 80
    else:
        max_interval = 40
    # the interval for ramping up and down
    ramp_up_interval = np.arange(max_interval,clocks_per_motor_step,-2)
    ramp_down_interval = np.arange(clocks_per_motor_step,max_interval+1,2)
    ramping_steps = np.sum(len(ramp_down_interval)+len(ramp_up_interval)) # number steps used in ramping up and down process
    
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
    steps_left = steps - ramping_steps
    clocks_left = np.int32(AlineTriggers-len(ramp_down_waveform)-len(ramp_up_waveform))
    stride = round(clocks_left/steps_left)
    if stride < 2:
        stride = 2
    clocks_left = np.int32(steps_left * stride)
    stagewaveform = np.zeros(clocks_left)
    for ii in range(0,clocks_left,stride):
        stagewaveform[ii] = 1
    
    # append all arrays
    DOwaveform = np.append(ramp_up_waveform,stagewaveform)
    DOwaveform = np.append(DOwaveform,ramp_down_waveform)
    if len(DOwaveform) < AlineTriggers:
        DOwaveform = np.append(DOwaveform,np.zeros(AlineTriggers-len(DOwaveform),dtype = np.uint16))
    elif len(DOwaveform) > AlineTriggers:
        DOwaveform = DOwaveform[0:AlineTriggers]
    return DOwaveform

def GenAODO(mode='RptBline', Aline_frq = 100000, XStepSize = 1, XSteps = 1000, AVG = 1, bias = 0, obj = 'OptoSigma5X',\
            preclocks = 50, postclocks = 200, YStepSize = 1, YSteps = 200, BVG = 1, CSCAN_AXIS = pow(2, 1), Galvo_bias = 3, DISTANCE = 2, STEPS = 25000):
    # AVG: Aline average
    # BVG: Bline average
    # bias: Galvo bias voltage
    # preclocks: #Aline triggers for Galvo ramping up
    # postclocks: #Aline triggers for Galvo fly-back
    
    # DO clock is swept source A-line trigger at 100kHz
    # DO configure: port0 line 0 for X stage, port0 line 1 for Y stage, port 0 line 2 for Z stage, port 0 line 3 for Digitizer enable
    if mode == 'RptAline' or mode == 'SingleAline':
        # RptAline is for checking Aline profile, we don't need to capture each Aline, only display 30 Alines per second\
        # if one wants to capture each Aline, they can set X and Y step size to be 0 and capture Cscan instead
        # 33 frames per second, how many samples for each frame
        # trigger enbale waveform generation
        CscanAO = np.ones(BVG*(preclocks + XSteps * AVG + preclocks + postclocks)) * Galvo_bias
        status = 'waveform updated'
        return None, CscanAO, status
    
    elif mode == 'RptBline' or mode == 'SingleBline':
        # RptBline is for checking Bline profile, only display 30 Blines per second
        # if one wants to capture each Bline, they can set Y stepsize to be 0 and capture Cscan instead
        # generate AO waveform for Galvo control
        AOwaveform, status = GenGalvoWave(XStepSize, XSteps, AVG, bias, obj, preclocks, postclocks, Galvo_bias)
        CscanAO = np.tile(AOwaveform, BVG)
        status = 'waveform updated'
        return None, CscanAO, status
    
    
    elif mode in ['SingleCscan','Mosaic','Mosaic+Cut']:
        # RptCscan is for acquiring Cscan at the same location repeatitively
        # generate AO waveform for Galvo control for one Bline
        AOwaveform, status = GenGalvoWave(XStepSize, XSteps, AVG, bias, obj, preclocks, postclocks, Galvo_bias)
        CscanAO = np.tile(AOwaveform, YSteps*BVG)
            
        if YStepSize == 0:
            stagewave = np.zeros(len(AOwaveform))
        else:
            stagewave = GenStageWave_ramp(YSteps * YStepSize/1000, (XSteps*AVG + 2 * preclocks + postclocks)* YSteps * BVG, DISTANCE, STEPS)
        # append preclocks and postclocks
        stagewave = CSCAN_AXIS*stagewave
        # print('distance per Cscan: ',np.sum(stagewaveform)/STEPS*DISTANCE*1000/pow(2,CSCAN_AXIS),'um')
        
        status = 'waveform updated'
        return np.uint32(stagewave), CscanAO, status
    
    else:
        status = 'invalid task type! Abort action'
        return None, None, status
    

def GenMosaic_XYGalvo(Xmin, Xmax, Ymin, Ymax, FOV, overlap=10):
    # all arguments are with units mm
    # overlap is with unit %
    if Xmin > Xmax:
        status = 'Xmin is larger than Xmax, Mosaic generation failed'
        return None, status
    if Ymin > Ymax:
        status = 'Y min is larger than Ymax, Mosaic generation failed'
        return None, status
    # get FOV step size
    stepsize = FOV*(1-overlap/100)
    # get how many FOVs in X direction
    Xsteps = np.ceil((Xmax-Xmin)/stepsize)
    # get actual X range
    actualX=Xsteps*stepsize
    # generate start and stop position in X direction
    # add or subtract a small number to avoid precision loss
    startX=Xmin-(actualX-(Xmax-Xmin))/2
    stopX = Xmax+(actualX-(Xmax-Xmin))/2+0.01
    # generate X positions
    Xpositions = np.arange(startX, stopX, stepsize)
    #print(Xpositions)
    
    Ysteps = np.ceil((Ymax-Ymin)/stepsize)
    actualY=Ysteps*stepsize
    
    startY=Ymin-(actualY-(Ymax-Ymin))/2
    stopY = Ymax+(actualY-(Ymax-Ymin))/2+0.01
    
    Ypositions = np.arange(startY, stopY, stepsize)
    
    Positions = np.meshgrid(Xpositions, Ypositions)
    status = 'Mosaic Generation success'
    return Positions, status

class MOSAIC():
    # assume scanning direction is Y axis
    def __init__(self, x, ystart, ystop):
        super().__init__()
        self.x = x
        self.ystart = ystart
        self.ystop = ystop
        
def GenMosaic_XGalvo(Xmin, Xmax, Ymin, Ymax, FOV, overlap=10):
    # all arguments are with units mm
    # overlap is with unit %
    if Xmin > Xmax:
        status = 'Xmin is larger than Xmax, Mosaic generation failed'
        return None, status
    if Ymin > Ymax:
        status = 'Y min is larger than Ymax, Mosaic generation failed'
        return None, status
    if FOV < 0.001:
        return None, ''
    # get FOV step size
    stepsize = FOV*(1-overlap/100)
    # get how many FOVs in X direction
    Xsteps = np.ceil((Xmax-Xmin)/stepsize)
    # get actual X range
    actualX=Xsteps*stepsize
    # generate start and stop position in X direction
    # add or subtract a small number to avoid precision-induced error
    startX=Xmin-(actualX-(Xmax-Xmin))/2
    stopX = Xmax+(actualX-(Xmax-Xmin))/2+0.01
    # generate X positions
    pos = np.arange(startX, stopX, stepsize)
    #print(Xpositions)
    mosaic = []
    for ii, xpos in enumerate(pos):
        mosaic = np.append(mosaic, MOSAIC(xpos, Ymin, Ymax))

    status = "Mosaic Generation success..."
    return mosaic, status
    
    
def GenHeights(start, depth, Nplanes):
    return np.arange(start, start+Nplanes*depth/1000+0.01, depth/1000)

from PyQt5.QtGui import QPixmap

from matplotlib import pyplot as plt

def LinePlot(AOwaveform, DOwaveform = None, m=2, M=4):
    # clear content on plot
    plt.cla()
    # plot the new waveform
    plt.plot(range(len(AOwaveform)),AOwaveform,linewidth=2)
    if np.any(DOwaveform):
        plt.plot(range(len(DOwaveform)),DOwaveform,linewidth=2)
    # plt.ylim(np.min(AOwaveform)-0.2,np.max(AOwaveform)+0.2)
    # plt.ylim([m,M])
    plt.xticks(fontsize=15)
    plt.yticks(fontsize=15)
    plt.rcParams['savefig.dpi']=150
    # save plot as jpeg
    plt.savefig('lineplot.jpg')
    # load waveform image
    pixmap = QPixmap('lineplot.jpg')
    return pixmap

def ScatterPlot(mosaic):
    # clear content on plot
    plt.cla()
    # plot the new waveform
    plt.scatter(mosaic[0],mosaic[1])
    plt.plot(mosaic[0],mosaic[1])
    # plt.ylim(-2,2)
    plt.ylabel('Y stage',fontsize=15)
    plt.xlabel('X stage',fontsize=15)
    plt.xticks(fontsize=15)
    plt.yticks(fontsize=15)
    plt.rcParams['savefig.dpi']=150
    # save plot as jpeg
    plt.savefig('scatter.jpg')
    # load waveform image
    pixmap = QPixmap('scatter.jpg')
    return pixmap

import qimage2ndarray as qpy
def ImagePlot(matrix, m=0, M=1):
    matrix = np.array(matrix)
    matrix[matrix<m] = m
    matrix[matrix>M] = M
    # adjust image brightness
    data = np.uint8((matrix-m)/np.abs(M-m+0.00001)*255.0)
    try:
        im = qpy.gray2qimage(data)
        pixmap = QPixmap(im)
    except:
        print(data.shape)
        pixmap = QPixmap(qpy.gray2qimage(np.zeros(1000,1000)))
    return pixmap
    
def findchangept(signal, step):
    # python implementation of matlab function findchangepts
    L = len(signal)
    z = np.argmax(signal)
    last = np.min([z+30,L-2])
    signal = signal[1:last]
    L = len(signal)
    residual_error = np.ones(L)*9999999
    for ii in range(2,L-2,step):
        residual_error[ii] = (ii-1)*np.var(signal[0:ii])+(L-ii+1)*np.var(signal[ii+1:L])
    pts = np.argmin(residual_error)
    # plt.plot(residual_error[2:-2])
    return pts
        