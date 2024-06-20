
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 18:26:44 2023

@author: admin
"""

from PyQt5.QtCore import  QThread
from Generaic_functions import LinePlot, ImagePlot, findchangept
import numpy as np
import traceback
global SCALE
SCALE =10000
import matplotlib.pyplot as plt
import datetime
import os
from scipy import ndimage
from libtiff import TIFF
# global SIM
# SIM = False
# use_maya = False
import time

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
            start=time.time()
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
                    self.Process_SurfScan(self.item.data, self.item.raw, self.item.args)
                elif self.item.action == 'display_mosaic':
                    self.Display_mosaic()
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
                elif self.item.action == 'Save_mosaic':
                    self.Save_mosaic()
                    
                else:
                    message = 'Display and save thread is doing something invalid' + self.item.action
                    self.ui.statusbar.showMessage(message)
                    # self.ui.PrintOut.append(message)
                    self.log.write(message)
                if time.time()-start>4:
                    print('time for DnS:',time.time()-start)
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
        
    def get_FOV_size(self, raw):
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
        return Zpixels, Xpixels
            
    def Display_aline(self, data, raw = False):
        Zpixels, Xpixels = self.get_FOV_size(raw)
        # get number of Y pixels
        Yrpt = self.ui.BlineAVG.value()
        # reshape data to [Ypixels*Xpixels, Zpixels]
        data = data.reshape([Yrpt*Xpixels,Zpixels])
        if raw and self.Digitizer == 'ART8912':
            Zpixels = self.ui.PostSamples_2.value()-self.ui.DelaySamples.value()-self.ui.TrimSamples.value()
            data = data[:,self.ui.DelaySamples.value():self.ui.PostSamples_2.value()-self.ui.TrimSamples.value()]

        self.Aline = data
        Ascan = np.float32(np.mean(data,0))
        # float32 data type
        pixmap = LinePlot(Ascan, [], self.ui.XYmin.value()*20, self.ui.XYmax.value()*30)
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
        Zpixels, Xpixels = self.get_FOV_size(raw)
        # get number of Y pixels
        Yrpt = self.ui.BlineAVG.value()
        # reshape data
        data = data.reshape([Yrpt,Xpixels,Zpixels])
        # trim fly-back pixels
        if self.Digitizer == 'ART8912':    
            data = data[:,self.ui.PreClock.value():self.ui.Xsteps.value()*self.ui.AlineAVG.value()+self.ui.PreClock.value(),:]
            Xpixels = self.ui.Xsteps.value()*self.ui.AlineAVG.value()
            
        self.Bline = data
        Bscan = np.float32(np.mean(data,0))
        Bscan = np.transpose(Bscan).copy()

        pixmap = ImagePlot(Bscan, self.ui.XYmin.value(), self.ui.XYmax.value())
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
        Zpixels, Xpixels = self.get_FOV_size(raw)
        # get number of Y pixels
        Ypixels = self.ui.Ysteps.value()*self.ui.BlineAVG.value()
        # reshape data
        data = data.reshape([Ypixels,Xpixels,Zpixels])
        # trim fly-back pixels
        if self.Digitizer == 'ART8912':    
            data = data[:,self.ui.PreClock.value():self.ui.Xsteps.value()*self.ui.AlineAVG.value()+self.ui.PreClock.value(),:]
            Xpixels = self.ui.Xsteps.value()*self.ui.AlineAVG.value()
            
        self.Cscan = data
        plane = np.transpose(data[0,:,:]).copy()# has to be first index, otherwise the memory space is not continuous
        # print(plane.shape)
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
        ###################### plot 3D visulaization
        # if self.use_maya:
        #     self.ui.mayavi_widget.visualization.update_data(self.Cscan/500)
        if self.ui.Save.isChecked():
            if raw:
                data = np.uint16(self.Cscan)
            else:
                data = np.uint16(self.Cscan/SCALE*65535)
            self.WriteData(data, self.CscanFilename([Ypixels,Xpixels,Zpixels]))
        
    def Init_SurfScan(self, raw = False, args = []):
        Xpixels = self.ui.Xsteps.value()*self.ui.AlineAVG.value()
        Ypixels = self.ui.Ysteps.value()*self.ui.BlineAVG.value()
        
        surfX = args[1][0]
        surfY = np.int32(args[1][1]/args[1][0])
        scale = self.ui.scale.value()
        self.surf = np.zeros([ surfX*(Ypixels//scale),surfY*(Xpixels//scale)],dtype = np.float32)

        pixmap = ImagePlot(self.surf, self.ui.Surfmin.value(), self.ui.Surfmax.value())
        # clear content on the waveformLabel
        self.ui.SampleMosaic.clear()
        # update iamge on the waveformLabel
        self.ui.SampleMosaic.setPixmap(pixmap)
        
        # load surface profile for high res imaging
        if os.path.isfile(self.ui.Surf_DIR.text()):
            self.surfCurve = np.uint16(np.fromfile(self.ui.Surf_DIR.text(), dtype=np.uint16))
        else:
            print('surface data not found, using all zeros')
            self.surfCurve = np.zeros([Xpixels],dtype = np.uint16)
        # plt.figure()
        # plt.plot(self.surfCurve)
        # plt.figure()
        print('surfCurve shape:',self.surfCurve.shape)
        # load darf field for shading correction
        if not self.ui.DSing.isChecked():
            if os.path.isfile(self.ui.DarkField_DIR.text()):
                self.darkField = np.float32(np.fromfile(self.ui.DarkField_DIR.text(), dtype=np.float32))
                self.darkField = self.darkField.reshape([Xpixels, Ypixels])
                self.darkField = self.darkField.transpose()
            else:
                print('dark field data not found, using all zeros')
                self.darkField = np.zeros([Ypixels, Xpixels],dtype = np.float32)
            # load flat field for shading correction
            if os.path.isfile(self.ui.FlatField_DIR.text()):
                self.flatField = np.float32(np.fromfile(self.ui.FlatField_DIR.text(), dtype=np.float32))
                self.flatField = self.flatField.reshape([Xpixels, Ypixels])
                self.flatField = self.flatField.transpose()
            else:
                print('flat data not found, using all ones')
                self.flatField = np.ones([Ypixels, Xpixels],dtype = np.float32)
            
            # plt.figure()
            # plt.imshow(self.flatField)
            # plt.figure()
            self.first_tile = True
            #######################################
        
            self.zmax_scale = 3
            ############## adjust scale
            while Xpixels%self.zmax_scale or Ypixels%self.zmax_scale:
                self.zmax_scale -= 1
            message = '\nslice '+str(self.sliceNum)+' zmax scale is '+str(self.zmax_scale)+'\n'
            print(message)
            self.log.write(message)
            self.surfZMAX = np.zeros([ surfX*(Ypixels//self.zmax_scale),surfY*(Xpixels//self.zmax_scale)],dtype = np.float32)
            pixmap = ImagePlot(self.surfZMAX, self.ui.XYZmin.value(), self.ui.XYZmax.value())
            # clear content on the waveformLabel
            self.ui.MUS_mosaic.clear()
            # update iamge on the waveformLabel
            self.ui.MUS_mosaic.setPixmap(pixmap)

            
    def Process_SurfScan(self, data, raw = False, args = []):
        Zpixels, Xpixels = self.get_FOV_size(raw)
        # get number of Y pixels
        Ypixels = self.ui.Ysteps.value()*self.ui.BlineAVG.value()
        # reshape into Ypixels x Xpixels x Zpixels
        data = data.reshape([Ypixels,Xpixels,Zpixels])
        # trim fly-back pixels
        if self.Digitizer == 'ART8912':    
            data = data[:,self.ui.PreClock.value():self.ui.Xsteps.value()*self.ui.AlineAVG.value()+self.ui.PreClock.value(),:]
            Xpixels = self.ui.Xsteps.value()*self.ui.AlineAVG.value()
        
        ########################################
        # for odd strips, need to flip data in Y dimension and also the sequence
        surfX = args[1][0]
        surfY = np.int32(args[1][1]/args[1][0])
        fileY = args[0][1]-1
        if np.mod(fileY,2) == 0:
            fileX = args[0][0]
        else:
            fileX = surfX - args[0][0]-1
            
        ########################################################
        if not raw:
            # start0=time.time()
            #######################################
            # CPU do surface flatterning, this takes about 1 sec
            data_flatten = np.zeros(data.shape, dtype = np.float32)
            for xx in range(Xpixels):
                    data_flatten[:,xx,0:data.shape[2]-self.surfCurve[xx]] = data[:,xx,self.surfCurve[xx]:]
            # print('flatten surface take', time.time()-start0)
            tmp = self.ui.SaveZstart.value()
            start_pixel =  tmp if tmp>-0.5 else self.ui.SurfSet.value()+7 ################# focus set to start from 7 pixels below surface
            thickness = self.ui.SaveZrange.value()
            
            if not self.ui.DSing.isChecked():
                # calculate data_focus and data_ds
                data_focus = data_flatten[:,:,start_pixel:start_pixel + thickness]
                data_ds = data_flatten.reshape([Ypixels//self.zmax_scale, self.zmax_scale, Xpixels//self.zmax_scale, self.zmax_scale, Zpixels]).mean(-2).mean(1) #################### zmax set to use 3x3 downsampling
                data_ds2 = data_flatten.reshape([Ypixels//10, 10, Xpixels//10, 10, Zpixels]).mean(-2).mean(1) #################### surfProfile set to use 10x10 downsampling
                ########################################
                # calculate AIP, surface, and zmax
                AIP = np.mean(data_focus,2)
                # shading correction
                AIP = (AIP-self.darkField)/self.flatField
                
                # start0 = time.time()
                surfProfile = np.zeros([data_ds2.shape[0], data_ds2.shape[1]])
                for yy in range(data_ds2.shape[0]):
                    for xx in range(data_ds2.shape[1]):
                        surfProfile[yy,xx] = findchangept(data_ds2[yy,xx,:],2)
                # print('calculate surface', time.time()-start0)
                
                kernel = np.ones([1,1,5])/5 # kernel size hard coded to be 5 in z dimension
                zmax = np.argmax(ndimage.convolve(data_ds,kernel,mode = 'reflect'),2)
                # for odd strips, need to flip data in Y dimension and also the sequence
                if np.mod(fileY,2)==1:
                    AIP = np.flip(AIP,0)
                    surfProfile = np.flip(surfProfile,0)
                    zmax = np.flip(zmax,0)
                    data_ds = np.flip(data_ds,0)
                    data_focus = np.flip(data_focus,0)
                self.Cscan = data_ds
                ######################################### save processed result
                # check if this is the first tile
                if self.first_tile:
                    mode = 'w'
                    self.first_tile = False
                else:
                    mode = 'a'
                    
                if self.ui.Save.isChecked():
                    self.writeTiff(self.ui.DIR.toPlainText()+'/aip/vol'+str(self.sliceNum)+'/AIP.tif', AIP, mode)
                if self.ui.Save.isChecked():
                    self.writeTiff(self.ui.DIR.toPlainText()+'/surf/vol'+str(self.sliceNum)+'/SURF.tif', surfProfile, mode)
                if self.ui.Save.isChecked():
                    self.writeTiff(self.ui.DIR.toPlainText()+'/fitting/vol'+str(self.sliceNum)+'/MAX.tif', zmax, mode)
                    
                self.surfZMAX[Ypixels//self.zmax_scale*fileX:Ypixels//self.zmax_scale*(fileX+1),\
                          Xpixels//self.zmax_scale*(surfY-fileY-1):Xpixels//self.zmax_scale*(surfY-fileY)] = zmax
            ##########################################################################
            else:
                # for fast pre-scan imaging
                data_ds = data_flatten
                if np.mod(fileY,2)==1:
                    data_ds = np.flip(data_ds,0)
                self.Cscan = data_ds
                AIP = np.mean(data_ds[:,:,start_pixel:start_pixel + thickness],2)
                
                
            ############################### ###############
            # display Bline
            plane = np.transpose(data_ds[0,:,:]).copy()
            pixmap = ImagePlot(plane, self.ui.XYmin.value(), self.ui.XYmax.value())
            # clear content on the waveformLabel
            self.ui.XZplane.clear()
            # update image on the waveformLabel
            self.ui.XZplane.setPixmap(pixmap)
            ############################## #######
            # display AIP
            scale = self.ui.scale.value()
            pixmap = ImagePlot(AIP[:,::scale], self.ui.XYmin.value(), self.ui.XYmax.value())
            # clear content on the waveformLabel
            self.ui.XYplane.clear()
            # update iamge on the waveformLabel
            self.ui.XYplane.setPixmap(pixmap)
            
            ###################### ############
            # # plot 3D visulaization
            # if self.use_maya:
            #     self.ui.mayavi_widget.visualization.update_data(data_ds/500)
            ###########################################
            # squeeze AIP into surface image
            scale = self.ui.scale.value()
            self.surf[Ypixels//scale*fileX:Ypixels//scale*(fileX+1),\
                      Xpixels//scale*(surfY-fileY-1):Xpixels//scale*(surfY-fileY)] = AIP[::scale,::scale]
                
            
            
        else:
            #######################################
            # for raw data, no display is available
            thickness = Zpixels
            self.Cscan = data
            if np.mod(fileY,2)==1:
                self.Cscan = np.flip(self.Cscan,0)
            
        ##########################################
        # save data to disk
        if self.ui.Save.isChecked():
            if raw:
                data = np.uint16(data)
            else:
                data = np.uint16(data_focus/SCALE*65535)
            self.WriteData(data, self.SurfFilename([Ypixels,Xpixels,thickness]))

    def writeTiff(self,filename, image, overlap):
        tif = TIFF.open(filename, mode=overlap)
        tif.write_image(image)
        tif.close()
        
    def Display_mosaic(self):
        pixmap = ImagePlot(self.surf, self.ui.Surfmin.value(), self.ui.Surfmax.value())
        self.ui.SampleMosaic.clear()
        self.ui.SampleMosaic.setPixmap(pixmap)
        
        if not self.ui.DSing.isChecked():
            pixmap = ImagePlot(self.surfZMAX, self.ui.XYZmin.value(), self.ui.XYZmax.value())
            # clear content on the waveformLabel
            self.ui.MUS_mosaic.clear()
            # update iamge on the waveformLabel
            self.ui.MUS_mosaic.setPixmap(pixmap)

        
    def Save_mosaic(self):
        if self.ui.Save.isChecked():
            tif = TIFF.open(self.ui.DIR.toPlainText()+'/aip/slice'+str(self.sliceNum)+'coase.tif', mode='w')
            tif.write_image(self.surf)
            tif.close()
            if not self.ui.DSing.isChecked():
                tif = TIFF.open(self.ui.DIR.toPlainText()+'/fitting/slice'+str(self.sliceNum)+'coase.tif', mode='w')
                tif.write_image(self.surfZMAX)
                tif.close()
            
        
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
            
            tmp = self.ui.SaveZstart.value()
            start_pixel =  tmp if tmp>-0.5 else self.ui.SurfSet.value()+7
            thickness = self.ui.SaveZrange.value()
            plane = np.mean(data[:,:,start_pixel:start_pixel + thickness],2)# has to be first index, otherwise the memory space is not continuous
            pixmap = ImagePlot(plane, self.ui.XYmin.value(), self.ui.XYmax.value())
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
        # if self.use_maya:
        #     self.ui.mayavi_widget.visualization.update_contrast(self.ui.XYZmin.value(), self.ui.XYZmax.value())
        pixmap = ImagePlot(self.surfZMAX, self.ui.XYZmin.value(), self.ui.XYZmax.value())
        # clear content on the waveformLabel
        self.ui.MUS_mosaic.clear()
        # update iamge on the waveformLabel
        self.ui.MUS_mosaic.setPixmap(pixmap)
    
    def restart_tilenum(self):
        self.tileNum = 1
        self.sliceNum = self.sliceNum+1
        self.ui.CuSlice.setValue(self.sliceNum)
        if not os.path.exists(self.ui.DIR.toPlainText()+'/aip/vol'+str(self.sliceNum)):
            os.mkdir(self.ui.DIR.toPlainText()+'/aip/vol'+str(self.sliceNum))
        if not os.path.exists(self.ui.DIR.toPlainText()+'/surf/vol'+str(self.sliceNum)):
            os.mkdir(self.ui.DIR.toPlainText()+'/surf/vol'+str(self.sliceNum))
        if not os.path.exists(self.ui.DIR.toPlainText()+'/fitting/vol'+str(self.sliceNum)):
            os.mkdir(self.ui.DIR.toPlainText()+'/fitting/vol'+str(self.sliceNum))
        
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
        if time.time()-start > 1:
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
        
