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
 * bits 0-2 = sens, bits 3-4 = octaves - 1. 0 = montant, 1 octave. L'interface les lit sur l'objet de la piste, celui
 * des réglages Rte et Len : à chaque note jouée (arp_rate, à la place de la lecture de Rte, 0x4001a1c4 et
 * 0x4001d25e) et à chaque changement dans le menu. Le côté audio les reçoit dans ui_cfg (le pattern qu'il joue est une
 * autre copie, essai du 03/10/2026 sur la machine).
 * Live rec (notes/32 §11) : l'OS enregistre une touche avec retrig comme UN pas avec retrig (sa note, répétée) ; les
 * notes d'un accord tombent sur le même pas et la dernière reste. Sur une piste dont l'arpège n'est pas OFF, l'interface
 * ne reçoit donc plus ces touches (arp_ui_post) : l'arpège lui envoie les notes qu'il joue, une à une, comme des
 * touches (rec), et le live rec de l'OS les enregistre avec leur durée. Une suite d'une seule note (une note tenue,
 * 1 octave) reste enregistrée comme d'origine : un pas avec retrig.
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
	u8 rnote, rmode;                              /* live rec : note envoyée à l'interface ; 0 aucune, 1 avec retrig,
						         2 sans */
	u32 t0;                                       /* heure de son envoi (0x8000184c) */
};
static struct trk st[6];
static u32 seed = 0x2545f491;
static volatile u8 ui_cfg[6];                     /* octet +512 de chaque piste, tel que l'interface l'a lu */
static u8 *ring;                                  /* live rec : 8 messages de 32 o pour l'interface (alloués par
						     arp_rate, côté interface) */
static u8 ring_i;

#define NEW(n)       ((void *(*)(u32))0x400802e0)(n)

/* L'octet +512 des données de la piste, par l'objet de la piste (vtable[10], comme 0x40016086 pour Rte) */
static u8 *track_data(void *obj)
{
	return obj ? ((u8 *(*)(void *))(*(void ***)obj)[10])(obj) : 0;
}

/* À la place de jsr 0x40016086 (Rte de la piste) quand une note est jouée : le même résultat (l'octet +514 des
 * données, 0 sans données), et le réglage de l'arpège de cette piste pour le côté audio (arp_hooks.S passe le numéro
 * de piste, d3 ou d2 selon l'endroit). */
u32 arp_rate(void *obj, u32 track)
{
	u8 *d = track_data(obj);

	if (!ring)                                    /* côté interface : new est permis ici, pas sous l'interruption */
		ring = NEW(8 * 32);
	if (!d)
		return 0;
	if (track < 6)
		ui_cfg[track] = d[512];
	return d[514];
}

static int mode_of(int c)
{
	c &= 7;
	return c < M_COUNT ? c : M_UP;
}

/* Live rec en cours, comme 0x4006ba76 : séquenceur en lecture (0x4005481a) et octet +359 de l'état de l'interface
 * (0x400cf9a8, déjà construit : son pointeur en 0x40fe4218). */
static int live_rec(void)
{
	u8 *ui = *(u8 **)0x40fe4218;

	return ui && ui[359] && (*(s32 *)0x40a78874 | *(s32 *)0x40a7883c) == 1;
}

/* Un message de note pour l'interface, comme ceux de 0x4008171e (kind 0, val = vitesse du retrig ou -1) et de
 * 0x4008145e (kind 1, fin de note, val = durée en moitiés de 0x8000184c) : la file de l'interface le reçoit comme une
 * touche, et le live rec de l'OS l'enregistre (0x40012158, 0x40011c84). Pas et micro-décalage par 0x40056178, comme
 * eux. Sous l'interruption audio : nos propres 8 tampons (ring), la file 0x40001fba masque les interruptions. */
static void post(u32 t, u32 kind, u32 note, s32 val, u32 vel)
{
	u8 *m = ring, pos[4];
	u32 i;

	if (!m)
		return;
	m += 32 * (ring_i++ & 7);
	for (i = 0; i < 32; i += 4)
		I32(m, i) = 0;
	((void (*)(u32, s32, u8 *))0x40056178)(*(u32 *)0x8000184c, t, pos);
	m[0] = 12;
	m[7] = kind;
	m[8] = t;
	m[15] = 0x40;                                 /* source : les touches (0x400813e2) */
	m[16] = note;
	if (kind) {
		I32(m, 20) = val;
		m[24] = 1;
	} else {
		m[17] = vel;
		m[18] = 1;
		m[19] = 0xff;
		m[20] = val;
	}
	*(short *)(m + 28) = (s8)pos[0];
	*(short *)(m + 30) = (s8)pos[1];
	((void (*)(u32, u8 *))0x40001fba)(*(u32 *)0x40149250, m);
}

/* Live rec : l'arpège joue la note v sur la piste t (-1 : il s'arrête) ; len = notes de sa suite (tenues x octaves).
 * La note envoyée avant se termine (sa durée) ; une suite d'une seule note est envoyée une fois, avec la vitesse du
 * retrig (ev +56) : un pas avec retrig, comme d'origine. */
static void rec(u32 t, int v, int len, u8 *ev)
{
	struct trk *s = &st[t];
	u32 now = *(u32 *)0x8000184c;

	if (s->rmode) {
		if (s->rmode == 1 && v == s->rnote)
			return;
		post(t, 1, s->rnote, (now >> 1) - (s->t0 >> 1), 0);
		s->rmode = 0;
	}
	if (v < 0 || !live_rec())
		return;
	s->rmode = len == 1 ? 1 : 2;
	s->rnote = v;
	s->t0 = now;
	post(t, 0, v, len == 1 ? I32(ev, 56) : -1, ev[22]);
}

void arp_filter(u8 *ev)
{
	u32 t = I32(ev, EV_TRACK), n, i;
	int c;
	struct trk *s;

	if (I32(ev, EV_TYPE) != 0 || I32(ev, EV_SRC) != 2 || t > 5)
		return;
	s = &st[t];
	if (!RTG(t, 4) || !RTG(t, 20))                /* plus de retrig sur la piste : liste périmée */
		s->n = 0;
	if (!s->n)
		rec(t, -1, 0, ev);                        /* plus d'arpège : sa dernière note enregistrée se termine */
	c = ui_cfg[t];
	n = I32(ev, EV_NOTE);
	if (I32(ev, EV_ONOFF) == 1) {
		if ((I32(ev, EV_FLAGS) & (F_RETRIG | F_REPEAT)) != F_RETRIG || n > 127)
			return;
		if (mode_of(c) == M_OFF) {                /* sens OFF : le retrig d'origine */
			s->n = 0;
			return;
		}
		if (!s->n) {                              /* 1re note : le retrig d'origine démarre avec elle */
			s->last = n;
			s->dir = 1;
			s->pos = 0;
			s->held[0] = n;
			s->n = 1;
			rec(t, n, ((c >> 3) & 3) + 1, ev);
			return;
		}
		I32(ev, EV_SRC) = -1;                     /* l'arpège tourne : la note y entre, le rythme continue */
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
			else {
				I32(ev, EV_NOTE) = CUR_NOTE(t);   /* la dernière : fin de la note en cours, l'OS arrête tout */
				rec(t, -1, 0, ev);
			}
			return;
		}
}

/* À la place de l'envoi à l'interface du message d'une note jouée (0x40081908, dans 0x4008171e ; arp_hooks.S). En
 * live rec, une note avec retrig (vitesse en +20) sur une piste dont l'arpège n'est pas OFF n'est pas envoyée :
 * l'arpège enregistre lui-même les notes qu'il joue (rec). held : 5e argument de 0x4008171e, pas tenus (la note va à
 * ces pas et n'est pas jouée) : envoyée telle quelle. */
void arp_ui_post(u8 *m, u32 held)
{
	u32 t = m[8];

	if (held || (s8)m[20] < 0 || t > 5 || mode_of(ui_cfg[t]) == M_OFF || !live_rec())
		((void (*)(u8 *))0x40080bf6)(m);
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
	c = ui_cfg[t];
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
	rec(t, v, len, dst);
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

#define TRACK_OBJ()  ((void *(*)(void *))0x4000f23e)(((void *(*)(void))0x400cf866)())

extern char item_label[];                         /* arp_hooks.S */
static const char *const MODE_NAME[M_COUNT] = { "UP", "DOWN", "UPDN", "RAND", "PLAY", "OFF" };

/* Données de la piste du pattern sélectionné, comme les réglages Rte et Len (0x4001611a) */
static u8 *ui_track(void **objp)
{
	void *obj = TRACK_OBJ();

	*objp = obj;
	return track_data(obj);
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
	d[512] = c = (c & ~(7 << shift)) | (v << shift);
	((void (*)(void *, u32 *))(*(void ***)obj)[4])(obj, &tag);
	v = ((u32 (*)(void *))0x40012412)(((void *(*)(void *))0x4000eb90)(((void *(*)(void))0x400cf866)()));
	if ((u32)v < 6)                               /* la piste sélectionnée, comme 0x4002d48c pour Rte : entendu */
		ui_cfg[v] = c;                            /* tout de suite, même pendant que les notes sont tenues */
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
