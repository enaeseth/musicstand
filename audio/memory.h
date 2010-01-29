#define debug_malloc(ptr, desc) fprintf(stderr, "Allocated %s at 0x%016lX.\n", \
    desc, (uintptr_t) ptr)
#define debug_free(ptr, desc) fprintf(stderr, "Freeing %s at 0x%016lX.\n", \
    desc, (uintptr_t) ptr)

