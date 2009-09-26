import pylab
from scikits import audiolab
import pyaudio
import pylab 
import wave
import sys
import chunk

filename = '840orig60to72.wav'
size = 1024

(sound, sampFreq, nBits) = audiolab.wavread(filename)
left, right = sound[:,0], sound[:,1]

spectrogram = pylab.specgram(left,NFFT=1024,hold=True)
powers, freqs, times  = spectrogram[0], spectrogram[1], spectrogram[2]
peaks = [0] * len(times)
for t in range(len(times)):
    best = None
    for f in range(len(freqs)):
        if best == None or powers[f][t] > powers[best][t]:
            best = f
    peaks[t] = freqs[best]

wf = wave.open(filename, 'rb')
p = pyaudio.PyAudio()

# open stream
stream = p.open(format =
                p.get_format_from_width(wf.getsampwidth()),
                channels = wf.getnchannels(),
                rate = wf.getframerate(),
                output = True)

## read data
#data = wf.readframes(size)
#
## play stream
#while data != '':
#    stream.write(data)
#    data = wf.readframes(size)

stream.close()
p.terminate()
pylab.plot(times,peaks,linewidth=4,color='k')
ax = pylab.axes()
ax.set_ylim([0,0.1])
print peaks
pylab.xlabel("Time")
pylab.ylabel("Frequency")
pylab.savefig("spectrogram.png")
