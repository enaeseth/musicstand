/**
 * A fast, thread-safe, blocking, FIFO queue implementation.
 */

#include <sys/time.h>
#include <errno.h>
#include <stdlib.h>
#include <stdio.h>
#include <stdint.h>
#include "queue.h"
#include "memory.h"

#define INITIAL_RESULT_CAPACITY 8

static inline int fft_result_grow(fft_result_t* result);
static PyObject* AudioQueue_Pop(AudioQueueObject* self, PyObject* unused);
static void audio_queue_dealloc(AudioQueueObject* self);
static PyObject* _unpack_fft_result(fft_result_t* result,
    user_data_wake_cb waker);

fft_result_t* fft_result_create(void)
{
    fft_result_t* result = (fft_result_t*) calloc(1, sizeof(fft_result_t));
    if (result != NULL) {
        debug_malloc(result, "FFT result");
        result->length = 0;
        result->capacity = INITIAL_RESULT_CAPACITY;
        result->buckets = calloc(result->capacity, sizeof(bucket_t));
        result->next = NULL;
        
        if (result->buckets == NULL) {
            debug_free(result, "FFT result");
            free(result);
            return NULL;
        } else {
            debug_malloc(result->buckets, "FFT result buckets");
            fprintf(stderr, "capacity: %lu; length: %lu\n", result->capacity,
                result->length);
        }
    }
    return result;
}

void fft_result_destroy(fft_result_t* result)
{
    if (result != NULL) {
        if (result->buckets != NULL) {
            debug_free(result->buckets, "FFT result buckets");
            free(result->buckets);
            result->buckets = NULL;
        }
        debug_free(result, "FFT result");
        free(result);
    }
}

int fft_result_append(fft_result_t* result, double time_offset,
    double frequency, double intensity, const void* user_data)
{
    if (result->length >= result->capacity) {
        if (!fft_result_grow(result))
            return -1;
    }
    
    bucket_t* bucket = (result->buckets + result->length);
    result->length++;
    
    bucket->offset = time_offset;
    bucket->frequency = frequency;
    bucket->intensity = intensity;
    bucket->user_data = user_data;
    
    return 0;
}

static inline int fft_result_grow(fft_result_t* result) {
    size_t new_capacity = result->capacity + (result->capacity / 2);
    
    bucket_t* new_buckets = realloc(result->buckets,
        sizeof(bucket_t) * new_capacity);
    if (new_buckets == NULL) {
        free(result->buckets);
        result->buckets = NULL;
        return 0;
    }
    
    result->buckets = new_buckets;
    return 1;
}

AudioQueueObject* audio_queue_create(user_data_wake_cb data_waker)
{
    AudioQueueObject* queue =
        (AudioQueueObject*) AudioQueueType.tp_alloc(&AudioQueueType, 0);
    
    if (queue != NULL) {
        debug_malloc(queue, "audio result queue");
        fprintf(stderr, "  reference count: %ld\n", queue->ob_refcnt);
        if (pthread_mutex_init(&queue->mutex, NULL) != 0) {
            Py_DECREF(queue);
            PyErr_SetFromErrno(PyExc_OSError);
            return NULL;
        }

        if (pthread_cond_init(&queue->condition, NULL) != 0) {
            pthread_mutex_destroy(&queue->mutex);

            Py_DECREF(queue);
            PyErr_SetFromErrno(PyExc_OSError);
            return NULL;
        }
        
        queue->waker = data_waker;
        queue->length = 0;
        queue->head = queue->tail = NULL;
    }
    
    return queue;
}

void audio_queue_push(AudioQueueObject* queue, fft_result_t* result)
{
    pthread_mutex_lock(&queue->mutex);
    if (queue->tail == NULL) {
        queue->head = queue->tail = result;
    } else {
        queue->tail->next = result;
        queue->tail = result;
    }
    queue->length++;
    pthread_cond_signal(&queue->condition);
    pthread_mutex_unlock(&queue->mutex);
}

static PyObject* AudioQueue_Pop(AudioQueueObject* self, PyObject* unused)
{
    PyThreadState* _save;
    struct timeval now;
    struct timespec timeout_point;
    int result = 0;
    fft_result_t* fft_result;
    
    Py_UNBLOCK_THREADS
    
    pthread_mutex_lock(&self->mutex);
    while (self->head == NULL && !self->no_memory) {
        gettimeofday(&now, NULL);
        timeout_point.tv_sec = now.tv_sec;
        timeout_point.tv_nsec = (now.tv_usec * 1000) + 500000000;
        if (timeout_point.tv_nsec >= 1000000000) {
            timeout_point.tv_nsec -= 1000000000;
            timeout_point.tv_sec++;
        }
        
        // wait for something to be put into the queue
        result = pthread_cond_timedwait(&self->condition, &self->mutex,
            &timeout_point);
        
        if (result != 0 && result != ETIMEDOUT) {
            pthread_mutex_unlock(&self->mutex);
            Py_BLOCK_THREADS
            
            if (PyErr_CheckSignals() == 0) {
                PyErr_SetObject(PyExc_OSError,
                    Py_BuildValue("(i, O)", result, PyString_FromFormat(
                    "Failed to wait for new item: %s",strerror(result))));
            }
            return NULL;
        } else if (result == 0) {
            Py_BLOCK_THREADS
            
            if (PyErr_CheckSignals() != 0) {
                pthread_mutex_unlock(&self->mutex);
                return NULL;
            } else {
                Py_UNBLOCK_THREADS
            }
        }
    }
    
    if (self->no_memory) {
        return PyErr_NoMemory();
    }
    
    fft_result = self->head;
    self->head = fft_result->next;
    if (self->head == NULL)
        self->tail = NULL;
    self->length--;
    
    pthread_mutex_unlock(&self->mutex);
    Py_BLOCK_THREADS
    
    return _unpack_fft_result(fft_result, self->waker);
}

static PyObject* _unpack_fft_result(fft_result_t* result,
    user_data_wake_cb waker)
{
    Py_ssize_t length = result->length;
    PyObject* result_list = PyList_New(length);
    PyObject* tuple;
    Py_ssize_t i;
    bucket_t* bucket = result->buckets;
    
    if (result_list == NULL) {
        free(result->buckets);
        free(result);
        return NULL;
    }
    
    for (i = 0; i < length; i++) {
        tuple = PyTuple_New(4);
        
        if (tuple == NULL) {
            Py_DECREF(result_list);
            free(result->buckets);
            free(result);
            return NULL;
        }
        
        /* timing information is not yet provided
        PyTuple_SET_ITEM(tuple, 0, PyFloat_FromDouble(bucket->offset));
        */
        PyTuple_SET_ITEM(tuple, 0, Py_None);
        PyTuple_SET_ITEM(tuple, 1, PyFloat_FromDouble(bucket->frequency));
        PyTuple_SET_ITEM(tuple, 2, PyFloat_FromDouble(bucket->intensity));

        if (waker != NULL && bucket->user_data != NULL) {
            PyTuple_SET_ITEM(tuple, 3, waker(bucket->user_data));
        } else {
            PyTuple_SET_ITEM(tuple, 3, Py_None);
        }
        
        PyList_SET_ITEM(result_list, i, tuple);
        bucket++;
    }
    
    free(result->buckets);
    free(result);
    return result_list;
}

Py_ssize_t audio_queue_length(AudioQueueObject* queue)
{
    return queue->length;
}

void audio_queue_signal_oom(AudioQueueObject* queue)
{
    queue->no_memory = 1;
}

int audio_queue_init(AudioQueueObject* self, PyObject* args, PyObject* kwargs)
{
    return 0;
}

static void audio_queue_dealloc(AudioQueueObject* self)
{
    fprintf(stderr, "Deallocating a queue.\n");
    pthread_mutex_lock(&self->mutex);
    fft_result_t* node = self->head;
    fft_result_t* next;
    while (node) {
        next = node->next;
        free(node);
        node = next;
    }
    pthread_mutex_unlock(&self->mutex);
    
    pthread_cond_destroy(&self->condition);
    pthread_mutex_destroy(&self->mutex);
    
    self->ob_type->tp_free(self);
    debug_free(self, "audio result queue");
}

static PyMethodDef audio_queue_methods[] = {
    {"pop", (PyCFunction) AudioQueue_Pop, METH_NOARGS,
        "Pop an item from the queue, blocking until one is available"},
    {NULL} // sentinel
};

static PySequenceMethods audio_queue_as_sequence = {
    (lenfunc) audio_queue_length,     /* sq_length */
    0,                                /* sq_concat */
    0,                                /* sq_repeat */
    0,                                /* sq_item */
    0,                                /* sq_slice */
    0,                                /* sq_ass_item */
    0,                                /* sq_ass_slice */
    0,                                /* sq_contains */
    0,                                /* sq_inplace_concat */
    0,                                /* sq_inplace_repeat */
};

PyTypeObject AudioQueueType = {
    PyObject_HEAD_INIT(NULL)
    0,                         /*ob_size*/
    "audio.Queue",             /*tp_name*/
    sizeof(AudioQueueObject),  /*tp_basicsize*/
    0,                         /*tp_itemsize*/
    (destructor)audio_queue_dealloc, /*tp_dealloc*/
    0,                         /*tp_print*/
    0,                         /*tp_getattr*/
    0,                         /*tp_setattr*/
    0,                         /*tp_compare*/
    0,                         /*tp_repr*/
    0,                         /*tp_as_number*/
    &audio_queue_as_sequence,  /*tp_as_sequence*/
    0,                         /*tp_as_mapping*/
    0,                         /*tp_hash */
    0,                         /*tp_call*/
    0,                         /*tp_str*/
    0,                         /*tp_getattro*/
    0,                         /*tp_setattro*/
    0,                         /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT,        /*tp_flags*/
    "A queue for FFT Data.",   /* tp_doc */
    0,                         /* tp_traverse */
    0,                         /* tp_clear */
    0,                         /* tp_richcompare */
    0,                         /* tp_weaklistoffset */
    0,                         /* tp_iter */
    0,                         /* tp_iternext */
    audio_queue_methods,  /* tp_methods */
    0,  /* tp_members */
    0,                         /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    (initproc)audio_queue_init,      /* tp_init */
    0,                         /* tp_alloc */
    /* Don't let Python code create Queue objects: */
    0,                         /* tp_new */
};
