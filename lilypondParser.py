# This thing reads a .ly file and spits out a list of all of the notes.
# It is ugly and dumb but it works.
# We may or may not comment this at a later date.
# Usage: python lilypondParser.py filetoparse.ly
# By Emily and Ben, 10/3/09

import sys
from string import punctuation

class Note():
	def __init__(self, octavo, meas, dur, num):
		self.pitch = 0
		self.number = num
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
				self.duration = char
			elif char == '\'':
				self.octave += 1
			elif char == ',':
				self.octave -= 1
				
	def printNote(self):
		noteArray = [self.measure, self.number, self.duration, [self.pitch, self.octave, self.accidental]]
		print noteArray
		
def parseFile(filename):
	notes = []
	file = open(filename, 'r')
	for line in file:
		list = line.split()
		if list:
			if list[0].isalpha() or list[0] == "<":
				for i in list:
					if i[0].isalpha():
						notes.append(i)
	file.close()
	octavo = 4
	measure = 0
	duration = 4
	number = 1
	for note in notes:
		thisNote = Note(octavo, measure, duration, number)
		thisNote.parseNote(note)
		thisNote.printNote()
		number += 1
		octavo = thisNote.octave
		measure = measure + (1/float(thisNote.duration))
		duration = thisNote.duration
	
	
if __name__ == '__main__':
	filename = sys.argv[1]
	parseFile(filename)
	
