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

        

class WeaverAction():
    def __init__(self, action):
        super().__init__()
        self.action = action
        
class DnSAction():
    def __init__(self, action, data=[], raw = False, args = []):
        super().__init__()
        self.action=action
        self.data = data
        self.raw = raw
        self.args = args

class GPUAction():
    def __init__(self, action, mode='', memoryLoc=0, args=[]):
        super().__init__()
        self.action = action
        self.mode = mode
        self.memoryLoc = memoryLoc
        self.args = args
        
class DAction():
    def __init__(self, action):
        super().__init__()
        self.action = action 
        
class DbackAction():
    def __init__(self, action):
        super().__init__()
        self.action = action 
        
class EXIT():
    def __init__(self):
        super().__init__()
        self.action='exit'
