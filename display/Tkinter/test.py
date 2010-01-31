from Tkinter import *
import os, sys
import re
import Image, ImageTk

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
    x = size[0]*0.38398
    y = size[1]*0.05858
    print x
    print y
    #image_list[0].paste("Red", (x, y, x+20, y+20))
    #image_list[0].save('march.png')
    display = PageDisplay(root, image_list)
    root.title('YEEEEEEEEEAAAAAAAAHHHHH')

    root.mainloop()
    
if __name__ == '__main__':
    main()