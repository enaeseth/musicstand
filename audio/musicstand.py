# encoding: utf-8

"""
An intelligent music stand.

(Oh, how I wish that were really true.)
"""
from __future__ import with_statement
from monitor import Monitor
from analyzer import Analyzer
from time import sleep
from Matcher import Matcher
import re
import lilypondParser
import PageOpener
import mutex as mu


def main(window_size, interval):
    #def matcher(results):
        #print results
    
    matcher = Matcher("page1.ly")
    monitor = Monitor(window_size)
    analyzer = Analyzer(matcher.add, window_size, interval)
    
    print "Starting audio analysis (dun dun dun...)"
    matcher.run()
    analyzer.start(monitor)
    
    try:
        while True:
            sleep(10)
    except KeyboardInterrupt:
        pass
    finally:
        analyzer.stop()
    
    print "All done."

if __name__ == '__main__':
    main(1024, 1024)
