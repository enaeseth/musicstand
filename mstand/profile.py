# encoding: utf-8

"""
Reading, writing, and creating instrument profiles.
"""

from __future__ import with_statement
import re
from threading import Thread, Condition
from mstand.notes import *

class Capturer(object):
    """
    Captures the decomposed frequency response pattern of a note.
    
    Create a Capturer by passing it an unstarted Listener object.
    """
    
    def __init__(self, listener):
        self._listener = listener
        self._running = False
        self._capturing = False
        self._forward_target = None
        self._sync = Condition()
        self._thread = None
        self._queue = None
        self._captured = None
        self._silence_count = 0
    
    def start(self):
        """
        Starts the underlying Listener and prepares the capturer to capture.
        """
        
        self._thread = Thread(target=self._run, name='ProfileCapture')
        self._running = True
        
        with self._sync:
            self._thread.start()
            
            # wait for the capture thread to signal its startup
            self._sync.wait()
            
            self._queue = self._listener.start()
            # signal to the capture thread that we have the FFT result queue
            self._sync.notify()
    
    def stop(self):
        """
        Stops the capturer and the underlying Listener.
        """
        
        if not self._running:
            raise RuntimeError('capturer is not running')
        
        self._listener.stop()
        self._running = False
    
    def capture(self):
        """
        Captures a decomposed frequency response.
        
        Waits until some audio samples are heard, then captures the response
        until no samples are heard anymore, and returns the response
        dictionary.
        """
        
        with self._sync:
            if self._capturing:
                raise RuntimeError('no simultaneous capture supported')
            
            self._silence_count = 0
            self._captured = {}
            self._capturing = True
            
            self._sync.wait()
        
        return self._captured
    
    def forward(self, target):
        generator = target()
        generator.next()
        
        with self._sync:
            if self._capturing:
                raise RuntimeError('no simultaneous capture supported')
            
            self._silence_count = None
            self._forward_target = generator
            try:
                while self._forward_target is not None:
                    self._sync.wait(0.2)
            finally:
                self._forward_target = None
    
    def _run(self):
        with self._sync:
            # signal to the main thread that this thread has started
            self._sync.notify()
            
            # wait for the main thread to signal that it has the audio queue
            self._sync.wait()
        
        while self._running:
            try:
                offset, buckets, data = self._queue.pop()
            except KeyboardInterrupt:
                break
            
            if self._forward_target is not None:
                if buckets and self._silence_count is None:
                    self._silence_count = 0
                elif not buckets and self._silence_count is not None:
                    self._silence_count += 1
                    if self._silence_count >= 30:
                        self._forward_target = None
                        with self._sync:
                            self._sync.notify()
                else:
                    self._forward_target.send(buckets)
                
                continue
            
            if not self._capturing:
                continue
            
            if not buckets and self._captured:
                # we're not hearing anything anymore; check end condition
                
                self._silence_count += 1
                if self._silence_count >= 30:
                    # it's all over
                    self._capturing = False
                    with self._sync:
                        self._sync.notify()
            elif buckets:
                for frequency, intensity in buckets:
                    note = freq_to_note(frequency)
                    
                    try:
                        self._captured[note] += 1
                    except KeyError:
                        self._captured[note] = 1

class Profile(object):
    """
    An instrument profile.
    """
    
    def __init__(self, name, mapping=None):
        self.name = name
        self._mapping = mapping or {}
    
    @property
    def mapping(self):
        return self._mapping
    
    def clear(self):
        self._mapping = {}
    
    def forget(self, note):
        return self._mapping.pop(note)
    
    def add(self, note, component_notes):
        try:
            self._mapping[note].append(component_notes)
            self._mapping[note].sort(key=lambda pat: len(pat), reverse=True)
        except KeyError:
            self._mapping[note] = [component_notes]
    
    def __getitem__(self, note):
        return self._mapping[note]
    
    def __setitem__(self, note, component_notes):
        self._mapping[note] = component_notes
    
    def __delitem__(self, note):
        del self._mapping[note]
    
    def __len__(self):
        return len(self._mapping)
    
    def __iter__(self):
        return iter(self._mapping)
    
    def __contains__(self, note):
        return note in self._mapping
    
    def notes(self):
        return sorted(self, key=lambda note: note_to_semitone(*note))
    
    def items(self):
        return self._mapping.iteritems()
    
    def __repr__(self):
        return '%s(%r, %r)' % (type(self).__name__, self.name, self._mapping)

class ProfileReadError(ValueError):
    pass

def read_profile(stream):
    header = stream.readline()
    match = re.match(r'^# Piano Hero Instrument Profile ([\d\.]+)', header)
    if not match:
        raise ProfileReadError('invalid header line %r' % header)
    
    version = match.group(1).split('.')
    if version[0] != '1':
        raise ProfileReadError('incompatible profile version %s' %
            '.'.join(version))
    
    name_line = stream.readline()
    match = re.match(r'^name: (.+)[\r\n]*$', name_line)
    if not match:
        raise ProfileReadError('profile has no valid "name:" line')
    name = match.group(1)
    
    profile = Profile(name)
    for line in stream:
        line = line.strip()
        if not line:
            continue
        
        match = re.match(r'^([A-G][#b]?-?\d+):\s+(.+)$', line)
        if not match:
            raise ProfileReadError('invalid mapping line %r' % line)
        
        note = Note.parse(match.group(1))
        components = set(Note.parse(n)
            for n in re.split(r',\s*', match.group(2)))
        profile.add(note, components)
    
    return profile

def write_profile(profile, stream):
    print >>stream, '# Piano Hero Instrument Profile 1.0'
    print >>stream, 'name: %s' % profile.name
    print >>stream, ''
    
    for note in sorted(profile, key=lambda n: note_to_semitone(*n)):
        for pattern in profile[note]:
            components = ', '.join('%3s' % unparse_note(*c) for c in pattern)
            print >>stream, '%3s:  %s' % (unparse_note(*note), components)
