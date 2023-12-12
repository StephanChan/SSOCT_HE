# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 16:43:51 2023

@author: admin
"""
# here defines all the legitimate actions that can be put into a queue

class moveto():
    def __init__(self, direction, destination):
        super().__init__()
        self.action='move to'
        self.direction=direction
        self.destination=destination
        
class setSpeed():
    def __init__(self, direction, speed):
        super().__init__()
        self.action='set speed'
        self.direction=direction
        self.speed=speed
        
class save():
    def __init__(self):
        super().__init__()
        self.action='save'
        
class process():
    def __init__(self):
        super().__init__()
        self.action='process'

class ACQ():
    def __init__(self, mode):
        super().__init__()
        self.action='acquire'
        self.mode=mode
        
class EXIT():
    def __init__(self):
        super().__init__()
        self.action='exit'