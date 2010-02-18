# encoding: utf-8

"""
A tool for testing note recognition.
"""

from __future__ import with_statement

from mstand.profile import load_profile
from mstand.terminal import color
from mstand.test import *

from warnings import simplefilter as filter_warnings
from fnmatch import fnmatch
import traceback
import sys
import os

try:
    from warnings import catch_warnings
except ImportError:
    # Python > 2.6
    from contextlib import contextmanager
    
    @contextmanager
    def catch_warnings(record=False):
        import warnings
        
        class _Warning(object):
            def __init__(self, message, category, filename, lineno):
                self.message = message
                self.category = category
                self.filename = filename
                self.lineno = lineno
                
        
        warn_list = []
        def save_warning(message, category, filename, lineno, *args):
            warn_list.append(_Warning(message, category, filename, lineno))
        
        old = warnings.showwarning
        try:
            warnings.showwarning = save_warning
            yield warn_list
        finally:
            warnings.showwarning = old

def load_tests():
    """
    Imports all of the Python files in the tests/identify folder.
    """
    
    root = os.path.dirname(__file__)
    source_dir = os.path.join(root, 'tests', 'identify')
    
    try:
        sys.path.insert(0, source_dir)
        for filename in os.listdir(source_dir):
            if filename.endswith('.py'):
                module = filename.replace('.py', '')
                __import__(module, globals(), locals())
    finally:
        sys.path.pop(0)
    
    return get_tests()

def filter_tests(tests, patterns):
    """
    Filter the given test dictionary using the given list of test handle
    patterns.
    """
    
    filtered = {}
    patterns = [pattern.lower() for pattern in patterns]
    
    for handle, test in tests.iteritems():
        if any(fnmatch(handle, pattern) for pattern in patterns):
            filtered[handle] = test
    
    return filtered

def run_tests(tests):
    """
    Runs all of the tests in the given test dictionary and prints the
    results.
    """
    
    results = {'ok': 0, 'warnings': 0, 'errors': 0}
    
    for handle in sorted(tests.iterkeys()):
        test = tests[handle]
        unheard = None
        missing_rec = None
        error = None
        warnings = []
        
        with catch_warnings(record=True) as w:
            try:
                run_test(test)
            except UnheardNoteError, e:
                unheard = e
            except MissingRecordingError, e:
                missing_rec = e
            except Exception:
                error = sys.exc_info()
            
        for warning in w:
            if warning.category is ExtraNoteWarning:
                warnings.append(warning.message)
        
        if unheard is not None or error is not None or missing_rec is not None:
            color_name = 'red!'
            results['errors'] += 1
        elif warnings:
            color_name = 'yellow!'
            results['warnings'] += 1
        else:
            color_name = 'green!'
            results['ok'] += 1
        
        print color(color_name, test.name)
        
        for warning in warnings:
            print '  %2d: Extra notes:' % warning.expectation, \
                ', '.join(str(note) for note in warning.notes)
        
        if unheard is not None:
            print color('red', '  %2d: Failed to detect ' %
                unheard.expectation +
                ', '.join(str(note) for note in unheard.notes))
        if missing_rec is not None:
            print color('red', '  Unable to find recording %r' %
                missing_rec.args[0])
        if error is not None:
            print color('red', '  %s' % error[1])
            trace = traceback.format_tb(error[2])
            for element in trace:
                for line in element.splitlines():
                    print >>sys.stderr, '  ' + line
    
    total = sum(results.itervalues())
    
    # display overall information
    print
    print 'Results: %d (%.0f%%) OK, %d (%.0f%%) warnings, %d (%.0f%%) failed' \
        % (results['ok'], 100 * float(results['ok']) / total,
            results['warnings'], 100 * float(results['warnings']) / total,
            results['errors'], 100 * float(results['errors']) / total,)

if __name__ == '__main__':
    from optparse import OptionParser
    
    parser = OptionParser('%prog [pattern ...]')
    parser.add_option('-p', '--profile', metavar='NAME',
        help='the instrument profile to use')
    parser.add_option('-l', '--live', action='store_true',
        help="don't use recordings; ask for live playing instead")
    parser.set_defaults(profile='piano', live=False)
    
    options, args = parser.parse_args()
    
    try:
        set_test_profile(load_profile(options.profile))
    except IOError, e:
        parser.error('failed to load profile %r: %s' %
            (options.profile, e.args[1]))
    
    tests = load_tests()
    if len(args) > 0:
        tests = filter_tests(tests, args)
    
    run_tests(tests)
