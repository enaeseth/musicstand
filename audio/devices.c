/**
 * Provides access to information about system audio devices.
 */

#include "devices.h"

static PyObject* audio_device_repr(DeviceObject* self);
static PyObject* audio_device_get_name(DeviceObject* self, void* closure);
static PyObject* audio_device_get_input_channels(DeviceObject* self,
    void* closure);
static PyObject* audio_device_get_output_channels(DeviceObject* self,
    void* closure);
static PyObject* audio_device_get_default_sample_rate(DeviceObject* self,
    void* closure);
static PyObject* audio_device_set(DeviceObject* self, PyObject* value,
    void* closure);

PyObject* audio_devices_get(PyObject* self, PyObject* nothing)
{
    PaDeviceIndex result = Pa_GetDeviceCount();
    if (result < 0) {
        PyErr_SetObject(PyExc_RuntimeError,
            Py_BuildValue("(s, i)", "Failed to get PortAudio devices",
                (int) result));
        return NULL;
    }
    
    Py_ssize_t device_count = (Py_ssize_t) result;
    PyObject* device_list = PyList_New(device_count);
    if (device_list == NULL) {
        return PyErr_NoMemory();
    }
    
    DeviceObject* device;
    const PaDeviceInfo* info;
    Py_ssize_t i;
    for (i = 0; i < device_count; i++) {
        device = PyObject_New(DeviceObject, &DeviceType);
        if (device == NULL) {
            Py_DECREF(device_list);
            return NULL;
        }
        
        info = Pa_GetDeviceInfo((PaDeviceIndex) i);
        if (info == NULL) {
            Py_DECREF(device_list);
            return NULL;
        }
        
        device->info = info;
        PyList_SET_ITEM(device_list, i, (PyObject*) device);
    }
    
    return device_list;
}

static PyObject* audio_device_repr(DeviceObject* self)
{
    return PyString_FromFormat("<audio.Device %s>", self->info->name);
}

static PyObject* audio_device_str(DeviceObject* self)
{
    return PyString_FromString(self->info->name);
}

static PyObject* audio_device_get_name(DeviceObject* self, void* closure)
{
    return PyString_FromString(self->info->name);
}

static PyObject* audio_device_get_input_channels(DeviceObject* self,
    void* closure)
{
    return PyInt_FromLong((long) self->info->maxInputChannels);
}

static PyObject* audio_device_get_output_channels(DeviceObject* self,
    void* closure)
{
    return PyInt_FromLong((long) self->info->maxOutputChannels);
}

static PyObject* audio_device_get_default_sample_rate(DeviceObject* self,
    void* closure)
{
    return PyFloat_FromDouble(self->info->defaultSampleRate);
}

static PyObject* audio_device_set(DeviceObject* self, PyObject* value,
    void* closure)
{
    PyErr_SetString(PyExc_AttributeError, "can't set attribute");
    return NULL;
}

static int audio_device_init(DeviceObject* self, PyObject* args,
    PyObject* kwds)
{
    return 0;
}

static void audio_device_dealloc(DeviceObject* self)
{
    // nothing to do
}

static PyGetSetDef Device_getset[] = {
    {"name", (getter) audio_device_get_name, (setter) audio_device_set,
        "The human-readable name of the audio device", NULL},
    {"input_channels", (getter) audio_device_get_input_channels,
        (setter) audio_device_set,
        "The maximum number of input channels that the device provides", NULL},
    {"output_channels", (getter) audio_device_get_output_channels,
        (setter) audio_device_set,
        "The maximum number of output channels that the device provides",
        NULL},
    {"default_sample_rate", (getter) audio_device_get_default_sample_rate,
        (setter) audio_device_set,
        "The default sample rate of the device (in Hz)", NULL},
    {NULL}  /* Sentinel */
};

PyTypeObject DeviceType = {
    PyObject_HEAD_INIT(NULL)
    0,                         /*ob_size*/
    "audio.Device",            /*tp_name*/
    sizeof(DeviceObject),      /*tp_basicsize*/
    0,                         /*tp_itemsize*/
    (destructor)audio_device_dealloc, /*tp_dealloc*/
    0,                         /*tp_print*/
    0,                         /*tp_getattr*/
    0,                         /*tp_setattr*/
    0,                         /*tp_compare*/
    (reprfunc)audio_device_repr,         /*tp_repr*/
    0,                         /*tp_as_number*/
    0,                         /*tp_as_sequence*/
    0,                         /*tp_as_mapping*/
    0,                         /*tp_hash */
    0,                         /*tp_call*/
    (reprfunc)audio_device_str,          /*tp_str*/
    0,                         /*tp_getattro*/
    0,                         /*tp_setattro*/
    0,                         /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT,        /*tp_flags*/
    "A system audio device",   /* tp_doc */
    0,                         /* tp_traverse */
    0,                         /* tp_clear */
    0,                         /* tp_richcompare */
    0,                         /* tp_weaklistoffset */
    0,                         /* tp_iter */
    0,                         /* tp_iternext */
    0,                         /* tp_methods */
    0,                         /* tp_members */
    Device_getset,             /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    (initproc)audio_device_init,/* tp_init */
    0,                         /* tp_alloc */
    0,                         /* tp_new */
};
