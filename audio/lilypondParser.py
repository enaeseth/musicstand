# This thing reads a .ly file and spits out a list of all of the notes.
# It is ugly and dumb but it works.
# We may or may not comment this at a later date.
# Usage: python lilypondParser.py filetoparse.ly
# By Emily and Ben, 10/3/09

import sys
import math
import os
from string import punctuation

class Note():
	def __init__(self, octavo, meas, dur, num):
		self.pitch = 0
		self.beatnumber = num
		self.measure = meas
		self.duration = dur
		self.accidental = None
		self.octave = octavo
		
	def parseNote(self, noteData):
		self.pitch = noteData[0]
		if 'is' in noteData:
			self.accidental = 'sharp'
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
		bigNoteArray.append((self.measure, self.beatnumber, self.duration, [(self.octave, self.pitch, self.accidental)]))
		
def parseFile(filename):
	notes = []
	bigNoteArray = []
	file = open(filename, 'r')
	
	notesPos = 0
	foundNotes = False
	for line in file:
		list = line.split()
		if list:
			if list[0][0].isalpha() or list[0] == "<":
				foundNotes = True
				for i in list:
					if i[0].isalpha():
						notes.append(i.upper())
		if not foundNotes:
			notesPos += 1
			
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
		
	loopNum = 1
	start = 0
	
	redcolor = "\override Voice.NoteHead	  #'color = #(rgb-color 1 0 .2) \n \override Voice.Stem			 #'color = #(rgb-color 1 0 .2)\n"
	blackcolor = "\override Voice.NoteHead		#'color = #(x11-color 'black) \n \override Voice.Stem		   #'color = #(x11-color 'black)\n"

	while loopNum <= bigNoteArray[-1][0]:
		curPos = 0
		newfilename = filename[:-2]+str(loopNum)+".ly"
		outfile = open(newfilename,'w')
		infile = open(filename,'r')
		
		# get the number of notes in this measure
		inmeasure = True
		numNotes = 0
		posInMeasure = start
		while inmeasure:
			if posInMeasure >= len(bigNoteArray):
				break
			elif bigNoteArray[posInMeasure][0] == loopNum:
				numNotes += 1
				posInMeasure += 1
			else:
				inmeasure = False
				
		print numNotes
		
		# writes lines leading up to notes to new file
		for line in infile:
			if curPos < notesPos:
				outfile.write(line)
				
			elif curPos == notesPos: 
			
				# write the notes before the notes that need to be colored
				list = line.split() 
				for i in range(start):
					outfile.write(list[i] + " ")
				
				# write the color setting
				outfile.write(redcolor)
				
				# write the colored notes
				for i in range(start, start+numNotes):
					outfile.write(list[i] + " ")
				
				# write black color
				outfile.write(blackcolor)
				
				for i in range(start+numNotes,len(list)):
					outfile.write(list[i]+ " ")
			
			else:
				outfile.write(line)
		
			curPos += 1
		
		loopNum += 1
		start += numNotes

		infile.close()
		outfile.close()
		
		os.system("lilypond.sh " + newfilename) 
	
	return bigNoteArray
	
def masterMethod(filename):
	notes = parseFile(filename)
	return notes

if __name__ == '__main__':
	filename = sys.argv[1]
	notes = parseFile(filename)
	for item in notes:
		print item
	
