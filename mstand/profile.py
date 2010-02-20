# encoding: utf-8

"""
Reading, writing, and creating instrument profiles.
"""

from __future__ import with_statement
from threading import Thread, Condition
from itertools import izip
from mstand.notes import *
import operator
import os.path
import math
import re

try:
    import simplejson as json
except ImportError:
    import json

def dot_product(*vectors):
    return sum(reduce(operator.mul, paired) for paired in izip(*vectors))

def magnitude(vector):
    return math.sqrt(sum(c * c for c in vector))

def cosine_distance(*vectors):
    """
    Computes the cosine distance between the given vectors.
    
    The return value is a float ranging over [-1, 1], where -1 indicates
    complete dissimilarity and 1 indicates that the vectors are identical.
    """
    
    return (float(dot_product(*vectors)) /
        reduce(operator.mul, (magnitude(v) for v in vectors)))

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
        self.path = path
    
    def find_match(self, peak, supporters, minimum_match=0.8):
        try:
            notes = self.peaks[peak]
        except KeyError:
            return None
        
        supporting_notes = set(supporters)
        for note, note_supporters in notes:
            supporting_notes |= set(note_supporters)
        
        def create_vector(supporters):
            return [supporters.get(note, 0.0) for note in supporting_notes]
        
        heard_vector = create_vector(supporters)
        
        def compute_similarity(note_supporters):
            try:
                return cosine_distance(heard_vector,
                    create_vector(note_supporters))
            except ZeroDivisionError:
                return minimum_match
        
        best_note = None
        best_match = -1
        
        # print 'peak of %3s: ' % str(peak),
        for note, note_supporters in notes:
            similarity = compute_similarity(note_supporters)
            # print '%3s (%.3f)' % (note, similarity),
            if similarity > best_match:
                best_match = similarity
                best_note = note
        # print
        
        return (best_note, best_match) if best_match >= minimum_match else None
    
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
    
    def as_note(v):
        return Note.parse(str(v))
    
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
            components = dict((as_note(component), intensity)
                for component, intensity in components.iteritems())
            signalled.append((as_note(note), components))
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

