# encoding: utf-8

"""
Profile musical instruments so that we know WTF is going on because daaaaaaamn.
"""

from __future__ import with_statement
from mstand import audio
from mstand.filters import *
from mstand.interpret import ProfileInterpreter
from mstand.notes import *
from mstand.profile import *
from time import sleep
from threading import Condition
import sys
import os

class ProfileTool(object):
    CUTOFFS = (0.6, 0.25)
    
    def __init__(self, listener):
        self.capturer = Capturer(listener)
        self.capturer.start()
        
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
                self.interpreter = ProfileInterpreter(self.profile)
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
    
    def show(self, *notes):
        if self.profile is None:
            print >>sys.stderr, 'error: no profile is loaded'
            return
        
        def show_patterns(note, patterns, prefix=''):
            for i, pattern in enumerate(patterns):
                if i == 0:
                    print '%s%-3s  -' % (prefix, unparse_note(*note)),
                else:
                    print '%s     -' % prefix,
                
                print ', '.join(unparse_note(*note) for note in
                    sorted(pattern, key=lambda n: note_to_semitone(*n)))
        
        if notes:
            for note in notes:
                try:
                    semitone = int(note)
                except (TypeError, ValueError):
                    note = parse_note(note)
                else:
                    note = semitone_to_note(semitone)[0]
                
                try:
                    patterns = self.profile[note]
                except KeyError:
                    pass
                else:
                    show_patterns(note, patterns)
        else:
            print '%s:' % self.profile.name
            for note in self.profile.notes():
                show_patterns(note, self.profile[note], '  ')
    
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
            readable_note = unparse_note(*semitone_to_note(semitone))
            print 'Play %s.' % readable_note
            
            try:
                captured = self.capturer.capture()
            except KeyboardInterrupt:
                self.capturer.stop()
                print
                print 'Aborted.'
                break
            
            print 'Captured:'
            notes = list(sorted(captured.keys(),
                key=lambda n: note_to_semitone(*n)))
            
            print '  ' + ', '.join('%s: %d' % (unparse_note(*n), captured[n])
                for n in notes)
                
            print 'Profiling %s as:' % readable_note
            max_samples = float(max(captured.values()))
            profiles = []
            for cutoff in self.CUTOFFS:
                profile = set(n for n, samples in captured.iteritems()
                    if samples >= (max_samples * cutoff))
                if len(profile) > 0 and profile not in profiles:
                    profiles.append(profile)
            
            note = get_note(note)
            try:
                self.profile.forget(note)
            except KeyError:
                pass
            
            for profile in profiles:
                notes = sorted(profile, key=lambda n: note_to_semitone(*n))
                print '  - %s' % (', '.join(unparse_note(*n) for n in notes))
                
                self.profile.add(note, profile)
    
    def interpret(self, *options):
        verbose = any(opt in ('-v', '--verbose') for opt in options)
        continuous = any(opt in ('-c', '--continuous') for opt in options)
        was_silence = [False]
        
        if continuous:
            print 'Play some notes. Press ^C to stop interpreting.'
        else:
            print 'Play a note.'
        
        def do_interpretation():
            last_note = None
            
            while True:
                buckets = yield
                
                notes = set(freq_to_note(freq) for freq, intensity in buckets)
                if verbose and len(notes) > 0:
                    print color('black!', ' '.join('%3s' % unparse_note(*note)
                        for note in
                        sorted(notes, key=lambda n: note_to_semitone(*n))))
                new_note = self.interpreter.match(notes)
                
                if last_note is not new_note:
                    if new_note is None:
                        print color('yellow!', '-silence-')
                    else:
                        was_silence[0] = False
                        print color('green!', unparse_note(*new_note))
                    last_note = new_note
        
        while True:
            try:
                self.capturer.forward(do_interpretation)
            except KeyboardInterrupt:
                print
                return
            
            if not continuous:
                break
            if not was_silence[0]:
                was_silence[0] = True
                # print color('yellow!', '-silence-')
    
def get_semitone(note):
    try:
        return int(note)
    except ValueError:
        try:
            return note_to_semitone(*parse_note(note))
        except ValueError:
            raise ValueError('invalid note %r' % note)

def get_note(note):
    if isinstance(note, tuple):
        return note
    elif isinstance(note, basestring):
        return parse_note(note)
    elif isinstance(note, int):
        return semitone_to_note(note)
    else:
        raise TypeError(type(note))

def color(color_spec, text, *args):
    colors = {
        '': '',
        'black': '30',
        'red': '31',
        'green': '32',
        'yellow': '33',
        'blue': '34',
        'purple': '35',
        'cyan': '36',
        'white': '37'
    }

    if color_spec.endswith('!'):
        bold = '1'
        color_spec = color_spec[:-1]
    else:
        bold = '0'

    if args:
        text = text % args

    color = colors[color_spec]
    if color:
        color = ';%s' % color
    return '\x1b[%s%sm%s\x1b[0;00m' % (bold, color, text)

if __name__ == '__main__':
    from optparse import OptionParser
    
    parser = OptionParser('%prog [options] [profile]')
    parser.add_option('-c', '--create', metavar='NAME',
        help='Create a new profile')
    parser.add_option('-i', '--interval', metavar='SAMPLES', type='int',
        help='FFT interval')
    parser.add_option('-w', '--window-size', metavar='SAMPLES', type='int',
        help='FFT window size')
    parser.set_defaults(interval=1024, window_size=4096*4)
    
    options, args = parser.parse_args()
    
    filters = [
        audio.CutoffFilter(4200.0),
        audio.NegativeFilter(),
        audio.CoalesceFilter(),
        MinimumIntensityFilter(20.0),
        SmoothFilter(4, 3)
    ]
    
    listener = audio.Listener(window_size=options.window_size,
        interval=options.interval, filters=filters)
    
    profiler = ProfileTool(listener)
    print 'Welcome to the Piano Hero instrument profiler.'
    
    if len(args) > 0:
        profiler.load(args[0])
    elif options.create:
        profiler.create(options.create)
    
    while True:
        try:
            full_command = raw_input(color('purple!', 'profiler> '))
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
                        for t in xrange(notes[-1] + 1, semitone + 1):
                            notes.append(t)
                    else:
                        notes.append(semitone)
                else:
                    profiler.learn(*notes)
        except (KeyboardInterrupt, EOFError):
            print
            break
        except:
            import traceback
            traceback.print_exc()
            continue
    
    profiler.capturer.stop()
    sys.exit(0)
