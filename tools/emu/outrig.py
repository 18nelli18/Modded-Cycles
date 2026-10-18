"""Banc de l'étage de sortie du Model:Cycles OS 1.13 : la vraie interruption audio, bloc par bloc, AVEC tout ce qui suit
la boucle des voix (notes/70 ; porté de l'étude d'optimisation archivée sous le tag etude-optimisation-os-2026-10-18).

Part de seqrig.py (le corps de l'interruption 0x40058ca0..0x40059382, séquenceur et événements compris) mais NE saute
PAS le mixeur, les effets et la sortie codec : 0x40056f58 (Volume + Dist), 0x40056ea8 (clic du métronome), 0x400567ba
(mixeur, envois, delay, reverb, master, anneau du codec). La fonction audio 0x4005979e est appelée par le vrai jsr de
0x40059382 (ou ce qu'un tweak y a mis), dans la pile de l'interruption, et le banc vérifie qu'elle rend la pile et les
registres. Ce qu'il faut pour que l'étage de sortie tourne :
  - la DDR vue deux fois, avec cache (0x42xxxxxx) et sans (0x4axxxxxx) : un seul tampon projeté aux deux adresses,
    comme le matériel (lignes du delay 0x4a400000, de la reverb 0x4a340000 et 0x4a3d0000, anneau du codec 0x4a3ed080) ;
  - l'eDMA simulé : les TCD (0xfc045000..) en MMIO ; écrire START dans le CSR d'un canal exécute tout de suite sa
    chaîne (boucles mineures, scatter-gather jusqu'au dernier TCD). Canal 30 : lectures DDR -> SRAM (2 prises du
    delay, 8 + 9 lignes de reverb) ; canal 42 : écritures SRAM -> DDR ;
  - l'initialisation de l'OS (0x4005974c : effets puis voix ; 0x400449ce : réglages par défaut) ;
  - un kit par défaut chargé par l'OS lui-même (0x400595a8) : sons par défaut (0x400618f2), niveaux de piste 100,
    effets aux défauts des descripteurs (Delay Time 23, Fdbk 32, Reverb Size 42, Tone 64).

    rig = OutRig(main_os, extra_code=[(va, taille), ...])   # extra_code : code ajouté qui contient de l'EMAC
    info = rig.block()   # info["out"] (6 x 32, voix), info["ring"] (32 x 2, codec), info["usb"] (32 x 2)
"""
import ctypes
import re
import struct
import sys
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import numpy as np                      # noqa: E402
from unicorn import UC_PROT_ALL         # noqa: E402
from unicorn import m68k_const as mk    # noqa: E402

import mcengine                         # noqa: E402
import seqrig                           # noqa: E402
from emac import REG, M32               # noqa: E402

OUTPUT_FNS = (0x40056f58, 0x40056ea8, 0x400567ba)
RING = 0x4a3ed080            # anneau du codec (deux moitiés de 32 trames stéréo, 24 bits)
USB_MIX = 0x40fe4b90         # copie du master pour l'USB (32 trames stéréo)
LINES = ((0x42400000, 0x400000), (0x42340000, 0x90000), (0x423d0000, 0x8000))   # delay, reverb (= 0x4a…)
KIT = seqrig.KIT
AUDIO_CALL = 0x40059382      # jsr 0x4005979e (fonction audio) dans l'interruption


def speed_up_emac(em):
    """Compile en fermetures les MAC 32 bits avec chargement (et décalage) que emac.EMAC exécute par son chemin
    lent : même sémantique, exactement (voir emac.EMAC._slow), seulement plus vite."""
    uc = em.uc
    rr, rw, mr = uc.reg_read, uc.reg_write, uc.mem_read
    n = 0
    for addr, (sz, mn, ops) in em.ops.items():
        if addr in em.fast or mn not in ("macl", "msacl"):
            continue
        args = [a.strip() for a in ops.split(",")]
        if not re.fullmatch(r"%acc[0-3]", args[-1]) or args[0] not in REG or args[1] not in REG:
            continue                    # autre forme : chemin lent de emac.EMAC, exact
        i = int(args[-1][4])
        ry, rx = REG[args[0]], REG[args[1]]
        rest = args[2:-1]
        shift = 0
        if rest and rest[0] in ("<<", ">>"):
            shift = 1 if rest[0] == "<<" else -1
            rest = rest[1:]
        sign = 1 if mn == "macl" else -1
        ea = None
        if rest:
            m = re.match(r"(%a[0-7]|%fp|%sp)@(\+|-|\((-?\d+)\))?(&?)$", rest[0])
            if not m:
                continue
            an, mode, disp, amp = REG[m.group(1)], m.group(2), int(m.group(3) or 0), bool(m.group(4))
            rd = REG[rest[1]]
            ea = (an, mode, disp, amp, rd)

        def f(ry=ry, rx=rx, i=i, shift=shift, sign=sign, ea=ea):
            a = rr(ry) & M32
            b = rr(rx) & M32
            if not em.macsr & 0x40:
                a = a - 0x100000000 if a & 0x80000000 else a
                b = b - 0x100000000 if b & 0x80000000 else b
            p = a * b
            if shift == 1:
                p <<= 1
            elif shift == -1:
                p >>= 1
            if em.macsr & 0x20:
                p = (p >> 23) << 23
            if ea is not None:
                an, mode, disp, amp, rd = ea
                base = rr(an) & M32
                if mode == "-":
                    base = (base - 4) & M32
                elif mode not in ("+",):
                    base = (base + disp) & M32
                ad = base & em.mask if amp else base
                if em.on_load:
                    em.on_load(ad)
                val = int.from_bytes(mr(ad, 4), "big")
            em.acc[i] += sign * p
            if ea is not None:
                rw(rd, val)
                if mode == "-":
                    rw(an, base)
                elif mode == "+":
                    rw(an, (base + 4) & M32)
        em.fast[addr] = f
        em.next[addr] = addr + sz
        n += 1
    return n


class EDMA:
    """TCD de l'eDMA en MMIO ; une chaîne démarrée (CSR.START) s'exécute entièrement, tout de suite."""

    def __init__(self, uc):
        self.uc = uc
        self.regs = bytearray(0x1000)
        self.log = []                   # (canal, source, destination, octets)
        self.starts = []
        self.csr_reads = 0
        uc.mem_unmap(0xfc045000, 0x1000)
        uc.mmio_map(0xfc045000, 0x1000, self._read, None, self._write, None)

    def _read(self, uc, off, size, ud):
        if off % 32 == 0x1e:
            self.csr_reads += 1
        return int.from_bytes(self.regs[off:off + size], "big")

    def _write(self, uc, off, size, value, ud):
        self.regs[off:off + size] = (value & ((1 << (8 * size)) - 1)).to_bytes(size, "big")
        ch, o = divmod(off, 32)
        if ch < 64 and o <= 0x1e < o + size:
            csr = int.from_bytes(self.regs[ch * 32 + 0x1e:ch * 32 + 0x20], "big")
            if csr & 1:
                self.starts.append(ch)
                self.run(ch)

    def run(self, ch):
        uc = self.uc
        b = ch * 32
        for _ in range(64):
            (saddr, attr, soff, nbytes, slast, daddr, citer, doff, dlast,
             biter, csr) = struct.unpack(">IHhIiIHhiHH", bytes(self.regs[b:b + 32]))
            ssize = (1, 2, 4, 0, 16, 32)[(attr >> 8) & 7]
            dsize = (1, 2, 4, 0, 16, 32)[attr & 7]
            smod, dmod = (attr >> 11) & 31, (attr >> 3) & 31
            n = citer & (0x1ff if citer & 0x8000 else 0x7fff)
            src0, dst0, tot = saddr, daddr, 0
            for _it in range(n):
                data = bytearray()
                left = nbytes
                while left > 0:
                    data += uc.mem_read(saddr, ssize)
                    left -= ssize
                    ns = (saddr + soff) & 0xffffffff
                    if smod:
                        m = (1 << smod) - 1
                        ns = (saddr & ~m) | (ns & m)
                    saddr = ns
                p = 0
                while p < len(data):
                    uc.mem_write(daddr, bytes(data[p:p + dsize]))
                    p += dsize
                    nd = (daddr + doff) & 0xffffffff
                    if dmod:
                        m = (1 << dmod) - 1
                        nd = (daddr & ~m) | (nd & m)
                    daddr = nd
                tot += nbytes
            self.log.append((ch, src0, dst0, tot))
            if csr & 0x10:              # ESG : charge le TCD suivant
                nxt = bytes(uc.mem_read(dlast & 0xffffffff, 32))
                self.regs[b:b + 32] = nxt
                if struct.unpack(">H", nxt[30:32])[0] & 1:
                    continue
                return
            saddr = (saddr + slast) & 0xffffffff
            daddr = (daddr + dlast) & 0xffffffff
            csr = (csr & ~1) | 0x80     # DONE
            self.regs[b:b + 32] = struct.pack(">IHhIiIHhiHH", saddr, attr, soff, nbytes, slast, daddr, biter,
                                              doff, dlast, biter, csr)
            return
        raise RuntimeError("chaîne eDMA sans fin")


class OutRig:
    """La vraie interruption audio avec l'étage de sortie (voir le module). main_os : section 3, éventuellement
    modifiée (plus sa charge utile) ; extra_code : [(va, taille)] du code ajouté où chercher de l'EMAC."""

    def __init__(self, main_os, bpm=120, extra_code=(), fast=True):
        e = self.e = mcengine.Engine(main_os, extra_code=extra_code)
        uc = self.uc = e.uc
        e.emac.on_load = None
        if fast:
            speed_up_emac(e.emac)
        orig = uc.hook_add
        hk = []

        def rec(htype, cb, *a, **kw):           # seqrig saute l'étage de sortie par des hooks à ces adresses
            h = orig(htype, cb, *a, **kw)
            if kw.get("begin") in OUTPUT_FNS:
                hk.append(h)
            return h
        uc.hook_add = rec
        try:
            self.rig = seqrig.Rig(e, bpm=bpm)
        finally:
            del uc.hook_add
        for h in hk:
            uc.hook_del(h)
        self._alias()
        self.dma = EDMA(uc)
        e.call(0x4005974c)                      # init de l'OS : effets, puis voix
        e.call(0x400449ce)                      # réglages par défaut (0x404e9b54 = 2 : son interne -> sortie)
        assert not e.unmapped, e.unmapped[:4]
        self._kit()

    def _alias(self):
        """0x42000000..0x43000000 (avec cache) et 0x4a000000.. (sans) : la même mémoire."""
        uc = self.uc
        data = bytes(uc.mem_read(0x42000000, 0x01000000))
        uc.mem_unmap(0x42000000, 0x00400000)
        uc.mem_unmap(0x42400000, 0x00c00000)
        self._ddr = ctypes.create_string_buffer(0x01000000)
        ptr = ctypes.addressof(self._ddr)
        uc.mem_map_ptr(0x42000000, 0x01000000, UC_PROT_ALL, ptr)
        uc.mem_map_ptr(0x4a000000, 0x01000000, UC_PROT_ALL, ptr)
        uc.mem_write(0x42000000, data)

    def _kit(self):
        e, rig, w16 = self.e, self.rig, self.w16
        e.call(0x4005a274)                      # tables de recherche des descripteurs (construites au démarrage)
        for t in range(6):
            e.call(0x400618f2, rig.sound(t), t)  # son par défaut de l'OS pour la piste t
            w16(KIT + 16 + 2 * t, 100 << 8)     # Track Level 100 (défaut du descripteur 0x4010ded8)
        fx = KIT + 628
        self.uc.mem_write(fx, bytes(66))
        for slot, v in ((9, 23), (10, 32), (11, 42), (12, 64)):   # descripteurs 0x4010e4f8..0x4010e5a0
            w16(fx + 2 * slot, v << 8)
        e.call(0x400595a8, KIT)                 # l'OS charge le kit : cibles et lissage
        for t in range(6):                      # niveaux de piste posés aussi dans le lissage (pas de rampe)
            self.uc.mem_write(seqrig.SMOOTH + 4 * t, struct.pack(">i", (100 << 8) << 16))
            w16(seqrig.PARAMS + 2 * t, 100 << 8)

    # --- accès ---
    def w16(self, a, v):
        self.uc.mem_write(a, struct.pack(">H", v & 0xffff))

    def r32s(self, a, n):
        return np.frombuffer(bytes(self.uc.mem_read(a, 4 * n)), ">i4").astype(np.int64)

    def param(self, t, slot, value):
        """Paramètre d'une piste 0..5, ou des effets (t = 6), en valeur affichée 0..127 (posé sans lissage)."""
        if t == 6:
            j = (0xe + 0x42 * 6 + 2 * slot) // 2
            v = struct.pack(">h", value << 8)
            self.uc.mem_write(KIT + 628 + 2 * slot, v)
            self.uc.mem_write(seqrig.TARGETS + 2 * j, v)
            self.uc.mem_write(seqrig.SMOOTH + 4 * j, struct.pack(">i", (value << 8) << 16))
            self.uc.mem_write(seqrig.PARAMS + 2 * j, v)
        else:
            self.rig.param(t, slot, value << 8)

    def target(self, t, slot, value):
        """Comme un potard tourné : seule la cible change, le lissage de l'OS (0x40058474) y glisse."""
        j = (0xe + 0x42 * t + 2 * slot) // 2
        self.uc.mem_write(seqrig.TARGETS + 2 * j, struct.pack(">h", value << 8))

    def block(self):
        """Un bloc : interruption jusqu'au jsr de 0x40059382, puis ce jsr (fonction audio et étage de sortie)."""
        rig, uc = self.rig, self.uc
        rig.w32(seqrig.NOW, rig.now)
        fp0 = seqrig.ISTACK - 4
        uc.reg_write(mk.UC_M68K_REG_A6, fp0)
        uc.reg_write(mk.UC_M68K_REG_A7, fp0 - 168)
        uc.reg_write(mk.UC_M68K_REG_D7, 0)
        start = 0x40058ca0
        if bytes(uc.mem_read(start, 6)) != seqrig.ISR_FIRST:
            self.e.emac.macsr = 0x20
            start += 6
        uc.emu_start(start, AUDIO_CALL, count=5_000_000)
        pc = uc.reg_read(mk.UC_M68K_REG_PC)
        assert pc == AUDIO_CALL and not self.e.unmapped, (hex(pc), self.e.unmapped[:4])
        fp = uc.reg_read(mk.UC_M68K_REG_A6)
        fr = [rig.r32(fp - 44 + 4 * k) for k in range(11)]
        info = dict(trig=fr[4], rel=fr[5])
        regs = [getattr(mk, f"UC_M68K_REG_{r}") for r in ("D2", "D3", "D4", "D5", "D6", "D7",
                                                           "A2", "A3", "A4", "A5", "A6")]
        sp0 = uc.reg_read(mk.UC_M68K_REG_A7)
        r0 = [uc.reg_read(r) for r in regs]
        uc.emu_start(AUDIO_CALL, AUDIO_CALL + 6, count=50_000_000)
        pc = uc.reg_read(mk.UC_M68K_REG_PC)
        assert pc == AUDIO_CALL + 6 and not self.e.unmapped, (hex(pc), self.e.unmapped[:4])
        assert uc.reg_read(mk.UC_M68K_REG_A7) == sp0 and [uc.reg_read(r) for r in regs] == r0, \
            "fonction audio : pile ou registres non rendus"
        info["out"] = np.frombuffer(bytes(uc.mem_read(0x80001858, 6 * 0x80)), ">i4").reshape(6, 32).astype(np.int64)
        rig.blocks.append(None)
        rig.now += rig.blk
        idx = rig.r32(seqrig.ISTACK - 4 - 44 + 40)       # demi-anneau écrit par ce bloc (fp-4)
        info["ring"] = self.r32s(RING + 256 * idx, 64).reshape(32, 2)
        info["usb"] = self.r32s(USB_MIX, 64).reshape(32, 2)
        return info

    def lines(self):
        """Lignes du delay et de la reverb en DDR (octets)."""
        return b"".join(bytes(self.uc.mem_read(a, n)) for a, n in LINES)

    def emac_state(self):
        em = self.e.emac
        return repr((list(em.acc), em.macsr))


class Pattern:
    """Un trig sur chaque pas des pistes données (120 BPM), daté comme le séquenceur (heure musicale exacte) ;
    every : un trig tous les `every` blocs au lieu de chaque pas."""

    def __init__(self, rig, tracks=range(6), first=2, every=None):
        self.r, self.tracks = rig, list(tracks)
        for t in self.tracks:
            rig.rig.set_step(t, 0, vel=100, length=seqrig.LEN_1_16)
        self.next = rig.rig.now + first * rig.rig.blk
        self.every = every * rig.rig.blk if every else seqrig.STEP

    def tick(self):
        """À appeler avant chaque bloc : programme le trig qui tombe dans le bloc suivant."""
        s = self.r.rig
        while self.next < s.now + 2 * s.blk:
            for t in self.tracks:
                s.schedule_step(t, 0, self.next)
            self.next += self.every
