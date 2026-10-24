/*
 * Firmware de mesure (notes/75) : ou passe le temps de l'interruption audio du Modded Cycles OS, sur la machine.
 * Trois ecrans de plus dans la page System de Model-TG (DATA vers la droite, apres ses deux ecrans) :
 *
 *   AUDIO : la part de chaque poste dans la duree d'un bloc (moyenne sur 0,5 s, en %) : sequenceur, USB, lissage,
 *           LFO, voix, apres les voix, Volume + Dist, sortie ; le total de l'interruption (moyenne et pire bloc) ;
 *           le temps libre de l'interface et le reste (autres interruptions, interface au travail).
 *   BENCH : des essais d'etalonnage, quand cet ecran est affiche : la frequence du processeur, les cycles par
 *           instruction de petits noyaux (calcul, produits de l'EMAC, memoire) dans le cache et en SRAM, une ligne
 *           de code droit (16 o) dans le cache et en SRAM, et ce que coute une ligne absente du cache (code,
 *           donnees).
 *   COLD  : quand cet ecran est affiche, un bloc sur deux commence cache d'instructions vide : ce que le cache
 *           garde d'un bloc a l'autre (total, voix, sortie, le reste), et les lectures sans cache et en SRAM.
 *
 * Les sondes (mesure_hooks.S) notent les durees dans m_site ; m_block_end (apres l'envoi a l'USB, le dernier
 * appel du bloc) les cumule. Variables : fenetre de RAM au-dessus du BSS de l'OS (gen_mesure.py, RAM), non remise a
 * zero au demarrage : m_fresh (dans l'image, 1 a chaque demarrage) declenche leur mise a zero au premier bloc.
 */
typedef unsigned int u32;
typedef int s32;
typedef unsigned short u16;
typedef unsigned char u8;

#define DTIM0 (*(volatile u32 *)0xfc07000c)
#define NSITE 12
enum { S_USBIN, S_FN, S_SMOOTH, S_VELMOD, S_LFO, S_VOICES, S_TGPOST, S_GAINS, S_DIST, S_MISC, S_OUT, S_USBOUT };

/* lus et ecrits par mesure_hooks.S */
struct site {
	u32 ret[NSITE], t0[NSITE], dur[NSITE];
};
struct site m_site;
u32 m_tisr, m_cold, m_idle_acc;
u32 m_fresh = 1;                                     /* dans l'image : 1 a chaque demarrage */

/* noyaux (mesure_hooks.S) */
u32 m_time(const void *code, void *data);
void m_icinv(void);
extern const u16 k_clk[], k_clk_end[], k_alu[], k_alu_end[], k_mac[], k_mac_end[], k_mem[], k_mem_end[], k_rd[];

#define WIN 750                                       /* blocs par fenetre : 0,5 s */
#define MAXPER (20 * 90112)                           /* au-dela (ou au 1er bloc), une pause : la fenetre repart */
#define SEEN 1600                                     /* blocs : un ecran redessine il y a moins (750 : Model-TG) */

/* postes de l'ecran AUDIO, dans l'ordre de l'ecran (deux colonnes) */
enum { A_SEQ, A_USB, A_SMOOTH, A_LFO, A_VOICES, A_POST, A_DIST, A_OUT, A_TOTAL, A_PEAK, A_IDLE, A_OTHER, NA };
/* essais : meilleur temps (le plus court) de la fenetre, en ticks */
enum { B_CLK, B_ALU, B_ALU_S, B_MAC, B_MAC_S, B_MEM, B_MEM_S, B_LINE, B_LINE_C, B_LINE_S, B_DW, B_DC, B_UNC, B_SRD,
       NB };
/* essai A/B (ecran COLD) : total, voix, sortie, pour les blocs normaux (0) et froids (1) */
enum { C_TOTAL, C_VOICES, C_OUT, NC };

#define SCRATCH 0x8000bec0                            /* SRAM : la zone de travail des voix (0x8000beb8..0x8000c8e8, */
#define SCRATCH_N 2064                                /* notes/26), ecrite avant d'etre lue a chaque bloc ; sauvee */
                                                      /* et rendue autour des essais */
struct state {
	u32 blocks, prev_isr;
	u32 n, per, idle0, sum[A_PEAK], peak;             /* la fenetre en cours */
	u32 shown[NA];                                    /* ecran AUDIO : dixiemes de % */
	u32 seen[4];                                      /* bloc du dernier dessin de chacun de nos ecrans */
	u32 step, best[NB], bshown[NB];                   /* essais */
	u32 cur_cold, cn[2], cper[2], csum[2][NC], cshown[2][NC + 1];
};
static struct state st;
static u32 save[SCRATCH_N / 4];
#define LINE_CODE 0x4233b000                          /* code droit genere : 128 lignes de 8 addq.l #1,d0, puis rts */
#define LINES 128
#define DBUF 0x4233b900                               /* 1 Ko lu par l'essai des donnees, puis 1 Ko d'ecriture */
#define UNCACHED(a) ((a) + 0x08000000)                /* la meme SDRAM, vue sans cache (0x48000000..) */

static __attribute__((noinline)) void copy(u32 *d, const u32 *s, u32 n)
{
	while (n--)
		*d++ = *s++;
}

static __attribute__((noinline)) void init(void)
{
	u32 *p = (u32 *)&st, i;
	u16 *code = (u16 *)UNCACHED(LINE_CODE);

	for (i = 0; i < sizeof(st) / 4; i++)
		p[i] = 0;
	for (i = 0; i < LINES * 8; i++)
		code[i] = 0x5280;                             /* addq.l #1,d0 */
	code[i] = 0x4e75;                                 /* rts */
	for (i = 0; i < NB; i++)
		st.best[i] = ~0u;
	m_cold = 0;
	m_icinv();
	m_fresh = 0;
}

static __attribute__((noinline)) u32 twice(const void *code, void *data)          /* le 2e passage : code et donnees dans les caches */
{
	m_time(code, data);
	return m_time(code, data);
}

/* Le code recopie en SRAM : le bootstrap y masque les acces au code (RAMBAR 0x80000235, notes/75 §1.2) ; ses
 * instructions passent donc par le cache d'instructions, qui peut tenir les lignes d'un essai precedent a la meme
 * adresse : on l'invalide avant de l'executer. */
static __attribute__((noinline)) u32 in_sram(const void *code, const void *end, void *data)
{
	u32 n = ((const u8 *)end - (const u8 *)code + 3) / 4, t;

	copy(save, (const u32 *)SCRATCH, n);
	copy((u32 *)SCRATCH, (const u32 *)code, n);
	m_icinv();
	t = twice((const void *)SCRATCH, data);
	copy((u32 *)SCRATCH, save, n);
	return t;
}

/* chasse les 64 lignes de DBUF du cache de donnees (8 Ko, 4 voies, 128 ensembles de 16 o) : 8 autres lignes du meme
 * ensemble chacune, lues dans le code de l'OS */
static __attribute__((noinline)) void evict(void)
{
	const volatile u32 *e = (const volatile u32 *)(0x40020000 + (DBUF & 2047));
	u32 i, j, x = 0;

	for (j = 1; j <= 8; j++)
		for (i = 0; i < 64; i++)
			x += e[(j * 2048 + 16 * i) / 4];
	(void)x;
}

/* les essais, un par bloc tant que l'ecran BENCH est affiche : comment (H_*), quel code, sur quelles donnees */
enum { H_TWICE, H_SRAM, H_COLD_I, H_LINE_SRAM, H_COLD_D, H_ONCE };
static const struct {
	u8 how;
	const void *code, *end;
	u32 data;
} BENCH[NB] = {
	{ H_TWICE, k_clk, k_clk_end, DBUF },
	{ H_TWICE, k_alu, k_alu_end, DBUF },
	{ H_SRAM, k_alu, k_alu_end, DBUF },
	{ H_TWICE, k_mac, k_mac_end, DBUF },
	{ H_SRAM, k_mac, k_mac_end, DBUF },
	{ H_TWICE, k_mem, k_mem_end, DBUF },
	{ H_SRAM, k_mem, k_mem_end, DBUF },
	{ H_TWICE, (const void *)LINE_CODE, 0, DBUF },            /* code droit : chaud */
	{ H_COLD_I, (const void *)LINE_CODE, 0, DBUF },           /* ... froid (cache d'instructions vide) */
	{ H_LINE_SRAM, (const void *)LINE_CODE, 0, DBUF },        /* ... en SRAM */
	{ H_TWICE, k_rd, 0, DBUF },                               /* 1 Ko lu : dans le cache */
	{ H_COLD_D, k_rd, 0, DBUF },                              /* ... absent du cache */
	{ H_ONCE, k_rd, 0, UNCACHED(DBUF) },                      /* ... par la vue sans cache */
	{ H_TWICE, k_rd, 0, SCRATCH },                            /* ... en SRAM */
};

/* le code droit, recopie en SRAM, cache d'instructions vide : ce que coute une ligne de code lue en SRAM (a
 * comparer a I-MISS, une ligne lue en SDRAM) */
static __attribute__((noinline)) u32 line_sram(void *d)
{
	u32 n = (LINES * 16 + 2 + 3) / 4, t;

	copy(save, (const u32 *)SCRATCH, n);
	copy((u32 *)SCRATCH, (const u32 *)UNCACHED(LINE_CODE), n);
	m_icinv();
	t = m_time((const void *)SCRATCH, d);
	copy((u32 *)SCRATCH, save, n);
	return t;
}

static __attribute__((noinline)) void bench(void)
{
	u32 t, k = st.step;
	void *d = (void *)BENCH[k].data;
	const void *code = BENCH[k].code;

	switch (BENCH[k].how) {
	case H_SRAM:
		t = in_sram(code, BENCH[k].end, d);
		break;
	case H_COLD_I:
		m_icinv();
		t = m_time(code, d);
		break;
	case H_LINE_SRAM:
		t = line_sram(d);
		break;
	case H_COLD_D:
		evict();
		t = m_time(code, d);
		break;
	case H_ONCE:
		t = m_time(code, d);
		break;
	default:
		t = twice(code, d);
	}
	if (t < st.best[k])
		st.best[k] = t;
	st.step = k + 1 < NB ? k + 1 : 0;
}

static __attribute__((noinline)) void publish(void)
{
	u32 c = st.per / 1000, i, m;                      /* dixiemes de % : ticks / (periode / 1 000) */

	if (c) {
		for (i = 0; i < A_PEAK; i++)
			st.shown[i] = st.sum[i] / c;
		st.shown[A_PEAK] = st.peak;
		i = st.idle0;
		st.shown[A_IDLE] = (m_idle_acc - i) / c;
		i = st.shown[A_TOTAL] + st.shown[A_IDLE];
		st.shown[A_OTHER] = i < 1000 ? 1000 - i : 0;
	}
	for (i = 0; i < NB; i++) {
		st.bshown[i] = st.best[i];
		st.best[i] = ~0u;
	}
	for (m = 0; m < 2; m++) {
		u32 cc = st.cper[m] / 1000;
		st.cshown[m][NC] = st.cn[m];
		for (i = 0; i < NC; i++) {
			st.cshown[m][i] = cc ? st.csum[m][i] / cc : 0;
			st.csum[m][i] = 0;
		}
		st.cn[m] = st.cper[m] = 0;
	}
}

/* l'ecran k (1 AUDIO, 2 BENCH, 3 COLD) est affiche : dessine depuis moins de SEEN blocs */
static __attribute__((noinline)) int shown(u32 k)
{
	return st.seen[k] && st.blocks - st.seen[k] < SEEN;
}

static __attribute__((noinline)) void restart(void)
{
	u32 i;

	st.n = st.per = st.peak = 0;
	for (i = 0; i < A_PEAK; i++)
		st.sum[i] = 0;
	st.idle0 = m_idle_acc;
}

static __attribute__((noinline)) void accumulate(u32 total, u32 per, u32 cold)
{
	u32 *d = m_site.dur, x;

	st.per += per;
	st.sum[A_SEQ] += m_site.t0[S_FN] - m_tisr - d[S_USBIN];
	st.sum[A_USB] += d[S_USBIN] + d[S_USBOUT];
	st.sum[A_SMOOTH] += d[S_SMOOTH];
	st.sum[A_LFO] += d[S_LFO];
	st.sum[A_VOICES] += d[S_VOICES];
	st.sum[A_POST] += d[S_FN] - d[S_SMOOTH] - d[S_LFO] - d[S_VOICES] - d[S_DIST] - d[S_OUT];
	st.sum[A_DIST] += d[S_DIST];
	st.sum[A_OUT] += d[S_OUT];
	st.sum[A_TOTAL] += total;
	x = total * 1000 / per;
	if (x > st.peak)
		st.peak = x;
	if (shown(3)) {
		st.cn[cold]++;
		st.cper[cold] += per;
		st.csum[cold][C_TOTAL] += total;
		st.csum[cold][C_VOICES] += d[S_VOICES];
		st.csum[cold][C_OUT] += d[S_OUT];
	}
}

void m_block_end(void)
{
	u32 end = DTIM0, t0 = m_tisr, per, cold;

	if (m_fresh)
		init();
	st.blocks++;
	per = st.prev_isr ? t0 - st.prev_isr : 0;        /* 0 au 1er bloc */
	st.prev_isr = t0;
	cold = st.cur_cold;
	st.cur_cold = m_cold;                             /* le bloc suivant : un sur deux froid, ecran COLD affiche */
	m_cold = shown(3) ? !m_cold : 0;
	if (!per || per > MAXPER) {
		restart();
		return;
	}
	accumulate(end - t0, per, cold);
	if (shown(2))
		bench();
	if (++st.n >= WIN) {
		publish();
		restart();
	}
}

/* ---- les ecrans ---------------------------------------------------------------------------------------------- *
 * Comme ceux de Model-TG (sys_txt) : petite police (0x40ea14cc), 0x40071a04(ecran, police, x, y, drapeaux, "%s",
 * texte) ; y compte depuis le bas : une ligne de 9 points dont le haut est a la ligne 1 + 10 r est en 54 - 10 r ;
 * drapeaux 0x10 (a gauche de x) ou 0x14 (contre x, a droite), le fond efface. */
#define DRAW_TEXT ((void (*)(void *, void *, s32, s32, s32, const char *, const char *))0x40071a04)
#define SMALL_FONT ((void *)0x40ea14cc)
#define FMT_S ((const char *)0x40124b58)

static void txt(void *bmp, s32 x, s32 row, s32 right, const char *s)
{
	DRAW_TEXT(bmp, SMALL_FONT, x, 54 - 10 * row, right ? 0x14 : 0x10, FMT_S, s);
}

/* v en centiemes (dec = 2), dixiemes (1) ou unites (0) -> texte ; rend la fin */
static __attribute__((noinline)) char *num(char *s, u32 v, u32 dec)
{
	u32 p = dec == 2 ? 100 : (dec == 1 ? 10 : 1), ip = v / p, fp = v % p, n = 0;
	char tmp[10];

	do {
		tmp[n++] = '0' + ip % 10;
		ip /= 10;
	} while (ip);
	while (n)
		*s++ = tmp[--n];
	if (dec) {
		*s++ = '.';
		if (dec == 2)
			*s++ = '0' + fp / 10;
		*s++ = '0' + fp % 10;
	}
	*s = 0;
	return s;
}

/* une case : l'etiquette a gauche de la colonne, la valeur contre sa droite (~0 : « -- ») */
static __attribute__((noinline)) void cell(void *bmp, u32 i, const char *label, u32 v, u32 dec, char unit)
{
	char b[12], *e = b;
	u32 col = i & 1, row = i >> 1;

	txt(bmp, col ? 68 : 2, row, 0, label);
	if (v == ~0u) {
		*e++ = '-';
		*e++ = '-';
	} else {
		e = num(b, v, dec);
		if (unit)
			*e++ = unit;
	}
	*e = 0;
	txt(bmp, col ? 125 : 60, row, 1, b);
}

/* ticks -> cycles x 100 par unite (instruction, ligne, mot), d'apres l'essai de l'horloge (1 056 instructions d'un
 * cycle en clk ticks) ; ~0 si l'un manque */
static __attribute__((noinline)) u32 cyc100(u32 ticks, u32 units)
{
	u32 clk = st.bshown[B_CLK];

	if (ticks == ~0u || clk == ~0u || !clk || ticks > 40000)
		return ~0u;
	return ticks * 105600 / clk / units;
}

/* les cases d'un ecran : etiquette, et la valeur : un poste (V_SHOWN, ecran AUDIO), un essai en cycles par unite
 * (V_CYC : a = l'essai, b = les unites), l'ecart de deux essais (V_DIFF : a - b, par c unites), la frequence (V_MHZ),
 * une colonne de l'essai A/B (V_AB : a = normal 0 / froid 1, b = le poste ; V_GAIN ; V_BLOCKS) */
enum { V_SHOWN, V_CYC, V_DIFF, V_MHZ, V_AB, V_GAIN, V_BLOCKS };
struct spec {
	const char *label;
	u8 kind, a, b, c, dec;
	char unit;
};

static const struct spec PAGE_AUDIO[NA] = {
	{ "SEQ", V_SHOWN, A_SEQ, 0, 0, 1, '%' }, { "USB", V_SHOWN, A_USB, 0, 0, 1, '%' },
	{ "SMOOTH", V_SHOWN, A_SMOOTH, 0, 0, 1, '%' }, { "LFO", V_SHOWN, A_LFO, 0, 0, 1, '%' },
	{ "VOICES", V_SHOWN, A_VOICES, 0, 0, 1, '%' }, { "POST", V_SHOWN, A_POST, 0, 0, 1, '%' },
	{ "DIST", V_SHOWN, A_DIST, 0, 0, 1, '%' }, { "OUTPUT", V_SHOWN, A_OUT, 0, 0, 1, '%' },
	{ "TOTAL", V_SHOWN, A_TOTAL, 0, 0, 1, '%' }, { "PEAK", V_SHOWN, A_PEAK, 0, 0, 1, '%' },
	{ "IDLE", V_SHOWN, A_IDLE, 0, 0, 1, '%' }, { "OTHER", V_SHOWN, A_OTHER, 0, 0, 1, '%' },
};
static const struct spec PAGE_BENCH[NA] = {
	{ "CPU", V_MHZ, 0, 0, 0, 0, 'M' }, { "RD SR", V_CYC, B_SRD, 64, 4, 2, 0 },
	{ "ALU", V_CYC, B_ALU, 132, 4, 2, 0 }, { "ALU SR", V_CYC, B_ALU_S, 132, 4, 2, 0 },
	{ "MAC", V_CYC, B_MAC, 84, 4, 2, 0 }, { "MAC SR", V_CYC, B_MAC_S, 84, 4, 2, 0 },
	{ "MEM", V_CYC, B_MEM, 68, 4, 2, 0 }, { "MEM SR", V_CYC, B_MEM_S, 68, 4, 2, 0 },
	{ "LINE", V_CYC, B_LINE, LINES, 1, 2, 0 }, { "LINE SR", V_CYC, B_LINE_S, LINES, 1, 2, 0 },
	{ "I-MISS", V_DIFF, B_LINE_C, B_LINE, LINES, 2, 0 }, { "D-MISS", V_DIFF, B_DC, B_DW, 64, 2, 0 },
};
static const struct spec PAGE_COLD[NA] = {
	{ "NORMAL", V_AB, 0, C_TOTAL, 0, 1, '%' }, { "COLD", V_AB, 1, C_TOTAL, 0, 1, '%' },
	{ "VOICES", V_AB, 0, C_VOICES, 0, 1, '%' }, { "VOICES", V_AB, 1, C_VOICES, 0, 1, '%' },
	{ "OUTPUT", V_AB, 0, C_OUT, 0, 1, '%' }, { "OUTPUT", V_AB, 1, C_OUT, 0, 1, '%' },
	{ "GAIN", V_GAIN, 0, 0, 0, 1, '%' }, { "BLOCKS", V_BLOCKS, 0, 0, 0, 0, 0 },
	{ "RD UNC", V_CYC, B_UNC, 64, 4, 2, 0 }, { "RD C", V_CYC, B_DW, 64, 4, 2, 0 },
	{ 0, 0, 0, 0, 0, 0, 0 }, { 0, 0, 0, 0, 0, 0, 0 },
};
static const struct spec *const PAGES[3] = { PAGE_AUDIO, PAGE_BENCH, PAGE_COLD };

static __attribute__((noinline)) u32 bench_value(const struct spec *p)
{
	u32 *b = st.bshown, x, y;

	if (p->kind == V_CYC)                             /* b x c unites : instructions, lignes ou mots */
		return cyc100(b[p->a], p->b * p->c);
	if (p->kind == V_DIFF) {
		x = cyc100(b[p->a], p->c);
		y = cyc100(b[p->b], p->c);
		return x == ~0u || y == ~0u ? ~0u : (x > y ? x - y : 0);
	}
	return b[B_CLK] == ~0u || !b[B_CLK] ? ~0u : 1056 * 135168 / b[B_CLK] / 1000;     /* V_MHZ : 1 056 cycles */
}

static __attribute__((noinline)) u32 value(const struct spec *p)
{
	u32 x, y;

	switch (p->kind) {
	case V_SHOWN:
		return st.shown[p->a];
	case V_CYC:
	case V_DIFF:
	case V_MHZ:
		return bench_value(p);
	case V_AB:
		return st.cshown[p->a][p->b];
	case V_GAIN:
		x = st.cshown[1][C_TOTAL];
		y = st.cshown[0][C_TOTAL];
		return x > y ? x - y : 0;
	default:
		return st.cshown[0][NC] + st.cshown[1][NC];
	}
}

/* m_sys (mesure_hooks.S) : ecran 1 AUDIO, 2 BENCH, 3 COLD */
void m_render(void *bmp, u32 page)
{
	const struct spec *p;
	u32 i;

	if (m_fresh || page < 1 || page > 3)
		return;
	st.seen[page] = st.blocks;
	p = PAGES[page - 1];
	for (i = 0; i < NA && p[i].label; i++)
		cell(bmp, i, p[i].label, value(&p[i]), p[i].dec, p[i].unit);
}
