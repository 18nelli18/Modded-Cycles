/*
 * Le coeur de MODAL (tools/machines/modal/modal_dsp.h) compile pour l'ordinateur, pilote comme rings_ref.cc :
 * memes enregistrements en entree (46 int32 par bloc), memes sorties (out[32] puis aux[32] en float32).
 * Option -i : sortie en int32 (UNIT = 2^24), pour comparer a l'octet pres avec le Cycles.
 */
#include <stdio.h>
#include <string.h>

#include "modal_dsp.h"

static struct modal_part part;

static s32 knob(s32 v)                               /* 0..65536 -> Q31 */
{
	return v >= 65536 ? Q31ONE : (v <= 0 ? 0 : v << 15);
}

int main(int argc, char **argv)
{
	s32 r[46], out[MB], aux[MB];
	int ints = argc > 1 && !strcmp(argv[1], "-i"), k;

	modal_init_tables();
	modal_part_init(&part);
	while (fread(r, sizeof(r), 1, stdin) == 1) {
		struct modal_perf ps;
		struct modal_patch pa;

		modal_set_model(&part, r[0]);
		if (r[1] != part.poly)
			modal_set_poly(&part, r[1]);
		ps.strum = r[2] != 0;
		ps.internal_exciter = r[3] != 0;
		ps.chord = r[4];
		ps.note = r[5];
		ps.tonic = r[6];
		ps.fm = r[7];
		ps.level = Q31ONE;
		pa.structure = knob(r[8]);
		pa.brightness = knob(r[9]);
		pa.damping = knob(r[10]);
		pa.position = knob(r[11]);
		modal_process(&part, &ps, &pa, &r[12], out, aux);
		if (ints) {
			fwrite(out, sizeof(out), 1, stdout);
			fwrite(aux, sizeof(aux), 1, stdout);
		} else {
			float fo[MB], fa[MB];
			for (k = 0; k < MB; k++) {
				fo[k] = out[k] / 16777216.0f;
				fa[k] = aux[k] / 16777216.0f;
			}
			fwrite(fo, sizeof(fo), 1, stdout);
			fwrite(fa, sizeof(fa), 1, stdout);
		}
	}
	return 0;
}
