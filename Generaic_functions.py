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
    steps1=preclocks
    # fly-back time in unit of clocks
    steps2=postclocks
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

def GenStageWave(one_cycle_samples, stageSpeed):
    # generate DO waveforms for moving stage
    return None

def GenAODO(mode, Aline_frq = 100000, XStepSize = 1, XSteps = 1000, AVG = 1, bias = 0, obj = 'OptoSigma5X',\
            preclocks = 50, postclocks = 200, YStepSize = 1, YSteps = 1000, BVG = 1):
    # DO clock is swept source A-line trigger at 100kHz
    if mode == 'RptAline':
        # RptAline is for checking Aline profile, we don't need to capture each Aline, only display 30 Alines per second\
        # if one wants to capture each Aline, they can set X and Y step size to be 0 and capture Cscan instead
        # 33 frames per second, how many samples for each frame
        one_cycle_samples = Aline_frq*0.03
        # trigger enbale waveform generation
        DOwaveform = np.append(np.zeros(one_cycle_samples-1000), np.ones(1000))
        status = 'waveform updated'
        return DOwaveform, None, status
    
    elif mode == 'SingleAline':
        # Single Aline is for checking Aline profile, only capture and display one Aline
        # 33 frames per second, how many samples for each frame
        one_cycle_samples = Aline_frq*0.03
        # trigger enbale waveform generation
        DOwaveform = np.append(np.zeros(one_cycle_samples-1000), np.ones(1000))
        status = 'waveform updated'
        return DOwaveform, None, status
    
    elif mode == 'RptBline':
        # RptBline is for checking Bline profile, only display 30 Blines per second
        # if one wants to capture each Bline, they can set Y stepsize to be 0 and capture Cscan instead
        # generate AO waveform for Galvo control
        AOwaveform, status = GenGalvoWave(XStepSize, XSteps, AVG, bias, obj, preclocks, postclocks)
        # total number of Alines
        one_cycle_samples = XSteps*AVG
        # generate trigger waveforms
        DOwaveform = np.append(np.zeros(preclocks), np.ones(one_cycle_samples))
        DOwaveform = np.append(DOwaveform, np.zeros(preclocks+postclocks))
        status = 'waveform updated'
        return DOwaveform, AOwaveform, status
    
    elif mode == 'SingleBline':
        # SingleBline is for checking Bline profile, only capture and display one Bline
        # generate AO waveform for Galvo control
        AOwaveform, status = GenGalvoWave(XStepSize, XSteps, AVG, bias, obj, preclocks, postclocks)
        # total number of Alines
        one_cycle_samples = XSteps*AVG
        # generate trigger waveforms
        DOwaveform = np.append(np.zeros(preclocks), np.ones(one_cycle_samples))
        DOwaveform = np.append(DOwaveform, np.zeros(preclocks+postclocks))
        status = 'waveform updated'
        return DOwaveform, AOwaveform, status
    
    elif mode == 'RptCscan':
        # RptCscan is for acquiring Cscan at the same location repeatitively
        # generate AO waveform for Galvo control
        AOwaveform, status = GenGalvoWave(XStepSize, XSteps, AVG, bias, obj, preclocks, postclocks)
        # total number of Alines
        one_cycle_samples = XSteps * AVG
        # generate trigger waveforms
        DOwaveform = np.append(np.zeros(preclocks), np.ones(one_cycle_samples))
        DOwaveform = np.append(DOwaveform, np.zeros(preclocks+postclocks))
        # calculate stage speed for Cscan
        stageSpeed=YStepSize/1000/(one_cycle_samples/Aline_frq) # unit: mm/s
        # generate stage control waveforms
        stagewaveform = GenStageWave(one_cycle_samples, stageSpeed)
        # append preclocks and postclocks
        stagewaveform = np.apped(np.zeros(preclocks), stagewaveform)
        stagewaveform = np.append(stagewaveform, np.zeros(preclocks+postclocks))
        # reshape into 1xN array shape
        DOwaveform = np.reshape(DOwaveform, [1,len(DOwaveform)])
        stagewaveform = np.reshape(stagewaveform, [1,len(stagewaveform)])
        # apped stagewaveform to trigger enable waveform 
        DOwaveform = np.append(DOwaveform, stagewaveform, axis= 0)
        status = 'waveform updated'
        return DOwaveform, AOwaveform, status
    
    elif mode == 'SingleCscan':
        # SingleCscan is for acquiring one Cscan at the current location
        # generate AO waveform for Galvo control
        AOwaveform, status = GenGalvoWave(XStepSize, XSteps, AVG, bias, obj, preclocks, postclocks)
        # total number of Alines
        one_cycle_samples = XSteps * AVG
        # generate trigger waveforms
        DOwaveform = np.append(np.zeros(preclocks), np.ones(one_cycle_samples))
        DOwaveform = np.append(DOwaveform, np.zeros(preclocks+postclocks))
        # calculate stage speed for Cscan
        stageSpeed=YStepSize/1000/(one_cycle_samples/Aline_frq) # unit: mm/s
        # generate stage control waveforms
        stagewaveform = GenStageWave(one_cycle_samples, stageSpeed)
        # append preclocks and postclocks
        stagewaveform = np.apped(np.zeros(preclocks), stagewaveform)
        stagewaveform = np.append(stagewaveform, np.zeros(preclocks+postclocks))
        # reshape into 1xN array shape
        DOwaveform = np.reshape(DOwaveform, [1,len(DOwaveform)])
        stagewaveform = np.reshape(stagewaveform, [1,len(stagewaveform)])
        # apped stagewaveform to trigger enable waveform 
        DOwaveform = np.append(DOwaveform, stagewaveform, axis= 0)
        status = 'waveform updated'
        return DOwaveform, AOwaveform, status
    
    elif mode == 'SurfScan':
        # SurfScan is for imaging the current surface with current stage height
        # generate AO waveform for Galvo control
        AOwaveform, status = GenGalvoWave(XStepSize, XSteps, AVG, bias, obj, preclocks, postclocks)
        # total number of Alines
        one_cycle_samples = XSteps * AVG
        # generate trigger waveforms
        DOwaveform = np.append(np.zeros(preclocks), np.ones(one_cycle_samples))
        DOwaveform = np.append(DOwaveform, np.zeros(preclocks+postclocks))
        # calculate stage speed for Cscan
        stageSpeed=YStepSize/1000/(one_cycle_samples/Aline_frq) # unit: mm/s
        # generate stage control waveforms
        stagewaveform = GenStageWave(one_cycle_samples, stageSpeed)
        # append preclocks and postclocks
        stagewaveform = np.apped(np.zeros(preclocks), stagewaveform)
        stagewaveform = np.append(stagewaveform, np.zeros(preclocks+postclocks))
        # reshape into 1xN array shape
        DOwaveform = np.reshape(DOwaveform, [1,len(DOwaveform)])
        stagewaveform = np.reshape(stagewaveform, [1,len(stagewaveform)])
        # apped stagewaveform to trigger enable waveform 
        DOwaveform = np.append(DOwaveform, stagewaveform, axis= 0)
        status = 'waveform updated'
        return DOwaveform, AOwaveform, status
    
    elif mode == 'SurfScan+Slice':
        # for serial sectioning OCT imaging
        # generate AO waveform for Galvo control
        AOwaveform, status = GenGalvoWave(XStepSize, XSteps, AVG, bias, obj, preclocks, postclocks)
        # total number of Alines
        one_cycle_samples = XSteps * AVG
        # generate trigger waveforms
        DOwaveform = np.append(np.zeros(preclocks), np.ones(one_cycle_samples))
        DOwaveform = np.append(DOwaveform, np.zeros(preclocks+postclocks))
        # calculate stage speed for Cscan
        stageSpeed=YStepSize/1000/(one_cycle_samples/Aline_frq) # unit: mm/s
        # generate stage control waveforms
        stagewaveform = GenStageWave(one_cycle_samples, stageSpeed)
        # append preclocks and postclocks
        stagewaveform = np.apped(np.zeros(preclocks), stagewaveform)
        stagewaveform = np.append(stagewaveform, np.zeros(preclocks+postclocks))
        # reshape into 1xN array shape
        DOwaveform = np.reshape(DOwaveform, [1,len(DOwaveform)])
        stagewaveform = np.reshape(stagewaveform, [1,len(stagewaveform)])
        # apped stagewaveform to trigger enable waveform 
        DOwaveform = np.append(DOwaveform, stagewaveform, axis= 0)
        status = 'waveform updated'
        return DOwaveform, AOwaveform, status
    
    elif mode == 'Slice':
        # for cutting once at current stage height
        
        DOwaveform, status = GenStageWave(one_cycle_samples, stageSpeed)
        status = 'waveform updated'
        return DOwaveform, None, status
    
    else:
        status = 'invalid task type! Abort action'
        return None, None, status
    
    
def GenMosaic(Xmin, Xmax, Ymin, Ymax, FOV, overlap=10):
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
    print(Xpositions)
    
    Ysteps = np.ceil((Ymax-Ymin)/stepsize)
    actualY=Ysteps*stepsize
    
    startY=Ymin-(actualY-(Ymax-Ymin))/2
    stopY = Ymax+(actualY-(Ymax-Ymin))/2+0.01
    
    Ypositions = np.arange(startY, stopY, stepsize)
    
    Positions = np.meshgrid(Xpositions, Ypositions)
    status = 'Mosaic Generation success'
    return Positions, status
    
    
def GenHeights(start, depth, Nplanes):
    return np.arange(start, start+Nplanes*depth/1000+0.01, depth/1000)

from PyQt5.QtGui import QPixmap, QImage

from matplotlib import pyplot as plt

def LinePlot(waveform):
    # clear content on plot
    plt.cla()
    # plot the new waveform
    plt.plot(range(len(waveform)),waveform)
    # plt.ylim(-2,2)
    #plt.ylabel('voltage(V)')
    plt.xticks(fontsize=15)
    plt.yticks(fontsize=15)
    plt.rcParams['savefig.dpi']=500
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
    # plt.ylim(-2,2)
    # plt.ylabel('voltage(V)')
    plt.xticks(fontsize=15)
    plt.yticks(fontsize=15)
    plt.rcParams['savefig.dpi']=500
    # save plot as jpeg
    plt.savefig('scatter.jpg')
    # load waveform image
    pixmap = QPixmap('scatter.jpg')
    return pixmap
    
def ImagePlot(matrix):
    # # clear content on plot
    # plt.cla()
    # # plot the new waveform
    # plt.imshow(matrix)
    # # plt.ylim(-2,2)
    # # plt.ylabel('voltage(V)')
    # plt.xticks(fontsize=15)
    # plt.yticks(fontsize=15)
    # plt.rcParams['savefig.dpi']=500
    # # save plot as jpeg
    # plt.savefig('Image.jpg')
    # # load waveform image
    # pixmap = QPixmap('Image.jpg')
    im = QImage(matrix.data, matrix.shape[1], matrix.shape[0], matrix.shape[1]*1, QImage.Format_Grayscale8)
    pixmap = QPixmap(im)
    return pixmap
    