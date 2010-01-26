/**
 * Listens to an audio input device and performs frequency decomposition.
 */

#ifndef _LISTEN_H_
#define _LISTEN_H_

#include <Python.h>
#include <portaudio.h>
#include <fftw3.h>
#include <pthread.h>
#include "queue.h"

typedef float sample_t;

typedef struct {
    PyObject_HEAD
    Py_ssize_t window_size;
    Py_ssize_t interval;
    double sample_rate;
    PaStream* stream;
    PaDeviceIndex device;
    
    int active;
    pthread_t analysis_thread;
    pthread_mutex_t sync;
    pthread_cond_t ready_for_fft;
    
    fftw_plan plan;
    size_t staging_buffer_size;
    size_t samples_collected;
    sample_t* staging_buffer;
    sample_t* staging_buffer_end;
    sample_t* staging_area;
    sample_t* staging_fft_position;
    sample_t* fft_buffer;
    QueueObject* result_queue;
} ListenerObject;

extern PyTypeObject ListenerType;

#endif /* end of include guard: _LISTEN_H_ */
