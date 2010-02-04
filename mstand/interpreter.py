''' interpreter.py
    Takes a list of heard frequencies from the FFT machine, and checks if any 
    overtones from the matcher's current note are in that list.
    
    THINGS TO DO:
        If False-
            Find all the shit that it could be, by looking at the overtones and shit. Return that shit. Be like, "HEY! THIS THING HAS SEVERAL HARMONICS!"
'''

from notes import *

class Interpreter(object):
    def __init__(self):
        # heard_notes stores the notes heard in frequency decomposition
        # we store notes instead of frequencies to work around floating-point
        # issues
        self.heard_notes = set()

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
        
    def heard(self, heard_frequencies):
        '''The FFT thing should call this.'''
        self.heard_notes = set(freq_to_note(freq)
            for freq, intensity in heard_frequencies)
        
    def looks_like(self, current_notes):
        '''The matcher should call this. It will return True to the matcher
        if any harmonic of the note has been heard, and False otherwise.
        Currently, chords need to be 100% correct to get a True.'''
        
        return self.overtones(note_to_freq(*note) for note in current_notes)
