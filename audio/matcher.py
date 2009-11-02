from __future__ import with_statement

import sys
import re
import notes
from lilypondParser import parseFile as parse_lilypond
from pages import open_page
from collections import deque
from threading import Condition

class Matcher(object):
    def __init__(self, filename, min_octave=2, debug=False):
        self.filename = filename
        self.incoming_notes = deque()
        self.note_available = Condition()
        self.lilypond_tuples = parse_lilypond(filename)
        
        self.min_octave = min_octave
        self.current_location = None
        self.current_note = None
        self.miss_count = None
        self.debug_enabled = debug
        self.running = False
    
    def add(self, freq):
        #print 'I AM IN ADD'
        note = notes.freq_to_note(freq) # fo' realz.
        
        if self.running:
            self.incoming_notes.append(note)
            with self.note_available:
                self.note_available.notify()
    
    def match(self, new_note):
        """
        Takes the parsed Lilypond array, the current location in the array (as an
        integer), the new note as a tuple inside a list like [(octave,note,accidental)],
        and the current number of misses in a row. 
        
        Returns an updated location and updated number of misses. (If the number of 
        misses isn't currently 0 and the new note looks correct, the number of misses
        goes down by 1.)
        """
        
        if new_note == self.lilypond_tuples[self.current_location][3]:
            self.miss_count = max(self.miss_count - 1, 0)
        elif new_note == self.lilypond_tuples[self.current_location+1][3]:
            self.current_location += 1
            self.miss_count = max(self.miss_count - 1, 0)
        else:
            self.miss_count += 1
    
    def debug(self, message, *args):
        if self.debug_enabled:
            print >>sys.stderr, message % args
    
    def run(self):
        self.running = True
        self.incoming_notes.clear()
        self.current_location = 0
        self.miss_count = 0
        
        def get_next_note():
            try:
                return self.incoming_notes.popleft()
            except IndexError:
                # no notes are available; wait until we're told that one is ready
                with self.note_available:
                    self.note_available.wait()
                
                return get_next_note() if self.running else None
        
        while self.running:
            new_note = get_next_note()
            if new_note is None:
                break
            
            if new_note[0] < self.min_octave:
                continue
            
            if new_note != self.current_note:
                self.debug('New note: %s', notes.unparse_note(*new_note))
                self.current_note = new_note
                
                self.match(new_note)
                self.debug('Current location in array: %d', self.current_location)
                self.debug('Current measure: %d', self.lilypond_tuples[self.current_location][0])
                self.debug('-' * 20)
            
            # if self.miss_count > 2:
            #     # nathan.do_something_useful()
            
            # open_page(self.lilypond_tuples[self.current_location][0])
    
    def shutdown(self):
        if not self.running:
            return False
        
        self.running = False
        with self.note_available:
            self.note_available.notify() # wake up our thread if it's waiting for this
        return True
    
    def __repr__(self):
        return '%s(%r, %r)' % (type(self).__name__, self.filename,
            self.debug_enabled)

if __name__ == '__main__':
    matcher = Matcher("test.ly")
    matcher.run()
