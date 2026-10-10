#!/usr/bin/env python3
"""Preuve du clavier CHORD diatonique, sur le JSON final (notes/40).

Exécute le code ColdFire dans ses masques définitifs et les vraies routines OS
pour les événements de touches et pads, les menus, les patterns et le DSP. Les helpers
précisent leurs limites d'instrumentation ; ce n'est pas un démarrage complet
ni un test matériel. Durée : quelques minutes, surtout les 14 000 accords DSP.

    python3 tools/emu/test_chord_keys.py --cycles firmware/model-cycles_OS1.13.syx
    python3 tools/emu/test_chord_keys.py --cycles firmware/model-cycles_OS1.13.syx --focus pad-release
    python3 tools/emu/test_chord_keys.py --cycles firmware/model-cycles_OS1.13.syx --focus compatibility --with model-tg
    python3 tools/emu/test_chord_keys.py --cycles firmware/model-cycles_OS1.13.syx \\
        --with 6ch-usbup,latching-mute,trig-preview,browser-scroll,trig-hold,arp,tempo-max,boot-anim,syntakt-sd-cp-toy-bits-swarm \\
        --syntakt firmware/Syntakt_OS1.42.syx
"""
import argparse
import json
from pathlib import Path
import struct
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import build
from gen_chord_keys import HOOKS, load_stock
from chord_audio_checks import (run_audio_checks, run_audio_storage_checks,
                                run_audio_governor_checks, run_audio_midi_checks)
import chord_ui_checks
import chord_routing_checks
import chord_harmony_checks
import chord_palette_ui_checks
import chord_pad_audio_checks
import chord_display_checks
import chord_recording_checks
from chord_slot_checks import run_slot_checks
from chord_plock_checks import run_plock_checks, _attack_recording_checks
from chord_lock_audio_checks import run_lock_audio_checks
from probe_chord_storage import run_storage_checks

DIRECTORY = HERE.parents[1] / "tweaks/model-cycles_OS1.13"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cycles", required=True)
    parser.add_argument("--with", dest="others", default="")
    parser.add_argument("--syntakt")
    parser.add_argument("--focus", choices=("pad-release", "pad-prepare", "live-recording", "compatibility", "midi-output"),
                        help="preuves ciblées TRIG/pads, P-locks, routage et DSP ; compatibility inclut Model-TG")
    args = parser.parse_args()
    stock = load_stock(args.cycles)
    by_id = {item["id"]: item for path in DIRECTORY.glob("*.json")
             if "id" in (item := json.loads(path.read_text()))}
    chosen = [by_id[key] for key in args.others.split(",") if key]
    tweak = by_id["chord-keys"]
    symbols = {name: int(value, 0) for name, value in tweak["symbols"].items()}
    reference, _ = build.apply_writes(stock, chosen)
    patched, dirty = build.apply_writes(stock, chosen + [tweak])
    build.check_conflicts(chosen + [tweak])
    build.check_caves(stock, chosen + [tweak], False, dirty, patched,
                      json.loads((DIRECTORY / "device.json").read_text()).get("cave_refs_ok"))
    payload, _ = build.build_payload(chosen, stock, args.syntakt)
    reference, patched = bytes(reference) + payload, bytes(patched) + payload
    failures = []

    def check(condition, message):
        print(("ok    " if condition else "FAIL  ") + message, flush=True)
        if not condition:
            failures.append(message)

    print("firmware : " + ", ".join(item["id"] for item in chosen + [tweak]), flush=True)
    for address, expected, symbol, opcode in HOOKS:
        old = bytes.fromhex(expected)
        new = (struct.pack(">I", symbols[symbol]) if opcode is None else
               struct.pack(">HI", opcode, symbols[symbol]))
        new += b"\x4e\x71" * ((len(old) - len(new)) // 2)
        check(stock[address-build.BASE:address-build.BASE+len(old)] == old and
              patched[address-build.BASE:address-build.BASE+len(new)] == new and
              symbols[symbol] % 2 == 0,
              f"accroche {symbol} : contrat stock et destination paire vérifiés")
    interiors = [(address-build.BASE+2, address-build.BASE+len(bytes.fromhex(expected)))
                 for address, expected, _, opcode in HOOKS if opcode]
    sure, branches = build.refs_into(stock, interiors)
    check(not sure and not branches,
          f"aucun pointeur ni branchement vers l'intérieur des instructions détournées : {sure + branches}")
    overlap = []
    for other in by_id.values():
        if other["id"] in (tweak["id"], *tweak["conflicts"]):
            continue
        for a in tweak["writes"]:
            for b in other.get("writes", []):
                lo = max(a["off"], b["off"])
                hi = min(a["off"] + len(a["new"])//2, b["off"] + len(b["new"])//2)
                if lo < hi and bytes.fromhex(a["new"])[lo-a["off"]:hi-a["off"]] != bytes.fromhex(b["new"])[lo-b["off"]:hi-b["off"]]:
                    overlap.append((other["id"], lo))
    check(not overlap, f"aucun chevauchement avec les autres tweaks compatibles : {overlap}")
    extra_code = [(build.BASE + w["off"], len(w["new"])//2) for w in tweak["writes"]
                  if len(w["new"])//2 > 32]
    if args.focus == "midi-output":
        import chord_midi_checks
        import chord_midi_event_checks
        run_storage_checks(reference, patched, symbols)
        chord_ui_checks._menu(patched, symbols, check)
        chord_midi_checks.run(reference, patched, symbols, check)
        chord_midi_event_checks.run(reference, patched, symbols, extra_code, check)
    elif args.focus == "compatibility":
        # Les intégrations touchées : clavier/entretien TG, nouvelle lane
        # HARMONY, Scale Lock et dispatch DSP. Pas de matrice musicale complète.
        run_storage_checks(reference, patched, symbols)
        run_plock_checks(reference, patched, symbols)
        chord_ui_checks.run_pad_release(reference, patched, symbols, check)
        chord_routing_checks.run(reference, patched, symbols, check)
        from chord_tg_scale_checks import run as run_scale, run_stock as run_scale_stock
        from chord_compat_audio_checks import run as run_compat_audio
        has_tg = any(item["id"].startswith("model-tg") for item in chosen)
        (run_scale if has_tg else run_scale_stock)(reference, patched, symbols, check)
        run_compat_audio(stock, reference, patched, symbols, chosen, args.syntakt, extra_code, check)
        if not has_tg:
            run_lock_audio_checks(reference, patched, symbols, extra_code, check)
            chord_recording_checks.run(reference, patched, symbols, extra_code, check)
    elif args.focus == "live-recording":
        chord_recording_checks.run(reference, patched, symbols, extra_code, check)
        _attack_recording_checks(reference, patched, symbols)
        run_lock_audio_checks(reference, patched, symbols, extra_code, check)
        chord_pad_audio_checks.run_prepare(patched, symbols, extra_code, check)
    elif args.focus == "pad-prepare":
        chord_ui_checks._pad_prepare(patched, symbols, check)
        chord_ui_checks._pad_latch(patched, symbols, check)
        chord_ui_checks._harmony_pads(reference, patched, symbols, check)
        chord_ui_checks._pad_dispatch(patched, symbols, check)
        try:
            _attack_recording_checks(reference, patched, symbols)
        except AssertionError as error:
            check(False, f"préparation et enregistrement : {error}")
        if chosen:
            from chord_compat_audio_checks import Config, runtime_payload, shared_engine
            tg = next((t for t in chosen if t["id"].startswith("model-tg")), None)
            runtime = runtime_payload(stock, chosen, args.syntakt)
            chord_pad_audio_checks.run_prepare(
                patched, symbols, extra_code, check,
                engine_factory=lambda: shared_engine(patched, extra_code, tg, runtime, len(stock)),
                config_factory=Config)
        else:
            chord_pad_audio_checks.run_prepare(patched, symbols, extra_code, check)
    elif args.focus == "pad-release":
        chord_ui_checks.run_pad_release(reference, patched, symbols, check)
        chord_routing_checks.run(reference, patched, symbols, check)
        try:
            run_plock_checks(reference, patched, symbols)
        except AssertionError as error:
            check(False, f"P-locks HARMONY : {error}")
        run_lock_audio_checks(reference, patched, symbols, extra_code, check)
        chord_pad_audio_checks.run(reference, patched, symbols, extra_code, check)
        chord_pad_audio_checks.run_prepare(patched, symbols, extra_code, check)
    else:
        try:
            run_storage_checks(reference, patched, symbols)
        except AssertionError as error:
            check(False, f"stockage : {error}")
        try:
            run_plock_checks(reference, patched, symbols)
        except AssertionError as error:
            check(False, f"P-locks HARMONY : {error}")
        chord_ui_checks.run(reference, patched, symbols, check)
        chord_routing_checks.run(reference, patched, symbols, check)
        run_slot_checks(reference, check)
        chord_palette_ui_checks.run(reference, patched, symbols, check)
        chord_display_checks.run(reference, patched, symbols, check)
        run_lock_audio_checks(reference, patched, symbols, extra_code, check)
        audio_failures = run_audio_checks(reference, patched, symbols["ck_audio_config"], extra_code)
        if audio_failures:
            failures.extend(["audio"] * audio_failures)
        midi_failures = run_audio_midi_checks(reference, patched, symbols, extra_code)
        if midi_failures:
            failures.extend(["notes MIDI aiguës"] * midi_failures)
        storage_audio_failures = run_audio_storage_checks(reference, patched, extra_code)
        if storage_audio_failures:
            failures.extend(["stockage audio"] * storage_audio_failures)
        chord_harmony_checks.run(reference, patched, symbols, extra_code, check)
        chord_pad_audio_checks.run(reference, patched, symbols, extra_code, check)
        chord_pad_audio_checks.run_prepare(patched, symbols, extra_code, check)
        chord_recording_checks.run(reference, patched, symbols, extra_code, check)
    for governor in (item for item in chosen if item.get("gov") and args.focus not in ("pad-prepare", "compatibility", "midi-output")):
        for new_controls in (False, True):
            governor_failures = run_audio_governor_checks(patched, governor, extra_code, new_controls)
            if governor_failures:
                failures.extend(["régulateur audio"] * governor_failures)
    print("TOUT OK" if not failures else f"FAIL : {len(failures)} échecs", flush=True)
    return int(bool(failures))


if __name__ == "__main__":
    sys.exit(main())
