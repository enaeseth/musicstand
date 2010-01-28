/**
 * Choose between single- and double-precision FFTW implementations.
 */

#ifndef _FFT_H_
#define _FFT_H_

#include <fftw3.h>
#include <stdint.h>

#ifdef SINGLE_PRECISION_FFT
#define _fft_malloc fftwf_malloc
#define _fft_free fftwf_free
#define _fft_plan fftwf_plan_r2r_1d
#define _fft_execute fftwf_execute
#define _fft_destroy_plan fftwf_destroy_plan
#else
#define _fft_malloc fftw_malloc
#define _fft_free(p) fprintf(stderr, "FFTW-freeing 0x%016lX.\n", \
     (uintptr_t) p); fftw_free(p)
#define _fft_plan fftw_plan_r2r_1d
#define _fft_execute fftw_execute
#define _fft_destroy_plan fftw_destroy_plan
#endif

#endif /* end of include guard: _FFT_H_ */
