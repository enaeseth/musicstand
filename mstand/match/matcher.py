# encoding: utf-8

"""
Basic facilities for matching.
"""

from __future__ import with_statement

from mstand.match.algorithm import Algorithm
from mstand.notes import Note

from threading import Thread, Condition
from Queue import Queue, Empty
from collections import deque
from time import sleep
import sys
import re

class Interval(object):
    """
    Represents a span of time in a piece of music.
    """
    
    def __init__(self, start, end, notes=None):
        self.start = start
        self.end = end
        self.notes = notes or []
    
    @property
    def measure(self):
        """The measure number that this interval starts in"""
        return int(self.start)
    
    def __repr__(self):
        return '%s(%r, %r, %r)' % (type(self).__name__, self.start,
            self.end, self.notes)

class HistoryQueue(object):
    """
    A queue of note history.
    """
    
    def __init__(self, memory=1):
        self._queue = deque()
        self._memory = 1
    
    def __getitem__(self, index):
        return self._queue[index]
    
    @property
    def memory(self):
        return self._memory
    
    def keep(self, memory):
        self._memory = max(self._memory, memory)
        return self._memory
    
    def put(self, item):
        self._queue.append(item)
        while len(self._queue) > self._memory:
            self._queue.popleft()

class MatcherStateError(RuntimeError):
    pass

class Matcher(object):
    """
    Provides basic facilities for matching.
    
    Matcher objects perform the basic bookkeeping tasks for matching: they
    maintain a queue of incoming notes, a history of recently-heard notes,
    convert the notes received from LilyPond into a list of intervals, and
    keep track of the current position within the piece.
    
    The task of figuring out new positions in response to notes being heard
    is deferred to Algorithm objects. An Algorithm is passed to the Matcher
    in its constructor.
    """
    
    # commands that can be inserted into the incoming note queue to influence
    # the matching loop
    _STOP_PIECE = intern('stop piece')
    _SHUTDOWN = intern('shutdown')
    
    def __init__(self, algorithm, interpreter, change_listener, debug=False,
                 progress_listener=None):
        if not isinstance(algorithm, Algorithm):
            raise TypeError('%r is not a matching algorithm object' %
                algorithm)
        
        self.current_location = None
        self.previous_location = None
        self._debug_enabled = debug
        self._running = False
        self._within_piece = False
        self._startup_condition = Condition()
        self._piece_control = Condition()
        
        self._playing_piece = False
        self._history = HistoryQueue()
        self.intervals = None
        self._incoming_notes = None
        
        self.interpreter = interpreter
        self.change_listener = change_listener
        self.progress_listener = progress_listener
        
        algorithm.assign_matcher(self)
        self._algorithm = algorithm
        
        self._thread = None
        self._stopping = False
    
    # ================================================================
    # State access and note management
    
    @property
    def current_interval(self):
        """
        The interval that was most recently matched.
        """
        if self.intervals is None:
            return None
        
        if self.current_location is not None and self.current_location >= 0:
            return self.intervals[self.current_location]
        else:
            return None
    
    @property
    def previous_interval(self):
        """
        The interval that was matched just before the current one.
        """
        if self.intervals is None:
            return None
        
        return (self.intervals[self.previous_location]
            if self.previous_location is not None else None)
    
    @property
    def history(self):
        """
        The history of heard notes that the matcher maintains.
        """
        return self._history
    
    def keep_history(self, length):
        """
        Requests the matcher to keep a running history of heard notes with
        at least the given length.
        """
        return self._history.keep(length)
    
    def add(self, notes):
        """
        Call this method when new notes have been heard.
        """
        
        if self._running and self._within_piece:
            self._incoming_notes.put(self._algorithm.filter_notes(notes))
    
    # ================================================================
    # Control methods
    
    def start(self, thread_name='Matcher'):
        """
        Starts the matcher on a dedicated thread.
        
        Blocks until the matcher starts. When this method returns, it will
        be safe to call `load_piece` on the matcher.
        """
        
        with self._startup_condition:
            if self._running:
                raise MatcherStateError('this matcher is already running')
            if self._thread is not None:
                raise MatcherStateError('this matcher already has a thread')
            
            self._thread = Thread(target=self._run, name=thread_name)
            
            self._thread.start()
            self._startup_condition.wait()
        
        assert self._running
    
    def shutdown(self):
        """
        Causes the matcher to shut down.
        
        If this matcher has had a thread started for it by calling `start`,
        this method will wait for that thread to exit before returning.
        """
        
        if not self._running:
            return
        
        self.debug('Matcher is shutting down.')
        self.stop_piece(_shutdown=True)
        
        with self._piece_control:
            self._running = False
            
            # unblock the _run loop, which may be waiting to be notified of
            # a new piece
            self._piece_control.notifyAll()
        
        if self._thread is not None:
            self._thread.join()
            self._thread = None
    
    def load_piece(self, notes):
        """
        Loads a new musical score into the matcher.
        
        The matcher must be running for this to work.
        """
        
        if not self._running:
            raise MatcherStateError('cannot load piece; matcher not running')
        
        self.stop_piece()
        
        with self._piece_control:
            self.intervals = self.create_intervals(notes)
            self.current_location = -1
            self.change_listener(self)
            
            self._piece_control.notify()
    
    def restart_piece(self):
        """
        Restarts the currently loaded musical piece.
        """
        
        if not self._running:
            raise MatcherStateError('cannot restart piece; '
                'matcher not running')
        elif self.intervals is None:
            raise MatcherStateError('no piece is currently loaded; cannot '
                'restart it')
        
        intervals = self.intervals
        self.stop_piece()
        
        with self._piece_control:
            self.intervals = intervals
            self.current_location = -1
            self.change_listener(self)
            
            self._piece_control.notify()
    
    def stop_piece(self, _shutdown=False):
        """
        Stop matching the current piece.
        """
        
        if not self._running:
            raise MatcherStateError('cannot stop piece; '
                'matcher not running')
        if not self._within_piece:
            return
        
        with self._piece_control:
            # tell the matching loop to back off
            message = self._STOP_PIECE if not _shutdown else self._SHUTDOWN
            self._incoming_notes.put(message)
            while self._within_piece:
                self._piece_control.wait()
        
        assert not self._within_piece
    
    # ================================================================
    # Matching loops
    
    def _run(self):
        """
        Runs the matcher. Waits for a piece to be loaded, and then matches
        that piece.
        """
        
        self._within_piece = False
        self._running = True
        
        # signal startup
        with self._startup_condition:
            self._startup_condition.notifyAll()
        
        while self._running:
            # wait for a piece to be loaded
            with self._piece_control:
                while self.intervals is None:
                    self._piece_control.wait()
                    
                    # check to see if we have been shut down
                    if not self._running:
                        return
            
            self._incoming_notes = Queue(0)
            
            # we have a piece! tell the algorithm about it
            self._algorithm.starting_piece(self.intervals)
            
            # perform the matching: this will run until the piece finishes
            # or is stopped
            try:
                self._match()
            finally:
                self._within_piece = False
                # notify anybody interested that the piece has finished
                # (this will unblock stop_piece, for example)
                with self._piece_control:
                    self.intervals = None
                    self._current_location = None
                    self.change_listener(self)
                
                    self._piece_control.notifyAll()
    
    def _match(self):
        """
        Matches the currently-loaded piece.
        """
        
        assert self.intervals is not None
        
        self._within_piece = True
        
        previous_notes = None
        while self._within_piece and self._running:
            new_notes = self._incoming_notes.get()
            
            if new_notes is self._STOP_PIECE:
                # the piece is being stopped
                self._within_piece = False
                break
            elif new_notes is self._SHUTDOWN:
                # the matcher is shutting down
                self._within_piece = self._running = False
                break
            elif new_notes == previous_notes:
                if self.progress_listener is not None:
                    self.progress_listener(new_notes, self.current_location)
                continue
            previous_notes = new_notes
            
            self._history.put(new_notes)
            
            location = self._algorithm.match(new_notes)
            
            if self.progress_listener is not None:
                self.progress_listener(new_notes, location)
            
            if location != self.current_location:
                # we have moved!
                self.previous_location = self.current_location
                self.current_location = location
                
                self.change_listener(self)
            
            if self.current_location >= (len(self.intervals) - 1):
                # done with the piece!
                self._within_piece = False
    
    # ================================================================
    # Utility methods
    
    def debug(self, message, *args):
        """
        Print a debugging message (if such messages are enabled.)
        """
        if self._debug_enabled:
            print >>sys.stderr, message % args
    
    def create_intervals(self, notes):
        """
        Converts the list of LilyPond notes to an ordered list of intervals.
        """
        
        times = set()
        
        for note in notes:
            if note[1] >= 1.0:
                raise ValueError('interval %r starts %.0f%% of the way '
                    'through measure %d' % (note, note[1] * 100, note[0]))
            start_time = (note[0] - 1) + note[1]
            end_time = start_time + note[2]
            times.add(start_time)
            times.add(end_time)
        
        def pair(sequence):
            last = None
            
            for item in sequence:
                if last is not None:
                    yield (last, item)
                last = item
        
        intervals = [Interval(start, end)
            for start, end in pair(sorted(times))]
        
        # warning: shit be O(n*k), yo.
        for note in notes:
            start_time = (note[0] - 1) + note[1]
            end_time = start_time + note[2]
            
            for interval in intervals:
                if start_time < interval.end and interval.start < end_time:
                    interval.notes.extend(note[3])
        
        return intervals
    
    def insert_rests_between_identical_intervals(self, intervals):
        # return intervals
        
        i = 0
        
        while i < len(intervals):
            current = intervals[i]
            try:
                upcoming = intervals[i + 1]
            except IndexError:
                break
            
            if current.notes == upcoming.notes:
                time = upcoming.start
                intervals.insert(i + 1, Interval(time, time))
            
            i += 1
        
        return intervals
    
    def __repr__(self):
        return '<%s using %s>' % (type(self).__name__,
            type(self._algorithm).__name__)
