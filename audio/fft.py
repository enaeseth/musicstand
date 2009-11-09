import matplotlib
matplotlib.use('Agg')
import pylab

from collections import deque

def fft(samples, min_power=0, inclusion=0.05, sample_rate=44100):
    spectrogram = pylab.specgram(samples, NFFT=2048*2, hold=True,
        scale_by_freq=False, Fs=sample_rate)
    powers, freqs, times = spectrogram[:3]
    
    accepted_frequencies = {}
    greatest_power = 0
    last_freq = None
    last_power = 0
    increasing = True
    for i, frequency in enumerate(freqs):
        peak_power = 0
        
        for power in powers[i]:
            if power > max(peak_power, min_power):
                peak_power = power
                greatest_power = max(greatest_power, power)

        if peak_power > 0:
            # print "%.02f => %d" % (frequency, int(peak_power)),
            
            if increasing and peak_power < last_power:
                increasing = False
                accepted_frequencies[last_freq] = last_power
                # print 'V'
            elif not increasing and peak_power > last_power:
                increasing = True
                # print '^'
            else:
                # print
                pass
            
            last_power = peak_power
            last_freq = frequency
    
    cutoff = greatest_power * inclusion
    return [freq for freq, power in
        sorted(accepted_frequencies.iteritems(), key=lambda (f, p): -p)
        if power >= cutoff]
