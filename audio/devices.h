/**
 * Provides access to information about system audio devices.
 */

#ifndef _DEVICES_H_
#define _DEVICES_H_

#include <Python.h>
#include <portaudio.h>

typedef struct {
    PyObject_HEAD
    PaDeviceIndex index;
    const PaDeviceInfo* info;
} DeviceObject;

#ifndef DEVICES_MODULE
extern PyTypeObject DeviceType;
#endif

/**
 * Gets a list of all system audio devices.
 */
PyObject* audio_devices_get(PyObject* self, PyObject* nothing);
int audio_device_init(DeviceObject* self, PyObject* args,
    PyObject* kwargs);

#endif /* end of include guard: _DEVICES_H_ */
