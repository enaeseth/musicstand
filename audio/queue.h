/**
 * A fast, thread-safe, blocking, FIFO queue implementation.
 */

#ifndef _QUEUE_H_
#define _QUEUE_H_

#include <Python.h>
#include <pthread.h>

typedef struct queue_node {
    PyObject* value;
    struct queue_node* next;
} queue_node_t;

typedef struct {
    PyObject_HEAD
    pthread_mutex_t mutex;
    pthread_cond_t condition;
    Py_ssize_t length;
    queue_node_t* head;
    queue_node_t* tail;
} QueueObject;

extern PyTypeObject QueueType;

int audio_queue_init(QueueObject* self, PyObject* args, PyObject* kwargs);
PyObject* audio_queue_push(QueueObject* self, PyObject* value);
PyObject* audio_queue_pop(QueueObject* self, PyObject* nada);

#endif /* end of include guard: _QUEUE_H_ */
