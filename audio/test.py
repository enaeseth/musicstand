# encoding: utf-8

import audio
import time

if __name__ == '__main__':
    # input_devices = [d for d in audio.get_devices() if d.input_channels > 0]
    
    listener = audio.Listener(window_size=4096*2, interval=1024)
    
    queue = listener.start()
    while True:
        try:
            buckets = queue.pop()
            notable = []
            for data in buckets:
                freq, intensity = data[1:3]
                if freq >= 4200:
                    break
                if intensity >= 5.0:
                    notable.append(freq)
            
            if len(notable) > 0:
                for data in buckets:
                    freq, intensity = data[1:3]
                    if any(abs(nf - freq) <= 5.0 for nf in notable):
                        print "%.02f:\t%.03f" % data[1:3]
                print '-' * 40
        except KeyboardInterrupt:
            print
            listener.stop()
            break
