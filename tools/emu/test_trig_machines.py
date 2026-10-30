#!/usr/bin/env python3
"""Pas tenu + MACHINES (notes/86 §7, tools/trig_machines.py, écrit avec Model-TG) : le navigateur des machines du pas
s'ouvre au relâchement de MACHINES et seulement si rien d'autre n'a servi pendant. Le vrai code de l'interface de
l'OS (MainScreenView::consumeKeyEvent 0x4001c0d2, ParameterPageView::encoder 0x4001f4f0 et ::consumeKeyEvent
0x4001f97e) avec les accroches de 30-model-tg-st.json ; les constructeurs des navigateurs (DrumSelect 0x400a22b0,
PresetManager 0x400a68fc) et la mise à l'écran (0x40077da8) bouchés et notés. Banc repris de l'agent DSH
(docs/2026-10-30-trig-machines-dsh.md). L'état des pas : UIStates (0x400cf9a8) +0x15c (masque des pas tenus) et +0x164
(maintien).

    python3 tools/emu/test_trig_machines.py --cycles firmware/model-cycles_OS1.13.syx
"""
import argparse
import json
import pathlib
import struct
import sys

from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import build                        # noqa: E402
import lofi_ui as L                 # noqa: E402
import test_sdvintage as T          # noqa: E402
import trig_machines as TM          # noqa: E402

TWEAK = HERE.parent.parent / "tweaks" / "model-cycles_OS1.13" / "30-model-tg-st.json"
FAIL = []
OPEN = {0x400a68fc: "presetMgr", 0x400a22b0: "drumSelect", 0x40077da8: "push", 0x400cf23c: "dtor",
        0x4006bb22: "bb22", 0x4006f6e2: "islevel"}


def check(ok, msg):
    print(f"  {'ok  ' if ok else 'FAIL'}  {msg}")
    if not ok:
        FAIL.append(msg)


class R(L.UI):
    def __init__(self, img):
        self.log = []
        self._own = {}
        super().__init__(img, end=L.BASE + len(img))
        self.uc.reg_write(mk.UC_M68K_REG_SR, 0x2700)       # superviseur : l'OS lit et pose SR (move sr)
        self._own = {a: (n, 0) for a, n in OPEN.items()}
        self.hooks.update(self._own)
        self.seq = self.call(0x400cf9a8)

    def _hook(self, uc, addr, size, ud):
        if addr in self._own:
            sp = uc.reg_read(mk.UC_M68K_REG_A7)
            self.log.append(self._own[addr][0])
            uc.reg_write(mk.UC_M68K_REG_D0, 0)
            uc.reg_write(mk.UC_M68K_REG_PC, struct.unpack(">I", uc.mem_read(sp, 4))[0])
            uc.reg_write(mk.UC_M68K_REG_A7, sp + 4)
        else:
            super()._hook(uc, addr, size, ud)

    def state(self, mask, hold):
        self.uc.mem_write(self.seq + 0x15c, struct.pack(">II", mask, 0))
        self.uc.mem_write(self.seq + 0x164, bytes([hold]))

    def pend(self):
        return self.uc.mem_read(TM.SYMS["mt_pend"], 1)[0] if "mt_pend" in TM.SYMS else None

    def reset(self):
        if "mt_pend" in TM.SYMS:
            self.uc.mem_write(TM.SYMS["mt_pend"], bytes(3))

    def main(self, code, flags):
        obj = L.SCRATCH + 0x3000
        self.uc.mem_write(obj, struct.pack(">II", 0x400ffe20, 0) + bytes(300))
        self.uc.mem_write(obj + 44, struct.pack(">I", 0x90000000))
        ev = L.SCRATCH + 0x4000
        self.uc.mem_write(ev, struct.pack(">6I", 0, 0, 0x11223344, code, flags, 0))
        self.log.clear()
        try:
            d = self.call(0x4001c0d2, obj, ev)
        except Exception as e:                              # noqa: BLE001
            return ("FAULT", str(e))
        return d & 0xff, list(self.log), self.pend(), self.sp_ok and not self.bad

    def knob(self, num, step):
        obj = L.SCRATCH + 0x3000
        self.uc.mem_write(obj, struct.pack(">II", 0x4010052c, 0) + bytes(800))
        self.uc.mem_write(obj + 104, struct.pack(">I", L.SCRATCH + 0x200))
        self.uc.mem_write(L.SCRATCH + 0x200, b"".join(struct.pack(">I", i) for i in range(1, 7)))
        ev = L.SCRATCH + 0x4000
        self.uc.mem_write(ev, struct.pack(">6I", 0x400fbebc, 0, 0, num, step, 0))
        self.log.clear()
        try:
            d = self.call(0x4001f4f0, obj, ev)
        except Exception as e:                              # noqa: BLE001
            return ("FAULT", str(e))
        return d & 0xff, list(self.log), self.pend(), self.sp_ok and not self.bad

    def pkey(self, code, flags):
        obj = L.SCRATCH + 0x3000
        self.uc.mem_write(obj, struct.pack(">II", 0x40100534 - 8, 0) + bytes(800))
        ev = L.SCRATCH + 0x4000
        self.uc.mem_write(ev, struct.pack(">6I", 0, 0, 0x11223344, code, flags, 0))
        self.log.clear()
        try:
            d = self.call(0x4001f97e, obj, ev)
        except Exception as e:                              # noqa: BLE001
            return ("FAULT", str(e))
        return d & 0xff, list(self.log), self.pend(), self.sp_ok and not self.bad


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True)
    args = ap.parse_args()
    stock = T.main_os_from_syx(args.cycles)
    tw = json.loads(TWEAK.read_text(encoding="utf-8"))
    pl, _ = build.build_payload([tw], stock, None)
    img = build.apply_writes(stock, [tw])[0] + pl
    hooked = all(img[va - L.BASE:va - L.BASE + 6] == struct.pack(">HI", op, TM.SYMS[s]) for va, _, op, s, _ in TM.HOOKS)
    check(hooked, "quatre accroches posées dans le tweak de Model-TG (0x4001c0d2, 0x4001c27c, 0x4001f4f0, 0x4001f97e)")
    # référence : Model-TG sans nos écritures (les quatre accroches et le code dans les masques)
    mine = {w["off"] for w in TM.writes(stock)}
    ref_tw = dict(tw, writes=[w for w in tw["writes"] if w["off"] not in mine])
    ref = build.apply_writes(stock, [ref_tw])[0] + pl
    S, P = R(ref), R(img)
    check(S.init_ok and P.init_ok, "UI de l'OS construite (Model-TG sans trig_machines, et avec)")
    DRUM, PRESET = ["drumSelect", "push"], ["presetMgr", "push"]

    # 1. sans pas tenu, ou avec FUNC : l'OS, à l'appui
    rows = []
    for mask, hold, flags in ((0, 0, 1), (0, 1, 1), (1, 0, 3), (1, 1, 3)):
        for r in (S, P):
            r.reset()
            r.state(mask, hold)
        a, b = S.main(5, flags), P.main(5, flags)
        rows.append((mask, hold, flags, a[1], b[1]))
    check(all(a == b and a != [] for *_, a, b in rows),
          f"sans pas tenu, ou avec FUNC : le navigateur s'ouvre à l'appui, comme l'OS {[(m, h, f, b) for m, h, f, a, b in rows]}")

    # 2. pas tenu : appui avalé, ouverture au relâchement (le navigateur que l'appui aurait ouvert)
    out = []
    for hold_press, hold_rel, want in ((0, 0, DRUM), (1, 0, PRESET), (0, 1, DRUM)):
        P.reset()
        P.state(1, hold_press)
        a = P.main(5, 1)
        P.state(1, hold_rel)
        b = P.main(5, 0)
        out.append((a, b, want))
    check(all(a[0] == 1 and a[1] == [] and a[2] == 1 and a[3] and b[1][:2] == w and b[2] == 0 and b[3]
              for a, b, w in out),
          f"pas tenu : MACHINES avalée à l'appui (rien d'ouvert, attente notée), navigateur au relâchement, celui de "
          f"l'appui (DrumSelect, ou PresetManager quand le pas était en maintien) {[(a[1], b[1]) for a, b, _ in out]}")
    S.reset()
    S.state(1, 0)
    check(S.main(5, 1)[1][:2] == DRUM, "sans trig_machines, pas tenu : DrumSelect dès l'appui (le défaut signalé)")

    # 3. ce qui annule l'attente : un potard tourné, une autre touche ; pas le clic d'un potard ; le pas lâché
    res = {}
    P.reset(); P.state(1, 0); P.main(5, 1)
    res["clic"] = (P.knob(3, 0)[2], P.main(5, 0)[1])
    P.reset(); P.state(1, 0); P.main(5, 1)
    k = P.knob(3, 4)
    res["potard"] = (k[2], P.main(5, 0)[1], k[3])
    P.reset(); P.state(1, 0); P.main(5, 1)
    res["[LFO] page"] = (P.pkey(8, 1)[2], P.main(5, 0)[1])
    P.reset(); P.state(1, 0); P.main(5, 1)
    res["TRK"] = (P.main(3, 1)[2], P.main(5, 0)[1])
    P.reset(); P.state(1, 0); P.main(5, 1)
    res["relâchement autre"] = (P.main(3, 0)[2], P.main(5, 0)[1])
    P.reset(); P.state(1, 0); P.main(5, 1); P.state(0, 0)
    res["pas lâché"] = (P.main(5, 0)[1], P.pend())
    res = {k: tuple(x[:2] if isinstance(x, list) else x for x in v) for k, v in res.items()}
    ok = res["clic"] == (1, DRUM) and res["potard"][:2] == (0, []) and res["potard"][2] \
        and res["[LFO] page"] == (0, []) and res["TRK"] == (0, []) and res["relâchement autre"] == (1, DRUM) \
        and res["pas lâché"] == ([], 0)
    check(ok, f"attente annulée par un potard tourné, [LFO] (page des paramètres), une autre touche ; gardée par un clic "
              f"de potard et un relâchement ; pas lâché avant MACHINES : rien ne s'ouvre {res}")

    # 4. les prologues remplacés : la fonction de l'OS rend la même chose, sans attente. Chaque cas sur une interface
    # neuve des deux côtés : l'OS garde un état entre deux appels (le deuxième tour de potard d'affilée ne détruit plus
    # ses objets temporaires), et S et P ont eu des histoires différentes ci-dessus
    same = []
    for name, fa in (("encoder", lambda r: r.knob(3, 4)), ("encoder clic", lambda r: r.knob(2, 0)),
                     ("touche page", lambda r: r.pkey(8, 1)), ("touche page rel", lambda r: r.pkey(8, 0)),
                     ("main TRK", lambda r: r.main(3, 1)), ("main MACHINES rel", lambda r: r.main(5, 0))):
        s_, p_ = R(ref), R(img)
        for r in (s_, p_):
            r.reset()
            r.state(0, 0)
        a, b = fa(s_), fa(p_)
        a2, b2 = fa(s_), fa(p_)
        same.append((name, a[:2] == b[:2] and a[3] == b[3] and a2[:2] == b2[:2] and b2[3], a, b))
    check(all(x[1] for x in same), "prologues remplacés (encoder, touches de la page, MainScreenView), deux appels "
                                   "d'affilée sur une interface neuve : même retour, mêmes appels que sans trig_machines, "
                                   f"pile rendue {[(n, a, b) for n, ok, a, b in same if not ok]}")
    print("\nTOUT OK" if not FAIL else f"\n{len(FAIL)} ÉCHEC(S)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
