import os
import sys
import re

def create_lilypond_files(file_path, song_name):
	#lilypond_path = os.path.join(os.path.dirname(__file__), 'lilypond.sh')
	#new_path = os.path.join(cache_dir, os.path.basename(newfilename))
	#os.system('"%s" "%s"' % (lilypond_path, new_path))
	
	cache_dir = "Songs/%s" % song_name
	file_name = re.split("/",file_path)[-1]

	# Make sure the "Songs" directory exists
	if not os.path.exists("Songs"):
		os.mkdir("Songs")
	
	if os.path.exists(cache_dir):
		# Song has already been previously added
		return
	else:
		# Song is new - make a directory for it and copy the .ly file to it
		os.mkdir(cache_dir)
		copy_lilypond = "cp %s %s" % (file_path, cache_dir)
		os.system(copy_lilypond)

	
	lilypond_path = os.path.join(os.path.dirname(__file__), 'lilypond.sh')
	new_path = os.path.join(cache_dir,file_name)
	
	# OPEN THE LILYPOND FILE AND LOOK THROUGH IT TO MAKE SURE IT HAS 
	# \midi AND \layout. IF IT DOES, FINE. IF IT DOESN'T, ADD THEM
	# AND OVERWRITE THE FILE
	
	os.system('"%s" "%s"' % (lilypond_path,new_path))
	
	

if __name__ == '__main__':
	create_lilypond_files("~/Desktop/march.ly", "ImperialMarch")