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

# Before declaring a rising->fading transition a peak, a component must go
# `PEAK_EVIDENCE` FFT runs without reaching an intensity greater than that of
# the sample before the transition.
PEAK_EVIDENCE = 4

# When looking for "supporting" components, average their intensities over
# the previous `SUPPORTER_HISTORY` runs.
SUPPORTER_HISTORY = 5

class Component(object):
    """
    A frequency component that is being tracked.
    """
    
    def __init__(self, note, intensity, counter, state=HEARD, history=6):
        self.note = note
        self.state = state
        self.previous_state = None
        self.intensities = [intensity]
        self.possible_peak = None
        self.peak = None
        self.last_peak = None
        self.peaked = False
        self.faded_count = 0
        self._history = history
        self.counter = counter
        
        assert history >= PEAK_EVIDENCE
    
    def update(self, intensity):
        """
        Updates this component with a new intensity.
        """
        
        self.counter += 1
        self.previous_state = self.state
        previous_intensity = self.intensity
        self.peaked = False
        
        # if self.peak:
        #     if intensity / self.peak[1] <= 0.35:
        #         self.peak = None
        
        if intensity == 0.0:
            self.state = FADED
            self.faded_count += 1
        elif intensity < self.intensity:
            if self.state is RISING:
                if self.peak is None or previous_intensity > self.peak[1] * 1.2:
                    self._mark_possible_peak(previous_intensity)
            self.state = FADING
        elif intensity > self.intensity:
            self.state = RISING
            self.faded_count = 0
        
        self.intensities.append(intensity)
        while len(self.intensities) > self._history:
            self.intensities.pop(0)
        
        if self.possible_peak:
            if self.counter >= self.possible_peak[0] + PEAK_EVIDENCE:
                self._check_peak()
    
    def _mark_possible_peak(self, intensity):
        if self.possible_peak:
            count, peak_intensity = self.possible_peak
            if intensity <= peak_intensity:
                return
        
        self.possible_peak = (self.counter, intensity)
    
    def _check_peak(self):
        intensities = self.intensities[-PEAK_EVIDENCE:]
        if max(intensities) <= self.possible_peak[1]:
            self.last_peak = self.peak
            self.peak, self.possible_peak = self.possible_peak, None
            self.peaked = True
        else:
            self.possible_peak = None
    
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
        self._counter = 0
    
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
                component = Component(note, intensity, self._counter)
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
        self._counter += 1
    

class Detector(object):
    """
    Examines tracked components and decides what notes are being played.
    """
    
    _profile = {
        Note.parse('C4'): [
            (Note.parse('C3'), {Note.parse('C#4'): 0.83, Note.parse('G4'): 0.39, Note.parse('A#3'): 0.38, Note.parse('D4'): 0.29,
                    Note.parse('E5'): 0.28, Note.parse('C#3'): 0.27, Note.parse('A3'): 0.27})
        ],
        Note.parse('D4'): [
            (Note.parse('D4'), {Note.parse('D5'): 0.95, Note.parse('D#4'): 0.92, Note.parse('C4'): 0.34, Note.parse('E4'): 0.31,
                    Note.parse('D#5'): 0.30, Note.parse('C#5'): 0.30, Note.parse('C#4'): 0.28})
        ],
        Note.parse('A4'): [
            (Note.parse('D3'), {Note.parse('A#4'): 0.43, Note.parse('G#4'): 0.34, Note.parse('D#3'): 0.27, Note.parse('D4'): 0.27,
                    Note.parse('D3'): 0.24})
        ],
        Note.parse('C5'): [
            (Note.parse('C4'), {Note.parse('C#4'): 0.61, Note.parse('C4'): 0.44, Note.parse('C#5'): 0.40, Note.parse('B4'): 0.39,
                    Note.parse('D4'): 0.22, Note.parse('B3'): 0.20, Note.parse('A#4'): 0.19}),
            (Note.parse('C5'), {Note.parse('C#5'): 0.39, Note.parse('B4'): 0.38, Note.parse('A#4'): 0.17, Note.parse('D5'): 0.15})
        ],
    }
    
    def __init__(self, callback):
        self._callback = callback
        
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
            if component.peaked:
                self._analyze_component(component, components)
        self._counter += 1
    
    def _analyze_component(self, peaked_component, all_components):
        try:
            fingerprints = self._profile[peaked_component.note]
        except KeyError:
            return
            # print 'sorry, got nothing for %s' % str(peaked_component.note)
        
        def get_average_intensity(component, index):
            start = index - 1
            length = 6
            
            intensities = component.intensities[start:start+length]
            try:
                return sum(intensities) / len(intensities)
            except ZeroDivisionError:
                return 0.0
        
        def get_distance(fingerprint, supporters):
            distance = 0.0
            for component, intensity in fingerprint.iteritems():
                actual_intensity = supporters.get(component, 0.0)
                distance += (actual_intensity - intensity) ** 2
            return distance / len(fingerprint)
        
        peak = peaked_component.peak
        peak_offset = peaked_component.counter - peak[0]
        peak_intensity = get_average_intensity(peaked_component, peak_offset)
        if peak_intensity <= 0.0:
            return
        
        supporters = {}
        for component in all_components:
            if component == peaked_component:
                continue
            
            intensity = get_average_intensity(component, peak_offset)
            ratio = intensity / peak_intensity
            
            if ratio > 0.08:
                supporters[component.note] = ratio
        
        best_match = min(((note, get_distance(fingerprint, supporters))
            for note, fingerprint in fingerprints), key=lambda (n, d): d)
        
        if best_match[1] <= 0.2:
            print 'Peak of %s gave note %s (distance: %.2f)' % \
                (peaked_component.note, best_match[0], best_match[1])
            print '    ' + ', '.join('%s: %.2f' % pair for pair in sorted(supporters.iteritems(),
                key=lambda (n, i): i, reverse=True))
        
        # self._callback(*best_match)

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
    
    def print_match(note, distance):
        print 'Found %s (distance: %.2f)' % (note, distance)
    
    callback = show_components if options.track else \
        Detector(print_match).update
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

