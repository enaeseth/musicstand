# encoding: utf-8

"""
Smart interpretation of heard notes.
"""

from notes import *
import math
import profile

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
    
    def looks_like(self, current_notes):
        """
        The matcher should call this. 
        It will return True if, for every expected note, either the expected note
        or at least three of its overtones are present. (Currently, chords need to 
        be 100% correct to get a True.)
        """
        
        matched_notes = []
        for expected_note in current_notes:
            num_overtones = 0
            for heard_note in self.heard_notes:
                if expected_note == heard_note:
                    matched_notes.append(expected_note)
                if (expected_note == (2, 'G', None) and heard_note == (5, 'D', None) or 
                    expected_note == (4, 'G', None) and heard_note == (5, 'G', None) or
                    expected_note == (5, 'E', None) and heard_note == (6, 'E', None)):
                    matched_notes.append(expected_note)
                elif (float(note_to_freq(*heard_note))/note_to_freq(*expected_note) - 
                    math.floor(note_to_freq(*heard_note)/note_to_freq(*expected_note)) < 0.02):
                    print expected_note, heard_note
                    num_overtones += 1
            print "LISTEN UP THIS IS THE NUMBER OF OVERTONES:", num_overtones
            print "-------------------------------------------------------"
            if expected_note[0] < 3 and num_overtones > 0:
                matched_notes.append(expected_note)
        if set(current_notes).issubset(set(matched_notes)):
            print "MOVING FORWARD YAY"
        return set(current_notes).issubset(set(matched_notes))
        
class CombinedInterpreter(Interpreter):
    """
    An interpreter that looks for profiled notes.
    """
    def __init__(self, profile):
        super(CombinedInterpreter, self).__init__()
        self.profile = profile

    def looks_like(self, current_notes):
        """
        The matcher should call this. 
        It will return True if, for every expected note, at least half of its
        profiled notes are present.
        """
     
        note_profiles = {}
        for key in sorted(self.profile.peaks.keys()):
            for other_notes in self.profile.peaks[key]:
                if other_notes[0] not in note_profiles:
                    note_profiles[other_notes[0]] = set()          
                for smaller_key in sorted(other_notes[1]):
                    if other_notes[1][smaller_key] > .5:
                        note_profiles[other_notes[0]].add(smaller_key)
                    note_profiles[other_notes[0]].add(key)
        
        matched_notes = []
        for expected_note in current_notes:
            
            pnotes = note_profiles[expected_note]
            num_pnotes = 0
            for heard_note in self.heard_notes:
            
                if heard_note in pnotes:
                    num_pnotes += 1
            percent_heard = float(num_pnotes) / len(pnotes)
            if percent_heard >= 0.5:
                matched_notes.append(expected_note)
        if set(current_notes).issubset(set(matched_notes)):
            print "JUST FOUND", current_notes, "MOVING FORWARD NOW."      
        return set(current_notes).issubset(set(matched_notes))
                
                
                
                