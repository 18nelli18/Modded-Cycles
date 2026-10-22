// Reference de tools/emu/test_modal_dsp.py : la Part de Rings (pichenettes/eurorack, code MIT d'Emilie Gillet),
// en flottant, compilee pour l'ordinateur depuis une copie des sources ou ne changent que kMaxBlockSize (24 -> 32, le
// bloc du Cycles) et les reglages eco de MODAL (test_modal_dsp.ECO), pilotee bloc par bloc comme la machine MODAL
// pilote son coeur en virgule fixe (modal_dsp.h).
//
// Entree (binaire, petit-boutiste) : une suite d'enregistrements de 46 int32, un par bloc de 32 trames :
//   model poly strum internal_exciter chord note tonic fm (demi-tons << 16)
//   structure brightness damping position (0..65536 = 0..1) in[32] (1,0 = 2^24) rsv[2]
// Sortie : par bloc, out[32] puis aux[32] en float32.
#include <cstdio>
#include <cstdint>
#include <cstring>

#include "rings/dsp/part.h"

static rings::Part part;
static uint16_t reverb_buffer[32768];

int main()
{
	int32_t r[46];
	float in[32], out[32], aux[32];

	part.Init(reverb_buffer);
	while (fread(r, sizeof(r), 1, stdin) == 1) {
		rings::PerformanceState ps;
		rings::Patch patch;

		part.set_model(static_cast<rings::ResonatorModel>(r[0]));
		if (r[1] != part.polyphony())                 // set_polyphony reconfigure toujours (dirty_)
			part.set_polyphony(r[1]);
		ps.strum = r[2] != 0;
		ps.internal_exciter = r[3] != 0;
		ps.internal_strum = false;
		ps.internal_note = false;
		ps.chord = r[4];
		ps.note = r[5] / 65536.0f;
		ps.tonic = r[6] / 65536.0f;
		ps.fm = r[7] / 65536.0f;
		patch.structure = r[8] / 65536.0f;
		patch.brightness = r[9] / 65536.0f;
		patch.damping = r[10] / 65536.0f;
		patch.position = r[11] / 65536.0f;
		for (int i = 0; i < 32; i++)
			in[i] = r[12 + i] / 16777216.0f;
		part.Process(ps, patch, in, out, aux, 32);
		fwrite(out, sizeof(out), 1, stdout);
		fwrite(aux, sizeof(aux), 1, stdout);
	}
	return 0;
}
