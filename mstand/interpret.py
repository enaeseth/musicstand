# encoding: utf-8

"""
Smart interpretation of heard notes.
"""

from notes import *

class Interpreter(object):
    """
    The prototype for interpreter implementations.
    """
    
    def __init__(self):
        # heard_notes stores the notes heard in frequency decomposition
        # we store notes instead of frequencies to work around floating-point
        # issues
        self.heard_notes = set()
    
    def heard(self, heard_frequencies):
        """
        This should be called at the end of the filter chain.
        """
        
        # XXX: this sucks
        if len(heard_frequencies) == 0:
            self.heard_notes = set()
        elif len(heard_frequencies[0]) == 2:
            self.heard_notes = set(freq_to_note(freq)
                for freq, intensity in heard_frequencies)
        else:
            self.heard_notes = set(heard_frequencies)
    
    def looks_like(self, current_notes):
        """
        Returns True if the given list of notes "looks like" what was
        heard; false if otherwise.
        """
        
        raise NotImplementedError

class ProfileInterpreter(Interpreter):
    """
    An interpreter that uses an instrument profile.
    """
    
    def __init__(self, profile):
        super(ProfileInterpreter, self).__init__()
        
        self.profile = profile
        self.mapping = profile.mapping.copy()
    
    def notes(self):
        return sorted(self.mapping, key=lambda note: note_to_semitone(*note))
    
    def match(self, heard_notes):
        if len(heard_notes) == 0:
            return None
        
        winner = None
        best_overlap = (0.0, 0.0, 0)
        # print ', '.join(unparse_note(*note) for note in heard_notes) + ':'
        for note in self.notes():
            # print '  ' + unparse_note(*note),
            for i, pattern in enumerate(self.mapping[note]):
                intersection = pattern & heard_notes
                inter_len = float(len(intersection))
                overlap = (inter_len / len(pattern),
                    inter_len / len(heard_notes), -i)
                # print '%r: %r' % ([unparse_note(*n) for n in pattern], overlap),
                if overlap > best_overlap:
                    best_overlap = overlap
                    winner = note
            # print
        
        return winner
    
    def looks_like(self, current_notes):
        if len(current_notes) > 1:
            raise ValueError('the profile interpreter cannot currently '
                'interpret chords')
        
        heard = self.match(self.heard_notes)
        
        if len(current_notes) == 0:
            return heard is None
        else:
            return heard == current_notes[0]

class OvertoneInterpreter(Interpreter):
    """
    An interpreter that looks for overtones.
    """
    
    def overtones(self, frequencies):
        """
        For all the given frequencies, check if either that frequency or one
        of its first few harmonics has been heard.
        """
        
        def has_overtone(freq):
            """
            Checks if a single frequency has really been "heard".
            """
            
            # check if the note was heard, or any of its first five harmonics
            # were heard
            return any(freq_to_note(freq * i) in self.heard_notes
                for i in xrange(1, 7))
        
        # check that has_overtone returns true for all the frequencies
        return all(has_overtone(freq) for freq in frequencies)
    
    def looks_like(self, current_notes):
        '''The matcher should call this. It will return True to the matcher
        if any harmonic of the note has been heard, and False otherwise.
        Currently, chords need to be 100% correct to get a True.'''
        
        return self.overtones(note_to_freq(*note) for note in current_notes)
