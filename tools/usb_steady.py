"""Envoi à l'USB à heure fixe (notes/34) : les écritures communes au mod 6 canaux et à Model-TG.

L'OS envoie chaque bloc audio à l'ordinateur juste après l'avoir calculé (0x40002912 en 0x40059392) : l'instant
varie avec le temps de calcul. Avec une charge qui varie beaucoup (Model-TG et les moteurs du Syntakt sautent les
pistes au repos, les mutes, les effets éteints), la file USB se vide ou déborde : trous et trames sautées côté
ordinateur, rares en stéréo, fréquents avec le ring du mod 6 canaux. machines/usb6/feed.S note les envois et les
fait au début de l'interruption suivante, avant tout calcul, et aligne la file au démarrage du flux.

Les octets sont les mêmes avec ou sans le mod 6 canaux (la cible de la file est tirée de la profondeur du ring, lue
dans le code de l'OS) : 6ch-usbup et Model-TG les écrivent tous deux, et les constructeurs (build.py, builder.js)
acceptent une écriture déjà faite à l'identique par un autre tweak. Le code va dans le masque de sprite libéré
0x4015c044 (tools/sprites.py), derrière les stubs de 6ch-usbup ; trig-hold en occupe le début.

Preuve : tools/emu/test_usb_in.py.
"""
import pathlib
import shutil
import subprocess
import tempfile

import sprites

HERE = pathlib.Path(__file__).resolve().parent
USB6 = HERE / "machines" / "usb6"
BASE = 0x40000400
CROSS = next((c for c in ("m68k-linux-gnu-", "m68k-elf-") if shutil.which(c + "as")), "m68k-linux-gnu-")
MASK = 0x4015c044                  # masque libéré (720 o) : trig-hold, puis les stubs de 6ch-usbup, puis feed.S
FEED_AT = 0x4015c23c               # juste derrière le dernier stub de 6ch-usbup (dstoff6, fin 0x4015c23a)
# (VA, octets d'origine, symbole appelé à la place)
HOOKS = (
    (0x40058ca0, "a93c00000020", "feed_isr"),     # début de l'interruption de rendu : movel #32,%macsr
    (0x40059392, "4eb940002912", "feed_note"),    # envoi du bloc calculé
    (0x400593ce, "4eb940002912", "feed_note"),    # envoi de silence (son coupé : fichier ouvert)
)


def assemble(src, at):
    """(octets, symboles) d'une source de machines/usb6 assemblée à l'adresse at."""
    with tempfile.TemporaryDirectory() as d:
        obj, elf, out = (pathlib.Path(d) / n for n in ("a.o", "a.elf", "a.bin"))
        subprocess.run([CROSS + "as", "-mcpu=54418", "-o", str(obj), str(USB6 / src)], check=True)
        subprocess.run([CROSS + "ld", f"-Ttext={at:#x}", "-e", "0", "-o", str(elf), str(obj)], check=True)
        subprocess.run([CROSS + "objcopy", "-O", "binary", "-j", ".text", str(elf), str(out)], check=True)
        syms = {}
        for line in subprocess.run([CROSS + "nm", str(elf)], capture_output=True, text=True, check=True).stdout.splitlines():
            p_ = line.split()
            if len(p_) == 3:
                syms[p_[2]] = int(p_[0], 16)
        return out.read_bytes(), syms


def writes():
    """Écritures JSON : le code (feed.S), les 3 crochets, et la redirection qui libère le masque."""
    code, syms = assemble("feed.S", FEED_AT)
    lo, n = sprites.zone(MASK)
    if FEED_AT + len(code) > lo + n:
        raise SystemExit(f"!! feed.S : {len(code)} o à 0x{FEED_AT:08x}, au-delà du masque 0x{lo:08x}..0x{lo + n:08x}")
    out = [{"off": FEED_AT - BASE, "old": "ff" * len(code), "new": code.hex()}]
    out += [{"off": va - BASE, "old": old, "new": "4eb9" + f"{syms[sym]:08x}"} for va, old, sym in HOOKS]
    out.append(sprites.redirect_write(MASK))
    return sorted(out, key=lambda w: w["off"])


NOTE = "Envoi à l'USB à heure fixe (tools/usb_steady.py, notes/34) : la charge varie avec l'arrêt des voix muettes."


def add_to(tweak):
    """Le tweak (dictionnaire) avec ces écritures en plus, à leur place dans l'ordre des adresses, et une ligne de
    description. Pure : gen_syntakt_engines.py l'applique à la fin de build_tweak, et elle s'applique de même à un
    JSON déjà versionné (même résultat, sans recompiler)."""
    steady = writes()
    taken = [(w["off"], w["off"] + len(w["new"]) // 2) for w in tweak["writes"]]
    for w in steady:
        a, b = w["off"], w["off"] + len(w["new"]) // 2
        if any(a < y and x < b for x, y in taken):
            raise SystemExit(f"!! envoi à heure fixe : 0x{a + BASE:08x} déjà écrit par {tweak['id']}")
    tweak["writes"] = sorted(tweak["writes"] + steady, key=lambda w: w["off"])
    tweak["description"] = tweak["description"] + [NOTE]
    return tweak
