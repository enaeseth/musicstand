# This thing reads a .ly file and spits out a list of all of the notes.
# It is ugly and dumb but it works.
# Usage: python lilypondParser.py filetoparse.ly
# By comps, 10/3/09

import sys

def parseFile(filename):
	file = open(filename, 'r')
	for line in file:
		list = line.split()
		if list:
			if list[0].isalpha() or list[0] == "<":
				for i in list:
					if i.isalpha():
						print i
	file.close()

if __name__ == '__main__':
	filename = sys.argv[1]
	parseFile(filename)