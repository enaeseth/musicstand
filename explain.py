# encoding: utf-8

from mstand.monitor import Monitor
from mstand.analyzer import Analyzer
from mstand.notes import *


if __name__ == '__main__':
    from optparse import OptionParser
    
    parser = OptionParser('%prog [options] [profile]')
    parser.add_option('-i', '--interval', metavar='SAMPLES', type='int',
        help='FFT interval')
    parser.add_option('-m', '--min-power', metavar='INTENSITY', type='int',
        help='minimum power')
    parser.add_option('-w', '--window-size', metavar='SAMPLES', type='int',
        help='FFT window size')
    parser.set_defaults(interval=1024, window_size=4096, min_power=40000000)
    
    options, args = parser.parse_args()
    
    samples = []
    capturing = False
    
    def add(freqs):
        if capturing:
            if len(samples) == 0:
                samples.append([freqs, 1])
            else:
                prev = samples[-1][0]
                if freqs == prev:
                    samples[-1][1] += 1
                else:
                    samples.append([freqs, 1])
    
    monitor = Monitor(min(options.window_size, 1024))
    analyzer = Analyzer(add, options.window_size, options.interval,
        options.min_power, monitor.sample_rate)
    analyzer.start(monitor)
    
    try:
        capturing = True
        print 'Listening. Press Return to stop.',
        raw_input()
        capturing = False
    except KeyboardInterrupt:
        capturing = False
        pass
    
    analyzer.stop()
    
    if samples:
        # strip off leading silence
        while len(samples[0][0]) == 0:
            samples.pop(0)

        # strip off ending silence
        while len(samples[len(samples) - 1][0]) == 0:
            samples.pop()
    
    if samples:
        for freqs, count in samples:
            if not freqs:
                print '- (x%d) silence' % count
                continue
            print '- (x%d) %s' % (count, ', '.join('%s (%.01fHz)' %
                (unparse_note(*freq_to_note(freq)), freq) for freq in freqs))
