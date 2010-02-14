# encoding: utf-8

"""
Frequency filters (implemented in Python).
"""

import operator
from collections import defaultdict

def get_standard_filters():
    import audio
    
    return [
        audio.CutoffFilter(4200.0),
        audio.NegativeFilter(),
        audio.CoalesceFilter(),
        MinimumIntensityFilter(20.0),
        SmoothFilter(2, 4)
    ]

class MinimumIntensityFilter(object):
    def __init__(self, threshold):
        self.threshold = threshold
    
    def __call__(self, samples):
        return [(f, i) for (f, i) in samples if i >= self.threshold]
    
    def __repr__(self):
        return '%s(%r)' % (type(self).__name__, self.threshold)

class HistoryList(list):
    def __init__(self, capacity):
        list.__init__(self)
        self._capacity = capacity
    
    def append(self, x):
        while len(self) >= self._capacity:
            self.pop(0)
        return list.append(self, x)
    
    def expired(self, out_requirement):
        count = 0
        for intensity in reversed(self):
            if intensity == 0.0:
                count += 1
            else:
                break
        return count >= out_requirement

class SmoothHistory(defaultdict):
    def __init__(self, in_requirement, out_requirement):
        self.default_factory = \
            lambda: HistoryList(max(in_requirement, out_requirement))
        self.out_requirement = out_requirement
        self.active_notes = set()
    
    def __missing__(self, key):
        self.active_notes.add(key)
        return defaultdict.__missing__(self, key)

# class SmoothFilter(object):
#     def __init__(self, memory):
#         self.memory = memory
#         self._history = []
#     
#     def __call__(self, buckets):
#         self._history.append(set(f for f, i in buckets))
#         
#         if len(self._history) < self.memory:
#             return []
#         
#         self._history.pop(0)
#         
#         common_freqs = reduce(operator.and_, self._history)
#         return [(f, i) for (f, i) in buckets if f in common_freqs]

class SmoothFilter(object):
    def __init__(self, in_requirement, out_requirement):
        self.in_requirement = in_requirement
        self.out_requirement = out_requirement
        self._active_freqs = set()
        
        self._history = SmoothHistory(in_requirement, out_requirement)
    
    def __call__(self, buckets):
        for freq, intensity in buckets:
            self._history[freq].append(intensity)
        
        for freq in self._history.active_notes - set(f for f, i in buckets):
            self._history[freq].append(0.0)
            if self._history[freq].expired(self.out_requirement):
                del self._history[freq]
                self._history.active_notes.remove(freq)
        
        def average(l):
            intensities = [s if s > 0 else 0.6 * l[i - 1]
                for i, s in enumerate(l)]
            return sum(intensities) / len(l)
        
        result = [(f, average(history))
            for f, history in self._history.iteritems()
            if len(history) >= self.in_requirement]
        result.sort(key=lambda p: p[0])
        
        return result
    
    def __repr__(self):
        return '%s(%r, %r)' % (type(self).__name__, self.in_requirement,
            self.out_requirement)
