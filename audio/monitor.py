# encoding: utf-8

from __future__ import with_statement

from pyaudio import PyAudio, paInt16
from threading import Thread, Lock, Condition
from collections import deque

class Monitor(object):
    """
    todo
    """
    
    DEFAULT_SAMPLE_RATE = 44100
    CHUNK_SIZE = 1024
    
    def __init__(self, device_index=None, sample_rate=None):
        self.pya = PyAudio()
        
        self.stream = self.pya.open(format=paInt16, channels=1, input=True,
            rate=sample_rate or self.DEFAULT_SAMPLE_RATE,
            frames_per_buffer=self.CHUNK_SIZE,
            input_device_index=device_index)
        self.access = Lock()
        self.samples_ready = Condition(lock=self.access)
        self.buffer = deque()
        self.thread = None
        self.running = False
    
    def start(self):
        if not self.stream:
            raise RuntimeError("PyAudio stream already closed")
        
        self.thread = Thread(target=self._monitor)
        self.running = True
        self.thread.start()
    
    def stop(self):
        self.running = False
        self.thread.join()
        self.thread = None
        
        self.stream.close()
        self.stream = None
        self.pya.terminate()
    
    def _monitor(self):
        while self.running:
            samples = self.stream.read(self.CHUNK_SIZE)
            with self.access:
                self.buffer.extend(samples)
                self.samples_ready.notify()
    
    def read(self):
        with self.access:
            if len(self.buffer) <= 0:
                self.samples_ready.wait()
            samples = self.buffer
            self.buffer = deque()
        
        return samples
