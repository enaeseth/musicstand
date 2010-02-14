# encoding: utf-8

"""
Experiments in profiling.
"""

from mstand import audio
from mstand.filters import get_standard_filters
from mstand.notes import *
from mstand.profile import load_profile
from mstand.terminal import color
from threading import Thread, Condition
from collections import defaultdict

class NoteEventEmitter(object):
    """
    Wraps a Listener and emits heard and faded events.
    
    Listeners maintain no state; for any given FFT run, they just pass the
    FFT buckets that resulted from that run. A NoteEventEmitter wraps around
    a listener to add state, so that instead of just producing lists of
    buckets, it tells its client when a note is first heard, and when a note
    fades out.
    """
    
    HEARD = intern('heard')
    FADED = intern('faded')
    
    EVENTS = (HEARD, FADED)
    
    def __init__(self, listener, event_receiver):
        self._receiver = event_receiver
        self._listener = listener
        self._thread = None
        self._running = False
        self._status_condition = None
        
        self._fft_queue = None
        self._active_notes = None
    
    def start(self):
        assert self._thread is None
        assert not self._running
        
        self._thread = Thread(name='NoteEventEmitter', target=self._run)
        self._status_condition = Condition()
        
        with self._status_condition:
            self._running = True
            self._thread.start()
            
            # wait for the thread to actually start up
            self._status_condition.wait()
    
    def stop(self):
        if not self._running:
            return
        
        assert self._status_condition is not None
        
        with self._status_condition:
            self._running = False
            
            # wait for the thread to signal its exit
            self._status_condition.wait()
    
    def _run(self):
        self._active_notes = set()
        self._fft_queue = self._listener.start()
        
        with self._status_condition:
            # tell the thread who started us that we're now running
            self._status_condition.notify()
        
        try:
            self._emit_events()
        finally:
            try:
                self._listener.stop()
                self._fft_queue = None
            finally:
                with self._status_condition:
                    # tell any thread who stopped us that we're shutting down
                    self._status_condition.notifyAll()
    
    def _emit_events(self):
        heard = self.HEARD
        faded = self.FADED
        
        while self._running:
            try:
                offset, buckets, data = self._fft_queue.pop()
            except KeyboardInterrupt:
                break
            
            # sort the buckets in descending order by intensity
            buckets.sort(key=lambda (freq, intensity): intensity, reverse=True)
            
            current = set()
            for freq, intensity in buckets:
                note = Note.from_frequency(freq)
                current.add(note)
                
                if note not in self._active_notes:
                    self._active_notes.add(note)
                    self._emit(heard, note)
            
            # print self._active_notes, current
            absent = self._active_notes - current
            for note in absent:
                self._emit(faded, note)
                self._active_notes.remove(note)
    
    def _emit(self, *args):
        try:
            self._receiver(*args)
        except Exception:
            import traceback
            traceback.print_exc()

class NoteResult(object):
    def __init__(self, notes):
        self.notes = set(notes) if notes else set()
        self.excluded = set()
        self.components = set()
        self.faded_components = set()
    
    def __repr__(self):
        return '<NoteResult {%s}>' % ', '.join(str(note) for note in self.notes)

class Interpreter(object):
    def __init__(self, listener, profile):
        self._listener = listener
        
        self._results = set()
        self._note_to_result = {}
        self._component_to_result = {}
        self._profile = profile
        
        self._component_notes = self._massage_profile(self._profile)
    
    def event(self, what, component):
        changed = False
        
        if what is NoteEventEmitter.HEARD:
            print color('green', component)
            changed = self._heard(component)
        elif what is NoteEventEmitter.FADED:
            print color('red', component)
            changed = self._faded(component)
        else:
            # ??
            assert what in NoteEventEmitter.EVENTS
        
        if changed:
            self._listener(self._results)
    
    def _heard(self, component):
        notes = self._component_notes.get(component)
        if not notes:
            return False
        
        try:
            result = self._component_to_result[component]
        except KeyError:
            pass
        else:
            result.faded_components.remove(component)
            result.components.add(component)
            return False
        
        changed = False
        for note in notes:
            result = self._note_to_result.get(note)
            if result:
                return self._refine_result(result, component)
        
        return self._add_result(component, notes)
    
    def _refine_result(self, result, component):
        result.components.add(component)
        self._component_to_result[component] = result
        
        to_remove = []
                
        for note in result.notes:
            if note not in self._component_notes[component]:
                to_remove.append(note)
        
        if len(result.notes) == 1 and len(to_remove) > 0:
            return False
        
        for note in to_remove:
            result.notes.remove(note)
            result.excluded.add(note)
        
        if len(result.notes) <= 0:
            self._remove_result(result)
        
        return len(to_remove) > 0
    
    def _add_result(self, component, notes):
        result = NoteResult(notes)
        
        result.components.add(component)
        self._component_to_result[component] = result
        for note in notes:
            self._note_to_result[note] = result
        self._results.add(result)
        return True
    
    def _faded(self, component):
        result = self._component_to_result.get(component)
        if not result:
            return False
        
        original_len = len(result.notes)
        result.components.remove(component)
        result.faded_components.add(component)
        
        if len(result.components) <= 0:
            self._remove_result(result)
            return True
        
        return False
    
    def _remove_result(self, result):
        for component in (result.faded_components | result.components):
            del self._component_to_result[component]
        for note in (result.notes | result.excluded):
            del self._note_to_result[note]
        
        self._results.remove(result)
    
    def _massage_profile(self, profile):
        mapping = defaultdict(lambda: set())
        
        for note, patterns in profile.items():
            for pattern in patterns:
                for component in pattern:
                    mapping[component].add(note)
        
        return dict(mapping)

if __name__ == '__main__':
    from optparse import OptionParser
    from Queue import Queue, Empty
    from time import sleep
    
    parser = OptionParser('%prog [options] [profile]')
    parser.add_option('-i', '--interval', metavar='SAMPLES', type='int',
        help='FFT interval')
    parser.add_option('-w', '--window-size', metavar='SAMPLES', type='int',
        help='FFT window size')
    parser.set_defaults(interval=1024, window_size=4096*4)
    
    options, args = parser.parse_args()
    
    listener = audio.Listener(window_size=options.window_size,
        interval=options.interval, filters=get_standard_filters())
    
    def show_results(results):
        def describe(result):
            notes = result.notes
            if len(notes) == 1:
                return color('green', str(list(notes)[0]))
            else:
                return color('yellow', '(%s)' %
                    (' | '.join(map(str, sorted(notes)))))
        
        output = ', '.join(describe(result) for result in results) if results \
            else color('red', '----')
        
        print '    ' + output
        
        if not results:
            print interpreter._note_to_result
            print interpreter._component_to_result
    
    interpreter = Interpreter(show_results, load_profile('playground'))
    
    emitter = NoteEventEmitter(listener, interpreter.event)
    
    emitter.start()
    try:
        while True:
            try:
                sleep(0.2)
            except Empty:
                continue
    except KeyboardInterrupt:
        print
    finally:
        emitter.stop()
