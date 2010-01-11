# encoding: utf-8

"""
Provides a simple matching algorithm.
"""

from mstand.notes import freq_to_note, note_to_freq, unparse_note
from mstand.match.algorithm import Algorithm, UnknownPositionError
from dtw import where_are_we

class SimpleAlgorithm(Algorithm):
    """
    Emma's original one-note-at-a-time matching algorithm.
    """
    
    def __init__(self, min_octave=2):
        super(SimpleAlgorithm, self).__init__()
        self.min_octave = min_octave
    
    def start_piece(self):
        self.intervals = self.matcher.intervals
        for interval in self.intervals:
            interval.notes = [freq_to_note(note_to_freq(*note)) for note in interval.notes]
        self.miss_count = 0
        self.current_location = 0
        self.last_note = None
        self.last_heard = []
    
    def filter_frequencies(self, frequencies):
        # only use the first (most prominent) note
        return freq_to_note(frequencies[0]) if frequencies else None
    
    def match(self, new_note):
        new_note = freq_to_note(note_to_freq(*new_note))
        
        if self.miss_count >= 4:
            staff = [i.notes[0][1] for i in self.matcher.intervals]
            self.miss_count = 0
            self.debug('looking for %r' % self.last_heard)
            self.current_location = where_are_we(staff, self.last_heard)[0]
            self.debug("DTW'ing our way to %r" % self.current_location)
            return self.current_location
        
        if new_note[0] < self.min_octave:
            # ignore it
            return self.current_location
        
        print '%s (%s), %d' % (new_note[1], unparse_note(*new_note), self.miss_count)
        
        if new_note != self.last_note:
            if len(self.last_heard) >= 4:
                self.last_heard.pop()
            self.last_heard.append(new_note[1])
        
        def matches(position):
            try:
                letters = [n[1] for n in self.intervals[position].notes]
                self.debug('%s =?= %s', new_note[1], ''.join(letters))
                return new_note[1] in letters
            except IndexError:
                return False
        
        # min(self.miss_count + 2, 4)
        for i in range(1, 2) + [0]:
            if matches(self.current_location + i):
                self.debug('found it on %d + %d' % (self.current_location, i))
                self.current_location += i
                self.miss_count = max(self.miss_count - (i + 1), 0)
                break
        else:
            if new_note != self.last_note: 
                self.miss_count += 1
        
        self.last_note = new_note
        # for i in range(1, min(self.miss_count + 1, 3) + 1) + [0]:
        #     if matches(self.current_location + i):
        #         self.current_location += i
        #         if i > 0:
        #             self.debug("onward, %d notes" % i)
        #             self.miss_count = max(self.miss_count - i, 0)
        # if matches(self.current_location + 1):
        #     # self.debug("MOVING FORWARD LIKE A SCREAMING NARWHAL")
        #     self.current_location += 1
        #     self.miss_count = max(self.miss_count - 1, 0)
        # elif matches(self.current_location):
        #     self.miss_count = max(self.miss_count - 1, 0)
        # else:
        #     self.miss_count += 1
        
        # self.debug('%r (%d misses)' % (self.current_location, self.miss_count))
        # self.debug('miss count is now %d', self.miss_count)
        return self.current_location
