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
 *   0x43000000  les fonctions (copie de 0x40002544.., meme disposition relative), puis leurs tables
 *   0x43020000  replique de sa SRAM (0x80000000..0x8000ffff) : voix de 1 800 o, tables, tampons
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

#define ST(a)       ((a) - 0x40002544 + 0x43000000)     /* code du Syntakt -> copie */
#define ST_SRAM     0x43020000
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
#define ST_RESET    ((void (*)(char *))ST(0x40003ee0))
#define ST_PREP     ((void (*)(char *))ST(0x4000255e))
#define ST_VINIT    ((void (*)(void))ST(0x40002544))

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

static char *st_voice(int i)
{
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
