"""Réserve de paramètres natifs disponible pour HARMONY (notes/42 §22, §33).

Les buffers OS contiennent 33 mots par piste. Model-TG emploie 23..27 et le
filtre par piste 28..31 (notes/47) ; HARMONY prend donc le dernier, 32. Ce
banc exécute les recherches de descripteurs et les six vrais moteurs pour
vérifier ce mot.
Les copies génériques/LFO peuvent toujours transporter ces mots ; ce banc ne
prouve pas leur absence de tous les accès de l'OS. La sérialisation et la
relecture des P-locks sont prouvées séparément.
"""
import struct

from unicorn import UC_HOOK_MEM_READ
from unicorn import m68k_const as mk

import mcengine as E
from chord_plock_checks import SLOT
from test_sdvintage_7th import UI


def run_slot_checks(stock, check, engine_factory=None, ui_factory=None):
    """Vérifie le stock, éventuellement avec les autres mods compatibles."""
    ui = ui_factory() if ui_factory else UI(stock, stock[E.IMAGE_LEN:])
    ui.call(0x4005a274)
    descriptors_ok = not ui.bad
    for machine in range(6):
        for slot in range(SLOT, 33):
            descriptors_ok &= ui.call(0x4005a692, slot, machine) == 0 and not ui.bad
    check(descriptors_ok,
          f"slot réservé : constructeur et recherche natifs, aucun descripteur pour {SLOT} sur les six machines")

    factory = engine_factory or (lambda: E.Engine(stock))
    a, b = factory(), factory()
    reads = []

    def read_spare(uc, access, address, size, value, userdata):
        reads.append((uc.reg_read(mk.UC_M68K_REG_PC), address, size))

    for track in range(6):
        for engine in (a, b):
            engine.machine_defaults(track, track)
            engine.set(track, note=48, pitch=64, finetune=64, decay=100)
        start = E.PARAMS + 14 + 66 * track + 2 * SLOT
        count = 33 - SLOT
        b.uc.mem_write(start, struct.pack(f">{count}H", *(0x100 * (i + 1) for i in range(count))))
        b.uc.hook_add(UC_HOOK_MEM_READ, read_spare, begin=start, end=start + 2 * count - 1)

    identical, audible = True, False
    for block in range(32):
        reference = a.block(63 if block == 0 else 0)
        observed = b.block(63 if block == 0 else 0)
        identical &= (reference == observed).all()
        audible |= reference.any()
    check(identical and audible and not reads,
          f"slot réservé : 32 blocs des six moteurs, sentinelle {SLOT} sans lecture DSP ni différence PCM")
    check(not a.unmapped and not b.unmapped,
          "slots réservés : aucun accès mémoire hors du banc natif")
