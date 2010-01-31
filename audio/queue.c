/**
 * A blocking queue specifically for passing FFT results to the upper layers
 * of the program.
 *
 * Uses fine-grained locking, so that the GIL need not be held to execute
 * a push.
 */

#include <sys/time.h>
#include <errno.h>
#include <stdlib.h>
#include <stdio.h>
#include <stdint.h>
#include "queue.h"
#include "memory.h"

static inline int fft_result_grow(fft_result_t* result);
static PyObject* AudioQueue_Pop(AudioQueueObject* self, PyObject* unused);
static void audio_queue_dealloc(AudioQueueObject* self);
static PyObject* _unpack_fft_result(fft_result_t* result,
    user_data_wake_cb waker);

fft_result_t* fft_result_create(size_t capacity, double time_offset,
    const void* user_data)
{
    fft_result_t* result = (fft_result_t*) calloc(1, sizeof(fft_result_t));
    if (result != NULL) {
        result->length = 0;
        result->capacity = capacity;
        result->buckets = calloc(result->capacity, sizeof(bucket_t));
        result->next = NULL;
        result->offset = time_offset;
        result->user_data = user_data;
        
        if (result->buckets == NULL) {
            free(result);
            return NULL;
        }
    }
    return result;
}

void fft_result_destroy(fft_result_t* result)
{
    if (result != NULL) {
        if (result->buckets != NULL) {
            free(result->buckets);
            result->buckets = NULL;
        }
        free(result);
    }
}

int fft_result_append(fft_result_t* result, double frequency,
    double intensity)
{
    if (result->length >= result->capacity) {
        if (!fft_result_grow(result))
            return -1;
    }
    
    bucket_t* bucket = (result->buckets + result->length);
    result->length++;
    
    bucket->frequency = frequency;
    bucket->intensity = intensity;
    
    return 0;
}

static inline int fft_result_grow(fft_result_t* result) {
    size_t new_capacity = result->capacity + (result->capacity * 3 / 4);
    
    bucket_t* new_buckets = realloc(result->buckets,
        sizeof(bucket_t) * new_capacity);
    if (new_buckets == NULL) {
        free(result->buckets);
        result->buckets = NULL;
        return 0;
    }
    
    result->capacity = new_capacity;
    result->buckets = new_buckets;
    return 1;
}

AudioQueueObject* audio_queue_create(user_data_wake_cb data_waker)
{
    AudioQueueObject* queue =
        (AudioQueueObject*) AudioQueueType.tp_alloc(&AudioQueueType, 0);
    
    if (queue != NULL) {
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
    PyObject* result_tuple;
    PyObject* result_list;
    PyObject* bucket_tuple;
    Py_ssize_t i;
    bucket_t* bucket = result->buckets;
    
    result_tuple = PyTuple_New(3);
    if (result_tuple == NULL) {
        fft_result_destroy(result);
        return NULL;
    }
    
    result_list = PyList_New(length);
    if (result_list == NULL) {
        Py_DECREF(result_tuple);
        fft_result_destroy(result);
        return NULL;
    }
    
    for (i = 0; i < length; i++) {
        bucket_tuple = PyTuple_New(2);
        
        if (bucket_tuple == NULL) {
            Py_DECREF(result_tuple);
            Py_DECREF(result_list);
            fft_result_destroy(result);
            return NULL;
        }
        
        PyTuple_SET_ITEM(bucket_tuple, 0,
            PyFloat_FromDouble(bucket->frequency));
        PyTuple_SET_ITEM(bucket_tuple, 1,
            PyFloat_FromDouble(bucket->intensity));
        
        PyList_SET_ITEM(result_list, i, bucket_tuple);
        bucket++;
    }
    
    /* timing information is not yet provided
    PyTuple_SET_ITEM(tuple, 0, PyFloat_FromDouble(result->offset));
    */
    Py_INCREF(Py_None);
    PyTuple_SET_ITEM(result_tuple, 0, Py_None);
    
    PyTuple_SET_ITEM(result_tuple, 1, result_list);
    
    if (waker != NULL && result->user_data != NULL) {
        PyTuple_SET_ITEM(result_tuple, 2, waker(result->user_data));
    } else {
        Py_INCREF(Py_None);
        PyTuple_SET_ITEM(result_tuple, 2, Py_None);
    }
    
    fft_result_destroy(result);
    return result_tuple;
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
