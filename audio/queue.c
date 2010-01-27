/**
 * A fast, thread-safe, blocking, FIFO queue implementation.
 */

#include <sys/time.h>
#include <errno.h>
#include "queue.h"

PyObject* audio_queue_push(QueueObject* self, PyObject* value)
{
    queue_node_t* node = PyMem_New(queue_node_t, 1);
    if (node == NULL) {
        // well shit, I thought we had modern computers
        return PyErr_NoMemory();
    }
    
    Py_XINCREF(value);
    
    Py_BEGIN_ALLOW_THREADS
    node->value = value;
    node->next = NULL;
    
    pthread_mutex_lock(&self->mutex);
    if (self->tail == NULL) {
        self->head = self->tail = node;
    } else {
        self->tail->next = node;
        self->tail = node;
    }
    self->length++;
    pthread_cond_broadcast(&self->condition);
    pthread_mutex_unlock(&self->mutex);
    Py_END_ALLOW_THREADS
    
    Py_RETURN_NONE;
}

PyObject* audio_queue_pop(QueueObject* self, PyObject* nada)
{   
    PyThreadState* _save;
    struct timeval now;
    struct timespec timeout_point;
    int result = 0;
    PyObject* value;
    
    Py_UNBLOCK_THREADS
    
    pthread_mutex_lock(&self->mutex);
    while (self->head == NULL) {
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
        
        Py_BLOCK_THREADS
        if (PyErr_CheckSignals() != 0) {
            pthread_mutex_unlock(&self->mutex);
            return NULL;
        }
        
        if (result != 0 && result != ETIMEDOUT) {
            PyErr_SetObject(PyExc_OSError,
                Py_BuildValue("(i, s)", result,
                    "Failed to wait for condition to be signalled"));
            return NULL;
        }
        
        Py_UNBLOCK_THREADS
    }
    
    value = self->head->value;
    self->head = self->head->next;
    if (self->head == NULL)
        self->tail = NULL;
    self->length--;
    
    pthread_mutex_unlock(&self->mutex);
    
    Py_BLOCK_THREADS
    return value;
}

Py_ssize_t audio_queue_length(QueueObject* self)
{
    return self->length;
}

static PyObject* audio_queue_new(PyTypeObject* type, PyObject* args,
    PyObject* kwargs)
{
    QueueObject* self;
    
    self = (QueueObject*) type->tp_alloc(type, 0);
    if (self != NULL) {
        if (pthread_mutex_init(&self->mutex, NULL) != 0) {
            Py_DECREF(self);
            PyErr_SetFromErrno(PyExc_OSError);
            return NULL;
        }
        
        if (pthread_cond_init(&self->condition, NULL) != 0) {
            pthread_mutex_destroy(&self->mutex);
            
            Py_DECREF(self);
            PyErr_SetFromErrno(PyExc_OSError);
            return NULL;
        }
    }
    
    return (PyObject*) self;
}

int audio_queue_init(QueueObject* self, PyObject* args, PyObject* kwargs)
{
    self->length = 0;
    return 0;
}

static void audio_queue_dealloc(QueueObject* self)
{
    pthread_mutex_lock(&self->mutex);
    queue_node_t* node = self->head;
    queue_node_t* next;
    while (node) {
        Py_XDECREF(node->value);
        next = node->next;
        PyMem_Free(node);
        node = next;
    }
    pthread_mutex_unlock(&self->mutex);
    
    pthread_cond_destroy(&self->condition);
    pthread_mutex_destroy(&self->mutex);
    
    self->ob_type->tp_free(self);
}

static PyMethodDef audio_queue_methods[] = {
    {"push", (PyCFunction) audio_queue_push, METH_O,
        "Push an item onto the queue"},
    {"pop", (PyCFunction) audio_queue_pop, METH_NOARGS,
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

PyTypeObject QueueType = {
    PyObject_HEAD_INIT(NULL)
    0,                         /*ob_size*/
    "audio.Queue",             /*tp_name*/
    sizeof(QueueObject),/*tp_basicsize*/
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
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
    "A blocking FIFO queue.",  /* tp_doc */
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
    audio_queue_new,                 /* tp_new */
};
