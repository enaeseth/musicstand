from distutils.core import setup, Extension
import os.path

files = ["audio.c", "devices.c", "queue.c", "ringbuffer.c", "filter.c",
    "listen.c", "filters/freq_cutoff.c", "filters/coalesce.c",
    "filters/negative.c"]

audio_dir = os.path.dirname(__file__)
files = [os.path.join(audio_dir, filename) for filename in files]

setup(name="audio", version="1.0",
      ext_modules=[Extension("audio", files,
        extra_compile_args=['-std=gnu99', '-Wall', '-fno-inline'],
        define_macros=[('DEBUG', None)],
        # define_macros=[('DEBUG', None), ('Py_DEBUG', None)],
        include_dirs=['/usr/local/include', '/opt/local/include'],
        library_dirs=['/usr/local/lib', '/opt/local/lib'],
        libraries=['pthread', 'portaudio', 'fftw3', 'm'])])
