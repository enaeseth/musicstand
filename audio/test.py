# encoding: utf-8

import audio
import time
import math
from mstand.notes import *
import operator

class MinimumIntensityFilter(object):
    def __init__(self, threshold):
        self.threshold = threshold
    
    def __call__(self, samples):
        return [(f, i) for (f, i) in samples if i >= self.threshold or int(f) == 196]

class SmoothFilter(object):
    def __init__(self, memory):
        self.memory = memory
        self._history = []
    
    def __call__(self, buckets):
        self._history.append(set(f for f, i in buckets))
        
        if len(self._history) < self.memory:
            return []
        
        self._history.pop(0)
        
        common_freqs = reduce(operator.and_, self._history)
        return [(f, i) for (f, i) in buckets if f in common_freqs]
        
class SineFilter(object):
    def __call__(self, buckets):
        return [(f, i) for (f, i) in buckets if i/(90*math.sin(f/(60*math.pi) + (3*math.pi)/2)+100) >= 1]
        
class LogFilter(object):
    def __call__(self, buckets):
        return [(f, i) for (f, i) in buckets if i/(math.log(f+1, 1.1) + 1) >= 1]
        
class SquareRootFilter(object):
    def __call__(self, buckets):
        return [(f, i) for (f, i) in buckets if i/((f/100)**2) >= 1]
                
if __name__ == '__main__':
    # input_devices = [d for d in audio.get_devices() if d.input_channels > 0]
    
    filters = [
        audio.CutoffFilter(4200.0),
        audio.NegativeFilter(),
        audio.CoalesceFilter(),
        # SineFilter(),
        # LogFilter(),
        # SquareRootFilter(),
        MinimumIntensityFilter(60.0),
        SmoothFilter(2)
    ]
    
    listener = audio.Listener(window_size=4096*4, interval=1024,
        filters=filters)
    
    queue = listener.start()
    while True:
        try:
            offset, buckets, data = queue.pop()
            good = 0
            for freq, intensity in buckets:
                good += 1
                bar = '=' * int(40 * (intensity / 110.0))
                print "%6.01f %3s:   %6.02f %s" % (freq,
                    unparse_note(*freq_to_note(freq)), intensity, bar)
            if good > 0:
                print
        except KeyboardInterrupt:
            print
            listener.stop()
            break
