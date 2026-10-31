/*
 * Origin: AveyCole fork (https://github.com/AveyCole/Modded-Cycles), MIT License.
 * RETROSYN : le coeur du son (voix Game Boy / SNES), en entiers 32 bits, sans FPU, sans division dans la boucle.
 *
 * Formes (SHAPE) : 0 PULSE (rapport continu de 12,5 à 75 %, modulable par un LFO), 1 TRI (32 pas de 4 bits, comme la
 * NES), 2 WAVE (table de 32 pas de 4 bits, canal « wave » du Game Boy, 8 tables), 3 NOISE-L (LFSR 15 bits), 4 NOISE-S
 * (LFSR 7 bits, son métallique), 5 SNES (boucle de 16 échantillons de 4 bits lue avec une interpolation gaussienne à
 * 4 points, 8 boucles).
 * COLOR : rapport / table / boucle / cadence du bruit (continue sur 3 octaves). Rapport et cadence suivent une droite
 * entre les centres des quatre anciens paliers (COLOR 4096 / 12288 / 20480 / 28672 : 12,5 / 25 / 50 / 75 %, horloge
 * du bruit = hauteur x 2^4..2^7) : à ces valeurs le son est identique, bit pour bit, à l'ancien. SWEEP : balayage de
 * hauteur à chaque note (centre = rien, droite = monte, gauche = descend ; cadence 128 Hz, comme le Game Boy ; une
 * note qui dépasse le haut se tait).
 * CONTOUR : arpège (accords), un pas tous les 1/60 s comme les macros d'arpège de la NES. PUNCH : sortie écrasée à 4 bits.
 *
 * L'enveloppe d'amplitude, DECAY et GATE sont ceux de l'OS (comme MACRO) : ce coeur ne fait que l'oscillateur. Le
 * niveau de sortie (RS_LEVEL_SH) reste à caler contre MACRO / TONE dans l'émulation.
 *
 * Ce fichier sert deux fois, comme acid_dsp.h : compilé pour le Cycles (-mcpu=54418) et pour l'ordinateur
 * (retrosyn_ref.c), même code C, aucune instruction propre à un processeur : la preuve compare les deux.
 *
 * Formats : hauteurs en demi-tons << 16 ; potards 0..32767 ; sortie Q31 (voir RS_LEVEL_SH).
 */
#ifndef RETROSYN_DSP_H
#define RETROSYN_DSP_H

typedef signed char s8;
typedef short s16;
typedef int s32;
typedef unsigned int u32;

#include "retrosyn_tables.h"

#define RS_BLOCK 32
#define RS_LEVEL_SH 22            /* un pas de 1/16 de la forme (-128..127) -> +-2^29 : 1/4 de la pleine echelle */
#define RS_ARP_PERIOD 800         /* 48000 / 60 */
#define RS_SWEEP_PERIOD 375       /* 48000 / 128 */
#define RS_TOP_PITCH (120 << 16)  /* balayage vers le haut : au-dela, la note se tait */

enum { RS_PULSE, RS_TRI, RS_WAVE, RS_NOISEL, RS_NOISES, RS_SNES };

typedef struct {
	u32 ph;            /* phase de l'oscillateur */
	u32 nph;           /* phase de l'horloge du bruit */
	u32 lfsr;          /* registre du bruit */
	s32 sweep;         /* decalage de hauteur du balayage, demi-tons << 16 */
	s32 arp_acc;       /* echantillons depuis le dernier pas d'arpege */
	s32 sweep_acc;     /* echantillons depuis le dernier tick de balayage */
	s32 arp_i;         /* pas d'arpege courant */
	s32 silent;        /* 1 : le balayage a depasse le haut */
} retrosyn_t;

typedef struct {
	s32 note;          /* hauteur, demi-tons << 16 (note du trig + PITCH + FINE), 0..127 << 16 */
	s32 trig;          /* 1 : nouvelle note (remet la phase, le balayage, l'arpege) */
	s32 shape, color, sweep, contour;  /* potards 0..32767 */
	s32 punch;         /* 0 : normal, 1 : 4 bits */
} retrosyn_in_t;

static const s8 RS_CHORD[8][4] = {{0, 0, 0, 0}, {0, 12, 0, 0}, {0, 4, 7, 0}, {0, 3, 7, 0},
				  {0, 7, 12, 0}, {0, 4, 7, 12}, {0, 3, 7, 12}, {0, 12, 24, 0}};
static const s8 RS_CHORD_N[8] = {1, 2, 3, 3, 3, 4, 4, 3};

static inline void retrosyn_reset(retrosyn_t *s)
{
	s->ph = s->nph = 0;
	s->lfsr = 0x7fff;
	s->sweep = s->arp_acc = s->sweep_acc = s->arp_i = s->silent = 0;
}

static inline u32 rs_lfsr(u32 l, s32 bits)               /* un pas du registre du bruit : 15 bits (x^15 + x^14 + 1) ou 7 bits */
{
	u32 fb = (l ^ (l >> 1)) & 1;
	return (l >> 1) | (fb << (bits - 1));
}

static inline u32 rs_duty(s32 c)                         /* COLOR -> seuil de phase du PULSE (2^29 = 12,5 %) */
{
	c = c < 4096 ? 4096 : (c > 28672 ? 28672 : c);
	return c < 12288 ? (1u << 29) + ((u32)(c - 4096) << 16) : (1u << 30) + ((u32)(c - 12288) << 17);
}

static inline u32 rs_inc(s32 pitch)                       /* demi-tons << 16 -> increment de phase */
{
	s32 i = pitch >> 16;
	u32 a = RS_INC[i], b = RS_INC[i + 1];
	u32 f = (u32)(pitch & 0xffff);
	/* (b - a) x f / 2^16 en 32 bits : (b - a) < 2^27, donc (b - a) >> 10 x f >> 6 < 2^17 x 2^10 */
	return a + (((b - a) >> 10) * (f >> 6));
}

/* un bloc de 32 echantillons dans out (Q31, avant la chaine d'ampli de l'OS) */
static inline void retrosyn_block(retrosyn_t *s, const retrosyn_in_t *in, s32 *out)
{
	s32 shape = (in->shape * 6) >> 15, ci = in->contour >> 12, n, sh, up;
	s32 d = in->sweep - 16384;
	s32 color = in->color;
	u32 ph, nph, lfsr, inc = 0, thr = rs_duty(color), nfi = 0;
	s32 nk, nm, nclk = 0;

	if (shape > 5) shape = 5;
	if (ci > 7) ci = 7;
	if (s->arp_i >= RS_CHORD_N[ci]) s->arp_i = 0;        /* CONTOUR tourne : le pas courant peut ne plus exister */
	if (in->trig) {
		s->ph = s->nph = 0;
		s->lfsr = shape == RS_NOISES ? 0x7f : 0x7fff;
		s->sweep = s->arp_acc = s->sweep_acc = s->arp_i = s->silent = 0;
	}
	/* balayage : decalage constant par tick, en demi-tons (f x (1 +- 2^-sh) par tick) */
	up = d > 0;
	d = (d < 0 ? -d : d) - 1024;
	sh = d <= 0 ? 0 : 7 - (d * 6) / 15360;
	if (sh < 2 && d > 0) sh = 2;
	/* bruit : horloge = hauteur x 2^nk x nm / 2^15, nk 4..7, nm = 2^f (f = fraction d'octave, parabole, ecart < 0,4 %) */
	nk = color < 4096 ? 0 : (color > 28672 ? 24576 : color - 4096);
	nm = (nk & 8191) << 2;
	nm = 32768 + ((nm * (21512 + ((nm * 11256) >> 15))) >> 15);
	nk = 4 + (nk >> 13);

	ph = s->ph; nph = s->nph; lfsr = s->lfsr;
	for (n = 0; n < RS_BLOCK; n++) {
		s32 w = 0;
		/* ticks : arpege 60 Hz, balayage 128 Hz (au plus un de chaque par echantillon) */
		if (++s->arp_acc >= RS_ARP_PERIOD) {
			s->arp_acc -= RS_ARP_PERIOD;
			if (RS_CHORD_N[ci] > 1 && ++s->arp_i >= RS_CHORD_N[ci])
				s->arp_i = 0;
			inc = 0;
		}
		if (++s->sweep_acc >= RS_SWEEP_PERIOD) {
			s->sweep_acc -= RS_SWEEP_PERIOD;
			if (sh) {
				s->sweep += up ? RS_SWEEP_UP[sh] : RS_SWEEP_DN[sh];
				if (s->sweep < -(120 << 16)) s->sweep = -(120 << 16);
				if (in->note + (RS_CHORD[ci][s->arp_i] << 16) + s->sweep > RS_TOP_PITCH) s->silent = 1;
			}
			inc = 0;
		}
		if (!inc || n == 0) {
			s32 p = in->note + (RS_CHORD[ci][s->arp_i] << 16) + s->sweep;
			inc = rs_inc(p < 0 ? 0 : (p > (127 << 16) ? 127 << 16 : p));
			if (shape == RS_NOISEL || shape == RS_NOISES) {
				/* inc < 2^30,1 : (inc >> 15) x nm < 2^32 ; nm = 32768 rend inc tel quel */
				u32 b = (inc >> 15) * (u32)nm + (((inc & 0x7fff) * (u32)nm) >> 15);
				nclk = (s32)(b >> (32 - nk));
				nfi = b << nk;
			}
		}
		ph += inc;
		switch (shape) {
		case RS_PULSE:
			w = (ph < thr ? 7 : -8) * 16;
			break;
		case RS_TRI: {
			s32 k = ph >> 27;
			w = ((k < 16 ? k : 31 - k) - 8) * 16;
		} break;
		case RS_WAVE:
			w = RS_WT[(color * 8) >> 15][ph >> 27] * 16;
			break;
		case RS_NOISEL:
		case RS_NOISES: {
			s32 bits = shape == RS_NOISES ? 7 : 15;
			s32 clocks = nclk, c;
			nph += nfi;
			if (nph < nfi) clocks++;
			if (clocks > 8) clocks = 8;
			for (c = 0; c < clocks; c++)
				lfsr = rs_lfsr(lfsr, bits);
			w = ((lfsr & 1) ? -8 : 7) * 16;
		} break;
		case RS_SNES: {
			const s8 *lp = RS_LOOPS[(color * 8) >> 15];
			s32 ix = ph >> 28, fr = (ph >> 20) & 255;
			const s16 *g = RS_GAUSS[fr];
			w = (g[0] * lp[(ix - 1) & 15] + g[1] * lp[ix] + g[2] * lp[(ix + 1) & 15] + g[3] * lp[(ix + 2) & 15]) >> 11;
		} break;
		}
		if (s->silent) w = 0;
		if (in->punch) w = ((w + 8) >> 4) * 16;              /* 4 bits : multiplication, pas de decalage a gauche d'un negatif */
		out[n] = w * (1 << RS_LEVEL_SH);
	}
	s->ph = ph; s->nph = nph; s->lfsr = lfsr;
}

#endif
