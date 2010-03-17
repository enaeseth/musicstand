Piano Hero
==========

["Piano Hero"][website] is an intelligent music stand – a program that displays sheet music on screen, and uses a computer microphone to follow along to you playing the piece on a piano, showing you where you are and turning the page for you.

It was created by a group of class of 2010 Computer Science majors at Carleton College for their senior integrative exercise. It has absolutely no relation to the "Guitar Hero" series of games.

Dependencies
------------

Piano Hero currently only runs on Mac OS X systems, version 10.5 and above. (Running Piano on Intel Macs requires Rosetta for a minor part of the music import toolchain.)

We depend on the following libraries and components:

  - [Python][python] 2.5 or higher, with its compilation headers available. Piano Hero requires CPython and does not run under Jython, IronPython, or any other implementation.
  - [PortAudio][portaudio] v19. It's best to install this using the Subversion trunk or a nightly snapshot of the trunk.
  - [fftw][fftw] v3.2 or newer.
  - [LilyPond][lilypond] 2.12.2, or possibly newer. The LilyPond application bundle should be installed into either the normal Applications folder, or the mstand folder within the project.
  - [Python Imaging Library][pil] 1.1.

Building
--------

Portions of Piano Hero are implemented as a C extension module for Python. To build this module, first ensure that the above dependencies are installed, and then run `make` from inside the top-level project directory.

Running
-------

To launch Piano Hero, run `python musicstand.py` from inside the top-level project directory.


[website]: http://www.pianohero.org/
[python]: http://www.python.org/
[portaudio]: http://www.portaudio.org/
[fftw]: http://www.fftw.org/
[lilypond]: http://www.lilypond.org/
[pil]: http://www.pythonware.com/products/pil/
