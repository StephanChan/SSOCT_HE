
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
SCALE =10000
import matplotlib.pyplot as plt
import datetime

# global SIM
# SIM = False
# use_maya = False

class DnSThread(QThread):
    def __init__(self):
        super().__init__()
        self.surf = []
        self.sliceNum = 0
        self.tileNum = 1
        self.AlineNum = 1
        self.BlineNum = 1
        self.CscanNum = 1
        self.totalTiles = 0
        self.display_actions = 0
        
    def run(self):
        self.sliceNum = self.ui.SliceN.value()-1
        self.QueueOut()
        
    def QueueOut(self):
        num = 0
        self.item = self.queue.get()
        self.DnSflag = 'busy'
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
                elif self.item.action == 'display_counts':
                    self.print_display_counts()
                elif self.item.action == 'restart_tilenum':
                    self.restart_tilenum()
                elif self.item.action == 'change_slice_number':
                    self.sliceNum = self.ui.SliceN.value()-1
                    self.ui.CuSlice.setValue(self.sliceNum)
                elif self.item.action == 'agarTile':
                    self.SurfFilename()
                elif self.item.action == 'WriteAgar':
                    self.WriteAgar(self.item.data, self.item.args)
                elif self.item.action == 'Init_SurfScan':
                    self.Init_SurfScan(self.item.data, self.item.args)
                    
                else:
                    message = 'Display and save thread is doing something invalid' + self.item.action
                    self.ui.statusbar.showMessage(message)
                    # self.ui.PrintOut.append(message)
                    self.log.write(message)
            except Exception as error:
                message = "\nAn error occurred:"+" skip the display and save action\n"
                print(message)
                self.ui.statusbar.showMessage(message)
                # self.ui.PrintOut.append(message)
                self.log.write(message)
                print(traceback.format_exc())
            num+=1
            # print(num, 'th display\n')
            self.item = self.queue.get()
        self.ui.statusbar.showMessage("Display and save Thread successfully exited...")
            
    def print_display_counts(self):
        message = str(self.display_actions)+ ' Blines displayed\n'
        print(message)
        # self.ui.PrintOut.append(message)
        self.log.write(message)
        self.display_actions = 0
        
    def Display_aline(self, data, raw = False):
        # get number of Z pixels
        if not raw:
            Zpixels = self.ui.DepthRange.value()
        else:
            if self.Digitizer == 'ATS9351':
                Zpixels = self.ui.PreSamples.value()+self.ui.PostSamples.value()
                # data = np.float32(data/pow(2,16))
            elif self.Digitizer == 'ART8912':
                Zpixels = self.ui.PostSamples_2.value()#-self.ui.DelaySamples.value()-self.ui.TrimSamples.value()
                # data = data[:,self.ui.DelaySamples.value():self.ui.PostSamples_2.value()-self.ui.TrimSamples.value()]
                # data = np.float32(data/pow(2,12))
        # get number of X pixels
        Xpixels = self.ui.Xsteps.value()*self.ui.AlineAVG.value()
        if self.Digitizer == 'ART8912':
            Xpixels = Xpixels + self.ui.PreClock.value()*2 + self.ui.PostClock.value()
        # get number of Y pixels
        Yrpt = self.ui.BlineAVG.value()
        # reshape data to [Ypixels*Xpixels, Zpixels]
        data = data.reshape([Yrpt*Xpixels,Zpixels])
        if raw and self.Digitizer == 'ART8912':
            Zpixels = self.ui.PostSamples_2.value()-self.ui.DelaySamples.value()-self.ui.TrimSamples.value()
            data = data[:,self.ui.DelaySamples.value():self.ui.PostSamples_2.value()-self.ui.TrimSamples.value()]

        self.Aline = data
        data = np.float32(np.mean(data,0))
        # float32 data type
        pixmap = LinePlot(data, [], self.ui.XYmin.value(), self.ui.XYmax.value())
        # clear content on the waveformLabel
        self.ui.XZplane.clear()
        # update iamge on the waveformLabel
        self.ui.XZplane.setPixmap(pixmap)
        
        if self.ui.Save.isChecked() and not self.ui.Gotozero.isChecked():
            if raw:
                data = np.uint16(self.Aline)
            else:
                data = np.uint16(self.Aline/SCALE*65535)
            self.WriteData(data, self.AlineFilename([Yrpt,Xpixels,Zpixels]))
            
    
    def Display_bline(self, data, raw = False):
        # get number of Z pixels
        if not raw:
            Zpixels = self.ui.DepthRange.value()
        else:
            if self.Digitizer == 'ATS9351':
                Zpixels = self.ui.PreSamples.value()+self.ui.PostSamples.value()
                # data = np.float32(data/pow(2,16))
            elif self.Digitizer == 'ART8912':
                Zpixels = self.ui.PostSamples_2.value()
                # data = np.float32(data/pow(2,12))
        # get number of X pixels
        Xpixels = self.ui.Xsteps.value()*self.ui.AlineAVG.value()
        if self.Digitizer == 'ART8912':
            Xpixels = Xpixels + self.ui.PreClock.value()*2 + self.ui.PostClock.value()
        # get number of Y pixels
        Yrpt = self.ui.BlineAVG.value()
        # reshape data
        data = data.reshape([Yrpt,Xpixels,Zpixels])

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
        # get number of Z pixels
        if not raw:
            Zpixels = self.ui.DepthRange.value()
        else:
            if self.Digitizer == 'ATS9351':
                Zpixels = self.ui.PreSamples.value()+self.ui.PostSamples.value()
                # data = np.float32(data/pow(2,16))
            elif self.Digitizer == 'ART8912':
                Zpixels = self.ui.PostSamples_2.value()
                # data = np.float32(data/pow(2,12))
        # get number of X pixels
        Xpixels = self.ui.Xsteps.value()*self.ui.AlineAVG.value()
        if self.Digitizer == 'ART8912':
            Xpixels = Xpixels + self.ui.PreClock.value()*2 + self.ui.PostClock.value()
        # get number of Y pixels
        Ypixels = self.ui.Ysteps.value()*self.ui.BlineAVG.value()
        # reshape data
        data = data.reshape([Ypixels,Xpixels,Zpixels])

        self.Cscan = data
        plane = np.transpose(data[0,:,:]).copy()# has to be first index, otherwise the memory space is not continuous
        # print(plane.shape)
        pixmap = ImagePlot(plane, self.ui.XYmin.value(), self.ui.XYmax.value())
        # clear content on the waveformLabel
        self.ui.XZplane.clear()
        # update image on the waveformLabel
        self.ui.XZplane.setPixmap(pixmap)
        
        plane = np.mean(data,2)# has to be first index, otherwise the memory space is not continuous
        # print(plane.shape)
        self.ui.tileMean.setValue(np.mean(plane))
        if np.mean(plane)>self.ui.AgarValue.value():
            self.ui.TissueRadio.setChecked(True)
        else:
            self.ui.TissueRadio.setChecked(False)
        pixmap = ImagePlot(plane, self.ui.XYmin.value(), self.ui.XYmax.value()/3)
        # clear content on the waveformLabel
        self.ui.XYplane.clear()
        # update image on the waveformLabel
        self.ui.XYplane.setPixmap(pixmap)
        ###################### plot 3D visulaization
        if self.use_maya:
            self.ui.mayavi_widget.visualization.update_data(self.Cscan/500)
        if self.ui.Save.isChecked():
            if raw:
                data = np.uint16(self.Cscan)
            else:
                data = np.uint16(self.Cscan/SCALE*65535)
            self.WriteData(data, self.CscanFilename([Ypixels,Xpixels,Zpixels]))
        
    def Init_SurfScan(self, raw = False, args = []):
        
        Xpixels = self.ui.Xsteps.value()*self.ui.AlineAVG.value()
        # if self.Digitizer == 'ART8912':
        #     Xpixels = Xpixels + self.ui.PreClock.value()*2 + self.ui.PostClock.value()
        Ypixels = self.ui.Ysteps.value()*self.ui.BlineAVG.value()
        
        #######################################
        # for even strips, need to flip data in Y dimension because scanning was in backward direction
        surfX = args[1][0]
        surfY = np.int32(args[1][1]/args[1][0])
        scale = self.ui.scale.value()
        self.surf = np.zeros([ surfX*(Ypixels//scale),surfY*(Xpixels//scale)],dtype = np.float32)
        pixmap = ImagePlot(self.surf, self.ui.Surfmin.value(), self.ui.Surfmax.value())
        # clear content on the waveformLabel
        self.ui.SampleMosaic.clear()
        # update iamge on the waveformLabel
        self.ui.SampleMosaic.setPixmap(pixmap)
        
        
        #######################################

        # self.surfMUS = np.zeros([ surfX*(Ypixels//scale),surfY*(Xpixels//scale)],dtype = np.float32)
        # pixmap = ImagePlot(self.surfMUS, self.ui.XYZmin.value(), self.ui.XYZmax.value())
        # # clear content on the waveformLabel
        # self.ui.MUS_mosaic.clear()
        # # update iamge on the waveformLabel
        # self.ui.MUS_mosaic.setPixmap(pixmap)
            
    def Display_SurfScan(self, data, raw = False, args = []):
        # get number of Z pixels
        if not raw:
            Zpixels = self.ui.DepthRange.value()
        else:
            if self.Digitizer == 'ATS9351':
                Zpixels = self.ui.PreSamples.value()+self.ui.PostSamples.value()
                # data = np.float32(data/pow(2,16))
            elif self.Digitizer == 'ART8912':
                Zpixels = self.ui.PostSamples_2.value()
                # data = np.float32(data/pow(2,12))
        # get number of X pixels
        Xpixels = self.ui.Xsteps.value()*self.ui.AlineAVG.value()
        if self.Digitizer == 'ART8912':
            Xpixels = Xpixels + self.ui.PreClock.value()*2 + self.ui.PostClock.value()
        # get number of Y pixels
        Ypixels = self.ui.Ysteps.value()*self.ui.BlineAVG.value()
        # print('get shape')
        data = data.reshape([Ypixels,Xpixels,Zpixels])
        # trim fly-back pixels
        data = data[:,self.ui.PreClock.value():self.ui.Xsteps.value()*self.ui.AlineAVG.value()+self.ui.PreClock.value()]
        Xpixels = self.ui.Xsteps.value()*self.ui.AlineAVG.value()
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
        # print('display Bline')
        plane = np.mean(data,2)
        self.ui.tileMean.setValue(np.mean(plane))
        if np.sum(plane > self.ui.AgarValue.value())>100:
            self.ui.TissueRadio.setChecked(True)
        else:
            self.ui.TissueRadio.setChecked(False)
        # print('identify agar')
        pixmap = ImagePlot(plane, self.ui.XYmin.value(), self.ui.XYmax.value()/3)
        # clear content on the waveformLabel
        self.ui.XYplane.clear()
        # update iamge on the waveformLabel
        self.ui.XYplane.setPixmap(pixmap)
        # print('display XY')
        scale = self.ui.scale.value()

        ###################### plot 3D visulaization
        if self.use_maya:
            self.ui.mayavi_widget.visualization.update_data(self.Cscan/500)
        # print('display 3D')
        # self.totalTiles = args[1][1]
        # print('before surf image update')
        plane_ds=plane[::scale,::scale]
        self.surf[Ypixels//scale*fileX:Ypixels//scale*(fileX+1),Xpixels//scale*fileY:Xpixels//scale*(fileY+1)] = plane_ds[0:Ypixels//scale,0:Xpixels//scale]
        # print('append tile')
        pixmap = ImagePlot(self.surf, self.ui.Surfmin.value(), self.ui.Surfmax.value())
        # print('gen pixmap')
        # clear content on the waveformLabel
        self.ui.SampleMosaic.clear()
        # print('clear window')
        # update iamge on the waveformLabel
        self.ui.SampleMosaic.setPixmap(pixmap)
        # print('update window')
        if self.ui.Save.isChecked():
            if raw:
                data = np.uint16(self.Cscan)
            else:
                data = np.uint16(self.Cscan/SCALE*65535)
            self.WriteData(data, self.SurfFilename([Ypixels,Xpixels,Zpixels]))

            
    def Update_contrast_XY(self):
        if self.ui.ACQMode.currentText() in ['SingleAline', 'RptAline']:
            data = np.float32(np.mean(self.Aline,0))
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
            pixmap = ImagePlot(plane, self.ui.XYmin.value(), self.ui.XYmax.value()/3)
            # clear content on the waveformLabel
            self.ui.XYplane.clear()
            # update image on the waveformLabel
            self.ui.XYplane.setPixmap(pixmap)
            
    def Update_contrast_Surf(self):
        # print(self.surf.shape)
        pixmap = ImagePlot(self.surf, self.ui.Surfmin.value(), self.ui.Surfmax.value())
        # clear content on the waveformLabel
        self.ui.SampleMosaic.clear()
        # update iamge on the waveformLabel
        self.ui.SampleMosaic.setPixmap(pixmap)
            
    def Update_contrast_XYZ(self):
        if self.use_maya:
            self.ui.mayavi_widget.visualization.update_contrast(self.ui.XYZmin.value(), self.ui.XYZmax.value())
    
    def restart_tilenum(self):
        self.tileNum = 1
        self.sliceNum = self.sliceNum+1
        self.ui.CuSlice.setValue(self.sliceNum)
        
    def SurfFilename(self, shape = [0,0,0]):
        filename = 'slice-'+str(self.sliceNum)+'-tile-'+str(self.tileNum)+'-Y'+str(shape[0])+'-X'+str(shape[1])+'-Z'+str(shape[2])+'.bin'
        self.tileNum = self.tileNum + 1
    
        print(filename)
        # self.ui.PrintOut.append(filename)
        self.log.write(filename)
        return filename
    
    def CscanFilename(self, shape):
        filename = 'Cscan-'+str(self.CscanNum)+'-Y'+str(shape[0])+'-X'+str(shape[1])+'-Z'+str(shape[2])+'.bin'
        self.CscanNum = self.CscanNum + 1
        return filename
    
    def BlineFilename(self, shape):
        filename = 'Bline-'+str(self.BlineNum)+'-Yrpt'+str(shape[0])+'-X'+str(shape[1])+'-Z'+str(shape[2])+'.bin'
        self.BlineNum = self.BlineNum + 1
        return filename
    
    def AlineFilename(self, shape):
        filename = 'Aline-'+str(self.AlineNum)+'-Yrpt'+str(shape[0])+'-Xrpt'+str(shape[1])+'-Z'+str(shape[2])+'.bin'
        self.AlineNum = self.AlineNum + 1
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
        message = 'time for saving: '+str(round(time.time()-start,3))
        print(message)
        # self.ui.PrintOut.append(message)
        self.log.write(message)
        
    def WriteAgar(self, data, args):
        [Ystep, Xstep] = args
        filename = 'slice-'+str(self.sliceNum)+'-agarTiles X-'+str(Xstep)+'-by Y-'+str(Ystep)+'-.bin'
        filePath = self.ui.DIR.toPlainText()
        filePath = filePath + "/" + filename
        # print(filePath)
        fp = open(filePath, 'wb')
        data.tofile(fp)
        fp.close()
        
