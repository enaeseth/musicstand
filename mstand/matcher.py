from __future__ import with_statement

import sys
import re
import notes
from lilypondParser import parseFile as parse_lilypond_file
from pages import open_page
from Queue import Queue, Empty

class Matcher(object):
    # a special value that gets inserted into the note queue upon shutdown;
    # when the matcher loop encounters it, it will exit
    SHUTDOWN_SENTINEL = object()
    
    class Interval(object):
        """A span of time with the notes being played during that span."""
        def __init__(self, start, end, notes=None):
            self.start = start
            self.end = end
            self.notes = notes or []
        
        def __repr__(self):
            return '%s(%r, %r, %r)' % (type(self).__name__, self.start,
                self.end, self.notes)
    
    def __init__(self, filename, min_octave=2, debug=False):
        self.filename = filename
        self.incoming_notes = None # this gets created in .run()
        notes, cache_dir = parse_lilypond_file(filename)
        self.intervals = self.create_intervals(notes)
        self.cache_dir = cache_dir
        self.measure_of_last_displayed_page = None
        
        self.min_octave = min_octave
        self.current_location = None
        self.current_note = None
        self.miss_count = None
        self.debug_enabled = debug
        self.running = False
    
    def add(self, freqs):
        #print 'I AM IN ADD'
        note_list = map(notes.freq_to_note, freqs)
        note = note_list[0] # fuck you, chords
        
        if self.running:
            self.incoming_notes.put(note)
    
    def match(self, new_note):
        """
        Takes the parsed Lilypond array, the current location in the array (as an
        integer), the new note as a tuple inside a list like [(octave,note,accidental)],
        and the current number of misses in a row. 
        
        Returns an updated location and updated number of misses. (If the number of 
        misses isn't currently 0 and the new note looks correct, the number of misses
        goes down by 1.)
        """
        
        def matches(position):
            try:
                letters = [n[1] for n in self.intervals[position].notes]
                self.debug('%s =?= %s', new_note[1], ''.join(letters))
                return new_note[1] in letters
            except IndexError:
                return False
        
        for i in range(1, min(self.miss_count + 1, 3)) + [0]:
            if matches(self.current_location + i):
                if i > 0:
                    self.debug("onward, %d notes" % i)
                    self.current_location += i
                    self.miss_count = max(self.miss_count - i, 0)
        if matches(self.current_location + 1):
            self.debug("MOVING FORWARD LIKE A SCREAMING NARWHAL")
            self.current_location += 1
            self.miss_count = max(self.miss_count - 1, 0)
        elif matches(self.current_location):
            self.miss_count = max(self.miss_count - 1, 0)
        else:
            self.miss_count += 1
        
        print 'miss count is now %d' % self.miss_count
    
    def debug(self, message, *args):
        if self.debug_enabled:
            print >>sys.stderr, message % args
    
    def run(self):
        self.running = True
        self.incoming_notes = Queue(0)
        self.current_location = 0
        self.miss_count = 0
        
        while self.running:
            new_note = self.queue.get()
            if new_note is self.SHUTDOWN_SENTINEL:
                break
            
            if new_note[0] < self.min_octave:
                continue
            
            if new_note != self.current_note:
                # self.debug(notes.unparse_note(*new_note))
                self.current_note = new_note
                
                self.match(new_note)
                
                if self.current_location >= (len(self.intervals) - 1):
                    print "Done with the piece!"
                    self.running = False
                
                # self.debug('Current location in array: %d', self.current_location)
                # self.debug('Current measure: %d', self.lilypond_tuples[self.current_location][0])
                # self.debug('-' * 20)
            
            # if self.miss_count > 2:
            #     # nathan.do_something_useful()
            
            this_measure = int(self.intervals[self.current_location].start)
            if this_measure != self.measure_of_last_displayed_page:
                self.measure_of_last_displayed_page = this_measure
                open_page(self.filename, this_measure, self.cache_dir)
        print "Exiting matcher."
    
    def shutdown(self):
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
        
        intervals = [self.Interval(start, end) for start, end in pair(sorted(times))]
        
        # warning: shit be O(n*k), yo. fix up when we care.
        for note in notes:
            start_time = note[0] + note[1]
            end_time = start_time + (1.0 / note[2])
            
            for interval in intervals:
                if start_time < interval.end and interval.start < end_time:
                    interval.notes.extend(note[3])
        
        return intervals
    
    def __repr__(self):
        return '%s(%r, %r)' % (type(self).__name__, self.filename,
            self.debug_enabled)

if __name__ == '__main__':
    matcher = Matcher("test.ly")
    matcher.run()
