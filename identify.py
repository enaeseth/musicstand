# encoding: utf-8

"""
Tell me who you are!
"""

from __future__ import with_statement

from mstand import audio
from mstand.capture import Capturer
from mstand.filters import *
from mstand.notes import Note
from mstand.terminal import color

from threading import Thread, Condition
from collections import defaultdict
import cPickle as pickle

# Component states:
HEARD  = intern('heard')   # a component that was just heard
RISING = intern('rising')  # a component whose intensity is rising
FADING = intern('fading')  # a component whose intensity is falling
FADED  = intern('faded')   # a component that is no longer being heard

class Component(object):
    """
    A frequency component that is being tracked.
    """
    
    def __init__(self, note, intensity, state=HEARD, history=4):
        self.note = note
        self.state = state
        self.previous_state = None
        self.intensities = [intensity]
        self.peak = None
        self.last_peak = None
        self.peaked = False
        self.faded_count = 0
        self._history = 4
    
    def update(self, intensity):
        """
        Updates this component with a new intensity.
        """
        
        self.previous_state = self.state
        previous_intensity = self.intensity
        self.peaked = False
        
        if self.peak:
            if intensity / self.peak <= 0.35:
                self.peak = None
        
        if intensity == 0.0:
            self.state = FADED
            self.faded_count += 1
        elif intensity < self.intensity:
            if self.state is RISING or self.state is HEARD:
                if self.peak is None or previous_intensity > self.peak * 1.2:
                    self.last_peak = self.peak
                    self.peak = previous_intensity
                    self.peaked = True
            self.state = FADING
        elif intensity > self.intensity:
            self.state = RISING
            self.faded_count = 0
        
        self.intensities.append(intensity)
        while len(self.intensities) > self._history:
            self.intensities.pop(0)
    
    @property
    def intensity(self):
        return self.intensities[-1]
    
    @property
    def previous_intensity(self):
        try:
            return self.intensities[-2]
        except IndexError:
            return None
    
    @property
    def zombie(self):
        return self.faded_count >= Tracker.MAX_FADED_COUNT
    
    def __nonzero__(self):
        return self.state is not FADED
    
    def __repr__(self):
        return '<%s @ %.1f, %s>' % (self.note, self.intensity, self.state)

class Tracker(object):
    """
    Tracks the frequency components that are being heard.
    """
    
    MAX_FADED_COUNT = 3
    
    def __init__(self, callback):
        self._components = {}
        self._active_notes = set()
        self._callback = callback
    
    def update(self, buckets):
        """
        Update the tracked components' states using the given new FFT
        result buckets.
        
        The buckets should be (note, intensity) pairs.
        """
        
        current_notes = set()
        for note, intensity in buckets:
            current_notes.add(note)
            
            component = self._components.get(note)
            if component is not None:
                component.update(intensity)
            else:
                component = Component(note, intensity)
                self._components[note] = component
        
        for faded_note in (self._active_notes - current_notes):
            component = self._components[faded_note]
            component.update(0.0)
            
            if component.faded_count > self.MAX_FADED_COUNT:
                del self._components[faded_note]
            else:
                current_notes.add(faded_note)
        
        self._callback(self._components)
        self._active_notes = current_notes
    

class Detector(object):
    """
    Examines tracked components and decides what notes are being played.
    """
    
    def __init__(self, callback=None, watched=None):
        self._callback = callback
        self._watched = watched or []
        self._counter = 0
    
    def _get_potential_supporters(self, target, components):
        frequency = target.frequency
        harmonics = [Note.from_frequency(frequency * i)
            for i in [1.0 / n for n in range(2, 5)] + range(2, 5)]
        
        def is_supporter(note):
            if abs(note.semitone - target.semitone) <= 1:
                return False
            
            return note in harmonics
        
        potentials = [c for c in components if is_supporter(c.note)]
        potentials.sort(key=lambda c: c.previous_intensity, reverse=True)
        return potentials
    
    def update(self, components):
        if self._counter is 0:
            print 'Ready.'
        
        components = components.values()
        components.sort(key=lambda component: -component.intensity)
        
        for component in components:
            if component.peaked and component.note in self._watched:
                top_intensity = max(c.previous_intensity for c in components)
                if component.peak / top_intensity >= 0.75:
                    print color('purple!', '%3d: %s peaked at %.1f',
                        self._counter, component.note, component.peak)
                    supporters = self._get_potential_supporters(component.note,
                        components)
                    print '    ' + ', '.join(str(c.note) for c in supporters)
        self._counter += 1

def create_listener(options):
    filters = [
        audio.CutoffFilter(4200.0),
        audio.NegativeFilter(),
        audio.CoalesceFilter(),
        MinimumIntensityFilter(5.0),
        # SmoothFilter(1, 4)
    ]
    
    return audio.Listener(window_size=options.window_size,
        interval=options.interval, filters=filters)

if __name__ == '__main__':
    from optparse import OptionParser
    
    parser = OptionParser('%prog [options] note')
    parser.add_option('-t', '--track', action='store_true',
        help="Don't detect notes, just track components")
    parser.add_option('-r', '--recording', metavar='FILENAME',
        help='Use a recording of FFT results instead of capturing live')
    parser.add_option('-i', '--interval', metavar='SAMPLES', type='int',
        help='FFT interval')
    parser.add_option('-w', '--window-size', metavar='SAMPLES', type='int',
        help='FFT window size')
    parser.set_defaults(interval=1024, window_size=4096, track=False)
    
    options, args = parser.parse_args()
    
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
    
    callback = show_components if options.track else \
        Detector(watched=watched).update
    tracker = Tracker(callback)
    
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
            results = pickle.load(stream)
        
        for buckets in results:
            buckets = [(Note.from_frequency(freq), intensity)
                for freq, intensity in buckets]
            tracker.update(buckets)
    else:
        # capture live
        capturer = Capturer(create_listener(options), tracker.update)
        capturer.run_until_interrupt()

