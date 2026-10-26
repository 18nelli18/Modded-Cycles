/*
 * MACRO : machine ajoutee du Model:Cycles (OS 1.13) qui joue les 47 modeles de synthese de Braids, le
 * module d'Emilie Gillet (code MIT, depot pichenettes/eurorack, braids/ et stmlib/, notes/43). Ce fichier
 * est notre seul code : les sources de Braids sont compilees telles quelles par tools/gen_macro.py.
 *
 * Contrat de la boucle des voix (notes/14) : update(pmod, v, p) puis render(out, v), une fois par bloc de
 * 32 trames a 48 kHz. pmod = note du trig (demi-tons << 16) ; v = voix du Cycles (0x31c o) ; p = parametres
 * de la piste (mots 8.8 : +0x14 PITCH, +0x16 COLOR, +0x18 SHAPE, +0x1a SWEEP, +0x1c CONTOUR, +0x1e PUNCH,
 * +0x22 FINE, +0x24 DECAY) ; v+0x34 / v+0x38 : trig de ce bloc / du bloc precedent ; out : 32 x int32 (Q31).
 *
 * Braids est fait pour 96 kHz (ses tables de hauteur, de filtres et d'ondes) et rend par blocs de 24 echantillons,
 * 4 000 fois par seconde sur le module : ses decroissances (STRUCK BELL, STRUCK DRUM), la consonne de VOWEL et ses
 * lissages avancent d'un pas par bloc. Il rend donc ici exactement comme sur le module, des blocs de 24 : 3, 3 puis 2
 * par bloc de 32 trames du Cycles (8 x 24 = 3 x 64), ce qui depasse attend le bloc suivant (16 echantillons au plus,
 * 0,17 ms). Les 64 echantillons du bloc sont ramenes a 48 kHz par un filtre demi-bande de 23 coefficients
 * (passe-bande 0..19 kHz a 0,04 dB pres, -46 dB des 29 kHz, ce qui se replierait sous 19 kHz). Son propre code
 * donne donc exactement le son de Braids, a 96 kHz, avant ce filtre.
 *
 * Modeles alleges (notes/55) : 13 modeles (LITE) ne dependent du temps que par leur hauteur (oscillateurs, cartes
 * d'ondes) ; rendus a 48 kHz une octave plus haut (+1536 en 1/128 de demi-ton), par blocs de 12 (toujours 4 000 rendus
 * par seconde), ils donnent le meme spectre sans le filtre, pour environ moitie moins de calcul. Leurs oscillateurs
 * plafonnent, en rendu allege, une octave plus haut qu'a 96 kHz (g_pitch_offset, tools/gen_macro.py, notes/81) : le
 * meme plafond en Hz, toutes les notes restent a 48 kHz. RATE plus bas : la frequence la plus basse ou la note, plus
 * ce que le modele y ajoute (LITE : les accords de WAVE PARAPHONIC, les desaccords des TRIPLE), tient sous ce plafond.
 *
 * 48 kHz natifs (notes/81) : 9 modeles (NATIVE) calculent deja a 48 kHz dans Braids et ecrivent chaque echantillon
 * deux fois (interpole, ou tenu) pour faire 96 kHz. On les rend comme a 96 kHz (memes rendus de 24, meme cadence) mais
 * on garde les echantillons calcules (un sur deux) au lieu de passer par le filtre demi-bande : un petit filtre de
 * 3 coefficients, (1 14 1) / 16 apres interpolation, (1 30 1) / 32 apres un echantillon tenu, refait la legere
 * douceur des aigus que donnait l'aller-retour (a moins de 1 dB jusqu'a 18 kHz), pour 1 300 instructions de moins par
 * bloc.
 *
 * Lo-fi (FUNC + PITCH, notes/55) : sur une piste MACRO, FINE n'accorde plus ; au centre (64), rien ne change.
 * En dessous, RATE : d = 64 - FINE pas, frequence 48 kHz x 2^(-86 d / 1536) (de 46 kHz a 4 kHz). Un modele allege
 * est alors vraiment rendu a cette frequence (hauteur + 86 d), chaque echantillon tenu le temps qu'il faut (si sa note
 * est trop haute pour cela, a la plus basse qui tienne sous le plafond, puis echantillonne-bloque) ; les autres sont
 * echantillonnes-bloques comme sur le module (leur calcul ne change pas). Au-dessus, BITS : de 12 bits
 * (65) a 2 bits (127), arrondis au plus pres (sans decalage continu, que le VCA ferait claquer).
 *
 * Potards : PITCH = la note, comme les machines d'origine ; COLOR = TIMBRE de Braids ; SHAPE = le
 * modele (0..46, l'ordre de Braids : CSAW, MORPH, ...) ; SWEEP = COLOR de Braids ; CONTOUR = l'enveloppe
 * d'ampli ouvre TIMBRE (0 : rien) ; FINE = RATE / BITS. DECAY, GATE et PUNCH : la chaine d'ampli d'origine, reglee
 * comme TONE (enveloppe 0x400a9252, VCA 0x400a9430, PUNCH 0x400a967a). Un trig frappe le modele (Strike).
 *
 * Etat : une voix de Braids par piste, ici (BSS de la charge utile, mis a zero au demarrage), initialisee a
 * la premiere note apres un changement de machine (marque en v+0x2c, effacee par la remise a zero de la voix,
 * 0x400a7ab8). Une voix muette (enveloppe d'ampli fermee, pas de trig) n'est pas calculee.
 */
#include <new>

#include "braids/macro_oscillator.h"

typedef signed char s8;
typedef short s16;
typedef int s32;
typedef unsigned int u32;

#define CYC_VOICE0  0x42308828
#define CYC_VSTRIDE 0x31c
#define MARK_OFF    0x2c
#define MARK        0x4d435231                       /* 'MCR1' */

#define AMP_ENV(v)  ((void (*)(char *))0x400a9252)(v)
#define VCA(o, v)   ((void (*)(s32 *, char *))0x400a9430)(o, v)
#define PUNCH(o, v) ((void (*)(s32 *, char *))0x400a967a)(o, v)
#define LUT_DECAY   ((const s32 *)0x4011d84c)        /* DECAY -> multiplicateur par bloc (celui de TONE) */

#define V32(o)      (*(s32 *)(v + (o)))
#define P16(o)      (*(const s16 *)(p + (o)))

#define MODELS      47                               /* CSAW .. DIGITAL_MODULATION (sans QUESTION_MARK) */
#define HIST        22                               /* echantillons du bloc precedent pour le filtre */
#define IDLE_LEVEL  (1 << 14)                        /* enveloppe d'ampli sous -102 dB : voix muette */
#define ONE         (1 << 24)                        /* RATE : un echantillon (Q24) */
#define OCTAVE      (12 << 7)                        /* hauteur de Braids : 1/128 de demi-ton */
#define TOP_NOTE    16383                            /* plafond des oscillateurs de Braids */
#define RATE_SHIFT  86                               /* un pas de RATE, en 1/128 de demi-ton */

struct Track {
	braids::MacroOscillator osc;
	alignas(4) s16 x[HIST + 64 + 16];                /* 96 kHz : fin du bloc precedent, ce bloc, puis l'avance ;
	                                                    48 kHz : le dernier rendu (x[rd..fill)) */
	s32 fill;                                        /* 96 kHz : echantillons rendus apres l'historique */
	s32 rd;                                          /* 48 kHz : prochain echantillon a sortir */
	s32 mode;                                        /* rendu en cours : 0 96 kHz, 1 48 kHz (ou moins), 2 48 kHz
	                                                    natifs, 3 48 kHz natifs par bloc entier, -1 aucun */
	s32 r1, r2;                                      /* 48 kHz natifs : les deux derniers echantillons (filtre) */
	s32 nat;                                         /* ... et NATIVE du modele de ce bloc */
	s32 off;                                         /* braids::g_pitch_offset de ce bloc */
	s32 want;                                        /* rendu demande par macro_update */
	u32 src;                                         /* 48 kHz : un echantillon rendu par sortie (Q24, ONE : tous) */
	u32 hold;                                        /* echantillonneur-bloqueur apres le rendu (Q24, ONE : rien) */
	s32 size;                                        /* 48 kHz : echantillons par rendu */
	s32 bits;                                        /* BITS (0 : 16 bits, rien) */
	u32 ph;                                          /* 48 kHz ou moins : phase du rendu (Q24) */
	u32 hph;                                         /* echantillonneur-bloqueur : sa phase (Q24) */
	s32 cur;                                         /* RATE : echantillon tenu */
};

/* de combien la hauteur donnee a Braids depasse la vraie note (rendu allege : une octave et le pas de RATE ; 0 a
 * 96 kHz), lu par les lignes de Braids qui s'en servent pour autre chose que l'accord (tools/gen_macro.py,
 * SEMANTIC_EDITS, notes/81) ; mis avant chaque rendu */
namespace braids {
int32_t g_pitch_offset;
int32_t g_native48;                                  /* rendu en 48 kHz natifs (modes 2, 3) : braids_semantic.inc */
}

/* pas de constructeurs globaux (rien ne les appellerait) : placement new a l'initialisation de la piste */
alignas(4) static unsigned char store[6][sizeof(Track)];
static const unsigned char no_sync[24] = { 0 };

/* filtre demi-bande, 23 coefficients (Q15, minimax, somme 1/2 : gain 1 en continu) : 1/2 au centre, puis +-1, +-3,
 * ... +-11 */
/* HB = { 10327, -3131, 1579, -820, 434, -197 } : les coefficients sont dans macro_halfband (macro_asm.S) */
extern "C" void macro_halfband(s32 *out, const s16 *x);

/* modeles alleges, rendus a 48 kHz (notes/55) : ce que le modele ajoute au-dessus de sa note (1/128 de demi-ton :
 * desaccord des TRIPLE jusqu'a 24 demi-tons, accords de WAVE PARAPHONIC jusqu'a 19 demi-tons + 5) ; -1 : 96 kHz */
static const s16 LITE[MODELS] = {
	0, -1, 0, 0, -1, 0, 0, -1, -1,                   /* CSAW, SAW_SQUARE, SINE_TRIANGLE (notes/81), SQUARE_SUB,
	                                                    SAW_SUB */
	3072, 3072, 3072, 3072,                          /* TRIPLE_SAW, _SQUARE, _TRIANGLE, _SINE */
	-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
	0, 0, 0, 2437,                                   /* WAVETABLES, WAVE_MAP, WAVE_LINE, WAVE_PARAPHONIC */
	-1, -1, -1, -1, -1,
	0,                                               /* DIGITAL_MODULATION */
};

/* 48 kHz natifs (notes/81) : 1 echantillon interpole entre deux calcules, 2 echantillon tenu, 3 comme 1 mais un rendu
 * par bloc (HARMONICS, braids_semantic.inc : son cout est surtout par rendu) ; 0 : non */
static const s8 NATIVE[MODELS] = {
	0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
	1,                                               /* VOWEL_FOF */
	3, 0, 0, 0,                                      /* HARMONICS */
	1, 1, 0, 0,                                      /* PLUCKED, BOWED */
	1, 1, 0, 0, 2,                                   /* STRUCK_BELL, STRUCK_DRUM ; SNARE */
	0, 0, 0, 0, 0,
	2, 0, 0, 2,                                      /* TWIN_PEAKS_NOISE ; PARTICLE_NOISE */
	0,
};

/* RATE : 2^(-86 d / 1536) en Q24, d = 0..64 pas sous FINE 64 (48 kHz .. 4 kHz) */
static const u32 RATE_STEP[65] = {
	16777216, 16138581, 15524256, 14933316, 14364871, 13818063, 13292070, 12786100,
	12299389, 11831206, 11380844, 10947625, 10530897, 10130032, 9744426, 9373499,
	9016691, 8673465, 8343305, 8025712, 7720208, 7426334, 7143646, 6871719,
	6610143, 6358524, 6116483, 5883655, 5659690, 5444251, 5237012, 5037662,
	4845900, 4661438, 4483998, 4313312, 4149123, 3991184, 3839257, 3693114,
	3552533, 3417304, 3287222, 3162092, 3041725, 2925940, 2814562, 2707424,
	2604365, 2505228, 2409865, 2318132, 2229891, 2145009, 2063358, 1984815,
	1909262, 1836584, 1766674, 1699424, 1634735, 1572507, 1512649, 1455069,
	1399681,
};

static inline Track *track_of(const char *v)
{
	return reinterpret_cast<Track *>(store[((u32)v - CYC_VOICE0) / CYC_VSTRIDE]);
}

static inline s32 knob(s32 x)                        /* 8.8, 0..127 -> 0..32766 */
{
	x = x < 0 ? 0 : (x > 0x7f00 ? 0x7f00 : x);
	return x + (x >> 7);
}

static inline u32 mag(s32 x)
{
	return x < 0 ? 0u - (u32)x : (u32)x;
}

extern "C" void macro_update(s32 pmod, char *v, const char *p)
{
	Track *tr = track_of(v);
	s32 dec, n, shape, timbre, env, fine, rate, head, d;

	if (V32(MARK_OFF) != MARK) {                     /* 1re note sur cette machine */
		new (tr) Track;
		tr->osc.Init();
		for (n = 0; n < HIST; n++)
			tr->x[n] = 0;
		tr->fill = tr->rd = 0;
		tr->mode = -1;
		tr->ph = tr->hph = ONE - 1;              /* le 1er echantillon sort tout de suite */
		tr->cur = 0;
		V32(MARK_OFF) = MARK;
	}
	/* chaine d'ampli d'origine, reglee comme TONE (0x400aa7b8) */
	dec = (s8)p[0x24];
	dec = dec < 0 ? 0 : (dec > 127 ? 127 : dec);
	V32(0x250) = LUT_DECAY[dec];
	if (V32(0x38)) {
		V32(0x274) = V32(0x278) = 0x012c0f26;
		V32(0x280) = V32(0x284) = 0x001f7c5c;
		V32(0x290) = V32(0x294) = 0x7fffffff;
		V32(0x27c) = 0x82581e4b;
		V32(0x288) = 0x803ef8b8;
		if (P16(0x1e)) {
			V32(0x29c) = 0x20000000; V32(0x2a0) = 0x60000000; V32(0x2a4) = 0x20000000;
			V32(0x48) = 1;
		} else {
			V32(0x29c) = 0x7fffffff; V32(0x2a0) = 0x20000000; V32(0x2a4) = 0x20000000;
			V32(0x48) = 0;
		}
	}

	shape = P16(0x18) >> 8;
	shape = shape < 0 ? 0 : (shape >= MODELS ? MODELS - 1 : shape);
	tr->osc.set_shape(static_cast<braids::MacroOscillatorShape>(shape));

	/* FINE (FUNC + PITCH) : RATE en dessous de 64, BITS au-dessus */
	fine = (P16(0x22) + 0x80) >> 8;
	fine = fine < 0 ? 0 : (fine > 127 ? 127 : fine);
	rate = fine < 64 ? 64 - fine : 0;
	tr->bits = fine > 64 ? 12 - (fine - 65) * 10 / 62 : 0;

	/* note : PITCH - 64 + note du trig, comme les machines d'origine ; Braids : 1/128 de demi-ton */
	n = ((s32)P16(0x14) << 8) - (64 << 16) + pmod;
	n = n < 0 ? 0 : (n > (127 << 16) ? 127 << 16 : n);
	n >>= 9;
	/* rendu : modele allege a la frequence de RATE, ou a la plus basse sous le plafond (puis bloque a celle de RATE) ;
	 * sinon 96 kHz (puis bloque) */
	head = LITE[shape];
	d = -1;
	if (head >= 0) {                                 /* plafond releve d'une octave en rendu allege (notes/81) */
		d = TOP_NOTE - head - n;
		d = d < 0 ? 0 : (d / RATE_SHIFT > rate ? rate : d / RATE_SHIFT);
	}
	if (d >= 0) {
		tr->want = 1;
		tr->src = RATE_STEP[d];
		tr->size = 2 * ((6 * (s32)(RATE_STEP[d] >> 8) + (1 << 15)) >> 16);   /* 4 000 rendus par seconde, pair */
		tr->size = tr->size < 2 ? 2 : tr->size;
		tr->osc.set_pitch(n + OCTAVE + RATE_SHIFT * d);
		tr->off = OCTAVE + RATE_SHIFT * d;
	} else {
		tr->want = NATIVE[shape] == 3 ? 3 : (NATIVE[shape] ? 2 : 0);
		tr->nat = NATIVE[shape];
		tr->off = 0;
		d = 0;
		tr->osc.set_pitch(n);
	}
	tr->hold = d == rate ? ONE : RATE_STEP[rate];

	/* TIMBRE = COLOR + CONTOUR x enveloppe d'ampli (son niveau au bloc precedent, plein au trig) */
	env = V32(0x38) ? 32767 : (s32)(mag(V32(0x230)) >> 16);
	env = env > 32767 ? 32767 : env;
	timbre = knob(P16(0x16)) + ((env * knob(P16(0x1c))) >> 15);
	timbre = timbre > 32767 ? 32767 : timbre;
	tr->osc.set_parameters(timbre, knob(P16(0x1a)));

	if (V32(0x38))
		tr->osc.Strike();
}

extern "C" void macro_render(s32 *out, char *v)
{
	Track *tr = track_of(v);
	u32 ph, f;
	s32 cur, m, h;
	int i;

	if (!V32(0x34) && !V32(0x38) && mag(V32(0x230)) < IDLE_LEVEL && mag(V32(0x234)) < IDLE_LEVEL) {
		for (i = 0; i < 32; i++)                     /* voix muette : pas calculee */
			out[i] = 0;
		return;
	}
	if (tr->want != tr->mode) {                      /* changement de rendu : on repart de zero */
		for (i = 0; i < HIST; i++)
			tr->x[i] = 0;
		tr->fill = tr->rd = 0;
		tr->r1 = tr->r2 = 0;
		tr->mode = tr->want;
	}
	ph = tr->ph;
	cur = tr->cur;
	braids::g_pitch_offset = tr->off;
	braids::g_native48 = tr->mode >= 2;
	if (tr->mode == 3) {                             /* 48 kHz natifs, un rendu de 64 par bloc : un echantillon */
		s32 r, r1 = tr->r1, r2 = tr->r2;             /* sur deux, puis (1 14 1) / 16 */
		const s16 *x = tr->x + 33;
		tr->osc.Render(no_sync, tr->x + 32, 64);
		for (i = 0; i < 32; i++) {
			r = x[2 * i];
			out[i] = (r2 + 14 * r1 + r) << 11;
			r2 = r1;
			r1 = r;
		}
		tr->r1 = r1;
		tr->r2 = r2;
	} else if (tr->mode == 2) {                      /* 48 kHz natifs : rendus de 24, un echantillon sur deux */
		s32 r, r1 = tr->r1, r2 = tr->r2, n, j;
		const s16 *x;
		for (i = 0; i < 32; i += n) {
			if (tr->rd == tr->fill) {
				tr->osc.Render(no_sync, tr->x + 32, 24);
				for (r = 0; r < 12; r++)
					tr->x[r] = tr->x[33 + 2 * r];
				tr->rd = 0;
				tr->fill = 12;
			}
			n = tr->fill - tr->rd;
			n = n > 32 - i ? 32 - i : n;
			x = tr->x + tr->rd;
			tr->rd += n;
			if (tr->nat == 1) {              /* (1 14 1) / 16, a l'echelle 1/2 (Q31) */
				for (j = 0; j < n; j++) {
					r = x[j];
					out[i + j] = (r2 + 14 * r1 + r) << 11;
					r2 = r1;
					r1 = r;
				}
			} else {                         /* (1 30 1) / 32 */
				for (j = 0; j < n; j++) {
					r = x[j];
					out[i + j] = (r2 + 30 * r1 + r) << 10;
					r2 = r1;
					r1 = r;
				}
			}
		}
		tr->r1 = r1;
		tr->r2 = r2;
	} else if (tr->mode) {                           /* 48 kHz ou moins : un rendu quand le precedent est sorti */
		f = tr->src;
		for (i = 0; i < 32; i++) {
			if (f != ONE) {
				ph += f;
				if (ph < ONE) {
					out[i] = cur;
					continue;
				}
				ph -= ONE;
			}
			if (tr->rd == tr->fill) {
				tr->osc.Render(no_sync, tr->x, tr->size);
				tr->rd = 0;
				tr->fill = tr->size;
			}
			out[i] = cur = (s32)tr->x[tr->rd++] << 15;   /* pleine echelle de Braids -> 1/2 (Q31) */
		}
	} else {
		while (tr->fill < 64) {                      /* des blocs de 24, comme sur le module */
			tr->osc.Render(no_sync, tr->x + HIST + tr->fill, 24);
			tr->fill += 24;
		}
		/* 96 -> 48 kHz : sortie m centree sur l'echantillon 2m + 11 de x (retard de 5,5 echantillons a 48 kHz) ;
		 * pleine echelle de Braids -> 1/2 pleine echelle (Q31). Sur l'EMAC (macro_asm.S, notes/81) :
		 *   out[m] = x[2m + 11] << 14 + sum_j HB[j] (x[2m + 10 - 2j] + x[2m + 12 + 2j]) */
		macro_halfband(out, tr->x);
		tr->fill -= 64;                          /* l'historique et l'avance glissent au debut */
		for (i = 0; i < HIST + tr->fill; i++)
			tr->x[i] = tr->x[64 + i];
	}
	tr->ph = ph;
	if (tr->hold != ONE) {                           /* RATE plus bas que le rendu : echantillonne-bloque */
		f = tr->hold;
		ph = tr->hph;
		for (i = 0; i < 32; i++) {
			ph += f;
			if (ph >= ONE) {
				ph -= ONE;
				cur = out[i];
			}
			out[i] = cur;
		}
		tr->hph = ph;
	}
	tr->cur = cur;
	if (tr->bits) {                                  /* BITS : les bits de poids fort de Braids, au plus pres */
		m = -(1 << (31 - tr->bits));
		h = 1 << (30 - tr->bits);
		for (i = 0; i < 32; i++)
			out[i] = (out[i] + h) & m;
	}
	AMP_ENV(v);
	VCA(out, v);
	PUNCH(out, v);
}
