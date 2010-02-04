# encoding: utf-8

import audio
import time
import math
from mstand.notes import *
from mstand.filters import *
        
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

if __name__ == '__main__':
    import sys
    # input_devices = [d for d in audio.get_devices() if d.input_channels > 0]
    
    filters = [
        audio.CutoffFilter(4200.0),
        audio.NegativeFilter(),
        audio.CoalesceFilter(),
        MinimumIntensityFilter(15.0),
        SmoothFilter(4, 2)
    ]
    
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
        colors = colors[:len(notes)]
        highlighted = notes[:len(colors)]
        
        for color_name, h_freq in zip(colors, highlighted):
            print color(color_name,
                '%3s ' % unparse_note(*freq_to_note(h_freq))),
        print
    else:
        highlighted = [0.0 for i in xrange(len(colors))]
    
    listener = audio.Listener(window_size=4096*4, interval=1024,
        filters=filters)
    
    queue = listener.start()
    while True:
        try:
            offset, buckets, data = queue.pop()
            good = 0
            notes = []
            for freq, intensity in buckets:
                notes.append((freq, unparse_note(*freq_to_note(freq)), intensity))
                # if freq == 0.0:
                #     continue
                # good += 1
                # bar = '=' * int(200 * (intensity / 700.0))
                # print "%6.01f %3s:   %6.02f %s" % (freq,
                #     unparse_note(*freq_to_note(freq)), intensity, bar)
            
            notes.sort(key=lambda p: p[2], reverse=True)
            if len(notes) > 0:
                for freq, note, power in notes:
                    text = '%3s: %6.02f ' % (note, power)
                    
                    for color_name, h_freq in zip(colors, highlighted):
                        if abs(h_freq - freq) < 2.0:
                            text = color(color_name, text)
                            break
                    else:
                        text = color('black!', text)
                    
                    print text,
                print
            
            if good > 0:
                print
        except KeyboardInterrupt:
            print
            listener.stop()
            break
