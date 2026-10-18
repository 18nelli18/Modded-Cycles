#!/usr/bin/env python3
"""Surcharge d'un bloc : ce que deviennent l'audio USB et l'heure musicale quand le rendu dépasse 100 %.

Banc de tools/emu/test_usb_in.py (vrai pilote USB de l'OS 1.13 dans Unicorn, contrôleur et horloges modélisés),
avec un ordonnancement fidèle des deux interruptions (lu dans l'OS) :
  - l'interruption DMA (0x400589c0, niveau 6) tombe à chaque bloc et met le bit de forçage du rendu
    (0xfc04c010 |= 0x80000000) ; c'est un bit, pas un compteur ;
  - le rendu (0x40058c5e, niveau 5) efface ce bit à son entrée (0x40058c6c) et ne peut pas s'interrompre lui-même
    (niveau 5 masqué pendant qu'il tourne) ; s'il dure plus d'un bloc, l'interruption DMA suivante remet le bit et
    le rendu suivant part dès sa fin ; si DEUX interruptions DMA tombent pendant un même rendu, l'une est perdue :
    un rendu de moins, donc 32 trames de moins envoyées à l'USB (0x40002912 une fois par rendu) et l'heure
    musicale (0x8000184c += 2 x tempo une fois par rendu, 0x400593fc) en retard d'un bloc.
Le contenu des trames reste continu (chaque rendu calcule les 32 trames suivantes) ; c'est le niveau de la file USB
qui baisse de 32 trames à chaque rendu perdu, sans que rien ne le remonte (la mesure du débit ne regarde pas la file,
notes/35 §1).

Scénarios (3 s, charge de base 77 % +-3 %) : une rafale de N blocs à L % à 1,0 s, puis la charge de base.
Mesures : rendus perdus, blocs en retard (la moitié de l'anneau DMA relue avant d'être réécrite : un craquement sur
les jacks), file USB avant/après, micro-trames vides après la rafale.

    python3 preuve_surcharge.py
"""
import json
import math
import random
import sys

sys.path.insert(0, "/home/user/Modded-Cycles/tools/emu")
sys.path.insert(0, "/home/user/Modded-Cycles/tools")
import build                    # noqa: E402
import test_sdvintage as T      # noqa: E402
import test_usb_in as U         # noqa: E402

CYCLES = "/home/user/Modded-Cycles/firmware/model-cycles_OS1.13.syx"
BLOCK = U.BLOCK


def schedule(nblocks, load):
    """Rendus (début, fin, nombre d'interruptions DMA perdues pendant ce rendu) selon la règle des niveaux."""
    out, k, a = [], 0, 40.0
    horizon = nblocks * BLOCK
    while a < horizon:
        c = load(k, a)
        e = a + c
        first = math.floor(a / BLOCK) + 1                      # 1re interruption DMA après le début du rendu
        during = max(0, math.ceil(e / BLOCK) - first)          # interruptions DMA pendant le rendu
        lost = max(0, during - 1)
        late = e > first * BLOCK                               # la moitié écrite est déjà relue par le DMA
        out.append((a, e, lost, late))
        a = e if during >= 1 else first * BLOCK + 40.0
        k += 1
    return out


def run(img, ch, hooks, renders, seconds, ppm=30.0, start_ms=20.33, split=1.0):
    u = U.Usb(img, ch, hooks)
    uf = U.UFRAME * (1 + ppm * 1e-6)
    for i in range(4):
        u.w32(U.RATE + 4 * i, 0x60000)
    u.uc.mem_write(0x404a0604, b"\x01")
    nblocks = int(seconds * 1500)
    events = [(n * BLOCK, 0, n, "stamp") for n in range(nblocks)]
    for k, (a, e, lost, late) in enumerate(renders):
        if hooks:
            events.append((a, 1, k, "isr"))
            events.append((e, 2, k, "end"))
        else:
            events.append((e, 1, k, "feed"))
    events.sort()
    k_uf, armed, started = 0, False, False
    expect = None
    st = {"trous": 0, "sautées": 0, "doubles": 0, "trames": 0, "file_max": 0, "file_min": 99}
    phase = {"avant": [99, -1, 0], "après": [99, -1, 0], "fin": [99, -1, 0]}
    t_split = split * 12288000
    t_late = (split + 1.5) * 12288000
    for t_ev, _, n, what in events:
        while k_uf * uf <= t_ev:
            t = k_uf * uf
            if not armed and t >= start_ms * 12288:
                u.call(U.START, 1)
                armed = True
            if armed and not started and k_uf % 8 == 0:
                started = True
            fr = k_uf & 0x3fff
            u.w32(U.FRINDEX, fr)
            u.w32(0x422ff158, int(t) & 0xffffffff)
            u.w32(U.SOF_T + (fr & 31) * 8, int(t - u.r32(U.STAMP) + 0.5) & 0xffffffff)
            if k_uf % 8 == 0:
                u.call(0x4000238e)
            if started:
                ph = phase["avant" if t < t_split else "après" if t < t_late else "fin"]
                if u.queue:
                    dtd = u.queue.pop(0)
                    tok, buf, cb = u.r32(dtd + 4), u.r32(dtd + 8), u.r32(dtd + 36)
                    u.w32(dtd + 4, tok & ~0x80)
                    data = bytes(u.uc.mem_read(buf, tok >> 16))
                    u.w32(U.FRAME_NO, (k_uf >> 3) & 2047)
                    if cb:
                        u.call(cb)
                    expect = u._check(data, expect, st)
                elif u.r32(0x404a0644):
                    st["trous"] += 1
                    ph[2] += 1
                if u.r32(0x404a0644) and t > 0.3 * 12288000:
                    ph[0], ph[1] = min(ph[0], len(u.queue)), max(ph[1], len(u.queue))
            k_uf += 1
        if what == "stamp":
            u.w32(U.STAMP, n * BLOCK)
            u.w32(U.BLKCNT, n)
        elif what == "feed":
            u.fill(n)
            u.call(U.FEED, U.MIX, 32)
        elif what == "isr":
            u.call(hooks["isr"])
        elif what == "end":
            u.fill(n)
            u.call(hooks["end"], U.MIX, 32)
    return st, phase


def base_load(seed):
    rnd = random.Random(seed)
    return lambda: BLOCK * rnd.uniform(0.74, 0.80)


def burst(at_s, n, level, seed=1):
    b = base_load(seed)
    t0 = at_s * 1500 * BLOCK
    state = {"left": n}

    def load(k, a):
        if a >= t0 and state["left"] > 0:
            state["left"] -= 1
            return BLOCK * level
        return b()
    return load


def main():
    stock = T.main_os_from_syx(CYCLES)
    dev = U.DEV
    by_id = {json.loads(f.read_text(encoding="utf-8"))["id"]: f for f in dev.glob("*.json") if f.name != "device.json"}
    usbup = json.loads(by_id["6ch-usbup"].read_text(encoding="utf-8"))
    after = build.apply_writes(stock, [usbup])[0]
    hooks = U.hook_tests(stock, usbup)
    seconds = 5.0
    print("\nscénario : rafale à 1,0 s ; file en cases (stéréo : ring de 16 ; 6 canaux : ring de 9) ;"
          " « après » = 1,0..2,5 s, « fin » = 2,5..5 s")
    print(f"{'rafale':>22} | perdus | en retard | {'firmware':>22} | avant | après : file, vides | fin : file, vides | sautées+doubles")
    for n, level in ((1, 1.10), (1, 1.60), (3, 1.25), (6, 1.20), (12, 1.10), (30, 1.06), (60, 1.06)):
        rs = schedule(int(seconds * 1500), burst(1.0, n, level))
        lost = sum(r[2] for r in rs)
        late = sum(1 for r in rs if r[3])
        for label, img, ch, hk in (("OS d'origine (stéréo)", stock, 2, None), ("6ch-usbup", after, 6, hooks)):
            st, ph = run(img, ch, hk, rs, seconds)
            print(f"{n:>4} bloc(s) à {level * 100:>4.0f} % | {lost:>6} | {late:>9} | {label:>22} | "
                  f"{ph['avant'][0]:>2}..{ph['avant'][1]:<2} | {ph['après'][0]:>2}..{ph['après'][1]:<2}, {ph['après'][2]:>4}     | "
                  f"{ph['fin'][0]:>2}..{ph['fin'][1]:<2}, {ph['fin'][2]:>4}   | {st['sautées'] + st['doubles']}")


if __name__ == "__main__":
    main()
