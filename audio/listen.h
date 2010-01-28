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
#include "ringbuffer.h"

typedef float sample_t;

#ifdef SINGLE_PRECISION_FFT
typedef float fft_sample_t;
#else
typedef double fft_sample_t;
#endif

typedef struct {
    PyObject_HEAD
    size_t window_size;
    size_t interval;
    double interval_ratio; // (interval / window_size) as a double
    double sample_rate;
    double sample_duration;
    PaStream* stream;
    PaDeviceIndex device;
    
    int active;
    pthread_t analysis_thread;
    pthread_mutex_t sync;
    pthread_cond_t ready_for_fft;
    
#ifdef SINGLE_PRECISION_FFT
    fftwf_plan plan;
#else
    fftw_plan plan;
#endif

    ringbuffer_t staging_buffer;
    fft_sample_t* fft_buffer;
    fft_sample_t* fft_result_buffer;
    AudioQueueObject* result_queue;
} ListenerObject;

extern PyTypeObject ListenerType;

#endif /* end of include guard: _LISTEN_H_ */
