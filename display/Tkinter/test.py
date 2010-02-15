from Tkinter import *
import os, sys
import re
import time
import Image, ImageTk


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
		self.note_output.set("Notes played so far: ")
		
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
		self.lilypond_text.append("\\header { \n")
		self.lilypond_text.append("title=\"Untitled\" \n")
		self.lilypond_text.append("}\n") # close \header
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
			self.lilypond_text[6] += note
			self.lilypond_text[6] += " "
		
		# Get the rest of the song info
		self.title = self.title_entry.get()
		
		if not self.title == "":
			self.lilypond_text[1] = "title=\"%s\" \n" % self.title
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
		
		# NEED TO IMPORT SOME STUFF?
		#create_lilypond_files(file_name,folder_name)
		
		# Clear everything out
		self.initialize_lilypond_string()
		
	
	def delete_note(self):
		'''Deletes the most recently added note. If no notes left, does nothing.'''
		try:
			del self.notes_to_add[len(self.notes_to_add)-1]
			print self.notes_to_add
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
		
		print self.notes_to_add
		
		# Update Label's text value i.e. self.note_output.set("TEXT")
		msg = self.note_output.get()
		main_msg = re.split(":",msg)[0]
		main_msg = main_msg + ": " + self.notes_to_add[-1]
		self.note_output.set(main_msg)
		
	
		

		

class PageDisplay:
    def __init__(self, parent, pic_dir):
        self.parent = parent
        self.image_dir = pic_dir
        self.tkimage_dir = [ImageTk.PhotoImage(image) for image in self.image_dir]
        self.cur_image_index = 0
        self.changing_page = False
        
        self.top_frame = Frame(parent)
        self.top_frame.pack()
          
        #buttons frame
        self.buttons_frame = Frame(self.top_frame)
        self.buttons_frame.pack(side=TOP)
        
        self.cur_image_object = self.tkimage_dir[0]
        
        #image label
        self.cur_image = Label(self.top_frame, \
        image = self.cur_image_object)
        self.cur_image.pack(side=TOP)
        
        #buttons for button_frame
        self.button_prev = Button(self.buttons_frame, command = self.prev_simple,\
            text="Previous")
        self.button_prev.pack(side=LEFT)
        
        self.button_simple = Button(self.buttons_frame, \
            command = self.next_simple, text="Simple")
        self.button_simple.pack(side=LEFT)
        
        self.button_hor_overlay = Button(self.buttons_frame, \
            command = lambda speed=10: self.next_hor_overlay(speed),\
            text="Horizontal Overlay")
        self.button_hor_overlay.pack(side=LEFT)
        
        self.button_hor_slide = Button(self.buttons_frame, \
            command = lambda speed=10: self.next_hor_slide(speed), \
            text="Horizontal Slide")      
        self.button_hor_slide.pack(side=LEFT)
        
        self.button_vert_overlay = Button(self.buttons_frame, \
            command = lambda speed=10: self.next_vert_overlay(speed),
            text="Vertical Overlay")
        self.button_vert_overlay.pack(side=LEFT)
        
        self.button_vert_slide = Button(self.buttons_frame, \
            command = lambda speed=10: self.next_vert_slide(speed),
            text="Vertical Slide")
        self.button_vert_slide.pack(side=LEFT)
        
        self.make_music = Button(self.buttons_frame, command = self.lilypond, text = "Create")
        self.make_music.pack(side=LEFT)
       
    def lilypond(self):
    	x = MakeLilyPond(self.parent)
    	
    def prev_simple(self):
        '''Destroys current display image and displays previous image in
        self.tkimage_dir'''
        self.cur_image_index = (self.cur_image_index-1)%len(self.image_dir)
        self.cur_image.destroy()
        self.cur_image = Label(self.top_frame, \
        image=self.tkimage_dir[self.cur_image_index])
        self.cur_image.pack(side=TOP)
        
    def next_simple(self):
        '''Destroys current display image and displays next image in
        self.tkimage_dir'''
        self.cur_image_index = (self.cur_image_index+1)%len(self.image_dir)
        self.cur_image.destroy()
        self.cur_image = Label(self.top_frame, \
        image=self.tkimage_dir[self.cur_image_index])
        self.cur_image.pack(side=TOP)
        
    def next_hor_overlay(self, speed):
        '''Changes to next picture in tkimage_dir by pasting strips of it,
        determined by the value of speed, over the previous image in a loop.'''
        next_image_index = (self.cur_image_index+1)%len(self.image_dir)
        cur_image = self.image_dir[self.cur_image_index].copy()
        next_image = self.image_dir[next_image_index].copy()
        self.changing_page = True
        right = speed
        height = next_image.size[1]
        while self.changing_page:
            region = next_image.crop((0, 0, right, height))
            cur_image.paste(region, (0, 0, right, height))
            cur_tkimage = ImageTk.PhotoImage(cur_image)

            self.cur_image.destroy()
            self.cur_image = Label(self.top_frame, image = cur_tkimage)
            self.cur_image.pack(side=TOP)
            right += speed
            self.cur_image.update() #need to call this if you don't go through
                                    #mainloop?
            if right == next_image.size[0]:
                self.changing_page = False
        self.cur_image.destroy()
        self.cur_image = Label(self.top_frame, \
            image=self.tkimage_dir[next_image_index])
        self.cur_image.pack(side=TOP)
        self.cur_image_index = next_image_index
        
    def next_hor_slide(self, speed):
        next_image_index = (self.cur_image_index+1)%len(self.image_dir)
        cur_image = self.image_dir[self.cur_image_index].copy()
        next_image = self.image_dir[next_image_index].copy()
        self.changing_page = True
        right = speed
        height = next_image.size[1]
        while self.changing_page:
            transition = Image.new(next_image.mode, next_image.size)
            new_region = next_image.crop((0, 0, right, height))
            old_region = cur_image.crop((right, 0, cur_image.size[0], height))
            transition.paste(new_region, (cur_image.size[0]-right, 0, \
                cur_image.size[0], height))
            transition.paste(old_region, (0, 0, cur_image.size[0]-right, height))
            tk_transition = ImageTk.PhotoImage(transition)
            self.cur_image.destroy()
            self.cur_image = Label(self.top_frame, image = tk_transition)
            self.cur_image.pack(side=TOP)
            right += speed
            self.cur_image.update()
            if right == next_image.size[0]:
                self.changing_page = False
        self.cur_image.destroy()
        self.cur_image = Label(self.top_frame, \
            image=self.tkimage_dir[next_image_index])
        self.cur_image.pack(side=TOP)
        self.cur_image_index = next_image_index
        
    def next_vert_overlay(self, speed):
        '''Changes to the next image in tkimage_dir by pasting horizontal
        strips, determined by speed, over the previous image in a loop.'''
        next_image_index = (self.cur_image_index+1)%len(self.image_dir)
        cur_image = self.image_dir[self.cur_image_index].copy()
        next_image = self.image_dir[next_image_index].copy()
        self.changing_page = True
        width = next_image.size[0]
        height = speed
        while self.changing_page:
            region = next_image.crop((0, 0, width, height))
            cur_image.paste(region, (0, 0, width, height))
            cur_tkimage = ImageTk.PhotoImage(cur_image)
            self.cur_image.destroy()
            self.cur_image = Label(self.top_frame, image = cur_tkimage)
            self.cur_image.pack(side=TOP)
            height += speed
            self.cur_image.update()
            if height == next_image.size[1]:
                self.changing_page = False
        self.cur_image.destroy()
        self.cur_image = Label(self.top_frame, \
            image=self.tkimage_dir[next_image_index])
        self.cur_image.pack(side=TOP)
        self.cur_image_index = next_image_index
    
    def next_vert_slide(self, speed):
        next_image_index = (self.cur_image_index+1)%len(self.image_dir)
        cur_image = self.image_dir[self.cur_image_index].copy()
        next_image = self.image_dir[next_image_index].copy()
        self.changing_page = True
        height = speed
        width = next_image.size[0]
        while self.changing_page:
            transition = Image.new(next_image.mode, next_image.size)
            new_region = next_image.crop((0, 0, width, height))
            old_region = cur_image.crop((0, height, width, \
                cur_image.size[1]))
            transition.paste(new_region, (0, cur_image.size[1]-height, width, \
                cur_image.size[1]))
            transition.paste(old_region, (0, 0, width, cur_image.size[1]-height))
            tk_transition = ImageTk.PhotoImage(transition)
            self.cur_image.destroy()
            self.cur_image = Label(self.top_frame, image = tk_transition)
            self.cur_image.pack(side=TOP)
            height += speed
            self.cur_image.update()
            if height == next_image.size[1]:
                self.changing_page = False
        self.cur_image.destroy()
        self.cur_image = Label(self.top_frame, \
            image=self.tkimage_dir[next_image_index])
        self.cur_image.pack(side=TOP)
        self.cur_image_index = next_image_index
    
def main():
    #get list of only images in current directory
    #image types allowed governed in re_image_types
    path = '.'
    dir_list = os.listdir(path)
    re_image_types = '.*.gif$|.*.jpg$|.*.png$|.*.jpeg$'
    pattern = re.compile(re_image_types, re.IGNORECASE)
    dir_list = filter(pattern.search, dir_list)
    
    #start root Tk window
    root = Tk()
    image_list = [Image.open(image) for image in dir_list]
    size = image_list[0].size
    #image_list[0].paste("Red", (x, y, x+20, y+20))
    #image_list[0].save('march.png')
    display = PageDisplay(root, image_list)
    root.title('YEEEEEEEEEAAAAAAAAHHHHH')

    root.mainloop()
    
if __name__ == '__main__':
    main()