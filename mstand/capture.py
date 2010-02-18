# encoding: utf-8

"""
Easily capture FFT results from a Listener.
"""

from __future__ import with_statement

from mstand import audio
from mstand.filters import *
from mstand.notes import Note

from threading import Thread, Condition
from time import sleep

class Capturer(object):
    """
    Captures FFT results from a listener.
    
    Using a Capturer object handles spawning a thread to read from the
    FFT result queue and handle the resulting buckets.
    """
    
    EXCESSIVE_SILENCE = 45
    
    def __init__(self, listener, handler=None, notes=True,
                 thread_name='Capturer'):
        self._listener = listener
        self._fft_queue = None
        self._thread = None
        self._thread_name = thread_name
        self._handler = handler
        self._running = False
        self._sync = Condition()
        
        self._freq_converter = Note.from_frequency if notes else None
    
    def start(self):
        """
        Starts the listener and begin reading its results on a dedicated
        thread.
        """
        
        assert not self._running
        
        self._fft_queue = self._listener.start()
        
        self._thread = Thread(target=self._run, name=self._thread_name)
        
        with self._sync:
            self._running = True
            self._thread.start()
            
            # wait for the thread to tell us that it has started
            self._sync.wait()
    
    def run_until_interrupt(self, check_interval=0.2):
        """
        Starts the listener and sleeps until the main thread is
        interrupted.
        """
        
        self.start()
        try:
            while True:
                try:
                    sleep(check_interval)
                except KeyboardInterrupt:
                    print
                    break
        finally:
            self.stop()
    
    def stop(self):
        """
        Stops capturing and listening.
        """
        
        if not self._running:
            return
        
        with self._sync:
            self._running = False
        self._thread.join()
        
        self._listener.stop()
        self._fft_queue = None
    
    class CaptureState(object):
        def __init__(self):
            self.results = []
            self.silence_count = 0
    
    def capture(self):
        """
        Captures a run of FFT results from the listener.
        """
        
        assert self._handler is None
        
        done = Condition()
        state = self.CaptureState()
        
        def handle_result(buckets):
            if len(buckets) == 0:
                if state.results:
                    state.silence_count += 1
                    if state.silence_count >= self.EXCESSIVE_SILENCE:
                        self._handler = None
                        with done:
                            done.notify()
            else:
                if state.silence_count > 0:
                    state.results += [[] for i in xrange(state.silence_count)]
                    state.silence_count = 0
                
                state.results.append(buckets)
        
        with done:
            old_handler, self._handler = self._handler, handle_result
            try:
                done.wait()
            finally:
                self._handler = old_handler
        
        return state.results
    
    def handle(self, results):
        """
        The default FFT result handler.
        
        It is possible to subclass Capturer and override this method
        instead of passing a handler function to the initializer.
        """
        pass
    
    def _run(self):
        # notify calling thread of startup
        with self._sync:
            self._sync.notify()
        
        while self._running:
            try:
                offset, buckets, data = self._fft_queue.pop()
            except KeyboardInterrupt:
                break
            
            if self._freq_converter:
                buckets = [(self._freq_converter(freq), intensity)
                    for freq, intensity in buckets]
            
            handler = (self._handler or self.handle)
            handler(buckets)
