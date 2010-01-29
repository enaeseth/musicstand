#!/usr/bin/env python
# encoding: utf-8

"""
An intelligent music stand.

(Oh, how I wish that were really true.)
"""

from __future__ import with_statement

from mstand.monitor import Monitor
from mstand.analyzer import Analyzer
from mstand.lilypondParser import parse_file as parse_lilypond_file
from mstand import notes
from mstand.pages import open_page
from mstand.match.matcher import Matcher
from mstand.match.algorithm import Algorithm

import re
import os
import sys
from time import sleep

def main(filename, algorithm, window_size, interval, debug=False):
    notes, cache_dir = parse_lilypond_file(filename)
    
    def position_changed(matcher):
        current_measure = matcher.current_interval.measure
        measure_changed = (matcher.previous_interval is None or
            matcher.previous_interval.measure != current_measure)
        
        # if measure_changed:
            # open_page(filename, current_measure, cache_dir)
        if matcher.current_location >= (len(matcher.intervals) - 1):
            print 'Done with the piece!'
            matcher.shutdown()
    
    print "Starting audio analysis (dun dun dun...)"
    matcher = Matcher(notes, algorithm, position_changed, debug)
    monitor = Monitor(min(window_size, 1024))
    analyzer = Analyzer(matcher.add, window_size, interval, 40000000,
        monitor.sample_rate)
    analyzer.start(monitor)
    
    matcher.start()
    
    while matcher.running:
        try:
            sleep(1)
        except KeyboardInterrupt:
            print "got interrupt"
            break
    
    matcher.shutdown()
    analyzer.stop()
    print '\nYEEEEEEEEEEAAAAAAAAAAAAHHHHHHHHHHHH!'
    os.system('killall Preview')

def get_algorithm(name):
    full_name = 'mstand.match.%s' % name
    try:
        module = __import__(full_name, globals(), locals(), name)
        for name in dir(module):
            member = getattr(module, name)
            try:
                if member is not Algorithm and issubclass(member, Algorithm):
                    return member
            except TypeError:
                pass
        raise ValueError('module %s contains no Algorithm '
            'subclasses' % full_name)
    except ImportError:
        raise ValueError('unknown matching algorithm %r' % name)

def parse_algorithm_options(raw_list):
    options = {}
    if raw_list is None:
        return options
    
    def parse_value(value):
        if value in ('true', 'True', 'yes', 'on'):
            return True
        elif value in ('false', 'False', 'no', 'off'):
            return False
        
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value
    
    for option in raw_list:
        try:
            name, value = option.split('=', 1)
        except ValueError:
            name = option
            value = True
        else:
            value = parse_value(value)
        options[name.replace('-', '_')] = value
    
    return options

def is_power_of_two(n):
    return (n & (n - 1)) == 0 # http://bit.ly/7iErcm

if __name__ == '__main__':
    from optparse import OptionParser
    
    parser = OptionParser('%prog [options] filename.ly')
    parser.add_option('-a', '-m', '--algorithm', metavar='NAME',
        help='the name of the matching algorithm to use')
    parser.add_option('-o', dest='algorithm_options', action='append',
        metavar='OPTION[=VALUE]', help='set an algorithm option')
    parser.add_option('-d', '--debug', action='store_true',
        help='show debugging output')
    parser.add_option('-i', '--interval', metavar='SAMPLES', type='int',
        help='FFT interval')
    parser.add_option('-w', '--window-size', metavar='SAMPLES', type='int',
        help='FFT window size')
    parser.set_defaults(algorithm='simple', debug=False, interval=1024,
        window_size=4096)
    
    options, args = parser.parse_args()
    if len(args) < 1:
        parser.error('which LilyPond file should I open?')
    elif not os.path.exists(args[0]):
        parser.error('file %r does not exist' % args[0])
    
    # Load the matching algorithm implementation
    try:
        algorithm_class = get_algorithm(options.algorithm)
        algorithm_options = parse_algorithm_options(options.algorithm_options)
        algorithm = algorithm_class(**algorithm_options)
    except ValueError, e:
        parser.error(e[0])
    
    # Do some sanity checks
    if not is_power_of_two(options.interval):
        print >>sys.stderr, 'warning: FFT interval should be a power of two'
    if not is_power_of_two(options.window_size):
        print >>sys.stderr, 'warning: FFT window size should be a power of two'
    
    main(args[0], algorithm, options.window_size, options.interval,
        options.debug)
