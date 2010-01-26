/**
 * Listens to an audio input device and performs frequency decomposition.
 */

#include <string.h>
#include "listen.h"
#include "devices.h"

#ifdef DEBUG
#define listen_debug(...) PySys_WriteStderr(__VA_ARGS__)
#else
#define listen_debug(...)
#endif

static PyObject* audio_listener_new(PyTypeObject* type, PyObject* args,
    PyObject* kwargs);
static int audio_listener_init(ListenerObject* self, PyObject* args,
    PyObject* kwargs);
static void audio_listener_dealloc(ListenerObject* self);
static PyObject* audio_listener_get_device(ListenerObject* self,
    void* closure);
static PyObject* audio_listener_get_interval(ListenerObject* self,
    void* closure);
static PyObject* audio_listener_get_window_size(ListenerObject* self,
    void* closure);
static PyObject* audio_listener_get_sample_rate(ListenerObject* self,
    void* closure);
static PyObject* audio_listener_repr(ListenerObject* self);
static PyObject* audio_listener_start(ListenerObject* self, PyObject* unused);
static PyObject* audio_listener_stop(ListenerObject* self, PyObject* unused);
static PyObject* audio_listener_set(ListenerObject* self, PyObject* value,
    void* closure);
static int audio_listener_callback(const void *input, void *unused,
    unsigned long frames_per_buffer, const PaStreamCallbackTimeInfo* time_info,
    PaStreamCallbackFlags status_flags, void *userData);
static void* audio_listener_analyze(void* data);

static PyObject* audio_listener_new(PyTypeObject* type, PyObject* args,
    PyObject* kwargs)
{
    static char* kwlist[] = {"device", "window_size", "interval",
        "sample_rate", NULL};
    
    PyObject* device = NULL;
    PaDeviceIndex device_index;
    Py_ssize_t window_size = 4096;
    Py_ssize_t interval = 1024;
    double sample_rate = 0.0;
    
    int result = PyArg_ParseTupleAndKeywords(args, kwargs, "|Onnd", kwlist,
        &device, &window_size, &interval, &sample_rate);
    if (!result)
        return NULL;
    
    if (sizeof(float) != sizeof(sample_t)) {
        PyErr_Format(PyExc_RuntimeError,
            "The size of a float should be %lu bytes, not %lu.",
            sizeof(sample_t), sizeof(float));
        return NULL;
    }
    
    if (device != NULL) {
        if (!PyObject_TypeCheck(device, &DeviceType)) {
            PyErr_SetString(PyExc_TypeError,
                "The device parameter must be an audio.Device object");
            return NULL;
        }
        device_index = ((DeviceObject*) device)->index;
    } else {
        device_index = Pa_GetDefaultInputDevice();
        if (device_index == paNoDevice) {
            PyErr_SetString(PyExc_RuntimeError,
                "PortAudio knows no default input device.");
            return NULL;
        }
    }
    
    ListenerObject* self = (ListenerObject*) type->tp_alloc(type, 0);
    if (self != NULL) {
        listen_debug("Allocated a new audio listener.\n");
        
        if (pthread_mutex_init(&self->sync, NULL) != 0) {
            Py_DECREF(self);
            PyErr_SetFromErrno(PyExc_OSError);
            return NULL;
        }
        
        if (pthread_cond_init(&self->ready_for_fft, NULL) != 0) {
            pthread_mutex_destroy(&self->sync);
            
            Py_DECREF(self);
            PyErr_SetFromErrno(PyExc_OSError);
            return NULL;
        }
        
        self->staging_buffer =
            (sample_t*) fftw_malloc(sizeof(sample_t) * window_size * 2);
        if (self->staging_buffer == NULL) {
            Py_DECREF(self);
            return PyErr_NoMemory();
        }
        self->staging_buffer_size = window_size * 2;
        self->staging_buffer_end = self->staging_buffer +
            self->staging_buffer_size;
        self->staging_area = self->staging_buffer;
        
        self->fft_buffer =
            (sample_t*) fftw_malloc(sizeof(sample_t) * window_size);
        if (self->fft_buffer == NULL) {
            fftw_free(self->staging_buffer);
            Py_DECREF(self);
            return PyErr_NoMemory();
        }
        
        self->active = 0;
        self->stream = NULL;
        self->result_queue = NULL;
        self->device = device_index;
        self->window_size = window_size;
        self->interval = interval;
        self->sample_rate = sample_rate;
    }
    
    return (PyObject*) self;
}

static int audio_listener_init(ListenerObject* self, PyObject* args,
    PyObject* kwargs)
{
    PaStreamParameters input_params;
    
    const PaDeviceInfo* info = Pa_GetDeviceInfo(self->device);
    listen_debug("Initializing an audio listener on \"%s\".\n", info->name);
    
    memset(&input_params, 0, sizeof(PaStreamParameters));
    input_params.channelCount = 1;
    input_params.device = self->device;
    input_params.sampleFormat = paFloat32;
    input_params.suggestedLatency = info->defaultLowInputLatency;
    
    double sample_rate = self->sample_rate;
    if (sample_rate == 0.0)
        sample_rate = info->defaultSampleRate;
    
    // Check if the input format we're about to ask for is supported.
    PaError err = Pa_IsFormatSupported(&input_params, NULL, sample_rate);
    if (err != paFormatIsSupported) {
        PyErr_Format(PyExc_ValueError, "Unsupported input format: %s (%d)",
            Pa_GetErrorText(err), (int) err);
        Py_DECREF(self);
        return -1;
    }
    
    // Open a PortAudio input stream that we can listen to. Note that this
    // call does not start sending audio samples to our callback function;
    // that happens in Listener.start (audio_listener_start).
    err = Pa_OpenStream(&self->stream, &input_params, NULL, sample_rate,
        self->interval, paNoFlag, audio_listener_callback, (void*) self);
    if (err != paNoError) {
        PyErr_Format(PyExc_RuntimeError,
            "Failed to open input stream: %s (%d)", Pa_GetErrorText(err),
            (int) err);
        Py_DECREF(self);
        return -1;
    }
    
    return 0; // success!
}

static void audio_listener_dealloc(ListenerObject* self)
{
    listen_debug("Deallocating an audio listener.\n");
    
    if (self->stream != NULL) {
        Pa_CloseStream(&self->stream);
        self->stream = NULL;
    }
    
    fftw_free(self->fft_buffer);
    fftw_free(self->staging_buffer);
    Py_XDECREF(self->result_queue);
    
    pthread_cond_destroy(&self->ready_for_fft);
    pthread_mutex_destroy(&self->sync);
    
    self->ob_type->tp_free(self);
}

static PyObject* audio_listener_get_device(ListenerObject* self,
    void* closure)
{
    DeviceObject* device = PyObject_New(DeviceObject, &DeviceType);
    if (device == NULL) {
        return PyErr_NoMemory();
    }
    
    PyObject* args = Py_BuildValue("(i)", (int) self->device);
    if (audio_device_init(device, args, NULL) != 0) {
        Py_DECREF(device);
        return NULL;
    }
    
    return (PyObject*) device;
}

static PyObject* audio_listener_get_interval(ListenerObject* self,
    void* closure)
{
    return PyInt_FromSsize_t(self->interval);
}

static PyObject* audio_listener_get_window_size(ListenerObject* self,
    void* closure)
{
    return PyInt_FromSsize_t(self->window_size);
}

static PyObject* audio_listener_get_sample_rate(ListenerObject* self,
    void* closure)
{
    return PyFloat_FromDouble(self->sample_rate);
}

static PyObject* audio_listener_set(ListenerObject* self, PyObject* value,
    void* closure)
{
    PyErr_SetString(PyExc_AttributeError, "can't set attribute");
    return NULL;
}

static PyObject* audio_listener_start(ListenerObject* self, PyObject* unused)
{
    PyThreadState* _save;
    Py_UNBLOCK_THREADS
    pthread_mutex_lock(&self->sync);
    
    if (self->active) {
        pthread_mutex_unlock(&self->sync);
        Py_BLOCK_THREADS
        PyErr_SetString(PyExc_RuntimeError, "listener is already running");
        return NULL;
    }
    
    memset(self->staging_buffer, 0,
        sizeof(sample_t*) * self->staging_buffer_size);
    
    Py_BLOCK_THREADS
    
    self->result_queue = PyObject_New(QueueObject, &QueueType);
    if (self->result_queue == NULL) {
        pthread_mutex_unlock(&self->sync);
        return PyErr_NoMemory();
    }
    
    int err = pthread_create(&self->analysis_thread, NULL,
        audio_listener_analyze, (void*) self);
    if (err != 0) {
        pthread_mutex_unlock(&self->sync);
        PyErr_SetObject(PyExc_OSError,
            Py_BuildValue("(i, s)", err, "Failed to create analysis thread"));
        return NULL;
    }
    
    // Wait for the analysis thread to signal its startup before we start the
    // PyAudio stream.
    pthread_cond_wait(&self->ready_for_fft, &self->sync);
    
    PaError start_err = Pa_StartStream(self->stream);
    if (start_err != paNoError) {
        // signal startup error to the analysis thread
        self->active = -1; 
        pthread_cond_broadcast(&self->ready_for_fft);
        
        pthread_mutex_unlock(&self->sync);
        PyErr_SetObject(PyExc_RuntimeError,
            Py_BuildValue("(s, i)", "Failed to initialize PortAudio",
                (int) start_err));
        return NULL;
    }
    
    // successful startup!
    pthread_mutex_unlock(&self->sync);
    
    return (PyObject*) self->result_queue;
}

static PyObject* audio_listener_stop(ListenerObject* self, PyObject* unused)
{
    Py_BEGIN_ALLOW_THREADS
    
    pthread_mutex_lock(&self->sync);
    self->active = 0;
    pthread_cond_broadcast(&self->ready_for_fft);
    pthread_mutex_unlock(&self->sync);
    
    if (self->stream != NULL && Pa_IsStreamActive(self->stream)) {
        Pa_StopStream(self->stream);
    }
    
    pthread_join(self->analysis_thread, NULL);
    
    Py_END_ALLOW_THREADS
    Py_XDECREF(self->result_queue);
    Py_RETURN_NONE;
}

static PyObject* audio_listener_repr(ListenerObject* self)
{
    const char* status =
        (self->stream != NULL && Pa_IsStreamActive(self->stream))
            ? "running"
            : "stopped";
    
    const PaDeviceInfo* info = Pa_GetDeviceInfo(self->device);
    
    return PyString_FromFormat("<%s on %s; %s>", self->ob_type->tp_name,
        info->name, status);
}

static int audio_listener_callback(const void *input, void *unused,
    unsigned long frames_per_buffer, const PaStreamCallbackTimeInfo* time_info,
    PaStreamCallbackFlags status_flags, void *data)
{
    // ListenerObject* self = (ListenerObject*) data;
    #warning audio listener callback not implemented
    return paContinue; // OK
}

static void* audio_listener_analyze(void* data)
{
    ListenerObject* self = (ListenerObject*) data;
    
    // audio_listener_start() waits for the analysis thread to signal its
    // startup, so let's oblige it
    pthread_mutex_lock(&self->sync);
    self->active = 1;
    pthread_cond_broadcast(&self->ready_for_fft);
    
    // main FFT analysis loop
    // (note that we still have the lock as we enter it the first time)
    while (1) {
        while (self->active > 0 && self->samples_collected < self->window_size)
            pthread_cond_wait(&self->ready_for_fft, &self->sync);
        
        if (self->active <= 0) {
            self->active = 0;
            break;
        }
        
        #warning audio analysis not implemented
    }
    
    pthread_mutex_unlock(&self->sync);
    pthread_exit(NULL);
}

static PyGetSetDef Listener_getset[] = {
    {"device", (getter) audio_listener_get_device, (setter) audio_listener_set,
        "The audio input device being used", NULL},
    {"interval", (getter) audio_listener_get_interval,
        (setter) audio_listener_set,
        "The interval (in samples) between FFT runs", NULL},
    {"window_size", (getter) audio_listener_get_window_size,
        (setter) audio_listener_set,
        "The size of the FFT window (in samples)", NULL},
    {"sample_rate", (getter) audio_listener_get_sample_rate,
        (setter) audio_listener_set,
        "The sample rate (in Hz) of the audio input stream",
        NULL},
    {NULL}  /* Sentinel */
};

static const char _start_help[] = "Starts listening to the input device.\n \
On success, returns a blocking queue that will be populated with \
discovered frequency sets.";

static PyMethodDef Listener_methods[] = {
    {"start", (PyCFunction) audio_listener_start, METH_NOARGS, _start_help},
    {"stop", (PyCFunction) audio_listener_stop, METH_NOARGS,
        "Stops listening to the input device."},
    {NULL} // sentinel
};

PyTypeObject ListenerType = {
    PyObject_HEAD_INIT(NULL)
    0,                         /*ob_size*/
    "audio.Listener",            /*tp_name*/
    sizeof(ListenerObject),      /*tp_basicsize*/
    0,                         /*tp_itemsize*/
    (destructor)audio_listener_dealloc, /*tp_dealloc*/
    0,                         /*tp_print*/
    0,                         /*tp_getattr*/
    0,                         /*tp_setattr*/
    0,                         /*tp_compare*/
    (reprfunc)audio_listener_repr,         /*tp_repr*/
    0,                         /*tp_as_number*/
    0,                         /*tp_as_sequence*/
    0,                         /*tp_as_mapping*/
    0,                         /*tp_hash */
    0,                         /*tp_call*/
    0,                         /*tp_str*/
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
    Listener_methods,          /* tp_methods */
    0,                         /* tp_members */
    Listener_getset,           /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    (initproc)audio_listener_init,/* tp_init */
    0,                         /* tp_alloc */
    audio_listener_new,        /* tp_new */
};
