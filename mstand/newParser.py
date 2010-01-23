"""
MIDI file parsetacular
By Emily.
Make sure any .ly file you test with this looks vaguely like this:
  \score {
    \relative { \time 6/8 c4 e g8 a8 b4 < a b c> c1 }
    \midi { }
  }
It can have other crap in it too, but the important part is the \midi { } line.
Eventually I'll probably write something that adds that line if the file doesn't have it,
but for now I just wanted to get this out.

Also to happen eventually: comments. LOLZ
"""

import sys
import os

class Note(object):
	def __init__(self, meas, dur, num):
	    self.pitch = 0
	    self.beat_number = num
	    self.measure = meas
	    self.duration = dur
	    self.accidental = None
	    self.octave = 0

        def pitch_to_note(self,pitch):
            pitch_dict = {0:['C',None],1:['C','sharp'],2:['D',None],3:['E','flat'],4:['E',None],5:['F',None],6:['F','sharp'],
                          7:['G',None],8:['G','sharp'],-3:['A',None],-2:['B','flat'],-1:['B',None]}
            self.octave = ((pitch+3)/12)-1
            norm_pitch = pitch-(12*(self.octave+1))
            new_pitch = pitch_dict[norm_pitch]
            self.pitch = new_pitch[0]
            self.accidental = new_pitch[1]

	def note_to_dict(self, notes_by_start_time, start_time):
	    notes_by_start_time[start_time] = [self.measure, self.beat_number, self.duration, [(self.octave, self.pitch, self.accidental)]]

def add_multiple(pitch):
    pitch_dict = {0:['C',None],1:['C','sharp'],2:['D',None],3:['E','flat'],4:['E',None],5:['F',None],6:['F','sharp'],
                  7:['G',None],8:['G','sharp'],-3:['A',None],-2:['B','flat'],-1:['B',None]}
    octave = ((pitch+3)/12)-1
    new_pitch, new_acc = pitch_dict[pitch-(12*(octave+1))][0], pitch_dict[pitch-(12*(octave+1))][1]
    return (octave, new_pitch, new_acc)

def parse_file(filename):
    notes = []
    ppq = 0
    time_sig = 0
    on_note_list = {}
    notes_by_start_time = {}
    big_note_array = []
    the_file = open(filename,'r')
    for line in the_file:
        line_list = line.split()
        if len(line_list) > 1 and line_list[1] == "TimeSig":
            time_sig = [int(line_list[2].split('/')[0]), int(line_list[2].split('/')[1])]
            ppq = ppq*4/time_sig[1]

        elif len(line_list) > 1 and line_list[0] == "MFile":
            ppq = int(line_list[3])

        elif len(line_list) > 1 and line_list[1] == "On":
            pitch = int(line_list[3].split('=')[1])
            on_note_list[pitch] = int(line_list[0])

        elif len(line_list) > 1 and line_list[1] == "Off":
            pitch = int(line_list[3].split('=')[1])
            start_time = on_note_list.pop(pitch)
            end_time = int(line_list[0])
            if start_time in notes_by_start_time:
                    note = notes_by_start_time.get(start_time)
                    note[3].append(add_multiple(pitch))
            else:
                    new_note = Note(((start_time/ppq)/time_sig[0])+1, (float(end_time-start_time)/ppq), ((float(start_time)/ppq))%time_sig[1]+1)
                    new_note.pitch_to_note(pitch)
                    new_note.note_to_dict(notes_by_start_time, start_time)
                    
    list_of_keys = notes_by_start_time.keys()
    list_of_keys.sort()
    for i in list_of_keys:
        big_note_array.append(notes_by_start_time[i])
    return big_note_array

def masterMethod(filename):
        os.system("mf2t "+filename + ".midi > "+filename+".txt")
        return parse_file(filename+".txt")

if __name__ == '__main__':
	filename = sys.argv[1]
        os.system("mf2t "+filename + ".midi > "+filename+".txt")
        notes = parse_file(filename+".txt")
	for item in notes:
		print item
