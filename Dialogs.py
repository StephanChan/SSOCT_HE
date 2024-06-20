# -*- coding: utf-8 -*-
"""
Created on Mon Apr 22 13:28:52 2024

@author: admin
"""
import sys

from PyQt5.QtWidgets import QApplication, QDialog
from Generaic_functions import ImagePlot
import numpy as np
from BlineDialogUI import Ui_Dialog as BlineDialogUI
from StageDialogUI import Ui_Dialog as StageDialogUI

class BlineDialog(QDialog):
    def __init__(self, Bline = []):
        super().__init__()

        self.ui = BlineDialogUI()
        self.ui.setupUi(self)
        
        pixmap = ImagePlot(Bline, 0, np.max(Bline[:])/2)
        # update image on the waveformLabel
        self.ui.Bline.setPixmap(pixmap)
        
        
class StageDialog(QDialog):
    def __init__(self, Xpos = 0, Ypos = 0, Zpos = 0):
        super().__init__()

        self.ui = StageDialogUI()
        self.ui.setupUi(self)
        self.ui.Xpos.setValue(Xpos)
        self.ui.Ypos.setValue(Ypos)
        self.ui.Zpos.setValue(Zpos)
        # self.confirm = False
        
        # self.ui.buttonBox.accepted.connect(self.accept)
        
    # def accept(self):
    #     self.confirm = True
        
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    # example = BlineDialog(np.random.random([200,1000]))
    example = StageDialog()
    example.show()
    sys.exit(app.exec_())