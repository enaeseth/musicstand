''' interpreter.py
	Takes a list of heard frequencies from the FFT machine, and checks if any 
	overtones from the matcher's current note are in that list.
	
	THINGS TO DO:
		If False-
			Find all the shit that it could be, by looking at the overtones and shit. Return that shit. Be like, "HEY! THIS THING HAS SEVERAL HARMONICS!"
'''

from notes import note_to_freq

class Interpreter():
	def __init__(self):
		self.heard_freqs = []

	def overtones(self, cur_freq):
		'''This actually checks for the notes in the list of heard frequencies.'''
		chord = True
		for note in cur_freq:
			cur_over = note
			while cur_over <= note*6:
				if cur_over not in heard:
					chord = False
				else:
					cur_over = cur_over + note
		if not chord:
			return freq_to_note(heard[0])
		else:
			return True
		
	def heard(self, heard_frequencies):
		'''The FFT thing should call this.'''
		heard = []
		for pair in self.heard_freqs:
			heard.append(pair[0])
		self.heard_freqs = heard
		
	def lookslike(self, current_notes):
		'''The matcher should call this. It will return True to the matcher
		if any harmonic of the note has been heard, and False otherwise.
		Currently, chords need to be 100% correct to get a True.'''
		cur_freq = []
		for note in current_notes:
			cur_freq.append(note_to_freq(note[0], note[1], note[2]))
		return overtones(cur_freq)