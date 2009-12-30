#This thing opens files. It has one function, for whatever reason.
#If it eats its vegetables, someday it will grow up and be able to close files too.

import os

def open_page(filename, measure_number, cache_dir):
    base, ext = os.path.splitext(os.path.basename(filename))
    path = os.path.join(cache_dir, '%s.%d.pdf' % (base, measure_number))
    os.system('open "%s"' % path)
