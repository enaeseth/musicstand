# encoding: utf-8

"""
Facilities for testing the note identification systems.
"""

from __future__ import with_statement
from threading import Thread, Lock, Condition
from warnings import warn
import cPickle as pickle
import os.path
import sys
import re

from identify import Tracker, Detector
from mstand.notes import Note

try:
    import simplejson as json
except ImportError:
    import json

_tests = {}
_run_mutex = Lock()
_current_run = None
_player = None
_profile = None

# ============================================================
# The public API that tests use:

def test(name, handle=None):
    """
    A decorator that defines a function as a test.
    
    Example usage:
    
        @test('C4')
        def test_c4():
            play('c4')    # plays the recording "c4.pickle"
            expect('C4')  # expects to hear a C4
        
        @test('Imperial March opening')
        def test_march_opening():
            play('march')
            expect('G4')
            expect('G4')
            expect('G4')
            # ...
    """
    
    def make_into_test(implementation):
        if handle is None:
            real_handle = re.sub(r'^test_?', '', implementation.__name__)
        else:
            real_handle = handle
        
        real_handle = '%s.%s' % (implementation.__module__, real_handle)
        
        _tests[real_handle] = Test(real_handle, name, implementation)
        return implementation
    
    return make_into_test

def play(recording):
    """
    Play a recording into the test.
    """
    
    path = os.path.join(get_recording_dir(), recording.lower() + '.pickle')
    try:
        with open(path, 'r') as stream:
            recording = pickle.load(stream)
        
            if isinstance(recording, dict) and 'results' in recording:
                recording = recording['results']
    except IOError, e:
        if e.errno == 2:
            raise MissingRecordingError(recording)
        else:
            raise # reraise the IOError
    
    _current_run.play(recording)

def expect(*notes):
    """
    Expect one or more notes to be heard.
    """
    
    notes = [Note.parse(note) for note in notes]
    _current_run.expect(notes)

# ============================================================
# The internal tools used by the test running code:

def get_tests():
    return _tests

def set_test_profile(profile):
    global _profile
    _profile = profile

def get_recording_dir():
    root = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(root, 'tests', 'identify', 'recordings')

def run_test(test):
    global _current_run
    
    if not isinstance(test, Test):
        raise TypeError('%r is not a Test' % test)
    
    with _run_mutex: # this lock isn't really necessary, but I am paranoid
        assert _current_run is None
        
        _current_run = TestRun(test)
        error = False
        try:
            test()
        except:
            error = True
            raise
        finally:
            _current_run.test_done()
            if not error:
                _current_run.wait_for_finish()
            _current_run = None

class Test(object):
    """
    A note identification test.
    """
    
    def __init__(self, handle, name, implementation):
        self.handle = handle
        self.name = name
        self.implementation = implementation
    
    def __call__(self, *args, **kwargs):
        return self.implementation(*args, **kwargs)
    
    def __repr__(self):
        return '%s(%r, %r, %r)' % (type(self).__name__, self.handle, self.name,
            self.implementation)

class UnheardNoteError(AssertionError):
    """
    The error that is raised when expected note(s) are not heard.
    """
    
    def __init__(self, notes, test, expectation):
        message = ', '.join(str(note) for note in notes)
        super(UnheardNoteError, self).__init__(message)
        self.notes = notes
        self.test = test
        self.expectation = expectation

class MissingRecordingError(Exception):
    """
    The error that is raised when a recording is missing.
    """
    
    def __init__(self, recording):
        super(MissingRecordingError, self).__init__(recording)

class ExtraNoteWarning(Warning):
    """
    The warning that is raised when unexpected note(s) are heard in a test.
    """
    
    def __init__(self, notes, test, expectation):
        message = ', '.join(str(note) for note in notes)
        super(ExtraNoteWarning, self).__init__(message)
        self.notes = notes
        self.test = test
        self.expectation = expectation

class TestRun(object):
    """
    Stores the state of a particular run through a test.
    """
    
    def __init__(self, test):
        self.test = test
        self.detected_notes = []
        self._ready = Condition()
        self._processed = Condition()
        self._finished = False
        self._test_done = False
        self._expectations = 0
        self._checking_expectation = False
        
        assert _profile is not None, 'no instrument profile loaded'
        
        self._detector = Detector(self.detected, _profile)
        self._tracker = Tracker(self._detector.update)
    
    def detected(self, note, distance):
        """
        Called by the test machinery when a note is detected and identified.
        """
        
        with self._ready:
            self.detected_notes.append(note)
            
            # tell the test thread that we have a new note
            self._ready.notifyAll()
        
        with self._processed:
            if self._checking_expectation:
                self._processed.wait()
            else:
                while not self._test_done and not self._finished:
                    # wait for the test thread to process the note
                    self._processed.wait(0.1)
    
    def finished(self):
        """
        Called by the test machinery when sample playback is finished.
        
        At this point, all the notes that were going to be detected will
        have already been detected.
        """
        
        with self._ready:
            self._finished = True
            self._ready.notifyAll()
    
    def wait_for_finish(self):
        with self._ready:
            while not self._finished:
                self._ready.wait()
            if self.detected_notes:
                # there are some notes that we detected but did not expect;
                # warn about these extra notes
                warn(ExtraNoteWarning(self.detected_notes, self.test,
                    self._expectations + 1))
            return
    
    def test_done(self):
        with self._processed:
            self._test_done = True
            self._processed.notifyAll()
    
    def play(self, recording):
        global _player
        
        if _player is None:
            _player = Player()
        
        _player.play(recording, self._tracker.update, self.finished)
    
    def expect(self, notes):
        """
        Called by a test when one or more notes is expected.
        """
        
        expected_notes = set(notes)
        
        # figure out which call to expect() this is (within the current test)
        self._expectations += 1
        index = self._expectations
        
        self._checking_expectation = True
        with self._ready:
            first_run = True
            
            while first_run or not self._finished: # poor man's do...while
                # find the expected notes (if any) which have now been
                # detected
                for expected in list(expected_notes):
                    for i, detected in enumerate(self.detected_notes):
                        if expected == detected:
                            # whoo! clear the note from the expected set and
                            # the detected list
                            expected_notes.remove(expected)
                            self.detected_notes.pop(i)
                
                if not expected_notes:
                    # we've found all the notes we were expecting here!
                    self._checking_expectation = False
                    break
                
                # tell the playback thread that we've processed a note
                with self._processed:
                    self._processed.notify()
                
                # wait for more
                first_run = False
                self._ready.wait()
        
        # tell the playback thread that we've finished processing notes
        with self._processed:
            self._processed.notify()
        
        if self.detected_notes:
            # there are some notes that we detected but did not expect;
            # warn about these extra notes
            warn(ExtraNoteWarning(self.detected_notes, self.test, index))
            
            self.detected_notes = []
        
        if expected_notes:
            # there are some notes that we expected but did not hear;
            # sound the alarm
            raise UnheardNoteError(expected_notes, self.test, index)
        
        # everything went according to plan; return normally

class Player(object):
    """
    Plays back recorded FFT results on a dedicated thread.
    """
    
    def __init__(self):
        self._recording = None
        self._receiver = None
        self._on_finish = None
        self._available = Condition()
        
        self._thread = Thread(name='Player', target=self._run)
        
        # A daemon thread will automatically be terminated when all
        # non-daemon threads exit; this frees us from having to shut down the
        # Player manually.
        self._thread.setDaemon(True)
        
        self._thread.start()
    
    def play(self, recording, receiver, finish_callback):
        from time import sleep
        
        i = 0
        while self._recording is not None and i <= 5:
            sleep(0.1)
            i += 1
        assert self._recording is None
        
        with self._available:
            self._recording = recording
            self._receiver = receiver
            self._on_finish = finish_callback
            self._available.notify()
    
    def _run(self):
        import traceback
        while True:
            with self._available:
                while not self._recording:
                    self._available.wait()
            
            try:
                for result in self._recording:
                    self._receiver([(Note.from_frequency(freq), intensity)
                        for freq, intensity in result])
            except Exception:
                traceback.print_exc()
            
            self._on_finish()
            self._recording = None
            self._on_finish = None
