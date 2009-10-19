# encoding: utf-8

from __future__ import with_statement

from threading import Thread, Lock, Condition
from collections import deque

class Analyzer(object):
    """
    Gets samples from a monitor and finds audio frequencies in them.
    """
    
    def __init__(self, monitor):
        self.monitor = monitor
        self.running = False
