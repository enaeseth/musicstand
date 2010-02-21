# encoding: utf-8

"""
I want to be able to identify my notes, so I will take their fingerprints.
"""

from __future__ import with_statement

from mstand import audio
from mstand.capture import Capturer
from mstand.filters import *
from mstand.notes import Note
from mstand.identify import *
from mstand.profile import *
from mstand.terminal import color

from threading import Thread, Condition
from collections import defaultdict

def create_listener(options):
    filters = [
        audio.CutoffFilter(4200.0),
        audio.NegativeFilter(),
        audio.CoalesceFilter(),
        MinimumIntensityFilter(5.0),
        SmoothFilter(2, 3)
    ]
    
    return audio.Listener(window_size=options.window_size,
        interval=options.interval, filters=filters)

class PeakDelegate(object):
    def __init__(self, target):
        self.best = None
        self.target = target
    
    def peaked(self, peaking_note, peaks):
        if self.target is not None and peaking_note != self.target:
            return
        if self.best is None or peaks[0][2] > self.best[0][2]:
            self.best = peaks
    
    def show(self):
        for note, index, intensity in self.best:
            print '%3s @ %5.2f' % (note, intensity)

def find_peaks(results, target=None):
    delegate = PeakDelegate(target)
    peak_tracker = PeakTracker(delegate)
    component_tracker = ComponentTracker(peak_tracker.update)
    
    for result in results:
        component_tracker.update(result)
    
    if not delegate.best:
        return None
    
    results = {}
    for note, index, intensity in delegate.best:
        results[note] = intensity
    
    return results

def create_vector(keys, peaks):
    return [peaks.get(key, 0.0) for key in keys]

def create_fingerprint(capturer, target, harmonics):
    runs = []
    notes = defaultdict(int)
    
    first_run = True
    while len(runs) < 4:
        color_name = 'purple!' if first_run else 'black!'
        print color(color_name, '--> Play %s quickly (do not hold the note).',
            target)
        first_run = False
        
        results = capturer.capture()
        peaks = find_peaks(results)
        if not peaks:
            continue
        for note, intensity in peaks.iteritems():
            notes[note] += 1
        runs.append(peaks)
    
    combined = {}
    for note, count in notes.iteritems():
        if count >= 3:
            total = 0.0
            for run in runs:
                try:
                    total += run[note]
                except KeyError:
                    continue
            combined[note] = total / count
    
    keys = []
    for note, intensity in sorted(combined.iteritems(), key=lambda (n, i): -i):
        keys.append(note)
        print '%3s @ %5.2f' % (note, intensity)
    note_vector = create_vector(keys, combined)
    
    for i in xrange(2):
        print color('green!', '--> Play %s quickly (do not hold the note).',
            target)
        results = capturer.capture()
        peaks = find_peaks(results, keys[0])
        
        if not peaks:
            print 'no match'
        else:
            print '%.3f' % cosine_distance(note_vector,
                create_vector(keys, peaks))
    
    return keys[0], combined

if __name__ == '__main__':
    from optparse import OptionParser
    import os.path
    
    parser = OptionParser('%prog [options] note')
    parser.add_option('-n', '--harmonics', metavar='NUMBER', type='int',
        help='the number of harmonics to examine')
    parser.add_option('-p', '--profile', metavar='NAME',
        help='the profile to which this fingerprint will be added')
    parser.add_option('-s', '--sure', '--overwrite', dest='sure',
        action='store_true', help="don't confirm saving new fingerprints")
    parser.add_option('-i', '--interval', metavar='SAMPLES', type='int',
        help='FFT interval')
    parser.add_option('-w', '--window-size', metavar='SAMPLES', type='int',
        help='FFT window size')
    parser.set_defaults(interval=1024, window_size=4096, harmonics=0,
        sure=False)
    
    options, args = parser.parse_args()
    
    profile = None
    if options.profile:
        try:
            profile = load_profile(options.profile)
        except IOError, e:
            if e.errno == 2:
                print 'Creating new profile.'
                profile_name = options.profile.capitalize().replace('-', ' ')
                path = os.path.join(get_profile_storage_dir(),
                    '%s.json' % options.profile)
                profile = Profile(profile_name, path=path)
            else:
                raise
        except ProfileReadError, e:
            parser.error('invalid profile: %s' % e)
    
    capturer = Capturer(create_listener(options))
    
    targets = []
    is_range = False
    for arg in args:
        if arg == '-':
            is_range = True
            continue
        
        note = Note.parse(arg)
        if is_range:
            start = targets[-1].semitone + 1
            for i in xrange(start, note.semitone + 1):
                targets.append(Note.from_semitone(i))
        else:
            targets.append(note)
    
    capturer.start()
    try:
        for target in targets:
            if options.harmonics:
                harmonics = target.get_harmonics(options.harmonics)
            else:
                harmonics = None
            
            result = create_fingerprint(capturer, target, harmonics)
            if not result:
                continue
            peak_note, intensity_map = result
            
            if not profile:
                continue
            
            if peak_note in profile.peaks:
                # prepare to overwrite any existing fingerprint
                
                existing = None
                for i, fingerprint in enumerate(profile.peaks[peak_note]):
                    note, existing_supporters = fingerprint
                
                    if note == target:
                        existing = profile.peaks[peak_note].pop(i)
                        break
                
                if existing and not options.sure:
                    answer = raw_input('Do you want to overwrite the existing '
                        'fingerprint? (y/n): ')
                    if not answer.lower().startswith('y'):
                        raise RuntimeError('Aborted.')
            
            if peak_note not in profile.peaks:
                profile.peaks[peak_note] = []
            
            profile.peaks[peak_note].append((target, intensity_map))
    except RuntimeError, e:
        # yeah, this is abuse of exceptions... I don't care
        print e.args[0]
    else:
        if profile:
            profile.save()
    finally:
        capturer.stop()
