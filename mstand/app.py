# encoding: utf-8

"""
The heart of the beast.
"""

from mstand import audio
from mstand.capture import Capturer
from mstand.display import Display
from mstand.filters import *
from mstand.interpret import *
from mstand.match import Matcher
from mstand.parser import parse_file
from Tkinter import Tk

class MusicStand(object):
    """
    An intelligent digital music stand.
    """
    
    def __init__(self, algorithm, listener, profile, interpreter, debug=False):
        self._matcher = Matcher(algorithm, interpreter, self._position_changed,
            debug)
        self._capturer = Capturer(listener, self._handle_buckets)
        self._display = None
        self._running = False
        self._debug = debug
        
    def run(self):
        """
        Runs the music stand.
        
        This method will not return until the application exits.
        """
        
        callbacks = dict(song_loaded=self._start_song,
            song_stopped=self._abort_song, song_restarted=self._restart_song)
        
        self._capturer.start()
        self._matcher.start()
        
        try:
            self._running = True
            
            root = Tk()
            self._display = Display(root, callbacks, self._debug)
            
            # run the Tkinter event loop
            root.mainloop()
        except KeyboardInterrupt:
            print
        finally:
            self._running = False
            self._matcher.shutdown()
            self._capturer.stop()
    
    def _start_song(self, lilypond_file):
        if self._debug:
            print 'Song loaded: %s' % lilypond_file
        
        notes = parse_file(lilypond_file)
        self._matcher.load_piece(notes)
    
    def _abort_song(self):
        self._matcher.stop_piece()
    
    def _restart_song(self):
        self._display.reset_song_positions()
        self._display.reset_sheetmusic()
        self._matcher.restart_piece()
    
    def _handle_buckets(self, buckets):
        # XXX: this is dumb
        notes = [p[0] for p in sorted(buckets, key=lambda b: b[1],
            reverse=True)]
        
        self._matcher.add(notes)
    
    def _position_changed(self, matcher):
        if matcher.intervals is None:
            return
        
        self._display.update_position(matcher)
        
        if matcher.current_location >= (len(matcher.intervals) - 1):
            if self._debug:
                print 'Done with the piece!'
