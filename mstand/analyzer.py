# encoding: utf-8
import fft
from threading import Thread
from pool import ThreadPool

class Analyzer(object):
    """
    Gets samples from a monitor and finds audio frequencies in them.
    """
    
    def __init__(self, callback, window_size, interval, fft_min_power=0):
        self.callback = callback
        self.window_size = window_size
        self.interval = interval
        
        self.monitor = None
        self.slicer_thread = None
        self.analyzer_pool = None
        self.sender_pool = None
        self.running = False
        self.min_power = fft_min_power
    
    def start(self, monitor):
        self.monitor = monitor
        self.running = True
        
        self.analyzer_pool = ThreadPool()
        self.sender_pool = ThreadPool()
        self.slicer_thread = Thread(name='Slicer', target=self._run)
        self.slicer_thread.start()
    
    def stop(self):
        if not self.running:
            return False
        
        self.running = False
        self.slicer_thread.join()
        self.slicer_thread = None
        
        return True
    
    def _run(self):
        self.monitor.start()
        
        buf = []
        
        while self.running:
            samples = self.monitor.read() # blocks until there are new samples
            if samples is None:
                # monitor was shut down
                self.running = False
                break
            
            buf.extend(samples)
            position = 0
            length = len(buf)
            while (length - position) >= self.window_size:
                end = position + self.window_size
                self._analyze(buf[position:end])
                
                position += self.interval
            
            if position > 0:
                buf = buf[position:]
        
        self.monitor.stop()
        self.analyzer_pool.shutdown()
        self.sender_pool.shutdown()
        print "Exiting analyzer."
    
    def _analyze(self, samples):
        def perform_analysis():
            #print len(samples), samples[0]
            results = fft.fft(samples, self.min_power)
            if results:
                self._send_results(results)
            else:
                self._send_results(None)
        
        self.analyzer_pool.execute(perform_analysis)
    
    def _send_results(self, results):
        self.sender_pool.execute(lambda: self.callback(results))
