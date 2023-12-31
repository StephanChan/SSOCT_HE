# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 16:43:51 2023

@author: admin
"""
# here defines all the legitimate actions that can be put into a queue

import numpy as np

class AODOAction():
    def __init__(self, action):
        super().__init__()
        self.action=action

        
class SaveAction():
    def __init__(self, action, data, filename):
        super().__init__()
        self.action=action
        self.data = data
        self.filename = filename
        

class ACQAction():
    def __init__(self, action):
        super().__init__()
        self.action = action
        
class DisplayAction():
    def __init__(self, action, data=[], args = []):
        super().__init__()
        self.action=action
        self.data = data
        self.args = args

class GPUAction():
    def __init__(self, action, mode, memoryLoc, args=[]):
        super().__init__()
        self.action = action
        self.mode = mode
        self.memoryLoc = memoryLoc
        self.args = args
        
class BoardAction():
    def __init__(self, action):
        super().__init__()
        self.action = action 
        
class Board2ACQAction():
    def __init__(self, action):
        super().__init__()
        self.action = action 
        
class EXIT():
    def __init__(self):
        super().__init__()
        self.action='exit'
