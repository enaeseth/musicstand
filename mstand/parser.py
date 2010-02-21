"""
MIDI file parsetacular
By Emily.

Also to maybe happen eventually: ...better comments? LOLZ
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
        '''MIDI gives us a number that corresponds to a note on a keyboard. For instance, 60 is Middle C. This converts that number to the note.'''
        pitch_dict = {0:['C',None],1:['C','sharp'],2:['D',None],3:['E','flat'],4:['E',None],5:['F',None],6:['F','sharp'], 7:['G',None],8:['G','sharp'],9:['A',None],10:['B','flat'],11:['B',None]}
        self.octave = ((pitch)/12)-1
        norm_pitch = pitch-(12*(self.octave+1))
        new_pitch = pitch_dict[norm_pitch]
        self.pitch = new_pitch[0]
        self.accidental = new_pitch[1]

    def note_to_dict(self, notes_by_start_time, start_time):
        '''Puts all the info into a form readable by the matcher.'''
        notes_by_start_time[start_time] = [self.measure, self.beat_number, self.duration, [(self.octave, self.pitch, self.accidental)]]

def add_multiple(pitch):
    '''If there are more than one note at a given time (MULTIPLE NOTES!?!?!) this adds those new notes to the correct place.'''
    pitch_dict = {0:['C',None],1:['C','sharp'],2:['D',None],3:['E','flat'],4:['E',None],5:['F',None],6:['F','sharp'], 7:['G',None],8:['G','sharp'],9:['A',None],10:['B','flat'],11:['B',None]}
    octave = ((pitch)/12)-1
    new_pitch, new_acc = pitch_dict[pitch-(12*(octave+1))][0], pitch_dict[pitch-(12*(octave+1))][1]
    return (octave, new_pitch, new_acc)

def is_current(generated_file, source_file):
    '''Eric did this.'''
    return os.path.getmtime(generated_file) >= os.path.getmtime(source_file)

def parse_file(filename):
    '''This function is Charles in Charge in this file.'''
    mf2t = os.path.join(os.path.dirname(__file__), './mf2t')
    
    base, ext = os.path.splitext(filename)
    if ext != '.midi':
        filename = base + '.midi'
    
    output = '%s.txt' % filename
    if not os.path.exists(output) or not is_current(output, filename):
        os.system('"%s" "%s" > "%s"' % (mf2t, filename, output))
    
    filename = '%s.txt' % filename
    notes = []
    ppq = 0
    time_sig = 0
    ppq_per_measure = 0
    on_note_list = {}
    notes_by_start_time = {}
    big_note_array = []
    the_file = open(filename,'r')
    for line in the_file:
        line_list = line.split()
        if len(line_list) > 1 and line_list[1] == "TimeSig":
            time_sig = [int(line_list[2].split('/')[0]), int(line_list[2].split('/')[1])]
            ppq_per_measure = (ppq*4*time_sig[0])/time_sig[1]

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
                #here there be dragons and super sketchy math
                new_note = Note((start_time/ppq_per_measure)+1, (float(end_time-start_time)/ppq_per_measure), (float(start_time)%ppq_per_measure)/ppq_per_measure)
                new_note.pitch_to_note(pitch)
                new_note.note_to_dict(notes_by_start_time, start_time)
                
    list_of_keys = notes_by_start_time.keys()
    list_of_keys.sort()
    for i in list_of_keys:
        big_note_array.append(tuple(notes_by_start_time[i]))
    return big_note_array

if __name__ == '__main__':
    filename = sys.argv[1]
    notes = parse_file(filename)
    for item in notes:
        print item
