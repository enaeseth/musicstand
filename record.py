# encoding: utf-8

"""
Records FFT results.
"""

from __future__ import with_statement
from mstand import audio
from mstand.filters import *
import cPickle as pickle
import os

if __name__ == '__main__':
    from optparse import OptionParser
    
    parser = OptionParser('%prog [options] name')
    parser.add_option('-c', '--comment', dest='comment',
        help='A description of the recording')
    parser.add_option('--dirty', '--no-clean', dest='clean',
        action='store_false', help="Don't clean up the recording")
    parser.add_option('-t', '--test', action='store_true',
        help='Place the recording in the test recordings folder')
    parser.add_option('-m', '--min-intensity', type='float',
        help='the value for the minimum intensity filters')
    parser.add_option('-i', '--interval', metavar='SAMPLES', type='int',
        help='FFT interval')
    parser.add_option('-w', '--window-size', metavar='SAMPLES', type='int',
        help='FFT window size')
    parser.set_defaults(clean=True, test=False, min_intensity=2.0,
        interval=1024, window_size=4096)
    
    options, args = parser.parse_args()
    
    if len(args) < 1:
        parser.error('need the name of the file to record to')
    elif len(args) != 1:
        parser.error('invalid arguments')
    
    filters = [
        audio.CutoffFilter(4200.0),
        audio.NegativeFilter(),
        audio.CoalesceFilter(),
        MinimumIntensityFilter(options.min_intensity),
        SmoothFilter(1, 4)
    ]
    
    listener = audio.Listener(window_size=options.window_size,
        interval=options.interval, filters=filters)
    
    results = []
    queue = listener.start()
    while True:
        try:
            offset, buckets, data = queue.pop()
            if len(results) == 0:
                print 'Ready.'
            results.append(buckets)
        except KeyboardInterrupt:
            print
            break
    listener.stop()
    
    def max_intensity(result):
        if len(result) == 0:
            return 0.0
        else:
            return max(intensity for freq, intensity in result)
    
    original_len = len(results)
    if options.clean:
        # cut the fat off of the start of the recording
        while len(results) > 0:
            if max_intensity(results[0]) <= 5.0:
                results.pop(0)
            else:
                break
        
        # cut the fat off of the start of the recording
        while len(results) > 0:
            if max_intensity(results[-1]) <= 2.0:
                results.pop()
            else:
                break
    
    print 'Recorded %d / %d FFT results.' % (len(results), original_len)
    
    if len(results) > 0:
        path = args[0].lower()
        if not path.endswith('.pickle'):
            path += '.pickle'
        
        if options.test:
            base = os.path.dirname(__file__)
            path = os.path.join(base, 'tests', 'identify', 'recordings', path)
        
        parent = os.path.dirname(path)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)
        
        recording = {
            'comment': options.comment,
            'results': results
        }
        
        with open(path, 'wb') as stream:
            pickle.dump(recording, stream, 2)
        print 'Saved recording to %s.' % path
