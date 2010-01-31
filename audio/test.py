# encoding: utf-8

import audio
import time

if __name__ == '__main__':
    # input_devices = [d for d in audio.get_devices() if d.input_channels > 0]
    
    filters = [
        audio.CutoffFilter(4200.0),
        audio.CoalesceFilter()
    ]
    
    listener = audio.Listener(window_size=4096*2, interval=1024,
        filters=filters)
    
    queue = listener.start()
    while True:
        try:
            offset, buckets, data = queue.pop()
            good = 0
            for freq, intensity in buckets:
                if intensity >= 20.0:
                    good += 1
                    bar = '=' * int(40 * (intensity / 110.0))
                    print "%6.01f:   %6.02f %s" % (freq, intensity, bar)
            if good > 0:
                print
        except KeyboardInterrupt:
            print
            listener.stop()
            break
