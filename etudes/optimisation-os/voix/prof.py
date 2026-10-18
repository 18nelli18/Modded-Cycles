"""Profileur d'instructions et d'accès mémoire pour mcengine / seqrig (travail, non versionné).

Attribue chaque instruction exécutée à la fonction en cours (pile d'appels fantôme : jsr/bsr -> entrée, retour à
l'adresse suivante -> sortie), compte les accès mémoire par région et par ligne de 16 o (les chargements des MAC
avec chargement, faits par emac.py en Python, compris), et garde la suite des accès pour un simulateur de cache.
"""
import sys, struct, collections
sys.path.insert(0, "/home/user/Modded-Cycles/tools/emu"); sys.path.insert(0, "/home/user/Modded-Cycles/tools")
import numpy as np
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE
from unicorn import m68k_const as mk
import mcengine as E

SEC3 = "/tmp/claude-0/-home-user-Modded-Cycles/4cafd55d-d242-5df3-ad6a-3e64ee54ea56/scratchpad/os/sec3.bin"
BASE = 0x40000400

NAMES = {
    0x400a7d4a: "voice_loop", 0x400a7d16: "trig_reset(0x400a7d16)", 0x400a7ab8: "voice_reset",
    0x400aa08c: "KICK.update", 0x400aa3c4: "KICK.render", 0x400ab3b0: "SNARE.update", 0x400ab6e8: "SNARE.render",
    0x400aa49c: "METAL.update", 0x400aa712: "METAL.render", 0x400aa998: "PERC.update", 0x400aacc2: "PERC.render",
    0x400aa7b8: "TONE.update", 0x400aa930: "TONE.render", 0x400aae88: "CHORD.update", 0x400ab24c: "CHORD.render",
    0x400a9120: "op_env(0x400a9120)", 0x400a9252: "amp_env(0x400a9252)", 0x400a9430: "vca(0x400a9430)",
    0x400a967a: "punch(0x400a967a)", 0x400a7e6c: "pitch_inc(0x400a7e6c)", 0x400a9884: "mix2(0x400a9884)",
    0x400a9d4e: "filt(0x400a9d4e)", 0x400a9cf6: "filt(0x400a9cf6)", 0x400a9302: "env2(0x400a9302)",
    0x400a9504: "vca2(0x400a9504)", 0x400a9ca8: "interp(0x400a9ca8)", 0x400a9ebe: "f(0x400a9ebe)",
    0x400a8204: "op(0x400a8204)", 0x400a8adc: "op(0x400a8adc)", 0x400a835e: "op(0x400a835e)",
    0x400a8722: "op(0x400a8722)", 0x400a8fc2: "op(0x400a8fc2)", 0x400a8060: "chord_tab(0x400a8060)",
    0x400a8080: "chord_wave(0x400a8080)",
    0x40058474: "param_smooth(0x40058474)", 0x40056e24: "vel_mod(0x40056e24)", 0x40091ab2: "lfo(0x40091ab2)",
    0x40056d9c: "vel_gain(0x40056d9c)", 0x4008f1f0: "gain_slew(0x4008f1f0)", 0x4005979e: "audio_fn(0x4005979e)",
}


def region(a):
    if 0x80000000 <= a < 0x80010000:
        return "SRAM"
    if 0x90000000 <= a < 0x90020000:
        return "pile(emu)"
    if 0x40000000 <= a < 0x48000000:
        return "SDRAM-cache"
    if 0x48000000 <= a < 0x50000000:
        return "SDRAM-noncache"
    return "autre"


class Prof:
    def __init__(self, uc, emac, record=True):
        self.uc = uc
        self.emac = emac
        self.record = record
        self.reset()
        self.h = [uc.hook_add(UC_HOOK_CODE, self._code), uc.hook_add(UC_HOOK_MEM_READ | UC_HOOK_MEM_WRITE, self._mem)]
        # sans ce vidage, les lectures du code déjà traduit ne passent pas par le crochet (unicorn 2.1.4, t_rd3.py)
        uc.ctl_flush_tb()
        orig = self._orig_ea = emac._ea
        def ea(spec, _o=orig):
            ad, post = _o(spec)
            self._acc(ad, 4, False)
            return ad, post
        emac._ea = ea
        self.on = True

    def close(self):
        for h in self.h:
            self.uc.hook_del(h)
        self.emac._ea = self._orig_ea
        self.on = False

    def reset(self):
        self.addr = collections.Counter()        # instructions par adresse
        self.excl = collections.Counter()        # par fonction (exclusif)
        self.incl = collections.Counter()        # par fonction (inclusif)
        self.calls = collections.Counter()
        self.stack = [(0, None)]                 # (fonction, adresse de retour)
        self.pending = None
        self.mem = collections.Counter()         # (région, r/w) -> accès
        self.lines = collections.defaultdict(set)  # région -> lignes de données
        self.wlines = collections.defaultdict(set)
        self.fnlines = collections.defaultdict(lambda: collections.defaultdict(set))  # fonction -> région -> lignes
        self.seq = []                            # (type, ligne) : 'I' code, 'R'/'W' données
        self.n = 0

    def _code(self, uc, a, size, ud):
        if not self.on:
            return
        st = self.stack
        if self.pending is not None:
            sp = uc.reg_read(mk.UC_M68K_REG_A7)
            st.append((a, struct.unpack(">I", bytes(uc.mem_read(sp, 4)))[0]))
            self.calls[a] += 1
            self.pending = None
        while len(st) > 1 and a == st[-1][1]:
            st.pop()
        f = st[-1][0]
        self.n += 1
        self.addr[a] += 1
        self.excl[f] += 1
        for g in {x[0] for x in st}:
            self.incl[g] += 1
        if self.record:
            self.seq.append(("I", a >> 4))
        op = struct.unpack(">H", bytes(uc.mem_read(a, 2)))[0]
        if (op & 0xffc0) == 0x4e80 or (op & 0xff00) == 0x6100:
            self.pending = True

    def _acc(self, a, size, w):
        if not self.on:
            return
        r = region(a)
        self.mem[(r, "W" if w else "R")] += 1
        f = self.stack[-1][0]
        for l in range(a >> 4, ((a + size - 1) >> 4) + 1):
            self.lines[r].add(l)
            if w:
                self.wlines[r].add(l)
            self.fnlines[f][r].add(l)
            if self.record and r != "SRAM" and r != "autre":
                self.seq.append(("W" if w else "R", l, r))

    def _mem(self, uc, access, a, size, value, ud):
        self._acc(a, size, access == 17)  # UC_MEM_WRITE = 17 (unicorn 2)

    def name(self, f):
        return "voice_loop" if f == 0 else NAMES.get(f, f"{f:#x}")


class Cache:
    """Cache 4 voies, lignes de 16 o, LRU ; 8 Ko -> 128 ensembles. Données : copyback, allocation en écriture."""
    def __init__(self, size=8192, ways=4, line=16):
        self.sets = size // line // ways
        self.ways = ways
        self.s = [collections.OrderedDict() for _ in range(self.sets)]
        self.miss = 0
        self.wb = 0

    def access(self, l, write=False):
        s = self.s[l % self.sets]
        if l in s:
            s.move_to_end(l)
            if write:
                s[l] = True
            return True
        self.miss += 1
        if len(s) >= self.ways:
            _, dirty = s.popitem(last=False)
            if dirty:
                self.wb += 1
        s[l] = write
        return False

    def flush(self):
        for s in self.s:
            s.clear()


def simulate(seqs, ic=None, dc=None):
    """Rejoue des suites d'accès ; rend [(défauts I, défauts D, écritures en retour D, accès non cachés)] par suite."""
    ic = ic or Cache()
    dc = dc or Cache()
    res = []
    for seq in seqs:
        mi, md, wb = ic.miss, dc.miss, dc.wb
        unc = 0
        for x in seq:
            if x[0] == "I":
                ic.access(x[1])
            elif x[2] == "SDRAM-noncache":
                unc += 1
            else:
                dc.access(x[1], x[0] == "W")
        res.append((ic.miss - mi, dc.miss - md, dc.wb - wb, unc))
    return res, ic, dc


def load_stock():
    return open(SEC3, "rb").read()
