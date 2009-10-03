# encoding: utf-8

"""
Find the frequencies of chromatic scale notes.
"""

import re

_reference_freq = 440.0 # use A440 as the reference note
_scale_constant = 2 ** (1.0/12)
def note_to_freq(octave, note, accidental):
    notes = dict((n, 1 - i)
        for i, n in enumerate(('B', 'A', 'G', 'F', 'E', 'D', 'C')))
    
    semitone = (octave - 4) * 12 + notes[note] * 2
    #if accidental in ('b', '♭'):
    if accidental == 'flat':
        if note == 'F':
            raise ValueError('F-flat does not exist')
        semitone -= 1
    #elif accidental in ('#', '♯'):
    elif accidental == 'sharp':
        if note == 'E':
            raise ValueError('E-sharp does not exist')
        semitone += 1
    
    return _reference_freq * (_scale_constant ** semitone)

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
