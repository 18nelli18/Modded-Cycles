/*
 * La machine MODAL entiere (tools/machines/modal/modal.c : passerelle et coeur) compilee pour l'ordinateur. La
 * preuve (tools/emu/test_modal.py) lui rejoue ce que la passerelle recoit dans l'emulation de l'OS, bloc par bloc,
 * et compare les sorties octet pour octet.
 *
 * Entree (binaire, petit-boutiste) :
 *   en tete, les cases de samples de Model-TG que la preuve a posees (le sample excitateur, notes/80) : un int32
 *   (nombre de cases), puis pour chacune case, empreinte, nombre d'echantillons (3 int32) et les echantillons
 *   (int16 gros-boutistes, comme en memoire, completes a un multiple de 4 octets) ;
 *   puis un enregistrement par appel d'update puis de render :
 *   piste, pmod, v+0x2c, v+0x34, v+0x38, gain (0x40fe4c90), gain suivant (0x40fe4cd0), track_slot et track_pend de
 *   la piste (Model-TG) : 9 int32 ; les parametres de la piste p+0x00..0x3f : 64 octets.
 * Sortie, par enregistrement : out[32] (int32), puis les deux gains, v+0x2c, track_slot et track_pend apres render
 * (5 int32).
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static short host_gain[6], host_gain_next[6];
static char host_voices[6 * 0x31c] __attribute__((aligned(4)));
static char host_ram[6 * 0x28000] __attribute__((aligned(16)));
static int host_tslot[6], host_tpend[6];
static unsigned int host_shash[64];
static int host_scount[64];
static short *host_spcm[64];

#define CYC_VOICE0  ((unsigned long)host_voices)
#define VGAIN       host_gain
#define VGAIN_NEXT  host_gain_next
#define MODAL_RAM   ((unsigned long)host_ram)
#define T_SLOT      host_tslot
#define T_PEND      host_tpend
#define S_HASH      host_shash
#define S_COUNT     host_scount
#define SLOT_PCM(s) ((const s16 *)host_spcm[s])

#include "modal.c"

static int read_slots(void)
{
	int n, h[3], k;

	if (fread(&n, sizeof(n), 1, stdin) != 1)
		return 0;
	while (n-- > 0) {
		unsigned char *be;
		int bytes;

		if (fread(h, sizeof(h), 1, stdin) != 1 || h[0] < 0 || h[0] >= 64 || h[2] < 0)
			return 0;
		bytes = (2 * h[2] + 3) & ~3;
		be = malloc(bytes ? bytes : 4);
		host_spcm[h[0]] = malloc(2 * (h[2] ? h[2] : 1));
		if (!be || !host_spcm[h[0]] || (bytes && fread(be, bytes, 1, stdin) != 1))
			return 0;
		for (k = 0; k < h[2]; k++)
			host_spcm[h[0]][k] = (short)(be[2 * k] << 8 | be[2 * k + 1]);
		free(be);
		host_shash[h[0]] = (unsigned int)h[1];
		host_scount[h[0]] = h[2];
	}
	return 1;
}

int main(void)
{
	int r[9];
	unsigned char p[64];
	s32 out[2 * MB], back[5];                        /* 32 trames a 48 kHz (notes/81) */

	if (!read_slots())
		return 1;
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
		host_tslot[r[0]] = r[7];
		host_tpend[r[0]] = r[8];
		modal_update(r[1], v, pp);
		modal_render(out, v);
		back[0] = host_gain[r[0]];
		back[1] = host_gain_next[r[0]];
		memcpy(&back[2], v + 0x2c, 4);
		back[3] = host_tslot[r[0]];
		back[4] = host_tpend[r[0]];
		fwrite(out, sizeof(out), 1, stdout);
		fwrite(back, sizeof(back), 1, stdout);
	}
	return 0;
}
