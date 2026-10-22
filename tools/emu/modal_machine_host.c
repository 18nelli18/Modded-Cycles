/*
 * La machine MODAL entiere (tools/machines/modal/modal.c : passerelle et coeur) compilee pour l'ordinateur. La
 * preuve (tools/emu/test_modal.py) lui rejoue ce que la passerelle recoit dans l'emulation de l'OS, bloc par bloc,
 * et compare les sorties octet pour octet.
 *
 * Entree (binaire, petit-boutiste), un enregistrement par appel d'update puis de render :
 *   piste, pmod, v+0x2c, v+0x34, v+0x38, gain (0x40fe4c90), gain suivant (0x40fe4cd0) : 7 int32 ;
 *   les parametres de la piste p+0x00..0x3f : 64 octets.
 * Sortie, par enregistrement : out[32] (int32), puis les deux gains et v+0x2c apres update (3 int32).
 */
#include <stdio.h>
#include <string.h>

static short host_gain[6], host_gain_next[6];
static char host_voices[6 * 0x31c] __attribute__((aligned(4)));
static char host_ram[6 * 0x28000] __attribute__((aligned(16)));

#define CYC_VOICE0  ((unsigned long)host_voices)
#define VGAIN       host_gain
#define VGAIN_NEXT  host_gain_next
#define MODAL_RAM   ((unsigned long)host_ram)

#include "modal.c"

int main(void)
{
	int r[7];
	unsigned char p[64];
	s32 out[MB], back[3];

	while (fread(r, sizeof(r), 1, stdin) == 1 && fread(p, sizeof(p), 1, stdin) == 1) {
		char *v = host_voices + r[0] * 0x31c;
		const char *pp = (const char *)p;
		char pb[64];
		int k;

		/* les parametres sont des mots gros-boutistes (ColdFire) : les remettre dans l'ordre de l'ordinateur */
		for (k = 0; k < 64; k += 2) {
			pb[k] = (char)p[k + 1];
			pb[k + 1] = (char)p[k];
		}
		pp = pb;
		memcpy(v + 0x2c, &r[2], 4);
		memcpy(v + 0x34, &r[3], 4);
		memcpy(v + 0x38, &r[4], 4);
		host_gain[r[0]] = (short)r[5];
		host_gain_next[r[0]] = (short)r[6];
		modal_update(r[1], v, pp);
		modal_render(out, v);
		back[0] = host_gain[r[0]];
		back[1] = host_gain_next[r[0]];
		memcpy(&back[2], v + 0x2c, 4);
		fwrite(out, sizeof(out), 1, stdout);
		fwrite(back, sizeof(back), 1, stdout);
	}
	return 0;
}
