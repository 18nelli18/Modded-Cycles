#include <stdint.h>
int32_t dx7_math_probe(int32_t x,int32_t y){int32_t z,a=(int32_t)((uint32_t)x<<6);__asm__ volatile("mac.l %1,%2,<<,%%acc0\n\tmovclr.l %%acc0,%0":"=d"(z):"d"(a),"d"(y):"cc");return z;}
