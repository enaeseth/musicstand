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
import re
import signal

def main(window_size, interval):
    print "Starting audio analysis (dun dun dun...)"
    matcher = Matcher("page1.ly", debug=True)
    monitor = Monitor(window_size)
    analyzer = Analyzer(matcher.add, window_size, interval, 10000000)
    analyzer.start(monitor)
    
    def interrupt_handler(signum, frame):
        # This function will be called when ^C is pressed.
        matcher.shutdown()
        analyzer.stop()
    
    signal.signal(signal.SIGINT, interrupt_handler)
    
    matcher.run()
    analyzer.stop()
    
    print '\nYEEEEEEEEEEAAAAAAAAAAAAHHHHHHHHHHHH!'

if __name__ == '__main__':
    main(1024, 1024)
