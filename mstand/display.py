'''
THINGS TO NOTE:
-we start measures at 0!
-config file currently being overwritten when new song is loaded

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

class Display(object):
    def __init__(self, parent, song_loaded, DEBUG=False):
        self.parent = parent
        self.parent.title("Digital Music Stand")
        self.parent.geometry('+50+500')
        self.screen_width = float(self.parent.winfo_screenwidth())
        self.screen_height = float(self.parent.winfo_screenheight())
        self.image_dir = None
        self.tkimage_dir = None
        self.cur_image = None
        self.cur_tkimage = None
        self.options_window = None
        self.lilypond_file = 'march.ly'
        self.image_dir_zoom = None
        self.measure_percents = None 
        self.ps_info = None
        self.zoom_measures = []
        self.lines_per_page = 2
        self.playing = False
        self.cur_measure = -1
        self.cur_page_index = 0
        self.cur_zoom_index = 0
        self.zoomed = False
        self.debug = DEBUG
        self.transparent = None
        
        self.updates = Queue(0)
        self.song_loaded = song_loaded
        
        menubar = Menu(self.parent)
        menubar.add_command(label="YEEEEAAAAHHHH", \
            command=self.parent.quit)
        self.parent.config(menu=menubar)
        
        self.welcome_frame = self.init_welcome(self.parent)
        self.parent.after(50, self.check_for_updates)
    
    def update_position(self, matcher):
        interval = matcher.current_interval
        present_measure = interval.measure if interval is not None else 0
        
        if self.cur_measure != present_measure:
            # import traceback
            # traceback.print_stack()
            # print '--> Looks like the new measure in town is %d.' % present_measure
            self.updates.put(present_measure)
    
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
            
        
        load_button = Button(container, command = get_file_entry, text = "Load",\
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
        self.line_percents = self.ps_info[2]
        self.image_dir = self.load_images(path)
        #self.image_dir = self.resize_images(self.image_dir)
        # self.tkimage_dir = [ImageTk.PhotoImage(image) for image in \
                            # self.image_dir]
        self.welcome_frame.destroy()
        if self.zoomed:
            self.cur_tkimage = ImageTk.PhotoImage(self.image_dir_zoom[0][0])
            self.cur_image = Label(self.parent, image = self.cur_tkimage)
        else:
            self.cur_tkimage = ImageTk.PhotoImage(self.image_dir[0])
            self.cur_image = Label(self.parent, image = self.cur_tkimage)
        self.cur_image.grid()
        self.options_window = OptionsPane(self.parent, self)
        self.song_loaded(self)
    
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
        dir_list = [os.path.join(path, filename) for filename in dir_list]
        image_list = [Image.open(image) for image in dir_list]
        self.transparent = Image.open(os.path.join(os.path.dirname(__file__),
            "transparent.png"))
        if self.zoomed:
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
        final_pages = []
        for j in range(len(images)):
                line_percents = self.line_percents[j]
                page = images[j]
                width = page.size[0]
                height = page.size[1]
                top = 0
                bottom = 0
                pages = []
                for i in range(-1, len(line_percents), lines_per):
                    if i == -1:
                        top = 0
                    else:
                        top = line_percents[i][0]*height
                    #need to fix this for going to the next page
                    if i+lines_per+1 > len(line_percents)-1:
                        bottom = height
                    else:
                        bottom = line_percents[i+lines_per+1][1]*height
                    zoom = page.crop((0, int(top), width, int(bottom)))
                    pages.append(zoom)
                    
                    #doing measure translations
                    crop_percent = zoom.size[1]/float(height)
                    #need to save this staff height somewhere, but different
                    #for different zoomed sections
                    new_staff_height = self.staff_height/crop_percent
                    lines_used = [k for k in range(i+1, i+lines_per+1)]
                    ydiff = -1
                    for k in range(len(self.measure_percents)):
                        if self.measure_percents[k][3] in lines_used:
                            ydiff = (self.measure_percents[k][1] - top)
                        self.zoom_measures.append((self.measure_percents[k][0],\
                            ydiff, self.measure_percents[k][2], \
                            self.measure_percents[k][3]))
                
                final_pages.append(pages)
        self.image_dir_zoom = final_pages

    def next_page_voverlay(self, speed):
        if self.zoomed:
            pass
        else:
            next_image_index = self.cur_page_index+1
            cur_image = self.image_dir[self.cur_page_index].copy()
            next_image = self.image_dir[next_image_index].copy()
            self.changing_page = True
            width = next_image.size[0]
            height = speed
            while self.changing_page:
                region = next_image.crop((0, 0, width, height))
                cur_image.paste(region, (0, 0, width, height))
                cur_tkimage = ImageTk.PhotoImage(cur_image)
                self.cur_image.destroy()
                self.cur_image = Label(self.parent, image = cur_tkimage)
                self.cur_image.grid()
                height += speed
                self.cur_image.update()
                if height == next_image.size[1]:
                    self.changing_page = False
            self.cur_image.destroy()
            self.cur_tkimage = ImageTk.PhotoImage(next_image)
            self.cur_image = Label(self.parent, \
                image = self.cur_tkimage)
            self.cur_image.grid()
            self.cur_page_index = next_image_index
        
    def next_page_vslide(self, speed):
        if self.zoomed:
            self.next_page_vslide_zoomed(speed)
        else:
            next_image_index = self.cur_page_index + 1
            cur_image = self.image_dir[self.cur_page_index].copy()
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
                self.cur_image = Label(self.parent, image = tk_transition)
                self.cur_image.grid()
                height += speed
                self.cur_image.update()
                if height >= next_image.size[1]:
                    self.changing_page = False
            self.cur_image.destroy()
            self.cur_tkimage = ImageTk.PhotoImage(next_image)
            self.cur_image = Label(self.parent, \
                image = self.cur_tkimage)
            self.cur_image.grid()
            self.cur_page_index = next_image_index
    
    def next_page_vslide_zoomed(self, speed):
        next_zoom_index = self.cur_zoom_index + 1
        cur_image = self.image_dir_zoom[self.cur_page_index][self.cur_zoom_index].copy()
        next_image = self.image_dir_zoom[self.cur_page_index][next_zoom_index].copy()
        self.changing_page = True
        height = speed
        width = next_image.size[0]
        
        #maybe encapsulate this crap for finding the top
        new_first_line = (next_zoom_index * self.lines_per_page)
        new_top = None
        not_done = True
        index = 0
        while not_done:
            if self.zoom_measures[index][3] == new_first_line:
                new_top = self.zoom_measures[index][1]*next_image.size[1]
                not_done = False
            index += 1
        
        while self.changing_page:
            #print 'height', height
            #print 'next image', next_image.size[1]-new_top
            #print 'new top', new_top
            transition = Image.new(next_image.mode, next_image.size)
            
            new_region = next_image.crop((0, int(new_top), width, int(new_top+height)))
            
            
            old_region = cur_image.crop((0, height, width, \
                cur_image.size[1]))
            transition.paste(new_region, (0, next_image.size[1]-height, width, \
                next_image.size[1]))
            transition.paste(old_region, (0, 0, width, cur_image.size[1]-height))
            self.cur_tkimage = ImageTk.PhotoImage(transition)
            self.cur_image.destroy()
            self.cur_image = Label(self.parent, image = self.cur_tkimage)
            self.cur_image.grid()
            height += speed
            self.cur_image.update()
            if height >= next_image.size[1]-new_top:
                self.changing_page = False
        
        self.cur_image.destroy()
        self.cur_tkimage = ImageTk.PhotoImage(next_image)
        self.cur_image = Label(self.parent, \
            image = self.cur_tkimage)
        self.cur_image.grid()
        self.cur_zoom_index = next_zoom_index
        #need to update page if we change pages
    
    def highlight_measure(self, measure):
        # import traceback
        # traceback.print_stack()
        print '--> Going to measure %d.' % measure
        next_image = self.image_dir[self.cur_page_index].copy()
        im_width, im_height = next_image.size
        x_start = int(self.measure_percents[measure][0]*im_width)
        x_end = int(x_start + self.measure_percents[measure][2]*im_width)
        y_start = int(self.measure_percents[measure][1]*im_height)
        y_end = int((self.measure_percents[measure][1]+self.staff_height)*im_height)
        self.transparent = self.transparent.resize((x_end-x_start, y_end-y_start))
        next_image.paste("Red", (x_start, y_start, x_end, y_end), self.transparent)
        self.cur_tkimage = ImageTk.PhotoImage(next_image)
        self.changing_page = True
        self.cur_image.destroy()
        self.cur_image = Label(self.parent, image = self.cur_tkimage)
        self.cur_image.grid()
        self.cur_image.update()
        self.changing_page = False
        self.cur_measure = measure
    
    def highlight_next_measure(self):
        self.highlight_measure(self.cur_measure + 1)
    

class OptionsPane(object):
    def __init__(self, parent, display):
        self.parent = parent
        self.display = display
        options = Toplevel(self.parent)
        options.title("Options")
        options.geometry('+900+50')
        self.top_frame = Frame(options)
        self.top_frame.grid()
        c = Checkbutton(self.top_frame, text="check this shit yo")
        c.grid()
        
        self.buttons_frame = Frame(self.top_frame)
        self.buttons_frame.grid()
        
        self.button_next_measure = Button(self.buttons_frame, \
            command = lambda speed = 10: self.display.next_page_vslide(speed), \
            text = "Next Page (slide)")
        self.button_next_measure.grid()
        
        self.button_next_measure2 = Button(self.buttons_frame, \
            command = lambda speed = 10: self.display.next_page_voverlay(speed),\
            text = "New Page (overlay)")
        self.button_next_measure2.grid()
        
        self.button_highlight_next_measure = Button(self.buttons_frame, \
            command = self.display.highlight_next_measure,\
            text = "Highlight Next Measure")
        self.button_highlight_next_measure.grid()
        
        self.listbox = Listbox(self.top_frame)
        for picture in self.display.image_dir:
            self.listbox.insert(END, str(picture.size))
        self.listbox.grid()

        self.menubutton = Menubutton(self.top_frame, text="Look!",\
            relief=RAISED)
        menu = Menu(self.menubutton)
        menu.add_command(label="Made")
        menu.add_command(label="You")
        menu.add_command(label="Look")
        self.menubutton.config(menu=menu)
        self.menubutton.grid()

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
    display = Display(root, 'whatever', 'march.ps', True)
    root.mainloop() 
    
if __name__ == '__main__':
    main()
