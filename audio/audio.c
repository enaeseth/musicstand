/**
 * Piano Hero low-level audio processor.
 */

#include <Python.h>
#include <portaudio.h>
#include "devices.h"
#include "queue.h"
#include "listen.h"

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
    if (PyType_Ready(&QueueType) < 0)
        return;
    if (PyType_Ready(&ListenerType) < 0)
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
    
    Py_INCREF(&QueueType);
    PyModule_AddObject(module, "Queue", (PyObject*) &QueueType);
    
    Py_INCREF(&ListenerType);
    PyModule_AddObject(module, "Listener", (PyObject*) &ListenerType);
}
