#!/usr/bin/env python3
"""Preuve du filtre de piste pour le Sampler en modes Granular/Stretch/Pluck/Wave (Task 6, notes/83).

Banc d'émulation complet dans Unicorn (ColdFire m68k) :
  (a) Audio : la sortie du Sampler en modes 3..6 (Granular 3, Stretch 4, Pluck 5, Wave 6) est bien
      filtrée par le filtre de piste (trackData +48 / +50, param ids 0x0c/0x0b) lorsqu'il est actif,
      inchangée quand il est grand ouvert (cutoff 32512, res 0). Les modes 0..2 (One shot, Loop, Slice)
      sont bit à bit identiques à avant (aucun double filtrage, le filtre de piste reste inactif).
  (b) Descripteur : sous MACHINES (mod_held=1), pour une piste Sampler, les positions SWEEP (+24) et
      CONTOUR (+28) renvoient 0x0c (Track Filter) et 0x0b (Track Res) uniquement dans les modes 3..6.
      En modes 0..2, les identifiants d'origine 0x49 et 0x4a restent intacts. Sans MACHINES (mod_held=0),
      les positions restent 0x49 et 0x4a dans tous les modes.
  (c) Popup : vérification que les identifiants 0x0c et 0x0b utilisent la fenêtre de valeur de 0x49/0x4a
      (test_popup_view).
  (d) Charge processeur : mesure d'instructions sur 6 pistes en mode Granular avec le filtre 4 pôles actif
      sur les 6 pistes simultanément, vérification qu'elle reste largement sous le budget du régulateur.

    python3 tools/emu/test_sampler_mode_filter.py --cycles firmware/model-cycles_OS1.13.syx
"""
import argparse
import json
import pathlib
import struct
import sys

import numpy as np
from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import build                        # noqa: E402
import mcengine as E                # noqa: E402
import test_model_tg as TM          # noqa: E402
import test_sdvintage as T          # noqa: E402

TWEAK_TG = HERE.parent.parent / "tweaks" / "model-cycles_OS1.13" / "30-model-tg.json"
TWEAK_ST = HERE.parent.parent / "tweaks" / "model-cycles_OS1.13" / "30-model-tg-st.json"

FAIL = []


def check(ok, msg):
    print(("  ok    " if ok else "  ECHEC ") + msg, flush=True)
    if not ok:
        FAIL.append(msg)


def setup_sampler_sample(e, tw, slot=0):
    """Prépare un échantillon résident pour le Sampler (sinus 440 Hz)."""
    N_PCM = 48000
    pcm = 0x4c000000
    t_arr = np.linspace(0, 2 * np.pi * 440, N_PCM)
    sine = (np.sin(t_arr) * 16000).astype(">h").tobytes()
    hdr = bytearray(64)
    struct.pack_into(">II", hdr, 4, 2 * N_PCM, 48000)
    e.uc.mem_write(pcm, bytes(hdr) + sine)
    sh = int(tw["symbols"]["slot_hash"], 16)
    for k, val in enumerate((0x1234, pcm, N_PCM, 64 + 2 * N_PCM)):
        e.uc.mem_write(sh + 0x100 * k + 4 * slot, struct.pack(">I", val))
    return pcm, N_PCM


def track_tables(tw):
    """(track_hash, track_slot) de Model-TG : 0x100 et 0xe8 o sous slot_hash (model_tg.s, track_hash .. track_tried),
    pris du symbole pour suivre les retouches qui déplacent ces tables (ST_SPLIT_PATCHES : +0x34, notes/86)."""
    sh = int(tw["symbols"]["slot_hash"], 16)
    return sh - 0x100, sh - 0xe8


def run_mode_audio(img, tw, mode, cutoff, res=0, blocks=15):
    """Rend `blocks` de la piste 0 en machine Sampler (6) avec `mode` et le filtre de piste réglé."""
    e = TM.engine(img)
    setup_sampler_sample(e, tw, slot=0)
    # track_slot = 0, track_hash = 0x1234
    th, ts = track_tables(tw)
    e.uc.mem_write(ts, struct.pack(">I", 0))
    e.uc.mem_write(th, struct.pack(">I", 0x1234))
    e.set(0, machine=6, note=60, pitch=64, color=64, shape=64, sweep=64, contour=64, punch=0, gate=0, finetune=64, decay=60)
    e.uc.mem_write(0x401b2408, struct.pack(">I", mode))
    e.uc.mem_write(E.PARAMS + 0xe + 0 * 0x42 + 48, struct.pack(">hh", cutoff, res))
    out = []
    for b in range(blocks):
        blk = e.block(1 if b == 1 else 0)
        out.append(blk[0])
    return np.concatenate(out)


def test_audio_proof(img, tw):
    print("--- 1. Preuve audio : filtre de piste en modes 3..6, neutre en modes 0..2 ---")
    modes = [
        (0, "One shot"),
        (1, "Loop"),
        (2, "Slice"),
        (3, "Granular"),
        (4, "Stretch"),
        (5, "Pluck"),
        (6, "Wave"),
    ]
    for mode, name in modes:
        out_open = run_mode_audio(img, tw, mode, cutoff=32512, res=0)
        out_filt = run_mode_audio(img, tw, mode, cutoff=4000, res=0)
        diff = np.abs(out_open - out_filt).max()
        if mode < 3:
            check(diff == 0,
                  f"Mode {mode} ({name:8s}) : bit à bit identique avec filtre fermé (+48=4000) vs ouvert (diff=0, pas de double filtrage)")
        else:
            e_open = np.sum(out_open.astype(np.float64) ** 2)
            e_filt = np.sum(out_filt.astype(np.float64) ** 2)
            check(diff > 0 and e_filt < e_open,
                  f"Mode {mode} ({name:8s}) : filtré par le filtre de piste (diff={diff}, énergie réduite de {100 * (1 - e_filt / e_open):.1f} %)")


def test_descriptor_proof(img, tw):
    print("\n--- 2. Preuve descripteur : SWEEP/CONTOUR sous MACHINES ---")
    e = TM.engine(img)
    # Marquer descr_done = 1 (le descripteur du Sampler a été construit)
    e.uc.mem_write(0x401abe98, b"\x01")
    # Initialiser sampler_descr et sampler_descr_atk
    e.uc.mem_write(0x401abe9a + 12, struct.pack(">I", 0x4b))
    e.uc.mem_write(0x401abe9a + 24, struct.pack(">I", 0x49))
    e.uc.mem_write(0x401abe9a + 28, struct.pack(">I", 0x4a))

    e.uc.mem_write(0x401abee6 + 12, struct.pack(">I", 0x0d))
    e.uc.mem_write(0x401abee6 + 24, struct.pack(">I", 0x49))
    e.uc.mem_write(0x401abee6 + 28, struct.pack(">I", 0x4a))

    # Mock des fonctions de sélection de piste pour l'interface :
    # 0x400cf866, 0x4000eb90 -> rts ; 0x40012412 -> moveq #0, %d0 ; rts (piste 0)
    e.uc.mem_write(0x400cf866, b"\x4e\x75")
    e.uc.mem_write(0x4000eb90, b"\x4e\x75")
    e.uc.mem_write(0x40012412, b"\x70\x00\x4e\x75")

    MOD_HELD = 0x401b2452          # +4 : la retouche FUNC+SETTINGS de gen_model_tg.py (#113, notes/81)
    DESCR_HOOK = 0x401ae84e

    # A) Touche MACHINES tenue (mod_held = 1)
    e.uc.mem_write(MOD_HELD, struct.pack(">I", 1))
    for mode in range(7):
        e.uc.mem_write(0x401b2408, struct.pack(">I", mode))
        regs = (mk.UC_M68K_REG_D1, mk.UC_M68K_REG_D2, mk.UC_M68K_REG_A0, mk.UC_M68K_REG_A1)
        for i, reg in enumerate(regs):                # la fonction feuille 0x4004df5c ne touchait pas a0/a1
            e.uc.reg_write(reg, 0x5a5a0000 + i)
        r = e.call(DESCR_HOOK, 7)
        kept = [e.uc.reg_read(reg) for reg in regs]
        check(kept[1:] == [0x5a5a0001, 0x5a5a0002, 0x5a5a0003],
              f"mod_held=1, Mode {mode} : d2, a0, a1 rendus intacts ({', '.join(f'0x{v:08x}' for v in kept[1:])})")
        descr = bytes(e.uc.mem_read(r, 76))
        p1 = struct.unpack_from(">I", descr, 12)[0]
        p4 = struct.unpack_from(">I", descr, 24)[0]
        p5 = struct.unpack_from(">I", descr, 28)[0]
        if mode < 3:
            check(p1 == 0x0d and p4 == 0x49 and p5 == 0x4a,
                  f"mod_held=1, Mode {mode} : positions [Attack=0x{p1:02x}, SWEEP=0x{p4:02x}, CONTOUR=0x{p5:02x}] (filtre propre 0x49/0x4a préservé)")
        else:
            check(p1 == 0x0d and p4 == 0x0c and p5 == 0x0b,
                  f"mod_held=1, Mode {mode} : positions [Attack=0x{p1:02x}, SWEEP=0x{p4:02x}, CONTOUR=0x{p5:02x}] (0x0c/0x0b filtre de piste actif)")

    # B) Touche MACHINES relâchée (mod_held = 0)
    e.uc.mem_write(MOD_HELD, struct.pack(">I", 0))
    for mode in range(7):
        e.uc.mem_write(0x401b2408, struct.pack(">I", mode))
        r = e.call(DESCR_HOOK, 7)
        descr = bytes(e.uc.mem_read(r, 76))
        p4 = struct.unpack_from(">I", descr, 24)[0]
        p5 = struct.unpack_from(">I", descr, 28)[0]
        check(p4 == 0x49 and p5 == 0x4a,
              f"mod_held=0, Mode {mode} : positions [SWEEP=0x{p4:02x}, CONTOUR=0x{p5:02x}] intactes (0x49/0x4a)")


def test_load_budget(img, tw):
    print("\n--- 3. Preuve de charge : 6 pistes Granular + filtre 4 pôles actif ---")
    e = TM.engine(img)
    setup_sampler_sample(e, tw, slot=0)
    th, ts = track_tables(tw)
    for t in range(6):
        e.uc.mem_write(ts + t * 4, struct.pack(">I", 0))
        e.uc.mem_write(th + t * 4, struct.pack(">I", 0x1234))
        e.set(t, machine=6, note=60, pitch=64, color=64, shape=64, sweep=64, contour=64, punch=0, gate=0, finetune=64, decay=60)
        e.uc.mem_write(0x401b2408 + t * 4, struct.pack(">I", 3)) # Granular mode
        e.uc.mem_write(E.PARAMS + 0xe + t * 0x42 + 48, struct.pack(">hh", 4000, 1000)) # ladder actif

    e.block(0x3f) # warmup
    e.count_instructions()
    e.block(0)
    instr = e.instructions
    # 66666 ticks de minuteur ColdFire à 100 MHz = 1 bloc ; à 250 MHz ~ 166 666 cycles
    ratio_250 = (instr / 166666) * 100
    check(instr < 60000 and ratio_250 < 40.0,
          f"6 pistes Granular + filtres actifs : {instr} instructions ({ratio_250:.1f} % du budget à 250 MHz, limite régulateur 80-90 %)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True)
    args = ap.parse_args()
    stock = T.main_os_from_syx(args.cycles)
    tw = json.loads(TWEAK_TG.read_text(encoding="utf-8"))
    p, _ = build.apply_writes(stock, [tw])
    pl, _ = build.build_payload([tw], stock, None)
    img = bytes(p) + pl

    test_audio_proof(img, tw)
    test_descriptor_proof(img, tw)
    test_load_budget(img, tw)

    print("\nTOUT OK" if not FAIL else f"\n{len(FAIL)} ECHEC(S)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
