/**
 * A blocking queue specifically for passing FFT results to the upper layers
 * of the program.
 *
 * Uses fine-grained locking, so that the GIL need not be held to execute
 * a push.
 */

#ifndef _QUEUE_H_
#define _QUEUE_H_

#include <Python.h>
#include <pthread.h>

typedef PyObject* (*user_data_wake_cb)(const void* user_data);

typedef struct {
    double offset;
    double frequency;
    double intensity;
    const void* user_data;
} bucket_t;

typedef struct fft_result {
    Py_ssize_t length;
    Py_ssize_t capacity;
    bucket_t* buckets;
    struct fft_result* next;
} fft_result_t;

typedef struct {
    PyObject_HEAD
    user_data_wake_cb waker;
    int no_memory;
    pthread_mutex_t mutex;
    pthread_cond_t condition;
    Py_ssize_t length;
    fft_result_t* head;
    fft_result_t* tail;
} AudioQueueObject;

extern PyTypeObject AudioQueueType;

fft_result_t* fft_result_create(void);
void fft_result_destroy(fft_result_t* result);
int fft_result_append(fft_result_t* result, double time_offset,
    double frequency, double intensity, const void* user_data);

AudioQueueObject* audio_queue_create(user_data_wake_cb data_waker);
void audio_queue_push(AudioQueueObject* queue, fft_result_t* result);
Py_ssize_t audio_queue_length(AudioQueueObject* queue);
void audio_queue_signal_oom(AudioQueueObject* queue);

#endif /* end of include guard: _QUEUE_H_ */
