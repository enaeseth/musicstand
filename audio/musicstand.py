# encoding: utf-8

"""
An intelligent music stand.

(Oh, how I wish that were really true.)
"""

from monitor import Monitor
from analyzer import Analyzer
from time import sleep

def main(window_size, interval):
    def matcher(results):
        print results
    
    monitor = Monitor(window_size)
    analyzer = Analyzer(matcher, window_size, interval)
    
    print "Starting audio analysis (dun dun dun...)"
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
