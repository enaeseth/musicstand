/**
 * A filter that coalesces FFT bucket frequencies into actual note frequencies.
 */

#include "../filter.h"
#include <string.h>
#include <math.h>

#ifdef DEBUG
#include <stdio.h>

#define coalece_debug(_message) \
     fprintf(stderr, "[coalesce.c:%d] " _message, __LINE__)
#define coalece_debug_f(_format, ...) \
     fprintf(stderr, "[coalesce.c:%d] " _format, __LINE__, __VA_ARGS__)
#else
#define coalece_debug(_message)
#define coalece_debug_f(_format, ...)
#endif

static double key_frequencies[88]; // forward declaration

typedef struct {
    size_t index;
    double multiplier;
} bucket_source_t;

typedef struct {
    size_t count;
    bucket_source_t sources[];
} bucket_source_list_t;

typedef struct {
    FilterObject_HEAD
    size_t incoming_bucket_count;
    size_t target_count;
    bucket_t* target_buckets;
    bucket_source_list_t** sources;
} CoalesceFilterObject;

static int map_buckets(CoalesceFilterObject* self, bucket_t* buckets,
    size_t length);
static void delete_bucket_mapping(CoalesceFilterObject* self);

static int CoalesceFilter_Execute(CoalesceFilterObject* self, size_t* length,
    bucket_t* buckets)
{
    bucket_source_list_t* bucket_sources;
    bucket_t* target_buckets = self->target_buckets;
    
    if (*length != self->incoming_bucket_count) {
        int result = map_buckets(self, buckets, *length);
        if (result != 0)
            return result;
    }
    
    size_t target_count = self->target_count;
    for (size_t i = 0; i < target_count; i++) {
        bucket_sources = self->sources[i];
        target_buckets[i].intensity = 0.0;
        
        for (size_t j = 0; j < bucket_sources->count; j++) {
            bucket_source_t* source = &bucket_sources->sources[j];
            target_buckets[i].intensity +=
                (source->multiplier * buckets[source->index].intensity);
        }
    }
    
    memcpy(buckets, target_buckets, sizeof(bucket_t) * self->target_count);
    *length = self->target_count;
    return 0;
}

static PyObject* CoalesceFilter_new(PyTypeObject* subtype, PyObject* args,
    PyObject* kwds)
{
    CoalesceFilterObject* filter =
        (CoalesceFilterObject*) PyType_GenericNew(subtype, args, kwds);
    size_t bucket_count = sizeof(key_frequencies) / sizeof(double);
    size_t bucket_mem_size = sizeof(bucket_t) * bucket_count;
    
    if (filter != NULL) {
        filter->incoming_bucket_count = 0;
        filter->sources = NULL;
        
        filter->target_count = bucket_count;
        filter->target_buckets = PyMem_Malloc(bucket_mem_size);
        if (filter->target_buckets == NULL) {
            Py_DECREF(filter);
            return NULL;
        }
        
        memset(filter->target_buckets, 0, bucket_mem_size);
    }
    
    return (PyObject*) filter;
}

static int CoalesceFilter_init(CoalesceFilterObject* self, PyObject* args,
    PyObject* kwds)
{
    size_t bucket_count = self->target_count;
    for (size_t i = 0; i < bucket_count; i++) {
        self->target_buckets[i].frequency = key_frequencies[i];
    }
    
    self->impl = (filter_cb) CoalesceFilter_Execute;
    
    return 0;
}

static PyObject* CoalesceFilter_repr(CoalesceFilterObject* self)
{
    return PyString_FromFormat("%s()", self->ob_type->tp_name);
}

static void CoalesceFilter_dealloc(CoalesceFilterObject* self) {
    if (self->target_buckets != NULL) {
        PyMem_Free(self->target_buckets);
        self->target_buckets = NULL;
    }
    if (self->sources != NULL) {
        delete_bucket_mapping(self);
    }
    self->ob_type->tp_free(self);
}

static inline int allocate_source_list(bucket_source_list_t** list,
    size_t count)
{
    bucket_source_list_t* new_ptr = realloc(*list,
        sizeof(bucket_source_list_t) + (count * sizeof(bucket_source_t)));
    if (new_ptr == NULL) {
        free(*list);
        return 0;
    }
    
    *list = new_ptr;
    new_ptr->count = count;
    return 1;
}

static inline double get_multiplier(double span, double note,
    double incoming_freq)
{
    return fabs(incoming_freq - note) / span;
}

static int map_buckets(CoalesceFilterObject* self, bucket_t* buckets,
    size_t length)
{
    bucket_t* targets = self->target_buckets;
    
    if (self->sources != NULL)
        delete_bucket_mapping(self);
    
    self->sources = calloc(self->target_count, sizeof(bucket_source_list_t*));
    if (self->sources == NULL)
        return -1;
    
    size_t d = 0;
    for (size_t i = 0; i < length; i++) {
        bucket_t* incoming = (buckets + i);
        
        while (incoming->frequency >= self->target_buckets[d].frequency) {
            bucket_source_list_t* source_list;
            size_t count = (i == 0) ? 1 : 2;
            
            if (!allocate_source_list(&self->sources[d], count)) {
                delete_bucket_mapping(self);
                return -1;
            }
            
            source_list = self->sources[d];
            
            if (i == 0) {
                source_list->sources[0].index = i;
                source_list->sources[0].multiplier = 1.0;
            } else {
                double span = (incoming->frequency - buckets[i-1].frequency);
                double note_freq = targets[d].frequency;
                
                source_list->sources[0].index = i - 1;
                source_list->sources[0].multiplier = get_multiplier(span,
                    note_freq, buckets[i-1].frequency);
                
                source_list->sources[1].index = i;
                source_list->sources[1].multiplier = get_multiplier(span,
                    note_freq, incoming->frequency);
            }
            
            d++;
            
            if (d >= self->target_count)
                break;
        }
        
        if (d >= self->target_count)
            break;
    }

#ifdef DEBUG
    coalece_debug("Created coalescence mapping:\n");
    for (size_t i = 0; i < self->target_count; i++) {
        bucket_source_list_t* source_list = self->sources[i];
        fprintf(stderr, "%7.2f = ", self->target_buckets[i].frequency);
        
        for (size_t j = 0; j < source_list->count; j++) {
            bucket_source_t* source = (source_list->sources + j);
            if (j > 0)
                fprintf(stderr, " + ");
            fprintf(stderr, "(%.03f * v[%7.2f])", source->multiplier,
                buckets[source->index].frequency);
        }
        fprintf(stderr, "\n");
    }
#endif
    
    self->incoming_bucket_count = length;
    return 0;
}

static void delete_bucket_mapping(CoalesceFilterObject* self)
{
    for (size_t i = 0; i < self->target_count; i++) {
        free(self->sources[i]);
    }
    free(self->sources);
    self->sources = NULL;   
}

FilterType_SUBCLASS(CoalesceFilter, 0,
    "Maps incoming buckets onto actual note frequencies.");

static double key_frequencies[] = {
      27.500000, // A0
      29.135235, // A#0
      30.867706, // B0
      32.703196, // C1
      34.647829, // C#1
      36.708096, // D1
      38.890873, // D#1
      41.203445, // E1
      43.653529, // F1
      46.249303, // F#1
      48.999429, // G1
      51.913087, // G#1
      55.000000, // A1
      58.270470, // A#1
      61.735413, // B1
      65.406391, // C2
      69.295658, // C#2
      73.416192, // D2
      77.781746, // D#2
      82.406889, // E2
      87.307058, // F2
      92.498606, // F#2
      97.998859, // G2
     103.826174, // G#2
     110.000000, // A2
     116.540940, // A#2
     123.470825, // B2
     130.812783, // C3
     138.591315, // C#3
     146.832384, // D3
     155.563492, // D#3
     164.813778, // E3
     174.614116, // F3
     184.997211, // F#3
     195.997718, // G3
     207.652349, // G#3
     220.000000, // A3
     233.081881, // A#3
     246.941651, // B3
     261.625565, // C4
     277.182631, // C#4
     293.664768, // D4
     311.126984, // D#4
     329.627557, // E4
     349.228231, // F4
     369.994423, // F#4
     391.995436, // G4
     415.304698, // G#4
     440.000000, // A4
     466.163762, // A#4
     493.883301, // B4
     523.251131, // C5
     554.365262, // C#5
     587.329536, // D5
     622.253967, // D#5
     659.255114, // E5
     698.456463, // F5
     739.988845, // F#5
     783.990872, // G5
     830.609395, // G#5
     880.000000, // A5
     932.327523, // A#5
     987.766603, // B5
    1046.502261, // C6
    1108.730524, // C#6
    1174.659072, // D6
    1244.507935, // D#6
    1318.510228, // E6
    1396.912926, // F6
    1479.977691, // F#6
    1567.981744, // G6
    1661.218790, // G#6
    1760.000000, // A6
    1864.655046, // A#6
    1975.533205, // B6
    2093.004522, // C7
    2217.461048, // C#7
    2349.318143, // D7
    2489.015870, // D#7
    2637.020455, // E7
    2793.825851, // F7
    2959.955382, // F#7
    3135.963488, // G7
    3322.437581, // G#7
    3520.000000, // A7
    3729.310092, // A#7
    3951.066410, // B7
    4186.009045, // C8
};
