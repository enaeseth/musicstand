# encoding: utf-8

"""
Display the frequency decomposition of notes, and do other cool tricks.
"""

from __future__ import with_statement

try:
    import mstand
except ImportError:
    # automatically set PYTHONPATH appropriately
    import sys
    import os.path
    
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    import cPickle as pickle
except ImportError:
    import pickle

import audio
import time
import math
from mstand.notes import *
from mstand.filters import *
from mstand.terminal import color

if __name__ == '__main__':
    from optparse import OptionParser
    
    parser = OptionParser('%prog [options] [note ...]')
    parser.add_option('-r', '--record', metavar='FILENAME',
        help='Record FFT results to a file')
    parser.add_option('-o', '--only-highlighted', action='store_true',
        help='only show the highlighted notes')
    parser.add_option('-p', '--plot', action='store_true',
        help='Generate Mathematica plotting instructions')
    parser.add_option('-O', '--no-overtones', action='store_false',
        dest='overtones', help='do not automatically highlight overtones')
    parser.add_option('-m', '--min-intensity', type='float',
        help='the value for the minimum intensity filters')
    parser.add_option('-d', '--decibels', action='store_true',
        help='show intensities in dB')
    parser.add_option('-s', '--smooth', metavar='IN,OUT',
        help='set the parameters for the smoothing filter')
    parser.add_option('-i', '--interval', metavar='SAMPLES', type='int',
        help='FFT interval')
    parser.add_option('-w', '--window-size', metavar='SAMPLES', type='int',
        help='FFT window size')
    parser.set_defaults(interval=1024, window_size=4096, overtones=True,
        decibels=False, smooth='0', min_intensity=2.0, plot=False,
        only_highlighted=False)
    
    options, args = parser.parse_args()
    
    filters = [
        audio.CutoffFilter(4200.0),
        audio.NegativeFilter(),
        audio.CoalesceFilter(),
        MinimumIntensityFilter(options.min_intensity)
    ]
    
    if options.decibels:
        filters.append(audio.DecibelFilter)
    if options.smooth:
        smooth_spec = eval('(%s)' % options.smooth)
        if smooth_spec and smooth_spec != (0, 0):
            filters.append(SmoothFilter(*smooth_spec))
    
    notes = [note_to_freq(*parse_note(arg.upper())) for arg in args]
    colors = ['cyan!', 'green!', 'yellow!', 'red!', 'purple!', 'black!']
    if len(notes) > 0:
        print "Note highlighting:",
        highlighted = notes[:len(colors)]
        
        if options.overtones:
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
    
    listener = audio.Listener(window_size=options.window_size,
        interval=options.interval, filters=filters)
    
    queue = listener.start()
    recorded = []
    series = dict((Note.from_frequency(f), []) for f in highlighted)
    plotted_notes = set(series.keys())
    while True:
        try:
            offset, buckets, data = queue.pop()
            
            if options.record:
                recorded.append(buckets)
            
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
                        if options.only_highlighted:
                            continue
                        text = color('black', text)
                    
                    print text,
                print
                
                for unfound in (plotted_notes - found):
                    series[unfound].append(0.0)
            
            if good > 0:
                print
        except KeyboardInterrupt:
            print
            listener.stop()
            
            if plotted_notes and options.plot:
                mathematica_colors = ['Cyan', 'Green',
                    'RGBColor[0.8, 0.8, 0.1]', 'Red', 'Magenta',
                    'Black'][:len(series)]
                plots = []
                for freq in highlighted:
                    note = Note.from_frequency(freq)
                    plots.append('{%s}' %
                        ', '.join('%.02f' % power for power in series[note]))
                print 'ListLinePlot[{%s},\n    PlotStyle -> {%s},\n    ' \
                    'PlotRange -> All, PlotMarkers -> Automatic]' % \
                    (',\n    '.join(plots),
                    ', '.join('%s' % c for c in mathematica_colors))
            
            if options.record:
                while len(recorded) > 0 and len(recorded[0]) == 0:
                    recorded.pop(0)
                
                if recorded:
                    with open(options.record, 'wb') as stream:
                        pickle.dump(recorded, stream, 2)
            
            break
