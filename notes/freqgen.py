# encoding: utf-8

from __future__ import with_statement
import math
import struct
import itertools
from contextlib import closing

def generate_samples(frequency, frame_rate=48000):
    frame_rate = float(frame_rate)
    
    for i in itertools.count():
        yield math.sin(2 * math.pi * frequency * (i / frame_rate))

def combine_samples(sources):
    return (sum(samples) for samples in itertools.izip(*sources))

def scale_samples(samples, amplitude_multiplier=8000):
    return (sample * amplitude_multiplier / 2 for sample in samples)

def play_samples(source, frame_rate=48000):
    import pyaudio
    
    instance = pyaudio.PyAudio()
    stream = instance.open(format=instance.get_format_from_width(2),
        channels=1,
        rate=frame_rate,
        output=True)
    
    for sample in source:
        stream.write(struct.pack('h', sample))

def write_samples(source, output_file, duration=5.0, frame_rate=48000):
    import wave
    
    with closing(wave.open(output_file, 'w')) as out:
        out.setnchannels(1)
        out.setframerate(frame_rate)
        out.setsampwidth(2)
        
        for sample in itertools.islice(source, int(duration * frame_rate)):
            out.writeframes(struct.pack('h', sample))

if __name__ == '__main__':
    import sys
    import notes
    
    def get_frequency(arg):
        try:
            note = notes.parse_note(arg)
            return notes.note_to_freq(*note)
        except ValueError:
            return float(arg)
    
    frequencies = map(get_frequency, sys.argv[1:])
    
    sources = [generate_samples(f) for f in frequencies]
    source = scale_samples(combine_samples(sources), 12000)
    
    write_samples(source, "test.wav")
