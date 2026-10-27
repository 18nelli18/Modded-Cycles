/* Origin: AveyCole fork (https://github.com/AveyCole/Modded-Cycles), MIT License.
 * Hôte : le même retrosyn_dsp.h, appelé depuis Python (ctypes) pour les preuves. */
#include <stdlib.h>
#include "retrosyn_dsp.h"

retrosyn_t *rs_new(void) { retrosyn_t *s = calloc(1, sizeof *s); retrosyn_reset(s); return s; }
void rs_free(retrosyn_t *s) { free(s); }
void rs_block_c(retrosyn_t *s, int note, int trig, int shape, int color, int sweep, int contour, int punch, int *out)
{
	retrosyn_in_t in = {note, trig, shape, color, sweep, contour, punch};
	retrosyn_block(s, &in, out);
}
int rs_lfsr_period(int bits)
{
	u32 seed = bits == 7 ? 0x7f : 0x7fff, l = seed;
	int n = 0;
	do { l = rs_lfsr(l, bits); n++; } while (l != seed && n < 100000);
	return n;
}
unsigned rs_inc_c(int pitch) { return rs_inc(pitch); }
