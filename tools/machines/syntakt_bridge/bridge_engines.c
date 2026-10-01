/*
 * Passerelle Model:Cycles -> moteurs audio du Syntakt, N moteurs (notes/20) : bridge_multi.c (notes/19)
 * generalise. Pour chaque moteur du Syntakt E (6..10) compile, -DUPD_E=adresse -DRND_E=adresse (adresses du
 * Syntakt, section 7) donnent ses update/render ; les entrees bridge_update_E / bridge_render_E sont
 * appelees par la boucle des voix du Cycles pour la machine ajoutee correspondante.
 *
 * Les vrais moteurs du Syntakt (fonctions update/render de son processeur audio, et tout ce qu'elles
 * appellent) sont extraits AU BUILD du Syntakt_OS1.41.syx de l'utilisateur, relocalises et charges en
 * SDRAM a 0x43000000 (tools/gen_syntakt_engines.py, tools/build.py --syntakt). Aucun octet Elektron n'est
 * dans ce depot : ce fichier est notre seul code.
 *
 * Disposition en memoire (layout() de tools/gen_syntakt_engines.py) :
 *   0x43000000  zone de transit : les fonctions atteintes du Syntakt (blocs tasses) et ses tables les plus lues,
 *               recopiees au demarrage (stub.S) en SRAM interne (0x80001c5c, a la place des tables d'ondes de
 *               CHORD, qui passent dans la charge utile, notes/28), ou elles s'executent ; puis les autres tables
 *   0x43020000  replique de sa SRAM (0x80000000..0x8000ffff) : voix de 1 800 o, tables, tampons ; sauf
 *               ses tampons de travail (0x80008c60..0x80009ea8), dans la zone de travail des machines
 *               d'origine en SRAM interne (0x8000beb8..0x8000c8e8), et sa table de sinus, identique a celle
 *               du Cycles (0x8000eee4) : SRAM_MAP de gen_syntakt_engines.py (notes/26)
 *   0x43030000  fenetre de son BSS (0x4404f000..0x4404ffff) : graine aleatoire 0x4404f954
 *   0x43031000  cette passerelle, puis ses donnees (0x43032000)
 *
 * La passerelle reproduit pour chaque voix la sequence de la boucle des voix du Syntakt
 * (0x40004324 : changement de machine -> remise a zero, GATE -> voix+0x3ec, 0x4000255e, update,
 * render, +0x38 <- +0x34) et traduit les parametres du Cycles dans la disposition du Syntakt
 * (emplacements 18..26 a p + 2*emplacement) : PITCH=TUNE, COLOR..CONTOUR = p1..p4 du moteur,
 * PUNCH=emplacement 23 (PNCH), GATE=GATE, DECAY=DEC. FINE s'ajoute a la note (sans effet a 64).
 * OVER n'a pas de potard : 0, comme le defaut du Syntakt.
 */
typedef short s16;
typedef int s32;
typedef unsigned int u32;

/* UPD_E, RND_E, ST_*_AT : adresses d'EXECUTION des fonctions du Syntakt (en SRAM, donnees par le generateur) */
#define ST(a)       (a)
#ifndef ST_SRAM                                      /* replique de sa SRAM (gen_syntakt_engines.py, LAYOUT) */
#define ST_SRAM     0x43020000
#endif
#define SRAM(a)     ((a) - 0x80000000 + ST_SRAM)
#define ST_VSTRIDE  1800
typedef void (*update_fn)(s32, char *, const char *);
typedef void (*render_fn)(s32 *, char *);
/* update/render du Syntakt par moteur : 6 = SD VINTAGE, 7 = CP VINTAGE (tables 0x40014920 / 0x400148f0) */
static update_fn st_update(int e)
{
	switch (e) {
#ifdef UPD_6
	case 6: return (update_fn)ST(UPD_6);
#endif
#ifdef UPD_7
	case 7: return (update_fn)ST(UPD_7);
#endif
#ifdef UPD_8
	case 8: return (update_fn)ST(UPD_8);
#endif
#ifdef UPD_9
	case 9: return (update_fn)ST(UPD_9);
#endif
#ifdef UPD_10
	case 10: return (update_fn)ST(UPD_10);
#endif
	}
	return 0;
}

static render_fn st_render(int e)
{
	switch (e) {
#ifdef RND_6
	case 6: return (render_fn)ST(RND_6);
#endif
#ifdef RND_7
	case 7: return (render_fn)ST(RND_7);
#endif
#ifdef RND_8
	case 8: return (render_fn)ST(RND_8);
#endif
#ifdef RND_9
	case 9: return (render_fn)ST(RND_9);
#endif
#ifdef RND_10
	case 10: return (render_fn)ST(RND_10);
#endif
	}
	return 0;
}
#define ST_RESET    ((void (*)(char *))ST_RESET_AT)
#define ST_PREP     ((void (*)(char *))ST_PREP_AT)
#define ST_VINIT    ((void (*)(void))ST_VINIT_AT)

#define CYC_VOICE0  0x42308828
#define CYC_VSTRIDE 0x31c
#define MARK_OFF    0x2c                             /* efface par la remise a zero du Cycles (0x400a7ab8) */
#define MARK        0x53445631                       /* 'SDV1' */

#define V32(b, o)   (*(s32 *)((b) + (o)))
#define P16(o)      (*(const s16 *)(p + (o)))

static char params[6][0x40];                         /* p' du Syntakt = piste + 0x1c ; emplacement s a p' + 2 s */
static unsigned char need_reset[6];
static unsigned char engine_of[6];                   /* moteur du Syntakt de la voix */
static int ready;

/* etat de la voix i du Syntakt : en SRAM interne pour les 6 voix des pistes (ST_VOICE_i, recopiees au demarrage
 * avec le contenu initial de sa SRAM, notes/29) ; ses voix 6 et 7, initialisees comme sur le Syntakt mais jamais
 * jouees, restent dans la replique */
static char *st_voice(int i)
{
	switch (i) {
	case 0: return (char *)ST_VOICE_0;
	case 1: return (char *)ST_VOICE_1;
	case 2: return (char *)ST_VOICE_2;
	case 3: return (char *)ST_VOICE_3;
	case 4: return (char *)ST_VOICE_4;
	case 5: return (char *)ST_VOICE_5;
	}
	return (char *)SRAM(0x80000000) + ST_VSTRIDE * i;
}

static int voice_index(const char *v)
{
	return ((u32)v - CYC_VOICE0) / CYC_VSTRIDE;
}

/* ce que fait l'init du processeur audio du Syntakt (0x40000fd6..0x40001014), pour ses 8 voix */
static void st_init(void)
{
	int i;
	/* appelee au premier declenchement seulement (voir bridge_update) */
	for (i = 0; i < 8; i++) {
		char *sh = st_voice(i);
		ST_VINIT();
		V32(sh, 0x56c) = SRAM(0x80008a60) + 0x30 * i;
		ST_RESET(sh);
	}
	for (i = 0; i < 6; i++)
		need_reset[i] = 1;
	ready = 1;
}

static void update(int engine, s32 pmod, char *v, const char *p)
{
	int i = voice_index(v);
	char *sh, *pp = params[i];
	s16 *ps = (s16 *)pp;

	if (V32(v, MARK_OFF) != MARK || engine_of[i] != engine) {   /* machine (re)choisie sur le Cycles */
		V32(v, MARK_OFF) = MARK;
		engine_of[i] = engine;
		need_reset[i] = 1;
	}
	/* Securite : aucun code du Syntakt ne tourne tant qu'une piste SNARE n'a pas ete declenchee.
	 * Au demarrage (kit par defaut avec une piste SNARE), seule cette fonction s'execute : si le moteur
	 * posait probleme, le Cycles demarre quand meme et CONFIG > UPGRADE reste accessible. */
	if (!ready) {
		if (!V32(v, 0x38))
			return;
		st_init();
	}
	sh = st_voice(i);
	V32(sh, 0x34) = V32(v, 0x34);
	V32(sh, 0x38) = V32(v, 0x38);
	V32(sh, 0x3c) = V32(v, 0x3c);
	if (V32(sh, 0x38) && need_reset[i]) {           /* comme la boucle du Syntakt au changement de machine */
		ST_RESET(sh);
		V32(sh, 0x38) = 1;
		V32(sh, 0) = V32(sh, 4) = engine;
		need_reset[i] = 0;
	}
	if (need_reset[i])                               /* jamais declenchee depuis le choix de la machine */
		return;

	pp[0x22] = engine;                               /* emplacement 17 : type de machine (octet fort) */
	ps[18] = P16(0x14);                              /* TUNE  <- PITCH   */
	ps[19] = P16(0x16);                              /* INHM  <- COLOR   */
	ps[20] = P16(0x18);                              /* FCMP  <- SHAPE   */
	ps[21] = P16(0x1a);                              /* SWEP  <- SWEEP   */
	ps[22] = P16(0x1c);                              /* MENV  <- CONTOUR */
	ps[23] = P16(0x1e);                              /* PNCH  <- PUNCH   */
	ps[24] = P16(0x20);                              /* GATE  <- GATE    */
	ps[25] = P16(0x24);                              /* DEC   <- DECAY   */
	ps[26] = 0;                                      /* OVER             */
#ifdef UPD_9
	if (engine == 9) {                               /* SY BITS */
		if (ps[19] < 0x2800)                     /* DET va de 40 a 88 (valeur d'un autre moteur : bornee) */
			ps[19] = 0x2800;
		if (ps[19] > 0x5800)
			ps[19] = 0x5800;
		ps[23] = ps[23] ? PUNCH_ON_9 << 8 : 0;   /* emplacement 23 = Bit Redux (0..127), sans potard : PUNCH */
	}
#endif
#ifdef UPD_10
	if (engine == 10)                                /* SY SWARM : emplacement 23 = Fundamental Sub (0..2) */
		ps[23] = (ps[23] ? PUNCH_ON_10 : PUNCH_OFF_10) << 8;
#endif
	V32(sh, 0x3ec) = ps[24];                         /* la boucle du Syntakt recopie l'emplacement 24 */
	ST_PREP(sh);
	st_update(engine)(pmod + (((s32)P16(0x22) - 0x4000) << 3), sh, pp);
}

static void render(int engine, s32 *out, char *v)
{
	int i = voice_index(v), k;
	char *sh = st_voice(i);

	if (!ready || need_reset[i] || engine_of[i] != engine) {
		for (k = 0; k < 32; k++)
			out[k] = 0;
		return;
	}
	st_render(engine)(out, sh);
	V32(sh, 0x38) = V32(sh, 0x34);
}

/* Regulateur de charge (notes/25). Le minuteur DMA 0 du Cycles compte a 135,168 MHz (l'OS divise ses ticks par
 * 135 168 pour des millisecondes) : un bloc de 32 echantillons dure 90 112 ticks. La sonde de la fonction audio
 * (0x4005979e, appelee par l'interruption, detours) appelle audio_end() a chaque bloc ; le detour de la boucle
 * des voix appelle voice_gate() avant update/render de chaque piste et voice_after() apres.
 *  - Une voix restee sous le seuil pendant `NEED` blocs, sans trig, n'est plus calculee (sortie a zero) :
 *    -108 dB et 64 blocs d'ordinaire ; -66 dB et 16 blocs quand la charge moyenne depasse PRESSURE.
 *  - Le cout de chaque voix (update + render) est mesure a chaque bloc ou elle est calculee.
 *  - Surcharge : charge soutenue (moyenne lente, environ 170 ms) au-dessus de STEAL, qui priverait l'interface de
 *    temps (on revient a TARGET) ; ou un bloc au-dessus de PEAK, qui pourrait faire craquer le son (on revient a
 *    PEAK - GOV_MARGIN). On eteint par un fondu autant de voix calculees qu'il faut, des plus faibles aux
 *    plus fortes (depuis notes/30, les voix du Syntakt ne comptent plus pour moitie : elles coutent autant qu'une
 *    voix d'origine). Fondu de 8 blocs (5 ms) et
 *    notes d'au moins 16 blocs ; en surcharge severe (un bloc au-dessus de SEVERE) : 2 blocs et 4 blocs.
 *    Au plus 2 voix par bloc : la charge est remesuree au bloc suivant (les voix en cours de fondu comptent).
 *    Une voix eteinte n'est plus calculee jusqu'a son prochain trig.
 * Charges en 1/256 de la duree d'un bloc. Toutes les variables sont en BSS (a zero au demarrage) : la charge
 * utile ne recopie pas de donnees initialisees. */
#define TIMER (*(volatile u32 *)0xfc07000c)
#define NT 6
/* seuils en % (GOV_* : gen_syntakt_engines.py, notes/30) */
#define PCT(x) ((x) * 256 / 100)
#define PRESSURE PCT(72)
#define STEAL PCT(GOV_STEAL)       /* charge soutenue (gov_slow) : l'interface manquerait de temps */
#define TARGET PCT(GOV_TARGET)
#define PEAK PCT(GOV_PEAK)         /* un bloc trop long : le son pourrait craquer */
#define PEAK_TO PCT(GOV_PEAK - GOV_MARGIN)
#define SEVERE PCT(GOV_SEVERE)
u32 gov_ret_audio, gov_t0_audio, gov_load, gov_avg, gov_period;    /* dernier bloc, moyenne glissante (1/8) */
u32 gov_slow;                      /* moyenne glissante lente (1/2^GOV_SLOW, environ 170 ms) */
static u32 last_t0, vt0;
u32 gov_pressure;
unsigned char gov_quiet[NT], gov_fading[NT], gov_flen[NT], gov_stolen[NT], gov_st[NT];
#ifdef LOAD_METER
unsigned char gov_eng[NT];          /* moteur de chaque piste, pour le compteur */
#endif
unsigned short gov_age[NT];
s32 gov_peak[NT];
u32 gov_cost[NT];                 /* cout mesure d'update + render, en ticks (moyenne glissante 1/4) */
#define THR ((u32)(gov_pressure ? 1 << 20 : IDLE_THR))
#define NEED (gov_pressure ? 16 : IDLE_BLOCKS)

#ifdef TG_FIRST
/* Avec Model-TG (notes/31) : son Sampler (entree 6) et ses machines d'origine passent par son dispatch, qui a sa
 * propre logique des voix muettes ; l'arret des voix muettes ne vaut donc que pour nos moteurs (entree >= TG_FIRST).
 * Le regulateur peut eteindre toute piste, sauf le Sampler et la piste qu'il enregistre (reechantillonnage, rs_src)
 * ou dont il edite les tranches (sle_trk) : leur capture et leur lecture doivent garder le temps. Toutes les pistes
 * finissent en 0x400a7e24 (tg_after) : voice_done n'y mesure que celles que voice_gate a laisse calculer. */
#define U32AT(a) (*(volatile u32 *)(a))
unsigned char gov_free[NT];
u32 gov_ran;

static int tg_keep(int t)
{
	return (U32AT(TG_RS_STATE) && U32AT(TG_RS_SRC) == (u32)t) || (U32AT(TG_SLE_RUN) && U32AT(TG_SLE_TRK) == (u32)t);
}

int voice_gate(int t, int trig, int engine)
{
	gov_st[t] = engine >= TG_FIRST;
#ifdef LOAD_METER
	gov_eng[t] = engine;
#endif
	gov_free[t] = engine == 6 || tg_keep(t);
	if (gov_free[t])
		gov_fading[t] = gov_stolen[t] = 0;
	if (trig) {
		gov_quiet[t] = gov_fading[t] = gov_stolen[t] = 0;
		gov_age[t] = 0;
	} else {
		if (gov_age[t] < 0xffff)
			gov_age[t]++;
		if (!gov_free[t] && (gov_stolen[t] || (engine >= TG_FIRST && gov_quiet[t] >= NEED)))
			return 1;
	}
	gov_ran = 1;
	vt0 = TIMER;
	return 0;
}
#else
/* avant update/render d'une piste : 1 = ne pas la calculer (sortie a zero) */
int voice_gate(int t, int trig, int engine)
{
	gov_st[t] = engine >= 6;
#ifdef LOAD_METER
	gov_eng[t] = engine;
#endif
	if (trig) {
		gov_quiet[t] = gov_fading[t] = gov_stolen[t] = 0;
		gov_age[t] = 0;
	} else {
		if (gov_age[t] < 0xffff)
			gov_age[t]++;
		if (gov_stolen[t] || gov_quiet[t] >= NEED)
			return 1;
	}
	vt0 = TIMER;
	return 0;
}
#endif

/* apres render : cout, fondu eventuel, crete, compteur de blocs faibles */
void voice_after(int t, s32 *out)
{
	s32 pk = 0, x;
	int k;

	gov_cost[t] += ((s32)(TIMER - vt0) - (s32)gov_cost[t]) >> 2;
	if (gov_fading[t]) {
		u32 n = 32 * gov_flen[t];                        /* echantillons du fondu : 64 ou 256 */
		u32 p = (gov_flen[t] - gov_fading[t]) * 32;      /* position dans le fondu */
		u32 step = 65536 / n;
		for (k = 0; k < 32; k++, p++)
			out[k] = (out[k] >> 16) * (s32)((n - p) * step);
		if (--gov_fading[t] == 0)
			gov_stolen[t] = 1;
	}
	for (k = 0; k < 32; k++) {
		x = out[k] < 0 ? -out[k] : out[k];
		if (x > pk)
			pk = x;
	}
	gov_peak[t] = pk;
	if ((u32)pk < THR) {
		if (gov_quiet[t] < 255)
			gov_quiet[t]++;
	} else
		gov_quiet[t] = 0;
}

#ifdef TG_FIRST
void voice_done(int t, s32 *out)
{
	if (gov_ran) {
		gov_ran = 0;
		voice_after(t, out);
	}
}
#endif

static void govern(void)
{
	int t, v, severe, n = 0;
	u32 excess, best, key;

	gov_pressure = gov_avg >= PRESSURE;
	excess = 0;                                              /* ticks a liberer */
	if (gov_slow >= STEAL)                                   /* charge soutenue : revenir a TARGET */
		excess = (gov_slow - TARGET) * (gov_period >> 8);
	if (gov_load >= PEAK && (gov_load - PEAK_TO) * (gov_period >> 8) > excess)
		excess = (gov_load - PEAK_TO) * (gov_period >> 8);   /* bloc trop long : revenir sous PEAK - GOV_MARGIN */
	if (!excess)
		return;
	severe = gov_load >= SEVERE;
	for (t = 0; t < NT; t++)
		if (gov_fading[t])                               /* deja en cours d'extinction */
			excess = excess > gov_cost[t] ? excess - gov_cost[t] : 0;
	while (excess && n++ < 2) {                              /* 2 voix par bloc au plus, puis on remesure */
		v = -1;
		best = 0xffffffff;
		for (t = 0; t < NT; t++) {
			if (gov_stolen[t] || gov_fading[t] || gov_quiet[t] >= NEED || gov_age[t] < (severe ? 4 : 16))
				continue;                        /* deja arretee, ou note trop recente */
#ifdef TG_FIRST
			if (gov_free[t])
				continue;
#endif
			key = (u32)gov_peak[t];
			if (key < best) {
				best = key;
				v = t;
			}
		}
		if (v < 0)
			break;
		gov_flen[v] = gov_fading[v] = severe ? 2 : 8;
		excess = excess > gov_cost[v] + 1 ? excess - gov_cost[v] - 1 : 0;
	}
}

#ifdef LOAD_METER
/* Compteur de charge (firmware de diagnostic, notes/23, notes/27, notes/29) : toutes les 750 blocs (0,5 s), le nom
 * de la machine m (METER_BUF + 8 m, METER_N machines) devient, en % de la duree d'un bloc :
 *  - « pic/moyenne » de la fonction audio (par defaut) ;
 *  - avec METER_VOICE, « moyenne/voix » : charge moyenne et cout mesure de la voix qui joue cette machine (la plus
 *    chere si plusieurs pistes) ; « -- » si aucune piste ne la joue. */
static u32 w_period, w_audio, w_n, w_max;

static char *put2(char *s, u32 v)
{
	if (v > 99)
		v = 99;
	if (v >= 10)
		*s++ = '0' + v / 10;
	*s++ = '0' + v % 10;
	return s;
}

static void meter(u32 dur, u32 period)
{
	w_period += period;
	w_audio += dur;
	if (dur * 100 / period > w_max)
		w_max = dur * 100 / period;
	if (++w_n >= 750) {
		u32 avg = w_audio / (w_period / 100);
		int m;
#ifdef METER_VOICE
		u32 per = w_period / w_n, c;
		int t, any;
#endif

		for (m = 0; m < METER_N; m++) {
#ifdef METER_VOICE
			char *s = put2((char *)METER_BUF + 8 * m, avg);
			*s++ = '/';
			for (t = any = 0, c = 0; t < NT; t++)
				if (gov_eng[t] == m) {
					any = 1;
					if (gov_cost[t] * 100 / per > c)
						c = gov_cost[t] * 100 / per;
				}
			if (any)
				s = put2(s, c);
			else {
				*s++ = '-';
				*s++ = '-';
			}
#else
			char *s = put2((char *)METER_BUF + 8 * m, w_max);
			*s++ = '/';
			s = put2(s, avg);
#endif
			*s = 0;
		}
		w_n = w_period = w_audio = w_max = 0;
	}
}
#endif

/* apres chaque bloc audio (sonde de 0x4005979e) */
void audio_end(void)
{
	u32 now = TIMER, t0 = gov_t0_audio, dur = now - t0, period = t0 - last_t0;

	last_t0 = t0;
	if (!period || period > 20 * 90112) {                   /* premier bloc, ou pause */
#ifdef LOAD_METER
		w_n = w_period = w_audio = w_max = 0;
#endif
		return;
	}
	gov_load = dur * 256 / period;
	gov_avg += ((s32)gov_load - (s32)gov_avg) >> 3;
	gov_slow += ((s32)gov_load - (s32)gov_slow) >> GOV_SLOW;
	gov_period = period;
#ifdef LOAD_METER
	meter(dur, period);
#endif
	govern();
}

#define ENTRIES(E) \
	void bridge_update_##E(s32 pmod, char *v, const char *p) { update(E, pmod, v, p); } \
	void bridge_render_##E(s32 *out, char *v) { render(E, out, v); }
#ifdef UPD_6
ENTRIES(6)
#endif
#ifdef UPD_7
ENTRIES(7)
#endif
#ifdef UPD_8
ENTRIES(8)
#endif
#ifdef UPD_9
ENTRIES(9)
#endif
#ifdef UPD_10
ENTRIES(10)
#endif
