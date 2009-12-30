# encoding: utf-8

"""
Provides a simple matching algorithm.
"""

from mstand.notes import freq_to_note
from mstand.match.algorithm import Algorithm, UnknownPositionError

class SimpleAlgorithm(Algorithm):
    """
    Emma's original one-note-at-a-time matching algorithm.
    """
    
    def __init__(self, min_octave=2):
        super(SimpleAlgorithm, self).__init__()
        self.min_octave = min_octave
    
    def start_piece(self):
        self.intervals = self.matcher.intervals
        self.miss_count = 0
        self.current_location = 0
        self.current_note = None
    
    def filter_frequencies(self, frequencies):
        # only use the first (most prominent) note
        return freq_to_note(frequencies[0])
    
    def match(self, new_note):
        if new_note == self.current_note or new_note[0] < min_octave:
            # ignore it
            return self.current_location
        
        def matches(position):
            try:
                letters = [n[1] for n in self.intervals[position].notes]
                self.debug('%s =?= %s', new_note[1], ''.join(letters))
                return new_note[1] in letters
            except IndexError:
                return False
        
        for i in range(1, min(self.miss_count + 1, 3)) + [0]:
            if matches(self.current_location + i):
                if i > 0:
                    self.debug("onward, %d notes" % i)
                    self.current_location += i
                    self.miss_count = max(self.miss_count - i, 0)
        if matches(self.current_location + 1):
            self.debug("MOVING FORWARD LIKE A SCREAMING NARWHAL")
            self.current_location += 1
            self.miss_count = max(self.miss_count - 1, 0)
        elif matches(self.current_location):
            self.miss_count = max(self.miss_count - 1, 0)
        else:
            self.miss_count += 1
        
        self.debug('miss count is now %d', self.miss_count)
        return self.current_location
