"""Enveloppe de coupure de Wave sous FUNC + SWEEP (notes/62), sur le code de l'interface de l'OS, comme le lo-fi de MACRO
(lofi_ui.py) : la recherche du descripteur d'un potard, le tour de potard avec FUNC (0x4000b7d6), le texte de la
valeur (vrai sprintf), la fenêtre de valeur (0x4001d818). Avec MACRO dans le même firmware, FUNC + PITCH y reste son
lo-fi. Utilisé par test_wavetable.py et test_wave_combos.py."""

import lofi_ui as L

SWEEP_KNOB = 6
FTUN = L.FTUN


def want_text(fine):
    return "OFF" if fine == 64 else f"{fine - 64:+d}"


def check_fenv(base_img, fw_img, payload, wave, label, check, base, base_payload=None, macro=None):
    """FUNC + SWEEP sur une piste Wave (machine wave) : FINE, pas à pas, avec son texte ; les machines 0..wave-1
    comme base (le même firmware sans Wave), sauf FUNC + PITCH sur MACRO (macro : son index) si elle y est."""
    a = L.UI(base_img, base_payload)
    b = L.UI(fw_img, payload)
    check(a.init_ok and b.init_ok, f"{label} : objets d'interface construits par l'OS (0x400de244)")
    got, same = {}, True
    for m in range(wave + 1):
        for knob in range(2, 16):
            for func in (False, True):
                got[m, knob, func] = d = b.lookup(m, knob, func)
                if m < wave:
                    same &= d == a.lookup(m, knob, func)
    same &= None not in got.values()
    sweep = got[wave, SWEEP_KNOB, False]
    check(got[wave, SWEEP_KNOB, True] == FTUN and sweep not in (FTUN, None),
          f"{label} : piste Wave, FUNC + SWEEP -> {got[wave, SWEEP_KNOB, True]} (FINE, {FTUN}) ; SWEEP seul -> "
          f"{sweep} (Cutoff de Wave)")
    check(all(got[wave, k, True] == got[wave, k, False] for k in range(2, 14) if k != SWEEP_KNOB),
          f"{label} : les autres potards de Wave (2 à 13) : avec FUNC comme sans")
    check(same, f"{label} : machines 0..{wave - 1}, les 14 potards, avec et sans FUNC : le même descripteur que {base}")
    b.lookup(wave, SWEEP_KNOB, True)                    # les fonctions de FINE : celles de Wave
    cases = [(cur, d) for cur in (0, 0x100, 0x3f00, 0x4000, 0x4080, 0x4100, 0x7e00, 0x7f00, 0x1234)
             for d in (1, 0x100, 0x180, 0x300, -1, -0x100, -0x300, 0x7f00, -0x7f00)]
    bad = [(hex(c), hex(d), b.edit_func(FTUN, c, d)) for c, d in cases if b.edit_func(FTUN, c, d) != L.want_step(c, d)]
    check(not bad, f"{label} : FUNC + un tour sur FINE (vrai 0x4000b7d6) : un pas par cran, borné à 0..0x7f00 "
                   f"({len(cases)} cas){bad[:3]}")
    shown = [b.text(FTUN, n << 8) for n in range(128)]
    check(shown == [want_text(n) for n in range(128)] and all(len(s) <= 3 for s in shown),
          f"{label} : texte des 128 pas (vrai sprintf) : {shown[0]} .. {shown[63]} {shown[64]} {shown[65]} .. "
          f"{shown[127]}, trois caractères au plus")
    gauge = a.popup(FTUN, 0x2000)
    steps = (0, 1, 63, 64, 65, 100, 127)
    shots = {n: (b.popup(FTUN, n << 8), b.popup(FTUN, n << 8, text_path=True)) for n in steps}
    bad = [n for n, (x, y) in shots.items() if x is None or y is None or x != y or x[1] or x[0] == gauge[0]]
    check(not bad, f"{label} : fenêtre de valeur de FINE (vrai 0x4001d818) : le texte "
                   f"{', '.join(want_text(n) for n in steps)}, pixel pour pixel celui de l'OS ; plus de jauge {bad}")
    chars = sorted(set("".join(shown)))
    missing = [c for c in chars if not b.glyph(c)]
    check(not missing, f"{label} : chaque caractère ({''.join(chars)}) existe dans la grande police {missing}")
    if not bad:
        for n in (24, 104):
            print(f"      fenêtre de valeur, FUNC + SWEEP à {n - 64:+d} :")
            print(L.ascii_popup(b.popup(FTUN, n << 8)[0]))
    if macro is not None:                               # MACRO garde son lo-fi sous FUNC + PITCH
        d = b.lookup(macro, L.PITCH_KNOB, True)
        txt = b.text(FTUN, 23 << 8)
        check(d == FTUN and txt == L.want_text(23) and b.lookup(wave, SWEEP_KNOB, True) == FTUN
              and b.text(FTUN, 23 << 8) == want_text(23),
              f"{label} : MACRO (machine {macro + 1}) : FUNC + PITCH -> FINE, texte « {txt} » (son lo-fi) ; puis "
              f"Wave : FUNC + SWEEP -> FINE, texte « {want_text(23)} »")
