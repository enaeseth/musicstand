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

@test('lol')
def test_march_g_split():
    play('g_march')
    expect('G4')
    expect('G3')
    expect('G3')
    expect('G4')
