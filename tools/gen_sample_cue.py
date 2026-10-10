#!/usr/bin/env python3
"""Génère tweaks/model-cycles_OS1.13/34-sample-cue.json et 34-sample-cue-st.json : écouter les samples du navigateur
au casque seulement (cue « split »), avec le Sampler de Model-TG et l'écoute des samples (notes/48).

Le Model:Cycles n'envoie que deux canaux (G, D) à sa puce audio, et le casque et MAIN OUT les prennent tous les deux
(notes/48 §1) : un vrai cue casque stéréo est impossible. Le cue « split » des tables de mixage DJ l'est : MAIN OUT R
est coupé dans la puce (registre 0x1F), le canal G porte la perf en mono (MAIN OUT L et l'oreille gauche), le canal D
la perf en mono plus l'écoute (l'oreille droite seulement). L'écoute elle-même est un petit lecteur ajouté après le
mix, dans l'interruption audio : sur une piste Sampler, dans le navigateur, le pad de la piste fait entendre le sample
sous le curseur au casque, sans toucher aux six pistes, au mix USB ni au rééchantillonnage.

tools/machines/sample_cue/ : sample_cue.S (accroches, lecteur, données), lié par sample_cue.ld dans cinq masques de
sprites 48x22 libérés (tools/sprites.py). Le code lit l'état de Model-TG et appelle tok_of, aux adresses des
« symbols » de 30-model-tg.json et 30-model-tg-st.json, et compare le son désigné à pv_src (33-sample-preview.json) :
le tweak existe en deux fichiers aux écritures identiques, l'un pour chaque version de l'écoute des samples
(« requires »). sample_cue.S sait aussi ajouter l'écoute aux jacks seulement (pas à l'USB) ou à l'USB seulement
(MODES, CUE_MODE 2 et 3) ; seul le split est généré (choix de Maxime en attente, notes/48 §6).

    python3 tools/gen_sample_cue.py --cycles model-cycles_OS1.13.syx [--check]
"""
import argparse
import json
import pathlib
import struct
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "emu"))

import build                       # noqa: E402
import gen_sdvintage_exact as gx   # noqa: E402
import sprites                     # noqa: E402
import test_sdvintage as T         # noqa: E402

SRC = HERE / "machines" / "sample_cue"
TW = HERE.parent / "tweaks" / "model-cycles_OS1.13"
BASE = gx.BASE
# sorties possibles de l'écoute (CUE_MODE de sample_cue.S) ; GEN : celles dont on écrit les tweaks
MODES = {"split": 1, "jacks": 2, "usb": 3}
GEN = ("split",)
# version de l'écoute des samples -> (version de Model-TG, fichier de ce tweak)
OUTS = {"sample-preview": ("model-tg", TW / "34-sample-cue.json"),
        "sample-preview-st": ("model-tg-st", TW / "34-sample-cue-st.json")}
TG_FILES = {"model-tg": TW / "30-model-tg.json", "model-tg-st": TW / "30-model-tg-st.json"}
PV_FILES = {"sample-preview": TW / "33-sample-preview.json", "sample-preview-st": TW / "33-sample-preview-st.json"}
# sections liées -> masque 48x22 libéré qui les reçoit (sample_cue.ld)
CAVES = ((".cave1", 0x40152d38), (".cave2", 0x401592bc), (".cave3", 0x4015943c), (".cave4", 0x4015f38c),
         (".cave5", 0x40165fec))
# -D de sample_cue.S -> symbole de Model-TG, ou de l'écoute des samples
TG_DEFS = {"TG_TOK_OF": "tok_of", "TG_SLOT_HASH": "slot_hash", "TG_SLOT_BASE": "slot_base",
           "TG_SLOT_COUNT": "slot_count", "TG_SLOT_SOFF": "slot_soff", "TG_SLOT_PGAIN": "slot_pgain"}
PV_DEFS = {"PV_SRC": "pv_src"}
# Contrat avec Model-TG v1.1.0 (vérifié dans sa charge utile) : début de tok_of, tables des cases à zéro au départ
TG_HEADS = {"tok_of": "4feffff448d7000e"}
TG_ZERO = {"slot_hash": 256, "slot_base": 256, "slot_count": 256, "slot_soff": 256, "slot_pgain": 256}
# (adresse, octets d'origine vérifiés, accroche, rôle)
HOOKS = (
    (0x4008180e, "4aae00186664", "dec",
     "note jouée (0x4008171e) : tst.l 24(fp) ; bne.s 0x40081878 -> jmp cue_dec"),
    (0x4008145e, "4e56ff84707f", "off",
     "relâchement : link.w fp,#-124 ; moveq #127,d0 -> jmp cue_off"),
    (0x40081bd6, "41ef000423d0", "arm",
     "son désigné : lea 4(sp),a0 ; début de move.l (a0),0x40fb5a04 -> jmp cue_arm"),
    (0x400a6bec, "400a64fa", "load",
     "navigateur : adresse de la fonction de chargement d'un fichier -> cue_load"),
    (0x40059878, "4fef0014245f", "out",
     "fin du calcul d'un bloc (interruption audio) : lea 20(sp),sp ; movea.l (sp)+,a2 -> jmp cue_out"),
)
# split : la sortie ligne droite de la puce audio coupée, au démarrage et à chaque volume (0x400445ec)
CODEC = (0x40044614, "2f02", "42a7", "registre 0x1F (OUT1_R) : move.l d2,-(sp) -> clr.l -(sp)")
SYMBOLS = ("cue_dec", "cue_start", "cue_held", "cue_off", "cue_arm", "cue_load", "cue_out", "cue_play", "cue_data")


def symbols_of(files, names, what):
    """Symboles demandés, identiques dans les deux versions, et le JSON de chacune."""
    syms, tws = None, {}
    for tid, f in files.items():
        t = json.loads(f.read_text(encoding="utf-8"))
        s = {n: int(v, 16) for n, v in t.get("symbols", {}).items()}
        if set(names) - set(s):
            raise SystemExit(f"!! {f.name} ne porte pas les symboles {sorted(set(names) - set(s))} ({what})")
        s = {n: s[n] for n in sorted(names)}
        if syms is not None and s != syms:
            raise SystemExit(f"!! symboles différents entre les deux versions ({', '.join(p.name for p in files.values())})")
        syms, tws[tid] = s, t
    return syms, tws


def check_contract(stock, tg_syms, tgs, pv_syms, pvs):
    """Le code de Model-TG et de l'écoute des samples à ces adresses est bien celui pour lequel sample_cue.S est
    écrit : tok_of, ses tables à zéro au départ ; pv_parse construit son son dans pv_src et le désigne."""
    for tid, t in tgs.items():
        rt = build.payload_runtime(t, stock, None)
        dest = int(t["append"]["dest"], 16)
        for n, head in TG_HEADS.items():
            h = bytes.fromhex(head)
            if rt[tg_syms[n] - dest:tg_syms[n] - dest + len(h)] != h:
                raise SystemExit(f"!! {tid} : {n} ({tg_syms[n]:#x}) n'est plus le code attendu ; relire notes/48 §4")
        for n, size in TG_ZERO.items():
            if any(rt[tg_syms[n] - dest:tg_syms[n] - dest + size]):
                raise SystemExit(f"!! {tid} : {n} ({tg_syms[n]:#x}) n'est pas à zéro au départ")
    src = pv_syms["pv_src"].to_bytes(4, "big")
    for pid, t in pvs.items():
        code = b"".join(bytes.fromhex(w["new"]) for w in t["writes"])
        # lea pv_src,%a0 (le son construit) et move.l #pv_src,(%a2) (le résultat de la lecture du preset)
        if b"\x41\xf9" + src not in code or b"\x24\xbc" + src not in code:
            raise SystemExit(f"!! {pid} : pv_parse ne construit plus son son dans pv_src ({pv_syms['pv_src']:#x})")


def compile_cue(mode, tg_syms, pv_syms):
    """{section: (adresse, octets)} des caves, et les symboles."""
    with tempfile.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        obj, elf = d / "cue.o", d / "cue.elf"
        defs = [f"-D{k}={tg_syms[v]:#x}" for k, v in TG_DEFS.items()]
        defs += [f"-D{k}={pv_syms[v]:#x}" for k, v in PV_DEFS.items()] + [f"-DCUE_MODE={MODES[mode]}"]
        gx.run([gx.CROSS + "gcc", "-mcpu=54418", *defs, "-c", str(SRC / "sample_cue.S"), "-o", str(obj)])
        gx.run([gx.CROSS + "ld", "-T", str(SRC / "sample_cue.ld"), "--no-warn-rwx-segments", "-o", str(elf),
                str(obj)])
        out = {}
        for line in gx.run([gx.CROSS + "nm", str(elf)]).splitlines():
            p = line.split()
            if len(p) == 3:
                out[p[2]] = int(p[0], 16)
        heads = subprocess.run([gx.CROSS + "objdump", "-h", str(elf)], capture_output=True, text=True,
                               check=True).stdout
        caves = {}
        for sec, _ in CAVES:
            b = d / (sec[1:] + ".bin")
            gx.run([gx.CROSS + "objcopy", "-O", "binary", "-j", sec, str(elf), str(b)])
            caves[sec] = (int(heads.split(sec + " ")[1].split()[2], 16), b.read_bytes())
        return caves, out


def build_writes(stock, mode, tg_syms, pv_syms):
    caves, cue = compile_cue(mode, tg_syms, pv_syms)
    shared = stock[sprites.SHARED_48 - BASE:sprites.SHARED_48 - BASE + 192]
    writes, used = [], []
    for sec, mask in CAVES:
        addr, code = caves[sec]
        size = sprites.MASKS[mask][0]
        if addr != mask or len(code) > size:
            raise SystemExit(f"!! {sec} : {len(code)} o à {addr:#x}, place {size} o à {mask:#x}")
        if stock[mask - BASE:mask - BASE + size] != shared:
            raise SystemExit(f"!! le masque {mask:#x} n'est pas une copie du masque partagé {sprites.SHARED_48:#x}")
        old = stock[addr - BASE:addr - BASE + len(code)]
        writes += [{"off": addr - BASE, "old": old.hex(), "new": code.hex()}, sprites.redirect_write(mask)]
        used.append(len(code))
    target = {"dec": struct.pack(">HI", 0x4ef9, cue["cue_dec"]), "off": struct.pack(">HI", 0x4ef9, cue["cue_off"]),
              "arm": struct.pack(">HI", 0x4ef9, cue["cue_arm"]), "load": struct.pack(">I", cue["cue_load"]),
              "out": struct.pack(">HI", 0x4ef9, cue["cue_out"])}
    hooks = [(va, old, target[what]) for va, old, what, _ in HOOKS]
    if mode == "split":
        hooks.append((CODEC[0], CODEC[1], bytes.fromhex(CODEC[2])))
    for va, old_hex, new in hooks:
        old = bytes.fromhex(old_hex)
        if stock[va - BASE:va - BASE + len(old)] != old:
            raise SystemExit(f"!! octets d'origine inattendus en {va:#x}")
        if len(new) != len(old):
            raise SystemExit(f"!! accroche en {va:#x} : {len(new)} o au lieu de {len(old)}")
        writes.append({"off": va - BASE, "old": old.hex(), "new": new.hex()})
    writes.sort(key=lambda w: w["off"])
    return writes, cue, used


def make_tweak(pv, mode, writes, cue, used):
    st = pv == "sample-preview-st"
    return {
        "id": "sample-cue-st" if st else "sample-cue",
        "order": 34,
        "name": "Écoute des samples au casque (cue split, Model-TG)" + (", avec les moteurs du Syntakt" if st else ""),
        "description": [
            "Navigateur d'une piste Sampler de Model-TG, avec l'écoute des samples : le pad de la piste (ou ses touches "
            "en mode clavier) fait entendre le sample sous le curseur au casque seulement. La note ne part pas à la "
            "piste : un lecteur à part lit le sample et l'ajoute après le mix, ni dans l'USB ni dans le "
            "rééchantillonnage. Relâcher le pad, bouger le curseur, charger le fichier ou fermer le navigateur l'arrête.",
            "Cue « split », comme sur une table de mixage DJ : MAIN OUT R est coupé dans la puce audio, MAIN OUT L "
            "porte la perf en mono ; au casque, la perf à gauche, la perf et l'écoute à droite. L'USB reste stéréo.",
            "Les presets (sons des machines) s'écoutent comme avant, sur la piste.",
            "Pour " + ("la version de l'écoute des samples faite pour les moteurs du Syntakt (sample-preview-st)" if st
                        else "l'écoute des samples (sample-preview)") + " ; "
            f"lit l'état de Model-TG et appelle tok_of, aux adresses de ses symboles. Code et données dans cinq masques "
            f"de sprites 48x22 libérés (tools/sprites.py) : {' + '.join(map(str, used))} o. "
            f"Généré par tools/gen_sample_cue.py, notes/48.",
        ],
        "device": "Model:Cycles",
        "os": "1.13",
        "section": 3,
        "requires": [pv],
        "symbols": {n: f"{cue[n]:#x}" for n in SYMBOLS},
        "writes": writes,
    }


def check_overlaps(tweaks):
    """Aucune écriture de ce tweak ne recouvre celle d'un tweak qui peut aller avec lui."""
    cat = build.load_catalog()["model-cycles_OS1.13"][1]
    for t in tweaks:
        pv = cat[t["requires"][0]]
        tg = cat[pv["requires"][0]]
        never = set(t.get("conflicts", [])) | set(pv.get("conflicts", [])) | set(tg.get("conflicts", []))
        mine = [(w["off"], w["off"] + len(bytes.fromhex(w["old"]))) for w in t["writes"]]
        for o in cat.values():
            if (o["id"] in ("sample-cue", "sample-cue-st") or o["id"] in never
                    or {t["id"], pv["id"], tg["id"]} & set(o.get("conflicts", []))):
                continue                               # jamais construits ensemble
            for w in o["writes"]:
                a, b = w["off"], w["off"] + len(bytes.fromhex(w["old"]))
                for lo, hi in mine:
                    if a < hi and lo < b:
                        raise SystemExit(f"!! {t['id']} recouvre {o['id']} en {a + BASE:#x} : déclarer un conflit")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="model-cycles_OS1.13.syx officiel")
    ap.add_argument("--check", action="store_true", help="vérifie que les JSON versionnés correspondent")
    args = ap.parse_args()
    stock = T.main_os_from_syx(args.cycles)
    if build.sha(stock) != json.loads((TW / "device.json").read_text(encoding="utf-8"))["section_sha256"]:
        raise SystemExit("!! ce n'est pas le MAIN OS 1.13 officiel")
    tg_syms, tgs = symbols_of(TG_FILES, set(TG_DEFS.values()) | set(TG_HEADS), "tools/gen_model_tg.py")
    pv_syms, pvs = symbols_of(PV_FILES, set(PV_DEFS.values()), "tools/gen_sample_preview.py")
    check_contract(stock, tg_syms, tgs, pv_syms, pvs)
    ok = True
    for mode in GEN:
        writes, cue, used = build_writes(stock, mode, tg_syms, pv_syms)
        tweaks = [make_tweak(pv, mode, writes, cue, used) for pv in OUTS]
        for t in tweaks:
            pv = pvs[t["requires"][0]]
            build.apply_writes(stock, [tgs[pv["requires"][0]], pv, t])   # les octets d'origine collent
        check_overlaps(tweaks)
        print("  " + tweaks[0]["description"][-1])
        for t, (_, out) in zip(tweaks, OUTS.values()):
            text = json.dumps(t, indent=1) + "\n"
            if args.check:
                same = out.exists() and out.read_text(encoding="utf-8") == text
                ok &= same
                print(f"  {out.name} {'est à jour' if same else 'NE CORRESPOND PAS (autre binutils ?)'}")
            else:
                out.write_text(text, encoding="utf-8")
                print(f"  écrit : {out.relative_to(HERE.parent)} ({len(t['writes'])} écritures)")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
