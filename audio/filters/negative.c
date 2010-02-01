/**
 * Clips out frequencies with negative values.
 */

#include "../filter.h"

typedef struct {
    FilterObject_HEAD
} NegativeFilterObject;

static int NegativeFilter_Execute(NegativeFilterObject* self, size_t* length,
    bucket_t* buckets)
{
    size_t orig_len = *length;
    size_t i;
    bucket_t* bucket;
    
    for (i = 0, bucket = buckets; i < orig_len; i++, bucket++) {
        if (bucket->intensity < 0.0) {
            bucket->intensity = 0.0;
        }
    }
    
    return 0;
}

static PyObject* NegativeFilter_new(PyTypeObject* subtype, PyObject* args,
    PyObject* kwds)
{
    return PyType_GenericNew(subtype, args, kwds);
}

static int NegativeFilter_init(NegativeFilterObject* self, PyObject* args,
    PyObject* kwds)
{
    self->impl = (filter_cb) NegativeFilter_Execute;    
    return 0;
}

static PyObject* NegativeFilter_repr(NegativeFilterObject* self)
{
     return PyString_FromFormat("%s()", self->ob_type->tp_name);
}

static void NegativeFilter_dealloc(NegativeFilterObject* self) {
    self->ob_type->tp_free(self);
}

FilterType_SUBCLASS(NegativeFilter, 0,
    "Cuts off the frequencies whose FFT values are <= 0.");
