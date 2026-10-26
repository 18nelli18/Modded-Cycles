/* Adaptateur de types/macros pour le quantizer BRAIDS MIT, sans DSP modifie. */
#ifndef BQ_STMLIB_H
#define BQ_STMLIB_H
#include <stdint.h>
#include <stddef.h>
#define DISALLOW_COPY_AND_ASSIGN(T) T(const T&); void operator=(const T&)
static inline int abs(int value) { return value < 0 ? -value : value; }
#define CLIP(x) x = x < -32768 ? -32768 : x > 32767 ? 32767 : x;
#endif
