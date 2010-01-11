# encoding: utf-8

"""
Provides the base class for matching algorithms.
"""

class Algorithm(object):
    """
    An abstract class that matching algorithms should extend.
    
    Matchers call upon Algorithms to do the actual work of matching for
    them. They call an Algorithm method in four specific cases:
    
      - When a Matcher gets paired with an Algorithm, it calls the
        Algorithm's `assign_matcher` method.
      - When a Matcher is given a new piece of music to start, it calls
        the algorithm's `start_piece` method. The list of intervals in
        the piece is available on the matcher's `intervals` property.
      - When the Matcher receives new frequencies from the audio processor,
        it calls the Algorithm's `filter_frequencies` method.
      - When the Matcher is ready to update its current position within the
        piece, it calls the Algorithm's `match` method.
    """
    
    def __init__(self):
        self.matcher = None
    
    def assign_matcher(self, matcher):
        assert self.matcher is None, 'this algorithm object already has a ' \
            'matcher'
        self.matcher = matcher
        self.configure_matcher()
    
    def configure_matcher(self):
        """
        Override this function to make any desired calls into
        `self.matcher` at startup.
        """
        pass
    
    def start_piece(self):
        """
        Called by a Matcher when a new piece is started.
        """
        pass
    
    def filter_frequencies(self, frequencies):
        """
        Called by a Matcher when new frequencies are available.
        
        This method should convert the list of frequencies into whatever
        representation the matching algorithm desires, and return that
        representation.
        """
        
        # By default, do nothing.
        return frequencies
    
    def match(self, notes):
        """
        Finds the current position after hearing a new batch of notes.
        
        The `notes` parameter will be a list of notes, in whatever form
        was returned by `filter_frequencies`.
        
        This method should return the player's current position in the
        piece, as the index of the last-played interval. If the algorithm
        cannot determine the player's position (or can only do so with
        very low confidence), it should instead raise an
        UnknownPositionError.
        """
        
        raise NotImplementedError('`match` is an abstract method')
    
    def debug(self, message, *args):
        """
        Passes along the message to the matcher's `debug` method.
        """
        self.matcher.debug(message, *args)

class UnknownPositionError(RuntimeError):
    pass
