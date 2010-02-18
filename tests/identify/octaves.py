# encoding: utf-8

"""
Test notes across octaves.
"""

from mstand.test import *

@test('C3 - C6')
def test_c_series():
    play('c_series')
    expect('C3')
    expect('C4')
    expect('C5')
    expect('C6')
