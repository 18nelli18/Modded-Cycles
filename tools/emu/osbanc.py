"""Banc de l'interruption audio complète du Modded Cycles OS (os.json, notes/75, notes/77) : le vrai code, du début de
l'interruption de rendu (0x40058ca0, après la sauvegarde du contexte EMAC) jusqu'après la mise en file de l'envoi à
l'USB (0x40059398), en passant par le vrai appel de la fonction audio (0x40059382 : la sonde des moteurs du Syntakt,
le régulateur), la boucle des voix (Model-TG, nos machines), Volume + Dist, et l'étage de sortie : mixeur, envois,
delay, reverb, master, anneau du codec.

Repris du banc de l'étude d'optimisation de l'OS (17-18/10/2026, tag etude-optimisation-os-2026-10-18 :
optim/sortie/banc.py, essai/sources/preuves/banc_essai.py), pour l'OS complet :
  - la SDRAM vue deux fois, avec cache (0x40000000..) et sans (0x48000000..) : un seul tampon projeté aux deux
    adresses, comme le matériel (lignes du delay 0x4a400000, de la reverb 0x4a340000 et 0x4a3d0000, anneau du codec
    0x4a3ed080, zone d'échantillons de Model-TG, charge utile 0x46700000) ;
  - l'eDMA simulé (TCD en MMIO, 0xfc045000) : un départ (CSR.START) exécute toute la chaîne tout de suite ;
  - l'initialisation de l'OS (0x4005974c : effets puis voix), ses réglages par défaut (0x400449ce), un kit par
    défaut chargé par l'OS lui-même (0x400595a8), comme l'étude.

    b = OsBanc(fw)            # fw : test_modal.Fw de l'OS (ou d'une variante)
    b.rig.set_step(t, 0, ...); b.rig.schedule_step(t, 0, b.rig.now + b.rig.blk)
    info = b.block()          # out (sortie des 6 voix), ring (anneau du codec), usb (copie du master)
"""
import ctypes
import struct

import numpy as np
from unicorn import UC_PROT_ALL
from unicorn import m68k_const as mk

import seqrig as S

RING = 0x4a3ed080            # anneau du codec (vue sans cache)
USB_MIX = 0x40fe4b90         # copie du master pour l'USB (32 trames stéréo)
OUTPUT_FNS = (0x40056f58, 0x40056ea8, 0x400567ba)
AUDIO_CALL, AFTER_CALL, AFTER_USB = 0x40059382, 0x40059388, 0x40059398
MODAL_RAM = (0x46800000, 0x00100000)
REGS = ("D2", "D3", "D4", "D5", "D6", "D7", "A2", "A3", "A4", "A5", "A6")


class EDMA:
    """TCD de l'eDMA en MMIO ; une chaîne démarrée (CSR.START) s'exécute entièrement, tout de suite."""

    def __init__(self, uc):
        self.uc = uc
        self.regs = bytearray(0x1000)
        self.log = []                   # (canal, source, destination, octets)
        self.starts = []
        uc.mem_unmap(0xfc045000, 0x1000)
        uc.mmio_map(0xfc045000, 0x1000, self._read, None, self._write, None)

    def _read(self, uc, off, size, ud):
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
                ncsr = struct.unpack(">H", nxt[30:32])[0]
                if ncsr & 1:
                    continue
                return
            saddr = (saddr + slast) & 0xffffffff
            daddr = (daddr + dlast) & 0xffffffff
            csr = (csr & ~1) | 0x80     # DONE
            self.regs[b:b + 32] = struct.pack(">IHhIiIHhiHH", saddr, attr, soff, nbytes, slast, daddr, biter,
                                              doff, dlast, biter, csr)
            return
        raise RuntimeError("chaîne eDMA sans fin")


class OsBanc:
    def __init__(self, fw, bpm=120):
        e = self.e = fw.engine()
        uc = self.uc = e.uc
        S.ensure_map(uc, *MODAL_RAM)
        self._alias()
        orig, stubs = uc.hook_add, []

        def rec(htype, cb, *a, **kw):           # les crochets qui sautent l'étage de sortie (seqrig) : retirés
            h = orig(htype, cb, *a, **kw)
            if kw.get("begin") in OUTPUT_FNS:
                stubs.append(h)
            return h
        uc.hook_add = rec
        try:
            self.rig = S.Rig(e, bpm=bpm, keep=fw.keep)
        finally:
            del uc.hook_add
        for h in stubs:
            uc.hook_del(h)
        self.dma = EDMA(uc)
        e.call(0x4005974c)                      # init de l'OS : effets, puis voix
        e.call(0x400449ce)                      # réglages par défaut (0x404e9b54 = 2 : son interne -> sortie)
        assert not e.unmapped, e.unmapped[:4]
        self._kit()
        self.clock = 10_000_000                 # minuteur DMA 0 : avance d'un bloc à chaque bloc
        self.syms = {k: int(v, 16) for k, v in getattr(fw, "mine", {}).get("symbols", {}).items()}

    def _alias(self):
        """0x40000000..0x48000000 et 0x48000000..0x50000000 : la même mémoire (avec et sans cache)."""
        uc = self.uc
        keep = []
        for lo, hi, _ in sorted(uc.mem_regions()):
            if 0x40000000 <= lo < 0x50000000:
                if lo < 0x48000000:
                    keep.append((lo, bytes(uc.mem_read(lo, hi + 1 - lo))))
                uc.mem_unmap(lo, hi + 1 - lo)
        self._ram = ctypes.create_string_buffer(0x08000000)
        ptr = ctypes.addressof(self._ram)
        uc.mem_map_ptr(0x40000000, 0x08000000, UC_PROT_ALL, ptr)
        uc.mem_map_ptr(0x48000000, 0x08000000, UC_PROT_ALL, ptr)
        for lo, data in keep:
            uc.mem_write(lo, data)

    def _kit(self):
        e, rig = self.e, self.rig
        e.call(0x4005a274)                      # tables de recherche des descripteurs (construites au démarrage)
        for t in range(6):
            s = rig.sound(t)
            e.call(0x400618f2, s, t)            # son par défaut de l'OS pour la piste t
            self.w16(S.KIT + 16 + 2 * t, 100 << 8)     # Track Level 100
        fx = S.KIT + 628
        self.uc.mem_write(fx, bytes(66))
        for slot, v in ((9, 23), (10, 32), (11, 42), (12, 64)):   # Delay Time, Fdbk, Reverb Size, Tone
            self.w16(fx + 2 * slot, v << 8)
        e.call(0x400595a8, S.KIT)               # l'OS charge le kit : cibles et lissage
        for t in range(6):                      # niveaux de piste : la cible, et le lissage déjà arrivé
            self.uc.mem_write(S.SMOOTH + 4 * t, struct.pack(">i", (100 << 8) << 16))
            self.w16(S.PARAMS + 2 * t, 100 << 8)

    def w16(self, a, v):
        self.uc.mem_write(a, struct.pack(">H", v & 0xffff))

    def r32s(self, a, n):
        return np.frombuffer(bytes(self.uc.mem_read(a, 4 * n)), ">i4").astype(np.int64)

    def param(self, t, slot, value):
        """Paramètre d'une piste 0..5 (valeur affichée 0..127, posée sans lissage), ou des effets (t = 6)."""
        if t == 6:
            j = (0xe + 0x42 * 6 + 2 * slot) // 2
            v = struct.pack(">h", value << 8)
            self.uc.mem_write(S.KIT + 628 + 2 * slot, v)
            self.uc.mem_write(S.TARGETS + 2 * j, v)
            self.uc.mem_write(S.SMOOTH + 4 * j, struct.pack(">i", (value << 8) << 16))
            self.uc.mem_write(S.PARAMS + 2 * j, v)
        else:
            self.rig.param(t, slot, value << 8)

    def block(self):
        """Un bloc : l'interruption de rendu jusqu'à l'appel de la fonction audio, le vrai appel, puis la mise en file
        de l'envoi à l'USB. Rend out (sortie des 6 voix après le gain), ring (le demi-anneau du codec écrit par ce
        bloc), usb (copie du master)."""
        rig, uc = self.rig, self.uc
        rig.w32(S.NOW, rig.now)
        uc.mem_write(0xfc07000c, struct.pack(">I", self.clock & 0xffffffff))
        self.clock += 90112
        fp0 = S.ISTACK - 4
        uc.reg_write(mk.UC_M68K_REG_A6, fp0)
        uc.reg_write(mk.UC_M68K_REG_A7, fp0 - 168)
        uc.reg_write(mk.UC_M68K_REG_D7, 0)
        start = 0x40058ca0
        if bytes(uc.mem_read(start, 6)) != S.ISR_FIRST:
            self.e.emac.macsr = 0x20
            start += 6
        uc.emu_start(start, AUDIO_CALL, count=5_000_000)
        assert uc.reg_read(mk.UC_M68K_REG_PC) == AUDIO_CALL and not self.e.unmapped, self.e.unmapped[:4]
        sp0 = uc.reg_read(mk.UC_M68K_REG_A7)
        regs0 = [uc.reg_read(getattr(mk, f"UC_M68K_REG_{r}")) for r in REGS]
        uc.emu_start(AUDIO_CALL, AFTER_CALL, count=100_000_000)
        assert uc.reg_read(mk.UC_M68K_REG_PC) == AFTER_CALL and not self.e.unmapped, self.e.unmapped[:4]
        regs1 = [uc.reg_read(getattr(mk, f"UC_M68K_REG_{r}")) for r in REGS]
        assert uc.reg_read(mk.UC_M68K_REG_A7) == sp0 and regs1 == regs0, "pile ou registres non rendus"
        uc.emu_start(AFTER_CALL, AFTER_USB, count=1_000_000)
        assert uc.reg_read(mk.UC_M68K_REG_PC) == AFTER_USB and not self.e.unmapped, self.e.unmapped[:4]
        info = dict(out=np.frombuffer(bytes(uc.mem_read(0x80001858, 6 * 0x80)), ">i4").reshape(6, 32)
                    .astype(np.int64))
        rig.now += rig.blk
        idx = rig.r32(S.ISTACK - 4 - 44 + 40)
        info["ring"] = self.r32s(RING + 256 * idx, 64).reshape(32, 2)
        info["usb"] = self.r32s(USB_MIX, 64).reshape(32, 2)
        return info
