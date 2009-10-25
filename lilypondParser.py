# This thing reads a .ly file and spits out a list of all of the notes.
# It is ugly and dumb but it works.
# We may or may not comment this at a later date.
# Usage: python lilypondParser.py filetoparse.ly
# By Emily and Ben, 10/3/09

import sys
import math
from string import punctuation

class Note():
	def __init__(self, octavo, meas, dur, num):
		self.pitch = 0
		self.beatnumber = num
		self.measure = meas
		self.duration = dur
		self.accidental = False
		self.octave = octavo
		
	def parseNote(self, noteData):
		self.pitch = noteData[0]
		if 'is' in noteData:
			self.accidental = '#'
		if 'es' in noteData:
			self.accidental = 'flat'
		for char in noteData:
			if char.isdigit():
				self.duration = float(char)
			elif char == '\'':
				self.octave += 1
			elif char == ',':
				self.octave -= 1
				
	def printNote(self,bigNoteArray):
		bigNoteArray.append([self.measure, self.beatnumber, self.duration, [self.octave, self.pitch, self.accidental]])
		
def parseFile(filename):
	notes = []
	bigNoteArray = []
	file = open(filename, 'r')
	for line in file:
		list = line.split()
		if list:
			if list[0][0].isalpha() or list[0] == "<":
				for i in list:
					if i[0].isalpha():
						notes.append(i)
						
	file.close()
	octavo = 4
	measure = 1.00
	duration = 4.0
	number = 1
	for note in notes:
		measure = str(measure)
		parts = measure.split('.')
		beatnumber = "."+parts[1]
		measure = float(measure)
		measureNum = parts[0]
		thisNote = Note(octavo, float(measureNum), float(duration), float(beatnumber))
		thisNote.parseNote(note)
		thisNote.printNote(bigNoteArray)
		number += 1
		octavo = thisNote.octave
		measure = measure + (1/float(thisNote.duration))
		duration = thisNote.duration
		
	return bigNoteArray
	
	
if __name__ == '__main__':
	filename = sys.argv[1]
	notes = parseFile(filename)
	
