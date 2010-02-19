'''
THINGS TO NOTE:
-we start measures and pages at 0!

NEED TO FIX:
--Goddamn page2 zoom1 measure screwy percentages.

--Fix if there's only 1 zoom section, right now it just keeps big page.

--Make it so that if they're playing the piece, they can't change the zoom view.

--Deal with end of music stuff (index out of range!)
'''

from __future__ import with_statement
from Tkinter import *
from glob import glob
import os, sys
import re
import Image, ImageTk
import psprocess
from Queue import Queue, Empty as QueueEmpty
from songs import *
from lilypondcreator import *

class Display(object):
    def __init__(self, parent, song_loaded, DEBUG=False):
        self.parent = parent
        self.parent.title("Digital Music Stand")
        self.parent.geometry('+50+50')
        self.screen_width = float(self.parent.winfo_screenwidth())
        self.screen_height = float(self.parent.winfo_screenheight())
        self.image_dir = None
        self.tkimage_dir = None
        self.cur_image = None
        self.cur_tkimage = None
        self.options_window = None
        self.lilypond_file = 'march.ly'
        self.image_dir_zoom = []
        self.measure_percents = None 
        self.ps_info = None
        self.zoom_measures = []
        self.lines_per_page = 2
        self.playing = False
        self.cur_measure = 0
        self.cur_page_index = 0
        self.cur_zoom_index = 0
        self.zoomed = False
        self.debug = DEBUG
        self.transparent = None
        self.color = "Red"
        self.zoom_staff_height = -1
        self.cur_line = 0
        self.num_measures_before_transition = 0
        self.transition_measures = []
        self.transition_measures_zoom = []
        self.speed = 5
        self.transition = self.next_page_voverlay
        
        self.updates = Queue(0)
        self.song_loaded = song_loaded
        
        self.welcome_frame = self.init_welcome(self.parent)
        self.parent.after(50, self.check_for_updates)
    
    def remake_welcome(self):
    	print "Let's remake things!"
    	self.welcome_frame.destroy()
    	self.welcome_frame = self.init_welcome(self.parent)
    
    def update_position(self, matcher):
        interval = matcher.current_interval
        present_measure = interval.measure if interval is not None else 0
        
        if self.cur_measure != present_measure:
            # import traceback
            # traceback.print_stack()
            # print '--> Looks like the new measure in town is %d.' % present_measure
            #self.updates.put(present_measure)
            pass
    
    def check_for_updates(self):
        try:
            while True:
                measure = self.updates.get_nowait()
                self.highlight_measure(measure)
        except QueueEmpty:
            pass
        
        self.parent.after(50, self.check_for_updates)
    
    def init_welcome(self, parent):
        container = Frame(parent, width = 500, height = 500)
        #container.pack_propagate(0)    #Used to stop snapping to widget size
        welcome = Label(container, text = "Welcome to \n Digital Music Stand!", \
            font = ("Trebuchet MS", 24))
        
        music = get_songs()
        
        music_list = Listbox(container, selectmode = SINGLE)
        for piece in music:
            music_list.insert(END, piece)
        
        def get_sel(event):
            index = music_list.curselection()[0]
            text = music_list.get(index)
            self.load_music(text)
        
        music_list.bind('<ButtonRelease-1>', get_sel)
        
        new_song_entry = Entry(container, fg="Red")
        new_song =  Label(container, text = "New Song", \
            font = ("Trebuchet MS", 12))
        lilypond_entry = Entry(container, fg="Red")
        lilypond_file =  Label(container, text = "Lilypond File", \
            font = ("Trebuchet MS", 12))
        current_songs = Label(container, text="Current Songs", \
            font = ('Trebuchet MS', 12))
        
        def get_file_entry():
            #need to also get song name and put it somewhere
            lilypond_file = lilypond_entry.get()
            song_name = new_song_entry.get()
            folder_name = ''
            for word in song_name.lower().split():
                folder_name += word
            create_lilypond_files(lilypond_file, folder_name)
            
            self.folder_name = folder_name
            self.song_folder = os.path.join('songs', folder_name)
            self.lilypond_file = os.path.join(self.song_folder,
                os.path.basename(lilypond_file))
            add_song(song_name)
            self.load_music(song_name)
            
        def make_lilypond():
        	MakeLilyPond(self.parent)
        
        load_button = Button(container, command = get_file_entry, text = "Load",\
            font = ("Trebuchet MS", 10))
        
        
        create_button = Button(container, command = make_lilypond,text="Make",\
        	font = ("Trebuchet MS", 10))
        
        
        container.grid()
        welcome.grid(columnspan=2)
        current_songs.grid(sticky=S+W)
        music_list.grid(column=0, rowspan=5, sticky=W)
        new_song.grid(column=1, row=1, sticky=S)
        new_song_entry.grid(row=2, column=1, sticky=N)
        lilypond_file.grid(row=3, column=1, sticky=S)
        lilypond_entry.grid(row=4, column=1, sticky=N)
        load_button.grid(row=5, column=1, sticky=N)
        create_button.grid(row=6,column=1,sticky=N)
        
        return container

    def load_music(self, title):
        title = title.lower()
        folder = ''
        for word in title.split():
            folder += word
        
        path = get_song_path(folder)
        lilies = glob(os.path.join(path, '*.ly'))
        if not lilies:
            raise RuntimeError('there are no lilies in %s' % folder)
        elif len(lilies) > 1:
            raise RuntimeError('there are too many lilies in %s' % folder)
        
        self.lilypond_file = lilies[0]
        base_filename = os.path.splitext(self.lilypond_file)[0]
        
        ps_file = base_filename + '.ps'
        self.measure_percents, self.ps_info = \
            psprocess.parse_postscript(ps_file)
        self.staff_height = self.ps_info[0]
        self.transition_measures = self.ps_info[1]
        self.line_percents = self.ps_info[2]
        self.image_dir = self.load_images(path)
        self.welcome_frame.destroy()
        self.load_sheetmusic()
        self.song_loaded(self)
        self.options_window = OptionsPane(self.parent, self)
    
    def load_sheetmusic(self):
        try:
            self.cur_image.destroy()
        except:
            pass
        if self.zoomed:
            self.cur_tkimage = ImageTk.PhotoImage(self.image_dir_zoom[0][0])
            self.cur_image = Label(self.parent, image = self.cur_tkimage)
        else:
            self.cur_tkimage = ImageTk.PhotoImage(self.image_dir[0])
            self.cur_image = Label(self.parent, image = self.cur_tkimage)
        self.cur_image.grid()
    
    def load_images(self, path):
        dir_list = None
        try:
            dir_list = os.listdir(path)
        except:
            print 'Song not loaded into program currently.'
            return None
        re_image_types = r'.*\.(gif|jpe?g|png)$'
        pattern = re.compile(re_image_types, re.IGNORECASE)
        dir_list = filter(pattern.search, dir_list)
        dir_list.sort()
        dir_list = [os.path.join(path, filename) for filename in dir_list]
        image_list = [Image.open(image) for image in dir_list]
        self.transparent = Image.open(os.path.join(os.path.dirname(__file__),
            "transparent.png"))

        self.create_zoom_images(image_list, self.lines_per_page)
        image_list = self.resize_images(image_list)
        return image_list
    
    def resize_images(self, images):
        resized_images = []
        for image in images:
            percent = self.screen_height / image.size[1] - .1
            image = image.resize((int(image.size[0]*percent), \
                int(image.size[1]*percent)),
                Image.BILINEAR)
            resized_images.append(image)
        return resized_images
    
    def create_zoom_images(self, images, lines_per):
        #this stuff is so inefficient now, I really should fix it....
        final_pages = []
        self.cur_line = 0
        for j in range(len(images)):
            max_size = -1
            line_percents = self.line_percents[j]
            page = images[j]
            width = page.size[0]
            height = page.size[1]
            top = 0
            bottom = 0
            pages = []
            first_line = -1
            first_line_set = False
            for i in range(-1, len(line_percents), lines_per):
                page_done = False
                if i == -1:
                    top = 0
                else:
                    top = line_percents[i][0]*height
                #need to fix this for going to the next page
                if i+lines_per+1 > len(line_percents)-1:
                    bottom = height
                    page_done = True
                else:
                    bottom = line_percents[i+lines_per+1][1]*height
                zoom = page.crop((0, int(round(top)), width, int(round(bottom))))
                pages.append(zoom)
                
                #doing measure translations
                crop_percent = zoom.size[1]/float(height)
                new_staff_height = self.staff_height/crop_percent
                lines_used = [k for k in range(self.cur_line, self.cur_line+lines_per)]
                if not first_line_set:
                    first_line = self.cur_line
                    first_line_set = True
                ydiff = -1
                mes_temp = -1
                for k in range(len(self.measure_percents)):
                    if self.measure_percents[k][3] in lines_used:
                        ydiff = (self.measure_percents[k][1] - (top/height))
                        temp = ydiff * height
                        yper = temp / zoom.size[1]
                        #Tuple: (x, y, delta-x, line#, staffheight, page)
                        self.zoom_measures.append([self.measure_percents[k][0],\
                            yper, self.measure_percents[k][2], \
                        self.measure_percents[k][3], new_staff_height])
                        mes_temp = k
                self.transition_measures_zoom.append(mes_temp)
                if page_done:
                    break
                self.cur_line += lines_per   
                
            #fix size of first sheet on each page and all measure percentages.
            orig_size = float(pages[0].size[1])
            if len(pages) > 2:
                max_size = pages[1].size[1]
            else:
                max_size = pages[0].size[1]
            per_change = (max_size - orig_size) / float(max_size)
            new_page = Image.new(pages[0].mode,(pages[0].size[0], max_size), 'White')
            first_page = pages[0].copy()
            x_start = 0
            y_start = max_size - first_page.size[1]
            x_end = first_page.size[0]
            y_end = max_size
            new_page.paste(first_page, (x_start, y_start, x_end, y_end))
            pages[0] = new_page
            lines = [l for l in range(first_line, first_line+lines_per)]
            change = int(per_change * max_size)
            for k in range(len(self.zoom_measures)):
                if self.zoom_measures[k][3] in lines:
                    new_y = (self.zoom_measures[k][1]*orig_size + change) / max_size
                    self.zoom_measures[k][1] = new_y
                    new_staff = (self.zoom_measures[k][4]*orig_size) / max_size
                    self.zoom_measures[k][4] = new_staff
                    
            #fix size of last sheet on page and all measure percentages
            orig_size = pages[-1].size[1]
            if orig_size > max_size:
                pages[-1] = pages[-1].crop((0,0, pages[-1].size[0], max_size))
            else:
                per_change = (max_size - orig_size) / float(max_size)
                new_page = Image.new(pages[-1].mode, (pages[-1].size[0], max_size), 'White')
                last_page = pages[-1].copy()
                x_start = 0
                y_start = 0
                x_end = last_page.size[0]
                y_end = orig_size
                new_page.paste(last_page, (x_start, y_start, x_end, y_end))
                pages[-1] = new_page
            lines = [l for l in range(self.cur_line, self.cur_line+lines_per)]
            for k in range(len(self.zoom_measures)):
                if self.zoom_measures[k][3] in lines:
                    new_y = (self.zoom_measures[k][1]*orig_size) / max_size
                    self.zoom_measures[k][1] = new_y
                    new_staff = (self.zoom_measures[k][4]*orig_size) / max_size
                    self.zoom_measures[k][4] = new_staff
            final_pages.append(pages)
            self.cur_line += lines_per
        self.cur_line = 0
        self.image_dir_zoom = final_pages
        
    def next_page_voverlay(self):
        if self.zoomed:
            self.next_page_voverlay_zoomed()
        else:
            next_image_index = self.cur_page_index+1
            cur_image = self.image_dir[self.cur_page_index].copy()
            next_image = self.image_dir[next_image_index].copy()
            self.changing_page = True
            width = next_image.size[0]
            height = self.speed
            while self.changing_page:
                region = next_image.crop((0, 0, width, height))
                cur_image.paste(region, (0, 0, width, height))
                cur_tkimage = ImageTk.PhotoImage(cur_image)
                self.cur_image.destroy()
                self.cur_image = Label(self.parent, image = cur_tkimage)
                self.cur_image.grid()
                height += self.speed
                self.cur_image.update()
                if height >= next_image.size[1]:
                    self.changing_page = False
            self.cur_image.destroy()
            self.cur_tkimage = ImageTk.PhotoImage(next_image)
            self.cur_image = Label(self.parent, \
                image = self.cur_tkimage)
            self.cur_image.grid()
            self.cur_page_index = next_image_index
    
    def next_page_voverlay_zoomed(self):
        next_zoom_index = self.cur_zoom_index + 1
        cur_image = self.image_dir_zoom[self.cur_page_index][self.cur_zoom_index].copy()
        try:
            next_image = self.image_dir_zoom[self.cur_page_index][next_zoom_index].copy()
        except IndexError:
            next_image = self.image_dir_zoom[self.cur_page_index+1][0].copy()
            next_zoom_index = 0
            self.cur_page_index += 1
        self.changing_page = True
        width = next_image.size[0]
        height = self.speed
        while self.changing_page:
            region = next_image.crop((0, 0, width, height))
            cur_image.paste(region, (0, 0, width, height))
            cur_tkimage = ImageTk.PhotoImage(cur_image)
            self.cur_image.destroy()
            self.cur_image = Label(self.parent, image = cur_tkimage)
            self.cur_image.grid()
            height += self.speed
            self.cur_image.update()
            if height >= next_image.size[1]:
                self.changing_page = False
        self.cur_image.destroy()
        self.cur_tkimage = ImageTk.PhotoImage(next_image)
        self.cur_image = Label(self.parent, \
            image = self.cur_tkimage)
        self.cur_image.grid()
        self.cur_zoom_index = next_zoom_index

    def next_page_vslide(self):
        if self.zoomed:
            self.next_page_vslide_zoomed()
        else:
            next_image_index = self.cur_page_index + 1
            cur_image = self.image_dir[self.cur_page_index].copy()
            next_image = self.image_dir[next_image_index].copy()
            self.changing_page = True
            height = self.speed
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
                self.cur_image = Label(self.parent, image = tk_transition)
                self.cur_image.grid()
                height += self.speed
                self.cur_image.update()
                if height >= next_image.size[1]:
                    self.changing_page = False
            self.cur_image.destroy()
            self.cur_tkimage = ImageTk.PhotoImage(next_image)
            self.cur_image = Label(self.parent, \
                image = self.cur_tkimage)
            self.cur_image.grid()
            self.cur_page_index = next_image_index
    
    def next_page_vslide_zoomed(self):
        next_zoom_index = self.cur_zoom_index + 1
        new_page = False
        cur_image = self.image_dir_zoom[self.cur_page_index][self.cur_zoom_index].copy()
        if next_zoom_index == len(self.image_dir_zoom[self.cur_page_index]):
            self.cur_page_index += 1
            next_zoom_index = 0
            new_page = True

        next_image = self.image_dir_zoom[self.cur_page_index][next_zoom_index].copy()
        self.changing_page = True
        height = self.speed
        width = next_image.size[0]
            
        #maybe encapsulate this crap for finding the top
        self.cur_line += self.lines_per_page
        new_top = 0
        not_done = True
        index = 0
        if not new_page:
            while not_done:
                if self.zoom_measures[index][3] == self.cur_line:
                    new_top = int(round((self.zoom_measures[index][1] + \
                        self.zoom_measures[index][4])*next_image.size[1]))
                    not_done = False
                index += 1
        else:
            new_page = False
        diff = abs(cur_image.size[1]-next_image.size[1])
        while self.changing_page:
            transition = Image.new(next_image.mode, next_image.size, 'Green')
            new_region = next_image.crop((0, new_top, width, new_top+height+diff))
            old_region = cur_image.crop((0, height, width, \
                cur_image.size[1]))
            #magic 1s that move the picture up 1 pixel and make it less ugly
            transition.paste(new_region, (0, cur_image.size[1]-height, width, \
                cur_image.size[1]+diff))
            transition.paste(old_region, (0, 0, width, cur_image.size[1]-height))
            self.cur_tkimage = ImageTk.PhotoImage(transition)
            self.cur_image.destroy()
            self.cur_image = Label(self.parent, image = self.cur_tkimage)
            self.cur_image.grid()
            height += self.speed
            self.cur_image.update()
            #if height >= next_image.size[1]-new_top:
            if height >= cur_image.size[1] or height >= next_image.size[1]-new_top:
                self.changing_page = False
        
        self.cur_image.destroy()
        self.cur_tkimage = ImageTk.PhotoImage(next_image)
        self.cur_image = Label(self.parent, \
            image = self.cur_tkimage)
        self.cur_image.grid()
        self.cur_zoom_index = next_zoom_index
    
    def highlight_measure(self, measure):
        if measure >= self.cur_measure:
            self.cur_measure = measure
            if self.zoomed:
                self.highlight_next_measure_zoomed()
            else:
                print '--> Going to measure %d.' % self.cur_measure
                if self.cur_measure + self.num_measures_before_transition in self.transition_measures:
                    self.transition()
                    self.cur_measure += self.num_measures_before_transition
                next_image = self.image_dir[self.cur_page_index].copy()
                im_width, im_height = next_image.size
                x_start = int(self.measure_percents[self.cur_measure][0]*im_width)
                x_end = int(x_start + self.measure_percents[self.cur_measure][2]*im_width)
                y_start = int(self.measure_percents[self.cur_measure][1]*im_height)
                y_end = int((self.measure_percents[self.cur_measure][1]+self.staff_height)*im_height)
                self.transparent = self.transparent.resize((x_end-x_start, y_end-y_start))
                next_image.paste(self.color, (x_start, y_start, x_end, y_end), self.transparent)
                self.cur_tkimage = ImageTk.PhotoImage(next_image)
                self.changing_page = True
                self.cur_image.destroy()
                self.cur_image = Label(self.parent, image = self.cur_tkimage)
                self.cur_image.grid()
                self.cur_image.update()
                self.changing_page = False
    
    def highlight_next_measure_zoomed(self):
        print '--> Going to measure %d.' % self.cur_measure
        if self.cur_measure + self.num_measures_before_transition in self.transition_measures_zoom:
            self.transition()
            self.cur_measure += self.num_measures_before_transition + 1
        next_image = self.image_dir_zoom[self.cur_page_index][self.cur_zoom_index].copy()
        im_width = next_image.size[0]
        im_height = next_image.size[1]
        x_start = int(self.zoom_measures[self.cur_measure][0]*im_width)
        x_end = int(x_start + self.zoom_measures[self.cur_measure][2]*im_width)
        y_start = int(self.zoom_measures[self.cur_measure][1]*im_height)
        y_end = int((self.zoom_measures[self.cur_measure][1] + \
            self.zoom_measures[self.cur_measure][4])*im_height)
        self.transparent = self.transparent.resize((x_end-x_start, y_end-y_start))
        next_image.paste("Red", (x_start, y_start, x_end, y_end), self.transparent)
        self.cur_tkimage = ImageTk.PhotoImage(next_image)
        self.changing_page = True
        self.cur_image.destroy()
        self.cur_image = Label(self.parent, image = self.cur_tkimage)
        self.cur_image.grid()
        self.cur_image.update()
        self.changing_page = False
    
    def highlight_next_measure(self):
        self.highlight_measure(self.cur_measure + 1)
    
    
    def set_transition(self, transition):
        if transition == 'Slide':
            self.transition = self.next_page_vslide
        elif transition == 'Overlay':
            self.transition = self.next_page_voverlay

class OptionsPane(object):
    def __init__(self, parent, display):
        self.parent = parent
        self.display = display
        options = Toplevel(self.parent)
        options.title("Options")
        options.geometry('+900+50')
        self.top_frame = Frame(options)
        self.top_frame.grid()
        
        self.buttons_frame = Frame(self.top_frame)
        self.buttons_frame.grid()
        
        self.v = BooleanVar()
        def set_zoom():
            display.zoomed = self.v.get()
            display.load_sheetmusic()
        
        Radiobutton(self.buttons_frame, text="Regular", variable = self.v, value = False,\
            command = set_zoom).grid()
        Radiobutton(self.buttons_frame, text="Zoomed", variable = self.v, value = True,\
            command = set_zoom).grid()
        
        self.button_next_measure = Button(self.buttons_frame, \
            command = self.display.next_page_vslide, \
            text = "Next Page (slide)")
        self.button_next_measure.grid()
        
        self.button_next_measure2 = Button(self.buttons_frame, \
            command = self.display.next_page_voverlay,\
            text = "New Page (overlay)")
        self.button_next_measure2.grid()
        
        self.button_highlight_next_measure = Button(self.buttons_frame, \
            command = self.display.highlight_next_measure,\
            text = "Highlight Next Measure")
        self.button_highlight_next_measure.grid()
        
        self.v2 = StringVar()
        def set_transition():
            display.set_transition(self.v2.get())

        self.transition_type = Menubutton(self.buttons_frame, text = \
            "Transition", relief = RAISED)
        menu = Menu(self.transition_type)
        menu.add_radiobutton(label = 'Slide', variable = self.v2, \
            command = set_transition)
        menu.add_radiobutton(label = 'Overlay', variable = self.v2,\
            command = set_transition)
        
        self.transition_type.config(menu = menu)
        self.transition_type.grid()


def dln_the_white():
    magic()
    
def magic():
    pass

def create_display(*args, **kwargs):
    root = Tk()
    display = Display(root, *args, **kwargs)
    root.mainloop()

def main():
    root = Tk()
    display = Display(root, 'march.ps', True)
    root.mainloop() 
    
if __name__ == '__main__':
    main()
