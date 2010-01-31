/**
 * Piano Hero low-level audio processor.
 */

#include <Python.h>
#include <portaudio.h>
#include "devices.h"
#include "queue.h"
#include "listen.h"
#include "filter.h"

static void terminate_portaudio(void);

static PyMethodDef module_methods[] = {
    {"get_devices", (PyCFunction) audio_devices_get, METH_NOARGS,
        "Gets a list of all available system audio devices"},
    {NULL}  // sentinel
};

static void terminate_portaudio(void) {
    Pa_Terminate();
}

PyMODINIT_FUNC initaudio(void) {
    PyObject* module;
    
    DeviceType.tp_new = PyType_GenericNew;
    if (PyType_Ready(&DeviceType) < 0)
        return;
    if (PyType_Ready(&AudioQueueType) < 0)
        return;
    if (PyType_Ready(&ListenerType) < 0)
        return;
    FilterType.tp_new = PyType_GenericNew;
    if (PyType_Ready(&FilterType) < 0)
        return;
    if (PyType_Ready(&PythonFilterType) < 0)
        return;
    
    PaError err = Pa_Initialize();
    if (err != paNoError) {
        PyErr_SetObject(PyExc_RuntimeError,
            Py_BuildValue("(s, i)", "Failed to initialize PortAudio",
                (int) err));
        return;
    }
    
    if (Py_AtExit(terminate_portaudio) != 0) {
        PySys_WriteStderr("Failed to register the PortAudio cleanup function.");
    }
    
    module = Py_InitModule3("audio", module_methods,
        "Low-level audio processor");
    if (module == NULL)
        return;
    
    Py_INCREF(&DeviceType);
    PyModule_AddObject(module, "Device", (PyObject*) &DeviceType);
    
    Py_INCREF(&AudioQueueType);
    PyModule_AddObject(module, "Queue", (PyObject*) &AudioQueueType);
    
    Py_INCREF(&ListenerType);
    PyModule_AddObject(module, "Listener", (PyObject*) &ListenerType);
    
    Py_INCREF(&FilterType);
    PyModule_AddObject(module, "Filter", (PyObject*) &FilterType);
    
    Py_INCREF(&PythonFilterType);
    PyModule_AddObject(module, "PythonFilter", (PyObject*) &PythonFilterType);
}
