/**
 * An implementation of a ring buffer.
 *
 * Lovingly based on the ring buffer implementation in JACK.
 */

#ifndef _RINGBUFFER_H_
#define _RINGBUFFER_H_

#include <stdlib.h>

typedef struct ringbuffer {
    void* buf;
    volatile size_t write_pos;
    volatile size_t read_pos;
    size_t size;
    size_t size_mask;
} *ringbuffer_t;

ringbuffer_t ringbuffer_create(size_t size);
void ringbuffer_destroy(ringbuffer_t rb);
void ringbuffer_clear(ringbuffer_t rb);

size_t ringbuffer_read(ringbuffer_t rb, void* dest, size_t size);
size_t ringbuffer_peek(ringbuffer_t rb, void* dest, size_t size);
size_t ringbuffer_read_space(ringbuffer_t rb);
size_t ringbuffer_advance_read(ringbuffer_t rb, size_t size);

size_t ringbuffer_write(ringbuffer_t rb, const void* src, size_t size);
size_t ringbuffer_write_space(ringbuffer_t rb);

#endif /* end of include guard: _RINGBUFFER_H_ */
