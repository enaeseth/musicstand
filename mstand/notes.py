# encoding: utf-8

"""
Find the frequencies of chromatic scale notes.
"""

import re
import math
from operator import itemgetter as _itemgetter

class Note(tuple):
    """
    Note(octave, note, accidental): a chromatic scale musical note.
    """
    
    __slots__ = ()
    
    octave = property(_itemgetter(0))
    note = property(_itemgetter(1))
    letter = property(_itemgetter(1))
    accidental = property(_itemgetter(2))
    
    def __new__(cls, octave, note, accidental):
        return tuple.__new__(cls, (octave, note, accidental))
    
    def __repr__(self):
        return 'Note(%r, %r, %r)' % self
    
    def __str__(self):
        return unparse_note(*self)
    
    def __cmp__(self, other):
        try:
            if len(other) != 3:
                return NotImplemented
        except TypeError:
            return NotImplemented
        
        for i in xrange(3):
            result = cmp(self[i], other[i])
            if result != 0:
                return result
        
        return 0
    
    @property
    def frequency(self):
        return note_to_freq(*self)
    
    @classmethod
    def parse(cls, text):
        return cls(*parse_note(text))
    
    @classmethod
    def from_frequency(cls, freq):
        return cls(*freq_to_note(freq))

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
    error, semitone = round(raw)
    
    return semitone, error

def semitone_to_note(semitone):
    semitone += 48 # use A0 as the origin for this, not A4
    octave, step = divmod(semitone, 12)
    
    notes = (
        ('A', None),
        ('A', 'sharp'),
        ('B', None),
        ('C', None),
        ('C', 'sharp'),
        ('D', None),
        ('D', 'sharp'),
        ('E', None),
        ('F', None),
        ('F', 'sharp'),
        ('G', None),
        ('G', 'sharp')
    )
    
    if step > 2:
        octave += 1
    
    return (octave,) + notes[step]

def freq_to_note(frequency):
    return semitone_to_note(freq_to_semitone(frequency)[0])

_note_pattern = re.compile(r'^([A-G])([b♭#♯-♮])?(\d+)$')
def parse_note(note_description):
    """
    Parse a description of a note written in scientific pitch notation.
    """
    
    symbols = {
        'b': 'flat',
        '♭': 'flat',
        'flat': 'flat',
        '#': 'sharp',
        '♯': 'sharp',
        'sharp': 'sharp',
        '-': None,
        '♮': None,
        None: None
    }
    
    match = _note_pattern.match(note_description)
    if not match:
        raise ValueError('unable to interpret "%s" as a musical note' %
            note_description)
    
    return (int(match.group(3)), match.group(1), symbols[match.group(2)])

def unparse_note(octave, note, accidental, approx_symbols=True):
    symbols = {
        'b': ('b', '♭'),
        '♭': ('b', '♭'),
        'flat': ('b', '♭'),
        '#': ('#', '♯'),
        '♯': ('#', '♯'),
        'sharp': ('#', '♯')
    }
    
    sym_index = 0 if approx_symbols else 1
    try:
        symbol = symbols[accidental][sym_index]
    except KeyError:
        symbol = ''
    return "%s%s%d" % (note, symbol, octave)

if __name__ == '__main__':
    import sys
    
    try:
        semitone, error = freq_to_semitone(float(sys.argv[1]))
        print "%s (error: %.03f)" % (unparse_note(*semitone_to_note(semitone)),
            error)
    except ValueError:
        print "%.03f" % (note_to_freq(*parse_note(sys.argv[1])))
    
    # if len(sys.argv) < 2:
    #     print >>sys.stderr, "usage: python %s {note}[accidental]{octave}" % \
    #         sys.argv[0]
    #     print >>sys.stderr, "(e.g., A4, C#5, Eb3)"
    #     sys.exit(1)
    # 
    # print "%.03f" % note_to_freq(*parse_note(sys.argv[1]))
