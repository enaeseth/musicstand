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

#endif /* end of include guard: _FILTER_H_ */
