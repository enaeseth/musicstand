# encoding: utf-8

"""
I want to be able to identify my notes, so I will take their fingerprints.
"""

from __future__ import with_statement

from mstand import audio
from mstand.capture import Capturer
from mstand.filters import *
from mstand.notes import Note
from mstand.terminal import color

from threading import Thread, Condition
from collections import defaultdict

def create_listener(options):
    filters = [
        audio.CutoffFilter(4200.0),
        audio.NegativeFilter(),
        audio.CoalesceFilter(),
        MinimumIntensityFilter(5.0),
        SmoothFilter(1, 4)
    ]
    
    return audio.Listener(window_size=options.window_size,
        interval=options.interval, filters=filters)

def extract_notes(buckets, notes):
    filtered = defaultdict(float)
    
    for freq, intensity in buckets:
        filtered[Note.from_frequency(freq)] = intensity
        # for note in notes:
        #     if abs(note.frequency - freq) <= 1.0:
        #         filtered[note] = intensity
    
    return filtered

def find_biggest_peak(results):
    maximum = index = peak_note = None
    
    for i, buckets in enumerate(results):
        for note, intensity in buckets.iteritems():
            if intensity > maximum:
                maximum = intensity
                index = i
                peak_note = note
    
    return index, peak_note

def find_note_peaks(results, note):
    peaks = []
    last_intensity = 0.0
    increasing = True
    
    for i, buckets in enumerate(results):
        intensity = buckets[note]
        if intensity > last_intensity:
            increasing = True
        elif intensity < last_intensity and increasing:
            increasing = False
            peaks.append(i - 1)
        last_intensity = intensity
    
    return peaks

def create_fingerprint(capturer, target, harmonics):
    def capture():
        return [extract_notes(buckets, harmonics)
            for buckets in capturer.capture()]
    
    print color('purple!', '--> Play %s quickly (do not hold the note).',
        str(target))
    results = capture()
    
    index, peak_note = find_biggest_peak(results)
    print 'Found peak at result %d.' % index
    
    peak_intensity = results[index][peak_note]
    start = index - 1
    length = 6
    
    parts = results[start:start+length]
    peak_intensity = sum(p[peak_note] for p in parts) / len(parts)
    print color('green!', '  Peak note: %3s; intensity: %.1f', peak_note,
        peak_intensity)
    
    print len(results)
    components = list(sorted(results[index].iteritems(), key=lambda p: p[1],
        reverse=True))
    supporters = []
    for note, intensity in components:
        if note == peak_note:
            continue
        
        start = index - 1
        length = 6
        
        parts = results[start:start+length]
        avg_intensity = sum(p[note] for p in parts) / len(parts)
        ratio = (avg_intensity / peak_intensity)
        if ratio > 0.1:
            # print '    ' + repr([p[note] for p in parts])
            supporters.append((note, avg_intensity, ratio))
    
    supporters.sort(key=lambda s: s[2], reverse=True)
    for note, intensity, ratio in supporters:
        print '  Supporter: %3s; intensity: %.1f (%.0f%%)' % \
            (note, intensity, ratio * 100.0)
    
    return
    print color('purple!', '--> Play %s and hold it.',
        str(target))
    results = capture()
    
    peaks = find_note_peaks(results, peak_note)
    for peak in peaks:
        result = results[peak]
        
        print 'Peak at result %d:' % peak
        print color('green!', '  %3s: %.1f', peak_note, result[peak_note])
        
        for supporter, ratio in supporters:
            actual_ratio = result[supporter] / result[peak_note]
            print '  %3s: %.1f (%.0f%%; expected %.0f%%)' % \
                (supporter, result[supporter], 100 * actual_ratio, 100 * ratio)

if __name__ == '__main__':
    from optparse import OptionParser
    
    parser = OptionParser('%prog [options] note')
    parser.add_option('-n', '--harmonics', metavar='NUMBER', type='int',
        help='the number of harmonics to examine')
    parser.add_option('-p', '--profile', metavar='NAME',
        help='the profile to which this fingerprint will be added')
    parser.add_option('-i', '--interval', metavar='SAMPLES', type='int',
        help='FFT interval')
    parser.add_option('-w', '--window-size', metavar='SAMPLES', type='int',
        help='FFT window size')
    parser.set_defaults(interval=1024, window_size=4096, harmonics=3)
    
    options, args = parser.parse_args()
    
    capturer = Capturer(create_listener(options), notes=False)
    
    try:
        target = Note.parse(args[0])
    except IndexError:
        parser.error('please tell me what note to fingerprint')
    
    harmonics = target.get_harmonics(options.harmonics)
    
    capturer.start()
    try:
        create_fingerprint(capturer, target, harmonics)
    finally:
        capturer.stop()
    
    capturer.stop()
