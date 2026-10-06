#!/usr/bin/env python3
"""Preuve de l'OS Cycles pour Model:Samples et de son retour par USB (notes/41, tools/crossflash.py).

Une mise a jour USB passe deux portes (notes/15 §3.4bis) : 1) l'OS qui tourne verifie le conteneur recu
(checksum de contenu, HMAC) avant de le mettre en staging ; 2) au redemarrage, le bootstrap le re-verifie avec SA cle
et l'installe. Sur un Model:Samples, le bootstrap reste celui du Samples (cle Samples). Ce test fait tourner le vrai
code de verification des deux OS (0x4005a0e4 dans l'OS Cycles, son equivalent dans l'OS Samples) dans Unicorn :

  1. Aller : l'OS Samples d'origine accepte `--to samples` (porte 1), signe avec la cle du bootstrap Samples (porte 2).
  2. Le MAIN OS installe ne differe de l'OS Cycles officiel que par les 32 octets de la constante de cle.
  3. Retour : l'OS Cycles d'origine REFUSE `--back-samples` (HMAC : c'est le verrou a deux cles) ; l'OS Cycles de
     `--to samples` l'ACCEPTE ; et ce fichier est l'OS Samples officiel, octet pour octet une fois decode (porte 2 :
     la meme que pour une mise a jour officielle).
  4. Garde-fous : l'OS Cycles de `--to samples` refuse l'OS Cycles officiel (signe Cycles), qu'Elektron Transfer
     pourrait proposer ; un vrai Model:Cycles (OS Cycles d'origine) refuse `--to samples` et `--back-samples`.
  5. Transport : `--back-samples` porte l'en-tete SysEx du Cycles (produit 0x11, octet appareil 0x0C), comme les
     firmwares Model:Cycles que la page envoie deja.

    python3 tools/emu/test_crossflash_samples.py --cycles model-cycles_OS1.13.syx --samples model-samples_OS1.13.syx

Environ 30 s (chaque verification calcule deux SHA-256 et un HMAC sur ~1 Mo en emulation).
"""
import argparse
import hashlib
import hmac
import pathlib
import sys

from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE
from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import crossflash as X              # noqa: E402
from mtlib import aplib, container  # noqa: E402
from mtlib.syx import unwrap        # noqa: E402

BASE = X.MAIN_BASE
STOP = 0x9f000000
STACK = 0x9e000000
BUF = 0x91000000
FAIL = []

# Verification d'un conteneur recu (pointeur sur [longueur][checksum][conteneur]) : 1 = bon, 3 = checksum de
# contenu faux, 4 = HMAC faux, 5 = alimentation ; la verification d'alimentation (lecture de broches) est court-circuitee.
VERIFY = {"cycles": (0x4005a0e4, 0x400530ca), "samples": None}     # samples : trouve dans son MAIN OS (find_verify)
VERIFY_SAMPLES_HINT = 0x40059104                                     # notes/15 §3.4 : appelle le HMAC 0x40051728


def check(ok, msg):
    print(("  ok    " if ok else "  ECHEC ") + msg, flush=True)
    if not ok:
        FAIL.append(msg)


def find_verify(main):
    """Dans le MAIN OS Samples : la fonction qui appelle le HMAC (0x40051728) juste apres le checksum de contenu,
    sur le modele de 0x4005a0e4 du Cycles ; et la verification d'alimentation qu'elle appelle ensuite."""
    hm = (0x4eb9).to_bytes(2, "big") + (0x40051728).to_bytes(4, "big")
    i = main.find(hm)
    if i < 0 or main.find(hm, i + 1) >= 0:
        raise SystemExit("!! appel du HMAC introuvable ou multiple dans l'OS Samples")
    # debut de fonction : "move.l a2,-(sp)" (2f0a) dans les 40 octets avant, comme 0x4005a0e4
    start = main.rfind(b"\x2f\x0a\x24\x6f\x00\x08", i - 40, i)
    if start < 0:
        raise SystemExit("!! debut de la fonction de verification Samples introuvable")
    j = main.find(b"\x4e\xb9", i + 6, i + 40)
    power = int.from_bytes(main[j + 2:j + 6], "big")
    return BASE + start, power


def verify(main, fn, power, blob):
    """Fait tourner la verification de l'OS sur le conteneur `blob` ; renvoie son code."""
    uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
    uc.ctl_set_cpu_model(mk.UC_CPU_M68K_ANY)
    uc.reg_write(mk.UC_M68K_REG_SR, 0x2700)
    uc.mem_map(0x40000000, 0x02000000)
    uc.mem_write(BASE, main)
    uc.mem_map(0x90000000, 0x10000000)
    uc.mem_write(STOP, b"\x4e\x71\x4e\x71")
    buf = len(blob).to_bytes(4, "big") + container.content_checksum(blob).to_bytes(4, "big") + blob
    uc.mem_write(BUF, buf)

    def ret1(u, a, s, d):
        sp = u.reg_read(mk.UC_M68K_REG_A7)
        u.reg_write(mk.UC_M68K_REG_D0, 1)
        u.reg_write(mk.UC_M68K_REG_PC, int.from_bytes(u.mem_read(sp, 4), "big"))
        u.reg_write(mk.UC_M68K_REG_A7, sp + 4)
    uc.hook_add(UC_HOOK_CODE, ret1, begin=power, end=power)
    sp = STACK - 8
    uc.mem_write(sp, STOP.to_bytes(4, "big") + BUF.to_bytes(4, "big"))
    uc.reg_write(mk.UC_M68K_REG_A7, sp)
    uc.emu_start(fn, STOP, count=400_000_000)
    return uc.reg_read(mk.UC_M68K_REG_D0) & 0xff


def blob_of(raw):
    stream, info = unwrap(raw)
    return container.parse(stream)["blob"], info


def main3_of(raw):
    c = container.parse(unwrap(raw)[0])
    s = next(x for x in c["sections"] if x["id"] == 3)
    return aplib.depack(c["blob"][s["off"]:s["off"] + s["size"]])[0]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--samples", required=True)
    args = ap.parse_args()

    cyc, smp = X.load(args.cycles, "cycles"), X.load(args.samples, "samples")
    cyc_raw, smp_raw = cyc[0]["raw"], smp[0]["raw"]
    fwd, fwd_main_sha = X.cycles_for_samples(cyc, smp)
    back = X.samples_back(cyc, smp)
    c_key, s_key = X.host_key(cyc), X.host_key(smp)
    cyc_main, smp_main = cyc[3][3], smp[3][3]
    new_main = main3_of(fwd)
    s_fn, s_power = find_verify(smp_main)
    c_fn, c_power = VERIFY["cycles"]
    print(f"verification Samples : 0x{s_fn:08x} (alimentation 0x{s_power:08x})")
    b_cyc, b_smp, b_fwd, b_back = (blob_of(r)[0] for r in (cyc_raw, smp_raw, fwd, back))

    print("1. Aller (Model:Samples sous son OS)")
    check(verify(smp_main, s_fn, s_power, b_smp) == 1, "l'OS Samples accepte l'OS Samples officiel (temoin)")
    check(verify(smp_main, s_fn, s_power, b_fwd) == 1, "l'OS Samples accepte --to samples (porte 1)")
    check(hmac.new(s_key, b_fwd[:-32], hashlib.sha256).digest() == b_fwd[-32:],
          "--to samples est signe avec la cle du bootstrap Samples (porte 2)")
    sec = lambda b: {x["id"]: b[x["off"]:x["off"] + x["size"]] for x in container.parse(  # noqa: E731
        len(b).to_bytes(4, "big") + b"\0" * 4 + b)["sections"]}
    sf, ss = sec(b_fwd), sec(b_smp)
    check(all(sf[i] == ss[i] for i in (2, 4, 5)) and b_fwd[:0x20] == b_smp[:0x20],
          "bootstrap, updater, horodatage et en-tete : ceux du Samples, inchanges")
    check(verify(cyc_main, c_fn, c_power, b_fwd) == 4, "un vrai Model:Cycles refuse --to samples (HMAC)")

    print("2. MAIN OS installe")
    diff = [i for i in range(len(cyc_main)) if cyc_main[i] != new_main[i]] if len(cyc_main) == len(new_main) else None
    co = X.CYC_KEY_CONST_VA - BASE
    check(diff is not None and diff and min(diff) >= co and max(diff) < co + 32,
          f"OS Cycles officiel sauf {len(diff or [])} octets dans la constante 0x{X.CYC_KEY_CONST_VA:08x}")

    print("3. Retour (Model:Samples sous l'OS Cycles)")
    check(verify(cyc_main, c_fn, c_power, b_back) == 4, "OS Cycles d'origine : refuse le retour (verrou a deux cles)")
    check(verify(new_main, c_fn, c_power, b_back) == 1, "OS Cycles de --to samples : accepte le retour (porte 1)")
    check(b_back == b_smp and unwrap(back)[0] == unwrap(smp_raw)[0],
          "le retour est l'OS Samples officiel une fois decode (porte 2 : celle d'une MAJ officielle)")
    check(verify(new_main, c_fn, c_power, b_fwd) == 1, "OS Cycles de --to samples : accepte aussi --to samples (mise a jour)")

    print("4. Garde-fous")
    check(verify(new_main, c_fn, c_power, b_cyc) == 4, "OS Cycles de --to samples : refuse l'OS Cycles officiel")
    check(verify(cyc_main, c_fn, c_power, b_cyc) == 1, "OS Cycles d'origine : accepte l'OS Cycles officiel (temoin)")
    bad = bytearray(b_back)
    bad[0x1000] ^= 1
    check(verify(new_main, c_fn, c_power, bytes(bad)) in (3, 4), "un octet change dans le retour : refuse")

    print("5. Transport du retour")
    head = lambda r: r[:r.find(0xF7) + 1]                   # noqa: E731
    hc, hb = head(cyc_raw), head(back)
    check(hb[4] == 0x11 and hb[8] == 0x0C and hb[:9] == hc[:9], "en-tete SysEx du Cycles (0x11, appareil 0x0C)")
    check(blob_of(back)[1]["product"] == 0x11, "chaque paquet verifie avec les sommes du Cycles")
    print(f"\nMAIN OS de --to samples : {fwd_main_sha}")
    print(f"--to samples   : {hashlib.sha256(fwd).hexdigest()}")
    print(f"--back-samples : {hashlib.sha256(back).hexdigest()}")
    if FAIL:
        print(f"\n{len(FAIL)} ECHEC(S)")
        sys.exit(1)
    print("\ntout est ok")


if __name__ == "__main__":
    main()
