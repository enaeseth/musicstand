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

class Note(object):
	def __init__(self, meas, dur, num):
		self.pitch = 0
		self.beat_number = num
		self.measure = meas
		self.duration = dur
		self.accidental = None
		self.octave = 0
		
	def parse_note(self, note_data, time, beats):
		self.pitch = note_data[0]
		if 'is' in note_data:
			self.accidental = 'sharp'
		if 'es' in note_data:
			self.accidental = 'flat'
		for char in note_data:
			if char.isdigit():
				self.duration = time / (float(char) * beats)
			elif char == '\'':
				self.octave += 1
			elif char == ',':
				self.octave -= 1
				
	def print_note(self,big_note_array):
		big_note_array.append([self.measure, self.beat_number, self.duration, [(self.octave, self.pitch, self.accidental)]])

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

def parse_file(filename):
	notes = []
	big_note_array = []
	file = open(filename, 'r')
	notes_pos = 0
	found_notes = False
	beats = 4.0
	time = 4.0
	for line in file:
		list = line.split()
		if list:
			if list[0][0].isalpha() or list[0][0] == "<" or list[0][0] == ">":
				found_notes = True
				for i in list:
					if i[0].isalpha() and not i[0] == "r" or i[0] == "<" or i[0] == ">":
						notes.append(i.upper())
						
			elif list[0] == "\\time":
				timesig = list[1].split('/')
				beats = float(timesig[0])
				time = float(timesig[1])
				
		if not found_notes:
			notes_pos += 1
	
	file.close()
	octavo = 4
	measure = 1.00
	duration = time
	number = 1
	chord = False
	for note in notes:
		if note == "<":
			chord = True
		elif note == ">":
			chord = False
			measure += duration
		else:
			beat_number = measure - int(measure)
			this_note = Note(math.floor(measure), float(duration), float(beat_number))
			this_note.parse_note(note, time, beats)
			number += 1
			if len(big_note_array) >= 1:
				octavo = octavo + this_note.octave + find_octave(big_note_array[-1][3][0][1],this_note.pitch)
				this_note.octave = octavo
			else:
				octavo = octavo + this_note.octave
				this_note.octave = octavo
			this_note.print_note(big_note_array)
			if not chord:
				measure += (float(this_note.duration))
			duration = this_note.duration
	
	cache_dir = get_cache_dir(filename)
	# print cache_dir, os.path.exists(cache_dir)
	if os.path.exists(cache_dir):
		# already generated these PDF's
		return (big_note_array, cache_dir)
	else:
		os.mkdir(cache_dir)
	
	loop_num = 1
	start = 0
	
	redcolor = "\override Voice.NoteHead	  #'color = #(rgb-color 1 0 .2) \n \override Voice.Stem			 #'color = #(rgb-color 1 0 .2)\n"
	blackcolor = "\override Voice.NoteHead		#'color = #(x11-color 'black) \n \override Voice.Stem		   #'color = #(x11-color 'black)\n"

	lilypond_path = os.path.join(os.path.dirname(__file__), 'lilypond.sh')
	while loop_num <= big_note_array[-1][0]:
		cur_pos = 0
		newfilename = filename[:-2]+str(loop_num)+".ly"
		new_path = os.path.join(cache_dir, os.path.basename(newfilename))
		outfile = open(new_path,'w')
		infile = open(filename,'r')
		
		# get the number of notes in this measure
		inmeasure = True
		num_notes = 0
		pos_in_measure = start
		while inmeasure:
			if pos_in_measure >= len(big_note_array):
				break
			elif big_note_array[pos_in_measure][0] == loop_num:
				num_notes += 1
				pos_in_measure += 1
			else:
				inmeasure = False
				
		
		# writes lines leading up to notes to new file
		for line in infile:
			if cur_pos < notes_pos:
				outfile.write(line)
				
			elif cur_pos == notes_pos: 
			
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
							num_notes += 1
						i += 1

				
				# write the color setting
				outfile.write(redcolor)
				
				# write the colored notes
				while i < start+num_notes:
					outfile.write(list[i] + " ")
					if not list[i][0].isalpha():
						print list[i]
						num_notes += 1
					i += 1

					
				# write black color
				outfile.write(blackcolor)
				
				# write the rest of the notes
				for i in range(start+num_notes,len(list)):
					outfile.write(list[i]+ " ")
			else:
				outfile.write(line)
		
			cur_pos += 1
		
		loop_num += 1
		start += num_notes

		infile.close()
		outfile.close()
		
		os.system('"%s" "%s"' % (lilypond_path, new_path))
	
	return (big_note_array, cache_dir)
	
def find_octave(prevnote, curnote):
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
	notes = parse_file(filename)
	return notes

if __name__ == '__main__':
	filename = sys.argv[1]
	notes = parse_file(filename)
	for item in notes:
		print item
	
