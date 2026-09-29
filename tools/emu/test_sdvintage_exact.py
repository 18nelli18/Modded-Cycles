#!/usr/bin/env python3
"""Preuve du portage exact (notes/17) : le vrai SD VINTAGE du Syntakt, extrait de TON Syntakt_OS1.41.syx
et greffé dans TON OS Cycles par le tweak sdvintage-exact, doit sortir EXACTEMENT les mêmes échantillons
que dans le moteur audio du Syntakt émulé (stengine.py).

Même note, mêmes réglages, même instant de déclenchement. La boucle des voix du Cycles divise la sortie
d'une piste par 2 : on compare Cycles x 2 et Syntakt, à 1 LSB près (arrondi du décalage).

    python3 tools/emu/test_sdvintage_exact.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.41.syx
"""
import argparse
import json
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import build                  # noqa: E402  (tools/build.py)
import mcengine as E          # noqa: E402
import stengine as S          # noqa: E402
import syntakt                # noqa: E402
import test_sdvintage as T    # noqa: E402

TWEAK = HERE.parent.parent / "tweaks" / "model-cycles_OS1.13" / "21-sdvintage-exact.json"
DEF = dict(tune=64, inhm=0, fcmp=110, swep=74, menv=80, punch=0, gate=0, dec=33)
CASES = [
    ("défauts", {}), ("note 48", {"note": 48}), ("note 72", {"note": 72}), ("TUNE 76", {"tune": 76}),
    ("SWEP 127", {"swep": 127}), ("SWEP 0", {"swep": 0}), ("INHM 127", {"inhm": 127}), ("FCMP 0", {"fcmp": 0}),
    ("MENV 0", {"menv": 0}), ("DEC 90", {"dec": 90}), ("DEC 5", {"dec": 5}), ("PNCH", {"punch": 1}),
]


def render_syntakt(img, blocks, note, kw):
    e = S.Engine(img)
    e.solo(0)
    e.machine(0, "SD VINTAGE")
    e.note(0, note)
    e.set(0, tune=kw["tune"], p1=kw["inhm"], p2=kw["fcmp"], p3=kw["swep"], p4=kw["menv"], punch=kw["punch"],
          gate=kw["gate"], decay=kw["dec"], over=0)
    x = e.render(blocks, trig_at=(1,))
    assert not e.unmapped, e.unmapped[:3]
    return x


def render_cycles(os_img, blocks, note, kw):
    e = E.Engine(os_img)
    e.solo(0)
    e.set(0, machine="SNARE", note=note, pitch=kw["tune"], color=kw["inhm"], shape=kw["fcmp"], sweep=kw["swep"],
          contour=kw["menv"], punch=kw["punch"], gate=kw["gate"], finetune=64, decay=kw["dec"])
    x = e.render(blocks, trig_at=(1,))
    assert not e.unmapped, [(hex(a), hex(b)) for a, b in e.unmapped[:3]]
    return x


def boot_hook_ok(os_img, payload):
    """Exécute la vraie remise à zéro du BSS 0x400004b2 de l'OS patché : le crochet doit recopier la charge
    utile vers 0x43000000, puis le BSS (qui la contenait) doit être remis à zéro et la fonction revenir."""
    from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN
    from unicorn import m68k_const as mk
    import struct
    uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
    uc.ctl_set_cpu_model(mk.UC_CPU_M68K_ANY)
    uc.mem_map(0x40000000, 0x02400000)                 # image + BSS jusqu'à 0x423380b0
    uc.mem_map(E.PAYLOAD_DST, 0x00100000)
    uc.mem_map(0x90000000, 0x00020000)
    uc.mem_write(E.BASE, os_img)
    uc.mem_write(E.STOP, b"\x4e\x71\x4e\x71")
    sp = 0x90010000
    uc.mem_write(sp, struct.pack(">I", E.STOP))
    uc.reg_write(mk.UC_M68K_REG_A7, sp)
    uc.emu_start(0x400004b2, E.STOP, count=20_000_000)
    copied = bytes(uc.mem_read(E.PAYLOAD_DST, len(payload))) == payload
    src = E.BASE + E.IMAGE_LEN
    cleared = not any(uc.mem_read(src, len(payload))) and not any(uc.mem_read(0x42338000, 0xb0))
    back = uc.reg_read(mk.UC_M68K_REG_A7) == sp + 4
    ok = copied and cleared and back
    print(f"  {'ok   ' if ok else 'ECHEC'} crochet de démarrage : charge utile recopiée {'intacte' if copied else 'FAUSSE'},"
          f" BSS remis à zéro {'oui' if cleared else 'NON'}, retour {'normal' if back else 'ANORMAL'}", flush=True)
    return ok


def idle_is_safe(os_img):
    """Tant qu'aucune piste SNARE n'est déclenchée (démarrage, séquenceur arrêté), aucune instruction du code
    du Syntakt ne doit s'exécuter : si ce code posait problème, le Cycles démarrerait quand même."""
    from unicorn import UC_HOOK_CODE
    e = E.Engine(os_img)
    e.solo(0)
    e.set(0, machine="SNARE", note=60, pitch=64, finetune=64, color=0, shape=110, sweep=74, contour=80, decay=33)
    ran = []
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, u: ran.append(a), begin=E.PAYLOAD_CODE[0][0], end=E.PAYLOAD_CODE[0][1])
    x = e.render(50, trig_at=())
    ok = not ran and not x.any() and not e.unmapped
    print(f"  {'ok   ' if ok else 'ECHEC'} au repos (50 blocs sans déclenchement) : {len(ran)} instructions du Syntakt"
          f" exécutées, sortie {'muette' if not x.any() else 'NON muette'}", flush=True)
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="model-cycles_OS1.13.syx officiel")
    ap.add_argument("--syntakt", required=True, help="Syntakt_OS1.41.syx officiel")
    ap.add_argument("--blocks", type=int, default=200, help="blocs de 32 trames par cas")
    ap.add_argument("--cases", help="numéros des cas à jouer (défaut : tous)")
    args = ap.parse_args()

    tweak = json.loads(TWEAK.read_text(encoding="utf-8"))
    stock = T.main_os_from_syx(args.cycles)
    patched, _ = build.apply_writes(stock, [tweak])
    payload, _ = build.build_payload([tweak], stock, args.syntakt)
    os_img = patched + payload
    img = syntakt.dsp_image(args.syntakt)

    fail = (0 if boot_hook_ok(os_img, payload) else 1) + (0 if idle_is_safe(os_img) else 1)
    picks = [int(k) for k in args.cases.split(",")] if args.cases else range(len(CASES))
    for k in picks:
        name, over = CASES[k]
        kw = dict(DEF)
        kw.update(over)
        note = kw.pop("note", 60)
        a = render_syntakt(img, args.blocks, note, kw)
        b = render_cycles(os_img, args.blocks, note, kw) * 2
        diff = np.abs(a - b)
        loud = np.max(np.abs(a))
        ok = loud > 1e6 and diff.max() <= 2
        fail += not ok
        print(f"  {'ok   ' if ok else 'ECHEC'} {name:9} : crête {loud:.3g}, écart max {diff.max():.0f} LSB, "
              f"{np.count_nonzero(diff > 2)} échantillons différents sur {len(a)}", flush=True)
    print("\nIDENTIQUE au Syntakt" if not fail else f"\n{fail} cas différents")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
