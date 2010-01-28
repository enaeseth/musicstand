#define debug_malloc(ptr, desc) fprintf(stderr, "Allocated %s at 0x%016lX.\n", \
    desc, (uintptr_t) ptr)
#define debug_free(ptr, desc) fprintf(stderr, "Freeing %s at 0x%016lX.\n", \
    desc, (uintptr_t) ptr)

#define _INCREF(o) fprintf(stderr, "Adding reference to 0x%016lX.\n", \
    (uintptr_t) o); Py_INCREF(o)
#define _XINCREF(o) fprintf(stderr, "Adding reference to 0x%016lX.\n", \
    (uintptr_t) o); Py_XINCREF(o)
#define _DECREF(o) fprintf(stderr, "Removing reference to 0x%016lX.\n", \
    (uintptr_t) o); Py_DECREF(o)
#define _XDECREF(o) fprintf(stderr, "Safely removing reference to 0x%016lX.\n", \
    (uintptr_t) o); Py_XDECREF(o)
