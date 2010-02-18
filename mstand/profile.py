# encoding: utf-8

"""
Reading, writing, and creating instrument profiles.
"""

from __future__ import with_statement
from threading import Thread, Condition
from mstand.notes import *
import os.path
import re

try:
    import simplejson as json
except ImportError:
    import json

class Profile(object):
    """
    An instrument profile.
    """
    
    def __init__(self, name, peaks=None, path=None):
        self.name = name
        self.peaks = peaks or {}
        self.path = path
    
    def save(self, path=None):
        path = path or self.path
        if not path:
            raise ValueError('no path specified and none saved')
        
        with open(path, 'wb') as stream:
            write_profile(self, stream)
    
    def __repr__(self):
        return '%s(%r, %r, %r)' % (type(self).__name__, self.name, self.peaks,
            self.path)

class ProfileReadError(ValueError):
    pass

def get_profile_storage_dir():
    raw = os.path.join(os.path.dirname(__file__), '..', 'profiles')
    return os.path.normpath(raw)

def load_profile(filename):
    if os.path.splitext(filename)[1] != '.json':
        filename += '.json'
    
    if not os.path.exists(filename):
        standard = os.path.join(get_profile_storage_dir(), filename)
        if os.path.exists(standard):
            filename = standard
    
    with open(filename, 'rt') as stream:
        return read_profile(stream, filename)

def read_profile(stream, path=None):
    try:
        # try to load the JSON document that encodes the profile
        raw = json.load(stream)
    except ValueError, e:
        # uh fuck, it's not valid JSON
        raise ProfileReadError(*e.args)
    
    try:
        version = raw['version']
    except KeyError:
        raise ProfileReadError('profile has no version')
    else:
        if version != '2.0':
            raise ProfileReadError('incorrect profile version: %s' % version)
    
    name = raw['name']
    
    peaks = {}
    for peaking_note, signalled_notes in raw['peaks'].iteritems():
        peaking_note = Note.parse(str(peaking_note))
        
        signalled = []
        for note, components in signalled_notes:
            components = dict((Note.parse(str(component)), intensity)
                for component, intensity in components.iteritems())
            signalled.append((Note.parse(str(note)), components))
        peaks[peaking_note] = signalled
    
    return Profile(name, peaks, path)

def write_profile(profile, stream):
    serialized = {
        'version': '2.0',
        'name': profile.name,
        'peaks': {}
    }
    
    for peaking_note, signalled_notes in profile.peaks.iteritems():
        signalled = []
        
        for note, components in signalled_notes:
            components = dict((str(component), intensity)
                for component, intensity in components.iteritems())
            signalled.append((str(note), components))
        
        serialized['peaks'][str(peaking_note)] = signalled
    
    json.dump(serialized, stream, indent=4)

if __name__ == '__main__':
    import sys
    profile = load_profile(sys.argv[1])
    
    write_profile(profile, sys.stdout)
