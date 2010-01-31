from distutils.core import setup, Extension

setup(name="audio", version="1.0",
      ext_modules=[Extension("audio",
        ["audio.c", "devices.c", "queue.c", "ringbuffer.c", "filter.c",
            "filters/freq_cutoff.c", "listen.c"],
        extra_compile_args=['-std=gnu99', '-Wall', '-fno-inline'],
        define_macros=[('DEBUG', None)],
        # define_macros=[('DEBUG', None), ('Py_DEBUG', None)],
        include_dirs=['/usr/local/include', '/opt/local/include'],
        library_dirs=['/usr/local/lib', '/opt/local/lib'],
        libraries=['pthread', 'portaudio', 'fftw3', 'm'])])
