/*
 * Passerelle Model:Cycles -> moteur audio du Syntakt (notes/17).
 *
 * Le vrai moteur SD VINTAGE du Syntakt (fonctions update/render de son processeur audio, et tout ce
 * qu'elles appellent) est extrait AU BUILD du Syntakt_OS1.41.syx de l'utilisateur, relocalise et
 * charge en SDRAM a 0x46000000 (tools/gen_sdvintage_exact.py, tools/build.py --syntakt). Aucun octet
 * Elektron n'est dans ce depot : ce fichier est notre seul code.
 *
 * Disposition en memoire (au-dessus du BSS de l'OS Cycles, qui finit a 0x423380b0) :
 *   0x46000000  copie du programme audio du Syntakt (0x40000400..0x4004f6e0), decalage ST_DELTA
 *   0x46050000  replique de sa SRAM (0x80000000..0x8000ffff) : voix de 1 800 o, tables, tampons
 *   0x46060000  fenetre de son BSS (0x4404f000..0x4404ffff) : graine aleatoire 0x4404f954
 *   0x46061000  cette passerelle, puis ses donnees
 *
 * La passerelle reproduit pour chaque voix la sequence de la boucle des voix du Syntakt
 * (0x40004324 : changement de machine -> remise a zero, GATE -> voix+0x3ec, 0x4000255e, update,
 * render, +0x38 <- +0x34) et traduit les parametres du Cycles dans la disposition du Syntakt
 * (emplacements 18..26 a p + 2*emplacement). Les potards ont le sens de ceux du Syntakt :
 * PITCH=TUNE, COLOR=INHM, SHAPE=FCMP, SWEEP=SWEP, CONTOUR=MENV, PUNCH=PNCH, GATE=GATE, DECAY=DEC.
 * FINE s'ajoute a la note (sans effet a 64). OVER n'a pas de potard : 0, comme le defaut du Syntakt.
 */
typedef short s16;
typedef int s32;
typedef unsigned int u32;

#define ST_DELTA    0x05fffc00                       /* Syntakt 0x40000400 -> 0x46000000 */
#define ST(a)       ((a) + ST_DELTA)
#define ST_SRAM     0x46050000
#define SRAM(a)     ((a) - 0x80000000 + ST_SRAM)
#define ST_VSTRIDE  1800
#define ENGINE      6                                /* SD VINTAGE dans les tables du Syntakt */
#define ST_UPDATE   ((void (*)(s32, char *, const char *))ST(0x40008074))
#define ST_RENDER   ((void (*)(s32 *, char *))ST(0x4000847a))
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

void bridge_update(s32 pmod, char *v, const char *p)
{
	int i = voice_index(v);
	char *sh, *pp = params[i];
	s16 *ps = (s16 *)pp;

	if (!ready)
		st_init();
	if (V32(v, MARK_OFF) != MARK) {                  /* machine (re)choisie sur le Cycles */
		V32(v, MARK_OFF) = MARK;
		need_reset[i] = 1;
	}
	sh = st_voice(i);
	V32(sh, 0x34) = V32(v, 0x34);
	V32(sh, 0x38) = V32(v, 0x38);
	V32(sh, 0x3c) = V32(v, 0x3c);
	if (V32(sh, 0x38) && need_reset[i]) {           /* comme la boucle du Syntakt au changement de machine */
		ST_RESET(sh);
		V32(sh, 0x38) = 1;
		V32(sh, 0) = V32(sh, 4) = ENGINE;
		need_reset[i] = 0;
	}
	if (need_reset[i])                               /* jamais declenchee depuis le choix de la machine */
		return;

	pp[0x22] = ENGINE;                               /* emplacement 17 : type de machine (octet fort) */
	ps[18] = P16(0x14);                              /* TUNE  <- PITCH   */
	ps[19] = P16(0x16);                              /* INHM  <- COLOR   */
	ps[20] = P16(0x18);                              /* FCMP  <- SHAPE   */
	ps[21] = P16(0x1a);                              /* SWEP  <- SWEEP   */
	ps[22] = P16(0x1c);                              /* MENV  <- CONTOUR */
	ps[23] = P16(0x1e);                              /* PNCH  <- PUNCH   */
	ps[24] = P16(0x20);                              /* GATE  <- GATE    */
	ps[25] = P16(0x24);                              /* DEC   <- DECAY   */
	ps[26] = 0;                                      /* OVER             */
	V32(sh, 0x3ec) = ps[24];                         /* la boucle du Syntakt recopie l'emplacement 24 */
	ST_PREP(sh);
	ST_UPDATE(pmod + (((s32)P16(0x22) - 0x4000) << 3), sh, pp);
}

void bridge_render(s32 *out, char *v)
{
	int i = voice_index(v), k;
	char *sh = st_voice(i);

	if (need_reset[i]) {
		for (k = 0; k < 32; k++)
			out[k] = 0;
		return;
	}
	ST_RENDER(out, sh);
	V32(sh, 0x38) = V32(sh, 0x34);
}
