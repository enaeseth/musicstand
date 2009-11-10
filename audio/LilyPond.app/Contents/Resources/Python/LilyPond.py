"""LilyPond.py -- A minimal Document-based Cocoa application."""

from PyObjCTools import NibClassBuilder, AppHelper
from Foundation import NSBundle, NSURL
from AppKit import NSWorkspace, NSDocumentController, NSDocument
import AppKit

NibClassBuilder.extractClasses("TinyTinyDocument")

import URLHandlerClass
import subprocess
import os
import glob
import string
import re
import urllib

from ProcessLog import ProcessLogWindowController

firstStart = True
debug = False

# utility functions
def open_url (url):
        workspace = NSWorkspace.sharedWorkspace ()

        nsurl = NSURL.URLWithString_ (url)
        workspace.openURL_ (nsurl)

def lily_version ():
        bundle =  NSBundle.mainBundle ()
        appdir = NSBundle.mainBundle().bundlePath()
	share = appdir + '/Contents/Resources/share/lilypond'

	if not os.path.exists (share):
		share = os.environ['HOME'] + '/Desktop/LilyPond.app/Contents/Resources/share/lilypond'
		
        pattern = share + '/[0-9]*'
	
        versions = glob.glob (pattern)
        version = '2.8.0' 
        if versions:
            version = versions[0]
	    version = os.path.split(version)[1]
        
        return tuple (string.split (version, '.'))

def google_lilypond (str):
        (maj,min,pat) = lily_version ()

        url = '%s site:lilypond.org v%s.%s' % (str, maj, min)
        url = re.sub (' ', '+', url)
        url = urllib.quote (url, safe='+')
        url = 'http://www.google.com/search?q=%s' % url
        open_url (url)


# class defined in TinyTinyDocument.nib
class TinyTinyDocument(NibClassBuilder.AutoBaseClass):
    # the actual base class is NSDocument
    # The following outlets are added to the class:
    # textView

    startupPath = None  # fallback if instance has no startupPath.
    def init (self):
	self = NSDocument.init (self)
	self.processLogWindowController = None
	return self
    
    def windowNibName(self):
        return "TinyTinyDocument"

    def readFromFile_ofType_(self, path, tp):
        if self.textView is None:
            # we're not yet fully loaded
            self.startupPath = path
        else:
            # "revert"
            self.readFromUTF8(path)
            
        return True

    def writeToFile_ofType_(self, path, tp):
        f = file(path, "w")
        text = self.textView.string()
        f.write(text.encode("utf8"))
        f.close()

        return True

    def windowControllerDidLoadNib_(self, controller):
        global firstStart
        if self.startupPath:
            self.readFromUTF8 (self.startupPath)
        elif firstStart:
	    appdir = NSBundle.mainBundle().bundlePath()
	    prefix = appdir + "/Contents/Resources"
	    self.readFromUTF8 (prefix + '/Welcome-to-LilyPond-MacOS.ly')
	    
	firstStart = False
	    
    def readFromUTF8(self, path):
        f = file(path)
        text = unicode(f.read(), "utf8")
        f.close()
        self.textView.setString_(text)

    def compileFile_ (self, sender):
        if 0:
            self.saveDocumentWithDelegate_didSaveSelector_contextInfo_ (self,
                                                                        "compileDidSaveSelector:",
                                                                        None)
        if self.fileName():
            self.compileMe ()
        else:
            self.saveDocument_ (None)

    def updateSyntax_(self, sender):
        if self.fileName():
            self.updateMySyntax ()
        else:
            self.saveDocument_ (None)

    def processLogClosed_ (self, data):
	    self.processLogWindowController = None
	    
    def createProcessLog (self):
        if not self.processLogWindowController:
            wc = ProcessLogWindowController()
	    self.processLogWindowController = wc
	    center = NSWorkspace.sharedWorkspace().notificationCenter()
	    notification = AppKit.NSWindowWillCloseNotification
#	    center.addObserver_selector_name_object_(self, "processLogClosed:",
#						     notification,
#						     wc.window ())

	    wc.close_callback = self.processLogClosed_
        else:
            self.processLogWindowController.showWindow_ (None)

    def compileDidSaveSelector_ (doc, didSave, info):
        print "I'm here"
        if didSave:
            doc.compileMe ()

    def revert_ (self, sender):
        self.readFromUTF8 (self.fileName ())

    def updateMySyntax (self):
        env = os.environ.copy()
        bundle =  NSBundle.mainBundle ()
        appdir = NSBundle.mainBundle().bundlePath()
        prefix = appdir + '/Contents/Resources'
        env['LILYPONDPREFIX'] = prefix + '/share/lilypond/current' 
            
        self.writeToFile_ofType_(self.fileName (), None)
        binary = prefix + '/bin/convert-ly'

        pyproc = subprocess.Popen ([binary, '-e', self.fileName ()],
                                   env = env,
                                   stderr = subprocess.STDOUT,
                                   stdout = subprocess.PIPE,
                                   )
        self.createProcessLog ()
        wc = self.processLogWindowController
        wc.setWindowTitle_ ('convert-ly -- ' + self.fileName())
        wc.runProcessWithCallback (pyproc, self.revert_)
        
    def compileMe (self):
        bundle =  NSBundle.mainBundle ()
	try:
	    appdir = os.environ['LILYPOND_DEBUG_APPDIR']
	except KeyError:
	    appdir = NSBundle.mainBundle().bundlePath()
	executable = appdir + '/Contents/Resources/bin/lilypond'
	args = [executable]
	if debug:
		args += ['--verbose']
	args += [self.fileName()]
	dest = os.path.split (self.fileName())[0]
        call = subprocess.Popen (executable = executable,
				 args = args,
				 cwd = dest,
				 stdout = subprocess.PIPE,
				 stderr = subprocess.STDOUT,
				 shell = False)
		

        self.createProcessLog ()
	wc = self.processLogWindowController
	wc.setWindowTitle_ ('LilyPond -- ' + self.fileName())
	wc.runProcessWithCallback (call, self.open_pdf)
	
    def open_pdf (self, data):
	pdf_file = os.path.splitext (self.fileName())[0] + '.pdf'
	if os.path.exists (pdf_file):
		b = '/usr/bin/open'
		args = [b, pdf_file]
		os.spawnv (os.P_NOWAIT, b, args)
	
    def contextHelp_ (self, sender):
        tv = self.textView
        r = tv.selectedRange ()
        
        if r.length == 0:
            (maj,min,pat) = lily_version ()
            open_url ('http://lilypond.org/doc/v%s.%s' % (maj, min))
        else:
            substr = tv.string()[r.location:r.location + r.length]
            google_lilypond (substr)


if __name__ == "__main__":
    AppHelper.runEventLoop()
