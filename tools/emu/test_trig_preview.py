#!/usr/bin/env python3
"""Preuve de la retouche de l'écoute d'un pas (tweak trig-preview de drumkilla, aussi dans Model-TG) : notes/34.

L'écoute (pas tenu + PAGE) refusait le séquenceur en pause : son code teste 0x4005481a (0x40a78874 | 0x40a7883c), qui
vaut 0 à l'arrêt, 1 en lecture et 2 en pause. Un Stop MIDI reçu (gestionnaire 0x40080a72, horloge reçue) met le
séquenceur en pause (0x40056060) même s'il était à l'arrêt ; PAGE tournait alors la page au lieu de faire sonner le pas,
jusqu'au redémarrage (ou à PLAY / STOP). La retouche : « tst.l d0 ; bne » devient « lsr.l #1,d0 ; bcs » (même taille),
l'écoute ne refuse plus que la lecture (bit 0).

Banc de tools/emu/test_trig_hold.py : la vraie chaîne des touches, le vrai PatternGridView::consumeKeyEvent (0x40022382)
et le vrai UIStates. Interceptés en plus : la construction de l'événement du pas (0x400548ce, comptée : une écoute),
son envoi au moteur audio (0x40092116), le changement de page (0x40013958, compté : une page tournée), la longueur de
la piste (16 pas) ; pour le Stop MIDI, la remise en place du pattern (0x40055af4).

  1. Octets : la retouche dans trig-preview, et dans model-tg / model-tg-st s'ils sont dans --with.
  2. Stop MIDI reçu, séquenceur à l'arrêt : la vraie fonction le met en pause (0x4005481a rend 2).
  3. Écoute à l'arrêt, en lecture, en pause : avant et après la retouche.
  4. Après un Stop MIDI, pas tenu et trois appuis sur PAGE : écoutes ou pages tournées, trig gardé.

    python3 tools/emu/test_trig_preview.py --cycles model-cycles_OS1.13.syx \\
        [--with 6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm,arp,trig-hold --syntakt Syntakt_OS1.42.syx]
"""
import argparse
import json
import pathlib
import struct
import sys

from unicorn import UC_HOOK_CODE

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import build                        # noqa: E402
import test_sdvintage as T          # noqa: E402
import test_trig_hold as H          # noqa: E402

DEV = HERE.parent.parent / "tweaks" / "model-cycles_OS1.13"
BASE = build.BASE
FAIL = []

GATE = 0x40148a2a                 # jsr 0x4005481a, puis le test de l'état du séquenceur (code de l'écoute)
OLD = bytes.fromhex("4eb94005481a" "4a80" "66000138")       # tst.l d0 ; bne.w (drumkilla)
NEW = bytes.fromhex("4eb94005481a" "e288" "65000138")       # lsr.l #1,d0 ; bcs.w (notes/34)
SEQ_STATE = 0x4005481a            # 0x40a78874 | 0x40a7883c : 0 arrêt, 1 lecture, 2 pause
SEQ_A, SEQ_B = 0x40a78874, 0x40a7883c
MIDI_STOP = 0x40080a72            # Stop MIDI reçu (entrée 0xFC de la table 0x40112960)
CLOCK_RX = 0x40a70144             # horloge MIDI reçue (réglage)
BUILD_EV, SEND_EV, SET_PAGE = 0x400548ce, 0x40092116, 0x40013958
PAT, KIT = 0x93010000, 0x93020000
PAGE, STEP = 15, 16               # codes des touches PAGE et pas 1
STATES = {0: "arrêt", 1: "lecture", 2: "pause"}


def check(ok, msg):
    print(("  ok    " if ok else "  ECHEC ") + msg, flush=True)
    if not ok:
        FAIL.append(msg)


class Rig(H.Rig):
    """Le banc du mode grille, avec l'écoute : événements du pas et pages tournées comptés."""

    def __init__(self, img):
        super().__init__(img)
        self.previews, self.pages = [], []
        stubs = {
            BUILD_EV: self._build, SEND_EV: lambda a: 0, SET_PAGE: self._page,
            0x4000f23e: lambda a: H.FAKE, 0x40016402: lambda a: 16, 0x4000eb90: lambda a: H.FAKE,
            0x40055af4: lambda a: 0,
        }
        for addr, fn in stubs.items():
            self.uc.hook_add(UC_HOOK_CODE, self._stub(fn), begin=addr, end=addr)
        self.uc.mem_write(PAT, bytes(0x8000))
        self.uc.mem_write(KIT, bytes(0x1000))
        self.w32(0x40a7887c, PAT)
        self.w32(0x40a78888, KIT)

    def _post(self, a):
        if a[0] == self.r32(0x40148cd0):                     # boîte des touches ; la pause y poste un message de type 8
            return super()._post(a)
        return 0

    def _build(self, a):
        self.previews.append((self.now, a[3]))
        return 0

    def _page(self, a):
        self.pages.append(self.now)
        return 0

    def seq(self, state):
        self.w32(SEQ_A, state)
        self.w32(SEQ_B, state)

    def midi_stop(self):
        self.w32(CLOCK_RX, 1)
        self.call(MIDI_STOP, 0, 0, 0)
        return self.call(SEQ_STATE)


def variant(img, code):
    out = bytearray(img)
    o = GATE - BASE
    assert out[o:o + 12] in (OLD, NEW), out[o:o + 12].hex()
    out[o:o + 12] = code
    return bytes(out)


def taps(rig, n):
    """Pas 1 tenu, n appuis sur PAGE, pas relâché."""
    ev = {10: [(STEP, True)]}
    t = 300
    for _ in range(n):
        ev.setdefault(t, []).append((PAGE, True))
        ev.setdefault(t + 100, []).append((PAGE, False))
        t += 300
    ev.setdefault(t, []).append((STEP, False))
    rig.trigs[0] = "note"
    rig.run(ev, t + 300)
    return len(rig.previews), len(rig.pages), rig.trigs.get(0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--with", dest="others", default="", help="autres tweaks (ex. 6ch-usbup,model-tg,arp,trig-hold)")
    ap.add_argument("--syntakt", help="Syntakt_OS1.42.syx (ou 1.41), pour les moteurs du Syntakt")
    args = ap.parse_args()
    stock = T.main_os_from_syx(args.cycles)
    by_id = {json.loads(f.read_text(encoding="utf-8"))["id"]: f for f in DEV.glob("*.json") if f.name != "device.json"}
    load = lambda i: json.loads(by_id[i].read_text(encoding="utf-8"))
    others = [i for i in args.others.split(",") if i]
    ids = others if any(i.startswith("model-tg") for i in others) else ["trig-preview"] + others
    tweaks = [load(i) for i in ids]
    pl, _ = build.build_payload(tweaks, stock, args.syntakt)
    fixed = build.apply_writes(stock, tweaks)[0] + pl
    orig = variant(fixed, OLD)
    print(f"firmware : {', '.join(ids)}")

    print("octets")
    o = GATE - BASE
    check(stock[o:o + 12] == b"\xff" * 12, f"{GATE:#x} : zone libre dans l'OS d'origine")
    for i in ids:
        if i in ("trig-preview", "model-tg", "model-tg-st"):
            img = build.apply_writes(stock, [load(i)])[0]
            check(img[o:o + 12] == NEW, f"{i} : lsr.l #1,d0 ; bcs.w après jsr 0x4005481a")

    print("Stop MIDI reçu, séquenceur à l'arrêt")
    for name, img in (("origine", orig), ("retouché", fixed)):
        rig = Rig(img)
        before = rig.call(SEQ_STATE)
        after = rig.midi_stop()
        check(before == 0 and after == 2, f"{name} : 0x4005481a rend {before} puis {after} (pause)")

    print("écoute selon l'état du séquenceur (pas 1 tenu, PAGE)")
    want = {("origine", 0): (1, 0), ("origine", 1): (0, 1), ("origine", 2): (0, 1),
            ("retouché", 0): (1, 0), ("retouché", 1): (0, 1), ("retouché", 2): (1, 0)}
    for name, img in (("origine", orig), ("retouché", fixed)):
        for state, label in STATES.items():
            rig = Rig(img)
            rig.seq(state)
            n, p, trig = taps(rig, 1)
            ok = (n, p) == want[(name, state)] and trig == "note"
            check(ok, f"{name}, {label:7s} : {n} écoute, {p} page tournée, trig {'gardé' if trig else 'perdu'}")

    print("après un Stop MIDI : pas tenu, trois appuis sur PAGE")
    for name, img, exp in (("origine", orig, (0, 3)), ("retouché", fixed, (3, 0))):
        rig = Rig(img)
        rig.midi_stop()
        n, p, trig = taps(rig, 3)
        check((n, p) == exp and trig == "note", f"{name} : {n} écoutes, {p} pages tournées, trig "
                                                f"{'gardé' if trig else 'perdu'}")
    print("\nTOUT OK" if not FAIL else f"\n{len(FAIL)} ÉCHEC(S)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
