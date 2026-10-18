"""Mesure d'un bloc sur le banc (banc.py) : instructions, lignes touchées, caches simulés, accès non cachés.

Modèle des notes 27-28 : caches de 8 Ko d'instructions et 8 Ko de données, lignes de 16 o, 4 voies, LRU, recopie
(copyback) avec allocation en écriture pour 0x40000000..0x47ffffff (ACR0) ; la pile du banc (0x9000xxxx) compte
comme de la SDRAM cachée (la vraie pile est en SDRAM, 0x48000000 en haut au démarrage, 0x400004f2) ; SRAM
0x80000000..0x8000ffff hors cache, 1 cycle par accès ; 0x48000000..0x4fffffff non caché (alias de la DDR),
précis (CACR, rapport de « systeme »).
Coût = 1,54 cycle par instruction + 15 cycles par ligne transférée (remplissage ou recopie d'une ligne sale),
166 667 cycles par bloc.
"""
import bisect
from collections import defaultdict, OrderedDict

from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE

CPB = 166667.0
CPI = 1.54
LINE_CYC = 15

# fonctions (début, nom) ; une adresse appartient à la dernière fonction qui commence avant elle (jusqu'à la fin)
FUNCS = [
    (0x40000400, "autre-os"),
    (0x40002ae0, "usb-in(0x40002ae0)"), (0x40002b80, "autre-os"),
    (0x400565c6, "mix:gain x4 (0x400565c6)"),
    (0x40056610, "mix:master 8 entrées (0x40056610)"),
    (0x40056698, "mix:envoi reverb 7 entrées (0x40056698)"),
    (0x40056716, "mix:envoi delay 6 entrées (0x40056716)"),
    (0x4005678a, "mix:entrelace (0x4005678a)"),
    (0x400567a4, "mix:désentrelace (0x400567a4)"),
    (0x400567ba, "mix:corps (0x400567ba)"),
    (0x40056d9c, "gain vélocité (0x40056d9c)"),
    (0x40056dfe, "autre-os"),
    (0x40056e24, "mod. vélocité (0x40056e24)"),
    (0x40056ea0, "clic (0x40056ea0/ea8)"),
    (0x40056f58, "volume+dist (0x40056f58)"),
    (0x4005725e, "autre-os"),
    (0x400573fa, "dma écritures ch42 (0x400573fa)"),
    (0x40057488, "delay (0x40057488)"),
    (0x4005770e, "autre-os"),
    (0x40057942, "reverb pointeurs (0x40057942)"),
    (0x400579c4, "reverb (0x400579c4)"),
    (0x40057fa8, "autre-os"),
    (0x4005802e, "dma lectures ch30 (0x4005802e)"),
    (0x400582c4, "autre-os"),
    (0x40058474, "lissage (0x40058474)"),
    (0x40058502, "autre-os"),
    (0x40058c5e, "isr (0x40058c5e..)"),
    (0x40059388, "autre-os"),
    (0x4005979e, "fonction audio (0x4005979e)"),
    (0x40059882, "autre-os"),
    (0x4008f1f0, "memcpy (0x4008f1f0)"), (0x4008f238, "autre-os"),
    (0x40091ab2, "lfo/mod (0x40091ab2)"), (0x40091d80, "autre-os"),
    (0x400a7a00, "voix (0x400a7d4a + machines)"), (0x400c0000, "autre-os"),
]
STARTS = [a for a, _ in FUNCS]

# regroupement en postes de l'étage de sortie
POSTE = {
    "gain vélocité (0x40056d9c)": "1 gain vélocité",
    "volume+dist (0x40056f58)": "2 volume+dist",
    "clic (0x40056ea0/ea8)": "3 clic métronome",
    "dma lectures ch30 (0x4005802e)": "4 mixeur",
    "mix:corps (0x400567ba)": "4 mixeur",
    "mix:envoi delay 6 entrées (0x40056716)": "4 mixeur",
    "mix:envoi reverb 7 entrées (0x40056698)": "4 mixeur",
    "mix:master 8 entrées (0x40056610)": "4 mixeur",
    "mix:entrelace (0x4005678a)": "4 mixeur",
    "mix:désentrelace (0x400567a4)": "4 mixeur",
    "mix:gain x4 (0x400565c6)": "4 mixeur",
    "delay (0x40057488)": "5 delay",
    "reverb (0x400579c4)": "6 reverb",
    "reverb pointeurs (0x40057942)": "6 reverb",
    "dma écritures ch42 (0x400573fa)": "7 dma écritures",
}


def fname(a):
    i = bisect.bisect_right(STARTS, a) - 1
    return FUNCS[i][1] if i >= 0 else "hors-os"


class Cache:
    def __init__(self, size=8192, ways=4, line=16):
        self.sets = size // (ways * line)
        self.ways = ways
        self.s = [OrderedDict() for _ in range(self.sets)]

    def access(self, ln, write):
        """Rend (défaut, recopie d'une ligne sale)."""
        st = self.s[ln % self.sets]
        if ln in st:
            st.move_to_end(ln)
            if write:
                st[ln] = True
            return False, False
        wb = False
        if len(st) >= self.ways:
            _, dirty = st.popitem(last=False)
            wb = dirty
        st[ln] = write
        return True, wb

    def flush(self):
        for st in self.s:
            st.clear()


def region(a):
    if 0x80000000 <= a < 0x80010000:
        return "sram"
    if 0x40000000 <= a < 0x48000000 or 0x90000000 <= a < 0x90100000:
        return "sdram"
    if 0x48000000 <= a < 0x50000000:
        return "noncache"
    if a >= 0xfc000000:
        return "periph"
    return "autre"


class Tracer:
    """Pose les sondes ; stats remises à zéro par reset(), lues par report()."""

    def __init__(self, banc):
        self.b = banc
        self.uc = banc.uc
        self.ic = Cache()
        self.dc = Cache()
        self.cur = 0
        self.on = False
        self.reset()
        uc = self.uc
        uc.hook_add(UC_HOOK_CODE, self._code)
        uc.hook_add(UC_HOOK_MEM_READ, self._mem_r)
        uc.hook_add(UC_HOOK_MEM_WRITE, self._mem_w)
        banc.e.emac.on_load = self._emac_load
        # chemin lent de l'EMAC (macw...) : ses lectures passent par _ea
        em = banc.e.emac
        orig = em._ea

        def ea(spec):
            ad, post = orig(spec)
            self._emac_load(ad)
            return ad, post
        em._ea = ea

    def reset(self):
        self.ins = defaultdict(int)          # fonction -> instructions
        self.pc_count = defaultdict(int)     # adresse -> exécutions
        self.imiss = defaultdict(int)
        self.dmiss = defaultdict(int)
        self.dwb = defaultdict(int)
        self.lines = defaultdict(set)        # (fonction, région, r/w) -> lignes
        self.acc = defaultdict(int)          # (fonction, région, r/w) -> accès
        self.bytes = defaultdict(int)

    def _code(self, uc, a, size, ud):
        if not self.on:
            return
        self.cur = a
        f = fname(a)
        self.ins[f] += 1
        self.pc_count[a] += 1
        if 0x40000000 <= a < 0x48000000:
            for ln in {a >> 4, (a + size - 1) >> 4}:
                miss, _ = self.ic.access(ln, False)
                if miss:
                    self.imiss[f] += 1

    def _data(self, a, size, write):
        f = fname(self.cur)
        r = region(a)
        k = (f, r, "w" if write else "r")
        self.acc[k] += 1
        self.bytes[k] += size
        for ln in {a >> 4, (a + size - 1) >> 4}:
            self.lines[k].add(ln)
            if r == "sdram":
                miss, wb = self.dc.access(ln, write)
                if miss:
                    self.dmiss[f] += 1
                if wb:
                    self.dwb[f] += 1

    def _mem_r(self, uc, access, a, size, value, ud):
        if self.on:
            self._data(a, size, False)

    def _mem_w(self, uc, access, a, size, value, ud):
        if self.on:
            self._data(a, size, True)

    def _emac_load(self, a):
        if self.on:
            self._data(a, 4, False)

    # --- résultats ---
    def per_func(self):
        names = sorted(set(self.ins) | set(f for f, _, _ in self.acc))
        rows = {}
        for f in names:
            d = dict(ins=self.ins.get(f, 0), imiss=self.imiss.get(f, 0), dmiss=self.dmiss.get(f, 0),
                     dwb=self.dwb.get(f, 0))
            for r in ("sram", "sdram", "noncache", "periph"):
                for rw in "rw":
                    d[f"{r}_{rw}_lines"] = len(self.lines.get((f, r, rw), ()))
                    d[f"{r}_{rw}_acc"] = self.acc.get((f, r, rw), 0)
                    d[f"{r}_{rw}_bytes"] = self.bytes.get((f, r, rw), 0)
            d["cycles"] = CPI * d["ins"] + LINE_CYC * (d["imiss"] + d["dmiss"] + d["dwb"])
            d["pct"] = 100 * d["cycles"] / CPB
            rows[f] = d
        return rows
