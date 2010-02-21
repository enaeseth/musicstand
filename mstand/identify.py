# encoding: utf-8

"""
Note tracking and identification.
"""

from mstand.notes import Note
from mstand.terminal import color

import sys

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
        if not isinstance(note, Note):
            raise TypeError('%r is not a Note' % note)
        
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
        self.notes_since_last_peak = 1
        self.weak_notes_since_last = 0
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
            if self.state is RISING or self.state is HEARD:
                if self.peak is None or previous_intensity > self.peak[1] * .95:
                    self._mark_possible_peak(previous_intensity)
            self.state = FADING
        elif intensity > self.intensity:
            self.state = RISING
            self.faded_count = 0
        
        self.intensities.append(intensity)
        while len(self.intensities) > self._history:
            self.intensities.pop(0)
        
        is_peak = False
        
        if self.possible_peak:
            if self.counter >= self.possible_peak[0] + PEAK_EVIDENCE:
                is_peak = self._check_peak()
                
        if is_peak:
            return
         
        self.notes_since_last_peak += 1
        if self.peak:
            if intensity <= .5*self.peak[1]:
                self.weak_notes_since_last += 1
        
    def _mark_possible_peak(self, intensity):
        index = self.counter - 1
        
        if self.possible_peak:
            count, peak_intensity = self.possible_peak
            if intensity <= peak_intensity:
                return
        
        self.possible_peak = (index, intensity)
    
    def _check_peak(self):
        intensities = self.intensities[-PEAK_EVIDENCE:]
        if max(intensities) <= self.possible_peak[1]:
            self.last_peak = self.peak
            self.peak, self.possible_peak = self.possible_peak, None
            self.peaked = True
            self.weak_notes_since_last = 0
            self.notes_since_last_peak = 1
            return True
        else:
            self.possible_peak = None
            return False
    
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
        return self.faded_count >= ComponentTracker.MAX_FADED_COUNT
    
    def __nonzero__(self):
        return self.state is not FADED
    
    def __repr__(self):
        return '<%s @ %.1f, %s>' % (self.note, self.intensity, self.state)

class ComponentTracker(object):
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

class PeakTracker(object):
    """
    Tracks components that have peaked.
    """
    
    def __init__(self, delegate, delay=2, look_back=2, min_intensity=10.0):
        self._to_check = {}
        self._fade_tracked = {}
        self._delegate = delegate
        self._delay = delay
        self._look_back = look_back
        self._min_intensity = min_intensity
    
    def _find_nearby_peaks(self, target, components):
        position, intensity = target.peak
        minimum = position - self._look_back
        maximum = position + self._delay
        
        peaked_components = []
        
        for component in components.itervalues():
            if not component.peak or component.peak[1] > intensity * 1.05:
                continue
            if minimum <= component.peak[0] <= maximum:
                peaked_components.append((component.note,) + component.peak)
        
        peaked_components.sort(key=lambda c: c[2], reverse=True)
        return peaked_components
    
    def update(self, components):
        for note, component in components.iteritems():
            if component.zombie:
                try:
                    fade_obj = self._fade_tracked[note]
                except KeyError:
                    pass
                else:
                    self._delegate.faded(fade_obj)
                    del self._fade_tracked[note]
            elif component.peaked and component.peak[1] >= self._min_intensity:
                self._to_check[component.note] = (component.counter +
                    self._delay)
        
        for note, counter in self._to_check.items():
            try:
                component = components[note]
            except KeyError:
                continue
            
            if component.counter >= counter:
                del self._to_check[note]
                if component.peak:
                    peaked = self._find_nearby_peaks(component, components)
                    result = self._delegate.peaked(note, peaked)
                    if result is not None:
                        former = self._fade_tracked.get(note)
                        if former is not None and former != result:
                            self._delegate.faded(former)
                        self._fade_tracked[note] = result

class Identifier(object):
    """
    Examines tracked peaks and identifies what notes are being played.
    
    The identifier should be passed as the delegate to PeakTracker's
    initializer.
    """
    
    HEARD = intern('+')
    FADED = intern('-')
    
    def __init__(self, callback, profile, debug=False, debug_peaks=False):
        self._callback = callback
        self._profile = profile
        self._counter = 0
        self._debug = debug
        self._debug_peaks = debug_peaks
    
    def peaked(self, peak_note, peaks):
        peak_map = dict((note, intensity) for note, offset, intensity in peaks)
        
        from pprint import pprint
        if peak_note == Note.parse('C4'):
            pprint(peaks)
        note = self._profile.find_match(peak_note, peak_map)
        if note is not None:
            self._callback(self.HEARD, note)
            return note
    
    def faded(self, note):
        self._callback(self.FADED, note)

class Detector(object):
    """
    Examines tracked components and decides what notes are being played.
    """
    
    def __init__(self, callback, profile, debug=False, debug_peaks=False):
        self._callback = callback
        self._profile = profile
        self._counter = 0
        self._debug = debug
        self._debug_peaks = debug_peaks
    
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
        components = components.values()
        components.sort(key=lambda component: -component.intensity)
        
        for component in components:
            if component.peaked:
                self._analyze_component(component, components)
        self._counter += 1
    
    def _analyze_component(self, peaked_component, all_components):
        try:
            fingerprints = self._profile.peaks[peaked_component.note]
        except KeyError:
            return
            # print 'sorry, got nothing for %s' % str(peaked_component.note)
        
        def get_average_intensity(component, index):
            start = (-index) - 1
            length = 3
            
            intensities = component.intensities[start:start+length]
            try:
                return sum(intensities) / len(intensities)
            except ZeroDivisionError:
                return 0.0
        
        peak = peaked_component.peak
        peak_offset = peaked_component.counter - peak[0]
        
        # print peaked_component.note, peak[1],
        # for component in all_components:
        #     try:
        #         intensity = component.intensities[-peak_offset - 1]
        #         if peak[1] < intensity * 0.8:
        #             print
        #             return
        #     except IndexError:
        #         continue
        # print
        
        # print peaked_component.intensities
        peak_intensity = get_average_intensity(peaked_component, peak_offset)
        
        supporters = {}
        if peak_intensity > 0.0:
            for component in all_components:
                if component == peaked_component:
                    continue
                
                intensity = get_average_intensity(component, peak_offset)
                ratio = intensity / peak_intensity
                
                if ratio > 0.15:
                    supporters[component.note] = ratio
        
        if supporters:
            average = sum(supporters.itervalues()) / len(supporters)
            maximum = max(supporters.itervalues())
        else:
            average = maximum = 0.0
        
        if self._debug_peaks:
            print >>sys.stderr, '%4d:' % peak[0],
            if supporters:
                if average <= 0.5:
                    color_name = 'green!'
                else:
                    color_name = 'blue!'
                average_s = '%.2f' % average
            else:
                color_name = 'yellow!'
                average_s = '----'
            print >>sys.stderr, color(color_name, 'Component %s peaked at '
                '(%.2f => %.2f): %s', peaked_component.note, peak[1],
                peak_intensity, average_s)
            print >>sys.stderr, '    ' + ', '.join('%s: %.2f' % pair
                for pair in sorted(supporters.iteritems(),
                    key=lambda (n, i): i, reverse=True))
        
        if peak_intensity <= 0.0:
            return
        
        best_match = self._profile.find_match(peaked_component.note,
            supporters)
        
        if best_match and average <= 0.8 and maximum <= 2.0:
            if self._debug:
                print >>sys.stderr, '%3d:  Peak of %s @ %s indicates note %s ' \
                    '(distance: %.2f)' % ((peak[0], peaked_component.note,
                    peak_intensity) + best_match)
            
            self._callback(*best_match)
