# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\SSOCT_HE\software\GUI.ui'
#
# Created by: PyQt5 UI code generator 5.15.7
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1769, 1263)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.Tabs = QtWidgets.QTabWidget(self.centralwidget)
        self.Tabs.setGeometry(QtCore.QRect(0, 910, 1701, 291))
        font = QtGui.QFont()
        font.setPointSize(15)
        self.Tabs.setFont(font)
        self.Tabs.setObjectName("Tabs")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.toolBox = QtWidgets.QToolBox(self.tab)
        self.toolBox.setGeometry(QtCore.QRect(1400, 30, 141, 141))
        self.toolBox.setObjectName("toolBox")
        self.page = QtWidgets.QWidget()
        self.page.setGeometry(QtCore.QRect(0, 0, 141, 73))
        self.page.setObjectName("page")
        self.pushButton = QtWidgets.QPushButton(self.page)
        self.pushButton.setGeometry(QtCore.QRect(24, 30, 91, 41))
        self.pushButton.setObjectName("pushButton")
        self.toolBox.addItem(self.page, "")
        self.page_2 = QtWidgets.QWidget()
        self.page_2.setGeometry(QtCore.QRect(0, 0, 141, 73))
        self.page_2.setObjectName("page_2")
        self.toolBox.addItem(self.page_2, "")
        self.ACQmode = QtWidgets.QComboBox(self.tab)
        self.ACQmode.setGeometry(QtCore.QRect(20, 30, 161, 41))
        self.ACQmode.setObjectName("ACQmode")
        self.ACQmode.addItem("")
        self.ACQmode.addItem("")
        self.ACQmode.addItem("")
        self.ACQmode.addItem("")
        self.ACQmodeLabel = QtWidgets.QLabel(self.tab)
        self.ACQmodeLabel.setGeometry(QtCore.QRect(20, 10, 121, 16))
        self.ACQmodeLabel.setObjectName("ACQmodeLabel")
        self.FFTmode = QtWidgets.QComboBox(self.tab)
        self.FFTmode.setGeometry(QtCore.QRect(190, 30, 191, 41))
        self.FFTmode.setObjectName("FFTmode")
        self.FFTmode.addItem("")
        self.FFTmode.addItem("")
        self.FFTmode.addItem("")
        self.FFTmodeLabel = QtWidgets.QLabel(self.tab)
        self.FFTmodeLabel.setGeometry(QtCore.QRect(190, 10, 121, 16))
        self.FFTmodeLabel.setObjectName("FFTmodeLabel")
        self.ChannelLabel = QtWidgets.QLabel(self.tab)
        self.ChannelLabel.setGeometry(QtCore.QRect(400, 10, 121, 16))
        self.ChannelLabel.setObjectName("ChannelLabel")
        self.Channel = QtWidgets.QComboBox(self.tab)
        self.Channel.setGeometry(QtCore.QRect(400, 30, 81, 41))
        self.Channel.setObjectName("Channel")
        self.Channel.addItem("")
        self.Channel.addItem("")
        self.Channel.addItem("")
        self.Save = QtWidgets.QCheckBox(self.tab)
        self.Save.setGeometry(QtCore.QRect(30, 90, 91, 31))
        self.Save.setIconSize(QtCore.QSize(30, 30))
        self.Save.setObjectName("Save")
        self.textEdit = QtWidgets.QTextEdit(self.tab)
        self.textEdit.setGeometry(QtCore.QRect(20, 160, 104, 71))
        self.textEdit.setObjectName("textEdit")
        self.SaveDIRLabel = QtWidgets.QLabel(self.tab)
        self.SaveDIRLabel.setGeometry(QtCore.QRect(30, 130, 81, 31))
        self.SaveDIRLabel.setObjectName("SaveDIRLabel")
        self.DepthStartLabel = QtWidgets.QLabel(self.tab)
        self.DepthStartLabel.setGeometry(QtCore.QRect(190, 90, 141, 21))
        self.DepthStartLabel.setObjectName("DepthStartLabel")
        self.DepthRangeLabel = QtWidgets.QLabel(self.tab)
        self.DepthRangeLabel.setGeometry(QtCore.QRect(190, 170, 141, 21))
        self.DepthRangeLabel.setObjectName("DepthRangeLabel")
        self.DepthRange = QtWidgets.QSpinBox(self.tab)
        self.DepthRange.setGeometry(QtCore.QRect(190, 190, 101, 41))
        self.DepthRange.setWhatsThis("")
        self.DepthRange.setMinimum(1)
        self.DepthRange.setMaximum(1024)
        self.DepthRange.setObjectName("DepthRange")
        self.DepthStart = QtWidgets.QSpinBox(self.tab)
        self.DepthStart.setGeometry(QtCore.QRect(190, 110, 101, 41))
        self.DepthStart.setMinimum(1)
        self.DepthStart.setMaximum(1024)
        self.DepthStart.setObjectName("DepthStart")
        self.BlineAvgLabel = QtWidgets.QLabel(self.tab)
        self.BlineAvgLabel.setGeometry(QtCore.QRect(510, 10, 141, 21))
        self.BlineAvgLabel.setObjectName("BlineAvgLabel")
        self.BlineAVG = QtWidgets.QSpinBox(self.tab)
        self.BlineAVG.setGeometry(QtCore.QRect(510, 30, 101, 41))
        self.BlineAVG.setWhatsThis("")
        self.BlineAVG.setMinimum(1)
        self.BlineAVG.setObjectName("BlineAVG")
        self.Tabs.addTab(self.tab, "")
        self.GalvoTab = QtWidgets.QWidget()
        self.GalvoTab.setObjectName("GalvoTab")
        self.CenterGalvo = QtWidgets.QPushButton(self.GalvoTab)
        self.CenterGalvo.setGeometry(QtCore.QRect(10, 20, 121, 31))
        self.CenterGalvo.setAutoFillBackground(False)
        self.CenterGalvo.setCheckable(True)
        self.CenterGalvo.setObjectName("CenterGalvo")
        self.Xsteps = QtWidgets.QSpinBox(self.GalvoTab)
        self.Xsteps.setGeometry(QtCore.QRect(200, 20, 101, 41))
        self.Xsteps.setWrapping(False)
        self.Xsteps.setMinimum(1)
        self.Xsteps.setMaximum(100000)
        self.Xsteps.setProperty("value", 1000)
        self.Xsteps.setObjectName("Xsteps")
        self.XstepsLabel = QtWidgets.QLabel(self.GalvoTab)
        self.XstepsLabel.setGeometry(QtCore.QRect(200, 0, 81, 21))
        self.XstepsLabel.setObjectName("XstepsLabel")
        self.AlineAVG = QtWidgets.QSpinBox(self.GalvoTab)
        self.AlineAVG.setGeometry(QtCore.QRect(350, 20, 101, 41))
        self.AlineAVG.setProperty("value", 1)
        self.AlineAVG.setObjectName("AlineAVG")
        self.AlineAvgLabel = QtWidgets.QLabel(self.GalvoTab)
        self.AlineAvgLabel.setGeometry(QtCore.QRect(350, 0, 141, 21))
        self.AlineAvgLabel.setObjectName("AlineAvgLabel")
        self.XrangeLabel = QtWidgets.QLabel(self.GalvoTab)
        self.XrangeLabel.setGeometry(QtCore.QRect(200, 160, 191, 31))
        self.XrangeLabel.setObjectName("XrangeLabel")
        self.XStepSize = QtWidgets.QDoubleSpinBox(self.GalvoTab)
        self.XStepSize.setGeometry(QtCore.QRect(200, 90, 101, 41))
        self.XStepSize.setProperty("value", 2.0)
        self.XStepSize.setObjectName("XStepSize")
        self.Objective = QtWidgets.QComboBox(self.GalvoTab)
        self.Objective.setGeometry(QtCore.QRect(10, 70, 151, 41))
        self.Objective.setObjectName("Objective")
        self.Objective.addItem("")
        self.Objective.addItem("")
        self.XStepsizeLabel = QtWidgets.QLabel(self.GalvoTab)
        self.XStepsizeLabel.setGeometry(QtCore.QRect(200, 70, 141, 21))
        self.XStepsizeLabel.setObjectName("XStepsizeLabel")
        self.Bias = QtWidgets.QDoubleSpinBox(self.GalvoTab)
        self.Bias.setGeometry(QtCore.QRect(20, 150, 101, 41))
        self.Bias.setObjectName("Bias")
        self.BiasLabel = QtWidgets.QLabel(self.GalvoTab)
        self.BiasLabel.setGeometry(QtCore.QRect(20, 130, 81, 21))
        self.BiasLabel.setObjectName("BiasLabel")
        self.waveformLabel = QtWidgets.QLabel(self.GalvoTab)
        self.waveformLabel.setGeometry(QtCore.QRect(800, 0, 881, 241))
        self.waveformLabel.setScaledContents(True)
        self.waveformLabel.setObjectName("waveformLabel")
        self.Tabs.addTab(self.GalvoTab, "")
        self.DigitizerTab = QtWidgets.QWidget()
        self.DigitizerTab.setObjectName("DigitizerTab")
        self.Tabs.addTab(self.DigitizerTab, "")
        self.StageTab = QtWidgets.QWidget()
        self.StageTab.setObjectName("StageTab")
        self.Tabs.addTab(self.StageTab, "")
        self.horizontalLayoutWidget = QtWidgets.QWidget(self.centralwidget)
        self.horizontalLayoutWidget.setGeometry(QtCore.QRect(0, 50, 1701, 852))
        self.horizontalLayoutWidget.setObjectName("horizontalLayoutWidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_3 = QtWidgets.QLabel(self.horizontalLayoutWidget)
        self.label_3.setMinimumSize(QtCore.QSize(850, 850))
        font = QtGui.QFont()
        font.setPointSize(25)
        self.label_3.setFont(font)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout.addWidget(self.label_3)
        self.label_2 = QtWidgets.QLabel(self.horizontalLayoutWidget)
        self.label_2.setMinimumSize(QtCore.QSize(200, 0))
        self.label_2.setMaximumSize(QtCore.QSize(200, 16777215))
        font = QtGui.QFont()
        font.setPointSize(25)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout.addWidget(self.label_2)
        self.label = QtWidgets.QLabel(self.horizontalLayoutWidget)
        font = QtGui.QFont()
        font.setPointSize(25)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.RunButton = QtWidgets.QPushButton(self.centralwidget)
        self.RunButton.setGeometry(QtCore.QRect(30, 0, 111, 41))
        font = QtGui.QFont()
        font.setPointSize(20)
        self.RunButton.setFont(font)
        self.RunButton.setObjectName("RunButton")
        self.StopButton = QtWidgets.QPushButton(self.centralwidget)
        self.StopButton.setGeometry(QtCore.QRect(1570, 0, 101, 41))
        font = QtGui.QFont()
        font.setPointSize(20)
        self.StopButton.setFont(font)
        self.StopButton.setObjectName("StopButton")
        self.PauseButton = QtWidgets.QPushButton(self.centralwidget)
        self.PauseButton.setGeometry(QtCore.QRect(380, 0, 91, 41))
        font = QtGui.QFont()
        font.setPointSize(15)
        self.PauseButton.setFont(font)
        self.PauseButton.setObjectName("PauseButton")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1769, 33))
        font = QtGui.QFont()
        font.setPointSize(15)
        self.menubar.setFont(font)
        self.menubar.setObjectName("menubar")
        self.menumenu1 = QtWidgets.QMenu(self.menubar)
        self.menumenu1.setObjectName("menumenu1")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setMinimumSize(QtCore.QSize(0, 40))
        font = QtGui.QFont()
        font.setPointSize(15)
        self.statusbar.setFont(font)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionfunc1 = QtWidgets.QAction(MainWindow)
        self.actionfunc1.setObjectName("actionfunc1")
        self.actionfunc1_2 = QtWidgets.QAction(MainWindow)
        self.actionfunc1_2.setObjectName("actionfunc1_2")
        self.actionfunc2 = QtWidgets.QAction(MainWindow)
        self.actionfunc2.setObjectName("actionfunc2")
        self.menumenu1.addAction(self.actionfunc1_2)
        self.menumenu1.addSeparator()
        self.menumenu1.addAction(self.actionfunc2)
        self.menubar.addAction(self.menumenu1.menuAction())

        self.retranslateUi(MainWindow)
        self.Tabs.setCurrentIndex(1)
        self.toolBox.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.pushButton.setText(_translate("MainWindow", "PushButton"))
        self.toolBox.setItemText(self.toolBox.indexOf(self.page), _translate("MainWindow", "Page 1"))
        self.toolBox.setItemText(self.toolBox.indexOf(self.page_2), _translate("MainWindow", "Page 2"))
        self.ACQmode.setItemText(0, _translate("MainWindow", "RptAline"))
        self.ACQmode.setItemText(1, _translate("MainWindow", "RptBline"))
        self.ACQmode.setItemText(2, _translate("MainWindow", "SurfScan"))
        self.ACQmode.setItemText(3, _translate("MainWindow", "SurfScan_Slicing"))
        self.ACQmodeLabel.setText(_translate("MainWindow", "Acquire mode"))
        self.FFTmode.setItemText(0, _translate("MainWindow", "GPU FFT Amp"))
        self.FFTmode.setItemText(1, _translate("MainWindow", "GPU FFT Amp+Phase"))
        self.FFTmode.setItemText(2, _translate("MainWindow", "Alazar FFT"))
        self.FFTmodeLabel.setText(_translate("MainWindow", "FFT mode"))
        self.ChannelLabel.setText(_translate("MainWindow", "Channel"))
        self.Channel.setItemText(0, _translate("MainWindow", "A"))
        self.Channel.setItemText(1, _translate("MainWindow", "B"))
        self.Channel.setItemText(2, _translate("MainWindow", "A+B"))
        self.Save.setText(_translate("MainWindow", "Save?"))
        self.textEdit.setHtml(_translate("MainWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'SimSun\'; font-size:15pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:16pt;\">C:</span></p></body></html>"))
        self.SaveDIRLabel.setText(_translate("MainWindow", "Save DIR"))
        self.DepthStartLabel.setText(_translate("MainWindow", "Depth Start"))
        self.DepthRangeLabel.setText(_translate("MainWindow", "Depth Range"))
        self.BlineAvgLabel.setText(_translate("MainWindow", "Bline average"))
        self.Tabs.setTabText(self.Tabs.indexOf(self.tab), _translate("MainWindow", "AcquireSetting"))
        self.CenterGalvo.setText(_translate("MainWindow", "CenterGalvo"))
        self.XstepsLabel.setText(_translate("MainWindow", "Xsteps"))
        self.AlineAvgLabel.setText(_translate("MainWindow", "Aline average"))
        self.XrangeLabel.setText(_translate("MainWindow", "X range(mm)："))
        self.Objective.setItemText(0, _translate("MainWindow", "OptoSigma5X"))
        self.Objective.setItemText(1, _translate("MainWindow", "OptoSigma10X"))
        self.XStepsizeLabel.setText(_translate("MainWindow", "Xstep size(um)"))
        self.BiasLabel.setText(_translate("MainWindow", "Bias(mm)"))
        self.waveformLabel.setText(_translate("MainWindow", "Galvo waveform"))
        self.Tabs.setTabText(self.Tabs.indexOf(self.GalvoTab), _translate("MainWindow", "Galvo"))
        self.Tabs.setTabText(self.Tabs.indexOf(self.DigitizerTab), _translate("MainWindow", "Digitizer"))
        self.Tabs.setTabText(self.Tabs.indexOf(self.StageTab), _translate("MainWindow", "Stage"))
        self.label_3.setText(_translate("MainWindow", "XY view"))
        self.label_2.setText(_translate("MainWindow", "YZ view"))
        self.label.setText(_translate("MainWindow", "sample surface"))
        self.RunButton.setText(_translate("MainWindow", "Run"))
        self.StopButton.setText(_translate("MainWindow", "Stop"))
        self.PauseButton.setText(_translate("MainWindow", "Pause"))
        self.menumenu1.setTitle(_translate("MainWindow", "menu1"))
        self.actionfunc1.setText(_translate("MainWindow", "func1"))
        self.actionfunc1_2.setText(_translate("MainWindow", "func1"))
        self.actionfunc2.setText(_translate("MainWindow", "func2"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
