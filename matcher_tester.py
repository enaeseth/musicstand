#!/usr/bin/env python
# encoding: utf-8

from __future__ import with_statement
from mstand.interpreter import Interpreter
from mstand.notes import *
from mstand.newParser import parse_file
from mstand.match.matcher import Matcher, Interval
from mstand.match.algorithm import Algorithm
from mstand.terminal import color
from Queue import Queue
from time import sleep
import re

def read_note_file(filename):
    instructions = []
    
    def parse_line_notes(line):
        parts = re.split(r'\*,\s*|\s+', line)
        return [note_to_freq(*parse_note(part)) for part in parts]
    
    def is_silence(line):
        text = line.lower()
        return text.startswith('pause') or text.startswith('silence')
    
    with open(filename, 'rt') as f:
        expected_position = -1
        for line in f:
            line = line.strip()
            
            if line.endswith('+'):
                expected_position += 1
            elif line.endswith('.'):
                # stay put
                pass
            elif line.endswith('?'):
                expected_position = None
            else:
                parts = re.split(r'\s*([-=]>|➔|➞|➝)\s*', line)
                if len(parts) > 1:
                    expected_position = int(parts[2])
                    line = parts[0]
                else:
                    # default to increasing the position
                    expected_position += 1
            
            if is_silence(line):
                command = ('pause', None, expected_position)
            else:
                command = ('play', parse_line_notes(line), expected_position)
            
            instructions.append(command)
    
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

class Tester(object):
    SHUTDOWN_SENTINEL = object()
    
    def __init__(self, notes, instructions, algorithm, debug=False):
        self.matcher = Matcher(notes, algorithm, None, Interpreter(),
            self.position_changed, progress_listener=self.matched,
            debug=options.debug)
        self.instructions = instructions
        
        self._position_queue = Queue()
    
    def position_changed(self, matcher):
        pass
    
    def matched(self, notes, position):
        sleep(0.25)
        self._position_queue.put(position)
    
    def test(self):
        self.matcher.start()
        
        try:
            self._run()
        finally:
            self.matcher.shutdown()
            while self.matcher.running:
                sleep(0.2)
    
    def _describe_interval(self, i):
        if i >= 0:
            interval = self.matcher.intervals[i]
        else:
            # i = -1, which isn't a real interval
            # synthesize one here for display purposes
            interval = Interval(-1.0, 0.0, [])
        
        note_string = ', '.join(unparse_note(*note) for note in interval.notes)
        
        return '%d (%.3f:%.3f%s)' % (i, interval.start, interval.end,
            ('; ' + note_string if note_string else ''))
    
    def _run(self):
        last_pos = -1
        last_expected_pos = -1
        for action, arg, expected_pos in self.instructions:
            if action == 'pause':
                print '--> Playing silence.'
                self.matcher.add([])
            elif action == 'play':
                print '--> Playing %s.' % \
                    ', '.join(unparse_note(*freq_to_note(f)) for f in arg)
                self.matcher.add(arg)
            else:
                raise ValueError(action)
            
            # wait for the matcher to call our matched() method, and for
            # matched() to send us the matcher's new position through the queue
            new_pos = self._position_queue.get()
            
            if new_pos == last_pos:
                message = 'Stayed at'
            else:
                message = 'Moved to'
            
            # assess what happened:
            stop = False
            if expected_pos is None:
                # we didn't care where we went (instruction ended with ?)
                text_color = 'yellow'
            elif new_pos != expected_pos:
                # we didn't go where we expected
                text_color = 'red'
                stop = True
                verb = 'move to' if expected_pos != last_pos else 'stay at'
                expectation_string = '; expected to %s %s' % \
                    (verb, self._describe_interval(expected_pos))
            else:
                # we went where we expected
                text_color = 'green'
                expectation_string = ''
            
            # display what happened
            
            if new_pos == last_pos:
                message = 'Stayed at'
            else:
                message = 'Moved to'
            
            print color(text_color, '<-- %s %s%s.', message,
                self._describe_interval(new_pos), expectation_string)
            
            if stop:
                break
            
            # if we didn't care where we went on this step (i.e., the line for
            # this instruction ended with '?'), save our new position as the
            # last-expected position; otherwise, save the actual last-expected
            # position
            last_expected_pos = expected_pos if expected_pos is not None \
                else new_pos
            last_pos = new_pos
            sleep(0.5)

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
    
    try:
        # read the instruction file
        instructions = read_note_file(args[0])
        
        # read the LilyPond score
        if not args[1].endswith('.ly'):
            parser.error('looks like you did that backwards')
        notes = parse_file(args[1])
    except IndexError:
        parser.error('missing an argument')
    
    # Load the matching algorithm implementation
    try:
        algorithm_class = get_algorithm(options.algorithm)
        algorithm_options = parse_algorithm_options(options.algorithm_options)
        algorithm = algorithm_class(**algorithm_options)
    except ValueError, e:
        parser.error(e[0])
    
    # run the test
    tester = Tester(notes, instructions, algorithm, options.debug)
    tester.test()
