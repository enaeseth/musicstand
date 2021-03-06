/**
 * Listens to an audio input device and performs frequency decomposition.
 */

#include <string.h>
#include <math.h>
#include "listen.h"
#include "devices.h"
#include "fft.h"

#ifdef DEBUG
#define listen_debug(_message) \
     PySys_WriteStderr("[listen.c:%d] " _message, __LINE__)
#define listen_debug_f(_format, ...) \
     PySys_WriteStderr("[listen.c:%d] " _format, __LINE__, __VA_ARGS__)
#else
#define listen_debug(_message)
#define listen_debug_f(_format, ...)
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
        "sample_rate", "filters", NULL};
    
    PyObject* device = NULL;
    PaDeviceIndex device_index;
    Py_ssize_t window_size = 4096;
    Py_ssize_t interval = 1024;
    double sample_rate = 0.0;
    PyObject* filters = NULL;
    FilterChain* filter_chain = NULL;
    
    int result = PyArg_ParseTupleAndKeywords(args, kwargs, "|OnndO", kwlist,
        &device, &window_size, &interval, &sample_rate, &filters);
    if (!result)
        return NULL;
    
    if (sizeof(float) != sizeof(sample_t)) {
        PyErr_Format(PyExc_RuntimeError,
            "The size of a float should be %lu bytes, not %lu.",
            sizeof(sample_t), sizeof(float));
        return NULL;
    }
    
    if (device != NULL && device != Py_None) {
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
    
    if (filters != NULL && filters != Py_None) {
        filter_chain = FilterChain_Prepare(filters);
        if (filter_chain == NULL)
            return NULL;
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
            ringbuffer_create(sizeof(sample_t) * window_size * 6);
        if (self->staging_buffer == NULL) {
            Py_DECREF(self);
            return PyErr_NoMemory();
        }
        
        self->fft_buffer =
            (fft_sample_t*) _fft_malloc(sizeof(fft_sample_t) * window_size);
        if (self->fft_buffer == NULL) {
            ringbuffer_destroy(self->staging_buffer);
            self->staging_buffer = NULL;
            Py_DECREF(self);
            return PyErr_NoMemory();
        }
        
        self->fft_result_buffer =
            (fft_sample_t*) _fft_malloc(sizeof(fft_sample_t) * window_size);
        if (self->fft_buffer == NULL) {
            ringbuffer_destroy(self->staging_buffer);
            _fft_free(self->fft_buffer);
            self->staging_buffer = NULL;
            self->fft_buffer = NULL;
            Py_DECREF(self);
            return PyErr_NoMemory();
        }
        
        self->plan = _fft_plan((int) window_size, self->fft_buffer,
            self->fft_result_buffer, FFTW_HC2R, 0);
        
        self->active = 0;
        self->stream = NULL;
        self->result_queue = NULL;
        self->device = device_index;
        self->window_size = (size_t) window_size;
        self->interval = (size_t) interval;
        self->interval_ratio = ((double) interval) / window_size;
        self->sample_rate = sample_rate;
        self->sample_duration = (1 / sample_rate);
        self->filter_chain = filter_chain;
    }
    
    return (PyObject*) self;
}

static int audio_listener_init(ListenerObject* self, PyObject* args,
    PyObject* kwargs)
{
    PaStreamParameters input_params;
    
    const PaDeviceInfo* info = Pa_GetDeviceInfo(self->device);
    listen_debug_f("Initializing an audio listener on \"%s\".\n", info->name);
    
    memset(&input_params, 0, sizeof(PaStreamParameters));
    input_params.channelCount = 1;
    input_params.device = self->device;
    input_params.sampleFormat = paFloat32;
    input_params.suggestedLatency = info->defaultLowInputLatency;
    
    double sample_rate = self->sample_rate;
    if (sample_rate == 0.0) {
        sample_rate = info->defaultSampleRate;
        self->sample_rate = sample_rate;
        self->sample_duration = (1 / sample_rate);
    }
    
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
    
    if (self->active > 0) {
        if (audio_listener_stop(self, NULL) == NULL)
            return;
    }
    
    if (self->stream != NULL) {
        Pa_CloseStream(&self->stream);
        self->stream = NULL;
    }
    
    _fft_free(self->fft_buffer);
    _fft_free(self->fft_result_buffer);
    ringbuffer_destroy(self->staging_buffer);
    self->staging_buffer = NULL;
    self->fft_buffer = self->fft_result_buffer = NULL;
    _fft_destroy_plan(self->plan);
    
    if (self->filter_chain != NULL) {
        FilterChain_Destroy(self->filter_chain);
        self->filter_chain = NULL;
    }
    
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
    
    ringbuffer_clear(self->staging_buffer);
    
    Py_BLOCK_THREADS
    
    self->result_queue = audio_queue_create(NULL);
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
    if (self->active == -2) {
        pthread_mutex_unlock(&self->sync);
        return PyErr_NoMemory();
    } else if (self->active <= 0) {
        pthread_mutex_unlock(&self->sync);
        PyErr_SetObject(PyExc_RuntimeError,
            Py_BuildValue("(s, i)", "Failed to start analysis thread",
                self->active));
        return NULL;
    } else {
        listen_debug_f("Analysis thread signalled startup: %d.\n",
            self->active);
    }
    
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
    } else {
        listen_debug("Successfully started PortAudio stream.\n");
    }
    
    // successful startup!
    pthread_mutex_unlock(&self->sync);
    
    Py_INCREF(self->result_queue);
    return (PyObject*) self->result_queue;
}

static PyObject* audio_listener_stop(ListenerObject* self, PyObject* unused)
{
    listen_debug("Stopping the audio listener.\n");
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
    listen_debug("Analysis thread has exited.\n");
    Py_XDECREF(self->result_queue);
    self->result_queue = NULL;
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
    ListenerObject* self = (ListenerObject*) data;
    
    size_t input_size = (sizeof(sample_t) * frames_per_buffer);
    
    if (status_flags & paInputOverflow)
        fprintf(stderr, "warning: audio input buffer has overflowed\n");
    
    if (ringbuffer_write(self->staging_buffer, input, input_size) == 0) {
        fprintf(stderr, "warning: insufficient space in staging buffer\n");
    }
    // fprintf(stderr, "Received %lu audio samples.\n", frames_per_buffer);
    
    return paContinue; // OK
}

static fft_result_t* filter_and_create_result(ListenerObject* listener,
    fft_sample_t* intensities)
{
    double sample_rate = listener->sample_rate;
    size_t window_size = listener->window_size;
    
    fft_result_t* result = fft_result_create(listener->window_size, 0.0, NULL);
    if (result == NULL)
        return NULL;
    
    double frequency;
    fft_sample_t intensity;
    for (size_t i = 0; i < window_size; i++) {
        frequency = sample_rate * ((double) i) / window_size;
        intensity = intensities[i];
        
        if (fft_result_append(result, frequency, intensity) != 0) {
            audio_queue_signal_oom(listener->result_queue);
            listener->active = 0;
            fft_result_destroy(result);
            return NULL;
        }
    }
    
    if (listener->filter_chain != NULL) {
        int filter_result = FilterChain_Execute(listener->filter_chain,
            (size_t*) &result->length, result->buckets);
        
        if (filter_result != 0) {
            fprintf(stderr, "warning: FilterChain_Execute returned %d\n",
                filter_result);
            fft_result_destroy(result);
            return NULL;
        }
    }
    
    return result;
}

static void blackman(sample_t* samples, size_t count)
{
    static double alpha = 0.16;
    double a_2 = (alpha / 2);
    static double pies = M_PI * 2.0;
    size_t i;
    size_t almost = count - 1;
    
    for (i = 0; i < count; i++) {
        double mult = ((1-alpha) / 2) - 0.5 * cos(pies * i / almost) +
            a_2 * cos(2 * pies * i / almost);
        samples[i] *= mult;
    }
}

static void* audio_listener_analyze(void* data)
{
    ListenerObject* self = (ListenerObject*) data;
    size_t read;
    size_t peek_size = sizeof(sample_t) * self->window_size;
    size_t advance_size = sizeof(sample_t) * self->interval;
    sample_t* peek_dest;
    int gil_required = 0;
    PyGILState_STATE gil_state;
    PyThreadState* _save = NULL;

#ifdef SINGLE_PRECISION_FFT
    peek_dest = self->fft_buffer;
#else
    sample_t* short_samples = _fft_malloc(peek_size);
    peek_dest = short_samples;
#endif
    
    // audio_listener_start() waits for the analysis thread to signal its
    // startup, so let's oblige it
    pthread_mutex_lock(&self->sync);
#ifdef SINGLE_PRECISION_FFT
    self->active = 1;
#else
    self->active = (short_samples != NULL) ? 1 : -2;
#endif
    pthread_cond_broadcast(&self->ready_for_fft);
    pthread_mutex_unlock(&self->sync);

#ifndef SINGLE_PRECISION_FFT
    if (short_samples == NULL)
        pthread_exit(NULL);
#endif
    
    if (self->filter_chain)
        gil_required = FilterChain_RequiresGIL(self->filter_chain);
    
    if (gil_required) {
        gil_state = PyGILState_Ensure();
        Py_UNBLOCK_THREADS
    }
    
    fft_result_t* result;
    
    while (self->active > 0) {
        read = ringbuffer_peek(self->staging_buffer, peek_dest, peek_size);
        if (read < peek_size) {
            // sleep for a bit until we get some more samples
            usleep(1000000 * (self->interval * self->sample_duration));
            continue;
        }
        
        ringbuffer_advance_read(self->staging_buffer, advance_size);
        
        blackman(peek_dest, self->window_size);
        
#ifndef SINGLE_PRECISION_FFT
        for (size_t i = 0; i < self->window_size; i++) {
            self->fft_buffer[i] = (double) peek_dest[i];
        }
#endif
        
        _fft_execute(self->plan);
        
        result = filter_and_create_result(self, self->fft_result_buffer);
        if (result == NULL) {
            continue;
        }
        
        audio_queue_push(self->result_queue, result);
    }

#ifndef SINGLE_PRECISION_FFT
    _fft_free(short_samples);
#endif
    
    if (gil_required) {
        Py_BLOCK_THREADS
        PyGILState_Release(gil_state);
    }
    
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
