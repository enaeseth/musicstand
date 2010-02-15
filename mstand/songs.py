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
            return
    except IOError, e:
        if e.errno != 2:
            raise
    
    # make a new one!
    songs = get_songs_dir()
    if not os.path.isdir(songs):
        os.makedirs(songs)
    
    with open(get_config_path(), 'wt') as f:
        print >>f, title

def add_midi_line(file_path):
    '''This thing makes a balls-ton of assumptions. Most of them are legit, though.
    For instance, it assumes there will be a score block. It also assumes there will
    be no more blocks that end after the score block. Also also, it assumes that
    if there is already a midi block, there is also a layout block; that is, the
    person writing the lilypond file didn't royally f*ck it up. Um, what does this
    actually do? Makes sure the lilypond file is set up to generate a midi. That's
    all.
    '''
    ly_file = open(file_path, 'r+')
    if '\midi' in ly_file.read():
        return 1
    else:
        ly_file.seek(0)
        for ix in xrange(len(ly_file.read())):
            ly_file.seek(-ix,2)
            if ly_file.read(1) == '}':
                end_of_file = ly_file.read()
                ly_file.seek(-ix-1, 2)
                ly_file.write("\midi { } \n \layout { } \n }")
                ly_file.write(end_of_file)
                ly_file.close()
                return 1


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
    # Edit: This thing exists now. I hope it works and doesn't break like
    # everything else I touch. If it doesn't, at least you can just
    # comment out this line and everything will be okay.
    add_midi_line(new_path)
    
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
    
