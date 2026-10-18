#!/usr/bin/env python3
"""Horloge MIDI sortante et anneau d'octets plein : l'attente active à IPL 7 de 0x40001232, et un correctif de 2 octets.

Le vrai code de l'OS 1.13 (Unicorn) : l'interruption du top d'horloge 0x4005420c (corps à IPL 7) envoie 0xF8 par
0x40082512 -> 0x400824c4 -> 0x40001564 -> 0x40001232. Quand un message part par le DMA (0x4049dca0 non nul),
0x40001232 range l'octet dans l'anneau de 1 Kio *0x4049dcac ; s'il y a déjà 1024 octets (0x4049dccc > 1023), il
attend (0x4000123a..0x40001246) qu'une interruption de niveau 4 (émission UART 0x40000e8c, fin de DMA 37) le vide.
À IPL 7, aucune ne peut venir : la machine reste dans cette boucle (son : l'anneau DMA audio tourne en rond).

On joue la situation d'une surcharge prolongée (niveau 4 jamais servi : 0x4049dca0 reste non nul, l'anneau ne se vide
pas) : N tops d'horloge de suite. OS d'origine : le 1025e top ne revient pas (limite d'instructions, PC dans la boucle,
SR à IPL 7). Correctif 0x40001246 : 6ef2 (bgt.s 0x4000123a) -> 6e7e (bgt.s 0x400012c6, sortie sans rien ranger) :
l'octet est jeté et le top revient. Contrôles : avant d'être plein, l'anneau, ses index et le registre d'émission de
l'UART sont les mêmes octet pour octet avec et sans correctif (chemin direct UART libre, chemin anneau) ; aucun tweak
n'écrit 0x40001246..47.

    python3 preuve_midi_horloge.py
"""
import json
import pathlib
import struct
import sys

sys.path.insert(0, "/home/user/Modded-Cycles/tools/emu")
sys.path.insert(0, "/home/user/Modded-Cycles/tools")
import test_sdvintage as T      # noqa: E402
from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UcError   # noqa: E402
from unicorn import m68k_const as mk  # noqa: E402

CYCLES = "/home/user/Modded-Cycles/firmware/model-cycles_OS1.13.syx"
DEV = pathlib.Path("/home/user/Modded-Cycles/tweaks/model-cycles_OS1.13")
BASE = 0x40000400
TICK, TICK_RTE = 0x4005420c, 0x40054288
SPIN = (0x4000123a, 0x40001248)
RING = 0x4a3e0000
FIX = (0x40001246, bytes.fromhex("6ef2"), bytes.fromhex("6e7e"))
FAIL = []


def check(ok, msg):
    print(("  ok   " if ok else "  ÉCHEC ") + msg)
    if not ok:
        FAIL.append(msg)


class Rig:
    def __init__(self, img):
        uc = self.uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
        uc.ctl_set_cpu_model(mk.UC_CPU_M68K_ANY)
        uc.mem_map(0x40000000, 0x01000000)
        uc.mem_map(0x4a000000, 0x00400000)
        uc.mem_map(0xfc000000, 0x00100000)
        uc.mem_map(0xec000000, 0x00100000)
        uc.mem_map(0x90000000, 0x00010000)
        uc.mem_write(BASE, bytes(img))
        w = self.w32
        w(0x40fe4228, 1)                  # sortie MIDI prête
        uc.mem_write(0x404e9b50, b"\x00\x00\x01")   # OUT (pas THR), 0x404e9b52 : ports = DIN
        w(0x40a70148, 1)                  # envoi d'horloge activé
        w(0x40a78630, 0)
        uc.mem_write(0x40a788e6, b"\x00")
        w(0x4049dcac, RING)
        for a in (0x4049dca0, 0x4049dcc4, 0x4049dcc8, 0x4049dccc):
            w(a, 0)

    def w32(self, a, v):
        self.uc.mem_write(a, struct.pack(">I", v & 0xffffffff))

    def r32(self, a):
        return struct.unpack(">I", self.uc.mem_read(a, 4))[0]

    def tick(self, limit=200_000):
        """Une interruption du top d'horloge ; True si elle arrive à son rte."""
        sp = 0x9000f000
        self.uc.reg_write(mk.UC_M68K_REG_SR, 0x2500)     # entrée d'interruption de niveau 5 (SR avant SP)
        self.uc.reg_write(mk.UC_M68K_REG_A7, sp)
        try:
            self.uc.emu_start(TICK, TICK_RTE, count=limit)
        except UcError as e:
            return f"erreur {e}"
        return self.uc.reg_read(mk.UC_M68K_REG_PC) == TICK_RTE

    def state(self):
        return (bytes(self.uc.mem_read(RING, 1024)), self.r32(0x4049dcc8), self.r32(0x4049dccc),
                bytes(self.uc.mem_read(0xec07400c, 1)), bytes(self.uc.mem_read(0xfc044019, 1)))


def main():
    stock = T.main_os_from_syx(CYCLES)
    off = FIX[0] - BASE
    check(stock[off:off + 2] == FIX[1], f"octets d'origine en {FIX[0]:#x} : {stock[off:off + 2].hex()}")
    fixed = bytearray(stock)
    fixed[off:off + 2] = FIX[2]

    # aucun tweak n'écrit ces 2 octets
    hits = []
    for f in sorted(DEV.glob("*.json")):
        if f.name == "device.json":
            continue
        t = json.loads(f.read_text(encoding="utf-8"))
        for wr in t.get("writes", []):
            o, n = wr["off"], len(wr["new"]) // 2
            if o < off + 2 and off < o + n:
                hits.append(f.name)
    check(not hits, f"aucun tweak n'écrit {FIX[0]:#x}..{FIX[0] + 1:#x} ({len(list(DEV.glob('*.json'))) - 1} fichiers lus)"
          + (f" : {sorted(set(hits))}" if hits else ""))

    # 1. chemin direct : rien ne part par le DMA, l'UART est libre -> l'octet va droit dans le registre d'émission
    for label, img in (("origine", stock), ("corrigé", fixed)):
        r = Rig(img)
        r.uc.mem_write(0xec074004, b"\x04")
        ok = r.tick()
        check(ok is True and r.state()[3] == b"\xf8" and r.r32(0x4049dccc) == 0,
              f"{label} : UART libre, 0xF8 écrit dans 0xec07400c, anneau vide")

    # 2. surcharge : un message reste « en cours » par le DMA, le niveau 4 n'est jamais servi
    res = {}
    for label, img in (("origine", stock), ("corrigé", fixed)):
        r = Rig(img)
        r.w32(0x4049dca0, 2)
        r.uc.mem_write(0xec074004, b"\x00")
        states, n_ok = [], 0
        for k in range(1, 1027):
            ok = r.tick()
            if ok is not True:
                pc = r.uc.reg_read(mk.UC_M68K_REG_PC)
                sr = r.uc.reg_read(mk.UC_M68K_REG_SR)
                res[label] = (k, ok, pc, sr, states)
                break
            n_ok += 1
            states.append(r.state())
        else:
            res[label] = (None, True, None, None, states)
    k, ok, pc, sr, st = res["origine"]
    check(k == 1025 and SPIN[0] <= pc < SPIN[1] and (sr >> 8) & 7 == 7,
          f"origine : 1024 tops rangés, le 1025e ne revient pas (PC {pc:#x} dans 0x4000123a..46, SR {sr:#06x} : IPL 7)"
          if pc else f"origine : inattendu {res['origine'][:4]}")
    k2, ok2, _, _, st2 = res["corrigé"]
    check(k2 is None and len(st2) == 1026, "corrigé : les 1026 tops reviennent (le 1025e et le 1026e jettent leur octet)")
    check(st2[:1024] == st[:1024], "corrigé : les 1024 premiers tops laissent anneau, index, compte et registres "
          "identiques à l'origine, top après top")
    check(st2[1025][2] == 1024 and st2[1025][0] == st2[1023][0],
          "corrigé : anneau plein inchangé (compte 1024) après les octets jetés")
    check(all(x == b"\xf8" for x in (st2[1023][0][i:i + 1] for i in range(1024))), "l'anneau contient 1024 x 0xF8")

    print("\nTOUT OK" if not FAIL else f"\n{len(FAIL)} ÉCHEC(S)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
