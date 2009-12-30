# encoding: utf-8

"""
Basic facilities for matching.
"""

from __future__ import with_statement

import sys
import re

from Queue import Queue, Empty
from threading import Thread

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

class Matcher(object):
    # a special value that gets inserted into the note queue upon shutdown;
    # when the matcher loop encounters it, it will exit
    SHUTDOWN_SENTINEL = object()
    
    def __init__(self, notes, algorithm, change_listener, debug=False):
        algorithm.assign_matcher(self)
        
        self.algorithm = algorithm
        self.incoming_notes = None # this gets created in .run()
        self.intervals = self.create_intervals(notes)
        self.change_listener = change_listener
        
        self.current_location = None
        self.previous_location = None
        self.miss_count = None
        self.debug_enabled = debug
        self.running = False
        
        algorithm.start_piece()
    
    @property
    def current_interval(self):
        """The interval that was most recently matched"""
        return (self.intervals[self.current_location]
            if self.current_location else None)
    
    @property
    def previous_interval(self):
        """The interval that was matched just before the current one"""
        return (self.intervals[self.previous_location]
            if self.previous_location else None)
    
    def add(self, frequencies):
        """
        Call this method when new frequencies have been heard.
        """
        
        if self.running:
            self.incoming_notes.put(algorithm.filter_frequencies(frequencies))
    
    def debug(self, message, *args):
        if self.debug_enabled:
            print >>sys.stderr, message % args
    
    def start(self, name='Matcher'):
        """
        Starts a new thread for the matcher, and runs it in the thread.
        """
        
        thread = Thread(name=name, target=self.run)
        thread.start()
        return thread
    
    def run(self):
        """
        Runs the matching loop.
        """
        
        self.running = True
        self.incoming_notes = Queue(0)
        self.current_location = 0
        
        while self.running:
            new_notes = self.incoming_notes.get()
            if new_notes is self.SHUTDOWN_SENTINEL:
                # we're being told to stop
                break
            
            location = self.algorithm.match(new_notes)
            if location != self.current_location:
                # we have moved!
                self.previous_location = self.current_location
                self.current_location = location
                
                self.change_listener(self)
    
    def shutdown(self):
        """
        Causes the matcher to exit its loop and return from `run`.
        """
        if not self.running:
            return False
        
        self.incoming_notes.put(self.SHUTDOWN_SENTINEL)
        return True
    
    def create_intervals(self, notes):
        times = set()
        
        for note in notes:
            start_time = note[0] + note[1]
            end_time = start_time + (1.0 / note[2])
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
        
        # warning: shit be O(n*k), yo. fix up when we care.
        for note in notes:
            start_time = note[0] + note[1]
            end_time = start_time + (1.0 / note[2])
            
            for interval in intervals:
                if start_time < interval.end and interval.start < end_time:
                    interval.notes.extend(note[3])
        
        return intervals
    
    def __repr__(self):
        return '<%s using %s>' % (type(self).__name__,
            type(self.algorithm).__name__)
