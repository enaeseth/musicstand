#This thing opens files. It has one function, for whatever reason.
#If it eats its vegetables, someday it will grow up and be able to close files too.

import os

def openPage(measNum):
		pdfname = "page"+str(measNum)+".pdf"
		os.system("open "+ pdfname)