/**
 * Infrastructure for filtering audio frequency results.
 */

#ifndef _FILTER_H_
#define _FILTER_H_

#include <Python.h>
#include "queue.h"

typedef struct filter FilterObject;

/**
 * Defines a FFT result filter function.
 */
typedef int (*filter_cb)(FilterObject* filter, size_t* length,
    bucket_t* entries);

#define FilterObject_HEAD \
    PyObject_HEAD \
    filter_cb impl;

struct filter {
    FilterObject_HEAD
};

typedef struct {
    int requires_gil;
    size_t length;
    FilterObject* filters[];
} FilterChain;

FilterChain* FilterChain_Prepare(PyObject* chain);
int FilterChain_Execute(FilterChain* chain, size_t* length, bucket_t* entries);
int FilterChain_RequiresGIL(FilterChain* chain);
void FilterChain_Destroy(FilterChain* chain);

int Filter_Check(PyObject* inst);
int Filter_Execute(FilterObject* filter, size_t* length, bucket_t* entries);
int Filter_RequiresGIL(FilterObject* filter);

FilterObject* PythonFilter_FromCallable(PyObject* impl);

extern PyTypeObject FilterType;
extern PyTypeObject PythonFilterType;
extern PyTypeObject CutoffFilterType;
extern PyTypeObject CoalesceFilterType;

#define FilterType_SUBCLASS(name, methods, doc) \
     PyTypeObject name ## Type = { \
         PyObject_HEAD_INIT(NULL) \
         0,                         /*ob_size*/ \
         "audio." #name,            /*tp_name*/ \
         sizeof(name ## Object),    /*tp_basicsize*/ \
         0,                         /*tp_itemsize*/ \
         (destructor)name ## _dealloc, /*tp_dealloc*/ \
         0,                         /*tp_print*/ \
         0,                         /*tp_getattr*/ \
         0,                         /*tp_setattr*/ \
         0,                         /*tp_compare*/ \
         (reprfunc)name ## _repr,   /*tp_repr*/ \
         0,                         /*tp_as_number*/ \
         0,                         /*tp_as_sequence*/ \
         0,                         /*tp_as_mapping*/ \
         0,                         /*tp_hash */ \
         0,                         /*tp_call*/ \
         0,                         /*tp_str*/ \
         0,                         /*tp_getattro*/ \
         0,                         /*tp_setattro*/ \
         0,                         /*tp_as_buffer*/ \
         Py_TPFLAGS_DEFAULT,        /*tp_flags*/ \
         doc,                       /* tp_doc */ \
         0,                         /* tp_traverse */ \
         0,                         /* tp_clear */ \
         0,                         /* tp_richcompare */ \
         0,                         /* tp_weaklistoffset */ \
         0,                         /* tp_iter */ \
         0,                         /* tp_iternext */ \
         0,                         /* tp_methods */ \
         0,                         /* tp_members */ \
         0,                         /* tp_getset */ \
         &FilterType,               /* tp_base */ \
         0,                         /* tp_dict */ \
         0,                         /* tp_descr_get */ \
         0,                         /* tp_descr_set */ \
         0,                         /* tp_dictoffset */ \
         (initproc)name ## _init,   /* tp_init */ \
         0,                         /* tp_alloc */ \
         name ## _new,             /* tp_new */ \
     }

#endif /* end of include guard: _FILTER_H_ */
