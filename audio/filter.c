/**
 * Infrastructure for filtering audio frequency results.
 */

#include "filter.h"
#include <string.h>
#include <stdio.h>

typedef struct {
    FilterObject_HEAD
    PyObject* real_impl;
} PythonFilterObject;

static int PythonFilter_Defer(PythonFilterObject* filter, size_t* length,
    bucket_t* entries);

FilterChain* FilterChain_Prepare(PyObject* filters)
{
    Py_ssize_t signed_length = PySequence_Length(filters);
    if (signed_length < 0) {
        PyErr_SetString(PyExc_TypeError, "a filter chain must have a length");
        return NULL;
    }
    
    size_t length = (size_t) signed_length;
    PyObject* iterator = PyObject_GetIter(filters);
    PyObject* item;
    FilterChain* chain;
    
    if (iterator == NULL)
        return NULL;
    
    chain = (FilterChain*) PyMem_Malloc(sizeof(FilterChain) +
        (length * sizeof(FilterObject*)));
    
    if (chain != NULL) {
        size_t i = 0;
        chain->requires_gil = 0;
        
        while ((item = PyIter_Next(iterator))) {
            if (PyCallable_Check(item)) {
                item = (PyObject*) PythonFilter_FromCallable(item);
                chain->requires_gil = 1;
            } else if (!Filter_Check(item)) {
                PyErr_SetObject(PyExc_TypeError, PyString_Format(
                    PyString_FromString("invalid filter: %r"),
                    Py_BuildValue("(o)", item)));
                PyMem_Free(chain);
                chain = NULL;
                break;
            } else if (Filter_RequiresGIL((FilterObject*) item)) {
                chain->requires_gil = 1;
            }
            
            chain->filters[i++] = (FilterObject*) item;
        }
    }
    chain->length = length;
    
    Py_DECREF(iterator);
    
    return chain;
}

void FilterChain_Destroy(FilterChain* chain)
{
    for (size_t i = 0; i < chain->length; i++) {
        Py_DECREF(chain->filters[i]);
        chain->filters[i] = NULL;
    }
    
    PyMem_Free(chain);
}

int FilterChain_Execute(FilterChain* chain, size_t* length, bucket_t* entries)
{
    int result = 0;
    size_t i;
    
    if (chain->requires_gil) {
        PyGILState_STATE state;
        int lock_held = 0;
        FilterObject* filter;
        
        for (i = 0; i < chain->length; i++) {
            filter = chain->filters[i];
            
            if (lock_held && !Filter_RequiresGIL(filter)) {
                PyGILState_Release(state);
                lock_held = 0;
            } else if (!lock_held && Filter_RequiresGIL(filter)) {
                state = PyGILState_Ensure();
                lock_held = 1;
            }
            
            result = Filter_Execute(chain->filters[i], length, entries);
            if (result != 0) {
                fprintf(stderr, "error: filter %s returned %d\n",
                    chain->filters[i]->ob_type->tp_name, result);
                PyErr_Print();
                break;
            }
        }
                
        if (lock_held) {
            PyGILState_Release(state);
        }
    } else {
        for (i = 0; i < chain->length; i++) {
            result = Filter_Execute(chain->filters[i], length, entries);
            if (result != 0)
                break;
        }
    }
    
    return result;
}

int FilterChain_RequiresGIL(FilterChain* chain)
{
    return chain->requires_gil;
}

int Filter_Check(PyObject* obj)
{
    return PyObject_IsInstance(obj, (PyObject*) &FilterType);
}

static void Filter_dealloc(FilterObject* self) {
    self->ob_type->tp_free(self);
}

int Filter_Execute(FilterObject* filter, size_t* length, bucket_t* entries)
{
    return filter->impl(filter, length, entries);
}

int Filter_RequiresGIL(FilterObject* filter)
{
    return (filter->ob_type == &PythonFilterType);
}

static PyObject* PythonFilter_new(PyTypeObject* subtype, PyObject* args,
    PyObject* kwds)
{
    return PyType_GenericNew(subtype, args, kwds);
}

static int PythonFilter_init(PythonFilterObject* self, PyObject* args,
    PyObject* kwds)
{
    static char* kwlist[] = {"filter", NULL};
    PyObject* filter = NULL;
    
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O", kwlist, &filter))
        return -1;
    
    if (!filter || !PyCallable_Check(filter)) {
        PyErr_SetString(PyExc_TypeError,
            "filter implementation is not callable");
        return -1;
    }
    
    Py_INCREF(filter);
    self->real_impl = filter;
    self->impl = (filter_cb) PythonFilter_Defer;
    
    return 0;
}

static PyObject* PythonFilter_repr(PythonFilterObject* self)
{
    return PyString_Format(PyString_FromString("<%s %r>"),
        Py_BuildValue("(O, O)", PyString_FromString(self->ob_type->tp_name),
            self->real_impl));
}

static void PythonFilter_dealloc(PythonFilterObject* self) {
    Py_XDECREF(self->real_impl);
    self->real_impl = NULL;
    self->ob_type->tp_free(self);
}

FilterObject* PythonFilter_FromCallable(PyObject* impl)
{
    if (!PyCallable_Check(impl)) {
        PyErr_SetString(PyExc_TypeError,
            "filter implementation is not callable");
        return NULL;
    }
    
    PythonFilterObject* filter = (PythonFilterObject*)
        PythonFilterType.tp_new(&PythonFilterType, NULL, NULL);
    
    if (filter != NULL) {
        filter->real_impl = impl;
        filter->impl = (filter_cb) PythonFilter_Defer;
    }
    
    return (FilterObject*) filter;
}

static inline PyObject* check_tuple(PyObject* obj)
{
    if (!PyTuple_Check(obj)) {
        PyErr_SetString(PyExc_TypeError,
            "the filter function must return a sequence of tuples");
        return NULL;
    } else if (PyTuple_Size(obj) != 2) {
        PyErr_SetString(PyExc_ValueError,
            "filter result tuples must be of length 2");
        return NULL;
    }
    
    return obj;
}

static inline void populate_entry(bucket_t* entries, Py_ssize_t i,
    PyObject* result_tuple)
{
    bucket_t* entry = (entries + i);
    entry->frequency = PyFloat_AsDouble(PyTuple_GET_ITEM(result_tuple, 0));
    entry->intensity = PyFloat_AsDouble(PyTuple_GET_ITEM(result_tuple, 1));
}

static int PythonFilter_Defer(PythonFilterObject* filter, size_t* length,
    bucket_t* entries)
{
    size_t original_length = *length;
    PyObject* list = PyList_New((Py_ssize_t) original_length);
    
    for (size_t i = 0; i < original_length; i++) {
        bucket_t* entry = (entries + i);
        
        PyObject* tuple = PyTuple_New(2);
        PyTuple_SET_ITEM(tuple, 0, PyFloat_FromDouble(entry->frequency));
        PyTuple_SET_ITEM(tuple, 1, PyFloat_FromDouble(entry->intensity));
        
        PyList_SET_ITEM(list, (Py_ssize_t) i, tuple);
    }
    
    PyObject* filtered = PyObject_CallFunctionObjArgs(filter->real_impl,
        list, NULL);
    Py_DECREF(list);
    
    if (PyErr_Occurred())
        return -1;
    
    if (!PySequence_Check(filtered)) {
        PyErr_SetString(PyExc_TypeError,
            "the filter function must return a sequence");
        return -1;
    }
    
    Py_ssize_t filtered_length = 0;
    if (PyList_CheckExact(filtered)) {
        filtered_length = PyList_Size(filtered);
        for (Py_ssize_t i = 0; i < filtered_length; i++) {
            PyObject* tuple = check_tuple(PyList_GET_ITEM(filtered, i));
            if (tuple == NULL)
                break;
            populate_entry(entries, i, tuple);
        }
    } else {
        PyObject* iterator = PyObject_GetIter(filtered);
        PyObject* item;
        
        if (iterator != NULL) {
            while ((item = PyIter_Next(iterator))) {
                PyObject* tuple = check_tuple(PyList_GET_ITEM(filtered,
                    filtered_length));
                if (tuple == NULL) {
                    Py_DECREF(item);
                    break;
                }
                
                populate_entry(entries, filtered_length++, tuple);
                Py_DECREF(item);
            }
            
            Py_DECREF(iterator);
        }
    }
    
    Py_DECREF(filtered);
    
    *length = (size_t) filtered_length;
    return (PyErr_Occurred()) ? -1 : 0;
}

PyTypeObject FilterType = {
    PyObject_HEAD_INIT(NULL)
    0,                         /*ob_size*/
    "audio.Filter",            /*tp_name*/
    sizeof(FilterObject),      /*tp_basicsize*/
    0,                         /*tp_itemsize*/
    (destructor) Filter_dealloc, /*tp_dealloc*/
    0,                         /*tp_print*/
    0,                         /*tp_getattr*/
    0,                         /*tp_setattr*/
    0,                         /*tp_compare*/
    0,                         /*tp_repr*/
    0,                         /*tp_as_number*/
    0,                         /*tp_as_sequence*/
    0,                         /*tp_as_mapping*/
    0,                         /*tp_hash */
    0,                         /*tp_call*/
    0,                         /*tp_str*/
    0,                         /*tp_getattro*/
    0,                         /*tp_setattro*/
    0,                         /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,        /*tp_flags*/
    "A frequency result filter.", /* tp_doc */
    0,                         /* tp_traverse */
    0,                         /* tp_clear */
    0,                         /* tp_richcompare */
    0,                         /* tp_weaklistoffset */
    0,                         /* tp_iter */
    0,                         /* tp_iternext */
    0,                         /* tp_methods */
    0,                         /* tp_members */
    0,                         /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    0,                         /* tp_init */
    0,                         /* tp_alloc */
    0,                         /* tp_new */
};

FilterType_SUBCLASS(PythonFilter, 0, "A filter implemented in Python.");
