# encoding: utf-8

from __future__ import with_statement
import os
import sys
import subprocess
import re

def get_songs_dir():
    return 'songs'

def get_song_path(name):
    return os.path.join(get_songs_dir(), name)

def get_config_path():
    return os.path.join(get_songs_dir(), 'config.txt')

def get_songs():
    try:
        with open(get_config_path(), 'rt') as f:
            return [line.strip() for line in f]
    except IOError, e:
        if e.errno == 2:
            return [] # songs.txt was not found, but that's OK
        raise

def add_song(title):
    try:
        with open(get_config_path(), 'r+t') as f:
            for line in f:
                if line.strip() == title:
                    # got it already
                    return
            print >>f, title
    except IOError, e:
        if e.errno != 2:
            raise
    
    # make a new one!
    songs = get_songs_dir()
    if not os.path.isdir(songs):
        os.makedirs(songs)
    
    with open(get_config_path(), 'wt') as f:
        print >>f, title

def create_lilypond_files(file_path, song_name):
	'''Given a path to a lilypond file and the desired name of the song, creates
	a directory for that song in our Songs folder, copies the lilypond file to
	it, and runs the lilypond script to create .ps, .pdf, and .midi files.'''
	
	cache_dir = get_song_path(song_name)
	file_name = os.path.basename(file_path)
	
	if os.path.exists(cache_dir):
		# Song has already been previously added
		return
	else:
		# Song is new - make a directory for it and copy the .ly file to it
		os.makedirs(cache_dir)
		
		subprocess.check_call(['cp', file_path, cache_dir])

	lilypond_path = os.path.join(os.path.dirname(__file__), 'lilypond.sh')
	new_path = os.path.join(cache_dir, file_name)
	
	# OPEN THE LILYPOND FILE AND LOOK THROUGH IT TO MAKE SURE IT HAS 
	# \midi AND \layout. IF IT DOES, FINE. IF IT DOESN'T, ADD THEM
	# AND OVERWRITE THE FILE
	
	# Run lilypond script
	subprocess.check_call([lilypond_path, new_path])
	
	# Convert pdf to pictures
	file_base = os.path.splitext(file_name)[0]
	pdf_name = os.path.join(cache_dir, file_base + ".pdf")
	png_name = os.path.join(cache_dir, file_base + ".png")
		
	# Convert PDF to pictures
	print "Converting PDF to images...",
	os.system("convert -density 400 " + pdf_name + " -resize 25% " + png_name )
	print "done."

if __name__ == '__main__':
	create_lilypond_files("~/Desktop/march.ly", "ImperialMarch")
	