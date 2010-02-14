# encoding: utf-8

try:
    import mstand
except ImportError:
    # automatically set PYTHONPATH appropriately
    import sys
    import os.path
    
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

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
        # audio.DecibelFilter(),
        SmoothFilter(2, 4)
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
        highlighted = notes[:len(colors)]
        
        i = 2.0
        while len(highlighted) + len(notes) <= len(colors):
            highlighted += [freq * i for freq in notes]
            i += 1
        highlighted = list(set(highlighted))
        highlighted.sort()
        colors = colors[:len(highlighted)]
        
        for color_name, h_freq in zip(colors, highlighted):
            print color(color_name,
                '%3s ' % unparse_note(*freq_to_note(h_freq))),
        print
    else:
        highlighted = []
    
    listener = audio.Listener(window_size=4096, interval=1024,
        filters=filters)
    
    queue = listener.start()
    series = dict((Note.from_frequency(f), []) for f in highlighted)
    plotted_notes = set(series.keys())
    while True:
        try:
            offset, buckets, data = queue.pop()
            good = 0
            notes = []
            for freq, intensity in buckets:
                notes.append((freq, Note.from_frequency(freq), intensity))
                # if freq == 0.0:
                #     continue
                # good += 1
                # bar = '=' * int(200 * (intensity / 700.0))
                # print "%6.01f %3s:   %6.02f %s" % (freq,
                #     unparse_note(*freq_to_note(freq)), intensity, bar)
            
            notes.sort(key=lambda p: p[2], reverse=True)
            if len(notes) > 0:
                found = set()
                for freq, note, power in notes:
                    try:
                        series[note].append(power)
                        found.add(note)
                    except KeyError:
                        pass
                    
                    text = '%3s: %6.02f ' % (note, power)
                    
                    for color_name, h_freq in zip(colors, highlighted):
                        if abs(h_freq - freq) < 4.0:
                            text = color(color_name, text)
                            break
                    else:
                        text = color('black!', text)
                    
                    print text,
                print
                
                for unfound in (plotted_notes - found):
                    series[unfound].append(0.0)
            
            if good > 0:
                print
        except KeyboardInterrupt:
            print
            listener.stop()
            
            if plotted_notes:
                mathematica_colors = ['Cyan', 'Green',
                    'RGBColor[0.8, 0.8, 0.1]', 'Red', 'Magenta',
                    'Black'][:len(series)]
                plots = []
                for freq in highlighted:
                    note = Note.from_frequency(freq)
                    plots.append('{%s}' %
                        ', '.join('%.02f' % power for power in series[note]))
                print 'ListLinePlot[{%s}, PlotStyle -> {%s}]' % \
                    (',\n    '.join(plots),
                    ', '.join('{%s, Thick}' % c for c in mathematica_colors))
            
            break
