# encoding: utf-8

"""
Provides a simple matching algorithm.
"""

from mstand.notes import freq_to_note, note_to_freq, unparse_note
from mstand.match.algorithm import Algorithm, UnknownPositionError
# from dtw import where_are_we

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
        self.current_location = -1
        self.last_notes = None
    
    def filter_frequencies(self, frequencies):
        notes = map(freq_to_note, frequencies)
        return notes
    
    def match(self, new_notes):
        if new_notes:
            if all(new_note[0] < self.min_octave for new_note in new_notes):
                # treat it as silence (XXX: is that the right thing to do?)
                new_notes = []
        
        self.matcher.interpreter.heard(new_notes)
        
        # print [unparse_note(*note) for note in new_notes]
        
        # if self.miss_count >= 4:
        #     staff = [i.notes[0][1] for i in self.matcher.intervals]
        #     self.miss_count = 0
        #     self.debug('looking for %r' % self.last_heard)
        #     self.current_location = where_are_we(staff, self.last_heard)
        #     self.debug("DTW'ing our way to %r" % self.current_location)
        #     return self.current_location
        
        # if new_note is not None:
        #     print '%s (%s), %d' % (new_note[1], unparse_note(*new_note),
        #         self.miss_count)
        # else:
        #     print '-silence-, %d' % self.miss_count
        
        # min(self.miss_count + 2, 4)
        for i in range(1, 2) + [0]:
            position = self.current_location + i
            
            if position < 0:
                # that would be before the start of the piece
                continue
            
            debug_new_notes = new_notes
            if hasattr(self.matcher.interpreter, 'match'):
                matched = self.matcher.interpreter.match(set(new_notes))
                debug_new_notes = [matched] if matched else []
            
            expected = self.intervals[position].notes
            self.debug('%02d: [%s] =?= [%s]', position,
                ', '.join(unparse_note(*note) for note in debug_new_notes),
                ', '.join(unparse_note(*note) for note in expected))
            
            if self.matcher.interpreter.looks_like(expected):
                self.debug('found it on %d + %d' % (self.current_location, i))
                self.current_location += i
                self.miss_count = max(self.miss_count - (i + 1), 0)
                break
        else:
            if new_notes != self.last_notes:
                self.miss_count += 1
        
        # self.debug('miss count is now %d' % self.miss_count)
        self.last_notes = new_notes
        return self.current_location
