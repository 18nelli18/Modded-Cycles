#!/usr/bin/env python3
"""Tweaks de travail des deux fichiers d'essai de l'optimisation de l'OS 1.13 (étude optim du 17-18/10/2026).

Ce ne sont PAS des mods du flasher : rien n'est écrit dans le dépôt. Ce script lit TON .syx officiel, assemble
les sources de src/ aux adresses des masques choisis ci-dessous, vérifie chaque octet d'origine et écrit, dans
tweaks/model-cycles_OS1.13/ de CE dossier (avec une copie de device.json du dépôt), un tweak par morceau :

  90 essai-compteur        compteur de charge « pic/moyenne/libre » (dans les DEUX fichiers, même code, même place)
  91 essai-gel-machines    D1 : MACHINES ne gèle plus sur une machine inconnue (0x4004df66, 0x4004df80)
  92 essai-gel-horloge     D2 : l'horloge MIDI sortante ne gèle plus la machine, anneau plein (0x40001246)
  93 essai-dist            p1 : saturateur de Dist sauté quand Dist est à 0 (optim/sortie, vd_skip.S)
  94 essai-effets          p2 : sommeil exact du delay et de la reverb (optim/sortie, fx_lib/fx_dly/fx_rev.S)
  95 essai-envois          p3 : envois à gain nul sautés (optim/sortie, send_skip.S)
  96 essai-mix2            mix2 sans sa boucle morte, en place (optim/voix, mix2.S)
  97 essai-punch           PUNCH éteint par un chemin court (optim/voix, punch.S)
  98 essai-voix-muettes    arrêt des voix muettes pour l'OS seul (optim/voix, idle_stock.S)

Masques : tous marqués libres dans REGISTRY.md §1, un seul usage chacun, aucun de ceux que réserve la PR brouillon
du retour casque (0x40152d38, 0x401592bc, 0x4015943c, 0x4015f38c, 0x40165fec, 0x40168a84, 0x40168da4,
0x4016bcd8). Par rapport aux études : p1, p3, fx_lib et fx_dly sont déplacés (réassemblés ici) ; fx_rev, punch et
l'arrêt des voix muettes restent où ils étaient.

    python3 gen_essai.py --cycles /home/user/Modded-Cycles/firmware/model-cycles_OS1.13.syx
"""
import argparse
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

REPO = pathlib.Path("/home/user/Modded-Cycles")
sys.path.insert(0, str(REPO / "tools"))
import build                     # noqa: E402
import sprites                   # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / "src"
DEV_DIR = HERE / "tweaks" / "model-cycles_OS1.13"
BASE = 0x40000400
CROSS = "m68k-linux-gnu-"

RESERVED = {0x40152d38, 0x401592bc, 0x4015943c, 0x4015f38c, 0x40165fec, 0x40168a84, 0x40168da4, 0x4016bcd8}
MASK = {
    "compteur.m1": 0x40167c50,    # 35x35, 280 o
    "compteur.m2": 0x40171a48,    # 48x22, 192 o
    "vd_skip": 0x4016dab8,        # 48x22 (étude : 0x40152d38, réservé)
    "fx_lib": 0x4016fae8,         # 48x22 (étude : 0x401592bc, réservé)
    "fx_dly": 0x40189618,         # 34x34 (étude : 0x40185f48, pris ici par l'arrêt des voix muettes)
    "fx_rev": 0x4018d918,         # 41x41, 328 o (comme l'étude)
    "send_skip": 0x40170c48,      # 48x22 (étude : 0x4015943c, réservé)
    "punch": 0x40186238,          # 34x34 (comme l'étude)
    "idle_stock": 0x40185f48,     # 34x34 (comme l'étude)
}
NAMES = 0x401177e4                # 6 noms de machines (écran MACHINES), lus seulement en 0x400a2612


def main_os(path):
    raw = pathlib.Path(path).read_bytes()
    stream, _ = build.unwrap(raw)
    c = build.container.parse(stream)
    s3 = next(s for s in c["sections"] if s["id"] == 3)
    img = build.aplib.depack(c["blob"][s3["off"]:s3["off"] + s3["size"]])[0]
    dev = json.loads((REPO / "tweaks" / "model-cycles_OS1.13" / "device.json").read_text(encoding="utf-8"))
    if hashlib.sha256(raw).hexdigest() != dev["stock_syx_sha256"] or \
            hashlib.sha256(img).hexdigest() != dev["section_sha256"]:
        raise SystemExit("!! ce n'est pas le .syx officiel de l'OS 1.13 (empreintes de device.json)")
    return img


def assemble(src, sections, defs=()):
    """Assemble src ; sections : {nom de section : adresse}. Rend ({section : octets}, {symbole : adresse})."""
    with tempfile.TemporaryDirectory() as d:
        o, elf = pathlib.Path(d) / "a.o", pathlib.Path(d) / "a.elf"
        cmd = [CROSS + "as", "-mcpu=54418", "-o", str(o), str(SRC / src)]
        for k, v in defs:
            cmd += ["--defsym", f"{k}={v:#x}"]
        subprocess.run(cmd, check=True)
        ld = [CROSS + "ld", "-e", "0", "-o", str(elf), str(o)]
        for sec, va in sections.items():
            ld.append(f"-Ttext={va:#x}" if sec == ".text" else f"--section-start={sec}={va:#x}")
        subprocess.run(ld, check=True)
        out = {}
        for sec in sections:
            b = pathlib.Path(d) / "s.bin"
            subprocess.run([CROSS + "objcopy", "-O", "binary", "-j", sec, str(elf), str(b)], check=True)
            out[sec] = b.read_bytes()
        nm = subprocess.run([CROSS + "nm", str(elf)], check=True, capture_output=True, text=True).stdout
    syms = {l.split()[2]: int(l.split()[0], 16) for l in nm.splitlines() if len(l.split()) == 3}
    return out, syms


class Tw:
    def __init__(self, img, tid, order, name, desc):
        self.img, self.t = img, {"id": tid, "order": order, "name": name, "description": desc,
                                 "device": "Model:Cycles", "os": "1.13", "section": 3, "writes": []}
        self.masks = []

    def w(self, va, new, old=None):
        o = va - BASE
        cur = self.img[o:o + len(new)]
        if old is not None and cur != bytes.fromhex(old):
            raise SystemExit(f"!! {self.t['id']} {va:#x} : {old} attendu, {cur.hex()} trouvé")
        self.t["writes"].append({"off": o, "old": cur.hex(), "new": new.hex()})

    def mask(self, key, code):
        va = MASK[key]
        size = sprites.MASKS[va][0]
        if va in RESERVED or len(code) > size:
            raise SystemExit(f"!! masque {va:#x} : réservé ou trop petit ({len(code)} > {size})")
        self.w(va, code)
        self.t["writes"].append(sprites.redirect_write(va))
        self.masks.append((va, len(code), size))

    def hook(self, va, old, target, size, call=False):
        new = bytes.fromhex("4eb9" if call else "4ef9") + target.to_bytes(4, "big")
        new += bytes.fromhex("4e71") * ((size - 6) // 2)
        assert len(new) == size == len(bytes.fromhex(old))
        self.w(va, new, old)


def tweaks(img):
    out, info = [], {}

    # --- 90 compteur (les deux fichiers)
    secs, s = assemble("compteur.S", {".m1": MASK["compteur.m1"], ".m2": MASK["compteur.m2"]})
    t = Tw(img, "essai-compteur", 90, "Essai : compteur de charge pic/moyenne/libre",
           ["Fichier d'essai (étude optim, pas une carte du flasher) : nom de toutes les machines = pic/moyenne/libre",
            "en % d'un bloc, de l'entrée de l'interruption de rendu à la fin de la fonction audio, toutes les 0,5 s.",
            "Masques 0x40167c50 et 0x40171a48. gen_essai.py, src/compteur.S."])
    t.mask("compteur.m1", secs[".m1"])
    t.mask("compteur.m2", secs[".m2"])
    t.hook(0x40058c5e, "4e56ff5848d73fff", s["m_entry"], 8)
    t.hook(0x40059382, "4eb94005979e", s["m_probe"], 6, call=True)
    t.hook(0x4000543a, "4fef001860fe", s["m_idle_loop"], 6)
    old = img[NAMES - BASE:NAMES - BASE + 24]
    t.w(NAMES, s["m_name"].to_bytes(4, "big") * 6, old.hex())
    t.t["symbols"] = {k: f"{s[k]:#x}" for k in ("m_entry", "m_probe", "m_show", "m_idle_loop", "V", "idle_acc",
                                                "m_name")}
    out.append(t)

    # --- 91 D1, 92 D2 (optim/stabilite §4.2, §5.2)
    t = Tw(img, "essai-gel-machines", 91, "Essai : MACHINES ne gèle plus (machine inconnue -> CHORD)",
           ["D1 de optim/stabilite : moveq #-1 -> moveq #6 dans les accesseurs 0x4004df5c et 0x4004df76."])
    t.w(0x4004df66, bytes.fromhex("7006"), "70ff")
    t.w(0x4004df80, bytes.fromhex("7006"), "70ff")
    out.append(t)
    t = Tw(img, "essai-gel-horloge", 92, "Essai : horloge MIDI sortante, anneau plein -> octet jeté",
           ["D2 de optim/stabilite : bgt.s 0x4000123a -> bgt.s 0x400012c6 (sortie), sans attendre à IPL 7."])
    if img[0x400012c6 - BASE:0x400012cc - BASE].hex() != "241f261f4e75":
        raise SystemExit("!! 0x400012c6 n'est pas la sortie move.l (sp)+,d2 ; move.l (sp)+,d3 ; rts")
    t.w(0x40001246, bytes.fromhex("6e7e"), "6ef2")
    out.append(t)

    # --- 93 p1, 94 p2, 95 p3 (optim/sortie §4)
    secs, s = assemble("vd_skip.S", {".text": MASK["vd_skip"]})
    t = Tw(img, "essai-dist", 93, "Essai : saturateur de Dist sauté quand Dist est à 0",
           ["p1 de optim/sortie (vd_skip.S), masque 0x4016dab8, détour 0x40057062."])
    t.mask("vd_skip", secs[".text"])
    t.hook(0x40057062, "286f0038206f0040", s["vd_check"], 8)
    info["vd_hit"] = s["vd_hit"]
    out.append(t)

    lib, sl = assemble("fx_lib.S", {".text": MASK["fx_lib"]})
    defs = [("ZSCAN", sl["zscan"]), ("ZFILL", sl["zfill"])]
    dly, sd = assemble("fx_dly.S", {".text": MASK["fx_dly"]}, defs)
    rev, sr = assemble("fx_rev.S", {".text": MASK["fx_rev"]}, defs)
    t = Tw(img, "essai-effets", 94, "Essai : sommeil exact du delay et de la reverb",
           ["p2 de optim/sortie (fx_lib.S, fx_dly.S, fx_rev.S), masques 0x4016fae8, 0x40189618, 0x4018d918 ;",
            "détours 0x40057516, 0x40057ac8, 0x40057dc6."])
    t.mask("fx_lib", lib[".text"])
    t.mask("fx_dly", dly[".text"])
    t.mask("fx_rev", rev[".text"])
    t.hook(0x40057516, "2f03260dea83", sd["dz_check"], 6)
    t.hook(0x40057ac8, "2a7c8000a9b0", sr["rz_check"], 6)
    t.hook(0x40057dc6, "207c8000ad20", sr["rz_mod"], 6)
    info["dz_sleep"], info["rz_slept"] = sd["dz_sleep"], sr["rz_slept"]
    out.append(t)

    secs, s = assemble("send_skip.S", {".text": MASK["send_skip"]})
    t = Tw(img, "essai-envois", 95, "Essai : envois à gain nul sautés",
           ["p3 de optim/sortie (send_skip.S), masque 0x40170c48, détours 0x40056716, 0x40056698."])
    t.mask("send_skip", secs[".text"])
    t.hook(0x40056716, "4fefffe048d70cfc", s["s6_check"], 8)
    t.hook(0x40056698, "4fefffd848d73cfc", s["s7_check"], 8)
    info["zero_out"] = s["zero_out"]
    out.append(t)

    # --- 96 mix2, 97 PUNCH, 98 arrêt des voix muettes (optim/voix §4.1-4.3)
    secs, _ = assemble("mix2.S", {".text": 0x400a98c4})
    code = secs[".text"][:0x1c]
    code += bytes.fromhex("4e71") * ((0x40 - len(code)) // 2)
    if secs[".text"][0x18:0x1c] != bytes.fromhex("6000") + (0x40 - 0x1a).to_bytes(2, "big"):
        raise SystemExit("!! mix2 : bra.w de fin inattendu")
    t = Tw(img, "essai-mix2", 96, "Essai : mix2 sans sa boucle morte",
           ["optim/voix §4.2 (mix2.S) : 64 o en place, 0x400a98c4..0x400a9904."])
    t.w(0x400a98c4, code)
    if t.t["writes"][0]["old"][:16] != "22115c8124730800":
        raise SystemExit("!! mix2 : octets d'origine")
    out.append(t)

    secs, s = assemble("punch.S", {".text": MASK["punch"]})
    t = Tw(img, "essai-punch", 97, "Essai : PUNCH éteint par un chemin court",
           ["optim/voix §4.3 (punch.S), masque 0x40186238, détour 0x400a9714."])
    t.mask("punch", secs[".text"])
    t.hook(0x400a9714, "2e2802a42213", MASK["punch"] + 0, 6)
    if s.get("pstub", MASK["punch"]) != MASK["punch"]:
        raise SystemExit("!! punch : pstub n'est pas au début du masque")
    out.append(t)

    secs, s = assemble("idle_stock.S", {".text": MASK["idle_stock"]}, [("IDLE_N", 64), ("IDLE_T", 4096)])
    t = Tw(img, "essai-voix-muettes", 98, "Essai : arrêt des voix muettes (OS seul)",
           ["optim/voix §4.1 (idle_stock.S, 64 blocs sous -108 dB), masque 0x40185f48, détours 0x400a7dfe, 0x400a7e24."])
    t.mask("idle_stock", secs[".text"])
    t.hook(0x400a7dfe, "b08465222046", s["gate"], 6)
    t.hook(0x400a7e24, "269522434280", s["after"], 6)
    info["QUIET"] = s["QUIET"]
    out.append(t)
    return out, info


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", default=str(REPO / "firmware" / "model-cycles_OS1.13.syx"))
    args = ap.parse_args()
    img = main_os(args.cycles)
    tws, info = tweaks(img)
    DEV_DIR.mkdir(parents=True, exist_ok=True)
    for f in DEV_DIR.glob("*.json"):
        f.unlink()
    shutil.copy(REPO / "tweaks" / "model-cycles_OS1.13" / "device.json", DEV_DIR / "device.json")
    # chaque morceau seul, puis tous ensemble, sur l'image officielle (refuse un « old » faux ou un recouvrement)
    for t in tws:
        build.apply_writes(img, [t.t])
    build.apply_writes(img, [t.t for t in tws])
    spans = sorted((w["off"], w["off"] + len(w["new"]) // 2, t.t["id"]) for t in tws for w in t.t["writes"])
    for (a0, a1, i0), (b0, b1, i1) in zip(spans, spans[1:]):
        if b0 < a1:
            raise SystemExit(f"!! recouvrement {i0} / {i1} en {a0 + BASE:#x}")
    for t in tws:
        p = DEV_DIR / f"{t.t['order']}-{t.t['id']}.json"
        p.write_text(json.dumps(t.t, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        ms = ", ".join(f"{va:#x} {n}/{size} o" for va, n, size in t.masks)
        print(f"  {p.name:32s} {len(t.t['writes']):2d} écritures" + (f" ; masques {ms}" if ms else ""))
    (HERE / "symboles.json").write_text(json.dumps(
        {**{k: f"{v:#x}" for k, v in info.items()}, **tws[0].t["symbols"]}, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
