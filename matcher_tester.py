#!/usr/bin/env python
# encoding: utf-8

from __future__ import with_statement
from mstand.notes import *
from mstand.newParser import parse_file
from mstand.match.matcher import Matcher
from mstand.match.algorithm import Algorithm
from time import sleep
import re

def read_note_file(filename):
    instructions = []
    
    def parse_line_notes(line):
        parts = re.split(r'\*,\s*|\s+', line)
        return [note_to_freq(*parse_note(part)) for part in parts]
    
    with open(filename, 'rt') as f:
        for line in f:
            line = line.strip()
            if line.lower().startswith('pause'):
                match = re.search(r'(\d+(?:\.\d+))$', line)
                if match is None:
                    raise ValueError(line)
                instructions.append(('pause', float(match.group(1))))
            else:
                instructions.append(('play', parse_line_notes(line)))
    
    return instructions

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

if __name__ == '__main__':
    from optparse import OptionParser
    
    parser = OptionParser('%prog [options] test.txt score.ly')
    parser.add_option('-a', '-m', '--algorithm', metavar='NAME',
        help='the name of the matching algorithm to use')
    parser.add_option('-o', dest='algorithm_options', action='append',
        metavar='OPTION[=VALUE]', help='set an algorithm option')
    parser.add_option('-d', '--debug', action='store_true',
        help='show debugging output')
    parser.set_defaults(algorithm='simple', debug=False)
    
    options, args = parser.parse_args()
    
    instructions = read_note_file(args[0])
    
    if not args[1].endswith('.ly'):
        parser.error('looks like you did that backwards')
    notes = parse_file(args[1])
    
    # Load the matching algorithm implementation
    try:
        algorithm_class = get_algorithm(options.algorithm)
        algorithm_options = parse_algorithm_options(options.algorithm_options)
        algorithm = algorithm_class(**algorithm_options)
    except ValueError, e:
        parser.error(e[0])
    
    def position_changed(matcher):
        interval = matcher.current_interval
        if interval is None:
            print '<-- Matching started.'
        else:
            print '<-- Moved to %.3f (%s).' % (interval.start,
            ', '.join(unparse_note(*n) for n in interval.notes))
    
    matcher = Matcher(notes, algorithm, position_changed, options.debug)
    matcher.start()
    try:
        for action, arg in instructions:
            if action == 'pause':
                print '--> Playing silence for %.2f seconds.' % arg
                matcher.add([])
                sleep(arg)
            elif action == 'play':
                print '--> Played', \
                    ', '.join(unparse_note(*freq_to_note(f)) for f in arg)
                matcher.add(arg)
                sleep(0.5)
            else:
                raise ValueError(action)
    finally:
        matcher.shutdown()
        while matcher.running:
            sleep(0.2)
