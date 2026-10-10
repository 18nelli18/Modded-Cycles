#!/usr/bin/env python3
"""Preuve de l'écoute des samples au casque (cue split, notes/48 ; tweaks/model-cycles_OS1.13/34-sample-cue.json
avec l'écoute des samples pour Model-TG, 34-sample-cue-st.json pour sa version avec les moteurs du Syntakt).

Le vrai code de l'OS, de Model-TG et de l'écoute des samples, exécuté (Unicorn) sur deux images construites depuis le
.syx officiel : l'« origine » = Model-TG + l'écoute des samples (et les tweaks de --with), l'image modifiée = la même
plus ce tweak. Le banc est celui de tools/emu/test_sample_preview.py (Rig : navigateur, note jouée, Model-TG) ; le
lecteur est exécuté à son accroche, en 0x40059878 (fin de 0x4005979e, dans l'interruption audio), sur une moitié du
ring des jacks, le mix USB et des samples remplis au hasard (graine fixe), et comparé à un modèle numpy.

  1. Écritures : octets d'origine (ceux de l'image avec l'écoute des samples) ; l'image ne diffère de l'origine que
     par elles ; aucune ne recouvre un tweak qui peut aller avec (gen_sample_cue.check_overlaps) ; refusé sans
     l'écoute des samples (requires) ; les cinq masques 48x22 ne sont plus désignés, leur sprite prend la copie
     gardée ; accroches = jmp vers le code ; données de départ (GO … POS à 0, TRK = NOTE = -1).
  2. Interface (vrais 0x4008171e avec pv_note, 0x4008145e, 0x40081bd6, 0x400a64be) : sample sous le curseur en
     mémoire -> l'origine envoie la note d'écoute à la piste ; le tweak n'envoie rien (ni moteur audio, ni message
     d'enregistrement), les compteurs de notes tenues reviennent à l'état d'avant, d2-d7/a2-a6 rendus, niveau
     d'interruption rendu, et l'écoute démarre (case, empreinte, adresse, nombre, gain = vélocité × 106, gain d'une
     prise, plafonné). Relâchement de cet appui : rien n'est envoyé, arrêt demandé ; autre note, autre source :
     identique à l'origine. Preset désigné, autre piste, autre source, appui « sans envoi », sample pas en mémoire
     (chargement raté), prise du rééchantillonnage : identique à l'origine, l'écoute ne démarre pas. Chargement
     réussi au premier appui : l'écoute démarre sur la case chargée. Curseur bougé : arrêt demandé ; même son
     désigné : rien, d0/d1/a1 gardés. Chargement d'un fichier (cue_load) : arrêt demandé, tous les registres et la pile
     intacts, puis la fonction d'origine.
  3. Lecteur (accroche 0x40059878, les trois sorties de sample_cue.S : split, jacks, USB) : sortie exacte face au
     modèle (repos, lecture, fin du sample, case vidée ou déplacée, nombre réduit, fondu d'arrêt, écrêtage, plan
     stéréo valide ou non) ; lectures des samples seulement dans les échantillons de ce bloc ; écritures seulement
     dans la moitié des jacks (ou le mix USB) et cue_data ; d2-d7/a4-a6, a2/a3 de la pile et la pile rendus ;
     l'origine ne touche à rien. Coût en instructions.
  4. Puce audio (vrais 0x400445ec et 0x400447b6, réglage du volume) : l'origine écrit OUT1_R (registre 0x1F) comme
     OUT1_L ; le tweak (split) y écrit 0 ; le reste à l'identique.
  5. De bout en bout : navigateur -> pad -> trois blocs audio -> relâchement -> fondu -> silence de l'écoute ; un
     nouvel appui repart du début.

    python3 tools/emu/test_sample_cue.py --cycles model-cycles_OS1.13.syx \\
        [--with 6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm,arp,trig-hold,tempo-max,boot-anim \\
         --syntakt Syntakt_OS1.42.syx]
"""
import argparse
import json
import pathlib
import struct
import sys

import numpy as np
from unicorn import UcError, UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE
from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import build                        # noqa: E402
import gen_sample_cue as G          # noqa: E402
import sprites                      # noqa: E402
import test_sample_preview as SP    # noqa: E402
import test_sdvintage as T          # noqa: E402

TW = HERE.parent.parent / "tweaks" / "model-cycles_OS1.13"
BASE = build.BASE
FAIL = []

NOTE_ON, NOTE_OFF, ARM, LOAD = 0x4008171e, 0x4008145e, 0x40081bd6, 0x400a64fa
ACTIVE, ARMED, NOTES = SP.ACTIVE, SP.ARMED, 0x40fb5c0c
TAIL_HOOK = 0x40059878            # fin de 0x4005979e : lea 20(sp),sp ; movea.l (sp)+,a2 ; movea.l (sp)+,a3 ; rts
HALF = 0x4a3ed180                 # moitié haute du ring DMA des jacks (vue sans cache)
USB_MIX = 0x40fe4b90
STATE = 0x93001234
STOP = SP.STOP
CALLEE, CALLEE_VALS = SP.CALLEE, SP.CALLEE_VALS
FIELDS = ("go", "stop", "slot", "hash", "base", "count", "soff", "gain", "pos", "trk", "note")
SLOT, H1, H2, RS_H = 7, SP.H1, SP.H2, 0x524d0011
PCM = 0x4c200000                  # échantillons du banc (zone avec cache de Model-TG)
N = 4000                          # échantillons par plan
RNG = np.random.default_rng(48)
STOP_CASE = "fondu d'arrêt"


def check(ok, msg):
    print(("  ok    " if ok else "  ECHEC ") + msg, flush=True)
    if not ok:
        FAIL.append(msg)


class Variant:
    """Les tweaks choisis + Model-TG + l'écoute des samples (origine), et la même chose avec ce tweak."""

    def __init__(self, stock, ids, by_id, syntakt_file):
        load = (lambda i: json.loads(by_id[i].read_text(encoding="utf-8")))
        st = "model-tg-st" in ids
        self.pv = load("sample-preview-st" if st else "sample-preview")
        self.cue = load("sample-cue-st" if st else "sample-cue")
        self.tweaks = sorted([load(i) for i in ids] + [self.pv], key=lambda t: t["order"])
        self.tg = next(t for t in self.tweaks if t["id"] in ("model-tg", "model-tg-st"))
        self.label = ", ".join(t["id"] for t in self.tweaks)
        pl, _ = build.build_payload(self.tweaks, stock, syntakt_file)
        self.base = bytes(build.apply_writes(stock, self.tweaks)[0]) + pl
        self.img = bytes(build.apply_writes(stock, sorted(self.tweaks + [self.cue], key=lambda t: t["order"]))[0]) + pl
        self.pl = pl
        self.end = BASE + len(stock) + self.tg["append"]["size"]
        syn = [t for t in self.tweaks if t.get("append", {}).get("syntakt")]
        self.payload = None
        if syn:
            import syntakt
            self.payload = (int(syn[0]["append"]["dest"], 16),
                            build.payload_runtime(syn[0], stock, syntakt.dsp_image(syntakt_file)))
        self.tgs = {n: int(v, 16) for n, v in self.tg["symbols"].items()}
        self.pvs = {n: int(v, 16) for n, v in self.pv["symbols"].items()}
        self.cs = {n: int(v, 16) for n, v in self.cue["symbols"].items()}

    def with_mode(self, stock, mode):
        """Image avec le lecteur assemblé pour une autre sortie (CUE_MODE de sample_cue.S)."""
        writes, cue, _ = G.build_writes(stock, mode, *self.syms())
        t = {"id": f"sample-cue-{mode}", "order": 34, "writes": writes}
        img = bytes(build.apply_writes(stock, sorted(self.tweaks + [t], key=lambda x: x["order"]))[0]) + self.pl
        return img, cue

    def syms(self):
        tg = {n: self.tgs[n] for n in set(G.TG_DEFS.values())}
        return tg, {"pv_src": self.pvs["pv_src"]}


# --- état du lecteur ------------------------------------------------------------------------------------------------
def cue_state(r, data):
    vals = struct.unpack(">11i", r.mem(data, 44))
    st = dict(zip(FIELDS, vals))
    st["held"] = struct.unpack(">4I", r.mem(data + 44, 16))
    return st


def set_state(r, data, **kw):
    for k, val in kw.items():
        r.w32(data + 4 * FIELDS.index(k), val)


def put_sample(r, slot, h, base, mid, side=None, pgain=0):
    """Une case de Model-TG : en-tête de 64 o, plan milieu, plan côté (soff = 2 × N) s'il y en a un."""
    tg = r.v.tgs
    body = mid.astype(">i2").tobytes() + (side.astype(">i2").tobytes() if side is not None else b"")
    r.uc.mem_write(base, bytes(64) + body + bytes(16))
    for name, val in (("slot_hash", h), ("slot_base", base), ("slot_count", len(mid)),
                      ("slot_soff", 2 * len(mid) if side is not None else 0), ("slot_pgain", pgain)):
        r.w32(tg[name] + 4 * slot, val)


# --- 1. écritures ---------------------------------------------------------------------------------------------------
def writes_tests(v):
    cue, cs = v.cue, v.cs
    ok_old = all(v.base[w["off"]:w["off"] + len(bytes.fromhex(w["old"]))] == bytes.fromhex(w["old"])
                 for w in cue["writes"])
    check(ok_old, f"{cue['id']} : {len(cue['writes'])} écritures, octets d'origine = l'image avec "
                  f"{v.pv['id']} (masques, constantes des sprites, accroches)")
    spans = [(w["off"], w["off"] + len(bytes.fromhex(w["new"]))) for w in cue["writes"]]
    dif = [k for k in range(len(v.base)) if v.base[k] != v.img[k]] if len(v.base) == len(v.img) else None
    check(dif is not None and all(any(lo <= k < hi for lo, hi in spans) for k in dif),
          f"l'image modifiée ne diffère de l'origine que dans ces écritures ({len(dif or [])} octets)")
    try:
        G.check_overlaps([cue])
        alone = True
    except SystemExit as ex:
        alone, why = False, str(ex)
    mine = [(w["off"], w["off"] + len(bytes.fromhex(w["old"]))) for w in cue["writes"]]
    bad = [f"{o['id']}@{w['off'] + BASE:#x}" for o in v.tweaks for w in o["writes"]
           for lo, hi in mine if w["off"] < hi and lo < w["off"] + len(bytes.fromhex(w["old"]))]
    check(alone and not bad, f"aucun recouvrement avec {v.label}, ni avec les tweaks du catalogue qui peuvent aller "
                             f"avec {'' if alone else why} {bad[:4]}")
    refused = []
    for combo in ([v.tg, cue], [cue]):
        try:
            build.check_conflicts(combo)
            refused.append(False)
        except SystemExit:
            refused.append(True)
    try:
        build.check_conflicts([v.tg, v.pv, cue])
        accepted = True
    except SystemExit:
        accepted = False
    check(all(refused) and accepted, f"build : {cue['id']} refusé sans {v.pv['id']} (requires), accepté avec")
    masks = [m for _, m in G.CAVES]

    def refs(img, m):                                  # hors des écritures du tweak (ses accroches et ses jmp)
        k, out = img.find(m.to_bytes(4, "big")), []
        while k >= 0:
            if not any(lo <= k < hi for lo, hi in spans):
                out.append(k)
            k = img.find(m.to_bytes(4, "big"), k + 1)
        return out
    gone = all(not refs(v.img, m) and v.base.count(m.to_bytes(4, "big")) == 1
               and v.img[sprites.MASKS[m][1] - BASE:][:4] == sprites.SHARED_48.to_bytes(4, "big") for m in masks)
    shared = v.img.count(sprites.SHARED_48.to_bytes(4, "big")) - v.base.count(sprites.SHARED_48.to_bytes(4, "big"))
    check(gone and shared == len(masks),
          f"les {len(masks)} masques 48x22 ne sont plus désignés que par les accroches et le code du tweak ; leurs sprites "
          f"prennent la copie gardée "
          f"({sprites.SHARED_48:#x}, {shared} constantes de plus)")
    at = {w["off"] + BASE: bytes.fromhex(w["new"]) for w in cue["writes"]}
    jmp = (lambda s: struct.pack(">HI", 0x4ef9, cs[s]))
    check(at.get(0x4008180e) == jmp("cue_dec") and at.get(NOTE_OFF) == jmp("cue_off") and at.get(ARM) == jmp("cue_arm")
          and at.get(TAIL_HOOK) == jmp("cue_out") and at.get(0x400a6bec) == struct.pack(">I", cs["cue_load"])
          and at.get(0x40044614) == bytes.fromhex("42a7"),
          "accroches : 0x4008180e jmp cue_dec, 0x4008145e jmp cue_off, 0x40081bd6 jmp cue_arm, 0x40059878 jmp "
          "cue_out, 0x400a6bec = cue_load, 0x40044614 clr.l -(sp) (registre 0x1F à 0)")
    d = cs["cue_data"] - BASE
    vals = struct.unpack(">15i", v.img[d:d + 60])
    check(vals == (0,) * 9 + (-1, -1) + (0,) * 4 and any(lo <= d and d + 60 <= hi for lo, hi in spans),
          f"cue_data ({cs['cue_data']:#x}) : GO … POS à 0, TRK = NOTE = -1, notes tenues à 0, dans l'image")


# --- 2. interface ---------------------------------------------------------------------------------------------------
def rigs(v):
    out = []
    for img in (v.base, v.img):
        r = SP.Rig(v, img)
        r.w32(ARMED, 0)
        put_sample(r, SLOT, H1, PCM, RNG.integers(-30000, 30000, N))
        out.append(r)
    return out


def note(r, t, n=60, vel=100, src=0x40, held=0):
    r.posted.clear()
    r.ui.clear()
    before = r.mem(NOTES, 4 * 128 * 6)
    r.call(NOTE_ON, t, n, vel, src, held, 0xffffffff, 0xffffffff, sr=0x2000, regs=True)
    return dict(posted=list(r.posted), ui=len(r.ui), notes=r.mem(NOTES, 4 * 128 * 6) == before,
                regs=r.regs_after == CALLEE_VALS, sr=r.sr_after & 0x700)


def release(r, t, n=60, src=0x40):
    r.posted.clear()
    r.ui.clear()
    r.call(NOTE_OFF, t, n, src, sr=0x2000, regs=True)
    return dict(posted=list(r.posted), ui=len(r.ui), regs=r.regs_after == CALLEE_VALS)


def ui_tests(v):
    data = v.cs["cue_data"]
    o, m = rigs(v)
    for r in (o, m):
        r.browse(0)                                    # 2 Mo, empreinte H1, en mémoire (case SLOT)
    armed = (o.r32(ARMED), m.r32(ARMED))
    same_src = m.mem(armed[1], 100) == m.mem(v.pvs["pv_src"], 100)
    a, b = note(o, 2), note(m, 2)
    st = cue_state(m, data)
    check(armed[0] and armed[1] and same_src and len(a["posted"]) == 1 and a["ui"] == 1
          and struct.unpack(">I", a["posted"][0][52:56])[0] == armed[0],
          "origine : le curseur désigne le sample (copie exacte de pv_src) ; le pad envoie la note d'écoute à la "
          "piste (son désigné dans l'événement), avec son message d'enregistrement")
    check(not b["posted"] and b["ui"] == 0 and b["notes"] and b["regs"] and b["sr"] == 0 and m.clean()
          and st["go"] == 1 and st["stop"] == 0 and st["slot"] == SLOT and st["hash"] == H1 and st["base"] == PCM
          and st["count"] == N and st["soff"] == 0 and st["gain"] == 100 * 106 and st["pos"] == 0
          and st["trk"] == 2 and st["note"] == 60 and st["held"] == (0, 1 << 28, 0, 0),
          f"modifié : rien n'est envoyé (ni note, ni message), compteurs de notes tenues rendus, d2-d7/a2-a6 rendus, "
          f"niveau 0 rendu ; l'écoute démarre : case {st['slot']}, empreinte {st['hash']:#x}, {st['count']} "
          f"échantillons, gain {st['gain']}, note 60 tenue")
    a, b = release(o, 2), release(m, 2)
    st = cue_state(m, data)
    check(len(a["posted"]) == 1 and not b["posted"] and b["ui"] == 0 and b["regs"] and st["stop"] != 0
          and st["go"] == 1 and st["held"] == (0, 0, 0, 0),
          "relâchement : l'origine envoie la fin de note ; le tweak rien, demande l'arrêt (fondu dans l'interruption), "
          "la note n'est plus tenue")
    # autres appuis : identiques à l'origine, l'écoute ne démarre pas
    for name, kw, prep in (("source 0x80 (MIDI)", dict(src=0x80), None), ("autre piste (1)", dict(t=0), None),
                           ("appui « sans envoi »", dict(held=1), None), ("preset désigné", {}, lambda r: r.browse(1))):
        res = []
        for r in (o, m):
            r.browse(0)
            if prep:
                prep(r)
            if r is m:
                set_state(r, data, go=0, stop=0)
            k = dict(kw)
            t = k.pop("t", 2)
            res.append(note(r, t, **k))
            res[-1]["rel"] = release(r, t, src=k.get("src", 0x40))
        st = cue_state(m, data)
        x, y = res
        check([p[:52] for p in x["posted"]] == [p[:52] for p in y["posted"]] and x["ui"] == y["ui"] and y["regs"]
              and [p[:52] for p in x["rel"]["posted"]] == [p[:52] for p in y["rel"]["posted"]] and st["go"] == 0,
              f"{name} : note et relâchement identiques à l'origine ({len(x['posted'])} + {len(x['rel']['posted'])} "
              f"événement(s)), l'écoute ne démarre pas")
    # pas en mémoire : chargement raté (rien ne joue, comme pv_note), puis réussi (l'écoute démarre sur cette case)
    for r in (o, m):
        r.browse(3)                                    # 2 Mo, empreinte H2, pas en mémoire
        r.loader = lambda h: -1
    set_state(m, data, go=0)
    a, b = note(o, 2), note(m, 2)
    check(not a["posted"] and not b["posted"] and a["ui"] == b["ui"] == 1 and b["notes"] is False
          and cue_state(m, data)["go"] == 0,
          "sample pas en mémoire, chargement raté : rien ne joue, comme l'écoute des samples seule (message "
          "d'enregistrement et note tenue comme l'origine) ; l'écoute ne démarre pas")
    release(o, 2)
    release(m, 2)

    def loaded(r):
        def ld(h, r=r):
            put_sample(r, 9, h, PCM + 0x100000, RNG.integers(-30000, 30000, 1000))
            return 9
        r.loader = ld
    for r in (o, m):
        loaded(r)
        r.browse(4)
        r.browse(3)
    a, b = note(o, 2, n=64, vel=127), note(m, 2, n=64, vel=127)
    st = cue_state(m, data)
    check(len(a["posted"]) == 1 and not b["posted"] and b["notes"] and b["regs"] and st["go"] == 1
          and st["slot"] == 9 and st["hash"] == H2 and st["count"] == 1000 and st["gain"] == 127 * 106
          and st["held"] == (0, 0, 1 << 0, 0),
          f"chargé au premier appui (pv_note) : l'origine joue la note ; le tweak démarre l'écoute sur la case chargée "
          f"(case {st['slot']}, gain {st['gain']} pour la vélocité 127)")
    release(m, 2, n=64)
    # gain d'une prise (Q12), plafonné
    for pg, vel, want in ((2048, 100, 10600 * 2048 >> 12), (3 * 4096, 127, 32767)):
        m.w32(v.tgs["slot_pgain"] + 4 * 9, pg)
        set_state(m, data, go=0)
        note(m, 2, n=65, vel=vel)
        release(m, 2, n=65)
        check(cue_state(m, data)["gain"] == want, f"gain de la prise {pg / 4096:g}, vélocité {vel} : {want}")
    # une prise du rééchantillonnage (empreinte 0x524d00nn, dernière entrée du navigateur) ne passe jamais par l'écoute
    res = []
    for r in (o, m):
        put_sample(r, 11, RS_H, PCM + 0x200000, RNG.integers(-100, 100, 100))
        r.browse(len(SP.FILES) - 1)
        if r is m:
            set_state(r, data, go=0)
        res.append(note(r, 2, n=70))
        release(r, 2, n=70)
    check(len(res[0]["posted"]) == 1 and not res[1]["posted"] and cue_state(m, data)["go"] == 0,
          "prise du rééchantillonnage sous le curseur (0x524d0011) : l'écoute ne démarre pas, rien ne joue")
    # le son désigné change : arrêt ; le même : rien, d0/d1/a1 gardés
    set_state(m, data, go=1, stop=0)
    m.browse(0)
    s1 = cue_state(m, data)["stop"]
    set_state(m, data, stop=0)
    for reg, val in ((mk.UC_M68K_REG_D0, 0x0d0d0d0d), (mk.UC_M68K_REG_D1, 0x1d1d1d1d), (mk.UC_M68K_REG_A1, 0x1a1a1a1a)):
        m.uc.reg_write(reg, val)
    cur = m.r32(ARMED)
    m.call(ARM, cur, sr=0x2000)
    kept = [m.uc.reg_read(x) for x in (mk.UC_M68K_REG_D0, mk.UC_M68K_REG_D1, mk.UC_M68K_REG_A1)]
    s2 = cue_state(m, data)["stop"]
    m.call(ARM, 0, sr=0x2000)
    check(s1 != 0 and s2 == 0 and kept == [0x0d0d0d0d, 0x1d1d1d1d, 0x1a1a1a1a] and m.r32(ARMED) == 0
          and cue_state(m, data)["stop"] != 0,
          "son désigné : curseur bougé -> arrêt demandé ; même son -> rien, d0/d1/a1 gardés ; plus rien (fermeture) "
          "-> arrêt demandé ; ARMED écrit comme l'origine")
    # chargement d'un fichier : cue_load, puis la fonction d'origine, sans rien toucher
    got = {}

    def at_load(uc, a, size, ud):
        got["regs"] = [uc.reg_read(getattr(mk, f"UC_M68K_REG_{r}")) for r in
                       ("D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7")]
        uc.reg_write(mk.UC_M68K_REG_PC, STOP)
    h = m.uc.hook_add(UC_HOOK_CODE, at_load, begin=LOAD, end=LOAD)
    marks = [0xd0000000 + i for i in range(8)] + [0xa0000000 + i for i in range(7)]
    names = ("D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "A0", "A1", "A2", "A3", "A4", "A5", "A6")
    set_state(m, data, stop=0)
    for r_, val in zip(names, marks):
        m.uc.reg_write(getattr(mk, f"UC_M68K_REG_{r_}"), val)
    m.uc.reg_write(mk.UC_M68K_REG_A7, SP.CALL_SP - 16)
    m.uc.mem_write(SP.CALL_SP - 16, struct.pack(">4I", STOP, 0x11, 0x22, 0x33))
    m.uc.emu_start(v.cs["cue_load"], STOP, count=1000)
    m.uc.hook_del(h)
    ptr = struct.unpack(">I", v.img[0x400a6bec - BASE:0x400a6bec - BASE + 4])[0]
    check(ptr == v.cs["cue_load"] and struct.unpack(">I", v.base[0x400a6bec - BASE:][:4])[0] == LOAD
          and got.get("regs") == marks + [SP.CALL_SP - 16] and cue_state(m, data)["stop"] == 1
          and m.mem(SP.CALL_SP - 16, 16) == struct.pack(">4I", STOP, 0x11, 0x22, 0x33),
          "chargement d'un fichier : la fonction installée est cue_load (origine : 0x400a64fa) ; arrêt demandé, puis "
          "0x400a64fa avec tous les registres et la pile intacts")
    check(o.clean() and m.clean() and not m.low, "aucun accès hors mémoire")


# --- 3. lecteur -----------------------------------------------------------------------------------------------------
def block(r, jacks, usb):
    """Un passage à l'accroche 0x40059878, comme à la fin de 0x4005979e (interruption audio, niveau 5)."""
    uc = r.uc
    uc.mem_write(HALF, struct.pack(">64i", *jacks))
    uc.mem_write(USB_MIX, struct.pack(">64i", *usb))
    sp = SP.CALL_SP - 0x100
    frame = struct.pack(">5I", HALF, STATE, 1, 2, 3) + struct.pack(">3I", 0x1111a2a2, 0x1111a3a3, STOP)
    uc.mem_write(sp - 0x400, b"\xa5" * 0x400)
    uc.mem_write(sp, frame)
    uc.reg_write(mk.UC_M68K_REG_A7, sp)
    uc.reg_write(mk.UC_M68K_REG_SR, 0x2500)
    keep = CALLEE[:6] + CALLEE[8:]                     # d2-d7, a4-a6
    vals = CALLEE_VALS[:6] + CALLEE_VALS[8:]
    for x, val in zip(keep, vals):
        uc.reg_write(x, val)
    for x in (mk.UC_M68K_REG_A2, mk.UC_M68K_REG_A3, mk.UC_M68K_REG_D0, mk.UC_M68K_REG_D1, mk.UC_M68K_REG_A0,
              mk.UC_M68K_REG_A1):
        uc.reg_write(x, 0xdeadbeef)
    reads, writes, n = [], [], [0]

    def rd(uc, access, addr, size, value, ud):
        if 0x4c000000 <= addr < 0x4e000000:
            reads.append(addr)

    def wr(uc, access, addr, size, value, ud):
        if not sp - 0x400 <= addr < sp + len(frame):
            writes.append(addr)

    def ins(uc, a, size, ud):
        n[0] += 1
    hooks = [uc.hook_add(UC_HOOK_MEM_READ, rd), uc.hook_add(UC_HOOK_MEM_WRITE, wr), uc.hook_add(UC_HOOK_CODE, ins)]
    err = None
    try:
        uc.emu_start(TAIL_HOOK, STOP, count=100_000)
    except UcError as ex:
        err = f"{ex} en {uc.reg_read(mk.UC_M68K_REG_PC):#x}"
    for h in hooks:
        uc.hook_del(h)
    ok = (err is None and uc.reg_read(mk.UC_M68K_REG_PC) == STOP and uc.reg_read(mk.UC_M68K_REG_A7) == sp + len(frame)
          and [uc.reg_read(x) for x in keep] == vals and uc.reg_read(mk.UC_M68K_REG_A2) == 0x1111a2a2
          and uc.reg_read(mk.UC_M68K_REG_A3) == 0x1111a3a3)
    return dict(jacks=list(struct.unpack(">64i", r.mem(HALF, 256))), usb=list(struct.unpack(">64i", r.mem(USB_MIX, 256))),
                reads=reads, writes=sorted(set(writes)), ok=ok, err=err, n=n[0])


def clip(x, lo, hi):
    return max(lo, min(hi, x))


def model(mode, jacks, usb, st, slot, mid, side):
    """Ce que doit faire le lecteur (sample_cue.S) : (jacks, usb, go, pos, échantillons lus)."""
    J, U = list(jacks), list(usb)
    if mode == "split":
        for i in range(32):
            J[2 * i] = J[2 * i + 1] = (J[2 * i] + J[2 * i + 1]) >> 1
    if not st["go"]:
        return J, U, 0, st["pos"], range(0)
    if slot["hash"] != st["hash"] or slot["base"] != st["base"]:
        return J, U, 0, st["pos"], range(0)
    n = slot["count"] if slot["count"] <= st["count"] else st["count"]
    rem = n - st["pos"]
    if rem <= 0:
        return J, U, 0, st["pos"], range(0)
    k, p0 = min(32, rem), st["pos"]
    g0, step = st["gain"], (st["gain"] >> 5 if st["stop"] else 0)
    stereo = st["soff"] != 0 and slot["soff"] == st["soff"]
    for i in range(k):
        mm, ss, g = int(mid[p0 + i]), (int(side[p0 + i]) if stereo else 0), g0 - i * step
        if mode == "split":
            J[2 * i + 1] = clip(J[2 * i + 1] - ((mm * g) >> 8), -0x800000, 0x7fffff)
        elif mode == "jacks":
            J[2 * i] = clip(J[2 * i] - (((mm + ss) * g) >> 8), -0x800000, 0x7fffff)
            J[2 * i + 1] = clip(J[2 * i + 1] - (((mm - ss) * g) >> 8), -0x800000, 0x7fffff)
        else:
            U[2 * i] = clip(U[2 * i] + (mm + ss) * g, -0x80000000, 0x7fffffff)
            U[2 * i + 1] = clip(U[2 * i + 1] + (mm - ss) * g, -0x80000000, 0x7fffffff)
    return J, U, (0 if st["stop"] else 1), p0 + k, range(p0, p0 + k)


def player_tests(v, stock):
    images = [("split", v.img, v.cs)] + [(md, *v.with_mode(stock, md)) for md in ("jacks", "usb")]
    o = SP.Rig(v, v.base)
    for mode, img, cs in images:
        r = SP.Rig(v, img)
        data = cs["cue_data"]
        mid = RNG.integers(-32768, 32768, N)
        side = RNG.integers(-32768, 32768, N)
        put_sample(r, SLOT, H1, PCM, mid, side)
        put_sample(o, SLOT, H1, PCM, mid, side)
        tg = v.tgs
        cases = [
            ("repos", dict(go=0), {}, {}),
            ("lecture, début", dict(go=1, pos=0), {}, {}),
            ("lecture, plus loin", dict(go=1, pos=1234), {}, {}),
            ("fin du sample (8 restants)", dict(go=1, pos=N - 8), {}, {}),
            ("après la fin", dict(go=1, pos=N), {}, {}),
            ("case vidée (empreinte)", dict(go=1, pos=64), {"slot_hash": 0}, {}),
            ("case déplacée (adresse)", dict(go=1, pos=64), {"slot_base": PCM + 0x40}, {}),
            ("nombre réduit à 100", dict(go=1, pos=90), {"slot_count": 100}, {}),
            (STOP_CASE, dict(go=1, pos=500, stop=1), {}, {}),
            ("écrêtage (gain 32767, jacks aux bords)", dict(go=1, pos=700, gain=32767), {}, {"edge": True}),
            ("plan côté retiré (soff 0 dans la case)", dict(go=1, pos=300), {"slot_soff": 0}, {}),
            ("plan côté inconnu au départ (mono)", dict(go=1, pos=300, soff=0), {}, {}),
        ]
        bad, cost = [], {}
        for name, stv, slotv, opt in cases:
            st = dict(go=0, stop=0, slot=SLOT, hash=H1, base=PCM, count=N, soff=2 * N, gain=10600, pos=0)
            st.update(stv)
            put_sample(r, SLOT, H1, PCM, mid, side)
            for k, val in slotv.items():
                r.w32(tg[k] + 4 * SLOT, val)
            set_state(r, data, **st)
            if opt.get("edge"):
                jacks = [(0x7fffff if (i // 2) % 2 else -0x800000) - (1 - 2 * ((i // 2) % 2)) * (i % 5) for i in range(64)]
                usb = [(0x7ffffff0 if (i // 2) % 2 else -0x7ffffff0) for i in range(64)]
            else:
                jacks = [int(x) for x in RNG.integers(-0x800000, 0x800000, 64)]
                usb = [int(x) for x in RNG.integers(-0x40000000, 0x40000000, 64)]
            slot = {"hash": r.r32(tg["slot_hash"] + 4 * SLOT), "base": r.r32(tg["slot_base"] + 4 * SLOT),
                    "count": r.r32(tg["slot_count"] + 4 * SLOT), "soff": r.r32(tg["slot_soff"] + 4 * SLOT)}
            J, U, go, pos, used = model(mode, jacks, usb, st, slot, mid, side)
            out = block(r, jacks, usb)
            got = cue_state(r, data)
            allowed = set(range(data, data + 60))
            allowed |= set(range(USB_MIX, USB_MIX + 256)) if mode == "usb" else set(range(HALF, HALF + 256))
            stereo = mode != "split"
            okreads = set(PCM + 64 + 2 * p + b for p in used for b in (0, 1))
            okreads |= {a + 2 * N for a in okreads} if stereo and st["soff"] == slot["soff"] and st["soff"] else set()
            okreads |= set(PCM + 64 + 2 * p + b for p in used for b in (0, 1))
            fine = (out["ok"] and out["jacks"] == J and out["usb"] == U and got["go"] == go and got["pos"] == pos
                    and set(out["reads"]) <= okreads and set(out["writes"]) <= allowed
                    and (not used or set(out["reads"]) >= set(PCM + 64 + 2 * p for p in used)))
            if not fine:
                bad.append(f"{name} ({out['err'] or ''} jacks {out['jacks'] == J} usb {out['usb'] == U} go {got['go']}/{go}"
                           f" pos {got['pos']}/{pos} lectures {len(out['reads'])} écritures hors zone "
                           f"{[hex(a) for a in set(out['writes']) - allowed][:3]})")
            cost[name] = out["n"]
        check(not bad, f"{mode} : {len(cases)} cas exacts face au modèle (repos, lecture, fin, case vidée/déplacée, "
                       f"nombre réduit, fondu, écrêtage, plan côté) ; lectures dans les échantillons du bloc, écritures "
                       f"dans {'le mix USB' if mode == 'usb' else 'la moitié des jacks'} et cue_data ; registres et pile "
                       f"rendus {bad[:2]}")
        print(f"        coût par bloc ({mode}) : {cost['repos']} instructions au repos, {cost['lecture, début']} en "
              f"lecture, {cost[STOP_CASE]} pendant le fondu")
    jacks = [int(x) for x in RNG.integers(-0x800000, 0x800000, 64)]
    usb = [int(x) for x in RNG.integers(-0x40000000, 0x40000000, 64)]
    out = block(o, jacks, usb)
    check(out["ok"] and out["jacks"] == jacks and out["usb"] == usb and not out["reads"] and not out["writes"],
          "origine : la fin de 0x4005979e ne touche ni aux jacks, ni au mix USB, ni aux samples")


# --- 4. puce audio --------------------------------------------------------------------------------------------------
def codec_tests(v):
    res = {}
    for name, img in (("origine", v.base), ("modifié", v.img)):
        r = SP.Rig(v, img)
        seen = []
        r.stub(0x400443ba, lambda a, seen=seen: seen.append((a[0], a[1] & 0xff)) or 0)
        r.call(0x400445ec, 20, sr=0x2000, regs=True)
        first = (list(seen), r.regs_after == CALLEE_VALS)
        seen.clear()
        r.w32(0x404e9af8, 0)
        r.call(0x400447b6, 30, sr=0x2000, regs=True)
        res[name] = (first, (list(seen), r.regs_after == CALLEE_VALS), r.clean())
    (o1, o2, oc), (m1, m2, mc) = res["origine"], res["modifié"]
    check(o1 == ([(0x1e, 0xa4), (0x1f, 0xa4)], True) and o2[0] == [(0x1e, 0xae), (0x1f, 0xae)],
          "origine : 0x400445ec(20) et le volume (0x400447b6(30)) écrivent OUT1_L (0x1E) et OUT1_R (0x1F) = "
          "(volume + 16) | 0x80")
    check(m1 == ([(0x1e, 0xa4), (0x1f, 0x00)], True) and m2[0] == [(0x1e, 0xae), (0x1f, 0x00)] and m2[1] and oc and mc,
          "modifié : OUT1_L comme l'origine, OUT1_R (0x1F) = 0 (sortie ligne droite coupée : MAIN OUT R muet), au "
          "démarrage et à chaque volume ; registres rendus")


# --- 5. de bout en bout ---------------------------------------------------------------------------------------------
def chain_tests(v):
    data = v.cs["cue_data"]
    res = {}
    mid = RNG.integers(-20000, 20000, N)
    for name, img in (("origine", v.base), ("modifié", v.img)):
        r = SP.Rig(v, img)
        r.w32(ARMED, 0)
        put_sample(r, SLOT, H1, PCM, mid)
        r.browse(0)
        p = note(r, 2, vel=100)
        outs, refs = [], []
        st = dict(go=1, stop=0, slot=SLOT, hash=H1, base=PCM, count=N, soff=0, gain=10600, pos=0)
        slot = dict(hash=H1, base=PCM, count=N, soff=0)
        for b in range(5):
            if b == 3:
                p["rel"] = release(r, 2)
                st["stop"] = 1
            jacks = [int(x) for x in RNG.integers(-0x400000, 0x400000, 64)]
            out = block(r, jacks, [0] * 64)
            if name == "modifié":
                J, _, go, pos, _ = model("split", jacks, [0] * 64, st, slot, mid, None)
                refs.append(out["jacks"] == J and out["ok"])
                st["go"], st["pos"] = go, pos
            else:
                refs.append(out["jacks"] == jacks and out["ok"])
            outs.append(out)
        p2 = note(r, 2, n=61, vel=100)
        res[name] = dict(p=p, refs=refs, go=cue_state(r, data)["go"] if name == "modifié" else None,
                         pos=cue_state(r, data)["pos"] if name == "modifié" else None, p2=p2, clean=r.clean())
    o, m = res["origine"], res["modifié"]
    check(len(o["p"]["posted"]) == 1 and all(o["refs"]) and o["clean"],
          "origine : le pad envoie l'écoute à la piste (dans le mix) ; la fin du bloc ne change rien")
    check(not m["p"]["posted"] and all(m["refs"]) and not m["p"]["rel"]["posted"] and m["clean"]
          and m["go"] == 1 and m["pos"] == 0,
          "modifié : navigateur -> pad -> 3 blocs d'écoute à droite (perf mono à gauche et à droite) -> relâchement "
          "-> un bloc de fondu -> l'écoute se tait (5e bloc : la perf seule) ; nouvel appui : repart du début")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--with", dest="others", default="",
                    help="autres tweaks appliqués avant (ex. 6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm)")
    ap.add_argument("--syntakt", help="Syntakt_OS1.42.syx (ou 1.41), pour les moteurs du Syntakt")
    args = ap.parse_args()
    stock = T.main_os_from_syx(args.cycles)
    SP.FILES.append((2_000_000, RS_H))          # une prise du rééchantillonnage dans le navigateur du banc (2.)
    by_id = {json.loads(f.read_text(encoding="utf-8"))["id"]: f for f in TW.glob("[0-9]*.json")}
    others = [i for i in args.others.split(",") if i]
    if "model-tg" in others or "model-tg-st" in others:
        sets = [others]
    else:                                       # Model-TG seul par défaut ; les deux versions avec --syntakt
        sets = [others + ["model-tg"]] + ([others + ["model-tg-st"]] if args.syntakt else [])
    for ids in sets:
        v = Variant(stock, ids, by_id, args.syntakt)
        print(f"\n== origine : {v.label} ; modifié : + {v.cue['id']}")
        print("1. écritures")
        writes_tests(v)
        print("2. interface : pad, relâchement, son désigné, chargement")
        ui_tests(v)
        print("3. lecteur, dans l'interruption audio")
        player_tests(v, stock)
        print("4. puce audio : sortie ligne droite")
        codec_tests(v)
        print("5. de bout en bout")
        chain_tests(v)
    print("\nTOUT OK" if not FAIL else f"\n{len(FAIL)} ÉCHEC(S)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
