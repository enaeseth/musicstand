# encoding: utf-8

"""
Tell me who you are!

I am the goddamn Batman.
"""

from __future__ import with_statement

from mstand import audio
from mstand.capture import Capturer
from mstand.filters import *
from mstand.identify import *
from mstand.notes import Note
from mstand.profile import *
from mstand.terminal import color

from threading import Thread, Condition
from collections import defaultdict
import cPickle as pickle

def create_listener(options):
    filters = [
        audio.CutoffFilter(4200.0),
        audio.NegativeFilter(),
        audio.CoalesceFilter(),
        MinimumIntensityFilter(10.0),
        SmoothFilter(1, 4)
    ]
    
    return audio.Listener(window_size=options.window_size,
        interval=options.interval, filters=filters)

if __name__ == '__main__':
    from optparse import OptionParser
    
    parser = OptionParser('%prog [-p profile | -t] [options] note')
    parser.add_option('-p', '--profile',
        help='The profile to use for note identification')
    parser.add_option('-t', '--track', action='store_true',
        help="Don't detect notes, just track components")
    parser.add_option('-d', '--debug', action='store_true',
        help="Debug note identification")
    parser.add_option('--peaks', action='store_true',
        help='Debug peak detection')
    parser.add_option('-r', '--recording', metavar='FILENAME',
        help='Use a recording of FFT results instead of capturing live')
    parser.add_option('-i', '--interval', metavar='SAMPLES', type='int',
        help='FFT interval')
    parser.add_option('-w', '--window-size', metavar='SAMPLES', type='int',
        help='FFT window size')
    parser.set_defaults(interval=1024, window_size=4096, track=False,
        debug=False, peaks=False, profile='piano')
    
    options, args = parser.parse_args()
    
    profile = None
    if options.profile:
        try:
            profile = load_profile(options.profile)
        except Exception, e:
            parser.error('error reading profile: %s' % e)
    
    watched = [Note.parse(arg) for arg in args]
    
    def show_components(components):
        watched_components = [components.get(note) for note in watched]
        
        def describe(component):
            if component is None:
                return ' ' * 14
            
            desc = '%-14s' % ('%5.1f, %s' % (component.intensity,
                component.state))
            if component.state is FADING and component.previous_state is RISING:
                return color('purple!', desc)
            elif component.state is RISING:
                return color('green', desc)
            elif component.state is FADING:
                return color('red', desc)
            else:
                return desc
        
        if len(filter(None, watched_components)) > 0:
            print ' '.join(describe(c) for c in watched_components)
    
    def print_match(note, distance):
        print color('red!', 'Found %s (distance: %.3f)' % (note, distance))
    
    def print_result(action, note, score=None):
        color_name = 'green!' if action == '+' else 'red!'
        if score:
            print color(color_name, '%3s (%.3f)', note, score)
        else:
            print color(color_name, '%3s', note)
    
    if options.track:
        # just track the frequency components visually; do not ID notes
        callback = show_components
    else:
        # full monty: identify the notes being played
        detector = Identifier(print_result, profile, debug=options.debug,
            debug_peaks=options.peaks)
        peak_tracker = PeakTracker(detector)
        callback = peak_tracker.update
    
    tracker = ComponentTracker(callback)
    
    if options.track:
        # print note headings
        for note in watched:
            print color('black!', '%-3s%s', note, ' ' * 11),
        print
        for note in watched:
            print color('black!', '=' * 14),
        print
    
    if options.recording:
        # read the FFT results from a file created by audio/test.py
        with open(options.recording, 'rb') as stream:
            recording = pickle.load(stream)
        
        if isinstance(recording, dict) and 'results' in recording:
            results = recording['results']
        else:
            results = recording
        
        for buckets in results:
            buckets = [(Note.from_frequency(freq), intensity)
                for freq, intensity in buckets]
            tracker.update(buckets)
    else:
        # capture live
        capturer = Capturer(create_listener(options), tracker.update)
        capturer.run_until_interrupt()
