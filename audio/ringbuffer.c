/**
 * An implementation of a ring buffer.
 *
 * Lovingly based on the ring buffer implementation in JACK.
 */

#include "ringbuffer.h"
#include "fft.h"
#include <unistd.h>
#include <string.h>

ringbuffer_t ringbuffer_create(size_t size)
{
    int power_of_two = 1;
    ringbuffer_t rb =
        (ringbuffer_t) _fft_malloc(sizeof(struct ringbuffer));
    
    if (rb == NULL)
        return NULL;
    
    // scale `size` up to the nearest power of two; this allows us to use bit
    // twiddling to implement the wrap-around-to-the-beginning behavior
    while ((1 << power_of_two) < size)
        power_of_two++;
    
    size = (1 << power_of_two);
    
    void* buffer = _fft_malloc(size);
    if (buffer == NULL) {
        _fft_free(rb);
        return NULL;
    }
    
    rb->buf = buffer;
    rb->size = size;
    rb->size_mask = size;
    rb->size_mask -= 1;
    rb->write_pos = rb->read_pos = 0;
    
    return rb;
}

void ringbuffer_destroy(ringbuffer_t rb)
{
    if (rb->buf != NULL) {
        _fft_free(rb->buf);
        rb->buf = NULL;
        _fft_free(rb);
    }
}

void ringbuffer_clear(ringbuffer_t rb)
{
    rb->write_pos = rb->read_pos = 0;
    memset(rb->buf, 0, rb->size);
}

#define _RINGBUFFER_READ(rb, dest, count) \
    memcpy((dest), (rb->buf + rb->read_pos), count); \
    rb->read_pos = (rb->read_pos + count) & rb->size_mask
size_t ringbuffer_read(ringbuffer_t rb, void* dest, size_t size)
{
    size_t available;
    size_t hypothetical_end;
    size_t n1, n2;
    
    if (rb->buf == NULL)
        return 0;
    
    available = ringbuffer_read_space(rb);
    if (available < size) {
        return 0;
    }
    
    hypothetical_end = rb->read_pos + size;
    
    if (hypothetical_end > rb->size) {
        // wrap around to the start of the buffer
        n1 = (rb->size - rb->read_pos);         // [       |====]
        n2 = hypothetical_end & rb->size_mask;  // [==     |    ]
    } else {
        n1 = size;                              // [  |======   ]
        n2 = 0;
    }
    
    _RINGBUFFER_READ(rb, dest, n1);
    if (n2 > 0) {
        _RINGBUFFER_READ(rb, dest + n1, n2);
    }
    
    return size;
}

size_t ringbuffer_peek(ringbuffer_t rb, void* dest, size_t size)
{
    size_t available;
    size_t hypothetical_end;
    size_t n1, n2;
    size_t read_pos;
    
    if (rb->buf == NULL)
        return 0;
    
    available = ringbuffer_read_space(rb);
    if (available < size) {
        return 0;
    }
    
    read_pos = rb->read_pos;
    hypothetical_end = read_pos + size;
    
    if (hypothetical_end > rb->size) {
        // wrap around to the start of the buffer
        n1 = (rb->size - rb->read_pos);         // [       |====]
        n2 = hypothetical_end & rb->size_mask;  // [==     |    ]
    } else {
        n1 = size;                              // [  |======   ]
        n2 = 0;
    }
    
    memcpy(dest, rb->buf + read_pos, n1);
    read_pos = (read_pos + n1) & rb->size_mask;
    
    if (n2 > 0) {
        memcpy(dest + n1, rb->buf + read_pos, n2);
    }
    
    return size;
}

size_t ringbuffer_read_space(ringbuffer_t rb)
{
    size_t w;
    size_t r;
    
    if (rb->buf == NULL)
        return 0;
    
    w = rb->write_pos;
    r = rb->read_pos;
    
    if (w > r) {
        return (w - r);
    } else {
        return (w - r + rb->size) & rb->size_mask;
    }
}

size_t ringbuffer_advance_read(ringbuffer_t rb, size_t size)
{
    size_t tmp = (rb->read_pos + size) & rb->size_mask;
    rb->read_pos = tmp;
    return size;
}

#define _RINGBUFFER_WRITE(rb, src, count) \
    memcpy((rb->buf + rb->write_pos), (src), count); \
    rb->write_pos = (rb->write_pos + count) & rb->size_mask
size_t ringbuffer_write(ringbuffer_t rb, const void* src, size_t size)
{
    size_t available;
    size_t hypothetical_end;
    size_t n1, n2;
    
    if (rb->buf == NULL)
        return 0;
    
    available = ringbuffer_write_space(rb);
    if (available < size) {
        return 0;
    }
    
    hypothetical_end = rb->read_pos + size;
    
    if (hypothetical_end > rb->size) {
        // wrap around to the start of the buffer
        n1 = (rb->size - rb->write_pos);         // [       |====]
        n2 = hypothetical_end & rb->size_mask;   // [==     |    ]
    } else {
        n1 = size;                               // [  |======   ]
        n2 = 0;
    }
    
    _RINGBUFFER_WRITE(rb, src, n1);
    if (n2 > 0) {
        _RINGBUFFER_WRITE(rb, src + n1, n2);
    }
    
    return size;
}

size_t ringbuffer_write_space(ringbuffer_t rb)
{
    size_t w;
    size_t r;
    
    if (rb->buf == NULL)
        return 0;
    
    w = rb->write_pos;
    r = rb->read_pos;
    
    if (w > r) {
        return ((r - w + rb->size) & rb->size_mask) - 1;
    } else if (w < r) {
        return (r - w) - 1;
    } else {
        return rb->size - 1;
    }
}
