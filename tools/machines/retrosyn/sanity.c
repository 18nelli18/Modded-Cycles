/* Origin: AveyCole fork (https://github.com/AveyCole/Modded-Cycles), MIT License.
 * Balayage de tous les réglages sous UBSan : aucun débordement signé, aucune lecture hors table, sortie bornée. */
#include <stdio.h>
#include <stdlib.h>
#include "retrosyn_dsp.h"
int main(void)
{
	retrosyn_t s; s32 out[RS_BLOCK]; long blocks = 0; srand(1);
	for (int it = 0; it < 3000; it++) {
		retrosyn_in_t in;
		in.note = (rand() % 128) << 16 | (rand() & 0xffff);
		if (in.note > (127 << 16)) in.note = 127 << 16;
		in.shape = rand() % 32768; in.color = rand() % 32768; in.sweep = rand() % 32768; in.contour = rand() % 32768;
		in.punch = rand() & 1;
		if (it % 7 == 0) { in.shape = 32767; in.color = 32767; in.sweep = 32767; in.contour = 32767; }
		if (it % 11 == 0) { in.shape = 0; in.color = 0; in.sweep = 0; in.contour = 0; in.note = 0; }
		retrosyn_reset(&s);
		for (int b = 0; b < 150; b++) {                       /* ~0,1 s : passe les ticks d'arpège et de balayage */
			in.trig = b == 0;
			retrosyn_block(&s, &in, out);
			for (int n = 0; n < RS_BLOCK; n++)
				if (out[n] > (1 << 29) || out[n] < -(1 << 29)) { printf("out of range %d\n", out[n]); return 1; }
			blocks++;
		}
	}
	printf("sanity ok: %ld blocks\n", blocks);
	return 0;
}
