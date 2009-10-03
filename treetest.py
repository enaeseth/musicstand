#THIS CODE IS PROBS BROKEN. BUT WE PROBABLY WON'T USE IT BECAUSE IT IS MUSICXML 
#WHICH IS LAMESAUCE. ANYWAY I AM PUTTING IT HERE IN CASE WE DECIDE WE NEED IT.

import ElementTree as ET
import notes
file = open("filename.txt", 'w')
tree = ET.parse("entertainer.xml")
divisions = 0
for element in tree.getiterator():
	if element.findtext('divisions'):
		for beats in element.getiterator('divisions'):
			divisions = beats.text
			print divisions
	if element.findtext('note'):
			for thing in element.getiterator('note'):
				def get_item(tag):
					return thing.getiterator(tag).next().text
				
				step, accidental, octave = map(get_item, ['step', 'accidental', 'octave'])
				
				print notes.note_to_freq(octave, step, accidental)
				for otherthing in thing.getiterator('step'):
					file.write(otherthing.text,)
				for otherthing4 in thing.getiterator('accidental'):
					file.write(' '+otherthing4.text+' ',)
				for otherthing2 in thing.getiterator('octave'):
					file.write(otherthing2.text+'\n')
'''				for otherthing5 in thing.getiterator('rest'):
					print "REST",'''
'''				for otherthing3 in thing.getiterator('duration'):
					print otherthing3.text'''
file.close()