import matplotlib
matplotlib.use('Agg')
import pylab

from collections import deque

def fft(samples, min_power=0):
    sampFreq = 44100
    spectrogram = pylab.specgram(samples,NFFT=2048*2,hold=True,scale_by_freq=False,Fs=sampFreq)
    powers, freqs, times = spectrogram[:3]
    
    peaks = deque()
    
    #loop for each time interval
    for t in xrange(len(times)):
        best = None
        best_power = 0
        
        #loop over each bin, if the power > the best so far, record it
        for f in xrange(len(freqs)):
            if powers[f][t] > max(best_power, min_power):
                best = f
                best_power = powers[best][t]
                # print best_power
        
        if best is not None:
            peaks.append(freqs[best])
    
    return (sum(peaks) / len(peaks)) if len(peaks) > 0 else None
