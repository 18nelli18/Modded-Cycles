"""Émulation (Unicorn, m68k « ANY » = ColdFire + EMAC corrigée) du moteur audio du Syntakt OS 1.42 (même section 7 que 1.41) :
le programme du processeur DSP (section 7 du .syx), et sa vraie boucle des 8 voix numériques,
bloc par bloc (32 trames, 48 kHz). Pendant de mcengine.py pour le Model:Cycles.

Aucune image n'est fournie : on passe la section 7 extraite de TON Syntakt_OS1.42.syx
(tools/emu/syntakt.py). Contrat décodé le 29/09/2026, voir notes/16 :
- section 7 chargée à 0x40000400 ; au démarrage, 0x4004f6e0..0x40057670 est copié en SRAM
  0x80000000 et 0x40057670..0x4005df10 en 0x80008000 (le reste de la SRAM est mis à zéro) ;
- boucle des voix 0x40004324(out, params, trig_mask, release_mask), MACSR = 0xa0 pendant la boucle ;
- voix i à 0x80000000 + 1800*i ; paramètres de la piste i à params + 142*i, type de machine
  (0..45) en +0x3e, traduit en moteur 0..11 par la table d'octets 0x40014950 ;
- update[m](pmod, voix, params + 0x1c + 142*i) puis render[m](out + 128*i, voix) ;
  tables 0x40014920 (update) et 0x400148f0 (render) ; pmod de la piste i à 0x80008150 + 4*i.
"""
import hashlib
import os
import struct
import tempfile

import numpy as np
from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_MEM_UNMAPPED, UC_HOOK_CODE
from unicorn import m68k_const as mk

import emac

BASE = 0x40000400
VOICE_LOOP = 0x40004324
VOICE_RESET = 0x40003ee0         # remise à zéro d'une voix (appelée au changement de machine)
VOICE_PREP = 0x40002544          # appelée avant chaque remise à zéro par l'init (0x40000fd6)
VOICE_BUF, VOICE_BUF_OFF = 0x80008a60, 0x56c   # voix+0x56c -> petit tampon SRAM de 0x30 o par voix
VOICE0, VSTRIDE = 0x80000000, 1800
PMOD = 0x80008150
TSTRIDE, MTYPE_OFF, UPD_OFF = 142, 0x3e, 0x1c
DATA_COPIES = ((0x4004f6e0, 0x40057670, 0x80000000), (0x40057670, 0x4005df10, 0x80008000))
CODE_RANGE = (BASE, 0x4004f6e0)
UPDATE_TAB, RENDER_TAB, MAP_TAB = 0x40014920, 0x400148f0, 0x40014950
# zone à nous, hors de la mémoire du programme : paramètres, sorties, adresse de retour
SCRATCH = 0x50000000
PARAMS, OUT, STOP = SCRATCH, SCRATCH + 0x1000, SCRATCH + 0x2000
STACK = 0x90010000
N_VOICES = 8
# types de machine (index de la table des noms de l'interface, section 3 à 0x4022aefc + 35*4)
MACHINES = {"BD MODERN": 0, "SD BASIC": 1, "CY ALLOY": 2, "PC CARBON": 3, "SY TONE": 4,
            "SY CHORD": 5, "SD VINTAGE": 6, "CP VINTAGE": 7, "SY TOY": 36, "SY BITS": 37, "SY SWARM": 38}

# Paramètres de synthèse : mot 8.8 à params + 0x1c + 2*slot (même convention que le Cycles, p + 2*slot).
# Famille FM (types 0..7) : même disposition que les machines du Model:Cycles, plus OVER (notes/16).
SLOT = {"tune": 18, "p1": 19, "p2": 20, "p3": 21, "p4": 22, "punch": 23, "gate": 24, "decay": 25, "over": 26}
# SD VINTAGE : p1 INHM, p2 FCMP, p3 SWEP, p4 MENV ; défauts du descripteur de l'interface (sec3 0x4022ff78..)
SDVN_DEFAULTS = dict(tune=64, p1=0, p2=110, p3=74, p4=80, punch=0, gate=0, decay=33, over=0)

_EMAC_CACHE = {}


def _emac_instrs(image):
    key = hashlib.sha256(image).hexdigest()
    if key not in _EMAC_CACHE:
        fd, path = tempfile.mkstemp(suffix=".bin")
        try:
            os.write(fd, image)
            os.close(fd)
            _EMAC_CACHE[key] = emac.disasm(path, BASE, *CODE_RANGE)
        finally:
            os.unlink(path)
    return _EMAC_CACHE[key]


class Engine:
    def __init__(self, image):
        self.img = bytes(image)
        uc = self.uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
        uc.ctl_set_cpu_model(mk.UC_CPU_M68K_ANY)
        uc.mem_map(0x40000000, 0x04100000)     # SDRAM : image + BSS (jusqu'à 0x4404f980)
        uc.mem_map(0x80000000, 0x00020000)     # SRAM interne (voix, tables)
        uc.mem_map(SCRATCH, 0x00010000)
        uc.mem_map(0x90000000, 0x00020000)     # pile
        uc.mem_write(BASE, self.img)
        uc.mem_write(STOP, b"\x4e\x71\x4e\x71")
        for lo, hi, dst in DATA_COPIES:          # ce que fait le démarrage (0x400004bc)
            uc.mem_write(dst, self.img[lo - BASE:hi - BASE])
        self.unmapped = []
        uc.hook_add(UC_HOOK_MEM_UNMAPPED, self._unmapped)
        self.emac = emac.EMAC(uc)
        self.n_emac = self.emac.install(_emac_instrs(self.img))
        for t in range(N_VOICES):                # init des voix, comme 0x40000fd6..0x40001014
            self.call(VOICE_PREP)
            v = VOICE0 + VSTRIDE * t
            uc.mem_write(v + VOICE_BUF_OFF, struct.pack(">I", VOICE_BUF + 0x30 * t))
            self.call(VOICE_RESET, v)
        self.params = [bytearray(TSTRIDE) for _ in range(N_VOICES)]
        self.pmod = [0] * N_VOICES
        self.instructions = None

    def _unmapped(self, uc, access, addr, size, value, ud):
        self.unmapped.append((uc.reg_read(mk.UC_M68K_REG_PC), addr))
        return False

    def solo(self, track):
        """Seule la voix `track` est calculée : les autres reçoivent un moteur hors bornes (> 11), que la
        boucle saute tant qu'elles ne sont pas déclenchées (même astuce que mcengine.solo)."""
        for t in range(N_VOICES):
            if t != track:
                v = VOICE0 + VSTRIDE * t
                self.uc.mem_write(v, struct.pack(">II", 12, 12))

    def call(self, fn, *args):
        sp = STACK - 0x200
        self.uc.mem_write(sp, struct.pack(">I" + "I" * len(args), STOP, *[a & 0xffffffff for a in args]))
        self.uc.reg_write(mk.UC_M68K_REG_A7, sp)
        self.uc.emu_start(fn, STOP, count=5_000_000)
        return self.uc.reg_read(mk.UC_M68K_REG_D0)

    def machine(self, t, name_or_type):
        m = MACHINES.get(name_or_type, name_or_type)
        self.params[t][MTYPE_OFF] = m & 0xff

    def set(self, t, **kw):
        """Paramètres de synthèse en valeurs d'interface (0..127, TUNE 40..88), écrits en 8.8."""
        for k, v in kw.items():
            self.u16(t, UPD_OFF + 2 * SLOT[k], int(round(v * 256)))

    def u8(self, t, off, v):
        self.params[t][off] = v & 0xff

    def u16(self, t, off, v):
        struct.pack_into(">H", self.params[t], off, v & 0xffff)

    def note(self, t, semis):
        """Note du trig, en demi-tons << 16 (même convention que le Cycles, à vérifier)."""
        self.pmod[t] = int(round(semis * 65536))

    def count_instructions(self):
        self.instructions = 0

        def hk(uc, a, s, u):
            self.instructions += 1
        self.uc.hook_add(UC_HOOK_CODE, hk)

    def _write(self):
        for t in range(N_VOICES):
            self.uc.mem_write(PARAMS + TSTRIDE * t, bytes(self.params[t]))
            self.uc.mem_write(PMOD + 4 * t, struct.pack(">i", self.pmod[t]))

    def block(self, trig_mask=0, release_mask=0):
        self._write()
        sp = STACK - 0x100
        self.uc.mem_write(sp, struct.pack(">IIIII", STOP, OUT, PARAMS, trig_mask, release_mask))
        self.uc.reg_write(mk.UC_M68K_REG_A7, sp)
        self.uc.emu_start(VOICE_LOOP, STOP, count=20_000_000)
        raw = self.uc.mem_read(OUT, N_VOICES * 0x80)
        return np.frombuffer(bytes(raw), dtype=">i4").reshape(N_VOICES, 32).astype(np.int64)

    def render(self, blocks, trig_at=(0,), track=0, on_block=None):
        out = []
        for b in range(blocks):
            if on_block:
                on_block(self, b)
            out.append(self.block((1 << track) if b in trig_at else 0)[track])
        return np.concatenate(out)


def wav(path, x, sr=48000):
    import wave
    y = np.asarray(x, dtype=np.float64)
    peak = np.max(np.abs(y)) or 1
    y = (y / peak * 0.9 * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(y.tobytes())
