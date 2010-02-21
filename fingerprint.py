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
from pprint import pprint

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
    def __init__(self, target, harmonics=None):
        self.best = None
        self.target = target
        self.harmonics = harmonics
    
    def peaked(self, peaking_note, peaks):
        if self.target is not None and peaking_note != self.target:
            return
        
        if self.harmonics:
            check_peaks = [peak for peak in peaks if peak[0] in self.harmonics]
            if not peaks:
                return
        else:
            check_peaks = peaks
        
        if self.best is None or check_peaks[0][2] > self.best[0][2]:
            if self.harmonics:
                while len(peaks) > 0 and peaks[0][0] not in self.harmonics:
                    peaks.pop(0)
                if len(peaks) == 0:
                    return
            
            self.best = peaks
    
    def show(self):
        for note, index, intensity in self.best:
            print '%3s @ %5.2f' % (note, intensity)

def find_peaks(results, target=None, harmonics=None, maximum=None):
    delegate = PeakDelegate(target, harmonics)
    peak_tracker = PeakTracker(delegate)
    component_tracker = ComponentTracker(peak_tracker.update)
    
    for result in results:
        component_tracker.update(result)
    
    if not delegate.best:
        return None
    
    best = delegate.best
    if maximum is not None:
        best = best[:maximum]
    
    results = {}
    for note, index, intensity in best:
        results[note] = intensity
    
    return results

def create_vector(keys, peaks):
    return [peaks.get(key, 0.0) for key in keys]

def create_fingerprints(capturer, target, harmonics):
    runs = []
    notes = defaultdict(int)
    
    print 'Fingerprinting %s;' % str(target),
    if harmonics is None:
        print 'not restricting to harmonics.'
    else:
        print 'harmonics: %s' % ', '.join(str(h) for h in harmonics)
    
    def get_common(threshold=3):
        common = set()
        for note, count in notes.iteritems():
            if count >= threshold:
                common.add(note)
        return common
    
    def make_fingerprint(notes, run):
        return dict((note, run.get(note, 0.0)) for note in notes)
    
    def reduce_run(run, max_length=5):
        return dict([(note, power) for note, power in
            sorted(run.iteritems(), key=lambda p: -p[1])][:max_length])
    
    def make_combined(common_notes):
        combined = {}
        for note in common_notes:
            total = 0.0
            count = 0
            for run in runs:
                try:
                    total += run[note]
                    count += 1
                except KeyError:
                    continue
            combined[note] = (total / count)
        return combined
    
    first_run = True
    while (len(runs) < 4 or len(get_common()) < 5) and len(runs) < 7:
        color_name = 'purple!' if first_run else 'black!'
        if len(runs) < 2:
            style = 'quickly (do not hold the note)'
        elif len(runs) < 4:
            style = 'and hold'
        else:
            style = 'however you feel best expresses yourself'
        print color(color_name, '--> Play %s %s.', target, style)
        first_run = False
        
        results = capturer.capture()
        peaks = find_peaks(results, harmonics=harmonics, maximum=6)
        if not peaks:
            continue
        
        for note, intensity in peaks.iteritems():
            notes[note] += 1
        print '{%s}' % (', '.join('%s: %d' % pair
            for pair in sorted(notes.iteritems(), key=lambda p: -p[1])))
        runs.append(peaks)
    
    common_notes = get_common()
    fingerprints = [reduce_run(run) for run in runs]
    fingerprints.append(make_combined(common_notes))
    
    for l in xrange(len(runs), 3, -1):
        very_common_notes = get_common(l)
        if len(very_common_notes) >= 3:
            max_combined = make_combined(very_common_notes)
            if make_combined != fingerprints[-1]:
                fingerprints.append(max_combined)
            break
    
    combined = {}
    strict = {}
    for note, count in notes.iteritems():
        if count >= 3:
            total = 0.0
            strict_total = 0.0
            for i, run in enumerate(runs):
                try:
                    total += run[note]
                    if count >= 4:
                        strict_total += run[note]
                    fingerprints[i][note] = run[note]
                except KeyError:
                    continue
            combined[note] = total / count
        if count >= 4:
            strict[note] = strict_total / count
    
    keys = []
    for fp in (fingerprints + [combined, strict]):
        print '-' * 30
        for note, intensity in sorted(fp.iteritems(), key=lambda (n, i): -i):
            keys.append(note)
            print '%3s @ %5.2f' % (note, intensity)
    note_vector = create_vector(keys, combined)
    
    for i in xrange(2):
        print color('green!', '--> Play %s in some fashion.',
            target)
        results = capturer.capture()
        peaks = find_peaks(results, keys[0])
        
        if not peaks:
            print 'no match'
        else:
            print '%.3f' % cosine_distance(note_vector,
                create_vector(keys, peaks))
    
    return fingerprints + [combined, strict]

def find_note(notes, target):
    for i, (note, components) in enumerate(notes):
        if note == target:
            return i
    return -1

if __name__ == '__main__':
    from optparse import OptionParser
    import os.path
    
    parser = OptionParser('%prog [options] note')
    parser.add_option('-n', '--harmonics', metavar='NUMBER', type='int',
        help='the number of harmonics to examine')
    parser.add_option('-p', '--profile', metavar='NAME',
        help='the profile to which this fingerprint will be added')
    parser.add_option('-r', '--replace', action='store_true',
        help='replace existing fingerprints')
    parser.add_option('-i', '--interval', metavar='SAMPLES', type='int',
        help='FFT interval')
    parser.add_option('-w', '--window-size', metavar='SAMPLES', type='int',
        help='FFT window size')
    parser.set_defaults(interval=1024, window_size=4096, harmonics=0,
        replace=True)
    
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
            
            fingerprints = create_fingerprints(capturer, target, harmonics)
            if not (fingerprints and profile):
                continue
            
            if options.replace:
                for peak_note, notes in profile.peaks.iteritems():
                    while True:
                        index = find_note(notes, target)
                        if index < 0:
                            break
                        del notes[index]
            
            for fingerprint in fingerprints:
                if not fingerprint:
                    continue
                peak_note = max((pair for pair in fingerprint.iteritems()),
                    key=lambda (n, i): i)[0]
                
                if peak_note not in profile.peaks:
                    profile.peaks[peak_note] = []
                
                profile.peaks[peak_note].append((target, fingerprint))
    except RuntimeError, e:
        # yeah, this is abuse of exceptions... I don't care
        print e.args[0]
    else:
        if profile:
            profile.save()
    finally:
        capturer.stop()
