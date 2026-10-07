/* SPDX-License-Identifier: MIT — Copyright (c) 2026 Combust. Voir ../LICENSE. */
/* La page GEN (Model:Cycles OS 1.13 + Model-TG 70b39dd), notes/50 §3.5.
 *
 *   SETTINGS + PAGE      ouvre la page plein écran (un clone de DrumSelect, comme Model-TG construit ses pages)
 *   sur la page :
 *     potards 1-4        piste EUC (couche 2) : Cycle, Densité, Régularité, Décalage ; écrits en direct
 *                        piste MAP (couche 1) : Style et Chaos (tout le kit), Remplissage, Décalage ; en direct
 *     potard 5           style de densité des pistes EUC (régulier / imbriqué)
 *     potard 6           mode de la piste de batterie choisie, EUC ou MAP (Kick..Perc ; Tone et Chord restent EUC)
 *     potards 7-10       Tone : SPR BIA STP DJV ; Chord : ADV CPX DJV OCT (notes, couche 3) ; écrits en direct
 *     potards 11, 12     TONIQUE et GAMME, pour Tone et Chord (tout le morceau)
 *   L'écran suit la dernière rangée de potards tournée : rythme (rangée 1) ou notes (rangée 2).
 *     DATA, pad de piste choisit la piste ; un nouvel appui sur le pad de la piste choisie la verrouille contre
 *                        Random (FUNC + pad garde son sens d'origine : FUNC ouvre la vue des mutes, qui prend les pads)
 *     PUNCH              Random (pistes non verrouillées) ; FUNC + PUNCH Undo (non affiché : les accords SETTINGS
 *                        font de même)
 *     RETURN, ou SETTINGS + PAGE à nouveau   ferme ; l'interface d'origine revient telle quelle
 *   Les voyants des touches de pas et la bande à l'écran montrent les 16 premiers pas de la piste choisie, tels que
 *   le pattern les tient. Page ouverte, aucun potard n'atteint un paramètre de son et les pads ne sonnent pas.
 *   SETTINGS + PATTERN / SETTINGS + TEMPO marchent partout.
 *
 * Appels de l'OS : ABI GCC m68k (arguments empilés de droite à gauche en mots longs, dépilés par l'appelant,
 * d0/d1/a0/a1 écrasables). */
#include "tweak.h"
#define STYLEMAP_WANT_NAMES
#include "../core/stylemap.h"

/* --- vues --- */
#define APP()             FN(0x400d0974, u32, void)()                 /* l'objet application de l'interface */
#define ROOT_OF(app)      FN(0x400060d8, u32, u32)(app)               /* = app + 64, le ViewController racine */
#define DRUMSELECT(o)     FN(0x400a22b0, void, void *)(o)             /* constructeur de DrumSelect, 0xd0 octets */
#define PRESENT(r, sp, f) FN(0x4007700e, u32, u32, void *, u32)(r, sp, f) /* empile un shared_ptr<View> */
#define RELEASE(pctl)     FN(0x400cf23c, void, void *)(pctl)          /* lâche une référence du bloc de contrôle */
#define REDRAW(v)         FN(0x40076082, void, void *)(v)             /* vue+20 = 1, racine+32 = 1 */
#define LEDS_DIRTY(r)     FN(0x40076c04, void, u32)(r)                /* racine+33 = 1 : redessiner les voyants */
#define BASE_KEYS(v, e)   FN(0x40075f3c, u32, void *, void *)(v, e)   /* la distribution des touches propre à View */
#define KEYCODE(e)        FN(0x4007240c, u32, void *)(e)              /* l'accesseur (par notre accroche) */
#define CLICKS(e, s, f)   FN(0x4006f73a, s32, void *, s32, s32)(e, s, f) /* pas du potard x (lent | rapide) */
/* --- dessin (y compté depuis le BAS) --- */
#define RECT(c, x0, y0, x1, y1, m)  FN(0x40070dea, void, void *, s32, s32, s32, s32, s32)(c, x0, y0, x1, y1, m)
#define FRAME(c, x0, y0, x1, y1, m) FN(0x40070c4e, void, void *, s32, s32, s32, s32, s32)(c, x0, y0, x1, y1, m)
#define PIXEL(c, x, y, m)           FN(0x400701b8, void, void *, s32, s32, s32)(c, x, y, m)
#define TEXT                        ((s32 (*)(void *, u32, s32, s32, u32, const char *, ...))0x40071a04)
#define FONT_SMALL 0x40ea14cc       /* SYS_FONT/MM_FONT de TG, 5x9 */
#define FMT_S      0x40124b58       /* « %s » dans l'OS */
/* options du texte : 0x02 centré, 0x04 aligné à droite, 0x08 inversé, 0x10 efface derrière */
/* --- voyants --- */
#define LIGHTS()           FN(0x400cfaf4, u32, void)()
#define LIGHT(l, i, on, c) FN(0x40005fe6, void, u32, u32, u32, u32)(l, i, on, c) /* mode 2 allumé / 1 éteint */
#define TRIG_LIGHT(k)      FN(0x4000608c, u32, u32)(k)                /* touche de pas 0..15 -> indice de voyant */
#define PAD_LIGHT(t)       FN(0x400060bc, u32, u32)(t)                /* pad de piste 0..5 -> indice de voyant */
#define VIEW_LIGHTS(r)     FN(0x40076ca2, void, u32)(r)               /* le LedHandler de chaque vue, la plus haute d'abord */
#define LIGHT_COLOR 0x404a8cb8

#define TG_MM_OBJ   (*(volatile u32 *)0x401b2088)
#define VIEWS_UP    (*(volatile u32 *)0x40fe4178)                     /* « vues prêtes » de mm_open de TG */

#define KEY_PUNCH 6
#define KEY_RETURN 12
#define KEY_SETTINGS 13
#define KEY_OPEN 15                 /* PAGE (mesuré par TG) */

/* ---- état (exporté pour la preuve en émulation) ---- */
u32 pg_obj;                         /* la page tant qu'elle est ouverte */
u32 pg_vt[0xb0 / 4];                /* notre copie du groupe de vtables de DrumSelect 0x40117918 */
u32 pg_sel;                         /* piste choisie */
s32 pg_last_idx;                    /* indice du dernier potard tourné (plus affiché ; la preuve le lit) */
static void *chord_ev, *rel_ev;     /* l'appui sur PAGE pris (ouvrir/fermer) et son relâchement */

static int ipl0(void)
{
	u16 sr;
	__asm__ volatile("move.w %%sr,%0" : "=d"(sr));
	return (sr & 0x0700) == 0;
}

static u32 root(void) { return ROOT_OF(APP()); }

static void close_page(void)
{
	u32 o = pg_obj;
	if (o)                                          /* fermeture différée : vtable principale +0x28 = 0x40076126 */
		(*(void (**)(u32))(*(u32 *)o + 0x28))(o);
}

void page_changed(void)
{
	if (pg_obj) {
		tw_read_rhythms();
		REDRAW((void *)pg_obj);
		LEDS_DIRTY(root());
	}
}

/* Construit et empile la page, comme mm_open de Model-TG (model_tg.s:8444-8575). Tâche d'interface, depuis
 * l'accesseur de touche. */
static int page_open(void)
{
	u32 o, *h, i, sp[2];

	if (pg_obj || TG_MM_OBJ || TG_RTG_ON || TG_SLE_ON || !VIEWS_UP || !ipl0() || !tw_ready())
		return 0;
	for (i = 0; i < 0xb0 / 4; i++)
		pg_vt[i] = ((const u32 *)0x40117918)[i];
	{
		extern void pg_dtor0(void), pg_dtor1(void), pg_enc_th(void);
		extern u32 pg_key(u32, void *), pg_enc(u32, void *);
		extern void pg_render(u32, void *);
		pg_vt[0x08 / 4] = (u32)pg_dtor0;        /* principale, emplacements 0, 1 : destructeurs */
		pg_vt[0x0c / 4] = (u32)pg_dtor1;
		pg_vt[0x10 / 4] = (u32)pg_key;          /* emplacement 2 : consumeKeyEvent (origine 0x400a292c) */
		pg_vt[0x18 / 4] = (u32)pg_render;       /* emplacement 4 : dessin (origine 0x400a24ca) */
		pg_vt[0x4c / 4] = (u32)pg_enc;          /* emplacement 17 : potard (origine 0x400a28b4) */
		pg_vt[0x60 / 4] = (u32)pg_enc_th;       /* base EncoderHandler, emplacement 2 (thunk d'origine 0x400a2926) */
	}
	o = (u32)NEW(0xd0);
	if (!o)
		return 0;
	DRUMSELECT((void *)o);
	((u32 *)o)[0] = (u32)&pg_vt[0x08 / 4];      /* vptr principal */
	((u32 *)o)[1] = (u32)&pg_vt[0x58 / 4];      /* vptr de EncoderHandler (+4) */
	h = (u32 *)NEW(0x10);                       /* bloc de contrôle du shared_ptr, comme l'ouverture d'origine 0x4001ca40 */
	if (!h) {
		FN(0x400f4486, void, u32)(o);           /* destructeur d'origine avec libération */
		return 0;
	}
	h[0] = 0x401000c4;
	h[1] = 1;
	h[2] = 1;
	h[3] = o;
	pg_obj = o;
	sp[0] = o;
	sp[1] = (u32)h;
	PRESENT(root(), sp, 0);
	RELEASE(&sp[1]);
	page_changed();
	return 1;
}

void pg_gone(void)                              /* depuis pg_dtor0/1 */
{
	pg_obj = 0;
	LEDS_DIRTY(root());                         /* les vues d'origine redessinent tous les voyants à la trame suivante */
}

/* ---- l'accesseur de touche, devant key_hook de TG : le code à rendre, ou TW_PASS ---- */
u32 ours_key(void *ev)
{
	u32 code = EV_CODE(ev), fl = EV_FLAGS(ev), r;

	r = tw_chord(ev);                           /* les accords SETTINGS, page ouverte ou non */
	if (r != TW_PASS)
		return r;
	if (code == KEY_OPEN) {                     /* l'appui de notre accord : relectures ; son relâchement */
		if (fl & 1) {
			if (chord_ev == ev) {
				EV_FLAGS(ev) = fl | 8;
				return 0;
			}
		} else {
			if (chord_ev) {
				chord_ev = 0;
				rel_ev = ev;
				return 0;
			}
			if (rel_ev == ev)
				return 0;
		}
	}
	if (pg_obj) {
		if (code == KEY_SETTINGS)
			return TW_PASS;                     /* kh_mod de TG : set_held, appui long, mod_used */
		return code;                            /* pas d'accords de TG sur notre page : la page décide */
	}
	if (code != KEY_OPEN || !TG_SET_HELD || TG_RTG_ON || TG_SLE_ON || !(fl & 1) || (fl & 8))
		return TW_PASS;
	if (!page_open())
		return TW_PASS;
	chord_ev = ev;
	rel_ev = 0;
	EV_FLAGS(ev) = fl | 8;                      /* les filtres de nouvel appui (0x400724a0) l'écartent désormais */
	TG_MOD_USED = 1;                            /* au relâchement de SETTINGS : pas de Config Menu */
	return 0;
}

/* ---- le gestionnaire de touches de la page (this, événement) -> utilisé ---- */
u32 pg_key(u32 self, void *ev)
{
	u32 fl = EV_FLAGS(ev);
	int fresh = (fl & 1) && !(fl & 8);
	u32 code = KEYCODE(ev);                     /* notre accroche : code brut, 0 si pris, SETTINGS par TG */

	if (code == 0)
		return 1;
	if (code == KEY_RETURN) {
		if (fl & 0x10)                          /* le clic, comme la page des machines se ferme (0x40072434) */
			close_page();
		return 1;
	}
	if (code == KEY_OPEN) {
		if (fresh && TG_SET_HELD) {
			chord_ev = ev;
			rel_ev = 0;
			EV_FLAGS(ev) = fl | 8;
			TG_MOD_USED = 1;
			close_page();
		}
		return 1;
	}
	if (code == KEY_PUNCH) {
		if (fresh) {
			if (fl & 2) {                       /* FUNC tenu (0x40072490) */
				tw_undo();
			} else {
				tw_random();
			}
			page_changed();
		}
		return 1;
	}
	if ((code >= 16 && code <= 31) || code == KEY_SETTINGS)
		return 1;                               /* ici, les touches de pas ne font qu'afficher le rythme */
	return BASE_KEYS((void *)self, ev);         /* FUNC + REC/PLAY/STOP : copier/effacer/coller de la vue */
}

/* ---- potards (this, événement) -> consommé. +12 indice (DATA 1, potards 2..13), +16 crans signés, +20 rapide ---- */
static s32 clamp(s32 v, s32 lo, s32 hi)
{
	return v < lo ? lo : v > hi ? hi : v;
}

static int track_is_l1(int t)
{
	return t < L1_LANES && ours_controls[CTRL(t, T_MODE)] == MODE_L1;
}

/* Après un changement pour tout le kit : réécrit la piste choisie et chaque piste générée, non verrouillée, de cette
 * couche. */
static void rewrite_layer(int l1, int sel)
{
	int i;
	for (i = 0; i < GEN_TRACKS; i++)
		if (i == sel || (((pg_owned >> i) & 1) && !((pg_lock >> i) & 1) && track_is_l1(i) == l1))
			tw_edit(i);
}

static const u8 L1_FILL_DEFAULT[L1_LANES] = {68, 70, 74, 55};   /* le cœur du motif et quelques coups secondaires */
static u8 pg_row2;                                                /* afficher les réglages de notes (rangée 2) */

/* Après un changement de tonalité : réécrit Tone et Chord s'ils sont la piste choisie, ou générés et non
 * verrouillés. */
static void rewrite_melodic(int sel)
{
	int i;
	for (i = TONE_TRACK; i <= CHORD_TRACK; i++)
		if (i == sel || (((pg_owned >> i) & 1) && !((pg_lock >> i) & 1)))
			tw_edit(i);
}

/* Passe la piste t entre la couche 2 (EUC) et la couche 1 (MAP), avec les réglages par défaut de cette couche. */
static void set_mode(int t, u16 mode)
{
	u16 *c = ours_controls, def[GEN_CONTROLS];
	if (t >= L1_LANES || c[CTRL(t, T_MODE)] == mode)
		return;
	gen_default_controls(def);
	c[CTRL(t, T_MODE)] = mode;
	if (mode == MODE_L1) {
		c[CTRL(t, T_DENSITY)] = L1_FILL_DEFAULT[t];
		c[CTRL(t, T_SHIFT)] = 0;
	} else {
		c[CTRL(t, T_CYCLE)] = def[CTRL(t, T_CYCLE)];
		c[CTRL(t, T_DENSITY)] = def[CTRL(t, T_DENSITY)];
		c[CTRL(t, T_EVENNESS)] = def[CTRL(t, T_EVENNESS)];
		c[CTRL(t, T_SHIFT)] = def[CTRL(t, T_SHIFT)];
	}
	tw_edit(t);
}

u32 pg_enc(u32 self, void *ev)
{
	s32 idx = *(s32 *)((u8 *)ev + 12);
	s32 d = CLICKS(ev, 1, 4);
	u16 *c = ours_controls;
	int t = (int)pg_sel, i;

	(void)self;
	if (!d)
		return 1;
	pg_last_idx = idx;
	if (idx == 1) {
		pg_sel = (u32)clamp((s32)pg_sel + (d > 0 ? 1 : -1), 0, GEN_TRACKS - 1);
	} else if (idx >= 2 && idx <= 5 && track_is_l1(t)) {
		if (idx == 2) {
			c[CTRL_STYLE] = (u16)clamp((s32)c[CTRL_STYLE] + d, 0, STYLE_MAX);
			rewrite_layer(1, t);
		} else if (idx == 3) {
			c[CTRL(t, T_DENSITY)] = (u16)clamp((s32)c[CTRL(t, T_DENSITY)] + d, 0, FILL_MAX);
			tw_edit(t);
		} else if (idx == 4) {
			c[CTRL_CHAOS] = (u16)clamp((s32)c[CTRL_CHAOS] + d, 0, CHAOS_MAX);
			rewrite_layer(1, t);
		} else {
			c[CTRL(t, T_SHIFT)] = (u16)((((s32)c[CTRL(t, T_SHIFT)] + d) % MAP_STEPS + MAP_STEPS) % MAP_STEPS);
			tw_edit(t);
		}
	} else if (idx >= 2 && idx <= 5) {
		s32 n = c[CTRL(t, T_CYCLE)], k = c[CTRL(t, T_DENSITY)], e = c[CTRL(t, T_EVENNESS)], s = c[CTRL(t, T_SHIFT)];
		n = clamp(n, 1, GEN_MAX_CYCLE);
		if (idx == 2)
			n = clamp(n + d, 1, GEN_MAX_CYCLE);
		k = clamp(idx == 3 ? k + d : k, 0, n);
		e = clamp(idx == 4 ? e + d : e, 0, tw_even_count(n, k) - 1);
		s = idx == 5 ? ((s + d) % n + n) % n : clamp(s, 0, n - 1);
		c[CTRL(t, T_CYCLE)] = (u16)n;
		c[CTRL(t, T_DENSITY)] = (u16)k;
		c[CTRL(t, T_EVENNESS)] = (u16)e;
		c[CTRL(t, T_SHIFT)] = (u16)s;
		tw_edit(t);
	} else if (idx == 6) {
		u16 style = d > 0 ? DENSITY_NESTED : DENSITY_EUCLIDEAN;
		if (c[CTRL_DENSITY_STYLE] != style) {
			c[CTRL_DENSITY_STYLE] = style;
			for (i = 0; i < GEN_TRACKS; i++) {
				if (!((pg_owned >> i) & 1) || ((pg_lock >> i) & 1) || track_is_l1(i))
					continue;
				c[CTRL(i, T_EVENNESS)] = (u16)clamp(c[CTRL(i, T_EVENNESS)], 0,
					tw_even_count(c[CTRL(i, T_CYCLE)], c[CTRL(i, T_DENSITY)]) - 1);
				tw_edit(i);
			}
		}
	} else if (idx == 7) {
		set_mode(t, d > 0 ? MODE_L1 : MODE_L2);
	} else if (idx >= 8 && idx <= 11 && t >= TONE_TRACK) {
		int base = t == TONE_TRACK ? CTRL_TONE : CTRL_CHORD, k = (int)idx - 8;
		s32 hi = (t == CHORD_TRACK && k == 3) ? 4 : 127;          /* octave de Chord : 0..4 = -2..+2 */
		c[base + k] = (u16)clamp((s32)c[base + k] + d, 0, hi);
		tw_edit(t);
	} else if (idx == 12) {
		c[CTRL_ROOT] = (u16)((((s32)c[CTRL_ROOT] + d) % 12 + 12) % 12);
		rewrite_melodic(t);
	} else if (idx == 13) {
		c[CTRL_SCALE] = (u16)clamp((s32)c[CTRL_SCALE] + (d > 0 ? 1 : -1), 0, L3_SCALES - 1);
		rewrite_melodic(t);
	}
	if (idx >= 2 && idx <= 7)
		pg_row2 = 0;
	else if (idx >= 8)
		pg_row2 = 1;
	page_changed();
	return 1;                                   /* jamais transmis plus bas : aucun paramètre de son ne bouge */
}

/* ---- pads, depuis ours_pad_hook tant que la page est ouverte ---- */
void ours_pad(void *ev)
{
	u32 type = *(u32 *)((u8 *)ev + 16), id = *(u32 *)((u8 *)ev + 20), t;

	if (type != 1 || id >= 7)
		return;
	t = ((const u32 *)0x401001d0)[id];          /* numéro de pad -> piste, la table d'origine qu'utilise TG */
	if (t > 5)
		return;
	if (t == pg_sel)
		pg_lock ^= 1u << t;                     /* un nouvel appui sur la piste choisie : verrouiller / déverrouiller */
	else
		pg_sel = t;
	page_changed();
}

/* ---- voyants : à la place de « jsr 0x40076ca2 » en 0x40006a76. Le premier mode posé dans une trame l'emporte. ---- */
void ours_led_frame(u32 r)
{
	if (pg_obj) {
		u32 L = LIGHTS(), k;
		for (k = 0; k < 16; k++)
			LIGHT(L, TRIG_LIGHT(k), (pg_rhythm[pg_sel] >> k) & 1, LIGHT_COLOR);
		for (k = 0; k < 6; k++)
			LIGHT(L, PAD_LIGHT(k), k == pg_sel, LIGHT_COLOR);
	}
	VIEW_LIGHTS(r);
}

/* ---- dessin ---- */
static char *put_u(char *p, u32 v)
{
	char tmp[10];
	int n = 0;
	do {
		tmp[n++] = (char)('0' + v % 10);
		v /= 10;
	} while (v);
	while (n)
		*p++ = tmp[--n];
	return p;
}

static char *put_s(char *p, const char *s)
{
	while (*s)
		*p++ = *s++;
	return p;
}

static void text(void *c, s32 x, s32 top, u32 flags, const char *s)
{
	TEXT(c, FONT_SMALL, x, 55 - top, flags, (const char *)FMT_S, s);
}

static const char *const NAMES[GEN_TRACKS] = {"KICK", "SNARE", "METAL", "PERC", "TONE", "CHORD"};
static const char *const LABELS[4] = {"CYC", "DEN", "EVN", "SFT"};
static const char *const LABELS_L1[4] = {"STY", "FIL", "CHS", "SFT"};
static const char *const LABELS_TONE[4] = {"SPR", "BIA", "STP", "DJV"};
static const char *const LABELS_CHORD[4] = {"ADV", "CPX", "DJV", "OCT"};
static const char *const ROOTS[12] = {"C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"};
static const char *const SCALE_NAMES[L3_SCALES] = {"MAJ", "MIN", "DOR", "MIX", "HMI", "PMA", "PMI"};
static const s32 COL_X[4] = {13, 39, 75, 113};    /* centres des colonnes ; les valeurs EVN vont jusqu'à « 123/809 » */

void pg_render(u32 self, void *c)
{
	char b[24], *p;
	s32 i;
	int t = (int)pg_sel;
	u32 r = pg_rhythm[t];
	const u16 *ct = ours_controls;
	u32 v[4];

	(void)self;
	int l1 = track_is_l1(t), melodic = t >= TONE_TRACK, row2 = melodic && pg_row2;
	const char *const *labels = row2 ? (t == TONE_TRACK ? LABELS_TONE : LABELS_CHORD) : l1 ? LABELS_L1 : LABELS;
	v[0] = l1 ? ct[CTRL_STYLE] : ct[CTRL(t, T_CYCLE)];
	v[1] = ct[CTRL(t, T_DENSITY)];
	v[2] = l1 ? ct[CTRL_CHAOS] : ct[CTRL(t, T_EVENNESS)];
	v[3] = ct[CTRL(t, T_SHIFT)];
	if (row2)
		for (i = 0; i < 4; i++)
			v[i] = ct[(t == TONE_TRACK ? CTRL_TONE : CTRL_CHORD) + i];
	/* Disposition, en lignes depuis le haut : en-tête 0-8, filet 11, noms des réglages 15-23, valeurs 25-33,
	 * bande des 16 pas 40-52, repères des temps 55. Colonnes centrées ; la régularité a la plus large. */
	RECT(c, 0, 0, 127, 63, 0);                  /* efface tout l'écran */
	text(c, 2, 0, 0x08, l1 ? "MAP" : "EUC");    /* étiquette inversée : le mode de la piste */
	p = put_s(b, NAMES[t]);
	if ((pg_lock >> t) & 1)
		p = put_s(p, " LOCK");
	*p = 0;
	text(c, 26, 0, 0x10, b);
	if (melodic) {                              /* la tonalité, ou le motif du plan le plus proche, ou le style de densité */
		p = put_s(b, ROOTS[ct[CTRL_ROOT] % 12]);
		*p++ = ' ';
		p = put_s(p, SCALE_NAMES[ct[CTRL_SCALE] < L3_SCALES ? ct[CTRL_SCALE] : 0]);
		*p = 0;
		text(c, 125, 0, 0x14, b);
	} else if (l1) {
		s32 st = ct[CTRL_STYLE] > STYLE_MAX ? STYLE_MAX : ct[CTRL_STYLE];
		text(c, 125, 0, 0x14, STYLE_SHORT[(st + 8) >> 4]);
	} else {
		text(c, 125, 0, 0x14, ct[CTRL_DENSITY_STYLE] == DENSITY_NESTED ? "NEST" : "EVEN");
	}
	RECT(c, 0, 63 - 11, 127, 63 - 11, 1);       /* filet */
	for (i = 0; i < 4; i++) {                   /* les quatre réglages de la piste */
		text(c, COL_X[i], 15, 0x12, labels[i]);
		p = b;
		if (row2 && t == CHORD_TRACK && i == 3) {   /* octave : 0..4 affiché -2..+2 */
			*p++ = v[i] < 2 ? '-' : v[i] > 2 ? '+' : ' ';
			p = put_u(p, v[i] < 2 ? 2 - v[i] : v[i] - 2);
		} else {
			p = put_u(p, v[i]);
		}
		if (i == 2 && !l1 && !row2) {
			*p++ = '/';
			p = put_u(p, (u32)tw_even_count((int)v[0], (int)v[1]) - 1);
		}
		*p = 0;
		text(c, COL_X[i], 25, 0x12, b);
	}
	for (i = 0; i < 16; i++) {                  /* la bande des 16 pas */
		s32 x0 = 8 * i, x1 = 8 * i + 6;
		if ((r >> i) & 1)
			RECT(c, x0, 63 - 52, x1, 63 - 40, 1);
		else
			FRAME(c, x0, 63 - 52, x1, 63 - 40, 1);
		if ((i & 3) == 0)
			PIXEL(c, x0 + 3, 63 - 55, 1);       /* repère sous les pas 1, 5, 9, 13 */
	}
}
