from Tkinter import *
import os, sys
import re
import time
import Image, ImageTk
from songs import *


class MakeLilyPond:
	def __init__(self, parent,window):
		self.title = None
		self.lilypond_text = None
		self.notes_to_add = []
		self.main_display = window
		
		# New notes use info from previous notes - keep track of that stuff here
		self.last_octave = 4
		self.last_note = 'c'
		self.last_duration = 0
		
		self.initialize_lilypond_string()
		
		self.lilypond_window = Toplevel(parent)
		self.lilypond_window.title("LilyPond Music Creator")
		self.lilypond_window.geometry('750x300+700+100')
				
		self.top_frame = Frame(self.lilypond_window)
		self.top_frame.grid()

		
		#############################################
		## This stuff goes in the note creation frame
		#############################################
		self.note_buttons_frame = Frame(self.top_frame)
		self.note_buttons_frame.grid(column=0,row=1,rowspan=2)
		
		self.add_time_button = Button(self.note_buttons_frame, \
			command = self.add_note, text = "Add note", \
                        font = ("Trebuchet MS", 14))
		self.add_time_button.grid(row=20)
		
		# Entry boxes for note name, octave (?)
		self.note_name_label = Label(self.note_buttons_frame,text="Note name:", \
                        font = ("Trebuchet MS", 14))
		self.note_name_label.grid(row=7,column=0)

		self.note_name_entry = Entry(self.note_buttons_frame,width=2)
		self.note_name_entry.grid(row=7,column=1)
		
		self.note_octave_label = Label(self.note_buttons_frame,text="Octave:", \
                        font = ("Trebuchet MS", 14))
		self.note_octave_label.grid(row=8,column=0)
		
		self.note_octave_entry = Entry(self.note_buttons_frame,width=2)
		self.note_octave_entry.grid(row=8,column=1)
		
		# Radio buttons for sharp/flat/natural
		self.sharp = StringVar()
		Radiobutton(self.note_buttons_frame,text="Natural",variable=self.sharp,value="natural").grid(row=9,column=0,sticky=W)		
		Radiobutton(self.note_buttons_frame,text="Sharp",variable=self.sharp,value="sharp").grid(row=10,column=0,sticky=W)		
		Radiobutton(self.note_buttons_frame,text="Flat",variable=self.sharp,value="flat").grid(row=11,column=0,sticky=W)
		
		# Radio buttons for duration
		self.duration = IntVar()
		Radiobutton(self.note_buttons_frame,text="Whole",variable=self.duration,value=1).grid(row=9,column=1,sticky=W)
		Radiobutton(self.note_buttons_frame,text="Half",variable=self.duration,value=2).grid(row=10,column=1,sticky=W)
		Radiobutton(self.note_buttons_frame,text="Quarter",variable=self.duration,value=4).grid(row=11,column=1,sticky=W)
		Radiobutton(self.note_buttons_frame,text="Eighth",variable=self.duration,value=8).grid(row=12,column=1,sticky=W)
		Radiobutton(self.note_buttons_frame,text="Sixteenth",variable=self.duration,value=16).grid(row=13,column=1,sticky=W)
		
		
		############################################
		## This stuff goes in the main buttons frame
		############################################
		self.main_buttons_frame = Frame(self.top_frame)
		self.main_buttons_frame.grid(column=20,row=3)
		
		self.quit_button = Button(self.main_buttons_frame, \
			command = self.quit,text="Quit", \
                        font = ("Trebuchet MS", 14))
		self.quit_button.grid(column=1,row=0,padx=5)
		
		self.add_create_button = Button(self.main_buttons_frame, \
			command = self.write_to_file, text="Create!", \
                        font = ("Trebuchet MS", 14))
		self.add_create_button.grid(column=0,row=0,padx=5)
		
		
		######################################
		## This stuff goes in the output frame
		######################################
		self.output_frame = Frame(self.top_frame,height=100,width=300)
		self.output_frame.grid(column=3,row=2,sticky=W)
		self.output_frame.grid_propagate(False)
		
		self.note_output = StringVar()
		self.note_output.set("")
		
		self.notes_entered_1 = Label(self.output_frame,text="Last note added:", \
                        font = ("Trebuchet MS", 14))
		self.notes_entered_1.grid(column=1, row=0, sticky=W)

		self.notes_entered_2 = Label(self.output_frame,textvariable=self.note_output, \
                        font = ("Trebuchet MS",18),height=1,width=20)
		self.notes_entered_2.grid(column=2,row=0)
		
		self.delete_note_button = Button(self.output_frame, \
			command = self.delete_note,text="Delete last note", \
                        font = ("Trebuchet MS", 14))
		self.delete_note_button.grid(column=1,row=21,pady=10)
		
		
		
		#########################################
		## This stuff goes in the song info frame
		#########################################
		self.song_info_frame = Frame(self.top_frame)
		self.song_info_frame.grid(column=0,row=0,columnspan=4)
		
		self.title_label = Label(self.song_info_frame,text="Song name:", \
                        font = ("Trebuchet MS", 14))
		self.title_label.grid(column=0,row=0,padx=5)
		
		self.title_entry = Entry(self.song_info_frame)
		self.title_entry.grid(column=1,row=0,padx=5)
		
		
		
	def initialize_lilypond_string(self):
		self.lilypond_text = []
		self.lilypond_text.append("\\paper { \n")
		self.lilypond_text.append("print-page-number = ##f \n")
		self.lilypond_text.append("}\n") # close \paper
		self.lilypond_text.append("\\score { \n")
		self.lilypond_text.append("\\relative c' { \n")
		self.lilypond_text.append("\\time 4/4 \n")
		self.lilypond_text.append("") # this is where notes will go
		self.lilypond_text.append("}\n") # close \relative
		self.lilypond_text.append("\\midi { } \n")
		self.lilypond_text.append("\\layout { } \n")
		self.lilypond_text.append("} \n") # close \score
		self.lilypond_text.append("\\version \"2.12.2\" \n")

	def quit(self):
		self.lilypond_window.destroy()
		self.main_display.remake_welcome()
	
	def write_to_file(self):
	
		# Put the notes in the array of lilypond text
		for note in self.notes_to_add:
			self.lilypond_text[6] += note
			self.lilypond_text[6] += " "
		
		# Get the rest of the song info
		self.title = self.title_entry.get()
		
		if not self.title == "":
			folder_name = ''
			for word in self.title.lower().split():
				folder_name += word 
			file_name = folder_name + ".ly"
			add_song(self.title)
			
		else: # If no title set, use the current time as the folder name
			cur_time = time.localtime()
			folder_name = str(cur_time[4]) + str(cur_time[3]) + str(cur_time[2])
			add_song(folder_name)
			file_name = folder_name+".ly"
		
		outfile = open(file_name,'w')
		for item in self.lilypond_text:
			outfile.write(item)
		outfile.close()
		
		# Make the file!
		create_lilypond_files(file_name,folder_name)
		
		# Clear everything out
		self.initialize_lilypond_string()
		self.last_octave = 4
		self.last_note = 'c'
		self.last_duration = 0
		
		
	
	def delete_note(self):
		'''Deletes the most recently added note. If no notes left, does nothing.'''
		try:
			del self.notes_to_add[-1]
			self.last_note = self.notes_to_add[-1][0]
			self.last_duration = int(re.findall('[0-9]', self.notes_to_add[-1])[0])
			self.update_note_output()
		except IndexError:
			self.note_output.set("")
		
	def add_note(self):
		new_note = ""
		
		# If no note name entered, don't add anything
		new_note_name = self.note_name_entry.get().lower()
		if new_note_name == "":
			return
		elif new_note_name not in ['a','b','c','d','e','f','g','r']:
			return
		else:
			new_note += new_note_name
		
		if new_note_name != 'r':
			# Make correct sharp/flat
			cur_sharp = self.sharp.get()
			sharp_ly_format = ""
			if cur_sharp == "sharp":
				sharp_ly_format = "is"
			elif cur_sharp == "flat":
				sharp_ly_format = "es"
				
			new_note += sharp_ly_format

		# Modify the octave accordingly
		note_octave = self.note_octave_entry.get()
		if note_octave != "":
			note_octave = int(note_octave)
			actual_oct_dif = note_octave - self.last_octave
			theoretical_oct_dif = self.find_octave(self.last_note,new_note_name)
			new_octave = actual_oct_dif - theoretical_oct_dif
			
			marker = ""
			if new_octave > 0:
				marker = "'"
			elif new_octave < 0:
				marker = ","
			
			new_note += (marker*abs(new_octave))
				
			self.last_octave = note_octave
		
		# Set the duration of this note (it's not necessary if the 
		# new note's duration is the same as that of the last, but it
		# makes it easier for displaying stuff)
		new_duration = self.duration.get()
		new_note += str(new_duration)
		self.last_duration = int(new_duration)
		
		# Add the new note to the array
		self.notes_to_add.append(new_note)		
				
		# Update Label's text value
		self.update_note_output()
		
		# Set what most recently added note was
		self.last_note = new_note_name
	
	def update_note_output(self):
		if len(self.notes_to_add) == 0:
			self.note_output.set("")
		else:
			self.note_output.set(self.interpret_note(self.notes_to_add[-1]))
	
	def interpret_note(self,note):
		
		mappings = {1:"whole", 2:"half", 4:"quarter", 8:"eighth", 16:"sixteenth"}
		
		note_name = note[0].upper()
		if note_name == 'R':
			note_name = "Rest"
			
		if "is" in note:
			note_name += " sharp"
		elif "es" in note:
			note_name += " flat"
		
		note_name = note_name + " (%s)" % mappings[self.last_duration]
		return note_name
		
		
	def find_octave(self, prevnote, curnote):
		'''Given the previous note and the new note, determines whether
		the new note is in the same octave or not.'''
		curval = ord(curnote)
		prevval = ord(prevnote)
		if curval > prevval:
			dif = curval - prevval
			if dif > 3:
				return -1
			else:
				return 0
		else:
			dif = prevval - curval
			if dif > 3:
				return 1
			else:
				return 0