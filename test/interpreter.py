# encoding: utf-8

"""
Tests for the interpreter.
"""

import os
import sys
import unittest
import random

try:
    import mstand
except ImportError:
    # automatically set the correct Python import path for the Music Stand
    # code
    sys.path.insert(0,
        os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mstand.notes import note_to_freq, freq_to_note, parse_note
from mstand.interpreter import Interpreter

class InterpreterTests(unittest.TestCase):
    def setUp(self):
        self.interpreter = Interpreter()
    
    def _freqs(self, *notes):
        def as_bucket(note):
            intensity = random.uniform(10.0, 300.0)
            try:
                return (float(note), intensity)
            except:
                return (note_to_freq(*parse_note(note)), intensity)
        
        return [as_bucket(note) for note in notes]
    
    def _heard(self, *notes):
        self.interpreter.heard(self._freqs(*notes))
    
    def _contains(self, *notes):
        notes = [parse_note(note) for note in notes]
        return self.interpreter.looks_like(notes)
    
    def testHeard(self):
        self._heard('A4', 'A5')
    
    def testSingleNote(self):
        self._heard('A4')
        self.assertTrue(self._contains('A4'))
    
    def testHeardFirstOvertone(self):
        self._heard('A5')
        self.assertTrue(self._contains('A4'))
    
    def testHeardSecondOvertone(self):
        self._heard('A5')
        self.assertTrue(self._contains('D4'))
    
    def testNoHarmonicsHeard(self):
        self._heard('G4')
        self.assertFalse(self._contains('D4'))
    
    def testChord(self):
        self._heard('C4', 'E4', 'G4')
        self.assertTrue(self._contains('C4', 'E4', 'G4'))
    
    def testChordMissingNote(self):
        self._heard('C4', 'G4')
        self.assertFalse(self._contains('C4', 'E4', 'G4'))
    
    def testChordHarmonics(self):
        self._heard('C4', 'E4', 'C5', 'E5', 'G5')
        self.assertTrue(self._contains('C4', 'E4', 'G4'))

if __name__ == '__main__':
    unittest.main()
