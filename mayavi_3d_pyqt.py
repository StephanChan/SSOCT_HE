# -*- coding: utf-8 -*-
"""
Created on Mon Mar 18 00:00:16 2024

@author: 帅斌
"""

# First, and before importing any Enthought packages, set the ETS_TOOLKIT
# environment variable to qt4, to tell Traits that we will use Qt.
import os
os.environ['ETS_TOOLKIT'] = 'qt4'
# os.environ['QT_API'] = 'pyqt'
# By default, the PySide binding will be used. If you want the PyQt bindings
# to be used, you need to set the QT_API environment variable to 'pyqt'
#os.environ['QT_API'] = 'pyqt'

# To be able to use PySide or PyQt4 and not run in conflicts with traits,
# we need to import QtGui and QtCore from pyface.qt
from PyQt5 import QtWidgets
# Alternatively, you can bypass this line, but you need to make sure that
# the following lines are executed before the import of PyQT:
#   import sip
#   sip.setapi('QString', 2)
import numpy as np
from traits.api import HasTraits, Instance, on_trait_change
from traitsui.api import View, Item
from mayavi.core.ui.api import MayaviScene, MlabSceneModel, \
        SceneEditor
from mayavi import mlab 
################################################################################

# class Visualization(HasTraits):
#     scene = Instance(MlabSceneModel, ())
#     low = Range(1, 100,  30)
#     high = Range(1, 100, 80)
#     def __init__(self, data):
#         HasTraits.__init__(self)
#         self.data = data
#         # self.low = low
#         # self.high = high
        
#         # self.plot = mlab.pipeline.volume(mlab.pipeline.scalar_field(self.data), vmax = self.high, vmin = self.low)
#     # 
#         # self.update_plot(data)
#     @on_trait_change('low, high')
#     def contrast(self):
#         print(self.high)
#         self.plot.mlab_source.trait_set(data = self.data, vmax = self.high, vmin = self.low)
#         self.plot = mlab.pipeline.volume(mlab.pipeline.scalar_field(self.data))
#     @on_trait_change('scene.activated')
#     def update_plot(self):
#     ## PLot to Show        
        
#         # 使用Mayavi的mlab模块绘制三维散点图
#         # print(self.data)
#         self.plot = mlab.pipeline.volume(mlab.pipeline.scalar_field(self.data), vmax = self.high*2.55, vmin = self.low*2.55)

        
#     # the layout of the dialog screated
#     view = View(Item('scene', editor=SceneEditor(scene_class=MayaviScene),
#                       height=250, width=300, show_label=False),
#                 HGroup(
#                         '_', 'low', 'high',
#                     ),
#                 resizable=True # We need this to resize with the parent widget
#                 )

class Visualization(HasTraits):
    scene = Instance(MlabSceneModel, ())
    def __init__(self, data, low, high):
        HasTraits.__init__(self)
        self.data = data
        self.low = low
        self.high = high
        
    # @on_trait_change('low, high')
    def update_contrast(self, low, high):
        # self.plot.mlab_source.scalars = data
        self.plot.current_range=(low,high)
        # print(self.plot.current_range)
        # self.plot.mlab_source.scalars = data
        # self.plot.clf()
        
    def update_data(self, data, low, high):
        self.plot.mlab_source.scalars = data
        # self.plot.mlab_source.vmin = low
        # self.plot.clf()
        
        
        # self.plot = mlab.pipeline.volume(mlab.pipeline.scalar_field(self.data, vmax = high, vmin = low))
    @on_trait_change('scene.activated')
    def update_plot(self):
        self.plot = mlab.pipeline.volume(mlab.pipeline.scalar_field(self.data), vmax = 20, vmin = 200)
        # print(self.plot)
        self.scene.background=(0,0,0)
        # self.plot.lut_manager.lut_mode = 'grey'
        a=self.plot.lut_manager
        # print(self.plot.mlab_source.all_trait_names())
        # print(self.plot.all_trait_names())
        # print(self.plot.current_range)
        self.plot.current_range=(10,5535)

    # the layout of the dialog screated
    view = View(Item('scene', editor=SceneEditor(scene_class=MayaviScene),
                      height=250, width=300, show_label=False),
                resizable=True # We need this to resize with the parent widget
                )
################################################################################
# The QWidget containing the visualization, this is pure PyQt4 code.
class MayaviQWidget(QtWidgets.QWidget):
    def __init__(self, parent=None, data = None, low = 30, high = 250):
        QtWidgets.QWidget.__init__(self, parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)
        self.visualization = Visualization(data, low, high)

        # If you want to debug, beware that you need to remove the Qt
        # input hook.
        #QtCore.pyqtRemoveInputHook()
        #import pdb ; pdb.set_trace()
        #QtCore.pyqtRestoreInputHook()

        # The edit_traits call will generate the widget to embed.
        self.ui = self.visualization.edit_traits(parent=self,
                                                 kind='subpanel').control
        layout.addWidget(self.ui)
        self.ui.setParent(self)


    

if __name__ == "__main__":
    # Don't create a new QApplication, it would unhook the Events
    # set by Traits on the existing QApplication. Simply use the
    # '.instance()' method to retrieve the existing one.
    app = QtWidgets.QApplication.instance()
    container = QtWidgets.QWidget()
    container.setWindowTitle("Embedding Mayavi in a PyQt4 Application")
    # define a "complex" layout to test the behaviour
    # global layout
    layout = QtWidgets.QGridLayout(container)

    # put some stuff around mayavi

    button = QtWidgets.QPushButton(container)
    # label.setText("Your QWidget at (%d, %d)" % (i,j))
    # label.setAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter)
    layout.addWidget(button, 1,1)
    
    button2 = QtWidgets.QPushButton(container)
    # label.setText("Your QWidget at (%d, %d)" % (i,j))
    # label.setAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter)
    layout.addWidget(button2, 2, 2)
    nx, ny, nz = (500,100,150)

    x = np.arange(nx)
    y = np.arange(ny)
    z = np.arange(nz)
    X, Y, Z = np.meshgrid(x, y, z)
    data1 = np.uint16( np.random.random(X.shape)*105)
    data1[:,:,10] = 200
    data1[:,:,30] = 145
    data1[:,:,80] = 20
    data1[:,:,120] = 10
    
    global mayavi_widget
    mayavi_widget = MayaviQWidget(container, data1, low = 70, high = 258)
    layout.replaceWidget(button2, mayavi_widget)
    global ii
    ii = 1
    def func():
        global data1
        # global mayavi_widget
        # data1[:,:,120] = 200
        # data1=np.array(data1)-10
        # mayavi_widget.visualization.update_data(data1, 10, 200)
        mayavi_widget.visualization.update_contrast(500, 20000)
        # layout.removeWidget(mayavi_widget)
        # mayavi_widget = MayaviQWidget(container, data1, low = ii*10, high = 200)
        # layout.addWidget(mayavi_widget,2,2)
    button.clicked.connect(func)
    # layout.addWidget(mayavi_widget, 1, 1)
    container.show()
    window = QtWidgets.QMainWindow()
    window.setCentralWidget(container)
    window.show()
    

    # Start the main event loop.
    app.exec_()
    
