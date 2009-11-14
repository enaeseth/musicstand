# This thing reads a .ly file and spits out a list of all of the notes.
# It is ugly and dumb but it works.
# We may or may not comment this at a later date.
# Usage: python lilypondParser.py filetoparse.ly
# By Emily and Ben, 10/3/09

from __future__ import with_statement

import sys
import math
import os
from string import punctuation

try:
	from hashlib import sha1
except ImportError:
	from sha import new as sha1

class Note():
	def __init__(self, meas, dur, num):
		self.pitch = 0
		self.beatnumber = num
		self.measure = meas
		self.duration = dur
		self.accidental = None
		self.octave = 0
		
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
		bigNoteArray.append([self.measure, self.beatnumber, self.duration, [(self.octave, self.pitch, self.accidental)]])

def get_cache_dir(score_filename):
	digester = sha1()
	with open(score_filename, 'r') as score_file:
		for line in score_file:
			digester.update(line)
	
	osx_path = os.path.expanduser('~/Library/Application Support')
	if os.path.exists(osx_path):
		cache_root = os.path.join(osx_path, 'Music Stand')
	else:
		cache_root = os.path.expanduser('~/.musicstand')
	
	if not os.path.exists(cache_root):
		os.makedirs(cache_root)
	return os.path.join(cache_root, digester.hexdigest())

def parseFile(filename):
	notes = []
	bigNoteArray = []
	file = open(filename, 'r')
	notesPos = 0
	foundNotes = False
	for line in file:
		list = line.split()
		if list:
			if list[0][0].isalpha() or list[0][0] == "<" or list[0][0] == ">":
				foundNotes = True
				for i in list:
					if i[0].isalpha() or i[0] == "<" or i[0] == ">":
						notes.append(i.upper())
						
		if not foundNotes:
			notesPos += 1
			
	file.close()
	octavo = 4
	measure = 1.00
	duration = 4.0
	number = 1
	chord = False
	for note in notes:
		if note == "<":
			chord = True
		elif note == ">":
			chord = False
			measure = measure + (1/float(duration))
		else:
			measure = str(measure)
			parts = measure.split('.')
			beatnumber = "."+parts[1]
			measure = float(measure)
			measureNum = parts[0]
			thisNote = Note(float(measureNum), float(duration), float(beatnumber))
			thisNote.parseNote(note)
			number += 1
			if len(bigNoteArray) >= 1:
				octavo = octavo + thisNote.octave + findOctave(bigNoteArray[-1][3][0][1],thisNote.pitch)
				thisNote.octave = octavo
			else:
				octavo = octavo + thisNote.octave
				thisNote.octave = octavo
			thisNote.printNote(bigNoteArray)
			if not chord:
				measure = measure + (1/float(thisNote.duration))
			duration = thisNote.duration
	
	cache_dir = get_cache_dir(filename)
	if os.path.exists(cache_dir):
		# already generated these PDF's
		return (bigNoteArray, cache_dir)
	else:
		os.mkdir(cache_dir)
	
	loopNum = 1
	start = 0
	
	redcolor = "\override Voice.NoteHead	  #'color = #(rgb-color 1 0 .2) \n \override Voice.Stem			 #'color = #(rgb-color 1 0 .2)\n"
	blackcolor = "\override Voice.NoteHead		#'color = #(x11-color 'black) \n \override Voice.Stem		   #'color = #(x11-color 'black)\n"

	lilypond_path = os.path.join(os.path.dirname(__file__), 'lilypond.sh')
	while loopNum <= bigNoteArray[-1][0]:
		curPos = 0
		newfilename = filename[:-2]+str(loopNum)+".ly"
		new_path = os.path.join(cache_dir, os.path.basename(newfilename))
		outfile = open(new_path,'w')
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
				
		
		# writes lines leading up to notes to new file
		for line in infile:
			if curPos < notesPos:
				outfile.write(line)
				
			elif curPos == notesPos: 
			
				# write the notes before the notes that need to be colored
				list = line.split() 
				i = 0
				
				if start == 0:
					outfile.write(redcolor)
					
				else:	
					while i < start:
						outfile.write(list[i] + " ")
						if not list[i][0].isalpha():
							print list[i]
							numNotes += 1
						i += 1

				
				# write the color setting
				outfile.write(redcolor)
				
				# write the colored notes
				while i < start+numNotes:
					outfile.write(list[i] + " ")
					if not list[i][0].isalpha():
						print list[i]
						numNotes += 1
					i += 1

					
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
		
		os.system('"%s" "%s"' % (lilypond_path, new_path))
	
	return (bigNoteArray, cache_dir)
	
def findOctave(prevnote, curnote):
	curval = ord(curnote)
	prevval = ord(prevnote)
	if curval > prevval:
		dif = curval - prevval
		if dif > 3:
			return -1
		else:
			return 0
	else:
		dif = prevval - curval
		if dif > 3:
			return 1
		else:
			return 0
	
def masterMethod(filename):
	notes = parseFile(filename)
	return notes

if __name__ == '__main__':
	filename = sys.argv[1]
	notes = parseFile(filename)
	for item in notes:
		print item
	
