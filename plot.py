# encoding: utf-8

"""
Generate a plot of a recording of FFT results.
"""

from __future__ import with_statement
from mstand.notes import Note
from mstand.terminal import color
from collections import defaultdict
import cPickle as pickle
import os.path

def get_colors(n):
    colors = [
        ('cyan!', 'Cyan'),
        ('green!', 'Green'),
        ('yellow!', 'RGBColor[0.8, 0.8, 0.1]'),
        ('red!', 'Red'),
        ('purple!', 'Magenta'),
        ('black!', 'Black')
    ]
    
    return colors[:n]

if __name__ == '__main__':
    from optparse import OptionParser
    
    parser = OptionParser('%prog [options] filename note [note ...]')
    parser.add_option('-t', '--test', action='store_true',
        help='Load the recording from the test recordings folder')
    parser.set_defaults(test=False)
    
    options, args = parser.parse_args()
    
    if len(args) < 1:
        parser.error('need the filename of the recording to plot')
    elif len(args) < 2:
        parser.error('need at least one note to plot')
    
    path = args[0].lower()
    if not path.endswith('.pickle'):
        path += '.pickle'
    
    if options.test:
        base = os.path.dirname(__file__)
        path = os.path.join(base, 'tests', 'identify', 'recordings', path)
    
    try:
        with open(path, 'r') as stream:
            recording = pickle.load(stream)
    except IOError, e:
        if e.errno == 2:
            parser.error('file not found: %s' % path)
        else:
            raise
    
    notes = map(Note.parse, args[1:])
    
    if isinstance(recording, dict) and 'results' in recording:
        results = recording['results']
    else:
        results = recording
    
    plotted_series = defaultdict(list)
    for result in results:
        needed = set(notes)
        for freq, intensity in result:
            note = Note.from_frequency(freq)
            if note in needed:
                needed.remove(note)
                plotted_series[note].append(intensity)
        
        for unfound in needed:
            plotted_series[unfound].append(0.0)
    
    colors = get_colors(len(notes))
    
    for i, color_info in enumerate(colors):
        print color(color_info[0], '%-3s', notes[i]),
    print
    
    plots = []
    for note in notes:
        plots.append('{%s}' %
            ', '.join('%.02f' % power for power in plotted_series[note]))
    print 'ListLinePlot[{%s},\n    PlotStyle -> {%s},\n    ' \
        'PlotRange -> All, PlotMarkers -> Automatic]' % \
        (',\n    '.join(plots),
        ', '.join('%s' % c[1] for c in colors))
