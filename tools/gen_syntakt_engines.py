#!/usr/bin/env python3
"""Génère les tweaks « syntakt-<moteurs> » : N vrais moteurs du Syntakt en machines ajoutées du Model:Cycles,
pour n'importe quel choix de moteurs du catalogue (notes/20). Le flasher web fait cocher les moteurs voulus.

Même méthode que gen_syntakt_machines.py (notes/19, testé : SDVtg + CPVtg), généralisée :
  - catalogue des moteurs (CATALOG) ; les machines ajoutées prennent les index 6, 7, 8… dans l'ordre du catalogue ;
  - passerelle bridge_engines.c (un moteur du Syntakt par machine) ; détours générés pour N machines ;
  - table machine -> moteur de l'OS (8 octets, 0x40118640) déplacée : plus de 2 machines ajoutées possibles ;
  - charge utile : moteurs du catalogue (réunion) et tables à adresses fixes, prévues pour 6 machines ajoutées.
Toutes les combinaisons sont générées ici, avec l'arrêt des voix muettes (notes/23) ; les anciens tweaks
sdvintage-7th et syntakt-vintage restent disponibles avec build.py.

    python3 tools/gen_syntakt_engines.py --cycles … --syntakt … --engines cp [--check]
    python3 tools/gen_syntakt_engines.py --cycles … --syntakt … --all [--check]   # toutes les autres combinaisons
"""
import argparse
import itertools
import json
import pathlib
import struct
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "emu"))

import gen_sdvintage_exact as gx   # noqa: E402
import gen_sdvintage_7th as g7     # noqa: E402
import gen_syntakt_machines as g8  # noqa: E402
import sprites                     # noqa: E402
import syntakt                     # noqa: E402

DEV = HERE.parent / "tweaks" / "model-cycles_OS1.13"
BASE = gx.BASE

# --- catalogue : moteurs de la boucle des voix du Syntakt, dans l'ordre des machines ajoutées ------------
# name : nom dans le menu MACHINES (5 lettres) ; engine : moteur du Syntakt (tables 0x40014920 / 0x400148f0) ;
# image : image de machine du Cycles montrée (l'OS n'en a que 6) ; knobs : COLOR, SHAPE, SWEEP, CONTOUR = p1..p4
# du Syntakt (nom long en mots de 8 lettres au plus, nom court, défaut[, min, max]), d'après les descripteurs de
# son interface. Ce que le moteur ajoute à la copie : code_end (fin de la plage de code), tables_high (tables
# placées à TABLES_AT), imm (immédiats « move.l #adr » qui sont des adresses, vérifiés à la main), roots
# (fonctions appelées par pointeur que la fermeture ne suit pas d'elle-même).
# punch_on / punch_off : valeur de l'emplacement 23 du Syntakt quand PUNCH est actif / inactif (défaut : celle
# du Cycles, PNCH 0..1 ; punch_off vaut 0 si absent).
CATALOG = {
    "sd": dict(label="SD VINTAGE", name="SDVtg", engine=6, update=0x40008074, render=0x4000847a, image=1, decay=33,
               knobs=(("Inharm", "INHM", 0), ("Freq Complex", "FCMP", 110), ("Pitch Sweep", "SWEP", 74),
                      ("Mod Envelope", "MENV", 80))),
    "cp": dict(label="CP VINTAGE", name="CPVtg", engine=7, update=0x40008580, render=0x40008988, image=3, decay=32,
               knobs=(("Body Char", "BODY", 24), ("Balance", "BAL", 25), ("Spacing Crunch", "SPCR", 46),
                      ("Body Envelope", "BENV", 37))),
    # type 36, descripteurs « TOY » 0x402302e8.. : Form, Impact, Brightness, Partial Decay (PNCH 0..1 : PUNCH)
    # imm : 0x800098ec = tampon SRAM rangé dans la voix (+412), suite de la série 0x8000945c, 0x80009580,
    # 0x800096a4, 0x800097c8 (pas de 0x124) déjà classée en adresses (gen_sdvintage_exact.py).
    "toy": dict(label="SY TOY", name="SYToy", engine=8, update=0x40008ae8, render=0x40008d58, image=4, decay=60,
                knobs=(("Form", "FORM", 24), ("Impact", "IMP", 60), ("Bright", "BRIG", 110),
                       ("Partial Decay", "PART", 64)),
                code_end=0x40008e0c, tables_high=((0x4003be38, 0x4003de38),), imm={0x800098ec}),
    # type 37, descripteurs « BITS » 0x40230488.. : Detune (40..88), Balance, Sample Rate Redux, Waveform.
    # L'emplacement 23 est Bit Redux (0..127), sans potard sur le Cycles : PUNCH actif = punch_on.
    # imm : 10 tables d'ondes de 0x804 o en SRAM (0x80004f74.. et 0x8000c888..), rangées dans la voix (+176,
    # +180) par 0x40006588 et l'update ; 0x8000a064 : tampon SRAM pris dans a4 (0x40006276).
    "bits": dict(label="SY BITS", name="SYBit", engine=9, update=0x40008e0c, render=0x400091e0, image=4, decay=60,
                 knobs=(("Detune", "DET", 52, 40, 88), ("Balance", "BAL", 102), ("Rate Redux", "SRR", 0),
                        ("Waveform", "WAVE", 21)), punch_on=80,
                 roots=(0x40006646,),           # appelée par pointeur (« lea 0x40006646,%fp » en 0x40008fd8)
                 code_end=0x400092ec, tables_high=((0x4003de38, 0x4003ee38),),
                 imm={0x80004f74, 0x80005778, 0x80005f7c, 0x80006780, 0x80006f84, 0x80007788, 0x8000c888,
                      0x8000d08c, 0x8000d890, 0x8000e094, 0x8000a064}),
    # type 38, descripteurs « SSAW » 0x40230628.. : Noise Modulation, Detune Animation, Detune, Oscillator Mix.
    # L'emplacement 23 est Fundamental Sub (0..2, défaut 2 = note jouée ; 1 et 0 : une et deux octaves plus bas),
    # sans potard sur le Cycles : PUNCH inactif = 2, actif = 1.
    # imm : 4 tampons SRAM (0x80009c58.., pas de 0x94) rangés dans la voix (+288, +416, +668).
    "swarm": dict(label="SY SWARM", name="SYSwm", engine=10, update=0x400092ec, render=0x400096e8, image=5, decay=75,
                  knobs=(("Noise Mod", "NMOD", 20), ("Detune Anim", "ANIM", 15), ("Detune", "DET", 70),
                         ("Osc Mix", "MIX", 127)), punch_off=2, punch_on=1,
                  code_end=0x400097dc, tables_high=((0x4003ee38, 0x40040038),),
                  imm={0x80009c58, 0x80009cec, 0x80009d80, 0x80009e14}),
}
# Combinaisons qui gardaient leur tweak d'origine (notes/18, notes/19). Depuis l'arrêt des voix muettes (notes/23),
# toutes passent par ce générateur ; sdvintage-7th et syntakt-vintage restent disponibles avec build.py.
LEGACY = {}
# Combinaisons testées sur un vrai Model:Cycles (affiché dans le flasher). Ajouter ici après un test réussi.
# Testés avant l'arrêt des voix muettes (30/09/2026) : SD, SD + CP, SY TOY, SD + CP + SY TOY, SY BITS, SY SWARM ;
# à retester avec lui.
HW_TESTED = set()
MAX_EXTRA = 6

# --- Syntakt : fermeture et plages copiées -----------------------------------------------------------------
# La copie dépend du DERNIER moteur coché (ordre du catalogue) : elle contient tout ce qu'il faut aux moteurs du
# catalogue jusqu'à lui, et au moins jusqu'à SY TOY. Ajouter un moteur au catalogue ne change donc pas, à
# l'octet près, les firmwares déjà testés sur la machine.
BASE_GEN = "toy"
CODE_START = 0x40002544                         # les fonctions (plage contiguë : le relatif au PC reste juste)
TABLES_LOW = (                                  # à la suite du code, sous la réplique de sa SRAM (0x43020000)
    (0x4000e488, 0x40010490),                   # table centrée sur 0x4000f48c (8 Ko), CP VINTAGE
    (0x40014980, 0x40016b90),                   # constantes + 2 tables de 4 Ko (0x40014b80, 0x40015b80)
    (0x40028438, 0x4003be38),                   # DEC x MENV, tables de 512 o de SD et CP VINTAGE
)
GX_IMM_ADDR = frozenset(gx.IMM_ADDR)             # immédiats-adresses de SD VINTAGE (gen_sdvintage_exact.py)

# --- SRAM interne du Cycles empruntée (notes/26) -------------------------------------------------------------
# Le cache de données du MCF54415 ne fait que 8 Ko : ce que les moteurs du Syntakt lisent et écrivent dans la
# réplique de leur SRAM (en SDRAM) passe par lui, à chaque bloc. Deux choses vont donc en SRAM interne :
#  - leurs tampons de travail, partagés par toutes les voix et écrits avant d'être lus à chaque calcul (comme sur le
#    Syntakt) : tableaux A et B de 7 éléments de 292 o (remise à zéro 0x40003f6c..0x4000402c : A + 292 k, B + 292 k)
#    et 4 tampons C de 148 o (SY SWARM). Seuls les 128 premiers octets de chaque élément servent (32 échantillons).
#    Ils prennent la zone de travail commune des machines d'origine, réécrite par chaque voix d'origine
#    (SCRATCH_POOL : leurs tableaux de 4 éléments de 292 o, 0x400a7b3e..0x400a7bd6, plus KICK et TONE), A et B
#    entrelacés pour garder le pas de 292 o (la somme des 7 voix de SY SWARM, 0x4000978a, lit B + 292 k) ;
#  - leur table de sinus (257 mots), identique à l'octet près à celle du Cycles (0x8000eee4, mêmes pointeurs dans
#    la remise à zéro des voix) : vérifié au build sur les deux fichiers.
SCRATCH_POOL = (0x8000beb8, 0x8000c8e8)
SRAM_MAP = (
    (0x80008c60, 0x8000945c, SCRATCH_POOL[0]),           # A_k -> zone + 292 k
    (0x8000945c, 0x80009c58, SCRATCH_POOL[0] + 128),     # B_k -> zone + 128 + 292 k
    (0x80009c58, 0x80009ea8, SCRATCH_POOL[0] + 2008),    # C_j -> zone + 2008 + 148 j
    (0x80004b70, 0x80004f74, 0x8000eee4),                # table de sinus
)
SCRATCH_HEADS = ((0x80008c60, 292, 7), (0x8000945c, 292, 7), (0x80009c58, 148, 4))   # (début, pas, éléments)
SINE = SRAM_MAP[3]


def sram_moved(a):
    """Adresse en SRAM du Cycles d'une adresse de la SRAM du Syntakt déplacée (SRAM_MAP), ou None."""
    for lo, hi, dst in SRAM_MAP:
        if lo <= a < hi:
            return a - lo + dst
    return None


def check_sram_map(img, st_img):
    """Les 128 premiers octets de chaque tampon tombent dans la zone empruntée, sans se chevaucher ; la table de
    sinus du Syntakt est celle du Cycles."""
    heads = sorted((sram_moved(s + k * step), s + k * step) for s, step, n in SCRATCH_HEADS for k in range(n))
    for (a, sa), (b, sb) in zip(heads, heads[1:]):
        if a + 128 > b:
            raise SystemExit(f"!! tampons {sa:#x} et {sb:#x} : chevauchement en SRAM")
    if heads[0][0] < SCRATCH_POOL[0] or heads[-1][0] + 128 > SCRATCH_POOL[1]:
        raise SystemExit("!! tampons hors de la zone de travail des machines d'origine")
    lo, hi, dst = SINE
    if sram_init(st_img, gx.ST_SRAM_INIT, lo, hi - lo) != sram_init(img, CY_SRAM_INIT, dst, hi - lo):
        raise SystemExit("!! table de sinus du Syntakt différente de celle du Cycles")


# contenu initial de la SRAM du Cycles, recopié au démarrage (0x4000045c) : (source, fin, destination)
CY_SRAM_INIT = ((0x4019b590, 0x401a2a50, 0x80000000), (0x401a2a50, 0x401aa140, 0x80008000))


def sram_init(image, init, a, n):
    """n octets de la SRAM à l'adresse a, tels que le démarrage les y recopie depuis l'image."""
    for lo, hi, dst in init:
        if dst <= a and a + n <= dst + hi - lo:
            return bytes(image[lo - BASE + a - dst:][:n])
    return None

# --- charge utile (adresses fixes, jusqu'à 6 machines ajoutées) --------------------------------------------
DST_BRIDGE = 0x43031000
STUBS = 0x43033000
DATA = 0x43033800            # noms, update/render, VEC, table machine -> moteur, chaînes
DESCN = 0x43034000           # 76 + 5 x N descripteurs (au plus 106 x 0x38 = 0x1730)
ROWSN = 0x43035800           # (6 + N) x 32 o
CCROWSN = 0x43035a00         # (6 + N) x 32 o
RECS = 0x43035c00            # enregistrement par machine ajoutée : 0x60 o chacun (76 o + drapeau)
TABLES_AT = 0x43036000       # tables_high des moteurs


def generation(codes):
    """Moteurs du catalogue dont la copie contient le code et les tables : jusqu'au dernier coché, au moins
    jusqu'à BASE_GEN."""
    order = list(CATALOG)
    return tuple(order[:max(order.index(BASE_GEN), max(order.index(c) for c in codes)) + 1])


# --- code du Syntakt en SRAM interne (notes/28) --------------------------------------------------------------
# Avec plusieurs moteurs différents, leur code ne tient pas dans le cache d'instructions (8 Ko) : il est relu en
# SDRAM à chaque bloc (notes/27). Environ 30 Ko de la SRAM ne servent qu'aux 30 tables d'ondes de CHORD, que seule
# son update lit, par la table de 32 pointeurs 0x40118590 (0x400a8060). Ces tables passent dans la charge utile
# (copiées au build depuis le MAIN OS de l'utilisateur ; l'OS réutilise leur copie de démarrage comme BSS) et
# CHORD_PTRS pointe dessus. La 1re zone libérée reçoit les fonctions atteintes du Syntakt (blocs tassés dans
# l'ordre : les sauts relatifs entre blocs sont recalculés, ils ne peuvent que raccourcir) et ses tables les plus
# lues ; le crochet de démarrage (stub.S) les y recopie depuis la charge utile, après l'initialisation de la SRAM.
CHORD_PTRS = 0x40118594      # 31 pointeurs (le 1er des 32, 0x40118590, vise une table de l'OS en SDRAM)
CHORD_BANKS = ((0x80001c5c, 0x800074b4), (0x8000cac0, 0x8000eae0))     # 22 + 8 tables de 1 028 o
SRAM_RUN = CHORD_BANKS[0]    # où s'exécute le code du Syntakt ; la 2e zone reçoit des états de voix (notes/29)
SRAM_TABLES = (                                  # tables de la SRAM du Syntakt, lues à chaque bloc, en lecture seule
    (0x8000a080, 0x8000a888),                   # SD VINTAGE : 2 tables (0x8000a080, 0x8000a484)
    (0x80006f84, 0x80007788),                   # SY SWARM (forme d'onde, aussi l'une des 10 de SY BITS)
)
GUARD = 16                   # octets voisins recopiés de part et d'autre (lectures juste avant ou après une table)
VOICES = 6                   # états des voix du Syntakt en SRAM (1 par piste ; ses voix 6 et 7 restent dans la réplique)
ST_VSTRIDE = 1800            # taille de l'état d'une voix du Syntakt (bridge_engines.c)


def code_blocks(ins, insns):
    """Plages contiguës du code atteint (écarts de remplissage de 2 o au plus compris)."""
    runs = []
    for a in sorted(insns):
        if runs and a - runs[-1][1] <= 2:
            runs[-1][1] = a + ins[a][0]
        else:
            runs.append([a, a + ins[a][0]])
    return [tuple(r) for r in runs]


def st_sram_src(a):
    """Adresse, dans l'image du Syntakt, du contenu initial de l'adresse a de sa SRAM."""
    for lo, hi, dst in gx.ST_SRAM_INIT:
        if dst <= a < dst + hi - lo:
            return lo + a - dst
    raise SystemExit(f"!! {a:#x} hors de la SRAM initialisée du Syntakt")


def layout(gen, blocks):
    """Disposition de la charge utile pour une génération. Zone de transit (DST_CODE..) : l'image des deux zones
    de SRAM libérées, que le crochet de démarrage y recopie (SRAM_BANKS) ; la 1re reçoit les blocs de code, les
    SRAM_TABLES (avec leurs gardes) puis des voix du Syntakt ; la 2e, les autres voix (VOICES en tout, contenu
    initial de leur SRAM). Puis les tables du bas (sous la réplique de la SRAM), les tables du haut (TABLES_AT) et
    les tables de CHORD. Rend copies (source Syntakt, fin, destination), move (plages pour gx.move : adresses
    d'EXÉCUTION), stage (code : source, fin, transit), run(transit) -> exécution, voices (adresses d'exécution
    des voix 0..VOICES-1), et la fin de la charge utile. Le code et les tables gardent l'alignement de leur source
    modulo 4 (en SRAM) ou 8 (en SDRAM) ; les voix sont alignées sur 8, comme dans la SRAM du Syntakt."""
    banks, at = [], gx.DST_CODE
    for lo, hi in CHORD_BANKS:
        banks.append((at, lo, hi - lo))
        at += hi - lo
    stage_end = at
    stage, pads, at = [], [], gx.DST_CODE
    for lo, hi in blocks:
        if (lo - at) % 4:                          # 2 o (code aligné sur 2) : un nop, pour un désassemblage suivi
            pads.append(at)
            at += 2
        stage.append((lo, hi, at))
        at += hi - lo
    tabs = []
    for lo, hi in SRAM_TABLES:
        at += (lo - GUARD - at) % 4
        tabs.append((lo, hi, at + GUARD))
        at += hi - lo + 2 * GUARD
    voices = []
    for b0, _, n in banks:
        at = max(at, b0)
        while len(voices) < VOICES and (at + 7) // 8 * 8 + ST_VSTRIDE <= b0 + n:
            at = (at + 7) // 8 * 8
            voices.append(at)
            at += ST_VSTRIDE
        if at > b0 + n:
            raise SystemExit(f"!! code et tables pour la SRAM : {at - b0} o, plus de place")
    if len(voices) < VOICES:
        raise SystemExit(f"!! {len(voices)} voix du Syntakt seulement en SRAM")

    def run(x):
        for b0, r0, n in banks:
            if b0 <= x < b0 + n:
                return x - b0 + r0
        return x
    copies = (list(stage) + [(st_sram_src(lo - GUARD), st_sram_src(hi + GUARD), dst - GUARD) for lo, hi, dst in tabs]
              + [(st_sram_src(0x80000000 + ST_VSTRIDE * i), st_sram_src(0x80000000 + ST_VSTRIDE * (i + 1)), v)
                 for i, v in enumerate(voices)])
    high = tuple(t for c in gen for t in CATALOG[c].get("tables_high", ()))
    sdram, at = [], stage_end
    for group, limit in ((TABLES_LOW, gx.DST_SRAM), (high, None)):
        if limit is None:
            at = TABLES_AT
        for lo, hi in group:
            at += (lo - at) % 8
            sdram.append((lo, hi, at))
            at += hi - lo
        if limit is not None and at > limit:
            raise SystemExit(f"!! tables du bas jusqu'à {at:#x} : plus de place sous {limit:#x}")
    copies += sdram
    chord_at = (at + 0xff) & ~0xff
    end = chord_at + sum(hi - lo for lo, hi in CHORD_BANKS)
    # gx.move prend la 1re plage qui contient l'adresse : code et tables en SRAM du Cycles, tables en SDRAM, puis la
    # SRAM du Syntakt (tampons et table de sinus dans la SRAM du Cycles, SRAM_MAP ; le reste dans sa réplique)
    move = ([(lo, hi, run(dst)) for lo, hi, dst in stage] + [(lo, hi, run(dst)) for lo, hi, dst in tabs] + sdram
            + [*SRAM_MAP, (0x80000000, 0x80010000, gx.DST_SRAM), (*gx.ST_BSS, 0x43030000)])
    return dict(copies=copies, move=tuple(move), stage=stage, pads=pads, stage_end=stage_end, run=run, banks=banks,
                voices=[run(v) for v in voices], chord_at=chord_at, end=(end + 0xff) & ~0xff)


def code_patches(st_img, ins, insns, lay, relocs):
    """Zone de transit corrigée : relocalisations des adresses absolues, et déplacements relatifs au PC recalculés
    pour les blocs tassés. Rend [(adresse dans la charge utile, 4 octets d'origine, 4 octets corrigés)] sans
    chevauchement, et le nombre de déplacements changés."""
    lo0, hi0 = gx.DST_CODE, lay["stage_end"]
    orig = bytearray(hi0 - lo0)
    for lo, hi, dst in lay["copies"]:
        if lo0 <= dst < hi0:
            orig[dst - lo0:dst - lo0 + hi - lo] = st_img[lo - BASE:hi - BASE]
    for a in lay["pads"]:
        orig[a - lo0:a - lo0 + 2] = b"\x4e\x71"
    new = bytearray(orig)

    def stage_of(va):
        return next(dst + va - lo for lo, hi, dst in lay["stage"] if lo <= va < hi)

    def run_of(va):
        return lay["run"](stage_of(va))
    for va, old, nv in relocs:
        at = stage_of(va) - lo0
        if new[at:at + 4] != old.to_bytes(4, "big"):
            raise SystemExit(f"!! relocalisation {va:#x}")
        new[at:at + 4] = nv.to_bytes(4, "big")
    moved = 0
    for a in sorted(insns):
        size, mn, ops = ins[a]
        branch = bool(gx.BRANCH.match(mn))
        if not branch and "%pc@" not in ops:
            continue
        t = gx.values(ops, immediates=False)[0]
        raw = st_img[a - BASE:a - BASE + size]
        if branch:                                   # déplacement 8 bits dans l'opcode, ou 16 / 32 bits ensuite
            k, n = (1, 1) if size == 2 else (2, 2) if size == 4 else (2, 4)
            base = 2
        else:                                        # (d16,PC) : mot d'extension, base = son adresse
            k = next((k for k in range(2, size - 1, 2)
                      if int.from_bytes(raw[k:k + 2], "big", signed=True) == t - (a + k)), None)
            if k is None:
                raise SystemExit(f"!! {a:#x} {mn} {ops} : déplacement relatif au PC introuvable")
            n, base = 2, k
        if int.from_bytes(raw[k:k + n], "big", signed=True) != t - (a + base):
            raise SystemExit(f"!! {a:#x} {mn} {ops} : déplacement inattendu")
        d = run_of(t) - (run_of(a) + base)
        if not -(1 << (8 * n - 1)) <= d < 1 << (8 * n - 1) or (n == 1 and d in (0, -1)):
            raise SystemExit(f"!! {a:#x} {mn} {ops} : nouveau déplacement {d} hors du champ")
        if d != t - (a + base):
            moved += 1
            at = stage_of(a) + k - lo0
            new[at:at + n] = d.to_bytes(n, "big", signed=True)
    patches, p = [], 0
    while p < len(new):
        if new[p] != orig[p]:
            if p + 4 > len(new):
                raise SystemExit("!! correction en fin de zone de transit")
            patches.append((lo0 + p, bytes(orig[p:p + 4]), bytes(new[p:p + 4])))
            p += 4
        else:
            p += 1
    return patches, moved


def chord_moved(a, lay):
    """Nouvelle adresse (charge utile) d'une adresse des tables d'ondes de CHORD en SRAM."""
    at = lay["chord_at"]
    for lo, hi in CHORD_BANKS:
        if lo <= a < hi:
            return at + a - lo
        at += hi - lo
    raise SystemExit(f"!! {a:#x} : pas une table d'ondes de CHORD")


MAP = g7.ENGINE_MAP          # table machine -> entrée des tables update/render (8 octets, 0x40118640)

# --- régulateur de charge (notes/23, notes/25) : dans la boucle des voix, l'appel update/render de chaque piste
# (0x400a7dfe..0x400a7e24) passe par un détour qui demande à la passerelle (voice_gate, voice_after) s'il faut la
# calculer ; la sonde de l'appel de la fonction audio (0x40059382) mesure la charge de chaque bloc (audio_end).
# D'ordinaire, une voix restée sous IDLE_THR (valeur absolue, échelle 32 bits de la sortie de render) pendant
# IDLE_BLOCKS blocs, sans trig, n'est plus calculée ; sous forte charge, le seuil monte et la voix la plus faible
# s'éteint par un fondu (bridge_engines.c). Vaut pour les 6 machines d'origine comme pour les machines ajoutées.
DISPATCH = (0x400a7dfe, 0x400a7e24)
AUDIO_CALL = 0x40059382      # jsr 0x4005979e : fonction audio, appelée par l'interruption à chaque bloc
IDLE_BLOCKS = 64             # 43 ms
IDLE_THR = 1 << 13           # -108 dB sous la pleine échelle
# Firmware de diagnostic (--meter) : noms des machines « pic/moyenne » (False, notes/23, notes/29) ou
# « moyenne/voix » (True : coût de la voix de chaque machine, diagnostics v6 et v7, notes/27)
METER_VOICE = False


def subset_id(codes, generic=False):
    return (not generic and LEGACY.get(tuple(codes))) or "syntakt-" + "-".join(codes)


def subsets():
    """Toutes les combinaisons de moteurs du catalogue, dans l'ordre du catalogue."""
    for r in range(1, len(CATALOG) + 1):
        yield from (list(c) for c in itertools.combinations(CATALOG, r))


def detours_asm(n, images, firsts):
    """Détours pour n machines ajoutées (index 6..5+n), descripteurs firsts[i]..firsts[i]+4 (5 par machine)."""
    last = 76 + 5 * n                                    # 1er descripteur après ceux des machines ajoutées
    a = [".text"]

    def lab(s):
        a.append(s + ":")

    def ins(s):
        a.append("\t" + s)
    # état par descripteur : descripteurs ajoutés -> objets de SNARE 51..55
    lab("map_state")
    ins("moveq #76, %d1"); ins("cmp.l %d1, %d0"); ins("bcs.w 9f")
    ins(f"cmp.l #{last}, %d0"); ins("bcs.s 1f"); ins("moveq #0, %d0"); ins("rts")
    lab("1")
    ins("moveq #76, %d1"); ins("sub.l %d1, %d0")
    lab("2")
    ins("moveq #5, %d1"); ins("cmp.l %d1, %d0"); ins("bcs.s 3f"); ins("sub.l %d1, %d0"); ins("bra.s 2b")
    lab("3")
    ins("moveq #51, %d1"); ins("add.l %d1, %d0")
    lab("9"); ins("rts")
    for name, off in (("state_at", "0x40a71754"), ("state_connect", "0x40a71768")):
        a.append(f"\t.globl\t{name}"); lab(name)
        ins("move.l 4(%sp), %d0"); ins("bsr.w map_state"); ins("moveq #100, %d1"); ins("muls.l %d1, %d0")
        ins(f"add.l #{off}, %d0")
        if name == "state_at":
            ins("rts")
        else:
            ins("pea 0x40a71500"); ins("move.l 12(%sp), -(%sp)"); ins("move.l %d0, -(%sp)"); ins("jsr 0x400ddf60")
            ins("lea 12(%sp), %sp"); ins("move.l #0x40a71500, %d0"); ins("rts")
    # CC reçu -> descripteur
    a.append("\t.globl\tcc_bounds"); lab("cc_bounds")
    ins("moveq #5, %d2"); ins("cmp.l %d1, %d2"); ins("bcs.s 1f")
    ins(f"moveq #{5 + n}, %d2"); ins("cmp.l %d0, %d2"); ins("bcs.s 2f"); ins("jmp 0x4005a8fa")
    lab("1"); ins("jmp 0x4005a928")
    lab("2"); ins("jmp 0x4005a91c")
    # image montrée pour une machine
    lab("shown")
    for i in range(n):
        ins(f"moveq #{6 + i}, %d1"); ins("cmp.l %d1, %d0"); ins(f"bne.s 8{i}f"); ins(f"moveq #{images[i]}, %d0"); ins("rts")
        lab(f"8{i}")
    ins("rts")
    a.append("\t.globl\tdrum_icons"); lab("drum_icons")
    ins("move.l %d3, %d0"); ins("bsr.w shown"); ins("move.l %d0, %d4"); ins("lsl.l #2, %d0"); ins("lsl.l #5, %d4")
    ins("sub.l %d0, %d4"); ins("pea 0x1"); ins("pea 0x17"); ins("pea 0x20"); ins("lea 0x40071da4, %a2")
    ins("movea.l 0x40fe32cc, %a1"); ins("adda.l %d4, %a1"); ins("move.l %a1, -(%sp)"); ins("move.l %d2, -(%sp)")
    ins("jsr (%a2)"); ins("lea 48(%sp), %sp"); ins("pea 0x1"); ins("pea 0x22"); ins("add.l 0x40fe384c, %d4")
    ins("pea 0x60"); ins("move.l %d4, -(%sp)"); ins("move.l %d2, -(%sp)"); ins("jsr (%a2)"); ins("lea 20(%sp), %sp")
    ins("jmp 0x400a2680")
    a.append("\t.globl\tsmall_icon"); lab("small_icon")
    ins("lea 10(%a0), %a0"); ins("move.l %a0, -(%sp)"); ins("move.l 16(%fp), -(%sp)"); ins("move.l %d2, %d0")
    ins("bpl.s 1f"); ins("moveq #0, %d0")
    lab("1"); ins("moveq #5, %d1"); ins("cmp.l %d0, %d1"); ins("bge.s 3f"); ins("bsr.w shown")
    ins("moveq #5, %d1"); ins("cmp.l %d0, %d1"); ins("bge.s 3f"); ins("moveq #5, %d0")
    lab("3"); ins("jmp 0x400a4dde")
    # enregistrements par machine. Une machine ou un index hors limites (piste réglée sur une machine ajoutée
    # par un autre choix de moteurs, notes/20 §5) donne celui de KICK : l'OS lirait sinon 76 o avant le tableau.
    a.append("#define REC_BASE 0x40a71540")
    a.append("#define REC_SNARE (REC_BASE + 2 * 76)")
    a.append("\t.globl\trecord_at"); lab("record_at")
    ins("move.l 4(%sp), %d0")
    for i in range(n):
        ins(f"moveq #{7 + i}, %d1"); ins("cmp.l %d1, %d0"); ins(f"beq.w rec_{i}")
    ins("moveq #6, %d1"); ins("cmp.l %d0, %d1"); ins("bcc.s 1f"); ins("moveq #1, %d0")
    lab("1"); ins("moveq #76, %d1"); ins("muls.l %d1, %d0"); ins("add.l #REC_BASE, %d0"); ins("rts")
    a.append("\t.globl\trecord_of"); lab("record_of")
    ins("move.l 4(%sp), %d0")
    for i in range(n):
        ins(f"moveq #{6 + i}, %d1"); ins("cmp.l %d1, %d0"); ins(f"beq.w rec_{i}")
    ins("moveq #5, %d1"); ins("cmp.l %d0, %d1"); ins("bcs.s 2f"); ins("lea 0x401091b4, %a0")
    ins("mvs.b (%a0,%d0.l), %d0"); ins("moveq #6, %d1"); ins("cmp.l %d0, %d1"); ins("bcc.s 3f")
    lab("2"); ins("moveq #1, %d0")
    lab("3"); ins("moveq #76, %d1"); ins("muls.l %d1, %d0"); ins("add.l #REC_BASE, %d0"); ins("rts")
    for i in range(n):
        lab(f"rec_{i}"); ins(f"lea {RECS + 0x60 * i:#x}, %a0"); ins(f"moveq #{firsts[i] - 51}, %d0"); ins("bra.w rec_build")
    lab("rec_build")
    ins("tst.b 76(%a0)"); ins("bne.w 9f"); ins("move.l %d2, -(%sp)"); ins("move.l %a2, -(%sp)"); ins("movea.l %a0, %a2")
    ins("move.l %d0, %d2"); ins("pea REC_SNARE"); ins("move.l %a2, -(%sp)"); ins("jsr 0x400f8f02"); ins("addq.l #8, %sp")
    ins("pea REC_SNARE + 4"); ins("pea 4(%a2)"); ins("jsr 0x400f8f02"); ins("addq.l #8, %sp")
    ins("lea REC_SNARE + 8, %a0"); ins("lea 8(%a2), %a1"); ins("moveq #16, %d1"); ins("move.l %d1, -(%sp)")
    lab("1"); ins("move.l (%a0)+, %d0"); ins("moveq #51, %d1"); ins("cmp.l %d1, %d0"); ins("blt.s 2f")
    ins("moveq #55, %d1"); ins("cmp.l %d0, %d1"); ins("blt.s 2f"); ins("add.l %d2, %d0")
    lab("2"); ins("move.l %d0, (%a1)+"); ins("subq.l #1, (%sp)"); ins("bpl.s 1b"); ins("addq.l #4, %sp")
    ins("moveq #1, %d0"); ins("move.b %d0, 76(%a2)"); ins("movea.l %a2, %a0"); ins("move.l (%sp)+, %a2")
    ins("move.l (%sp)+, %d2")
    lab("9"); ins("move.l %a0, %d0"); ins("rts")
    # potard -> descripteur : table machine -> enregistrement [1..6+n]
    a.append("\t.globl\tknob_vec"); lab("knob_vec")
    ins("move.l 36(%sp), %d0"); ins("movea.l 104(%a2), %a1"); ins(f"moveq #{5 + n}, %d1"); ins("cmp.l %d0, %d1")
    ins("bcc.s 1f"); ins("moveq #0, %d0"); ins("rts")                    # hors limites : les potards de KICK
    lab("1"); ins("moveq #6, %d1"); ins("cmp.l %d1, %d0")
    ins("blt.s 2f"); ins(f"lea {DATA + 12 * (6 + n):#x}, %a1")
    lab("2"); ins("rts")
    # machine d'un descripteur (applicabilité) et rangée du constructeur : descripteurs ajoutés -> leur machine
    a.append("\t.globl\tdesc_machine"); lab("desc_machine")
    ins("move.l 4(%sp), %d0")
    for i in range(n):
        ins(f"cmp.l #{firsts[i]}, %d0"); ins(f"bcs.s 7{i}f"); ins(f"cmp.l #{firsts[i] + 3}, %d0"); ins(f"bhi.s 7{i}f")
        ins(f"moveq #{6 + i}, %d0"); ins("rts")
        lab(f"7{i}")
    ins(f"cmp.l #{last}, %d0"); ins("bcs.s 2f"); ins("moveq #0, %d0")
    lab("2"); ins("move.l %d0, %d1"); ins("lsl.l #3, %d1"); ins("lsl.l #6, %d0"); ins("sub.l %d1, %d0")
    ins(f"lea {DESCN:#x}, %a0"); ins("move.l (%a0,%d0.l), %d0"); ins("rts")
    a.append("\t.globl\tbuilder_row"); lab("builder_row")
    ins("moveq #6, %d0"); ins("cmp.l %d5, %d0"); ins("bcs.w 1f")
    for i in range(n):
        ins(f"cmp.l #{firsts[i]}, %d2"); ins(f"bcs.s 6{i}f"); ins(f"cmp.l #{firsts[i] + 3}, %d2"); ins(f"bhi.s 6{i}f")
        ins(f"moveq #{6 + i}, %d5"); ins("bra.w 2f")
        lab(f"6{i}")
    lab("2"); ins("jmp 0x4005a384")
    lab("1"); ins("jmp 0x4005a346")
    return "\n".join(a) + "\n"


def probe_asm(syms):
    """Sonde de l'appel de la fonction audio par l'interruption (0x40059382) : met de côté l'adresse de retour
    (la fonction appelée voit la pile exactement comme avant), note l'heure, appelle la fonction, puis
    audio_end() (régulateur de charge, compteur du firmware de diagnostic)."""
    g = lambda n: f"{syms[n]:#x}"
    return f"""
	.globl	audio_probe
audio_probe:
	move.l	(%sp)+, {g('gov_ret_audio')}
	move.l	0xfc07000c, %d1
	move.l	%d1, {g('gov_t0_audio')}
	jsr	0x4005979e
	move.l	%d0, -(%sp)
	jsr	{g('audio_end')}
	move.l	(%sp)+, %d0
	move.l	{g('gov_ret_audio')}, -(%sp)
	rts
"""


def dispatch_asm(syms, rnd_at):
    """Détour de l'appel update/render d'une piste dans la boucle des voix (0x400a7dfe). Registres de la boucle à
    l'entrée : d0 = borne des machines, d4 = entrée des tables, d1 = modulation de note, d6 = table update,
    d3 = sortie de la piste (32 x int32), d2 = numéro de piste, a2 = paramètres, fp = voix, a5 = voix + 0x34
    (trig de ce bloc), a3 = voix + 0x38 (trig du bloc précédent). Seuls d0, d1, a0 et a1 sont modifiés, comme
    par les appels d'origine ; voice_gate et voice_after (C) préservent les autres."""
    g = lambda n: f"{syms[n]:#x}"
    return f"""
	.globl	dispatch
dispatch:
	cmp.l	%d4, %d0
	bcs.w	9f			/* machine hors borne : rien, comme l'OS */
	move.l	%d1, -(%sp)		/* modulation de note, pour update */
	move.l	%d4, -(%sp)		/* voice_gate(piste, trig, moteur) */
	move.l	(%a5), %d0
	or.l	(%a3), %d0
	move.l	%d0, -(%sp)
	move.l	%d2, -(%sp)
	jsr	{g('voice_gate')}
	lea	12(%sp), %sp
	move.l	(%sp)+, %d1
	tst.l	%d0
	beq.s	3f
	movea.l	%d3, %a0		/* pas calculée : sortie à zéro */
	moveq	#31, %d0
2:	clr.l	(%a0)+
	subq.l	#1, %d0
	bpl.s	2b
	bra.w	9f
3:	movea.l	%d6, %a0		/* update puis render, exactement comme l'OS */
	movea.l	(%a0,%d4.l*4), %a1
	move.l	%a2, -(%sp)
	move.l	%fp, -(%sp)
	move.l	%d1, -(%sp)
	jsr	(%a1)
	move.l	%fp, -(%sp)
	move.l	%d3, -(%sp)
	lea	{rnd_at:#x}, %a0
	movea.l	(%a0,%d4.l*4), %a1
	jsr	(%a1)
	lea	20(%sp), %sp
	move.l	%d3, -(%sp)		/* voice_after(piste, sortie) */
	move.l	%d2, -(%sp)
	jsr	{g('voice_after')}
	addq.l	#8, %sp
9:	jmp	{DISPATCH[1]:#x}
"""


def compile_code(tmp, machines, payload_longs, meter=None, rnd_at=None, nm=0, run=None, lay=None):
    """run : adresse d'exécution d'une fonction du Syntakt ; lay : disposition (layout()) : zones de SRAM que le
    crochet de démarrage remplit (stub.S), adresses des états de voix."""
    defs = [f"-DST_VINIT_AT={run(0x40002544):#x}", f"-DST_RESET_AT={run(0x40003ee0):#x}",
            f"-DST_PREP_AT={run(0x4000255e):#x}"] + [f"-DST_VOICE_{i}={v:#x}" for i, v in enumerate(lay["voices"])]
    for m in machines:
        defs += [f"-DUPD_{m['engine']}={run(m['update']):#x}", f"-DRND_{m['engine']}={run(m['render']):#x}"]
        if "punch_on" in m:
            defs.append(f"-DPUNCH_ON_{m['engine']}={m['punch_on']}")
        if "punch_off" in m:
            defs.append(f"-DPUNCH_OFF_{m['engine']}={m['punch_off']}")
    defs += [f"-DIDLE_THR={IDLE_THR}", f"-DIDLE_BLOCKS={IDLE_BLOCKS}"]
    if meter:                                   # noms des machines (écran MACHINES) : « moyenne/voix »
        defs += ["-DLOAD_METER", f"-DMETER_BUF={meter:#x}", f"-DMETER_N={nm}"] + (["-DMETER_VOICE"] if METER_VOICE else [])
    obj, stub, elf = tmp / "bridge.o", tmp / "stub.o", tmp / "bridge.elf"
    gx.run([gx.CROSS + "gcc", *gx.CFLAGS, *defs, "-c", str(gx.SRC / "bridge_engines.c"), "-o", str(obj)])
    (s0, r0, n0), (s1, r1, n1) = lay["banks"]
    if s0 != gx.DST_CODE or s1 != s0 + n0 or n0 % 4 or n1 % 4:
        raise SystemExit("!! zones de SRAM : transit au début de la charge utile, à la suite, en mots")
    gx.run([gx.CROSS + "gcc", "-mcpu=54418", "-c", str(gx.SRC / "stub.S"), "-o", str(stub),
            f"-DPAYLOAD_SRC={BASE + gx.IMAGE_LEN:#x}", f"-DPAYLOAD_DST={gx.DST_CODE:#x}", f"-DPAYLOAD_LONGS={payload_longs}",
            f"-DSRAM_RUN_AT={r0:#x}", f"-DSRAM_LONGS={n0 // 4}", f"-DSRAM2_RUN_AT={r1:#x}", f"-DSRAM2_LONGS={n1 // 4}"])
    gx.run([gx.CROSS + "ld", "-T", str(gx.SRC / "link.ld"), "-o", str(elf), str(stub), str(obj)])
    blobs = {}
    for sec in (".stub", ".bridge"):
        out = tmp / (sec.strip(".") + ".bin")
        gx.run([gx.CROSS + "objcopy", "-O", "binary", "-j", sec, str(elf), str(out)])
        blobs[sec] = out.read_bytes()
    syms, data_end = {}, DST_BRIDGE + 0x1000
    for line in gx.run([gx.CROSS + "nm", "-S", str(elf)]).splitlines():
        parts = line.split()
        syms[parts[-1]] = int(parts[0], 16)
        if len(parts) == 4 and int(parts[0], 16) >= DST_BRIDGE + 0x1000:
            data_end = max(data_end, int(parts[0], 16) + int(parts[1], 16))
    if len(blobs[".bridge"]) > 0x1000 or data_end > gx.DST_END:
        raise SystemExit("!! passerelle trop grande")
    # la charge utile ne recopie que le code (et les constantes) de la passerelle : ses variables doivent être en
    # BSS, donc à zéro au démarrage ; une section .data non vide y serait perdue
    for line in gx.run([gx.CROSS + "objdump", "-h", str(obj)]).splitlines():
        f = line.split()
        if len(f) > 2 and f[1].startswith(".data") and int(f[2], 16):
            raise SystemExit(f"!! passerelle : données initialisées ({f[1]}), non recopiées dans la charge utile")
    src, o, e, b = tmp / "det.S", tmp / "det.o", tmp / "det.elf", tmp / "det.bin"
    src.write_text(detours_asm(len(machines), [m["image"] for m in machines], [76 + 5 * i for i in range(len(machines))])
                   + probe_asm(syms) + dispatch_asm(syms, rnd_at))
    gx.run([gx.CROSS + "gcc", "-mcpu=54418", "-c", str(src), "-o", str(o)])
    gx.run([gx.CROSS + "ld", "-Ttext", f"{STUBS:#x}", "-o", str(e), str(o)])
    gx.run([gx.CROSS + "objcopy", "-O", "binary", "-j", ".text", str(e), str(b)])
    ssyms = {p[-1]: int(p[0], 16) for p in (l.split() for l in gx.run([gx.CROSS + "nm", str(e)]).splitlines()) if len(p) == 3}
    stubs = b.read_bytes()
    if STUBS + len(stubs) > DATA:
        raise SystemExit("!! détours trop grands")
    return blobs, syms, stubs, ssyms


GX_ROOTS = tuple(gx.ROOTS)
_ANALYSIS = {}


def analyse(st_img, gen):
    """Pour une génération (moteurs dont la copie contient le code) : fermeture, blocs, disposition et corrections
    du code du Syntakt copié. Laisse gx.SEGMENTS sur cette disposition (gx.move : adresses d'exécution)."""
    gx.ROOTS = GX_ROOTS + tuple(x for c in gen for x in (CATALOG[c]["update"], CATALOG[c]["render"],
                                                        *CATALOG[c].get("roots", ())))
    gx.IMM_ADDR = set(GX_IMM_ADDR) | g8.IMM_ADDR | {a for c in gen for a in CATALOG[c].get("imm", ())}
    if gen not in _ANALYSIS:
        with tempfile.TemporaryDirectory() as d:
            ins = gx.disasm(st_img, pathlib.Path(d))
        funcs, insns = gx.closure(ins)
        code = (CODE_START, max(CATALOG[c].get("code_end", 0) for c in gen))
        if not all(code[0] <= a < code[1] for a in insns):
            raise SystemExit(f"!! code hors de la plage prévue : {[hex(a) for a in sorted(insns) if not code[0] <= a < code[1]][:4]}")
        # Garde-fou : une adresse de code prise par « lea » (pointeur de fonction) doit être dans la fermeture,
        # sinon ses adresses ne sont pas relocalisées (SY BITS : « lea 0x40006646,%fp », notes/21).
        missed = sorted({v for a in insns if ins[a][1] == "lea" for v in gx.values(ins[a][2], immediates=False)
                         if gx.ST_CODE[0] <= v < code[1] and v in ins and v not in insns})
        if missed:
            raise SystemExit(f"!! pointeurs de fonction non suivis (à ajouter à roots) : {[hex(v) for v in missed]}")
        blocks = code_blocks(ins, insns)
        lay = layout(gen, blocks)
        gx.SEGMENTS, gx.PC_OK = lay["move"], blocks
        relocs = gx.relocations(st_img, ins, insns)
        patches, moved = code_patches(st_img, ins, insns, lay, relocs)
        _ANALYSIS[gen] = dict(lay=lay, blocks=blocks, patches=patches, moved=moved, relocs=len(relocs),
                              funcs=len(funcs), code_bytes=sum(ins[a][0] for a in insns))
    an = _ANALYSIS[gen]
    gx.SEGMENTS, gx.PC_OK = an["lay"]["move"], an["blocks"]
    return an


def build_tweak(img, st_img, codes, generic=False, meter=False):
    machines = [dict(CATALOG[c], code=c, index=6 + i) for i, c in enumerate(codes)]
    n = len(machines)
    if not 1 <= n <= MAX_EXTRA:
        raise SystemExit("!! nombre de moteurs")
    u32 = lambda va: struct.unpack_from(">I", img, va - BASE)[0]
    check_sram_map(img, st_img)
    an = analyse(st_img, generation(codes))
    lay = an["lay"]
    size = lay["end"] - gx.DST_CODE
    nm = 6 + n
    names_at, upd_at, rnd_at, vec_at, map_at = DATA, DATA + 4 * nm, DATA + 8 * nm, DATA + 12 * nm, DATA + 16 * nm
    strings = [m["name"] for m in machines] + [k[i] for m in machines for k in m["knobs"] for i in (0, 1)]
    at, addr = map_at + ((nm + 3) & ~3), {}
    for s in strings:
        if s not in addr:
            addr[s] = at
            at += len(s) + 1
    meter_at = at                               # compteur : un nom de 8 o par machine (5 caractères au plus)
    if meter:
        at += 8 * nm
    with tempfile.TemporaryDirectory() as d:
        blobs, syms, stubs, ssyms = compile_code(pathlib.Path(d), machines, size // 4,
                                                 meter_at if meter else None, rnd_at, nm, gx.move, lay)

    names = [u32(g7.NAMES + 4 * i) for i in range(6)] + [addr[m["name"]] for m in machines]
    if meter:
        names = [meter_at + 8 * m for m in range(nm)]
    upd = [u32(g7.UPDATE_TAB + 4 * i) for i in range(6)] + [syms[f"bridge_update_{m['engine']}"] for m in machines]
    rnd = [u32(g7.RENDER_TAB + 4 * i) for i in range(6)] + [syms[f"bridge_render_{m['engine']}"] for m in machines]
    data = bytearray()
    for t in (names, upd, rnd, range(1, nm + 1)):
        data += b"".join(g7.be32(x) for x in t)
    data += img[MAP - BASE:MAP - BASE + 6] + bytes(range(6, nm)) + bytes(((nm + 3) & ~3) - nm)   # machine -> entrée
    for s in addr:
        data += s.encode("ascii") + b"\0"
    if meter:
        data += b"--/--\0\0\0" * nm
    if DATA + len(data) > DESCN:
        raise SystemExit("!! données")

    new = bytearray()
    for m in machines:
        for k, (long_, short, default, *rng) in enumerate(m["knobs"]):
            e = bytearray(img[g7.DESC + (g7.SNARE_DESC + k) * g7.DSTRIDE - BASE:][:g7.DSTRIDE])
            e[0x00:0x04] = g7.be32(6)                 # « propre à une machine » ; rattaché à la sienne par les détours
            if rng:                                    # plage propre (sinon 0..127, comme SNARE)
                e[0x08:0x0c], e[0x0c:0x10] = g7.be32(rng[0] << 8), g7.be32(rng[1] << 8)
            e[0x10:0x14] = g7.be32(default << 8)
            e[0x2c:0x30] = g7.be32(addr[long_])
            e[0x34:0x38] = g7.be32(addr[short])
            new += e
        e = bytearray(img[g7.DESC + (g7.SNARE_DESC + 4) * g7.DSTRIDE - BASE:][:g7.DSTRIDE])
        e[0x10:0x14] = g7.be32(m["decay"] << 8)
        new += e
    ndesc = g7.NDESC + 5 * n

    writes = []

    def w(va, old, new_):
        if img[va - BASE:va - BASE + len(old)] != old:
            raise SystemExit(f"!! {va:#x} : {old.hex()} attendu, {img[va - BASE:va - BASE + len(old)].hex()} trouvé")
        writes.append({"off": va - BASE, "old": old.hex(), "new": new_.hex()})

    def moveq(va, old, new_, reg_byte):
        w(va, bytes([reg_byte, old]), bytes([reg_byte, new_]))

    stub = blobs[".stub"]
    w(gx.CAVE, b"\xff" * len(stub), stub)
    writes.append(sprites.redirect_write(gx.CAVE))
    w(gx.HOOK, bytes.fromhex(gx.HOOK_OLD), bytes.fromhex("4ef9") + g7.be32(gx.CAVE) + bytes.fromhex("4e71"))
    moved = {g7.DESC: DESCN, g7.DESC + 8: DESCN + 8, g7.DESC + 0x20: DESCN + 0x20, g7.ROWS: ROWSN, g7.CCROWS: CCROWSN,
             g7.NAMES: names_at, g7.UPDATE_TAB: upd_at, g7.RENDER_TAB: rnd_at, MAP: map_at}
    for old, new_ in moved.items():
        rs = g7.refs32(img, old)
        if len(rs) != {g7.DESC: 34, g7.DESC + 8: 1, g7.DESC + 0x20: 2, g7.ROWS: 5, g7.CCROWS: 2, MAP: 1}.get(old, 1):
            raise SystemExit(f"!! références à {old:#x} : {len(rs)}")
        for va in rs:
            if DISPATCH[0] <= va < DISPATCH[1]:
                continue                        # dans le code remplacé par le détour des voix muettes
            w(va, g7.be32(old), g7.be32(new_))
    w(DISPATCH[0], img[DISPATCH[0] - BASE:DISPATCH[0] - BASE + 6], bytes.fromhex("4ef9") + g7.be32(ssyms["dispatch"]))
    jumps = g7.JUMPS + g8.JUMPS8
    for va in g7.BOUNDS:
        if va in {j[0] for j in jumps}:
            continue
        b0, b1 = img[va - BASE], img[va - BASE + 1]
        if b0 & 0xf1 != 0x70 or b1 not in (75, 76):
            raise SystemExit(f"!! {va:#x}")
        moveq(va, b1, b1 + 5 * n, b0)
    top = 5 + n                                             # plus grand index de machine
    for va, reg in ((0x400a7dba, 0x72), (0x400a7df4, 0x70), (0x4005a6a6, 0x72), (0x400147a4, 0x70),
                    (0x400148aa, 0x72), (0x400148b2, 0x70), (0x400a25e0, 0x70)):
        moveq(va, 5, top, reg)
    moveq(0x4005a572, 5, 6, 0x72)                           # champ machine « propre à une machine » : <= 6
    w(0x4005a2b8, bytes.fromhex("487800c0"), bytes.fromhex("4878") + (32 * nm).to_bytes(2, "big"))
    if n > 1:
        moveq(0x400a26a2, 80, 80 - 7 * (n - 1), 0x78)       # 1er repère plus à gauche : les 6 + n repères tiennent
    moveq(0x400a26e8, 6, nm, 0x70)
    for va in (0x4001b69c, 0x400a40a6, 0x400a4fb0):
        moveq(va, 5, 1, 0x70)
    for va, old, sym in jumps:
        w(va, bytes.fromhex(old), bytes.fromhex("4ef9") + g7.be32(ssyms[sym]))
    for va, old, sym in g7.CALLS:
        w(va, bytes.fromhex(old), bytes.fromhex("4eb9") + g7.be32(ssyms[sym]) + bytes.fromhex("4e71"))
    # sonde du régulateur de charge autour de l'appel de la fonction audio (jsr abs.l)
    w(AUDIO_CALL, bytes.fromhex("4eb94005979e"), bytes.fromhex("4eb9") + g7.be32(ssyms["audio_probe"]))
    # tables d'ondes de CHORD : lues dans la charge utile, leur place en SRAM reçoit le code du Syntakt
    ptrs = [u32(CHORD_PTRS + 4 * i) for i in range(31)]
    w(CHORD_PTRS, b"".join(g7.be32(x) for x in ptrs), b"".join(g7.be32(chord_moved(x, lay)) for x in ptrs))
    writes.sort(key=lambda x: x["off"])
    for a_, b_ in zip(writes, writes[1:]):
        if a_["off"] + len(a_["new"]) // 2 > b_["off"]:
            raise SystemExit(f"!! écritures qui se chevauchent en {BASE + b_['off']:#x}")

    parts = [{"dest": f"{dst:#x}", "syntakt": [f"{lo:#x}", f"{hi:#x}"]} for lo, hi, dst in lay["copies"]]
    for lo, hi, dst in gx.ST_SRAM_INIT:
        parts.append({"dest": f"{gx.move(dst):#x}", "syntakt": [f"{lo:#x}", f"{hi:#x}"]})
    parts += [{"dest": f"{a:#x}", "hex": "4e71"} for a in lay["pads"]]
    for lo, hi in CHORD_BANKS:                  # tables d'ondes de CHORD, depuis le MAIN OS de l'utilisateur
        src = next(s_ + lo - d_ for s_, e_, d_ in CY_SRAM_INIT if d_ <= lo and hi <= d_ + e_ - s_)
        parts.append({"dest": f"{chord_moved(lo, lay):#x}", "cycles": [f"{src:#x}", f"{src + hi - lo:#x}"]})
    parts += [
        {"dest": f"{DST_BRIDGE:#x}", "hex": blobs[".bridge"].hex()},
        {"dest": f"{STUBS:#x}", "hex": stubs.hex()},
        {"dest": f"{DATA:#x}", "hex": bytes(data).hex()},
        {"dest": f"{DESCN:#x}", "cycles": [f"{g7.DESC:#x}", f"{g7.DESC + g7.NDESC * g7.DSTRIDE:#x}"]},
        {"dest": f"{DESCN + g7.NDESC * g7.DSTRIDE:#x}", "hex": bytes(new).hex()},
    ]
    reloc = [[f"{at:#x}", old.hex(), new_.hex()] for at, old, new_ in an["patches"]]
    alg_max = g7.DESC + g7.ALG_DESC * g7.DSTRIDE + 0x0c
    if u32(alg_max) != 5 << 8:
        raise SystemExit("!! max du paramètre Algorithm")
    reloc.append([f"{alg_max - g7.DESC + DESCN:#x}", gx.be32(5 << 8), gx.be32(top << 8)])
    tid = "syntakt-meter" if meter else subset_id(codes, generic)
    others = sorted(({"sdvintage-snare", "sdvintage-exact", "sdvintage-7th", "syntakt-vintage", "syntakt-meter"}
                     | {subset_id(c) for c in subsets()}) - {tid})
    return {
        "id": tid,
        "order": 90 if meter else 24,
        "name": ("DIAGNOSTIC, compteur de charge. " if meter else "") +
                "Vrais moteurs du Syntakt en machines ajoutées : " + ", ".join(f"{m['name']} ({m['label']})" for m in machines),
        "description": ([
            "FIRMWARE DE DIAGNOSTIC (notes/23, notes/27) : l'écran MACHINES affiche, pour chaque machine,",
            "« moyenne/voix » (charge moyenne, coût de la voix qui joue cette machine) ou « pic/moyenne » de la",
            "charge audio, en % de la durée d'un bloc de 32 échantillons, mis à jour toutes les 0,5 s.",
            "À n'utiliser que pour mesurer.",
        ] if meter else []) + [
            "Moteurs du Syntakt (OS 1.41) extraits AU BUILD de TON Syntakt_OS1.41.syx, en machines ajoutées après",
            "les 6 d'origine (notes/20) : " + ", ".join(f"{m['name']} = {m['label']} (machine {m['index'] + 1})" for m in machines) + ".",
            "Potards propres, noms et défauts du Syntakt. Généré par tools/gen_syntakt_engines.py.",
            "Demande build.py --syntakt Syntakt_OS1.41.syx. Aucun octet Elektron dans ce fichier.",
        ],
        "gov": {k: f"{syms[k]:#x}" for k in sorted(syms) if k.startswith("gov_") or k in ("audio_end", "voice_gate", "voice_after")},
        "device": "Model:Cycles",
        "os": "1.13",
        "section": 3,
        "conflicts": others,
        "writes": writes,
        "append": {
            "at": f"{BASE + gx.IMAGE_LEN:#x}",
            "dest": f"{gx.DST_CODE:#x}",
            "size": size,
            "syntakt": {"os": "1.41", "syx_sha256": syntakt.SYX_SHA256, "section": 7, "section_sha256": syntakt.DSP_SHA256},
            "parts": parts,
            "reloc": reloc,
        },
    }, ndesc


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="model-cycles_OS1.13.syx officiel")
    ap.add_argument("--syntakt", required=True, help="Syntakt_OS1.41.syx officiel")
    ap.add_argument("--engines", help="moteurs du catalogue, séparés par des virgules : " + ",".join(CATALOG))
    ap.add_argument("--all", action="store_true", help="toutes les combinaisons qui n'ont pas leur tweak d'origine")
    ap.add_argument("--generic", action="store_true", help="même pour une combinaison de LEGACY (vérification), avec --out")
    ap.add_argument("--out", help="fichier de sortie (sinon tweaks/…/24-<id>.json)")
    ap.add_argument("--check", action="store_true", help="vérifie que les JSON versionnés correspondent")
    ap.add_argument("--meter", action="store_true", help="firmware de diagnostic : compteur de charge (notes/23)")
    args = ap.parse_args()
    img = g7.cycles_main(args.cycles)
    if len(img) != gx.IMAGE_LEN:
        raise SystemExit("!! ce n'est pas le MAIN OS 1.13 officiel")
    if args.all:
        todo = [c for c in subsets() if tuple(c) not in LEGACY]
    else:
        want = args.engines.split(",")
        if set(want) - set(CATALOG):
            raise SystemExit(f"!! moteurs inconnus : {set(want) - set(CATALOG)}")
        todo = [[c for c in CATALOG if c in want]]
    st_img = syntakt.dsp_image(args.syntakt)
    bad = 0
    for codes in todo:
        if tuple(codes) in LEGACY and not args.generic and not args.meter:
            raise SystemExit(f"!! {codes} : tweak d'origine {LEGACY[tuple(codes)]} (ou --generic)")
        gen = generation(codes)
        if gen not in _ANALYSIS:
            an = analyse(st_img, gen)
            print(f"  Syntakt jusqu'à {CATALOG[gen[-1]]['label']} : {an['funcs']} fonctions, {an['code_bytes']} o de code,"
                  f" {len(an['blocks'])} blocs, {an['relocs']} relocalisations, {an['moved']} sauts recalculés")
        tweak, ndesc = build_tweak(img, st_img, codes, args.generic, args.meter)
        path = pathlib.Path(args.out) if args.out else DEV / f"{tweak['order']}-{tweak['id']}.json"
        text = json.dumps(tweak, indent=1) + "\n"
        print(f"  {tweak['id']} : {len(tweak['writes'])} écritures, {ndesc} descripteurs, charge utile {tweak['append']['size']} o")
        if args.check:
            ok = path.exists() and path.read_text(encoding="utf-8") == text
            print(f"    {path.name} {'est à jour' if ok else 'NE CORRESPOND PAS (autre GCC ?)'}")
            bad += not ok
        else:
            path.write_text(text, encoding="utf-8")
            print(f"    écrit : {path}")
    if bad:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
