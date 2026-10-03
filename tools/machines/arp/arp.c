/* Arpégiateur à la place du retrig du Model:Cycles (MAIN OS 1.13), notes/32.
 *
 * Côté audio (interruption audio, file d'événements lue en 0x40058d46) :
 *   - arp_filter : en tête du traitement des notes (0x40058e28), pour le jeu en direct. Tient la liste des notes
 *     enfoncées de chaque piste ; une note ajoutée pendant que l'arpège tourne y entre sans jouer (l'OS l'ignore) ;
 *     une fin de note n'arrête l'arpège que s'il ne reste plus rien.
 *   - arp_copy : à la place de la copie de l'événement gardé, à chaque répétition (0x400587f6) : la répétition joue
 *     la note suivante de l'arpège.
 * Côté interface (menu FUNC + RETRIG, RetrigPadsMenuView) :
 *   - arp_menu_add : deux lignes de plus en fin de constructeur, « Arp » (sens) et « Oct » (octaves).
 * Réglages : octet +512 de la piste du pattern (inutilisé par l'OS, recopié tel quel à l'enregistrement),
 * bits 0-2 = sens, bits 3-4 = octaves - 1. 0 = montant, 1 octave.
 */
typedef unsigned char u8;
typedef signed char s8;
typedef unsigned int u32;
typedef int s32;

enum { M_UP, M_DOWN, M_UPDN, M_RAND, M_PLAY, M_OFF, M_COUNT };
#define MAXN 12                                   /* notes tenues par piste */

/* --- événement de note (0x4005894a) --- */
#define EV_TYPE    0                              /* 0 : note */
#define EV_ONOFF   4                              /* 1 : note, 2 : fin de note */
#define EV_TRACK   8
#define EV_SRC     12                             /* 2 : jeu en direct ; -1 : l'OS l'ignore */
#define EV_NOTE    28
#define EV_FLAGS   40
#define F_RETRIG   0x8000
#define F_REPEAT   0x40000                        /* répétition produite par le retrig */

#define I32(p, o)  (*(volatile s32 *)((u8 *)(p) + (o)))
#define RTG(t, o)  I32(0x40a78d58 + 28 * (t), o)  /* état du retrig : +4 fin (-1 : note tenue), +20 copie rejouée */
#define CUR_NOTE(t) I32(0x40fe4cb4, 4 * (t))      /* note en cours de la piste */

struct trk {
	u8 held[MAXN];                                /* notes tenues, dans l'ordre de jeu */
	u8 n, last, pos;                              /* nombre ; dernière note jouée ; position (ordre de jeu, hasard) */
	s8 dir;                                       /* aller-retour : +1 monte, -1 descend */
};
static struct trk st[6];
static u32 seed = 0x2545f491;

/* Octet +512 de la piste t du pattern en cours (0x40054828 : *(0x40a7887c) + 30706), lu côté audio. */
static int cfg_audio(int t)
{
	u8 *seq = *(u8 **)0x40a7887c;
	u32 pat;

	if (!seq)
		return 0;
	pat = I32(seq, 30706);
	if (pat > 95)
		return 0;
	return ((u8 *)0x406f3a40)[pat * 30710 + t * 722 + 512];
}

static int mode_of(int c)
{
	c &= 7;
	return c < M_COUNT ? c : M_UP;
}

void arp_filter(u8 *ev)
{
	u32 t = I32(ev, EV_TRACK), n, i;
	struct trk *s;

	if (I32(ev, EV_TYPE) != 0 || I32(ev, EV_SRC) != 2 || t > 5)
		return;
	s = &st[t];
	if (!RTG(t, 4) || !RTG(t, 20))                /* plus de retrig sur la piste : liste périmée */
		s->n = 0;
	n = I32(ev, EV_NOTE);
	if (I32(ev, EV_ONOFF) == 1) {
		if ((I32(ev, EV_FLAGS) & (F_RETRIG | F_REPEAT)) != F_RETRIG || n > 127)
			return;
		if (mode_of(cfg_audio(t)) == M_OFF) {     /* sens OFF : le retrig d'origine */
			s->n = 0;
			return;
		}
		if (!s->n) {                              /* 1re note : le retrig d'origine démarre avec elle */
			s->last = n;
			s->dir = 1;
			s->pos = 0;
		} else
			I32(ev, EV_SRC) = -1;                 /* l'arpège tourne : la note y entre, le rythme continue */
		for (i = 0; i < s->n; i++)
			if (s->held[i] == n)
				return;
		if (s->n < MAXN)
			s->held[s->n++] = n;
		return;
	}
	for (i = 0; i < s->n; i++)                    /* fin de note : retirée de la liste */
		if (s->held[i] == n) {
			for (s->n--; i < s->n; i++)
				s->held[i] = s->held[i + 1];
			if (s->n)
				I32(ev, EV_SRC) = -1;             /* d'autres notes restent tenues : on continue */
			else
				I32(ev, EV_NOTE) = CUR_NOTE(t);   /* la dernière : fin de la note en cours, l'OS arrête tout */
			return;
		}
}

/* Plus petite (up) ou plus grande (!up) valeur de la liste (notes tenues + 12 x octave) strictement au-delà de
 * ref ; -1 s'il n'y en a pas. */
static int beyond(struct trk *s, int octs, int ref, int up)
{
	int i, v, best = -1;

	for (i = 0; i < s->n * octs; i++) {
		v = s->held[i % s->n] + 12 * (i / s->n);
		if (v <= 127 && (up ? v > ref && (best < 0 || v < best) : v < ref && v > best))
			best = v;
	}
	return best;
}

/* À la place de jsr 0x40091f20(copie, événement gardé) dans le traitement d'une répétition (0x40058736). */
void arp_copy(u8 *dst, u8 *src)
{
	u32 t, p, len;
	int c, mode, octs, v, up;
	struct trk *s;

	((void (*)(u8 *, u8 *))0x40091f20)(dst, src);
	t = I32(dst, EV_TRACK);
	if (t > 5 || !st[t].n)
		return;
	s = &st[t];
	c = cfg_audio(t);
	mode = mode_of(c);
	octs = ((c >> 3) & 3) + 1;
	len = s->n * octs;
	if (mode == M_OFF)
		return;
	if (mode >= M_RAND) {                         /* hasard, ordre de jeu : par position */
		if (mode == M_RAND) {
			seed = seed * 1103515245 + 12345;
			p = (seed >> 16) % len;
			if (len > 1 && p == s->pos)           /* pas deux fois la même de suite */
				p = (p + 1) % len;
		} else
			p = (s->pos + 1) % len;
		s->pos = p;
		v = s->held[p % s->n] + 12 * (p / s->n);
		if (v > 127)
			v = s->held[p % s->n];
	} else {                                      /* montant, descendant, aller-retour : d'après la dernière note */
		up = mode == M_UPDN ? s->dir > 0 : mode == M_UP;
		v = beyond(s, octs, s->last, up);
		if (v < 0 && mode == M_UPDN) {            /* au bout : demi-tour, sans rejouer la note du bout */
			s->dir = -s->dir;
			up = !up;
			v = beyond(s, octs, s->last, up);
		}
		if (v < 0 && mode != M_UPDN)              /* au bout : on repart de l'autre bout */
			v = beyond(s, octs, up ? -1 : 128, up);
		if (v < 0)
			v = s->last;
	}
	s->last = v;
	I32(dst, EV_NOTE) = v;
}

/* ---------------------------------------------------------------------------------------------------------------
 * Menu FUNC + RETRIG : chaque ligne a quatre std::function (libellé, appui, affichage, changement). Toutes utilisent le
 * gestionnaire 0x4002cf00 de l'OS (fermeture de 4 o, copiée telle quelle), qui garde ici : le libellé, le menu (pour
 * l'appui d'origine 0x4002ccd0), ou le numéro de la ligne (0 : Arp, 1 : Oct).
 */
typedef struct {
	void *st0, *st1;                              /* std::function : stockage, gestionnaire, appel */
	u32 mgr;
	void *inv;
} fn_t;

#define NEW(n)       ((void *(*)(u32))0x400802e0)(n)
#define TRACK_OBJ()  ((void *(*)(void *))0x4000f23e)(((void *(*)(void))0x400cf866)())

extern char item_label[];                         /* arp_hooks.S */
static const char *const MODE_NAME[M_COUNT] = { "UP", "DOWN", "UPDN", "RAND", "PLAY", "OFF" };

/* Données de la piste du pattern sélectionné, comme les réglages Rte et Len (0x4001611a) */
static u8 *ui_track(void **objp)
{
	void *obj = TRACK_OBJ();

	*objp = obj;
	return obj ? ((u8 *(*)(void *))(*(void ***)obj)[10])(obj) : 0;
}

/* L'affichage de la valeur, comme 0x4002d768 */
void item_draw(u32 **functor, u32 a, u32 canvas, u8 *item, u32 b)
{
	void *obj;
	u8 *d = ui_track(&obj);
	int c = d ? d[512] : 0;
	u32 buf[2];

	(void)a;
	((void (*)(u32 *, u32))0x40072260)(buf, 0x40140ab0);
	if (**functor)
		((void (*)(u32, u32 *, u8 *, u32, u32, u32, int))0x40071a04)(canvas, buf, item + 24, b, 4, 0x40126f6e,
									  ((c >> 3) & 3) + 1);
	else
		((void (*)(u32, u32 *, u8 *, u32, u32, u32, const char *))0x40071a04)(canvas, buf, item + 24, b, 4,
										      0x40124b58,
										      MODE_NAME[mode_of(c)]);
	((void (*)(u32 *))0x40072080)(buf);
}

/* Le changement de valeur, comme 0x4002d4f4 ; puis « réglage de piste modifié », comme 0x4001614a */
void item_change(u32 **functor, u32 a, s32 delta)
{
	void *obj;
	u8 *d = ui_track(&obj);
	int c, v, shift = **functor ? 3 : 0, max = **functor ? 3 : M_OFF;
	u32 tag = 0x400ff5ac;

	(void)a;
	if (!d)
		return;
	c = d[512];
	v = (shift ? (c >> 3) & 3 : mode_of(c)) + delta;
	if (v < 0)
		v = 0;
	if (v > max)
		v = max;
	d[512] = (c & ~(7 << shift)) | (v << shift);
	((void (*)(void *, u32 *))(*(void ***)obj)[4])(obj, &tag);
}

/* Fin du constructeur de RetrigPadsMenuView (0x4002d138) : les deux lignes, construites comme Len, ajoutées au menu */
void arp_menu_add(void *view)
{
	static const char *const LABEL[2] = { "Arp", "Oct" };
	static void *const INV[4] = { item_label, (void *)0x4002ccd0, item_draw, item_change };
	u32 k, i;

	for (k = 0; k < 2; k++) {
		fn_t f[4];
		void *item;

		for (i = 0; i < 4; i++) {
			u32 *p = NEW(4);

			*p = i == 0 ? (u32)LABEL[k] : i == 1 ? (u32)view : k;
			f[i].st0 = p;
			f[i].st1 = 0;
			f[i].mgr = 0x4002cf00;
			f[i].inv = INV[i];
		}
		item = NEW(0x54);
		((void (*)(void *, fn_t *, fn_t *, fn_t *, fn_t *, s32, s32))0x400734b0)(item, &f[0], &f[1], &f[2],
											 &f[3], -1, 8);
		((void (*)(void *, void *))0x40072ce6)(view, item);
		for (i = 0; i < 4; i++)
			((void (*)(fn_t *))0x400cf044)(&f[i]);
	}
}
