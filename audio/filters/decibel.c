/**
 * A filter that converts absolute intensity values to decibels.
 */

#include "../filter.h"
#include <stdio.h>
#include <math.h>

typedef struct {
    FilterObject_HEAD
} DecibelFilterObject;

static int DecibelFilter_Execute(DecibelFilterObject* self, size_t* length_ptr,
    bucket_t* buckets)
{
    size_t length = *length_ptr;
    size_t i;
    bucket_t* bucket;
    // double total = 0.0;
    double reference = 0.0;
    
    for (bucket = buckets, i = 0; i < length; i++, bucket++) {
        if (bucket->intensity > reference)
            reference = bucket->intensity;
    }
    
    // fprintf(stderr, "reference intensity: %.05f\n", reference);
    
    for (bucket = buckets, i = 0; i < length; i++, bucket++) {
        bucket->intensity = 10 * log10(bucket->intensity / reference);
    }
    
    return 0;
}

static PyObject* DecibelFilter_new(PyTypeObject* subtype, PyObject* args,
    PyObject* kwds)
{
    return PyType_GenericNew(subtype, args, kwds);
}

static int DecibelFilter_init(DecibelFilterObject* self, PyObject* args,
    PyObject* kwds)
{
    self->impl = (filter_cb) DecibelFilter_Execute;
    return 0;
}

static PyObject* DecibelFilter_repr(DecibelFilterObject* self)
{
    return PyString_FromFormat("%s()", self->ob_type->tp_name);
}

static void DecibelFilter_dealloc(DecibelFilterObject* self) {
    self->ob_type->tp_free(self);
}

FilterType_SUBCLASS(DecibelFilter, 0,
    "Converts absolute FFT intensities to decibels.");
