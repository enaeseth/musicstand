#This thing will probably turn into a Perl script when it grows up.
#For now, it is what it is.
#Emily and Ben, 10/25/09

import os

os.system("python lilypondParser.py test.ly")

#Make Eric/David's thing start. The other people can work out how
#to combine this Nathan/Emma

#Nathan/Emma's thing, returns a measure number. Call it measNum. The rest of
#this program needs to run every time we get something from Nathan/Emma.
measNum = 10
pdfname = "test"+str(measNum)+".pdf"
os.system("open "+pdfname)