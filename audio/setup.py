from distutils.core import setup, Extension

setup(name="playground", version="1.0",
      ext_modules=[Extension("audio",
        ["audio.c", "devices.c", "queue.c", "listen.c"],
        define_macros=[('DEBUG', None)],
        include_dirs=['/opt/local/include'],
        library_dirs=['/opt/local/lib'],
        libraries=['pthread', 'portaudio', 'fftw3', 'm'])])
