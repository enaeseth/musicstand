# encoding: utf-8

import audio
import time
import math
from mstand.notes import *
import operator

class MinimumIntensityFilter(object):
    def __init__(self, threshold):
        self.threshold = threshold
    
    def __call__(self, samples):
        return [(f, i) for (f, i) in samples if i >= self.threshold]

class SmoothFilter(object):
    def __init__(self, memory):
        self.memory = memory
        self._history = []
    
    def __call__(self, buckets):
        self._history.append(set(f for f, i in buckets))
        
        if len(self._history) < self.memory:
            return []
        
        self._history.pop(0)
        
        common_freqs = reduce(operator.and_, self._history)
        return [(f, i) for (f, i) in buckets if f in common_freqs]

class SineFilter(object):
    def __call__(self, buckets):
        return [(f, i) for (f, i) in buckets if i/(90*math.sin(f/(60*math.pi) + (3*math.pi)/2)+100) >= 1]
        
class LogFilter(object):
    def __call__(self, buckets):
        return [(f, i) for (f, i) in buckets if i/(math.log(f+1, 1.1) + 1) >= 1]
        
class SquareRootFilter(object):
    def __call__(self, buckets):
        return [(f, i) for (f, i) in buckets if i/((f/100)**2) >= 1]
        
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
    import sys
    # input_devices = [d for d in audio.get_devices() if d.input_channels > 0]
    
    filters = [
        audio.CutoffFilter(4200.0),
        audio.NegativeFilter(),
        audio.CoalesceFilter(),
        # SineFilter(),
        # LogFilter(),
        # SquareRootFilter(),
        MinimumIntensityFilter(10.0),
        SmoothFilter(4)
    ]
    
    colors = ['blue!', 'green!', 'yellow!', 'red!', 'purple!', 'black!']
    
    try:
        expected = note_to_freq(*parse_note(sys.argv[1]))
        highlighted = [expected * (i + 1.0) for i in xrange(len(colors))]
        
        for color_name, h_freq in zip(colors, highlighted):
            print color(color_name,
                '%3s ' % unparse_note(*freq_to_note(h_freq))),
        print
    except IndexError:
        expected = ot_1 = ot_2 = ot_3 = 0.0
    
    listener = audio.Listener(window_size=4096*4, interval=1024,
        filters=filters)
    
    queue = listener.start()
    while True:
        try:
            offset, buckets, data = queue.pop()
            good = 0
            notes = []
            for freq, intensity in buckets:
                notes.append((freq, unparse_note(*freq_to_note(freq)), intensity))
                # if freq == 0.0:
                #     continue
                # good += 1
                # bar = '=' * int(200 * (intensity / 700.0))
                # print "%6.01f %3s:   %6.02f %s" % (freq,
                #     unparse_note(*freq_to_note(freq)), intensity, bar)
            
            notes.sort(key=lambda p: p[2], reverse=True)
            if len(notes) > 0:
                for freq, note, power in notes:
                    text = '%3s: %6.02f' % (note, power)
                    
                    for color_name, h_freq in zip(colors, highlighted):
                        if abs(h_freq - freq) < 2.0:
                            text = color(color_name, text)
                            break
                    
                    print text,
                print
            
            if good > 0:
                print
        except KeyboardInterrupt:
            print
            listener.stop()
            break
