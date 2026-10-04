"""Boucle des voix de l'OS (notes/36) : la division par 2 de chaque piste, plus courte, mêmes octets écrits.

Après update/render, la boucle des voix (0x400a7d4a) divise par 2 les 32 échantillons de la piste, en place, avec un
compteur : 7 instructions par échantillon (0x400a7e2a..0x400a7e38), 1 344 par bloc pour 6 pistes. Réécrite dans
les mêmes 14 octets, la fin de la piste prise comme borne : 5 instructions par échantillon, 384 de moins par bloc.
  lea 128(a1),a0 ; 1: move.l (a1),d1 ; asr.l #1,d1 ; move.l d1,(a1)+ ; cmpa.l a0,a1 ; bne.s 1b
Mêmes valeurs, même a1 à la sortie (fin de la piste) ; d0, d1 et a0 n'y sont plus lus (0x400a7e40 recharge d0, le
haut de la boucle recalcule d1 et recharge a0 avant de s'en servir, la fin de la fonction ne les rend pas). Le
détour de Model-TG (sampler_dispatch) et celui des moteurs du Syntakt (tg_after) rejoignent 0x400a7e24 ou 0x400a7e2a,
avant ce code.

Écrit par 6ch-usbup, Model-TG (les deux tweaks) et les moteurs du Syntakt sans Model-TG (même octets : les
constructeurs acceptent une écriture déjà faite à l'identique par un autre tweak). Preuve : tools/emu (sortie des
voix identique échantillon par échantillon, tous les tests du son).
"""
BASE = 0x40000400
HALVE = 0x400a7e2a
OLD = "2211e281528022c17220b28066f2"
NEW = "41e900802211e28122c1b3c866f6"
NOTE = "Boucle des voix : division des pistes par 2 plus courte (tools/voice_loop.py, notes/36), mêmes valeurs."


def writes():
    return [{"off": HALVE - BASE, "old": OLD, "new": NEW}]


def add_to(tweak):
    """Le tweak (dictionnaire) avec cette écriture en plus, à sa place dans l'ordre des adresses, et une ligne de
    description. Pure, comme usb_steady.add_to."""
    taken = [(w["off"], w["off"] + len(w["new"]) // 2) for w in tweak["writes"]]
    for w in writes():
        a, b = w["off"], w["off"] + len(w["new"]) // 2
        if any(a < y and x < b for x, y in taken):
            raise SystemExit(f"!! boucle des voix : 0x{a + BASE:08x} déjà écrit par {tweak['id']}")
    tweak["writes"] = sorted(tweak["writes"] + writes(), key=lambda w: w["off"])
    tweak["description"] = tweak["description"] + [NOTE]
    return tweak
