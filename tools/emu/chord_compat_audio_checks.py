"""Compatibilité DSP ciblée de Chord Keys avec les autres tweaks (notes/40).

La boucle des six voix, le getter de pattern, l'EMAC de Model-TG, ses effets
par piste et le régulateur s'exécutent. Les recettes Syntakt sont reconstituées
à leur vraie adresse d'exécution (0x46700000 avec Model-TG). Le banc fournit
les gains de mixeur, les objets de pattern et les événements déjà décodés ;
il ne simule ni le démarrage complet ni les transports MIDI/USB.
"""
import struct

import numpy as np
from unicorn import UC_HOOK_MEM_READ

import build
import gen_syntakt_engines as gs
import gov_asm
import mcengine as E
import syntakt
import test_model_tg as TG
from test_sdvintage_7th import UI
from chord_audio_checks import NativeAudioConfig, config_word
from chord_harmony_checks import expected_notes
from chord_lock_audio_checks import RAW, EVENT, EXTRACT, APPLY, SET_PARAM, SMOOTH, LOCK_MASK
from chord_plock_checks import SLOT
from chord_slot_checks import run_slot_checks
from probe_chord_keys import frequency_ratios
from test_governor import TIMER, BLOCK, GAINS, FULL


class Config(NativeAudioConfig):
    """Même fixture de pattern ; la zone BSS est déjà mappée par le banc TG."""

    def __init__(self, engine):
        self.engine = engine
        self.write(0x40fe4228, self.ROOT)
        self.write(0x40a7887c, self.ACTIVE)
        self.select(0)


def run(stock, reference, patched, symbols, chosen, syntakt_path, extra_code, check):
    """Compare le même ensemble de mods avant et après ajout de Chord Keys."""
    tg = next((t for t in chosen if t['id'].startswith('model-tg')), None)
    ours = next((t for t in chosen if t.get('append', {}).get('syntakt')), None)
    payload = (E.PAYLOAD_DST, b'')
    if ours:
        payload = (int(ours['append']['dest'], 16),
                   build.payload_runtime(ours, stock, syntakt.dsp_image(syntakt_path)))
        check(payload[0] == (gs.PAY_TG if tg else gs.PAY_ALONE),
              f"DSP partagé : charge utile Syntakt à son adresse d'exécution {payload[0]:#x}")
    tg_code = [(TG.BLOB, E.BASE + len(stock) + tg['append']['size'] - TG.BLOB)] if tg else []
    engines = []

    def engine(image, chord=False):
        e = E.Engine(image, extra_code=tg_code + (list(extra_code) if chord else []), payload=payload)
        e.uc.mem_map(0x40800000, 0x01800000)
        if tg:
            e.uc.mem_map(0x42400000, 0x00c00000)
            e.uc.mem_map(0x48000000, 0x08000000)
            e.uc.mem_map(0xfc078000, 0x1000)
        for track in range(6):
            for address in GAINS:
                e.uc.mem_write(address + 4 * track, struct.pack('>I', FULL))
            if tg:
                e.uc.mem_write(E.PARAMS + 14 + 66 * track + 46,
                               struct.pack('>3H', 0, 32512, 0))
        engines.append(e)
        return e

    def ui():
        u = UI(reference, payload[1] if payload[0] == E.PAYLOAD_DST else b'')
        u.uc.mem_write(E.BASE + E.IMAGE_LEN, reference[E.IMAGE_LEN:])
        if payload[1] and payload[0] != E.PAYLOAD_DST:
            u.uc.mem_map(payload[0], 0x100000)
            u.uc.mem_write(*payload)
        return u

    run_slot_checks(reference, check, engine_factory=lambda: engine(reference), ui_factory=ui)
    active = config_word(root=24, extensions=(1,) * 7)

    def setup(e, machines, enabled):
        config = Config(e)
        config.configure([active if enabled else active & 0x7fffffff] * 6)
        for track, machine in enumerate(machines):
            e.set(track, machine=machine, note=24, pitch=64, finetune=64,
                  color=32, shape=3, sweep=48, contour=64, decay=100)
        return config

    def render(e, blocks=32):
        return np.stack([e.block(63 if block in (1, 24) else 0) for block in range(blocks)])

    a, b = engine(reference), engine(patched, True)
    setup(a, range(6), False)
    setup(b, range(6), False)
    off_a, off_b = render(a), render(b)
    check(np.array_equal(off_a, off_b) and all(off_a[:, track].any() for track in range(6)),
          "Keys OFF : six machines, vraie boucle des voix, PCM identique aux mêmes mods sans Chord Keys")

    a, b = engine(reference), engine(patched, True)
    setup(a, range(6), True)
    setup(b, range(6), True)
    on_a, on_b = render(a), render(b)
    check(np.array_equal(on_a[:, :5], on_b[:, :5]) and on_b[:, 5].any()
          and not np.array_equal(on_a[:, 5], on_b[:, 5]),
          "Keys ON : KICK/SNARE/METAL/PERC/TONE inchangés, CHORD diatonique audible dans le dispatch partagé")
    ratios = tuple(int.from_bytes(b.uc.mem_read(E.VOICE0 + 5 * E.VSTRIDE + 0x50 + 0x78 * i, 4), 'big')
                   for i in range(4))
    check(all(abs(x - y) <= 2 for x, y in zip(ratios, frequency_ratios((0, 4, 7, 11)))),
          "Keys ON : rapports de Cmaj7 exacts après le véritable rendu CHORD, oscillateur Model-TG compris")

    # Les machines ajoutées partagent les mots de paramètres. Keys ON partout
    # doit laisser leur DSP intact, même si une lane HARMONY contient une valeur.
    extra_machines = ([6] if tg else [])
    codes = [c for c in (ours['id'].split('-') if ours else []) if c in gs.CATALOG]
    first = 7 if tg else 6
    extra_machines += list(range(first, first + len(codes)))
    if extra_machines:
        u = ui()
        u.call(0x4005a274)
        spare = not u.bad
        for machine in extra_machines:
            for slot in range(SLOT, 33):
                spare &= u.call(0x4005a692, slot, machine) == 0 and not u.bad
        check(spare, "Machines ajoutées : aucun descripteur ne réserve les slots 28..32")
        a, b = engine(reference), engine(patched, True)
        machines = (extra_machines + [0] * 6)[:6]
        for candidate in (a, b):
            setup(candidate, machines, True)
            for track, machine in enumerate(machines):
                if first <= machine < first + len(codes):
                    entry = gs.CATALOG[codes[machine - first]]
                    candidate.set(track, **dict(zip(('color', 'shape', 'sweep', 'contour'),
                                                   [k[2] for k in entry['knobs']])))
                candidate.uc.mem_write(E.PARAMS + 14 + 66 * track + 2 * SLOT, struct.pack('>H', 6))
                candidate.uc.mem_write(LOCK_MASK + 8 * track, struct.pack('>I', 1 << SLOT))
        other_a, other_b = render(a), render(b)
        check(np.array_equal(other_a, other_b),
              f"Keys ON : machines ajoutées {extra_machines}, lane HARMONY présente, PCM identique")
        if tg:
            check(not other_b[:, 0].any(), "Keys ON : Sampler vide toujours muet")
        if codes:
            check(all(other_b[:, machines.index(first + i)].any() for i in range(len(codes))),
                  "Keys ON : chaque moteur Syntakt sélectionné reste audible")

    # Les cibles du lisseur et le bitmap viennent du vrai extracteur de locks.
    # Passer ensuite son buffer à la boucle audio inclut Attack/Filter/Res de TG.
    e = engine(patched, True)
    setup(e, [5] * 6, True)
    e._write_params()
    for index in range(238):
        value = int.from_bytes(e.uc.mem_read(E.PARAMS + 2 * index, 2), 'big', signed=True)
        e.call(SET_PARAM, index, value, E.PARAMS)
    correct, effects_intact, audible = True, True, True
    first_error = None
    for modifier in range(7):
        attack = modifier + 1
        raw = bytearray(b'\xff' * 68)
        struct.pack_into('>H', raw, 2 * SLOT, modifier)
        effects = (attack, 28000 - modifier * 512, 256 + modifier * 128)
        if tg:
            struct.pack_into('>3H', raw, 46, *effects)
        e.uc.mem_write(RAW, bytes(raw))
        e.call(EXTRACT, EVENT, RAW, 0, 0)
        e.call(APPLY, 0, EVENT, E.PARAMS)
        any_pcm = False
        for block in range(4):
            # L'interruption audio configure l'EMAC avant le lisseur, en
            # dehors de la boucle des voix appelée ici (même contrat que
            # chord_lock_audio_checks). Sans ce mode, le premier lissage
            # transforme à tort le sélecteur CHORD en une autre machine.
            e.emac.macsr = 0xa0
            smoothed = e.call(SMOOTH, E.PARAMS)
            e.call(E.VOICE_LOOP, E.TRACK_BASE, smoothed, 1 if block == 0 else 0, 0)
            any_pcm |= any(e.uc.mem_read(E.TRACK_BASE, 128))
        notes = expected_notes(0, 0, 1, 0, modifier)
        ratios = tuple(int.from_bytes(e.uc.mem_read(E.VOICE0 + 0x50 + 0x78 * i, 4), 'big')
                       for i in range(4))
        packet = int.from_bytes(e.uc.mem_read(symbols['ck_chord_live'], 4), 'big')
        expected_packet = 0x80000000 | 24 | ((notes[0] % 12) << 27)
        expected_packet |= sum(n << (7 + 5 * i) for i, n in enumerate(notes))
        matches = (all(abs(x - y) <= 2 for x, y in zip(ratios, frequency_ratios(notes)))
                   and packet == expected_packet)
        correct &= matches
        if tg:
            got_effects = struct.unpack('>3H', e.uc.mem_read(smoothed + 14 + 46, 6))
            effects_intact &= got_effects == effects
        if first_error is None and (not matches or tg and got_effects != effects):
            first_error = (modifier, hex(packet), hex(expected_packet), ratios,
                           int.from_bytes(e.uc.mem_read(smoothed + 14 + 2 * SLOT, 2), 'big'),
                           got_effects if tg else None)
        audible &= any_pcm
    check(correct and audible,
          "HARMONY : sept états relus par extracteur, lisseur, boucle audio et oscillateur réels ; rapports et noms exacts"
          + (f" ; premier écart {first_error}" if first_error else ""))
    if tg:
        check(effects_intact,
              "Model-TG : Attack23, Filter24 et Resonance25 conservent leurs locks pendant HARMONY28")

    governor = next((t for t in chosen if t.get('gov')), None)
    if governor:
        _governor(engine, patched, setup, governor, check)
    check(all(not e.unmapped for e in engines),
          f"DSP partagé : {len(engines)} instances ciblées, aucun accès mémoire hors du banc")


def _governor(factory, patched, setup, tweak, check):
    """Charge imposée au vrai régulateur ; aucune estimation de marge matérielle."""
    sy = {name: int(address, 16) for name, address in tweak['gov'].items()}

    def play(load):
        e = factory(patched, True)
        setup(e, [5] * 6, True)
        clock = {'now': 10_000_000, 'fixed': None}

        def timer(uc, access, address, size, value, userdata):
            clock['now'] += 2000
            value = clock['now'] if clock['fixed'] is None else clock['fixed']
            uc.mem_write(TIMER, struct.pack('>I', value & 0xffffffff))

        e.uc.hook_add(UC_HOOK_MEM_READ, timer, begin=TIMER, end=TIMER + 3)
        e.uc.mem_write(gov_asm.x_var(tweak, 'X_SLOW'), bytes(4))
        output, fading, stolen = [], [], []
        for block in range(96):
            output.append(e.block(63 if block in (1, 80) else 0))
            if load is not None:
                start = 10_000_000 + block * BLOCK
                e.uc.mem_write(sy['gov_t0_audio'], struct.pack('>I', start))
                clock['fixed'] = start + load(block) * BLOCK // 100
                e.call(sy['audio_end'])
                clock['fixed'] = None
            fading.append(bytes(e.uc.mem_read(sy['gov_fading'], 6)))
            stolen.append(bytes(e.uc.mem_read(sy['gov_stolen'], 6)))
        return np.stack(output), fading, stolen

    reference, _, _ = play(None)
    normal, _, stolen = play(lambda block: 50)
    check(np.array_equal(reference, normal) and reference.any() and not any(map(any, stolen)),
          "Régulateur partagé + six CHORD Keys : charge simulée de 50 %, PCM identique, aucune voix volée")
    overloaded, fading, stolen = play(lambda block: 99 if 40 <= block < 60 else 50)
    first = next((block for block, flags in enumerate(fading) if any(flags)), None)
    check(first == 41 and any(map(any, stolen))
          and np.array_equal(reference[:first + 1], overloaded[:first + 1])
          and np.abs(overloaded[81:]).max() > 1_000_000,
          "Régulateur partagé + six CHORD Keys : surcharge répétée, fondu puis nouveau trig audible")
