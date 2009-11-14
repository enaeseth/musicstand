# encoding: utf-8

"""
An intelligent music stand.

(Oh, how I wish that were really true.)
"""

from __future__ import with_statement
from monitor import Monitor
from analyzer import Analyzer
from time import sleep
from matcher import Matcher
from threading import Thread
import re
import signal
import os
import notes

def main(window_size, interval):
    def dummy(results):
        print ', '.join('%s (%.1f)' % (notes.unparse_note(*notes.freq_to_note(f)), f) for f in results)
    
    print "Starting audio analysis (dun dun dun...)"
    matcher = Matcher("sarias.ly", debug=True)
    monitor = Monitor(min(window_size, 1024))
    analyzer = Analyzer(dummy, window_size, interval, 40000000)
    analyzer.start(monitor)
    
    Thread(name='Matcher', target=matcher.run).start()
    
    while True:
        try:
            sleep(1)
        except KeyboardInterrupt:
            print "got interrupt"
            matcher.shutdown()
            analyzer.stop()
            break
    
    print '\nYEEEEEEEEEEAAAAAAAAAAAAHHHHHHHHHHHH!'
    # os.system('open david_caruso_sunglasses.jpg')
    # os.system('open -a "/Applications/QuickTime Player.app" yeaaaaaaaah.mp3')

if __name__ == '__main__':
    main(4096, 1024)
