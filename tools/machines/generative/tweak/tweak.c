/* SPDX-License-Identifier: MIT — Copyright (c) 2026 Combust. Voir ../LICENSE. */
/* Le générateur dans l'OS, par-dessus model-tg (OS 1.13, Model-TG 70b39dd), notes/50 :
 *   SETTINGS + PATTERN = Random : nouveaux réglages pour chaque piste non verrouillée, écrits dans le pattern en
 *                        cours (trigs sur 64 pas, longueur propre à chaque piste, vélocités, notes, accords).
 *   SETTINGS + TEMPO   = Undo du dernier Random (trigs, données des pas, p-locks, longueurs et réglages GEN).
 * Les mêmes actions sont sur la page GEN (page.c), qui règle aussi une piste en direct.
 * Le calcul est dans ../core (portage C du cœur de référence, vérifié par les vecteurs dorés).
 *
 * Appels de l'OS : ABI GCC m68k, arguments empilés de droite à gauche en mots longs, dépilés par l'appelant,
 * résultat dans d0, d0-d1/a0-a1 écrasables. */
#include "tweak.h"

#define UI_CTX()             FNP(0x400cf866, void)()
#define CUR_PATTERN(ctx)     FNP(0x4000f208, void *)(ctx)
#define TRACK_OBJ(p, t)      FNP(0x4000cfcc, void *, s32)(p, t)      /* = p + 0x70 + 88*t */
#define SCALE_OBJ(p)         FNP(0x4000d0dc, void *)(p)              /* = p + 44 */
#define TRK_LEN(o)           FN(0x40016402, s32, void *)(o)
#define FLAG_TEST(o, s, m)   FN(0x400157d6, u32, void *, s32, u32)(o, s, m)
#define TRIG_SET(o, s, on)   FN(0x40017b48, void, void *, s32, u32)(o, s, on)
#define TRIG_ERASE(o, s, k)  FN(0x40017c4e, void, void *, s32, u32)(o, s, k)
#define VEL_SET(o, s, v)     FN(0x400166c2, void, void *, s32, s32)(o, s, v)  /* -1 = valeur de la piste ; notifie */
#define NOTE_SET(o, s, n)    FN(0x40016642, void, void *, s32, s32)(o, s, n)  /* note MIDI absolue, -1 = note de la piste */
#define SET_TRK_LEN(o, n)    FN(0x40016aec, void, void *, s32)(o, n)       /* borné à 2..64, notifie */
#define SET_SCALE_MODE(s, m) FN(0x4000cba6, void, void *, s32)(s, m)       /* 0 par pattern, 1 par piste */
#define SET_MASTER_LEN(s, n) FN(0x4000c9c4, void, void *, s32)(s, n)
#define DELETE(p)            FN(0x400802ec, void, void *)(p)
#define ALLOC(n)             FNP(0x40080064, u32)(n)
#define POST(q, m)           FN(0x40001fba, void, void *, void *)(q, m)
#define DATA(o)              ((u8 *)(*(u32 (***)(void *))(o))[10](o))      /* vtable[10] : le bloc de 722 octets */
/* p-locks : emplacement 0..32 par pas, -1 = aucun. Pose et effacement ignorent les pas au-delà de la longueur. */
#define LOCK_GET(o, s, k)    ((s16)FN(0x4001591e, s32, void *, s32, s32)(o, s, k))
#define LOCK_SET(o, s, k, v) FN(0x4001646a, s32, void *, s32, s32, s32)(o, s, k, v)
#define LOCK_CLEAR(o, s, k)  FN(0x400164b0, s32, void *, s32, s32)(o, s, k)

#define KEY_A 3              /* PATTERN */
#define TRACK_BYTES 722
#define LOCK_SLOTS 33
#define TRACK_LEN_OFF 713   /* 16 bits, non aligné */
#define VEL_OFF 128         /* vélocité de chaque pas, -1 = valeur de la piste */
#define NOTE_OFF 580        /* note de chaque pas : note MIDI absolue, -1 = note de la piste */
#define SLOT_SHAPE 12       /* emplacement de p-lock de SHAPE ; valeurs en virgule fixe 8.8 (valeur << 8) */

/* Qualité d'accord de la couche 3 -> indice SHAPE de la machine Chord (manuel, annexe C ; notes/50 §1.3) */
static const u8 CHORD_SHAPE[7] = {4 /* Major */, 3 /* minor */, 17 /* mb5 */, 10 /* Maj7 */, 8 /* M7 = septième de dominante */,
                                  7 /* m7 */, 19 /* m7b5 */};

/* ---- message à la tâche d'interface (sv_post de Model-TG, model_tg.s:17236-17266) ---- */
struct msg {
	u8 type, pad[3];
	void *data;              /* +4  stockage de la fermeture (ALLOC(1)), libéré par le gestionnaire */
	u32 z8;                  /* +8 */
	void *mgr;               /* +0xc GENERIC_MANAGER 0x4002f136 */
	void (*cb)(void *, u32); /* +0x10 appelé (fermeture, arg) dans la tâche d'interface */
	u32 arg;                 /* +0x14 */
	volatile u32 busy;       /* +0x18 remis à zéro par la tâche d'interface après l'appel (0x40008236) */
};
static struct msg m;
static void run(void *closure, u32 what);

static void post(u32 what)
{
	if (m.busy)
		return;
	m.data = ALLOC(1);
	m.z8 = 0;
	m.mgr = (void *)0x4002f136;
	m.cb = run;
	m.arg = what;
	m.busy = 1;
	m.type = 6;
	POST((void *)0x404a9154, &m);
}

/* ---- accords SETTINGS + PATTERN (Random), SETTINGS + TEMPO (Undo), depuis l'accesseur de touche ---- */
static void *took[2];          /* l'appui pris, par touche */
static void *rel[2];           /* le relâchement pris */
static u32 chord(u8 *ev)
{
	u32 code = EV_CODE(ev), *flags = (u32 *)(ev + 16);
	int k = code == KEY_A ? 0 : 1;

	if (*flags & 1) {                      /* enfoncée */
		if (took[k] == ev) {               /* une relecture de l'appui pris */
			*flags |= 8;
			return 1;
		}
		if (*flags & 8)                    /* répétition d'un appui non pris */
			return 0;
		took[k] = ev;
		rel[k] = 0;
		*flags |= 8;                       /* les filtres de nouvel appui (0x400724a0) l'écartent désormais */
		TG_MOD_USED = 1;
		post(k);
		return 1;
	}
	if (took[k]) {                         /* le relâchement de notre appui */
		took[k] = 0;
		rel[k] = ev;
		return 1;
	}
	return rel[k] == ev;                   /* une relecture de ce relâchement */
}

u32 tw_chord(void *ev)
{
	u32 code = EV_CODE(ev);
	if ((code != 3 && code != 14) || !TG_SET_HELD || TG_RTG_ON || TG_SLE_ON)
		return TW_PASS;
	return chord(ev) ? 0 : TW_PASS;        /* pris : code 0 pour cette lecture et les suivantes, comme TG */
}

/* ---- état du générateur ---- */
static necklace_t nk;
static u8 nk_ready, ctrl_ready;
u16 ours_controls[GEN_CONTROLS];   /* exporté pour que la preuve en émulation vérifie le tirage */
u32 ours_seed;
u32 pg_lock;
u32 pg_owned;
u16 pg_rhythm[GEN_TRACKS];
static u8 locked[GEN_TRACKS];
static gen_out_t *out;                 /* dans le tas (environ 1,6 Ko), alloué avec les tables */

int tw_ready(void)
{
	u16 *masks, *scratch;
	if (!ctrl_ready) {
		gen_default_controls(ours_controls);
		ctrl_ready = 1;
	}
	if (nk_ready)
		return 1;
	if (!out && !(out = NEW(sizeof(gen_out_t))))
		return 0;
	masks = NEW(NECKLACE_ENTRIES * 2);
	scratch = NEW(NECKLACE_SCRATCH_WORDS * 2);
	if (!masks || !scratch) {
		if (masks)
			DELETE(masks);
		if (scratch)
			DELETE(scratch);
		return 0;
	}
	necklace_init(&nk, masks, scratch);
	DELETE(scratch);
	nk_ready = 1;
	return 1;
}

u16 tw_even_count(int n, int k)
{
	if (ours_controls[CTRL_DENSITY_STYLE] == DENSITY_NESTED)
		return NESTED_EVEN_MAX + 1;
	return nk_ready ? necklace_count(&nk, n, k) : 1;
}

/* ---- Undo à un niveau : blocs des pistes, p-locks et réglages, dans le tas (environ 30 Ko, une fois) ---- */
struct snap {
	u8 track[GEN_TRACKS][TRACK_BYTES];
	s16 lock[GEN_TRACKS][GEN_STEPS][LOCK_SLOTS];
	u16 controls[GEN_CONTROLS];
	u32 owned;
};
static struct snap *snap;
static u8 snap_mode, snap_ok;
static u16 snap_mlen;

static int snapshot(void *pat, u8 *sb)
{
	int t, s, k;
	if (!snap && !(snap = NEW(sizeof(struct snap))))
		return 0;
	for (t = 0; t < GEN_TRACKS; t++) {
		void *o = TRACK_OBJ(pat, t);
		u8 *d = DATA(o);
		if (!d)
			return 0;
		for (s = 0; s < TRACK_BYTES; s++)
			snap->track[t][s] = d[s];
		for (s = 0; s < GEN_STEPS; s++)
			for (k = 0; k < LOCK_SLOTS; k++)
				snap->lock[t][s][k] = LOCK_GET(o, s, k);
	}
	for (k = 0; k < GEN_CONTROLS; k++)
		snap->controls[k] = ours_controls[k];
	snap->owned = pg_owned;
	snap_mode = sb[25];
	snap_mlen = *(u16 *)(sb + 20);
	snap_ok = 1;
	return 1;
}

/* Les trigs d'une piste par les fonctions d'origine, pour que le séquenceur soit notifié. Elles ignorent les pas
 * au-delà de la longueur de la piste : on l'ouvre d'abord à 64, l'appelant pose ensuite la vraie longueur. */
static void write_trigs(void *o, const u8 *want)
{
	int s;
	SET_TRK_LEN(o, 64);
	for (s = 0; s < GEN_STEPS; s++) {
		int have = FLAG_TEST(o, s, 1) & 0xff;
		if (want[s] && !have)
			TRIG_SET(o, s, 1);
		else if (!want[s] && have)
			TRIG_ERASE(o, s, 0);
	}
}

/* Écrit les pistes générées de `out` (celles marquées written, ou seulement `only` s'il est >= 0). */
static void write_out(void *pat, void *sc, int only)
{
	int t;
	SET_SCALE_MODE(sc, 1);                     /* les longueurs par piste ne valent que dans ce mode */
	for (t = 0; t < GEN_TRACKS; t++) {
		void *o = TRACK_OBJ(pat, t);
		if (!out->written[t] || (only >= 0 && t != only))
			continue;
		write_trigs(o, out->trig[t]);
		{                                      /* tant que la piste est ouverte à 64 pas : */
			const s8 *v = out->velocity[t], *n = out->note[t], *q = out->chord[t];
			u8 *d = DATA(o);
			int s;
			for (s = 0; s < GEN_STEPS; s++) {
				if (v[s] >= 0 && d && (s8)d[VEL_OFF + s] != v[s])
					VEL_SET(o, s, v[s]);           /* vélocités de la couche 1 : accents et notes fantômes */
				if (n[s] >= 0 && d && (s8)d[NOTE_OFF + s] != n[s])
					NOTE_SET(o, s, n[s]);          /* notes et fondamentales de la couche 3 */
				if (q[s] >= 0 && q[s] < 7) {       /* qualité d'accord de la couche 3 : un p-lock de SHAPE sur le trig */
					s32 want = CHORD_SHAPE[(int)q[s]] << 8;
					if (LOCK_GET(o, s, SLOT_SHAPE) != want)
						LOCK_SET(o, s, SLOT_SHAPE, want);
				}
			}
		}
		/* la longueur minimale de l'OS est 2 ; un cycle d'un pas est répété, 2 pas jouent pareil */
		SET_TRK_LEN(o, out->length[t] < 2 ? 2 : out->length[t]);
	}
	SET_MASTER_LEN(sc, 64);
}

void tw_read_rhythms(void)
{
	void *pat = CUR_PATTERN(UI_CTX());
	int t, s;
	for (t = 0; t < GEN_TRACKS; t++) {
		void *o = TRACK_OBJ(pat, t);
		s32 len = TRK_LEN(o);
		u16 r = 0;
		for (s = 0; s < 16 && s < len; s++)
			if (FLAG_TEST(o, s, 1) & 0xff)
				r |= (u16)(1u << s);
		pg_rhythm[t] = r;
	}
}

void tw_random(void)
{
	void *pat = CUR_PATTERN(UI_CTX()), *sc = SCALE_OBJ(pat);
	u8 *sb = DATA(sc);
	int t;

	if (!sb || !tw_ready() || !snapshot(pat, sb))
		return;
	for (t = 0; t < GEN_TRACKS; t++)
		locked[t] = (u8)((pg_lock >> t) & 1);
	ours_seed = gen_hash32(ours_seed ^ DTIM0);
	gen_randomize(&nk, ours_seed, ours_controls, locked);
	gen_generate(&nk, ours_seed, ours_controls, locked, out);
	write_out(pat, sc, -1);
	pg_owned |= ~pg_lock & 0x3f;
}

int tw_edit(int t)
{
	void *pat = CUR_PATTERN(UI_CTX()), *sc = SCALE_OBJ(pat);
	if (!DATA(sc) || !tw_ready())
		return 0;
	if (ours_controls[CTRL(t, T_MODE)] != MODE_L1)
		ours_controls[CTRL(t, T_MODE)] = MODE_L2;
	gen_generate(&nk, ours_seed, ours_controls, 0, out);
	write_out(pat, sc, t);
	pg_owned |= 1u << t;
	return 1;
}

void tw_undo(void)
{
	void *pat = CUR_PATTERN(UI_CTX()), *sc = SCALE_OBJ(pat);
	u8 want[GEN_STEPS];
	int t, s, k;

	if (!snap_ok)
		return;
	SET_SCALE_MODE(sc, 1);
	for (t = 0; t < GEN_TRACKS; t++) {
		void *o = TRACK_OBJ(pat, t);
		u8 *d, *tb = snap->track[t];
		for (s = 0; s < GEN_STEPS; s++)
			want[s] = tb[2 * s + 1] & 1;
		write_trigs(o, want);                   /* laisse la piste ouverte à 64 pas */
		d = DATA(o);                            /* puis les octets qu'un effacement remet : drapeaux, note, vélocité… */
		for (s = 0; s < TRACK_LEN_OFF - 1; s++)
			d[s] = tb[s];
		for (s = 0; s < GEN_STEPS; s++)         /* les p-locks qu'un effacement a ôtés, par les fonctions de p-lock */
			for (k = 0; k < LOCK_SLOTS; k++) {
				s16 v = snap->lock[t][s][k];
				if (LOCK_GET(o, s, k) == v)
					continue;
				if (v < 0)
					LOCK_CLEAR(o, s, k);
				else
					LOCK_SET(o, s, k, v);
			}
		SET_TRK_LEN(o, (tb[TRACK_LEN_OFF] << 8) | tb[TRACK_LEN_OFF + 1]);
	}
	for (k = 0; k < GEN_CONTROLS; k++)
		ours_controls[k] = snap->controls[k];
	pg_owned = snap->owned;
	SET_SCALE_MODE(sc, snap_mode);
	SET_MASTER_LEN(sc, snap_mlen);
	snap_ok = 0;
}

static void run(void *closure, u32 what)
{
	(void)closure;
	if (what == 0)
		tw_random();
	else
		tw_undo();
	page_changed();
}
