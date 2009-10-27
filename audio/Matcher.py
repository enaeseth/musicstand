from __future__ import with_statement
import re
import lilypondParser
import PageOpener

class Matcher():

	def __init__(self, filename):
		self.incomingNotes = [] #The queue!
		self.lilypond_tuples = lilypondParser.masterMethod(filename)
		self.current_location = 0
		self.num_misses = 0

	'''def get_lp_tuples(self, filename):
		"""
		Reads the text file with the given filename and returns an array of 
		the tuples in that file. Emily, feel free to ignore this and use your 
		array instead.
		"""
		with open(filename, 'rt') as f:
			lilypond_tuples = []
			for line in f:
				parts = [part.strip() for part in line.split(',')]
				
				note = parts[3:]
				note[0] = int(note[0])
				if len(note) == 2:
					note.append(None) # no accidental
				
				timing = map(int, parts[:3])
				timing.append([tuple(note)])
				lilypond_tuples.append(tuple(timing))
			return lilypond_tuples'''
			
	
	def match(self, new_note):
		"""
		Takes the parsed Lilypond array, the current location in the array (as an
		integer), the new note as a tuple inside a list like [(octave,note,accidental)],
		and the current number of misses in a row. 
		
		Returns an updated location and updated number of misses. (If the number of 
		misses isn't currently 0 and the new note looks correct, the number of misses
		goes down by 1.)
		"""
		if new_note == self.lilypond_tuples[self.current_location][3]:
			self.num_misses = max(self.num_misses - 1, 0)
		elif new_note == self.lilypond_tuples[self.current_location+1][3]:
			self.current_location += 1
			self.num_misses = max(self.num_misses - 1, 0)
		else:
			self.num_misses += 1
	
	
	
	def run(self):		
		# This is my makeshift queue.
		'''q = []
		q.append([(4, "D", "flat")])
		q.append([(4, "E", "flat")])
		q.append([(4, "F", None)])
		q.append([(4, "D", None)])        # wrong note
		q.append([(4, "D", "flat")])      # wrong note
		q.append([(4, "D", "flat")])      # wrong note
		q.append([(4, "G", "flat")])
		q.append([(4, "G", "flat")])
		q.append(False)                    # I'm assuming that when the audio runs out,
										  # David and Eric will pass me a False.'''
		
		while True:
			new_note = self.incomingNotes.pop(0)
			if new_note == False:
				break
			else:
				print "New note:", new_note
				match(new_note)
				print "Current location in the array:", self.current_location 
				print "Current measure:", self.lilypond_tuples[self.current_location][0]
				print "Current number of misses:", self.num_misses
				if self.num_misses > 2:
					print "THIS IS VERY BAD. INSERT NATHAN'S CODE HERE"
				print
				PageOpener.openPage(self.lilypond_tuples[current_location][0])	
	
	

if __name__ == '__main__':
	newMatch = Matcher("test.ly")
	newMatch.run()
	