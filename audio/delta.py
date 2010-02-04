# encoding: utf-8

"""
A tool for examining changes what notes are being heard.
"""

import audio
from datetime import datetime, timedelta
from mstand.notes import *
from mstand.filters import *
from collections import defaultdict
import operator

def color(color_spec, text, *args):
    colors = {
        '': '',
        'black': '30',
        'red': '31',
        'green': '32',
        'yellow': '33',
        'blue': '34',
        'purple': '35',
        'cyan': '36',
        'white': '37'
    }

    if color_spec.endswith('!'):
        bold = '1'
        color_spec = color_spec[:-1]
    else:
        bold = '0'

    if args:
        text = text % args

    color = colors[color_spec]
    if color:
        color = ';%s' % color
    return '\x1b[%s%sm%s\x1b[0;00m' % (bold, color, text)

def format_difference(event_time, reference_time):
    offset = event_time - reference_time
    
    minutes = offset.seconds / 60
    seconds = float(offset.seconds - minutes)
    seconds += offset.microseconds / 1000000.0
    
    return '%02d:%05.02f' % (minutes, seconds) 

if __name__ == '__main__':
    import sys
    
    notes = [note_to_freq(*parse_note(arg.upper())) for arg in sys.argv[1:]]
    colors = ['cyan!', 'green!', 'yellow!', 'red!', 'purple!', 'white!']
    if len(notes) == 1:
        print "Overtone highlighting:",
        
        highlighted = [notes[0] * (i + 1.0) for i in xrange(len(colors))]
        
        for color_name, h_freq in zip(colors, highlighted):
            print color(color_name,
                '%3s ' % unparse_note(*freq_to_note(h_freq))),
        print
    elif len(notes) > 1:
        print "Note highlighting:",
        highlighted = notes[:len(colors)]
        
        i = 2.0
        while len(highlighted) + len(notes) <= len(colors):
            highlighted += [freq * i for freq in notes]
            i += 1
        colors = colors[:len(highlighted)]
        
        for color_name, h_freq in zip(colors, highlighted):
            print color(color_name,
                '%3s ' % unparse_note(*freq_to_note(h_freq))),
        print
    else:
        highlighted = []
    
    filters = [
        audio.CutoffFilter(4200.0),
        audio.NegativeFilter(),
        audio.CoalesceFilter(),
        # SineFilter(),
        # LogFilter(),
        # SquareRootFilter(),
        MinimumIntensityFilter(20.0),
        SmoothFilter(4, 3)
    ]
    
    listener = audio.Listener(window_size=4096*4, interval=1024,
        filters=filters)
    
    queue = listener.start()
    
    start_time = None
    iterations = []
    notes = {}
    def print_profile():
        tones = notes.keys()
        tones.sort()
        
        note_names = [unparse_note(*semitone_to_note(tone)) for tone in tones]
        
        print ' ' * 8,
        for note, tone in zip(note_names, tones):
            freq = semitone_to_freq(tone)
            
            if len(highlighted) == 0:
                color_name = 'white!'
            else:
                color_name = 'black!'
                for i, h_freq in enumerate(highlighted):
                    if freq_to_note(h_freq) == semitone_to_note(tone):
                        color_name = colors[i]
                        break
            
            print color(color_name, '%-3s' % note),
        print
        
        active_notes = set()
        for i, event_time in enumerate(iterations):
            print color('black!', format_difference(event_time, start_time)),
            
            current_notes = set(tone for tone in tones if i in notes[tone])
            new_notes = current_notes - active_notes
            dead_notes = active_notes - current_notes
            normal_notes = current_notes - new_notes
            
            for note, tone in zip(note_names, tones):
                note = '%-3s' % note
                if tone in new_notes:
                    print color('green!', note),
                elif tone in dead_notes:
                    print color('red!', note),
                elif tone in normal_notes:
                    print note,
                else:
                    print '   ',
            print
            
            active_notes = current_notes
    
    while True:
        try:
            offset, buckets, data = queue.pop()
            
            if len(buckets) == 0:
                if len(notes) > 0:
                    iterations.append(datetime.now())
                    print_profile()
                    notes.clear()
            else:
                if len(notes) == 0:
                    print color('yellow!', 'Listening, please wait...')
                    start_time = datetime.now()
                    iterations = []
                
                i = len(iterations)
                iterations.append(datetime.now())
                
                for freq, intensity in buckets:
                    tone = freq_to_semitone(freq)[0]
                    
                    try:
                        notes[tone].append(i)
                    except KeyError:
                        notes[tone] = [i]
        except KeyboardInterrupt:
            print
            listener.stop()
            break
