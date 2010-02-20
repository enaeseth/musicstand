# encoding: utf-8

"""
Individual note tests.
"""

from mstand.test import *

def make_note_test(note):
    handle = note.lower()
    
    @test('%s (alone)' % note, handle)
    def test_individual_note():
        play(note.lower())
        expect(note)
    
    return test_individual_note

notes = ['C2', 'C#2', 'D2', 'D#2', 'C3', 'C#3', 'A3', 'C4', 'C#4', 'A4', 'C5', 'C#5', 'A5', 'C6']
for note in notes:
    make_note_test(note)
