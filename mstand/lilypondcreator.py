from Tkinter import *
import os, sys
import re
import time
import Image, ImageTk
from songs import *


class MakeLilyPond:
	def __init__(self, parent):
		self.title = None
		self.lilypond_text = None
		self.notes_to_add = []
		
		# Entered notes use info from previous notes - keep track of those here
		self.last_octave = 4
		self.last_note = 'C'
		self.last_duration = 0
		
		self.initialize_lilypond_string()
		
		self.lilypond_window = Toplevel(parent)
		self.lilypond_window.title("LilyPond Music Creator")
		self.lilypond_window.geometry('800x400+700+100')
				
		self.top_frame = Frame(self.lilypond_window)
		self.top_frame.grid()

		
		#############################################
		## This stuff goes in the note creation frame
		#############################################
		self.note_buttons_frame = Frame(self.top_frame)
		self.note_buttons_frame.grid(column=0,row=5)
		
		self.delete_note_button = Button(self.note_buttons_frame, \
			command = self.delete_note,text="Delete last note")
		self.delete_note_button.grid(row=21)
		
		self.add_time_button = Button(self.note_buttons_frame, \
			command = self.add_note, text = "Add note")
		self.add_time_button.grid(row=20)
		
		# Entry boxes for note name, octave (?)
		self.note_name_label = Label(self.note_buttons_frame,text="Note name:")
		self.note_name_label.grid(row=7,column=0)

		self.note_name_entry = Entry(self.note_buttons_frame,width=2)
		self.note_name_entry.grid(row=7,column=1)
		
		self.note_octave_label = Label(self.note_buttons_frame,text="Octave:")
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
		self.main_buttons_frame.grid(column=5,row=10)
		
		self.quit_button = Button(self.main_buttons_frame, \
			command = self.quit,text="Quit")
		self.quit_button.grid(column=1,row=0)
		
		self.add_create_button = Button(self.main_buttons_frame, \
			command = self.write_to_file, text="Create!")
		self.add_create_button.grid(column=0,row=0)
		
		
		#########################################
		## This stuff goes in the output frame
		#########################################
		self.output_frame = Frame(self.top_frame)
		self.output_frame.grid(column=10,row=5)
		
		self.note_output = StringVar()
		self.note_output.set("Last note added: ")
		
		self.notes_entered = Label(self.output_frame,textvariable=self.note_output)
		self.notes_entered.grid()
		
		
		#############################################
		## This stuff goes in the miscellaneous frame
		#############################################
		self.song_info_frame = Frame(self.top_frame)
		self.song_info_frame.grid(column=5,row=0)
		
		self.title_label = Label(self.song_info_frame,text="Song name:")
		self.title_label.grid(column=0,row=0)
		
		self.title_entry = Entry(self.song_info_frame)
		self.title_entry.grid(column=1,row=0)
		
		self.time_sig_label = Label(self.song_info_frame,text="Time signature:")
		self.time_sig_label.grid(column=2,row=0)
		
		self.time_sig_entry = Entry(self.song_info_frame,width=5)
		self.time_sig_entry.grid(column=3,row=0)
		
		
		
	def initialize_lilypond_string(self):
		self.lilypond_text = []
		#self.lilypond_text.append("\\header { \n")
		#self.lilypond_text.append("title=\"Untitled\" \n")
		#self.lilypond_text.append("}\n") # close \header
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
	
	def write_to_file(self):
	
		# Put the notes in the array of lilypond text
		for note in self.notes_to_add:
			self.lilypond_text[3] += note
			self.lilypond_text[3] += " "
		
		# Get the rest of the song info
		self.title = self.title_entry.get()
		
		if not self.title == "":
			#self.lilypond_text[1] = "title=\"%s\" \n" % self.title
			folder_name = ''
			for word in self.title.lower().split():
				folder_name += word 
			file_name = folder_name + ".ly"
			
		else: # If no title set, use the current time as the folder name
			file_name = "newsong.ly"
			cur_time = time.localtime()
			folder_name = str(cur_time[3]) + str(cur_time[2]) + str(cur_time[1]) \
				+str(cur_time[0])
		
		outfile = open(file_name,'w')
		for item in self.lilypond_text:
			outfile.write(item)
		outfile.close()
		
		# Make the file!
		create_lilypond_files(file_name,folder_name)
		
		# Clear everything out
		self.initialize_lilypond_string()
		self.last_octave = 4
		self.last_note = 'C'
		self.last_duration = 0
		
		
		# ADD THE NEW FILE TO THE CONFIG AND MAKE IT PLAYABLE/SELECTABLE
		# THE LIST DOESN'T UPDATE - CAN WE CHANGE THAT?
		# ALTERNATIVELY, SHOULD WE JUST LOAD THE SONG UP IMMEDIATELY?
		add_song(self.title)
		
		
	
	def delete_note(self):
		'''Deletes the most recently added note. If no notes left, does nothing.'''
		try:
			del self.notes_to_add[-1]
		except IndexError:
			pass
		
	def add_note(self):
		new_note = ""
		
		# If no note name entered, don't add anything
		new_note_name = self.note_name_entry.get().lower()
		if new_note_name == "":
			return
		elif new_note_name not in ['a','b','c','d','e','f','g']:
			return
		else:
			new_note += new_note_name
			
		# Make correct sharp/flat
		cur_sharp = self.sharp.get()
		sharp_ly_format = ""
		if cur_sharp == "sharp":
			sharp_ly_format = "is"
		elif cur_sharp == "flat":
			sharp_ly_format = "es"
			
		new_note += sharp_ly_format
		
		note_octave = self.note_octave_entry.get()
		
		# Do some checking here for octave
		
		# If the duration of this note is different from the last,
		# make it so. Otherwise, lilypond will already know
		new_duration = self.duration.get()
		if new_duration != self.last_duration:
			new_note += str(new_duration)
			self.last_duration = new_duration
		
		# Add the new note to the array
		self.notes_to_add.append(new_note)		
				
		# Update Label's text value i.e. self.note_output.set("TEXT")
		msg = self.note_output.get()
		main_msg = re.split(":",msg)[0]
		main_msg = main_msg + ": " + self.notes_to_add[-1]
		self.note_output.set(main_msg)