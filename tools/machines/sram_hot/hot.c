/*
 * Code chaud en SRAM interne, charge selon les machines du projet (notes/76).
 *
 * Le cache d'instructions (8 Ko) ne garde presque rien d'un bloc a l'autre : le code que l'interruption audio
 * execute a chaque bloc (17 a 27 Ko) est relu en SDRAM, ligne de 16 o par ligne. Ce chargeur recopie en SRAM les
 * fonctions les plus chaudes (de l'OS, de Model-TG, de nos machines) pour les machines des 6 pistes, avec leurs
 * adresses corrigees, et les fait executer la-bas pendant le calcul audio.
 *
 *  - Unites (hot_units, triees par lignes chaudes par octet) : une ou plusieurs fonctions contigues, sans reference
 *    relative au PC qui sorte de l'unite. Une copie appelle les autres copies (corrections hot_fixes : champ de
 *    32 bits d'un jsr/jmp/lea absolu), ou les originaux en SDRAM.
 *  - Detours (hot_dets) : l'entree de chaque fonction chaude devient, au demarrage (hot_boot), « jmp talon » ; le
 *    talon (hot_asm.S) saute a hot_tab[i] : sa copie pendant le calcul audio (hot_probe), l'original sinon
 *    (hot_orig[i] : les instructions deplacees puis « jmp entree + k »). L'interface et les autres interruptions
 *    n'entrent donc jamais dans une copie, et une copie n'est recouverte qu'en dehors du calcul audio.
 *  - Place (hot_regs) : le code et les tables du Syntakt en SRAM quand aucune piste n'a de moteur du Syntakt, et
 *    deux fins de SRAM que l'OS ne designe nulle part. Une region dont une machine du projet a besoin est rendue
 *    (recopiee depuis la zone de transit de la charge utile). st_away (un bit par machine) met en pause les moteurs
 *    du Syntakt dont le code ou une table n'est pas en place, quoi que la boucle des voix choisisse (dispatch,
 *    gen_syntakt_engines.py) : leur piste reste muette, rien ne s'execute la-bas.
 *  - Le code en SRAM passe par le cache d'instructions (RAMBAR du bootstrap, notes/75 §1.2) : il est vide apres
 *    chaque recopie de code, avant que ce code serve (hot_icinv_run).
 *  - Chargement : a chaque bloc, avant le calcul audio, au plus HOT_BUDGET octets ; les copies ne servent qu'une
 *    fois toutes en place (activate).
 *
 * Les tables (hot_tables.c) sont generees par tools/gen_sram_hot.py, d'apres le profil d'emulation
 * (tools/emu/profile_hot.py). Aucun octet Elektron dans ce depot : le code copie l'est a l'execution, depuis la
 * memoire de la machine.
 */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef int s32;

struct hunit { u32 src; u16 len, mask, fix, nfix, det, ndet; };      /* mask : machines (bits 0..14) qui s'en servent */
struct hfix { u16 off, unit; };                                     /* unit : 0xffff = elle-meme */
struct hdet { u32 at; u16 unit, off, sum; u8 k, pad; };             /* sum : somme des k octets d'origine */
struct hreg { u32 lo, hi, src; u16 need, pad; };                    /* need : machines qui la veulent en place */

extern const struct hunit hot_units[HOT_NU];
extern const struct hfix hot_fixes[];
extern const struct hdet hot_dets[HOT_NDET];
extern const struct hreg hot_regs[HOT_NREG];
extern void hot_icinv(void), hot_icinv_run(void);
extern void hot_copy(void *to, const void *from, u32 longs);    /* hot_asm.S : par movem */
extern char hot_stubs[];

const u16 hot_n[3] = {HOT_NU, HOT_NDET, HOT_NREG};  /* pour les preuves (tools/emu/test_sram_hot.py) */

#define MAGIC   0x484f5421u                 /* « HOT! » : hot_boot a tourne */
#define NEXT    0xffffffffu                 /* signature a recalculer */

u32 hot_tab[HOT_NDET] __attribute__((aligned(4)));   /* lu par les talons : copie (calcul audio) ou original */
u8 hot_orig[HOT_NDET][16];
u32 st_away __attribute__((section(".bss.away")));  /* bit m : machine m en pause (son code n'est pas en place) */
u32 hot_sig;                                /* machines des 6 pistes (bits) */
u8 hot_state;                               /* 0 : rien ; 1 : chargement ; 2 : copies actives */
u32 hot_booted;
static u32 tclone[HOT_NDET] __attribute__((aligned(4))), torig[HOT_NDET] __attribute__((aligned(4)));
static u32 dst[HOT_NU] __attribute__((aligned(4)));
static u8 dirty[HOT_NREG], live[HOT_NDET];
static u32 cur, curoff, root;

/* l'emulateur pose ici ses crochets EMAC sur ce qui vient d'etre copie (tools/emu) ; ne fait rien */
void __attribute__((noinline)) hot_note(u32 at, u32 n)
{
	__asm__ volatile("" : : "r"(at), "r"(n) : "memory");
}

static void put32(u8 *p, u32 v)
{
	p[0] = v >> 24;
	p[1] = v >> 16;
	p[2] = v >> 8;
	p[3] = v;
}

static u32 get32(const u8 *p)
{
	return (u32)p[0] << 24 | (u32)p[1] << 16 | (u32)p[2] << 8 | p[3];
}

/* au demarrage (hot_boot : 2e etage du crochet, cache de donnees coupe) : les detours, puis le cache
 * d'instructions vide */
void hot_init(void)
{
	int i, k;

	for (i = 0; i < HOT_NDET; i++) {
		const struct hdet *e = &hot_dets[i];
		u8 *f = (u8 *)e->at, *o = hot_orig[i];
		u16 sum = 0;

		for (k = 0; k < e->k; k++)
			sum += f[k];
		torig[i] = hot_tab[i] = (u32)o;
		if (sum != e->sum)                  /* pas les octets attendus : pas de detour */
			continue;
		for (k = 0; k < e->k; k++)
			o[k] = f[k];
		o[k] = 0x4e;
		o[k + 1] = 0xf9;
		put32(o + k + 2, e->at + e->k);
		put32(f + 2, (u32)hot_stubs + 8 * i);
		f[1] = 0xf9;
		f[0] = 0x4e;
		live[i] = 1;
	}
	hot_sig = NEXT;
	hot_state = 0;
	st_away = 0;
	hot_booted = MAGIC;
	hot_icinv();
}

/* machines des 6 pistes : le parametre MACHINE (0x400a7db0 : borne, puis la table de la passerelle) et la machine
 * que joue la voix (Model-TG garde celle de la note en cours jusqu'au trig suivant) */
static u32 signature(void)
{
	u32 s = 0;
	int t;

	for (t = 0; t < 6; t++) {
		s32 p = *(signed char *)(HOT_MACHINE + 0x42 * t);   /* octet fort du parametre MACHINE de la piste */
		u32 v = *(u32 *)(HOT_VOICE + HOT_VSTRIDE * t);
		if (p < 0)
			p = 0;
		else if (p > 14)
			p = 5;
		s |= 1u << *(signed char *)(HOT_MAP + p);
		if (v < 15)
			s |= 1u << v;
	}
	return s;
}

/* machines en pause : celles qui ont besoin d'une region recouverte (ou pas encore rendue) */
static void away(void)
{
	u32 a = 0;
	int r;

	for (r = 0; r < HOT_NREG; r++)
		if (dirty[r])
			a |= hot_regs[r].need;
	st_away = a;
}

/* place des unites des machines du projet, par ordre de valeur ; regions a rendre */
static void plan(void)
{
	u32 lo[HOT_NREG], hi[HOT_NREG];
	int r, u, n = 0;

	for (r = 0; r < HOT_NREG; r++) {
		const struct hreg *g = &hot_regs[r];
		if (g->need & hot_sig)
			continue;
		if (n && hi[n - 1] == g->lo) {
			hi[n - 1] = g->hi;
		} else {
			lo[n] = g->lo;
			hi[n++] = g->hi;
		}
	}
	for (u = 0; u < HOT_NU; u++) {
		const struct hunit *h = &hot_units[u];
		dst[u] = 0;
		if (!(h->mask & hot_sig))
			continue;
		for (r = 0; r < n; r++) {
			u32 a = lo[r] + ((h->src - lo[r]) & 3);         /* meme alignement modulo 4 que l'original */
			if (a + h->len <= hi[r]) {
				dst[u] = a;
				lo[r] = a + h->len;
				break;
			}
		}
	}
	cur = curoff = 0;
	hot_state = 1;
}

/* n octets (pair) : le mot de tete s'il le faut (meme alignement modulo 4 des deux cotes, voir plan), puis par
 * mots longs, puis le mot de queue */
static void copy(u32 to, u32 from, u32 n)
{
	if ((from & 2) && n) {
		*(u16 *)to = *(const u16 *)from;
		to += 2;
		from += 2;
		n -= 2;
	}
	hot_copy((void *)to, (const void *)from, n >> 2);
	if (n & 2)
		*(u16 *)(to + (n & ~3)) = *(const u16 *)(from + (n & ~3));
}

/* une unite copiee : instructions d'origine aux detours, puis corrections */
static void finish(int u)
{
	const struct hunit *h = &hot_units[u];
	u8 *d = (u8 *)dst[u];
	int i, k;

	for (i = h->det; i < h->det + h->ndet; i++)
		if (live[i])
			for (k = 0; k < hot_dets[i].k; k++)
				d[hot_dets[i].off + k] = hot_orig[i][k];
	for (i = h->fix; i < h->fix + h->nfix; i++) {
		int v = hot_fixes[i].unit == 0xffff ? u : hot_fixes[i].unit;
		u8 *p = d + hot_fixes[i].off;
		u32 x = get32(p);
		if (dst[v] && x - hot_units[v].src < hot_units[v].len)
			put32(p, x - hot_units[v].src + dst[v]);
	}
	hot_note(dst[u], h->len);
}

static void activate(void)
{
	int i;

	for (i = 0; i < HOT_NDET; i++) {
		u32 d = dst[hot_dets[i].unit];
		tclone[i] = d ? d + hot_dets[i].off : torig[i];
	}
	root = dst[HOT_ROOT_UNIT] ? dst[HOT_ROOT_UNIT] + HOT_ROOT_OFF : HOT_ROOT_ORIG;
	hot_icinv_run();                            /* les copies, pas ce qu'il y avait a ces adresses */
	hot_state = 2;
}

static void work(s32 budget)
{
	while (budget > 0) {
		if (cur < HOT_NREG) {                       /* regions a rendre */
			const struct hreg *g = &hot_regs[cur];
			u32 n;
			if (!(g->need & hot_sig) || !dirty[cur]) {
				cur++;
				continue;
			}
			n = g->hi - g->lo - curoff;
			if (n > (u32)budget)
				n = budget;
			copy(g->lo + curoff, g->src + curoff, n);
			curoff += n;
			budget -= n;
			if (curoff == g->hi - g->lo) {
				hot_icinv_run();
				dirty[cur] = 0;
				away();
				hot_note(g->lo, g->hi - g->lo);
				cur++;
				curoff = 0;
			}
			continue;
		}
		if (cur - HOT_NREG >= HOT_NU) {
			activate();
			return;
		} else {
			int u = cur - HOT_NREG, r;
			const struct hunit *h = &hot_units[u];
			u32 n;
			if (!dst[u]) {
				cur++;
				continue;
			}
			if (!curoff) {                      /* les regions sous la copie ne sont plus en place */
				for (r = 0; r < HOT_NREG; r++)
					if (dst[u] < hot_regs[r].hi && hot_regs[r].lo < dst[u] + h->len)
						dirty[r] = 1;
				away();
			}
			n = h->len - curoff;
			if (n > (u32)budget)
				n = budget;
			copy(dst[u] + curoff, h->src + curoff, n);
			curoff += n;
			budget -= n;
			if (curoff == h->len) {
				finish(u);
				cur++;
				curoff = 0;
			}
		}
	}
}

/* avant le calcul audio (hot_probe) : rend la fonction a appeler (la passerelle, ou sa copie) */
u32 hot_step(void)
{
	u32 s;

	if (hot_booted != MAGIC)
		return HOT_ROOT_ORIG;
	s = signature();
	if (s != hot_sig) {
		hot_sig = s;
		plan();
	}
	if (hot_state == 1)
		work(HOT_BUDGET);
	if (hot_state == 2) {
		hot_copy(hot_tab, tclone, HOT_NDET);
		return root;
	}
	return HOT_ROOT_ORIG;
}

/* apres le calcul audio : les talons reviennent aux originaux */
void hot_after(void)
{
	if (hot_state == 2)
		hot_copy(hot_tab, torig, HOT_NDET);
}
