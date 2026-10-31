/*
 * Reference d'ACID pour l'ordinateur : le meme coeur (tools/machines/acid/acid_dsp.h), compile avec gcc, avec
 * l'arithmetique de l'EMAC reproduite a l'identique. tools/emu/test_acid.py compare sa sortie a celle de la
 * machine dans l'OS emule, echantillon par echantillon.
 *
 * Entree (stdin, texte) : une ligne par bloc de 32 echantillons et par voix,
 *     voix note tune cut res envmod decay drive wave trig slide_a dec_df acc accent reset
 * (les champs d'acid_in_t ; dec_df 1 : ACID_DEC_DF, 0 : ACID_DEC ; reset 1 : acid_reset avant le bloc).
 * Sortie (stdout) : 32 entiers int32 gros-boutistes par ligne. Avec ACID_REF_STATE dans l'environnement, la charge
 * de l'accent sweep (acid_t.as) apres chaque bloc, une par ligne, sur stderr.
 *
 *     gcc -O2 -I tools/machines/acid tools/emu/acid_ref.c -o acid_ref
 */
#include <stdio.h>
#include <stdlib.h>
#include "acid_dsp.h"

static acid_t voice[6];

int main(void)
{
	acid_in_t in;
	int t, reset, n, dec_df;
	s32 out[32];
	int state = getenv("ACID_REF_STATE") != 0;

	while (scanf("%d %d %d %d %d %d %d %d %d %d %d %d %d %d %d", &t, &in.note, &in.tune, &in.cut, &in.res,
		     &in.envmod, &in.decay, &in.drive, &in.wave, &in.trig, &in.slide_a, &dec_df, &in.acc, &in.accent,
		     &reset) == 15) {
		if (t < 0 || t > 5)
			return 1;
		in.dec = dec_df ? ACID_DEC_DF : ACID_DEC;
		if (reset)
			acid_reset(&voice[t]);
		acid_block(&voice[t], &in, out);
		if (state)
			fprintf(stderr, "%d\n", voice[t].as);
		for (n = 0; n < 32; n++) {
			unsigned char b[4] = { (unsigned char)(out[n] >> 24), (unsigned char)(out[n] >> 16),
					       (unsigned char)(out[n] >> 8), (unsigned char)out[n] };
			fwrite(b, 1, 4, stdout);
		}
	}
	return 0;
}
