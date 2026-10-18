"""Banc commun des preuves de l'essai : les MAIN OS lus dans les .syx livrés, et le banc de l'étage de sortie de
l'étude « sortie » (banc.py : vraie interruption audio de seqrig + mixeur, effets, codec, eDMA simulé) avec une
différence : le bloc passe par le VRAI appel de 0x40059382 (jsr 0x4005979e dans l'OS officiel, jsr m_probe dans
les fichiers d'essai), au lieu d'appeler 0x4005979e à part. La sonde du compteur tourne donc dans son contexte réel
(pile de l'interruption, argument fp-44 posé par l'OS), à chaque bloc.

Minuteur DMA 0 simulé (0xfc07000c) : avant chaque bloc, l'heure d'entrée m_t0 du compteur est posée comme si
m_entry l'avait notée (seqrig démarre en 0x40058ca0, après l'entrée), et le minuteur vaut m_t0 + DUR à la fin :
le compteur mesure, et affiche toutes les 750 blocs, dans les deux images d'essai.
"""
import hashlib
import json
import pathlib
import struct
import sys

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
ESSAI = HERE.parent
REPO = pathlib.Path("/home/user/Modded-Cycles")
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(REPO / "tools" / "emu"))

import numpy as np                          # noqa: E402
from unicorn import m68k_const as mk        # noqa: E402

import build                                # noqa: E402
import banc                                 # noqa: E402
import seqrig                               # noqa: E402

OFFICIAL = REPO / "firmware" / "model-cycles_OS1.13.syx"
OUT = pathlib.Path("/mnt/project-files/optimisation-os/essai")
FILES = {"reference": "model-cycles_OS1.13_essai-reference.syx", "optimise": "model-cycles_OS1.13_essai-optimise.syx"}
SYM = {k: int(v, 16) for k, v in json.loads((ESSAI / "symboles.json").read_text()).items()}
V = SYM["V"]
TIMER = 0xfc07000c
BLOCK_TICKS = 90112
DUR = 60000                                  # durée simulée d'un bloc (66 %)
# masques qui portent du code dans les images d'essai (pour l'EMAC émulé, mcengine extra_code)
CODE_MASKS = [(0x40167c50, 280), (0x40171a48, 192), (0x4016dab8, 192), (0x4016fae8, 192), (0x40189618, 272),
              (0x4018d918, 328), (0x40170c48, 192), (0x40186238, 272), (0x40185f48, 272)]
P1_STALE = (0x8000bc98, 0x8000bd98)          # sortie du saturateur, non réécrite par p1 (lue x 0)
QUIET = SYM["QUIET"]


def main_os(path):
    raw = pathlib.Path(path).read_bytes()
    stream, _ = build.unwrap(raw)
    c = build.container.parse(stream)
    s3 = next(s for s in c["sections"] if s["id"] == 3)
    return build.aplib.depack(c["blob"][s3["off"]:s3["off"] + s3["size"]])[0]


def images(out=OUT):
    """{nom : MAIN OS} : officiel, puis les deux fichiers livrés (relus dans les .syx)."""
    imgs = {"officiel": main_os(OFFICIAL)}
    dev = json.loads((REPO / "tweaks" / "model-cycles_OS1.13" / "device.json").read_text())
    assert hashlib.sha256(imgs["officiel"]).hexdigest() == dev["section_sha256"]
    for k, f in FILES.items():
        imgs[k] = main_os(pathlib.Path(out) / f)
    return imgs


def sha(b):
    return hashlib.sha256(b).hexdigest()


class Banc(banc.Banc):
    """banc.Banc, bloc passé par le vrai appel de 0x40059382."""

    def __init__(self, img, meter_clock=True, **kw):
        kw.setdefault("extra_code", CODE_MASKS)
        super().__init__(img=img, **kw)
        self.has_meter = img[0x40059382 - 0x40000400:0x40059384 - 0x40000400] == b"\x4e\xb9" and \
            int.from_bytes(img[0x40059384 - 0x40000400:0x40059388 - 0x40000400], "big") == SYM["m_probe"]
        self.clock = 10_000_000 if meter_clock else None
        self.at_call = None                     # appelé en 0x40059382, avant le jsr (mesures : début d'interruption)

    def block(self):
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
        if self.clock is not None:                      # ce que m_entry aurait noté à l'entrée
            if self.has_meter:
                uc.mem_write(V, struct.pack(">I", self.clock & 0xffffffff))
            uc.mem_write(TIMER, struct.pack(">I", (self.clock + DUR) & 0xffffffff))
            self.clock += BLOCK_TICKS
        uc.emu_start(start, 0x40059382, count=5_000_000)
        pc = uc.reg_read(mk.UC_M68K_REG_PC)
        assert pc == 0x40059382 and not self.e.unmapped, (hex(pc), self.e.unmapped[:4])
        fp = uc.reg_read(mk.UC_M68K_REG_A6)
        fr = [rig.r32(fp - 44 + 4 * k) for k in range(11)]
        six = lambda f: [f(t) for t in range(6)]
        info = dict(trig=fr[4], rel=fr[5], vel=six(lambda t: rig.r16(seqrig.VEL + 2 * t) >> 8),
                    gain=six(lambda t: rig.r16(seqrig.GAIN + 2 * t)))
        if self.at_call:
            self.at_call()
        sp0 = uc.reg_read(mk.UC_M68K_REG_A7)
        regs0 = [uc.reg_read(getattr(mk, f"UC_M68K_REG_{r}")) for r in ("D2", "D3", "D4", "D5", "D6", "D7",
                                                                          "A2", "A3", "A4", "A5", "A6")]
        uc.emu_start(0x40059382, 0x40059388, count=50_000_000)       # le vrai jsr : fonction audio (et sonde)
        pc = uc.reg_read(mk.UC_M68K_REG_PC)
        assert pc == 0x40059388 and not self.e.unmapped, (hex(pc), self.e.unmapped[:4])
        regs1 = [uc.reg_read(getattr(mk, f"UC_M68K_REG_{r}")) for r in ("D2", "D3", "D4", "D5", "D6", "D7",
                                                                          "A2", "A3", "A4", "A5", "A6")]
        assert uc.reg_read(mk.UC_M68K_REG_A7) == sp0 and regs1 == regs0, "pile ou registres non rendus"
        v32 = lambda t, o: rig.r32(seqrig.VOICE0 + seqrig.VSTRIDE * t + o, True)
        info.update(machine=six(lambda t: v32(t, 0)),
                    out=np.frombuffer(bytes(uc.mem_read(0x80001858, 6 * 0x80)), ">i4").reshape(6, 32).astype(np.int64))
        rig.blocks.append(None)
        rig.now += rig.blk
        idx = rig.r32(seqrig.ISTACK - 4 - 44 + 40)
        info["ring"] = self.r32s(banc.RING + 256 * idx, 64).reshape(32, 2)
        info["usb"] = self.r32s(banc.USB_MIX, 64).reshape(32, 2)
        return info

    def quiet(self):
        """Compteurs de blocs faibles de l'arrêt des voix muettes (image optimisée seulement)."""
        return list(self.uc.mem_read(QUIET, 6))

    def meter_name(self):
        return bytes(self.uc.mem_read(SYM["m_name"], 12)).split(b"\0")[0].decode()

    def snap(self, lines, p1=False):
        """SRAM entière (64 Ko ; sans 0x8000bc98..bd98 si p1), EMAC ; lignes en DDR (empreinte) si lines."""
        uc, em = self.uc, self.e.emac
        sram = bytearray(uc.mem_read(0x80000000, 0x10000))
        if p1:
            sram[P1_STALE[0] - 0x80000000:P1_STALE[1] - 0x80000000] = bytes(P1_STALE[1] - P1_STALE[0])
        s = [bytes(sram), repr((list(em.acc), em.macsr)).encode()]
        if lines:
            h = hashlib.sha256()
            for a, n in ((0x4a400000, 0x400000), (0x4a340000, 0x90000), (0x4a3d0000, 0x8000)):
                h.update(bytes(uc.mem_read(a, n)))
            s.append(h.digest())
        return s


STEP_BLOCKS = seqrig.STEP / (2 * 120 * 120)   # 187,5 blocs par pas (double croche) à 120 BPM


class Pattern:
    """Un trig sur chaque pas des pistes données (120 BPM), daté comme le séquenceur (heure musicale exacte)."""

    def __init__(self, b, tracks=range(6), first=2, every=None):
        self.b, self.tracks = b, list(tracks)
        for t in self.tracks:
            b.rig.set_step(t, 0, vel=100, length=seqrig.LEN_1_16)
        self.next = b.rig.now + first * b.rig.blk
        self.every = every * b.rig.blk if every else seqrig.STEP

    def tick(self):
        """À appeler avant chaque bloc : programme le trig qui tombe dans le bloc suivant."""
        rig = self.b.rig
        while self.next < rig.now + 2 * rig.blk:
            for t in self.tracks:
                rig.schedule_step(t, 0, self.next)
            self.next += self.every
