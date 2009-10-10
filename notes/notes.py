# encoding: utf-8

"""
Find the frequencies of chromatic scale notes.
"""

import re
import math

def note_to_semitone(octave, note, accidental):
    notes = {
        'A': 0,
        'B': 2,
        'C': -9,
        'D': -7,
        'E': -5,
        'F': -4,
        'G': -2
    }
    
    semitone = (octave - 4) * 12 + notes[note]
    print "(%d - 4 * 12 + %d) = %d" % (octave, notes[note], semitone)
    if accidental in ('b', '♭', 'flat'):
        semitone -= 1
    elif accidental in ('#', '♯', 'sharp'):
        semitone += 1
    return semitone

_reference_freq = 440.0 # use A440 as the reference note
_scale_constant = 2 ** (1.0/12)
def semitone_to_freq(semitone):
    return _reference_freq * (_scale_constant ** semitone)

def note_to_freq(octave, note, accidental):
    return semitone_to_freq(note_to_semitone(octave, note, accidental))

def freq_to_semitone(frequency):
    def round(value):
        def pair(transformer):
            transformed = transformer(value)
            return (abs(value - transformed), int(transformed))
        return min((pair(math.floor), pair(math.ceil)))
    
    raw = math.log(frequency / _reference_freq, 2) * 12
    semitone, error = round(raw)
    
    return semitone, error

def semitone_to_note(semitone):
    return semitone
    # return divmod(semitone + 10, 12)
    

_note_pattern = re.compile(r'^([A-G])([b♭#♯-♮])?(\d+)$')
def parse_note(note_description):
    """
    Parse a description of a note written in scientific pitch notation.
    """
    
    match = _note_pattern.match(note_description)
    if not match:
        raise ValueError('unable to interpret "%s" as a musical note' %
            note_description)
    
    return (int(match.group(3)), match.group(1), match.group(2) or None)

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print >>sys.stderr, "usage: python %s {note}[accidental]{octave}" % \
            sys.argv[0]
        print >>sys.stderr, "(e.g., A4, C#5, Eb3)"
        sys.exit(1)
    
    print "%.03f" % note_to_freq(*parse_note(sys.argv[1]))
