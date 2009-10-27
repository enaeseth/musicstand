import matplotlib
matplotlib.use('Agg')
import pylab

def fft(samples):
	sampFreq = 44100
	spectrogram = pylab.specgram(samples,NFFT=2048*2,hold=True,scale_by_freq=False,Fs=sampFreq)
	powers, freqs, times  = spectrogram[0], spectrogram[1], spectrogram[2]
	
	peaks = [0] * len(times)
	
	#loop for each time interval
	for t in range(len(times)):
		best = None
		#loop over each bin, if the power > the best so far, record it
		for f in range(len(freqs)):
			if best == None or powers[f][t] > powers[best][t]:
				best = f
		peaks[t] = freqs[best]
		
	guess = 0
	for freq in peaks:
		guess += freq
	guess = guess/len(peaks)
	return guess
    
