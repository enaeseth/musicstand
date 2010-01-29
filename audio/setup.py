from distutils.core import setup, Extension

setup(name="audio", version="1.0",
      ext_modules=[Extension("audio",
        ["audio.c", "devices.c", "queue.c", "ringbuffer.c", "listen.c"],
        extra_compile_args=['-std=gnu99', '-Wall'],
        define_macros=[('DEBUG', None)],
        include_dirs=['/opt/local/include'],
        library_dirs=['/opt/local/lib'],
        libraries=['pthread', 'portaudio', 'fftw3', 'm'])])
