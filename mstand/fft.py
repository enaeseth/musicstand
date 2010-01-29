import matplotlib
matplotlib.use('Agg')
import pylab
import notes
import sys

from collections import deque

def fft(samples, min_power=0, inclusion=0.05, sample_rate=44100):
    spectrogram = pylab.specgram(samples, NFFT=2048*4, hold=True,
        scale_by_freq=False, Fs=sample_rate)
    powers, freqs, times = spectrogram[:3]
    
    accepted_frequencies = {}
    greatest_power = 0
    last_freq = None
    last_bucket = 0
    last_power = 0
    increasing = True
    sufficient = 0
    
    debug = []
    
    for i, frequency in enumerate(freqs):
        peak_power = 0
        
        # try:
        #     print '%.02d:\t%s' % (frequency, notes.unparse_note(*notes.freq_to_note(frequency)))
        # except OverflowError:
        #     print '%.02d:\t----' % frequency
        
        for power in powers[i]:
            if power > max(peak_power, min_power):
                peak_power = power
                greatest_power = max(greatest_power, power)

        if peak_power > 0:
            debug.append((frequency, power))
            sufficient += 1
            # print "%.02f (%s) => %.02f" % (frequency, notes.unparse_note(*notes.freq_to_note(frequency)), peak_power)
            # print "%.02f (%s)\t=> %d" % (frequency, notes.unparse_note(*notes.freq_to_note(frequency)), int(peak_power)),
            
            if increasing and peak_power < last_power:
                increasing = False
                accepted_frequencies[last_freq] = last_power
                # print "%.01f (%r) =>\t%d" % (last_freq, notes.freq_to_semitone(last_freq)[0], int(last_power))
                # print 'V'
            elif not increasing and peak_power > last_power:
                increasing = True
                # print '^'
            else:
                # print
                pass
            
            last_power = peak_power
            last_freq = frequency
            last_bucket = i
    
    if sufficient > 0:
        cap = 100000000.0
        for freq, power in debug:
            percent = min(power, cap) / cap
            fill = '=' * int(200 * percent)
            print '%.02f (%s)\t=>  % .10d %s' % (freq,
                notes.unparse_note(*notes.freq_to_note(freq)),
                power, fill)
        print
    
    if sufficient == 1:
        accepted_frequencies[last_freq] = last_power
    
    cutoff = greatest_power * inclusion
    frequencies = [freq for freq, power in
        sorted(accepted_frequencies.iteritems(), key=lambda (f, p): -p)
        if power >= cutoff]
    
    # if len(frequencies) > 0:
        # print [notes.unparse_note(*notes.freq_to_note(f)) for f in frequencies]
    
    return frequencies
