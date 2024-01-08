# -*- coding: utf-8 -*-
"""
Created on Mon Dec 11 19:41:46 2023

@author: admin
"""

# Generating Galvo X direction waveforms based on step size, Xsteps, Aline averages and objective
# StepSize in unit of um
# bias in unit of mm
    
import numpy as np

def GenGalvoWave(StepSize = 1, Steps = 1000, AVG = 1, bias = 0, obj = 'OptoSigma5X', preclocks = 50, postclocks = 200):

    # total number of steps is the product of steps and aline average number
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
    stepsize = (Vmax-Vmin)/Steps/AVG
    # ramping up and down time in unit of clocks, i.e., A-lines
    steps1=preclocks
    # fly-back time in unit of clocks
    steps2=postclocks
    # linear waveform
    waveform=np.arange(Vmin, Vmax, stepsize)
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

def GenStageWave(one_cycle_samples, stageSpeed):
    # generate DO waveforms for moving stage
    return np.ones(one_cycle_samples)

def GenAODO(mode='RptBline', Aline_frq = 100000, XStepSize = 1, XSteps = 1000, AVG = 1, bias = 0, obj = 'OptoSigma5X',\
            preclocks = 50, postclocks = 200, YStepSize = 1, YSteps = 200, BVG = 1):
    # DO clock is swept source A-line trigger at 100kHz
    # DO configure: port0 line 0 for X stage, port0 line 1 for Y stage, port 0 line 2 for Z stage, port 0 line 3 for Digitizer enable
    if mode == 'RptAline' or mode == 'SingleAline':
        # RptAline is for checking Aline profile, we don't need to capture each Aline, only display 30 Alines per second\
        # if one wants to capture each Aline, they can set X and Y step size to be 0 and capture Cscan instead
        # 33 frames per second, how many samples for each frame
        one_cycle_samples = np.int32(Aline_frq*0.03)
        # trigger enbale waveform generation
        DOwaveform = np.append(np.zeros(one_cycle_samples-100), pow(2,3)*np.ones(100))
        CscanAO = np.zeros(BVG*len(DOwaveform))
        CscanDO = np.zeros(BVG*len(DOwaveform))
        for ii in range(BVG):
            CscanDO[ii*len(DOwaveform):(ii+1)*len(DOwaveform)] = DOwaveform
        status = 'waveform updated'
        return np.uint32(CscanDO), CscanAO, status
    
    elif mode == 'RptBline' or mode == 'SingleBline':
        # RptBline is for checking Bline profile, only display 30 Blines per second
        # if one wants to capture each Bline, they can set Y stepsize to be 0 and capture Cscan instead
        # generate AO waveform for Galvo control
        AOwaveform, status = GenGalvoWave(XStepSize, XSteps, AVG, bias, obj, preclocks, postclocks)
        
        # total number of Alines
        one_cycle_samples = XSteps*AVG
        # generate trigger waveforms
        DOwaveform = np.append(np.zeros(preclocks), pow(2,3)*np.ones(one_cycle_samples))
        DOwaveform = np.append(DOwaveform, np.zeros(preclocks+postclocks))
        CscanAO = np.zeros(BVG*len(AOwaveform))
        CscanDO = np.zeros(BVG*len(DOwaveform))
        for ii in range(BVG):
            CscanAO[ii*len(AOwaveform):(ii+1)*len(AOwaveform)] = AOwaveform
            CscanDO[ii*len(AOwaveform):(ii+1)*len(AOwaveform)] = DOwaveform
        status = 'waveform updated'
        return np.uint32(CscanDO), CscanAO, status
    
    
    elif mode in ['RptCscan','SingleCscan','SurfScan','SurfScan+Slice']:
        # RptCscan is for acquiring Cscan at the same location repeatitively
        # generate AO waveform for Galvo control for one Bline
        AOwaveform, status = GenGalvoWave(XStepSize, XSteps, AVG, bias, obj, preclocks, postclocks)
        # total number of Alines
        one_cycle_samples = XSteps * AVG
        # generate trigger waveforms
        DOwaveform = np.append(np.zeros(preclocks), pow(2,3)*np.ones(one_cycle_samples))
        DOwaveform = np.append(DOwaveform, np.zeros(preclocks+postclocks))
        # calculate stage speed for Cscan
        stageSpeed=YStepSize/1000/(len(AOwaveform)/Aline_frq) # unit: mm/s
        # generate stage control waveforms for one step
        stagewaveform = GenStageWave(one_cycle_samples, stageSpeed)
        # append preclocks and postclocks
        stagewaveform = np.append(np.zeros(preclocks), pow(2,0)*stagewaveform)
        stagewaveform = np.append(stagewaveform, np.zeros(preclocks+postclocks))
        # add stagewaveform with trigger enable waveform for DOwaveform
        DOwaveform = DOwaveform + stagewaveform
        # repeat the waveform for whole Cscan
        CscanAO = np.zeros(YSteps*BVG*len(AOwaveform))
        CscanDO = np.zeros(YSteps*BVG*len(DOwaveform))
        for ii in range(YSteps*BVG):
            CscanAO[ii*len(AOwaveform):(ii+1)*len(AOwaveform)] = AOwaveform
            CscanDO[ii*len(AOwaveform):(ii+1)*len(AOwaveform)] = DOwaveform
        status = 'waveform updated'
        return np.uint32(CscanDO), CscanAO, status

    
    elif mode == 'Slice':
        # for cutting once at current stage height
        
        DOwaveform, status = GenStageWave(one_cycle_samples, stageSpeed)
        status = 'waveform updated'
        return np.uint32(DOwaveform), None, status
    
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

    status = 'Mosaic Generation success'
    return mosaic, status
    
    
def GenHeights(start, depth, Nplanes):
    return np.arange(start, start+Nplanes*depth/1000+0.01, depth/1000)

from PyQt5.QtGui import QPixmap

from matplotlib import pyplot as plt

def LinePlot(AOwaveform, DOwaveform = None):
    # clear content on plot
    plt.cla()
    # plot the new waveform
    plt.plot(range(len(AOwaveform)),AOwaveform,linewidth=2)
    if np.any(DOwaveform):
        plt.plot(range(len(DOwaveform)),(DOwaveform>>3)*np.max(AOwaveform),linewidth=2)
    plt.ylim(np.min(AOwaveform)-0.2,np.max(AOwaveform)+0.2)

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
def ImagePlot(matrix):
    # select image brightness level
    M=np.max(matrix)
    level = -6
    while M > pow(10,level):
        level +=1
    # im = QImage(matrix, matrix.shape[1], matrix.shape[0], QImage.Format_Grayscale8)
    # adjust image brightness
    data = np.uint8(matrix/pow(10,level)*255.0*2)
    im = qpy.gray2qimage(data)
    pixmap = QPixmap(im)
    return pixmap
    