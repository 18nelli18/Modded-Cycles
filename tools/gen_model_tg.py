#!/usr/bin/env python3
"""Génère tweaks/model-cycles_OS1.13/30-model-tg.json : Model-TG de TinyGregAudio (licence MIT), tel que son
propre build l'exporte pour ce flasher (docs/PAYLOAD.md de Model-TG), depuis un clone de son dépôt au commit
épinglé (MODEL_TG_COMMIT), avec une retouche de sa source (MC_PATCHES : les mutes tout de suite). Notes : notes/31.

Model-TG est un tweak « append » sans Syntakt : ses écritures sur le MAIN OS d'origine, et un seul morceau
ajouté après l'image (l'espace vide jusqu'à 0x401ab750 et son code, qui s'exécute en place, dans des blocs du
cache du système de fichiers). Il ne se combine pas avec les tweaks de drumkilla, qu'il contient déjà.

Deux tweaks :
  - 30-model-tg.json : Model-TG, construit par son build depuis une copie de sa source avec MC_PATCHES ;
  - 30-model-tg-st.json : la base de la version combinée avec les moteurs du Syntakt (notes/31), construite par son
    build depuis une copie de sa source avec MC_PATCHES et ST_PATCHES, et les adresses de ses symboles dont nos
    détours ont besoin (gen_syntakt_engines.py --tg). Le flasher ne la prend qu'avec un tweak syntakt-tg-….

    git clone https://github.com/TinyGregAudio/Model-TG vendor/Model-TG
    git -C vendor/Model-TG checkout <MODEL_TG_COMMIT>
    python3 tools/gen_model_tg.py --cycles model-cycles_OS1.13.syx --model-tg vendor/Model-TG [--check]

Son build.py (relu : il n'appelle que l'assembleur, l'éditeur de liens, git et l'outil de dépaquetage, et n'écrit
que dans son dossier build/) est lancé avec la section 3 dépaquetée ici et un outil de dépaquetage qui ne fait
rien : le .syx n'est pas reconstruit par lui. Il vérifie lui-même son image et la réécrit comme ce flasher.
"""
import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "emu"))

import build                       # noqa: E402
import gen_sdvintage_exact as gx   # noqa: E402
import gen_syntakt_engines as gs   # noqa: E402
import usb_steady                  # noqa: E402
import voice_loop                  # noqa: E402
import test_sdvintage as T         # noqa: E402

DEV = HERE.parent / "tweaks" / "model-cycles_OS1.13"
OUT = DEV / "30-model-tg.json"
OUT_ST = DEV / "30-model-tg-st.json"
LICENSE_OUT = DEV / "LICENSE-Model-TG"
MODEL_TG_REPO = "TinyGregAudio/Model-TG"
MODEL_TG_COMMIT = "70b39dd6787770ebefc7a2d78dea1678ec012679"     # 02/10/2026, v1.1.0 (slide trigs)
STOCK_SHA256 = "cc99d4f0175d34d1e91d046e6ec85a5e8ab58ab9edbb3c24406acd48cb99ee98"


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()


# --- retouches de sa source, (fichier, texte d'origine, nouveau texte, pourquoi) ---
# Dans les deux tweaks (demande de l'utilisateur, 03/10/2026, notes/31 §10) : en mode mute, tenu ou verrouillé, chaque
# touche de piste mute tout de suite, comme le tweak latching-mute de drumkilla seul. Model-TG met ces appuis en attente
# et les applique tous en quittant le mode : son mq_toggle, appelé à la place de 0x40013904 (kit, piste, 1) en
# 0x40023550, rejoint maintenant ce 0x40013904 d'origine. La file reste vide (mq_muted et mq_apply ne changent plus
# rien), et la retouche a la même taille (10 o) : aucune adresse de Model-TG ne bouge.
# Dans les deux aussi (04/10/2026, notes/34) : sa copie du tweak trig-preview de drumkilla (tweaks/, appliquée par son
# build) reçoit la même retouche que notre 02-trig-preview.json. L'écoute refusait le séquenceur en pause (0x4005481a
# vaut 2), où le met un Stop MIDI reçu, même à l'arrêt : PAGE tournait la page jusqu'au redémarrage. Elle ne refuse plus
# que la lecture (bit 0) : « tst.l d0 ; bne » devient « lsr.l #1,d0 ; bcs », même taille.
# Dans les deux tweaks (notes/35 §3) : avec l'audio USB multipiste, une piste mutée ou au volume 0 n'est plus coupée
# net sur sa piste USB. voice_quiet ne calculait plus une machine d'origine dès que les 6 gains du mixeur passaient sous
# -90 dB : inaudible dans le mix, mais les pistes USB sont prises avant le mixeur, donc coupées net, et la note figée
# repartait d'un coup au démute. Avec un mod multipiste (l'octet 0x40002ceb, MaxPacketLength du point d'accès IN, n'est
# plus le 0x38 d'origine), le test des gains est sauté : la piste s'arrête quand sa propre sortie se tait, comme sans
# mute. Sans mod multipiste, rien ne change. Même taille (5 branchements raccourcis compensent les 10 octets du test) :
# seul le label local vq_nop bouge, aucune autre adresse de Model-TG.
VQ_OLD = '''vq_env:
    tstl    %a0@(0x34)
    bnew    vq_trig
    tstl    %a0@(0x38)
    bnew    vq_trig
    tstl    %a0@(0x3c)
    beqs    vq_nop
    tstl    SND_KILL              | the other pulse, from All Sound Off (a
    beqw    vq_trig               | double stop, CC 120, a load) - every track
    lea.l   trig_seen,%a1         | gets it: an idle voice stays idle, a
    tstb    %a1@(0,%d1:l)         | sounding one renders it (not a new note)
    beqw    vq_yes
    bsr     vq_over
    tstl    %d0
    bnew    vq_yes
    braw    vq_no
vq_nop:
    lea.l   trig_seen,%a1         | never played since power-on: silent
    tstb    %a1@(0,%d1:l)
    beqw    vq_yes
    movel   %d2,%sp@-             | the mixer's gains for this track
'''
VQ_NEW = '''vq_env:
    tstl    %a0@(0x34)
    bnes    vq_trig
    tstl    %a0@(0x38)
    bnes    vq_trig
    tstl    %a0@(0x3c)
    beqs    vq_nop
    tstl    SND_KILL              | the other pulse, from All Sound Off (a
    beqs    vq_trig               | double stop, CC 120, a load) - every track
    lea.l   trig_seen,%a1         | gets it: an idle voice stays idle, a
    tstb    %a1@(0,%d1:l)         | sounding one renders it (not a new note)
    beqw    vq_yes
    bsr     vq_over
    tstl    %d0
    bnes    vq_yes
    bras    vq_no
vq_nop:
    lea.l   trig_seen,%a1         | never played since power-on: silent
    tstb    %a1@(0,%d1:l)
    beqw    vq_yes
    moveq   #0x38,%d0             | Modded-Cycles: with a multichannel USB mod (the IN
    cmpb    0x40002ceb,%d0        | dQH MaxPacketLength is no longer the stock 0x38) the
    bnes    vq_envf               | stems are taken before the mixer: never its gains
    movel   %d2,%sp@-             | the mixer's gains for this track
'''
# Dans les deux tweaks (notes/85) : la résonance ne fait plus baisser le volume, sur toutes les machines (le Sampler,
# ladder_run, et les machines d'origine, gflt_run). Le filtre en échelle à contre-réaction fb (Q12, k = fb/4096) a
# un gain de 1/(1+k) dans sa bande passante : 0,21 à fb = 15000. Model-TG n'en compensait que la moitié, à l'entrée
# (filt_mkt, jusqu'à 2,1x) : au-delà, x * makeup déborde 32 bits et le pic de résonance tape dans les bornes. La
# compensation passe à la sortie et devient entière : y4 * (1 + fb/4096), exacte (gain 1 en continu quelle que soit la
# résonance), et l'échelle elle-même tourne comme avec makeup = 1, donc tape moins dans ses bornes qu'avant. Le pic
# de résonance (jusqu'à ~14x la bande passante) est arrondi par mc_sat, un écrêtage doux quadratique (linéaire jusqu'à
# 0,75 de la pleine échelle, puis v - (v - 0,75)^2, qui rejoint la pleine échelle à pente nulle) au lieu de la borne
# dure. mc_sat prend la place de la table filt_mkt, devenue inutile (256 o) : chaque retouche garde sa taille
# (bourrage tpf hors de la boucle), aucun symbole de Model-TG ne bouge. Résonance 0 : boucles rapides inchangées
# (filt_mk / gflt_mk valent toujours 4096) ; filtre grand ouvert sans résonance : toujours contourné.
RES_PATCHES = (
    ("src/model_tg.s", '''    movel   %d0,%d4               | resonance makeup: the ladder's passband
    asrl    #7,%d4                | drops to 0.23x at full feedback, which is
    lea.l   filt_mkt,%a0          | why resonance sounds thin. Half-compensate
    mvzw    %a0@(0,%d4:l:2),%d4   | (to ~0.48x) - full compensation needs 4.4x
''', '''    movel   #4096,%d4             | Modded-Cycles: the resonance makeup is
    tpfl    #0                    | applied in full at the ladder's output
    tpf                           | now (sv_f4l, mc_sat); filt_mk stays 1.0,
                                  | which keeps the fast loop at Resonance 0
''', "filtre : makeup de résonance (sp_flt_go) : filt_mk reste 1,0, la compensation passe à la sortie"),
    ("src/model_tg.s", '''sv_flt:
    movel   %a1@,%d6              | x = buf >> 13, then resonance makeup
    asrl    #8,%d6
    asrl    #5,%d6
    mulsl   %a0@,%d6
    asrl    %d7,%d6
    movea.l %d6,%a2
''', '''sv_flt:
    movel   %a1@,%d6              | x = buf >> 13 (makeup: at the output)
    asrl    #8,%d6
    asrl    #5,%d6
    movea.l %d6,%a2
''', "filtre du Sampler : plus de makeup à l'entrée de l'échelle"),
    ("src/model_tg.s", '''    movel   %d5,%d6               | output = y4, at the buffer's full scale
    asrl    %d7,%d6
    cmpil   #131068,%d6
    bles    sv_flt_oh
    movel   #131068,%d6
sv_flt_oh:
    cmpil   #-131068,%d6
    bges    sv_flt_ol
    movel   #-131068,%d6
sv_flt_ol:
    asll    #8,%d6
    asll    #5,%d6
    movel   %d6,%a1@+
    movel   %d6,%a1@+
    cmpal   %a3,%a1
    bnew    sv_flt
lr_st:
''', '''    movel   %d5,%d6               | output = y4 * (1 + fb/4096): the full
    asrl    %d7,%d6               | makeup, the passband back at 1.0 (y4 is
    movea.l %d6,%a2               | within +-131072 and fb <= 15000: no
    mulsl   %d1,%d6               | overflow)
    asrl    %d7,%d6
    addl    %a2,%d6
    cmpil   #98304,%d6            | past 3/4 of full scale: the soft clip
    bgts    sv_flt_oh
    cmpil   #-98304,%d6
    bges    sv_flt_ol
sv_flt_oh:
    jsr     mc_sat                | (far: jsr abs.l)
sv_flt_ol:
    asll    #8,%d6
    asll    #5,%d6
    movel   %d6,%a1@+
    movel   %d6,%a1@+
    cmpal   %a3,%a1
    bnew    sv_flt
    tpf                           | (same size as before)
lr_st:
''', "filtre du Sampler : makeup entier à la sortie, y4 * (1 + fb/4096), et écrêtage doux (mc_sat)"),
    ("src/model_tg.s", '''gr2_loop:
    movel   %a1@,%d6              | x = s >> 14, then makeup (Q12)
    asrl    #8,%d6
    asrl    #6,%d6
    mulsl   %a0@,%d6
    asrl    %d7,%d6
    movea.l %d6,%a5
''', '''gr2_loop:
    movel   %a1@,%d6              | x = s >> 14 (makeup: at the output)
    asrl    #8,%d6
    asrl    #6,%d6
    movea.l %d6,%a5
''', "filtre des machines d'origine : plus de makeup à l'entrée de l'échelle"),
    ("src/model_tg.s", '''    movel   %d5,%d6               | output = y4
    asrl    %d7,%d6
    cmpil   #131068,%d6
    bles    gr2_oh
    movel   #131068,%d6
gr2_oh:
    cmpil   #-131068,%d6
    bges    gr2_ol
    movel   #-131068,%d6
gr2_ol:
    asll    #8,%d6
    asll    #6,%d6
    movel   %d6,%a1@+
    cmpal   %a2,%a1
    bnew    gr2_loop
gr2_st:
''', '''    movel   %d5,%d6               | output = y4 * (1 + fb/4096), as sv_f4l
    asrl    %d7,%d6
    movea.l %d6,%a5
    mulsl   %d1,%d6
    asrl    %d7,%d6
    addl    %a5,%d6
    cmpil   #98304,%d6
    bgts    gr2_oh
    cmpil   #-98304,%d6
    bges    gr2_ol
gr2_oh:
    bsrw    mc_sat                | (near: bsr.w, spelled out)
gr2_ol:
    asll    #8,%d6
    asll    #6,%d6
    movel   %d6,%a1@+
    cmpal   %a2,%a1
    bnew    gr2_loop
    tpfw    #0                    | (same size as before)
gr2_st:
''', "filtre des machines d'origine : makeup entier à la sortie et écrêtage doux (mc_sat)"),
    ("src/model_tg.s", '''    movel   %d0,%d4               | resonance makeup
    asrl    #7,%d4
    lea.l   filt_mkt,%a0
    mvzw    %a0@(0,%d4:l:2),%d4
    lea.l   gflt_mk,%a0
''', '''    movel   #4096,%d4             | resonance makeup: at the output now
    tpfl    #0
    lea.l   gflt_mk,%a0
''', "filtre des machines d'origine : gflt_mk reste 1,0 (gflt_coef)"),
    ("src/model_tg.s", '''filt_mkt:                         | feedback (>>7) -> makeup, half compensation
    .word 4096,4149,4201,4253,4305,4356,4407,4458
    .word 4509,4559,4609,4659,4709,4758,4806,4855
    .word 4903,4951,4998,5045,5092,5138,5185,5230
    .word 5276,5321,5366,5411,5455,5499,5543,5586
    .word 5629,5672,5715,5757,5799,5841,5883,5924
    .word 5965,6006,6047,6087,6127,6167,6207,6246
    .word 6286,6325,6363,6402,6440,6478,6516,6554
    .word 6592,6629,6666,6703,6740,6777,6813,6849
    .word 6885,6921,6957,6993,7028,7063,7098,7133
    .word 7168,7203,7237,7271,7305,7339,7373,7407
    .word 7440,7474,7507,7540,7573,7606,7639,7671
    .word 7704,7736,7768,7800,7832,7864,7896,7927
    .word 7958,7990,8021,8052,8083,8114,8145,8175
    .word 8206,8236,8266,8297,8327,8357,8387,8416
    .word 8446,8476,8505,8534,8564,8593,8598,8598
    .word 8598,8598,8598,8598,8598,8598,8598,8598
''', '''filt_mkt:                         | Modded-Cycles: the half-makeup table is
                                  | gone (full makeup, at the output); its
                                  | 256 bytes hold mc_sat
| mc_sat(d6): soft clip of the ladder's output, in its units (full scale
| 131072). Linear up to +-98304 (3/4), then v - (v - 98304)^2 / 131072, which
| meets full scale with a zero slope at +-163840; bounded at +-131068 (<< 14
| must fit). Keeps every register but d6; no flags are read after it.
mc_sat:
    tstl    %d6
    bpls    ms_pos
    negl    %d6
    bsrs    ms_pos
    negl    %d6
    rts
ms_pos:
    cmpil   #98304,%d6
    bles    ms_ret
    cmpil   #163840,%d6
    bges    ms_top
    movel   %d0,%sp@-
    movel   %d6,%d0
    subil   #98304,%d0
    asrl    #1,%d0
    mulsl   %d0,%d0               | ((v - T) / 2)^2 <= 2^30
    asrl    #8,%d0
    asrl    #7,%d0
    subl    %d0,%d6
    movel   %sp@+,%d0
    cmpil   #131068,%d6
    bles    ms_ret
ms_top:
    movel   #131068,%d6
ms_ret:
    rts
    .space  256 - (. - filt_mkt)
''', "filtre : mc_sat, l'écrêtage doux, à la place de la table filt_mkt (même taille)"),
)
MC_PATCHES = (
    ("src/model_tg.s", "mq_toggle:\n    movel   %sp@(8),%d0\n    cmpil   #MAX_TRK,%d0\n",
     "mq_toggle:\n    jmp     0x40013904            | Modded-Cycles: the stock toggle, at once\n    nop\n    nop\n",
     "mode mute : chaque touche de piste mute tout de suite (mq_toggle -> 0x40013904 d'origine), sans file d'attente"),
    ("tweaks/model-cycles_OS1.13/02-trig-preview.json", "4eb94005481a4a8066000138", "4eb94005481ae28865000138",
     "écoute d'un pas : aussi séquenceur en pause (un Stop MIDI le met en pause ; PAGE tournait la page), notes/34"),
    ("src/model_tg.s", VQ_OLD, VQ_NEW,
     "audio USB multipiste : une piste mutée ou au volume 0 n'est plus coupée net sur sa piste USB (voice_quiet)"),
)
MC_PATCHES += RES_PATCHES
# --- version combinée (notes/31 §4) ---
# Une seule : sa zone d'échantillons (0x4a800000..0x4e800000, vue sans cache des 64 Mo 0x42800000..0x46800000)
# s'arrête 1 Mo plus bas, pour nos moteurs du Syntakt (gen_syntakt_engines.PAY_TG = 0x46700000). Tout ce qu'il y
# range au sommet (cordes de Pluck, noms, historiques de retrig...) est défini depuis REGION_END et descend avec.
ST_PATCHES = (
    ("src/model_tg.s", "    REGION_END  = 0x4e800000\n", "    REGION_END  = 0x4e700000\n",
     "zone d'échantillons : 1 Mo de moins, laissé aux moteurs du Syntakt (0x46700000..0x46800000)"),
)
# Ses symboles dont nos détours ont besoin (gen_syntakt_engines.py --tg) : chaînage, page System, rééchantillonnage ;
# l'état de ses slide trigs (v1.1.0), que tools/emu/test_model_tg_syntakt.py arme comme le fait son séquenceur ; et sa
# file de mutes et son test des voix muettes (MC_PATCHES), que ce test vérifie
ST_SYMBOLS = ("blob_start", "reserved_end", "REGION_END", "param_table", "boot_extra_hook", "sampler_dispatch",
              "descr_hook", "descr_b_hook", "sampler_lfo_gate", "sampler_amp_gate", "sampler_name_table",
              "apply_names", "mod_held", "prof_t0", "prof_ta", "prof_trk", "rs_state", "rs_src", "sle_run", "sle_trk",
              "ah_noenv", "voice_ptr", "SLD_BASE", "sld_init", "blk_clk", "mq_toggle", "mq_pending", "mq_apply",
              "voice_quiet")
# Symboles dont l'écoute des samples a besoin (tools/gen_sample_preview.py, notes/46), dans les deux tweaks : son code
# appelle ces fonctions et lit ces variables de Model-TG, aux mêmes adresses dans les deux builds.
PV_SYMBOLS = ("tok_of", "sound_obj", "ensure_loaded", "slot_hash", "pd_mode", "ld_busy", "pad_load_hook")
# Symboles du filtre en échelle que tools/emu/test_model_tg_res.py appelle directement (notes/85) : ils n'ont pas bougé
# avec RES_PATCHES, la preuve s'en sert aussi sur le tweak d'avant.
FLT_SYMBOLS = ("ladder_run", "filt_coef", "filt_fbmax", "filt_mkt", "filt_mk", "filt_y1", "gflt_run", "gflt_f",
               "gflt_q", "gflt_mk", "gflt_y1", "voice_ptr", "mc_sat")


def export(cycles, repo, patches=()):
    """Tweak exporté par le build de Model-TG (dictionnaire), et ses symboles. Avec des retouches, le build se fait
    sur une copie de sa source (le clone reste propre)."""
    head = git(repo, "rev-parse", "HEAD")
    if head != MODEL_TG_COMMIT:
        raise SystemExit(f"!! {repo} est au commit {head[:7]}, attendu {MODEL_TG_COMMIT[:7]} (git checkout {MODEL_TG_COMMIT})")
    if git(repo, "status", "--porcelain"):
        raise SystemExit(f"!! {repo} a des modifications locales : il faut un clone propre")
    if patches:
        with tempfile.TemporaryDirectory() as d:
            work = pathlib.Path(d) / "Model-TG"
            shutil.copytree(repo, work, ignore=shutil.ignore_patterns(".git", "build"))
            for f, old, new, _ in patches:
                text = (work / f).read_text(encoding="utf-8")
                if text.count(old) != 1:
                    raise SystemExit(f"!! retouche introuvable dans {f} : {old.strip()}")
                (work / f).write_text(text.replace(old, new), encoding="utf-8")
            tw, stock, log, syms = export_build(cycles, work)
        tw["version"] = git(repo, "describe", "--tags", "--always")
        return tw, stock, log, syms
    return export_build(cycles, repo)


def export_build(cycles, repo):
    stock = T.main_os_from_syx(cycles)
    if build.sha(stock) != STOCK_SHA256:
        raise SystemExit("!! ce n'est pas le MAIN OS 1.13 officiel")
    work = repo / "build"
    (work / "stock").mkdir(parents=True, exist_ok=True)
    (work / "stock" / "section_3_MAIN_OS.bin").write_bytes(stock)
    dummy = work / "_unused.syx"
    dummy.write_bytes(b"")                        # son build calcule l'empreinte du .syx qu'il aurait reconstruit
    out = work / "model-tg-modded-cycles.json"
    true = shutil.which("true") or "/usr/bin/true"
    env = {"CROSS": gx.CROSS, "PATH": os.environ["PATH"]}
    r = subprocess.run([sys.executable, "build.py", "--stock", str(cycles), "--tool", true, "--out", str(dummy),
                        "--modded-cycles", str(out)], cwd=repo, env=env, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit("!! build de Model-TG :\n" + r.stdout[-2000:] + r.stderr[-2000:])
    tw = json.loads(out.read_text(encoding="utf-8"))
    syms = {}
    for line in gx.run([gx.CROSS + "nm", str(work / "_b.elf")]).splitlines():
        p_ = line.split()
        if len(p_) == 3:
            syms[p_[2]] = int(p_[0], 16)
    return tw, stock, r.stdout, syms


def adapt_st(tw, stock, syms):
    """La base de la version combinée (30-model-tg-st.json)."""
    out = adapt(tw, stock, syms)
    others = sorted(set(out["conflicts"]) - {"model-tg-st"} | {"model-tg"})
    missing = [n for n in ST_SYMBOLS if n not in syms]
    if missing:
        raise SystemExit(f"!! symboles absents du build de Model-TG : {missing}")
    if syms["REGION_END"] != gs.PAY_TG + 0x08000000 or syms["reserved_end"] != BASE + len(stock) + tw["append"]["size"]:
        raise SystemExit("!! zone d'échantillons ou fin du bloc de Model-TG inattendues")
    out.update({
        "id": "model-tg-st",
        "name": "Model-TG (TinyGregAudio), base de la version avec les moteurs du Syntakt",
        "description": [
            f"Model-TG de TinyGregAudio, https://github.com/{MODEL_TG_REPO} (licence MIT, texte dans",
            "LICENSE-Model-TG), commit " + MODEL_TG_COMMIT[:7] + ", construit par son propre build depuis une copie de",
            "sa source avec ces retouches (tools/gen_model_tg.py, MC_PATCHES et ST_PATCHES) :",
            *[f"  - {f} : {why}" for f, _, _, why in MC_PATCHES + ST_PATCHES],
            "Plus l'envoi à l'USB à heure fixe de ce dépôt (tools/usb_steady.py, notes/35), comme 6ch-usbup,",
            "et la division des pistes par 2 plus courte de la boucle des voix (tools/voice_loop.py, notes/36).",
            "Base de la version combinée Model-TG + moteurs du Syntakt (notes/31) : ne s'installe qu'avec un tweak",
            "syntakt-tg-…, qui s'ajoute après lui et chaîne ses détours.",
        ],
        "conflicts": others,
        "symbols": {n: f"{syms[n]:#x}" for n in ST_SYMBOLS + tuple(n for n in PV_SYMBOLS if n not in ST_SYMBOLS)},
    })
    return out


def adapt(tw, stock, syms):
    """Format et métadonnées de ce dépôt ; vérifie que le tweak redonne l'image exportée."""
    missing = [n for n in PV_SYMBOLS + FLT_SYMBOLS if n not in syms]
    if missing:
        raise SystemExit(f"!! symboles absents du build de Model-TG : {missing}")
    patched, _ = build.apply_writes(stock, [tw])
    payload, _ = build.build_payload([tw], stock, None)
    if build.sha(bytes(patched) + payload) != tw["result_sha256"]:
        raise SystemExit("!! le tweak exporté ne redonne pas l'empreinte annoncée par Model-TG")
    if BASE + len(stock) + tw["append"]["size"] > 0x40200000:
        raise SystemExit("!! OS agrandi au-delà de la zone de travail du bootstrap (0x40200000)")
    others = sorted(set(tw["conflicts"]) | {gs.subset_id(c) for c in gs.subsets()}
                    | {"sdvintage-snare", "sdvintage-exact", "sdvintage-7th", "syntakt-vintage", "syntakt-meter", "model-tg-st"})
    # Envoi à l'USB à heure fixe (notes/35) : la charge de Model-TG varie beaucoup (pistes au repos, mutes, effets
    # éteints) et l'OS envoie chaque bloc à l'USB juste après l'avoir calculé. Mêmes écritures que 6ch-usbup.
    # Et la division des pistes par 2 plus courte de la boucle des voix (notes/36), comme 6ch-usbup.
    steady = usb_steady.writes() + voice_loop.writes()
    taken = [(w["off"], w["off"] + len(w["new"]) // 2) for w in tw["writes"]]
    for w in steady:
        a, b = w["off"], w["off"] + len(w["new"]) // 2
        if any(a < y and x < b for x, y in taken):
            raise SystemExit(f"!! envoi à heure fixe, boucle des voix : 0x{a + BASE:08x} déjà écrit par Model-TG")
    writes = sorted(tw["writes"] + steady, key=lambda w: w["off"])
    return {
        "id": "model-tg",
        "order": 30,
        "name": "Model-TG (TinyGregAudio) : machine Sampler, rééchantillonnage, retrig et effets master",
        "description": [
            f"Model-TG de TinyGregAudio, https://github.com/{MODEL_TG_REPO} (licence MIT, texte dans",
            "LICENSE-Model-TG), commit " + MODEL_TG_COMMIT[:7] + ", construit par son propre build pour ce flasher, depuis",
            "une copie de sa source avec cette retouche (tools/gen_model_tg.py, MC_PATCHES) :",
            *[f"  - {f} : {why}" for f, _, _, why in MC_PATCHES],
            "Machine Sampler (7e machine), rééchantillonnage, retrig et effets master, Attack / Filtre / Résonance sur",
            "les machines d'origine, slide trigs (v1.1.0), Scale Lock, envoi d'échantillons par Elektron Transfer, page",
            "System, et moins de charge processeur. Contient déjà les tweaks de drumkilla (mute verrouillé modifié,",
            "écoute d'un pas, défilement des noms). Avec les moteurs du Syntakt, le flasher prend model-tg-st (notes/31).",
            "Plus l'envoi à l'USB à heure fixe de ce dépôt (tools/usb_steady.py, notes/35), comme 6ch-usbup,",
            "et la division des pistes par 2 plus courte de la boucle des voix (tools/voice_loop.py, notes/36).",
            "Généré par tools/gen_model_tg.py. Aucun octet Elektron dans le code de Model-TG.",
        ],
        "version": tw["version"],
        "source": f"https://github.com/{MODEL_TG_REPO}/tree/{MODEL_TG_COMMIT}",
        "result_sha256": tw["result_sha256"],
        "device": tw["device"],
        "os": tw["os"],
        "section": tw["section"],
        "conflicts": others,
        "writes": writes,
        "append": tw["append"],
        "symbols": {n: f"{syms[n]:#x}" for n in PV_SYMBOLS + FLT_SYMBOLS},
    }


BASE = gx.BASE


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="model-cycles_OS1.13.syx officiel")
    ap.add_argument("--model-tg", required=True, help=f"clone de {MODEL_TG_REPO} au commit {MODEL_TG_COMMIT[:7]}")
    ap.add_argument("--check", action="store_true", help="vérifie que le JSON versionné correspond")
    args = ap.parse_args()
    repo = pathlib.Path(args.model_tg).resolve()
    cycles = pathlib.Path(args.cycles).resolve()
    lic = (repo / "LICENSE").read_text(encoding="utf-8")
    bad = 0
    for path, patches in ((OUT, MC_PATCHES), (OUT_ST, MC_PATCHES + ST_PATCHES)):
        tw, stock, log, syms = export(cycles, repo, patches)
        print("\n".join("  " + x.strip() for x in log.splitlines() if "MAIN OS sha256" in x or "one blob" in x
                        or "Modded-Cycles tweak" in x))
        out = adapt_st(tw, stock, syms) if path == OUT_ST else adapt(tw, stock, syms)
        text = json.dumps(out, indent=1) + "\n"
        if args.check:
            ok = path.exists() and path.read_text(encoding="utf-8") == text
            print(f"  {path.name} {'est à jour' if ok else 'NE CORRESPOND PAS (autre version des binutils ?)'}")
            bad += not ok
            continue
        path.write_text(text, encoding="utf-8")
        print(f"  écrit : {path.relative_to(HERE.parent)} ({len(out['writes'])} écritures, {out['append']['size']} o "
              f"ajoutés, MAIN OS {out['result_sha256'][:8]}…)")
    if args.check:
        ok = LICENSE_OUT.read_text(encoding="utf-8") == lic
        print(f"  {LICENSE_OUT.name} {'est à jour' if ok else 'NE CORRESPOND PAS'}")
        raise SystemExit(0 if ok and not bad else 1)
    LICENSE_OUT.write_text(lic, encoding="utf-8")
    print(f"  écrit : {LICENSE_OUT.name}")


if __name__ == "__main__":
    main()
