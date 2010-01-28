# encoding: utf-8

import audio
import time

if __name__ == '__main__':
    # input_devices = [d for d in audio.get_devices() if d.input_channels > 0]
    
    raw_input("Hit Return to start.")
    
    listener = audio.Listener(window_size=4096*2, interval=1024)
    
    queue = listener.start()
    while True:
        try:
            print queue.pop()
        except KeyboardInterrupt:
            print
            listener.stop()
            break
