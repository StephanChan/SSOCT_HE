# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 16:43:51 2023

@author: admin
"""
# here defines all the legitimate actions that can be put into a queue

class StageAction():
    def __init__(self, action):
        super().__init__()
        self.action=action

        
class SaveAction():
    def __init__(self, action, data, filename):
        super().__init__()
        self.action=action
        self.data = data
        self.filename = filename
        
class GPUAction():
    def __init__(self, action):
        super().__init__()
        self.action=action

class ACQAction():
    def __init__(self, action):
        super().__init__()
        self.action = action
        
class DisplayAction():
    def __init__(self, action, data):
        super().__init__()
        self.action=action
        self.data = data
        
class EXIT():
    def __init__(self):
        super().__init__()
        self.action='exit'
