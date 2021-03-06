#!/usr/bin/env python
# encoding: utf-8

"""
An intelligent music stand.

(This statement is now much more true than it once was.)
"""

from __future__ import with_statement

from mstand import notes
from mstand import audio
from mstand.app import MusicStand
from mstand.filters import *
from mstand.interpret import ProfileInterpreter, OvertoneInterpreter, CombinedInterpreter
from mstand.match.matcher import Matcher
from mstand.match.algorithm import Algorithm
from mstand.parser import parse_file
from mstand.profile import *
from mstand.display import Display

import re
import os
import sys
import operator
from Tkinter import Tk
from threading import Thread
from time import sleep

def main(algorithm, window_size, interval, interpreter, debug=False):
    filters = [
        audio.CutoffFilter(4200.0),
        audio.NegativeFilter(),
        audio.CoalesceFilter(),
        MinimumIntensityFilter(25.0),
        SmoothFilter(4, 3)
    ]
    
    listener = audio.Listener(window_size=window_size, interval=interval,
        filters=filters)
    
    stand = MusicStand(algorithm, listener, None, interpreter, debug)
    stand.run()

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
        window_size=4096*4)
    
    options, args = parser.parse_args()
    
    # Load the matching algorithm implementation
    try:
        algorithm_class = get_algorithm(options.algorithm)
        algorithm_options = parse_algorithm_options(options.algorithm_options)
        algorithm = algorithm_class(**algorithm_options)
    except ValueError, e:
        parser.error(e[0])
    
    profile = load_profile('piano-averaged')
    if profile.version != '2.0':
        parser.error('the combined interpreter needs a v2.0 profile')
    interpreter = CombinedInterpreter(profile)
    
    # Do some sanity checks
    if not is_power_of_two(options.interval):
        print >>sys.stderr, 'warning: FFT interval should be a power of two'
    if not is_power_of_two(options.window_size):
        print >>sys.stderr, 'warning: FFT window size should be a power of two'
    
    main(algorithm, options.window_size, options.interval, interpreter,
        options.debug)
