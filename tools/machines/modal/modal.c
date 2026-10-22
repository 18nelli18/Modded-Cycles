/*
 * MODAL : machine ajoutee du Model:Cycles (OS 1.13), un resonateur d'apres Rings d'Emilie Gillet (notes/74).
 * Le son est dans modal_dsp.h (la Part de Rings en virgule fixe, licence MIT : LICENSE-Rings) ; ce fichier le
 * branche sur la boucle des voix.
 *
 * Contrat de la boucle des voix (notes/14) : update(pmod, v, p) puis render(out, v), une fois par bloc de
 * 32 trames a 48 kHz. pmod = note du trig (demi-tons << 16) ; v = voix du Cycles (0x31c o) ; p = parametres
 * de la piste (mots 8.8 : +0x12 MACHINE, +0x14 PITCH, +0x16 COLOR, +0x18 SHAPE, +0x1a SWEEP, +0x1c CONTOUR,
 * +0x1e PUNCH, +0x20 GATE, +0x22 FINE, +0x24 DECAY) ; v+0x34 / v+0x38 : trig de ce bloc / du bloc precedent ;
 * out : 32 x int32 (Q31).
 *
 * Potards (choix de Maxime, 20/10/2026) : PITCH = FREQUENCY de Rings (avec la note du trig : la V/OCT) ;
 * DECAY = DAMPING ; COLOR = BRIGHTNESS ; SHAPE = MODEL (descripteur 0..3 : modal, cordes sympathiques, corde,
 * cordes en accord ; ni la voix FM ni la corde et reverbe de Rings, choix de Maxime) ; SWEEP = POSITION ; CONTOUR =
 * STRUCTURE (et l'accord des cordes quantifiees, avec l'hysteresis de Rings, rings/cv_scaler.cc) ; FUNC + SHAPE =
 * polyphonie 1, 2 ou 4, rangee dans FINE (aucun potard ne regle FINE sur le Cycles ; les detours de l'interface
 * la mettent sous FUNC + SHAPE). Pas d'enveloppe d'ampli : la resonance s'eteint d'elle-meme (DAMPING), comme sur
 * le module ; PUNCH et GATE ne servent pas.
 *
 * Velocite : elle regle la force de la frappe (l'excitateur), pas le volume de la piste ; sinon, en polyphonie,
 * la queue des notes precedentes sauterait de niveau a chaque trig. Au bloc du trig (v+0x34), l'OS vient d'ecrire
 * le gain de la nouvelle velocite en 0x40fe4cd0 (recopie en 0x40fe4c90 apres la boucle des voix, notes/54 §2) :
 * la passerelle le garde, et la frappe le recoit au bloc suivant (v+0x38, quand Rings joue la note, comme ACID).
 * Les deux gains restent a 127 : la sortie de la piste n'est plus multipliee.
 *
 * Etat : une Part de Rings par piste, en SDRAM au-dessus de la zone d'echantillons de Model-TG (MODAL_RAM : rien
 * de l'OS ni de Model-TG n'y va, notes/74), remise a neuf a la premiere note apres un changement de machine
 * (marque en v+0x2c, effacee par la remise a zero de la voix, 0x400a7ab8).
 */
#include "modal_dsp.h"

/* Adresses de l'OS ; tools/emu/modal_machine_host.c les redefinit pour compiler ce fichier sur l'ordinateur, la preuve
 * (tools/emu/test_modal.py) rejouant ce que la passerelle recoit dans l'emulation. */
#ifndef CYC_VOICE0
#define CYC_VOICE0  0x42308828
#define VGAIN       ((s16 *)0x40fe4c90)              /* gain de la velocite de ce bloc (0..127) */
#define VGAIN_NEXT  ((s16 *)0x40fe4cd0)              /* celui des blocs suivants */
#endif
#define CYC_VSTRIDE 0x31c
#define MARK_OFF    0x2c
#define MARK        0x524e4731                       /* 'RNG1' */
#define TRACK(v)    (((u32)(unsigned long)(v) - (u32)CYC_VOICE0) / CYC_VSTRIDE)

#define V32(o)      (*(s32 *)(v + (o)))
#define P16(o)      (*(const s16 *)(p + (o)))

#ifndef MODAL_RAM
#define MODAL_RAM   0x46800000
#endif
#define TRACK_SIZE  0x18000                          /* 96 Ko par piste : la Part */

struct track {
	struct modal_part part;
};

struct ctl {                                         /* ce que update prepare pour render */
	struct modal_perf ps;
	struct modal_patch pa;
	s32 model, poly, chord, fresh;
	s32 vel;                                         /* gain de velocite du dernier trig (0..127) */
	s32 pend;                                        /* un trig arrive pendant le calcul des tables */
};

static struct ctl ctl[6];

/* la Part d'une piste tient dans sa place */
typedef char modal_track_fits[(sizeof(struct track) <= TRACK_SIZE) ? 1 : -1];

/* SHAPE (0..3) -> modele de Rings (ResonatorModel, modal_dsp.h) */
static const s8 SHAPE_MODEL[4] = { MODEL_MODAL, MODEL_SYMPATHETIC, MODEL_STRING, MODEL_SYMPATHETIC_Q };

static inline struct track *track_of(int t)
{
	return (struct track *)(MODAL_RAM + (unsigned long)t * TRACK_SIZE);
}

static inline s32 knob(s32 x)                        /* 8.8, 0..127 -> Q31 */
{
	x = x < 0 ? 0 : (x > 0x7f00 ? 0x7f00 : x);
	return x * 66052;                                /* 2^31 / 0x7f00 */
}

void modal_update(s32 pmod, char *v, const char *p)
{
	s32 t = TRACK(v), fine, chord, h, tonic, note, shape;
	struct ctl *c = &ctl[t];

	if (V32(MARK_OFF) != MARK) {                     /* 1re note sur cette machine */
		V32(MARK_OFF) = MARK;
		c->fresh = 1;
		c->chord = 0;
		c->pend = 0;
		c->vel = V32(0x34) ? VGAIN_NEXT[t] : VGAIN[t];   /* le trig qui a choisi la machine */
		c->vel = c->vel < 0 ? 0 : (c->vel > 127 ? 127 : c->vel);
	}
	shape = (P16(0x18) + 0x80) >> 8;                 /* SHAPE : 0..3 */
	shape = shape < 0 ? 0 : (shape > 3 ? 3 : shape);
	c->model = SHAPE_MODEL[shape];
	fine = P16(0x22);                                /* FUNC + SHAPE : 0x4000 1 voix, 0x5000 2, 0x6000 4 */
	c->poly = fine < 0x4800 ? 1 : (fine < 0x5800 ? 2 : 4);
	c->pa.structure = knob(P16(0x1c));
	c->pa.brightness = knob(P16(0x16));
	c->pa.damping = knob(P16(0x24));
	c->pa.position = knob(P16(0x1a));
	/* l'accord (cordes quantifiees) : STRUCTURE x 10, avec l'hysteresis de 0,1 de Rings */
	chord = qmul(c->pa.structure, 10 << 16);         /* Q16 */
	h = chord - (c->chord << 16) > 0 ? -6554 : 6554;
	chord = (chord + h + 0x8000) >> 16;
	c->chord = chord < 0 ? 0 : (chord > 10 ? 10 : chord);
	c->ps.chord = c->chord;
	/* hauteur : PITCH donne la tonique (do 60 au centre, 64), la note du trig la V/OCT : un trig au do 60 avec PITCH
	 * au centre joue le do 60. La tonique et la note jouee sont bornees a MIDI 0..127 : Rings n'est defini que la
	 * (SemitonesToRatio lit hors de ses tables sous -128 demi-tons du la 440), et le module n'en sort jamais. */
	tonic = ((s32)P16(0x14) << 8) - (4 << 16);
	tonic = tonic < 0 ? 0 : (tonic > (127 << 16) ? 127 << 16 : tonic);
	note = ((s32)P16(0x14) << 8) - (64 << 16) + pmod;
	note = note < 0 ? 0 : (note > (127 << 16) ? 127 << 16 : note);
	c->ps.tonic = tonic;
	c->ps.note = note - tonic;
	c->ps.fm = 0;
	c->ps.internal_exciter = 1;
	if (V32(0x34)) {                                 /* la velocite pour la frappe, pas pour le volume */
		s32 g = VGAIN_NEXT[t];
		c->vel = g < 0 ? 0 : (g > 127 ? 127 : g);
	}
	VGAIN[t] = VGAIN_NEXT[t] = 127;
	c->ps.strum = V32(0x38) != 0;
	c->ps.level = c->vel >= 127 ? Q31ONE : c->vel * (Q31ONE / 127);
}

void modal_render(s32 *out, char *v)
{
	static s32 o[MB], a[MB];                         /* hors de la pile (modal_dsp.h, sc) */
	s32 t = TRACK(v);
	struct ctl *c = &ctl[t];
	struct modal_part *part = &track_of(t)->part;
	int i;

	if (m_ready < MODAL_TABLES && !modal_init_step()) {
		/* les tables se calculent par morceaux, une vingtaine de blocs (13 ms) a la toute premiere note de MODAL
		 * apres le demarrage : silence, et la note part des que c'est pret */
		c->pend |= c->ps.strum;
		for (i = 0; i < MB; i++)
			out[i] = 0;
		return;
	}
	if (c->pend) {
		c->ps.strum = 1;
		c->pend = 0;
	}
	if (c->fresh) {
		modal_part_init(part);
		c->fresh = 0;
	}
	modal_set_model(part, c->model);
	if (c->poly != part->poly)
		modal_set_poly(part, c->poly);
	modal_process(part, &c->ps, &c->pa, (const s32 *)0, o, a);   /* pas d'entree : l'excitateur interne */
	for (i = 0; i < MB; i++) {                       /* une sortie : ODD - EVEN (notes/74), 1,0 -> 1/2 pleine echelle */
		s32 x = o[i] - a[i];
		x = x > 0x1ffffff ? 0x1ffffff : (x < -0x2000000 ? -0x2000000 : x);
		out[i] = shl(x, 6);
	}
}

/* ---- FUNC + SHAPE : la polyphonie, rangee dans FINE (detours de l'interface, notes/74 §3) ------------------- *
 * Memes contrats que lofi_step, lofi_fmt et lofi_draw de MACRO (tools/gen_syntakt_engines.py, notes/55 §8) :
 * l'OS les appelle par les std::function de l'objet d'interface de FINE (+0x50, +0x20, +0x30), que les detours
 * remplacent sur une piste MODAL quand FUNC est tenu et que le potard est SHAPE. Trois crans : 0x4000 (1 voix, le
 * defaut de FINE), 0x5000 (2), 0x6000 (4). */
s32 modal_poly_step(void *fn, s32 value, s32 delta, s32 min, s32 max, s32 dflt)
{
	int i = value >= 0x5800 ? 2 : (value >= 0x4800 ? 1 : 0);

	(void)fn;
	(void)min;
	(void)max;
	(void)dflt;
	i += delta > 0 ? 1 : (delta < 0 ? -1 : 0);
	i = i < 0 ? 0 : (i > 2 ? 2 : i);
	return 0x4000 + 0x1000 * i;
}

void modal_poly_fmt(void *fn, s32 value, char *buf)
{
	(void)fn;
	buf[0] = value >= 0x5800 ? '4' : (value >= 0x4800 ? '2' : '1');
	buf[1] = 0;
}

#ifdef __mcoldfire__
/* la valeur dans la fenetre de valeur (0x4001d818), dessinee comme l'OS dessine le texte d'un parametre :
 * grande police (0x401429ec), alignement 2, "%s" (0x40124b58) */
void modal_poly_draw(void *fn, s32 value, void *bitmap, s32 x, s32 y, s32 flag)
{
	struct {
		char text[16];
		u32 font[2];
	} l;

	(void)fn;
	(void)flag;
	modal_poly_fmt(0, value, l.text);
	((void (*)(void *, const void *))0x40072260)(l.font, (const void *)0x401429ec);
	((void (*)(void *, void *, s32, s32, s32, const char *, const char *))0x40071a04)(bitmap, l.font, x, y, 2,
											  (const char *)0x40124b58, l.text);
	((void (*)(void *))0x40072080)(l.font);
}
#endif
