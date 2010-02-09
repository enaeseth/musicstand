# encoding: utf-8

"""
Utilities for interacting with the terminal.
"""

import sys

def color(color_spec, text, *args):
    """
    Colorize the given text.
    
    This only works in a UNIX terminal; on Windows, text will not be
    colored.
    """
    
    if sys.platform == 'win32':
        # gahhh
        return text % args if args else text
    
    colors = {
        '': '',
        'black': '30',
        'red': '31',
        'green': '32',
        'yellow': '33',
        'blue': '34',
        'purple': '35',
        'cyan': '36',
        'white': '37'
    }

    if color_spec.endswith('!'):
        bold = '1'
        color_spec = color_spec[:-1]
    else:
        bold = '0'

    if args:
        text = text % args

    color = colors[color_spec]
    if color:
        color = ';%s' % color
    return '\x1b[%s%sm%s\x1b[0;00m' % (bold, color, text)
