# encoding: utf-8

"""
Profile musical instruments so that we know WTF is going on because daaaaaaamn.
"""

from __future__ import with_statement
from mstand.monitor import Monitor
from mstand.analyzer import Analyzer
from mstand.notes import *
from mstand.profile import *
from time import sleep
from threading import Condition
import sys
import os

class Capturer(object):
    def __init__(self):
        self._capturing = False
        self._waiter = Condition()
        self._target = None
        self._heard_something = False
        self._freqs = self._last_heard = self._silence_count = None
    
    def add(self, freqs):
        if self._capturing:
            if len(freqs) == 0:
                self._silence_count += 1
                if self._silence_count >= 5 and self._heard_something:
                    self._done()
                    return
            else:
                self._heard_something = True
            
            if freqs != self._last_heard:
                self._last_heard = freqs
                self._freqs.append(freqs)
    
    def capture(self, target):
        assert not self._capturing
        
        self._target = target
        
        self._freqs = []
        self._last_matched = None
        self._silence_count = 0
        self._heard_something = False
        
        self._capturing = True
        
        with self._waiter:
            self._waiter.wait()
            self._capturing = False
        
        # strip off leading silence
        while len(self._freqs[0]) == 0:
            self._freqs.pop(0)
        
        # strip off ending silence
        while len(self._freqs[len(self._freqs) - 1]) == 0:
            self._freqs.pop()
        
        return self._freqs
    
    def _done(self):
        self._capturing = False
        with self._waiter:
            self._waiter.notifyAll()

class ProfileTool(object):
    def __init__(self, window_size, interval):
        self.capturer = Capturer()
        self.monitor = Monitor(min(window_size, 1024))
        self.analyzer = Analyzer(self.capturer.add, window_size, interval,
            2000000, self.monitor.sample_rate)
        self.analyzer.start(self.monitor)
        
        self.filename = None
        self.profile = None
    
    def create(self, name):
        self.profile = Profile(name)
        print 'started new profile: %s' % name
        print 'use the "save" command to save it to disk when finished'
    
    def _clean_filename(self, filename):
        base, extension = os.path.splitext(filename)
        if not extension:
            filename += '.phip'
        
        if not filename.startswith('/'):
            filename = os.path.join(os.path.dirname(__file__), 'profiles',
                filename)
        
        return filename
    
    def load(self, filename):
        filename = self._clean_filename(filename)
        with open(filename, 'rt') as f:
            try:
                self.profile = read_profile(f)
            except ProfileReadError, e:
                print >>sys.stderr, 'error: %s' % e
            else:
                self.filename = filename
                print 'Loaded %s.' % filename
    
    def save(self, filename=None):
        if self.profile is None:
            print >>sys.stderr, 'error: no profile is loaded'
            return
        
        if filename is None and self.filename is None:
            print >>sys.stderr, 'please pick a filename to save the profile to'
            return
        elif filename is None:
            filename = self.filename
        else:
            filename = self._clean_filename(filename)
        
        directory = os.path.dirname(filename)
        if not os.path.exists(directory):
            os.makedirs(directory)
        
        with open(filename, 'wt') as f:
            write_profile(self.profile, f)
        
        print 'saved profile to %s' % filename
        self.filename = filename
    
    def _get_semitone(self, note):
        try:
            return int(note)
        except ValueError:
            return note_to_semitone(*parse_note(note))
    
    def show(self, note=None):
        if self.profile is None:
            print >>sys.stderr, 'error: no profile is loaded'
            return
        
        def show_freqs(semitone, frequencies, prefix=''):
            print '%s%d (%s):\t%s' % (prefix, semitone,
                unparse_note(*semitone_to_note(semitone)),
                ', '.join('%.01f' % freq for freq in frequencies))
        
        if note is not None:
            semitone = self._get_semitone(note)
            
            try:
                frequencies = self.profile[semitone]
            except KeyError:
                print >>sys.stderr, 'error: profile %r has no frequencies ' \
                    'recorded at semitone %d' % semitone
            
            show_freqs(semitone, frequencies)
        else:
            print 'profile %s:' % self.profile.name
            for semitone in sorted(self.profile):
                frequencies = self.profile[semitone]
                show_freqs(semitone, frequencies, '  ')
    
    def learn(self, *notes):
        if self.profile is None:
            print >>sys.stderr, 'error: no profile is loaded'
            return
        
        if not notes:
            notes = []
            for i in xrange(-48, 40):
                if i not in self.profile:
                    notes.append(i)
        if not notes:
            print >>sys.stderr, 'error: profile %s already has entries for ' \
                'semitones 1-88'
            return
        
        for note in notes:
            semitone = self._get_semitone(note)
            print 'Play %s.' % (unparse_note(*semitone_to_note(semitone)))
            
            try:
                captured = self.capturer.capture(semitone)
            except KeyboardInterrupt:
                self.capturer._done()
                print
                print 'Aborted.'
                break
            
            print 'Captured:'
            for freq in captured[0]:
                print '  - %s (%.02fHz)' % (unparse_note(*freq_to_note(freq)),
                    freq)
            
            self.profile[semitone] = captured[0]

def get_semitone(note):
    try:
        return int(note)
    except ValueError:
        try:
            return note_to_semitone(*parse_note(note))
        except ValueError:
            raise ValueError('invalid note %r' % note)

if __name__ == '__main__':
    from optparse import OptionParser
    
    parser = OptionParser('%prog [options] [profile]')
    parser.add_option('-i', '--interval', metavar='SAMPLES', type='int',
        help='FFT interval')
    parser.add_option('-w', '--window-size', metavar='SAMPLES', type='int',
        help='FFT window size')
    parser.set_defaults(interval=1024, window_size=4096)
    
    options, args = parser.parse_args()
    
    profiler = ProfileTool(options.window_size, options.interval)
    print 'Welcome to the Piano Hero instrument profiler.'
    
    if len(args) > 0:
        profiler.load(args[0])
    
    while True:
        try:
            full_command = raw_input('profiler> ')
            parts = full_command.split(' ')
            command, arguments = parts[0], parts[1:]
            
            if command in ('exit', 'quit'):
                break
            elif command == 'help':
                print 'sorry'
            elif hasattr(profiler, command):
                getattr(profiler, command)(*arguments)
            else:
                # implicit "learn" command
                notes = []
                is_range = False
                for raw in parts:
                    if raw == '-':
                        is_range = True
                        continue
                    
                    try:
                        semitone = get_semitone(raw)
                    except ValueError, e:
                        if len(notes) == 0:
                            print >>sys.stderr, 'error: unknown command or ' \
                                'invalid note %r' % raw
                        else:
                            print >>sys.stderr, 'error: %s' % e
                        break
                    
                    if is_range:
                        is_range = False
                        for t in xrange(notes[-1], semitone + 1):
                            notes.append(t)
                    else:
                        notes.append(semitone)
                else:
                    profiler.learn(*notes)
        except KeyboardInterrupt:
            print
            break
        except:
            import traceback
            traceback.print_exc()
            continue
    
    profiler.analyzer.stop()
    sys.exit(0)
