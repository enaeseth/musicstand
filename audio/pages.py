#This thing opens files. It has one function, for whatever reason.
#If it eats its vegetables, someday it will grow up and be able to close files too.

import os

def open_page(measure_number):
    os.system('open page1.%d.pdf' % measure_number)
