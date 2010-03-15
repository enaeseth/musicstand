all: mstand/audio.so

mstand/audio.so:
	python audio/setup.py build_ext -b mstand

clean:
	rm -f mstand/audio.so
