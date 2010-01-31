/**
 * A simple frequency filter that enforces a particular high-end cutoff.
 */

#include "../filter.h"

typedef struct {
    FilterObject_HEAD
    double max_frequency;
    Py_ssize_t cutoff_length;
} CutoffFilterObject;

static int CutoffFilter_Execute(CutoffFilterObject* self, size_t* length,
    bucket_t* buckets)
{
    if (self->cutoff_length < 0) {
        self->cutoff_length = (Py_ssize_t) *length;
        
        for (size_t i = 0; i < *length; i++) {
            if (buckets[i].frequency > self->max_frequency) {
                self->cutoff_length = i;
                break;
            }
        }
    }
    
    *length = (size_t) self->cutoff_length;
    return 0;
}

static PyObject* CutoffFilter_new(PyTypeObject* subtype, PyObject* args,
    PyObject* kwds)
{
    return PyType_GenericNew(subtype, args, kwds);
}

static int CutoffFilter_init(CutoffFilterObject* self, PyObject* args,
    PyObject* kwds)
{
    static char* kwlist[] = {"maximum", NULL};
    double max_frequency;
    
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "d", kwlist, &max_frequency))
        return -1;
    
    if (max_frequency <= 0.0) {
        PyErr_SetString(PyExc_ValueError,
            "too harsh of a cutoff");
        return -1;
    }
    
    self->max_frequency = max_frequency;
    self->impl = (filter_cb) CutoffFilter_Execute;
    self->cutoff_length = -1;
    
    return 0;
}

static PyObject* CutoffFilter_repr(CutoffFilterObject* self)
{
    return PyString_FromFormat("%s(maximum=%f)", self->ob_type->tp_name,
        self->max_frequency);
}

static void CutoffFilter_dealloc(CutoffFilterObject* self) {
    self->ob_type->tp_free(self);
}

FilterType_SUBCLASS(CutoffFilter, 0,
    "Cuts off the frequencies at the given maximum frequency.");
