from notes import note_to_freq

class Interpreter():
	def __init__(self):
		self.heard_freqs = []

	def overtones(self, cur_freq):
		cur_over = cur_freq
		while cur_over <= cur_freq*4:
			if cur_over in heard:
				return True
			else:
				cur_over = cur_over + cur_freq
		return False
		
	def heard(self, heard_frequencies):
		heard = []
		for pair in self.heard_freqs:
			heard.append(pair[0])
		self.heard_freqs = heard
		
	def lookslike(self, current_note):
		cur_freq = note_to_freq(current_note[0], current_note[1], current_note[2])
		return overtones(cur_freq)

if __name__ == '__main__':
	print interp.cur_freq
	print interp.overtones()