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
    
    def starting_piece(self, intervals):
        self.intervals = intervals
        for interval in self.intervals:
            interval.notes = [freq_to_note(note_to_freq(*note)) for note in interval.notes]
        self.miss_count = 0
        self.current_location = -1
        self.last_notes = None
    
    def match(self, new_notes):
        if new_notes:
            if all(new_note[0] < self.min_octave for new_note in new_notes):
                # treat it as silence (XXX: is that the right thing to do?)
                new_notes = []
        
        self.matcher.interpreter.heard(new_notes)
        
        old_miss_count = self.miss_count
        for i in range(1, 1 + max(1, 1 + min(self.miss_count, 1))) + [0]:
            position = self.current_location + i
            
            if position < 0:
                # that would be before the start of the piece
                continue
            
            debug_new_notes = new_notes
            if hasattr(self.matcher.interpreter, 'match'):
                matched = self.matcher.interpreter.match(set(new_notes))
                debug_new_notes = [matched] if matched else []
            
            try:
                expected = self.intervals[position].notes
            except IndexError:
                # well, there isn't any interval there
                # we must be close to the end of the piece
                # that's exciting, but we should not crash here
                continue
            
            if i > 1 and len(expected) == 0:
            	continue
            
#            self.debug('%02d: [%s] =?= [%s]', position,
#                ', '.join(unparse_note(*note) for note in debug_new_notes),
#                ', '.join(unparse_note(*note) for note in expected))
            
            if self.matcher.interpreter.looks_like(expected):
                if i > 0:
                    self.debug('moving forward by %d to %d',
                        i, self.current_location + i)
                self.current_location += i
                self.miss_count = 0
                # self.miss_count = max(self.miss_count - (i + 1), 0)
                break
        else:
            if new_notes != self.last_notes and len(new_notes) > 0:
                self.miss_count += 1
        
#        if self.miss_count != old_miss_count:
#            self.debug('miss count is now %d' % self.miss_count)
        self.last_notes = new_notes
        return self.current_location
