
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 18:26:44 2023

@author: admin
"""

from PyQt5.QtCore import  QThread
from Generaic_functions import LinePlot, ImagePlot
import numpy as np
import traceback
global SCALE
SCALE =65535
import matplotlib.pyplot as plt
from scipy.signal import hilbert
import datetime

class DnSThread(QThread):
    def __init__(self):
        super().__init__()
        self.surf = []
        self.sliceNum = 1
        self.tileNum = 1
        self.BlineNum = 1
        self.CscanNum = 1
        self.totalTiles = 0
        self.display_actions = 0
        
    def run(self):
        self.QueueOut()
        
    def QueueOut(self):
        num = 0
        self.item = self.queue.get()
        while self.item.action != 'exit':
            #self.ui.statusbar.showMessage('Display thread is doing ' + self.item.action)
            try:
                if self.item.action in ['SingleAline','RptAline']:
                    
                    self.Display_aline(self.item.data, self.item.raw)
                
                elif self.item.action in ['SingleBline','RptBline']:
                    self.Display_bline(self.item.data, self.item.raw)
                    self.display_actions += 1
                    
                elif self.item.action in ['SingleCscan','RptCscan']:
                    self.Display_Cscan(self.item.data, self.item.raw)
                elif self.item.action == 'SurfScan':
                    self.Display_SurfScan(self.item.data, self.item.raw, self.item.args)
                
                elif self.item.action == 'Clear':
                    self.surf = []
                elif self.item.action == 'UpdateContrastXY':
                    self.Update_contrast_XY()
                elif self.item.action == 'UpdateContrastXYZ':
                    self.Update_contrast_XYZ()
                elif self.item.action == 'UpdateContrastSurf':
                    self.Update_contrast_Surf()
                elif self.item.action == 'dispersionCompensation':
                    self.dispersion_compensation()
                elif self.item.action == 'getBackground':
                    self.getBackground()
                elif self.item.action == 'display_counts':
                    self.print_display_counts()
                    
                else:
                    
                    self.ui.statusbar.showMessage('Display and save thread is doing something invalid' + self.item.action)
            except Exception as error:
                self.ui.statusbar.showMessage("\nAn error occurred:"+" skip the display and save action\n")
                print(traceback.format_exc())
            num+=1
            # print(num, 'th display\n')
            self.item = self.queue.get()
        current_message = self.ui.statusbar.currentMessage()
        self.ui.statusbar.showMessage(current_message+"Display and save Thread successfully exited...")
            
    def print_display_counts(self):
        print( self.display_actions, ' Blines displayed\n')
        self.display_actions = 0
        
    def Display_aline(self, data, raw = False):
        #data = ctypes.cast(data_address, ctypes.py_object).value 
        # TODO: make sure fft is shifted
        # check if displaying before FFT
        if not raw:
            Zpixels = self.ui.DepthRange.value()
        else:
            if self.Digitizer == 'ATS9351':
                Zpixels = self.ui.PreSamples.value()+self.ui.PostSamples.value()
                # data = np.float32(data/pow(2,16))
            elif self.Digitizer == 'ART8912':
                Zpixels = self.ui.PostSamples_2.value()
                # data = np.float32(data/pow(2,12))
        Xpixels = 10
        Yrpt = self.ui.BlineAVG.value()
        data = data.reshape([Yrpt,Xpixels,Zpixels])
        # data in original state
        if self.Digitizer == 'ART8912' and raw:
            Zpixels = self.ui.PostSamples_2.value() - self.ui.DelaySamples.value()
            data = data[:,:,self.ui.DelaySamples.value():]
        self.Aline = data
        
        data = np.float32(np.mean(data,0))
        data = data[1,:]
        # float32 data type
        pixmap = LinePlot(data, [], self.ui.XYmin.value(), self.ui.XYmax.value())
        # clear content on the waveformLabel
        self.ui.XZplane.clear()
        # update iamge on the waveformLabel
        self.ui.XZplane.setPixmap(pixmap)
    
    def Display_bline(self, data, raw = False):
        if not raw:
            Zpixels = self.ui.DepthRange.value()
        else:
            if self.Digitizer == 'ATS9351':
                Zpixels = self.ui.PreSamples.value()+self.ui.PostSamples.value()
                # data = np.float32(data/pow(2,16))
            elif self.Digitizer == 'ART8912':
                Zpixels = self.ui.PostSamples_2.value()
                # data = np.float32(data/pow(2,12))
        Xpixels = self.ui.Xsteps.value()*self.ui.AlineAVG.value()
        if self.Digitizer == 'ART8912':
            Xpixels = Xpixels + self.ui.PreClock.value()*2
        Yrpt = self.ui.BlineAVG.value()
        
        data = data.reshape([Yrpt,Xpixels,Zpixels])
        if self.Digitizer == 'ART8912' and raw:
            Zpixels = self.ui.PostSamples_2.value() - self.ui.DelaySamples.value()
            data = data[:,:,self.ui.DelaySamples.value():]
        # data in original state
        self.Bline = data
        data = np.float32(np.mean(data,0))
        data = np.transpose(data).copy()

        pixmap = ImagePlot(data, self.ui.XYmin.value(), self.ui.XYmax.value())
        # clear content on the waveformLabel
        self.ui.XZplane.clear()
        # update iamge on the waveformLabel
        self.ui.XZplane.setPixmap(pixmap)
        
        if self.ui.Save.isChecked():
            if raw:
                data = np.uint16(self.Bline)
            else:
                data = np.uint16(self.Bline/SCALE*65535)
            self.WriteData(data, self.BlineFilename([Yrpt,Xpixels,Zpixels]))
        
    def Display_Cscan(self, data, raw = False):
        if not raw:
            Zpixels = self.ui.DepthRange.value()
        else:
            if self.Digitizer == 'ATS9351':
                Zpixels = self.ui.PreSamples.value()+self.ui.PostSamples.value()
                # data = np.float32(data/pow(2,16))
            elif self.Digitizer == 'ART8912':
                Zpixels = self.ui.PostSamples_2.value()
                # data = np.float32(data/pow(2,12))
        Xpixels = self.ui.Xsteps.value()*self.ui.AlineAVG.value()
        if self.Digitizer == 'ART8912':
            Xpixels = Xpixels + self.ui.PreClock.value()*2
        Ypixels = self.ui.Ysteps.value()*self.ui.BlineAVG.value()
        data = data.reshape([Ypixels,Xpixels,Zpixels])
        if self.Digitizer == 'ART8912' and raw:
            Zpixels = self.ui.PostSamples_2.value() - self.ui.DelaySamples.value()
            data = data[:,:,self.ui.DelaySamples.value():]
        # data in original state
        self.Cscan = data

        plane = np.transpose(data[0,:,:]).copy()# has to be first index, otherwise the memory space is not continuous
        pixmap = ImagePlot(plane, self.ui.XYmin.value(), self.ui.XYmax.value())
        # clear content on the waveformLabel
        self.ui.XZplane.clear()
        # update image on the waveformLabel
        self.ui.XZplane.setPixmap(pixmap)
        
        plane = np.mean(data,2)# has to be first index, otherwise the memory space is not continuous
        pixmap = ImagePlot(plane, self.ui.XYmin.value(), self.ui.XYmax.value())
        # clear content on the waveformLabel
        self.ui.XYplane.clear()
        # update image on the waveformLabel
        self.ui.XYplane.setPixmap(pixmap)
        ###################### plot 3D visulaization
        self.ui.mayavi_widget.visualization.update_data(self.Cscan/500)
        if self.ui.Save.isChecked():
            if raw:
                data = np.uint16(self.Cscan)
            else:
                data = np.uint16(self.Cscan/SCALE*65535)
            self.WriteData(data, self.CscanFilename([Ypixels,Xpixels,Zpixels]))
        
        
        
        
    def Display_SurfScan(self, data, raw = False, args = []):
        if not raw:
            Zpixels = self.ui.DepthRange.value()
        else:
            if self.Digitizer == 'ATS9351':
                Zpixels = self.ui.PreSamples.value()+self.ui.PostSamples.value()
                # data = np.float32(data/pow(2,16))
            elif self.Digitizer == 'ART8912':
                Zpixels = self.ui.PostSamples_2.value()
                # data = np.float32(data/pow(2,12))
        Xpixels = self.ui.Xsteps.value()*self.ui.AlineAVG.value()
        if self.Digitizer == 'ART8912':
            Xpixels = Xpixels + self.ui.PreClock.value()*2
        Ypixels = self.ui.Ysteps.value()*self.ui.BlineAVG.value()
        data = data.reshape([Ypixels,Xpixels,Zpixels])
        
        if self.Digitizer == 'ART8912' and raw:
            Zpixels = self.ui.PostSamples_2.value() - self.ui.DelaySamples.value()
            data = data[:,:,self.ui.DelaySamples.value():]
        
        #######################################
        # for even strips, need to flip data in Y dimension because scanning was in backward direction
        surfX = args[1][0]
        surfY = np.int32(args[1][1]/args[1][0])
        fileY = args[0][1]-1
        if np.mod(fileY,2) == 0:
            fileX = args[0][0]
        else:
            fileX = surfX - args[0][0]-1
            
        if np.mod(fileY,2)==1:
            data = np.flip(data,0)
        #######################################
        
        self.Cscan = data
        
        plane = np.transpose(data[0,:,:]).copy()# has to be first index, otherwise the memory space is not continuous
        pixmap = ImagePlot(plane, self.ui.XYmin.value(), self.ui.XYmax.value())
        # clear content on the waveformLabel
        self.ui.XZplane.clear()
        # update image on the waveformLabel
        self.ui.XZplane.setPixmap(pixmap)
        
        plane = np.mean(data,2)
        pixmap = ImagePlot(plane, self.ui.XYmin.value(), self.ui.XYmax.value())
        # clear content on the waveformLabel
        self.ui.XYplane.clear()
        # update iamge on the waveformLabel
        self.ui.XYplane.setPixmap(pixmap)
        
        scale = 2

        ###################### plot 3D visulaization
        self.ui.mayavi_widget.visualization.update_data(self.Cscan/500)
        
        self.totalTiles = args[1][1]
        if not np.any(self.surf):
            self.surf = np.zeros([ surfX*Ypixels//scale,surfY*Xpixels//scale],dtype = np.float32)
        
        self.surf[Ypixels//scale*fileX:Ypixels//scale*(fileX+1),Xpixels//scale*fileY:Xpixels//scale*(fileY+1)] = plane[::scale,::scale]
        pixmap = ImagePlot(self.surf, self.ui.Surfmin.value(), self.ui.Surfmax.value())
        # clear content on the waveformLabel
        self.ui.SampleMosaic.clear()
        # update iamge on the waveformLabel
        self.ui.SampleMosaic.setPixmap(pixmap)
        if self.ui.Save.isChecked():
            if raw:
                data = np.uint16(self.Cscan)
            else:
                data = np.uint16(self.Cscan/SCALE*65535)
            self.WriteData(data, self.SurfFilename([Ypixels,Xpixels,Zpixels]))

            
    def Update_contrast_XY(self):
        if self.ui.ACQMode.currentText() in ['SingleAline', 'RptAline']:
            data = np.float32(np.mean(self.Aline,0))
            data = data[0,:]
            # if self.ui.LOG.currentText() == '10log10':
            #     data=10*np.log10(data+0.000001)
            pixmap = LinePlot(data, [], self.ui.XYmin.value(), self.ui.XYmax.value())
            # clear content on the waveformLabel
            self.ui.XZplane.clear()
            # update iamge on the waveformLabel
            self.ui.XZplane.setPixmap(pixmap)
        elif self.ui.ACQMode.currentText() in ['SingleBline', 'RptBline']:
            data = np.float32(np.mean(self.Bline,0))
            data = np.transpose(data).copy()
            # data = np.flip(data, 1).copy()
            # if self.ui.LOG.currentText() == '10log10':
            #     data=np.float32(10*np.log10(data+0.000001))
            pixmap = ImagePlot(data, self.ui.XYmin.value(), self.ui.XYmax.value())
            # clear content on the waveformLabel
            self.ui.XZplane.clear()
            # update iamge on the waveformLabel
            self.ui.XZplane.setPixmap(pixmap)
        elif self.ui.ACQMode.currentText() in ['SurfScan','SurfScan+Slice', 'SingleCscan']:
            data = self.Cscan
            
            plane = np.transpose(data[0,:,:]).copy()# has to be first index, otherwise the memory space is not continuous
            pixmap = ImagePlot(plane, self.ui.XYmin.value(), self.ui.XYmax.value())
            # clear content on the waveformLabel
            self.ui.XZplane.clear()
            # update image on the waveformLabel
            self.ui.XZplane.setPixmap(pixmap)
            
            plane = np.mean(data,2)# has to be first index, otherwise the memory space is not continuous
            pixmap = ImagePlot(plane, self.ui.XYmin.value(), self.ui.XYmax.value()/4)
            # clear content on the waveformLabel
            self.ui.XYplane.clear()
            # update image on the waveformLabel
            self.ui.XYplane.setPixmap(pixmap)
            
    def Update_contrast_Surf(self):
        
        pixmap = ImagePlot(self.surf, self.ui.Surfmin.value(), self.ui.Surfmax.value())
        # clear content on the waveformLabel
        self.ui.SampleMosaic.clear()
        # update iamge on the waveformLabel
        self.ui.SampleMosaic.setPixmap(pixmap)
            
    def Update_contrast_XYZ(self):
        self.ui.mayavi_widget.visualization.update_contrast(self.ui.XYZmin.value(), self.ui.XYZmax.value())
        
    def SurfFilename(self, shape):
        if self.tileNum <= self.totalTiles:
            filename = 'slice-'+str(self.sliceNum)+'-tile-'+str(self.tileNum)+'-Y'+str(shape[0])+'-X'+str(shape[1])+'-Z'+str(shape[2])+'.bin'
            self.tileNum = self.tileNum + 1
        else:
            self.sliceNum = self.sliceNum + 1
            self.tileNum = 1
            filename = 'slice-'+str(self.sliceNum)+'-tile-'+str(self.tileNum)+'-Y'+str(shape[0])+'-X'+str(shape[1])+'-Z'+str(shape[2])+'.bin'
        return filename
    
    def CscanFilename(self, shape):
        filename = 'Cscan-'+str(self.CscanNum)+'-Y'+str(shape[0])+'-X'+str(shape[1])+'-Z'+str(shape[2])+'.bin'
        self.CscanNum = self.CscanNum + 1
        return filename
    
    def BlineFilename(self, shape):
        filename = 'Bline-'+str(self.BlineNum)+'-Yrpt'+str(shape[0])+'-X'+str(shape[1])+'-Z'+str(shape[2])+'.bin'
        self.BlineNum = self.BlineNum + 1
        return filename

    def WriteData(self, data, filename):
        filePath = self.ui.DIR.toPlainText()
        filePath = filePath + "/" + filename
        # print(filePath)
        import time
        start = time.time()
        fp = open(filePath, 'wb')
        data.tofile(fp)
        fp.close()
        print('time for saving: ', time.time()-start)
        
    def dispersion_compensation(self):
        S = self.Aline.shape
        # print(S)
        ALINE = self.Aline.reshape([S[0]*S[1],S[2]])
        Aline = np.float32(ALINE[0,:])-2048
        plt.figure()
        plt.plot(np.abs(Aline))
        
        L=len(Aline)
        fR=np.fft.fft(Aline)/L # FFT of interference signal

        plt.figure()
        plt.plot(np.abs(fR[20:]))
        
        z = np.argmax(np.abs(fR[50:300]))+50
        low_position = max(10,z-75)
        high_position = min(L//2,z+75)

        fR[0:low_position]=0
        fR[high_position:L-high_position]=0
        fR[L-low_position:]=0
        
        plt.figure()
        plt.plot(np.abs(fR))
        
        Aline = np.fft.ifft(fR)

        hR=hilbert(np.real(Aline))
        hR_phi=np.unwrap(np.angle(hR))
        
        phi_delta=np.linspace(hR_phi[0],hR_phi[L-1],L)
        phi_diff=np.float32(phi_delta-hR_phi)
        ALINE = ALINE*np.exp(1j*phi_diff)
        
        plt.figure()
        plt.plot(phi_diff)
        # plt.figure()
        print('max phase difference is: ',np.max(np.abs(phi_diff)))
        # fR = np.fft.fft(ALINE, axis=1)/L

        # fR = np.abs(fR[:,self.ui.DepthStart.value():self.ui.DepthStart.value()+self.ui.DepthRange.value()])
        # # self.ui.MaxContrast.setValue(0.1)
        # self.Display_aline(fR, raw = False)
        
        filePath = self.ui.DIR.toPlainText()

        current_time = datetime.datetime.now()
        filePath = filePath + "/" + 'dispersion_compensation_'+\
            str(current_time.year)+'-'+\
            str(current_time.month)+'-'+\
            str(current_time.day)+'-'+\
            str(current_time.hour)+'-'+\
            str(current_time.minute)+\
            '.bin'
        fp = open(filePath, 'wb')
        phi_diff.tofile(fp)
        fp.close()
        print('dispersion compensasion success\n')
        self.ui.Disp_DIR.setText(filePath)
        
    def getBackground(self):
        background = np.float32(np.mean(self.Bline,1))
        
        filePath = self.ui.DIR.toPlainText()
        current_time = datetime.datetime.now()
        filePath = filePath + "/" + 'background_'+\
            str(current_time.year)+'-'+\
            str(current_time.month)+'-'+\
            str(current_time.day)+'-'+\
            str(current_time.hour)+'-'+\
            str(current_time.minute)+\
            '.bin'
        fp = open(filePath, 'wb')
        background.tofile(fp)
        fp.close()
        print('background measruement success\n')
        self.ui.BG_DIR.setText(filePath)