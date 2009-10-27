from __future__ import with_statement
import re
import lilypondParser
import PageOpener
import mutex as mu

class Matcher():

	def __init__(self, filename):
		self.incomingNotes = [] #The queue!
		self.lockQueue = mu.mutex()
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
			
	
	def add(self, freq):
		#print 'I AM IN ADD'
		note = [(4, "D", "flat")]
		self.lockQueue.lock(self.incomingNotes.append,note)
		while self.lockQueue.test():
			self.lockQueue.unlock()
	
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
										  # David and Eric will pass me a False.
										  #incorrect assumption, but we can try-- David'''
										  
		try:
			while True:
				done = False
				new_note = False
				while not done:
					if self.lockQueue.testandset():
						if len(self.incomingNotes) != 0:
							new_note = self.incomingNotes.pop(0)
							self.lockQueue.unlock()
							done = True
				if new_note == False:
					break
				else:
					print "New note:", new_note
					self.match(new_note)
					print "Current location in the array:", self.current_location 
					print "Current measure:", self.lilypond_tuples[self.current_location][0]
					print '------------------------'
					'''
					print "Current number of misses:", self.num_misses
					if self.num_misses > 2:
						print "THIS IS VERY BAD. INSERT NATHAN'S CODE HERE"
					print
					'''
					#PageOpener.openPage(int(self.lilypond_tuples[self.current_location][0]))
		except KeyboardInterrupt:
			pass
	
	

if __name__ == '__main__':
	newMatch = Matcher("test.ly")
	newMatch.run()
	
