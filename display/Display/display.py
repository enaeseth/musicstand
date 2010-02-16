'''
THINGS TO NOTE:
we start measures at 0!


Things to copy from here to main program:
create_zoom_images
next_page_vslide_zoomed
self.cur_line

#need to kill any titles in Lilypond file for image zooming purposes.
'''

from Tkinter import *
import os, sys
import re
import Image, ImageTk
import psprocess
import time

class Display(object):
    def __init__(self, parent, directory, ps_filename, DEBUG=False):
        self.parent = parent
        self.parent.title("Digital Music Stand")
        self.parent.geometry('+0+0')
        self.screen_width = float(self.parent.winfo_screenwidth())
        self.screen_height = float(self.parent.winfo_screenheight())
        self.image_dir = None
        self.tkimage_dir = None
        self.cur_image = None
        self.cur_tkimage = None
        self.options_window = None
        self.lilypond_file = None
        self.image_dir_zoom = None
        self.measure_percents, self.ps_info = psprocess.parse_postscript(ps_filename)
        self.staff_height = self.ps_info[0]
        self.line_percents = self.ps_info[2]
        self.zoom_measures = []
        self.lines_per_page = 1
        self.playing = False
        self.cur_measure = -1
        self.cur_page_index = 0
        self.cur_zoom_index = 0
        self.zoomed = True
        self.debug = DEBUG
        self.transparent = None
        self.zoom_staff_height = -1
        self.cur_line = 0
        
        
        menubar = Menu(self.parent)
        menubar.add_command(label="YEEEEAAAAHHHH", \
            command=self.parent.quit)
        self.parent.config(menu=menubar)
        
        self.welcome_frame = self.init_welcome(self.parent)
    
    def init_welcome(self, parent):
        container = Frame(parent, width = 500, height = 500)
        #container.pack_propagate(0)    #Used to stop snapping to widget size
        welcome = Label(container, text = "Welcome to \n Digital Music Stand!", \
            font = ("Trebuchet MS", 24))
        
        file = open("config.txt")
        music = []
        for line in file:
            music.append(line.strip())
        
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
            self.lilypond_file = lilypond_entry.get()
            #regex checking for .ly extension
        
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
        path = './songs/'+folder
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
        
    def load_images(self, path):
        dir_list = None
        try:
            dir_list = os.listdir(path)
        except:
            print 'Song not loaded into program currently.'
            return None
        re_image_types = '.*.gif$|.*.jpg$|.*.png$|.*.jpeg$'
        pattern = re.compile(re_image_types, re.IGNORECASE)
        dir_list = filter(pattern.search, dir_list)
        image_list = [Image.open(image) for image in dir_list]
        self.transparent = Image.open("transparent.png")
        if self.zoomed:
            self.create_zoom_images(image_list, self.lines_per_page)
        return image_list
    
    def resize_images(self, images):
        resized_images = []
        for image in images:
            percent = self.screen_height / image.size[1]
            image = image.resize((int(image.size[0]*percent), \
                int(image.size[1]*percent)),
                Image.BILINEAR)
            resized_images.append(image)
        return resized_images
    
    def create_zoom_images(self, images, lines_per):
        #this stuff is so inefficient now, I really should fix it....
        final_pages = []
        max_set = False
        max_size = -1
        self.cur_line = 0
        for j in range(len(images)):
            line_percents = self.line_percents[j]
            page = images[j]
            width = page.size[0]
            height = page.size[1]
            top = 0
            bottom = 0
            pages = []
            first_measure_of_page = -1
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
                print new_staff_height
                lines_used = [k for k in range(self.cur_line, self.cur_line+lines_per)]
                ydiff = -1
                for k in range(len(self.measure_percents)):
                    if self.measure_percents[k][3] in lines_used:
                        ydiff = (self.measure_percents[k][1] - (top/height))
                        temp = ydiff * height
                        yper = temp / zoom.size[1]
                        #Tuple: (x, y, delta-x, line#, staffheight, page)
                        self.zoom_measures.append([self.measure_percents[k][0],\
                            yper, self.measure_percents[k][2], \
                        self.measure_percents[k][3], new_staff_height, j])
                
                if page_done:
                    break
                self.cur_line += lines_per
                
            #fix size of first sheet on each page and all measure percentages.
            orig_size = float(pages[0].size[1])
            if not max_set:
                max_size = float(pages[1].size[1])
                max_set = True
            per_change = (max_size - orig_size) / max_size
            new_page = Image.new(pages[0].mode,(pages[0].size[0], max_size), 'White')
            first_page = pages[0].copy()
            x_start = 0
            y_start = int(max_size - first_page.size[1])
            x_end = int(first_page.size[0])
            y_end = int(max_size)
            new_page.paste(first_page, (x_start, y_start, x_end, y_end))
            pages[0] = new_page
            lines = [l for l in range(0, lines_per)]
            change = int(per_change * max_size)
            for k in range(len(self.zoom_measures)):
                if self.zoom_measures[k][3] in lines and self.zoom_measures[k][5] == j:
                    #fix  y-percentage and staff height
                    new_y = (self.zoom_measures[k][1]*orig_size + change) / max_size
                    self.zoom_measures[k][1] = new_y
                    new_staff = (self.zoom_measures[k][4]*orig_size) / max_size
                    self.zoom_measures[k][4] = new_staff
                    
            #fix size of last page and all measure percentages
            orig_size = float(pages[-1].size[1])
            if orig_size > max_size:
                pages[-1] = pages[-1].crop((0,0, pages[-1].size[0], max_size))
            else:
                per_change = (max_size - orig_size) / max_size
                new_page = Image.new(pages[-1].mode, pages[1].size, 'White')
                last_page = pages[-1].copy()
                x_start = 0
                y_start = 0
                x_end = int(last_page.size[0])
                y_end = int(orig_size)
                new_page.paste(last_page, (x_start, y_start, x_end, y_end))
                pages[-1] = new_page
            lines = [l for l in range(self.cur_line, self.cur_line+lines_per)]
            for k in range(len(self.zoom_measures)):
                if self.zoom_measures[k][3] in lines and self.zoom_measures[k][5] == j:
                    new_y = (self.zoom_measures[k][1]*orig_size) / max_size
                    self.zoom_measures[k][1] = new_y
                    new_staff = (self.zoom_measures[k][4]*orig_size) / max_size
                    self.zoom_measures[k][4] = new_staff
            final_pages.append(pages)
            self.cur_line += lines_per
            #so we know when we're heading to a new page.
            #final_pages.append("NEW_PAGE")
        self.cur_line = 0
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
        new_page = False
        cur_image = self.image_dir_zoom[self.cur_page_index][self.cur_zoom_index].copy()
        if next_zoom_index == len(self.image_dir_zoom[self.cur_page_index]):
            self.cur_page_index += 1
            next_zoom_index = 0
            new_page = True

        next_image = self.image_dir_zoom[self.cur_page_index][next_zoom_index].copy()
        self.changing_page = True
        height = speed
        width = next_image.size[0]
            
        #maybe encapsulate this crap for finding the top
        self.cur_line += self.lines_per_page
        new_top = 0
        not_done = True
        index = 0
        if not new_page:
            while not_done:
                #print self.zoom_measures[index][3]
                if self.zoom_measures[index][3] == self.cur_line:
                    new_top = (self.zoom_measures[index][1] + \
                        self.zoom_measures[index][4])*next_image.size[1]
                    not_done = False
                index += 1
        else:
            new_page = False
        #transition = Image.new(next_image.mode, next_image.size, 'Pink')
        while self.changing_page:
            #if self.cur_page_index == 1:
            #x = raw_input('hit enter')
            transition = Image.new(next_image.mode, next_image.size, 'Green')
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
    
    def highlight_next_measure(self):
        if self.zoomed:
            self.highlight_next_measure_zoomed()
        else:
            next_image = self.image_dir[self.cur_page_index].copy()
            im_width = next_image.size[0]
            im_height = next_image.size[1]
            self.cur_measure += 1
            x_start = int(self.measure_percents[self.cur_measure][0]*im_width)
            x_end = int(x_start + self.measure_percents[self.cur_measure][2]*im_width)
            y_end = int((self.measure_percents[self.cur_measure][1]+self.staff_height)*im_height)
            y_start = int(self.measure_percents[self.cur_measure][1]*im_height)
            self.transparent = self.transparent.resize((x_end-x_start, y_end-y_start))
            next_image.paste("Red", (x_start, y_start, x_end, y_end), self.transparent)
            #next_image.paste(self.transparent, (0,0,10,10), self.transparent)
            #so you have to save the image displayed somewhere permenent, otherwise
            #it goes bye bye.
            self.cur_tkimage = ImageTk.PhotoImage(next_image)
            self.changing_page = True
            self.cur_image.destroy()
            self.cur_image = Label(self.parent, image = self.cur_tkimage)
            self.cur_image.grid()
            self.cur_image.update()
            self.changing_page = False
            
    def highlight_next_measure_zoomed(self):
        next_image = self.image_dir_zoom[self.cur_page_index][self.cur_zoom_index].copy()
        im_width = next_image.size[0]
        im_height = next_image.size[1]
        self.cur_measure += 1
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
    
class OptionsPane(object):
    def __init__(self, parent, display):
        self.parent = parent
        self.display = display
        options = Toplevel(self.parent)
        options.title("Options")
        options.geometry('+900+40')
        self.top_frame = Frame(options)
        self.top_frame.grid()
        c = Checkbutton(self.top_frame, text="check this shit yo")
        c.grid()
        
        self.buttons_frame = Frame(self.top_frame)
        self.buttons_frame.grid()
        
        self.button_next_measure = Button(self.buttons_frame, \
            command = lambda speed = 5: self.display.next_page_vslide(speed), \
            text = "Next Page (slide)")
        self.button_next_measure.grid()
        
        self.button_next_measure2 = Button(self.buttons_frame, \
            command = lambda speed = 5: self.display.next_page_voverlay(speed),\
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

def main():
    root = Tk()
    display = Display(root, 'whatever', 'march.ps', True)
    root.mainloop()
    
if __name__ == '__main__':
    main()