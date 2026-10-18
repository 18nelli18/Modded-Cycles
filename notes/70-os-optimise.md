# 70 — OS optimisé : moins de charge, son identique, deux gels corrigés

Demande de Maxime (17/10/2026) : « y'a forcément un travail d'organisation lourd et efficace qui permettrait
d'économiser et d'améliorer la stabilité, même dans l'optimisation de l'OS natif. Creuse cette partie-là. » Quatre
études en parallèle (voix, sortie, système, stabilité) sur le vrai code de l'OS 1.13, dans une session cloud ; leurs
rapports, prototypes, bancs et journaux sont archivés tels quels sous le tag git `etude-optimisation-os-2026-10-18`
(dossier `etudes/optimisation-os/`, non fusionné). Deux fichiers d'essai ont été flashés par Maxime le 18/10/2026
(§4). Tweak `tweaks/model-cycles_OS1.13/70-os-optimise.json`, générateur `tools/gen_os_optimise.py`, sources
`tools/machines/os_optimise/`, preuve `tools/emu/test_os_optimise.py` (banc `tools/emu/outrig.py`, gels
`tools/emu/gels_checks.py`). Adresses : VA de l'OS 1.13.

## En bref

- **L'OS d'origine fait tout le travail tout le temps.** À l'arrêt, il calcule six voix de silence, un delay et une
  reverb qui ne reçoivent rien, un saturateur de Dist à 0 et des envois à gain nul : 72 % de chaque bloc audio
  (0,67 ms) mesurés sur la machine, à l'arrêt.
- **Le mod saute ce qui ne peut rien changer au son**, en six raccourcis exacts (§2), et corrige deux gels de l'OS
  d'Elektron (§5). Mesuré sur la machine (§4) : charge moyenne **72 → 20 % à l'arrêt, 77 → 65 % en lecture**,
  77 → 67 % avec la Dist à fond, 77 → 73 % avec le delay et la reverb en service. Son identique (Maxime, 18/10/2026).
- **Exact** : sortie identique à l'échantillon près, prouvée en émulation contre l'OS d'origine, sauf une voix
  arrêtée qui sort 0 au lieu de moins de -108 dB.
- **Limites** : une fois servis, le delay et la reverb ne se rendorment plus avant le prochain allumage (leurs restes
  ne sont jamais exactement nuls, §3) ; pas avec Model-TG, MACRO, ACID ni les moteurs du Syntakt (§6).
- **Le modèle de cache des notes 27-28 surestime les gains** : environ 80-85 % de ses prévisions pour les gros
  raccourcis, environ 50 % pour les petits (§4.3).

## 1. Où part le temps (OS d'origine, 6 pistes qui jouent, réglages par défaut)

`[FAIT en émulation]`, modèle de cache des notes 27-28 (rapports « voix », « sortie », « système » de l'étude) :

| Poste | % d'un bloc | Remarque |
|---|---|---|
| Boucle des voix `0x400a7d4a` | ~52 | les 6 voix calculées à chaque bloc, même muettes, même jamais déclenchées |
| Étage de sortie (`0x40056f58` Volume + Dist, `0x400567ba` mixeur, envois, delay, reverb, master, codec) | 28,7 | **constant** : même coût en silence, avec 1 ou 6 pistes, avec ou sans effets |
| Début d'interruption, séquenceur, lissage, LFO | ~3 | séquenceur 0,4 % à vide, 3,4 à 6 % au pire |
| Interruptions qui coupent l'audio (panneau 12 kHz, USB, DMA) | 1 à 1,5 | peu à gagner |

Le code d'un bloc (17,4 Ko) ne tient pas dans le cache d'instructions (8 Ko) : presque chaque ligne est relue en
SDRAM à chaque bloc, et le code de l'interface est chassé du cache à chaque bloc `[DÉDUIT]`.

## 2. Les six raccourcis

| Raccourci | Source | Accroche | Ce qu'il saute | Pourquoi c'est exact |
|---|---|---|---|---|
| Saturateur de Dist | `vd_skip.S`, masque `0x4016dab8` | détour `0x40057062` (8 o) | le saturateur d'une paire de pistes quand le wet est nul au bloc précédent (`0x40a78c2c + 8p`, `+4`) et VOL+DIST lissé <= 60 (15 360 en 8.8) sur les deux pistes : saut au calcul dry/wet `0x40057100` | le fondu `0x400571c4` multiplie la sortie du saturateur par un wet nul aux deux bouts ; les tampons `0x8000bc98..0x8000bd98`, lus seulement par ce fondu (× 0), gardent leur ancien contenu |
| Envois | `send_skip.S`, masque `0x40170c48` | détours `0x40056716` (6 entrées, delay) et `0x40056698` (7 entrées, reverb) | les 32 trames quand `acc0`, les gains et les pentes sont nuls : 32 zéros écrits | `acc0 -= Σ g·x` avec tout à zéro : sorties nulles, gains inchangés |
| Delay | `fx_dly.S` (+ `fx_lib.S`, masques `0x40189618`, `0x4016fae8`) | détour `0x40057516` | tout le delay quand `acc1..acc3`, l'état du filtre `0x8000b8dc`, l'entrée et les deux prises lues par l'eDMA sont nuls : sortie et temporaire à zéro, gains `0x8000a100` avancés de 32 pas exactement (`x += (cible − x) & ~31`), MACSR = 0xa0, attente de DONE du canal 30 (au plus 4 096 lectures) | calcul linéaire, MAC fractionnaires sans terme constant : tout ce qu'il lit est nul, tout ce qu'il écrit l'est |
| Reverb | `fx_rev.S`, masque `0x4018d918` | détours `0x40057ac8` (R1) et `0x40057dc6` (R2) | le calcul du son quand l'entrée, les états (`a2d0`, `a47c`, `a4c8`) et les 17 tampons de l'eDMA sont nuls (683 mots) ; la modulation `0x40057d72` reste celle de l'OS | idem ; les lignes continuent d'avancer comme dans l'OS d'origine, le réveil reprend exactement où il serait |
| mix2 | `mix2.S`, en place `0x400a98c4..0x400a9904` (64 o) | réécriture en place | la 1ʳᵉ boucle de `0x400a9884`, dont la sortie est entièrement réécrite par la 2ᵉ ; reste son effet sur les gains (`g += pas << 5`) et `acc0` vidé | mêmes valeurs modulo 2^32 |
| PUNCH | `punch.S`, masque `0x40186238` | détour `0x400a9714` | PUNCH éteint (pas d5 = 0, d6 = 0x20000000) : 5 instructions par échantillon au lieu de 13 (`y = c × x`, MAC avec chargement) | le gain « × 4 saturé » vaut exactement 1 ; 1ᵉʳ échantillon par les instructions d'origine |
| Voix muettes | `idle_stock.S`, masque `0x40185f48` | détours `0x400a7dfe` (avant update/render) et `0x400a7e24` (après render) | une voix sans trig (+0x34, +0x38) dont la sortie divisée par 2 reste dans [-4 096, 4 096[ pendant 64 blocs (43 ms) : sortie à zéro, +0x38 = +0x34, suite en `0x400a7e38` ; un trig la relance | **non exact** : 0 au lieu de moins de 2^13 avant division (-108 dB) ; au retrig, écart <= 2·10⁻⁶ de la crête (-114 dB) |

Coût quand le raccourci ne sert pas (effets en service, Dist qui distord) : quelques dizaines d'instructions par bloc
(0,02 % d'un bloc pour la Dist, au plus ~0,1 % pour les effets ; rapport « sortie » de l'étude, §4).

## 3. Écartés ou reportés

| Piste | Gain (modèle) | Pourquoi pas ici |
|---|---|---|
| Purge des restes du delay et de la reverb : leurs restes (≤ 24 pas de 24 bits au codec, -111 dBFS) remis à 0 pour qu'ils se rendorment après usage | -8 points 1 à 3 s après la fin de l'entrée ; mesuré : 7 points (§4.2) | pas exacte à l'octet ; **prévue après cette version** (choix de Maxime, 18/10/2026) |
| SRAM réorganisée : les 30 Ko de tables de CHORD en SDRAM, le code chaud de l'OS à leur place | -5 à -9 points, tout le temps | le plus gros travail ; incompatible avec les moteurs du Syntakt, qui occupent déjà cette SRAM |
| Lissage des paramètres sauté à son point fixe | jusqu'à -1,5 | conçu, pas prototypé |
| Opérateur `0x400a8204` réécrit | -0,8 | chiffré seulement |
| Moitié du cache verrouillée | -1,7 à -4,6 | l'interface perdrait la moitié des caches ; à mesurer |
| Horloge SPI de l'écran doublée | interface seulement | vitesse maximale de l'écran inconnue |

Écartées : aligner ou réordonner le code (le cache manque de place, ce n'est pas un conflit), descendre le panneau
sous le niveau de l'audio (scintillement des LED), regrouper l'USB, recopier des tables en SRAM (≤ 0,13 %).

## 4. Testé sur la machine (18/10/2026)

### 4.1 Les fichiers d'essai

Deux firmwares construits par `tools/build.py` depuis l'officiel, flashés l'un après l'autre par Maxime avec le même
projet : `essai-reference` (OS 1.13 officiel + un compteur de charge dans l'écran MACHINES : pic/moyenne/libre en %
d'un bloc, sur 0,5 s) et `essai-optimise` (le même compteur + D1, D2 et les six raccourcis). Les 27 écritures de
`70-os-optimise.json` sont celles des tweaks d'essai, **octet pour octet** (mêmes masques, mêmes adresses), sans le
compteur. Projet : 6 pistes aux machines par défaut, un trig sur les 16 pas des 6 pistes, 120 BPM, envois à 0,
VOL+DIST à 60.

### 4.2 Mesures (pic/moyenne/libre)

| Situation | Référence | Optimisé | Moyenne |
|---|---|---|---|
| À l'arrêt | 79/72/0 | 27/20/0 | **-52** |
| 6 pistes en lecture | 87/77/0 | 74/65/0 | **-12** |
| Dist à fond sur les 6 pistes | 86/77/0 | 77/67/0 | -10 |
| Delay et reverb à fond sur les 6 pistes | 87/77/0 | 82/73/0 | -4 |
| Envois remis à 0 (effets déjà servis), en lecture | 86/77/0 | 80/72/0 | -5 |

Son identique avec les deux fichiers (Maxime, en lecture). Ce que rapporte chaque raccourci, déduit des écarts (à ±1
point, la résolution de l'écran) : sommeil du delay et de la reverb **7 points** (72 contre 65), saturateur de Dist
**2 points** (67 contre 65), envois **~1 point** (73 contre 72), mix2 + PUNCH **~2 points** (77 − 73 − 2) ; l'arrêt
des voix muettes fait l'essentiel des 52 points à l'arrêt.

### 4.3 Le modèle face à la machine

| Situation | Écart prévu (modèle) | Mesuré | Rapport |
|---|---|---|---|
| À l'arrêt | -62 | -52 | 84 % |
| 6 pistes | -18 | -12 | 67 % |
| Dist à fond | -14 | -10 | 71 % |
| Delay et reverb en service | -7 | -4 | 57 % |
| Sommeil des effets seul | -8 à -9 | -7 | ~82 % |

Comme à la note 28 (-11,5 prévus, environ -8 mesurés) : compter **80-85 % des gains annoncés pour les gros
raccourcis** (une fonction entière sautée), **environ 50 % pour les petits**. Le modèle donne aussi la référence un
peu haut en lecture (79-82 prévus, 77 mesurés). Les pics mesurés dépassent la moyenne de 7 à 10 points (blocs des
trigs), plus que le modèle (3 à 4).

### 4.4 « libre » toujours à 0

Le temps libre de l'interface est resté à 0 partout, même à 20 % de charge : cette partie du compteur ne marche pas sur
la machine. `[HYP]` La boucle comptait les écarts de moins de 128 coups du minuteur DMA 0 (0,95 µs) entre deux
lectures, seuil marqué `[HYP]` dans l'étude : un tour de boucle sur la machine (lecture d'un registre de périphérique)
le dépasse sans doute, et rien n'est jamais compté. Sans effet sur le mod, qui ne contient pas le compteur ; à revoir
pour mesurer l'interface.

## 5. Les deux gels corrigés

**D1 — MACHINES gèle sur une machine inconnue** `[FAIT]` (constaté par Maxime le 12/10/2026). Un projet fait avec
MACRO, ACID ou les moteurs du Syntakt, rouvert sous un firmware qui n'a pas cette machine : la piste garde un numéro de
machine hors de 0..5. Les accesseurs des enregistrements par machine `0x4004df5c` (n, 0..6) et `0x4004df76` (machine
m, 0..5) rendent alors l'entrée -1 : `0x40a714f4`, 76 o **avant** le tableau `0x40a71540` (`moveq #-1` en
`0x4004df66` et `0x4004df80`). L'écran MACHINES (`0x400148dc`, appelée pour chaque piste par `0x400a2404`) suit les
pointeurs de ces 76 o. Correctif : `moveq #-1` → `moveq #6` (CHORD) aux deux adresses (4 octets). Prouvé : accesseurs,
écran MACHINES, potards de l'écran principal (`0x4001e814`), molette et vrai changement de machine (`0x400a2712`,
`0x40014072`) ; machines 0..5 identiques à l'origine. Corrige aussi ce que disait notes/18 §9 (« aucun plantage
attendu »). Model-TG a la même copie du défaut (`0x401bf7e2`, `0x401bf806`, `0x401bf81c`), à corriger avec sa
version.

**D2 — l'horloge MIDI sortante fige tout après une longue surcharge** `[FAIT]`. L'interruption du top d'horloge
`0x4005420c` (corps à IPL 7) envoie 0xF8 par `0x40001232` ; quand un message part par le DMA (`0x4049dca0` non nul),
l'octet va dans l'anneau de 1 Kio `*0x4049dcac`, et s'il est plein, `0x4000123a..0x40001246` attend qu'une
interruption de niveau 4 le vide, impossible à IPL 7 : gel complet, son compris, après 1 024 tops sans service
(4,7 s à 546 BPM, 21 s à 120 BPM). Correctif : `bgt.s 0x4000123a` → `bgt.s 0x400012c6` (sortie), 2 octets en
`0x40001246` : l'octet d'horloge est perdu. Prouvé : 1 024 premiers tops identiques à l'origine, le 1 025ᵉ revient.

Autres défauts relevés par l'étude, non corrigés ici : D3 (un bloc au-dessus de 100 % est perdu sans trace, l'heure
musicale et l'USB restent en retard d'un bloc ; avec l'audio USB 6 canaux, flux abîmé jusqu'à son redémarrage), D4
(piles : la plus petite fait 2 Kio, globales du noyau juste en dessous), D5 (carte SD/eMMC : erreurs ni activées ni
traitées). Pas de chien de garde dans l'OS, et il vaut mieux ne pas en ajouter (un redémarrage perdrait l'état non
sauvegardé).

## 6. Compatibilité

- **Pas avec Model-TG, MACRO, ACID ni les moteurs du Syntakt** (et SD VINTAGE en ligne de commande) : ils détournent la
  même boucle des voix (`0x400a7dfe`, `0x400a7e24`), Model-TG réécrit aussi mix2, et tous ont déjà leur arrêt des voix
  muettes (notes/23). Le générateur déclare ces conflits d'après le dossier des tweaks ; la carte du flasher les
  exclut. Une version pour ces familles (Dist, envois, effets, PUNCH, D1, D2 seulement) viendra ensuite.
- **Avec tous les autres mods** : aucune écriture partagée (`check_overlaps.py`), et prouvé en émulation avec eux (§8).
- **Place** : sept masques de sprites libérés (1 036 o), pris le 18/10/2026. Des PR ouvertes les réclamaient aussi :
  Chord Keys v2 (#87, les sept), LFO maintenu et sauvé (#93), le fork d'AveyCole (#75), Chord Keys de Nico (#46). Choix
  de Maxime (18/10/2026) : l'OS optimisé garde ses masques, aux adresses testées ; ces PR prendront d'autres masques à
  leur mise à jour.

## 7. Le tweak

`70-os-optimise.json`, 27 écritures : D1 (2 × 2 o), D2 (2 o), mix2 en place (64 o), 10 détours, sept masques et leurs
redirections (`sprites.redirect_write`). Masques : `0x4016dab8` (64/192 o), `0x4016fae8` (70/192), `0x40170c48`
(134/192), `0x40185f48` (204/272), `0x40186238` (88/272), `0x40189618` (220/272), `0x4018d918` (256/328). Assemblé
par `as` + `ld` + `objcopy` (binutils seulement) : les binutils `m68k-linux-gnu-` de l'étude et `m68k-elf-` 2.47
(Homebrew) donnent les mêmes octets.
`symbols` : les adresses des chemins courts et de `QUIET` (compteurs des voix), pour la preuve.

## 8. Preuve en émulation

`tools/emu/outrig.py` est le premier banc qui fait tourner l'étage de sortie : la vraie interruption audio (comme
`seqrig.py`) **avec** Volume + Dist, le mixeur, les envois, le delay, la reverb, le master et l'anneau du codec ; la
DDR vue avec et sans cache, l'eDMA simulé (TCD en MMIO, chaînes exécutées dès qu'elles démarrent), le kit par défaut chargé par
l'OS. `tools/emu/test_os_optimise.py` compare « base » (OS d'origine + les mods de `--with`) et « optimisé », bloc par
bloc : anneau du codec, USB, 6 voix, SRAM entière (sauf `0x8000bc98..0x8000bd98`), EMAC, lignes du delay et de la
reverb à chaque bloc ; toute la mémoire tous les 10 blocs.

`[FAIT en émulation]`, le 18/10/2026 (Mac, binutils `m68k-elf-` 2.47) : seul (56 contrôles), avec 14 mods dont
track-filter et chord-keys (62), avec 14 mods dont lfo-plus (56) — `6ch-usbup, latching-mute, trig-preview,
browser-scroll, trig-hold, arp, tempo-max, boot-anim, multiline-browser, level-pan-values, trigless-dim`, `midi-both`
ou `midi-live-both`, `chord-keys`, et `track-filter` ou `lfo-plus`. **Tout OK, mêmes résultats dans les trois cas**,
et les mêmes que les journaux de l'étude (même banc, porté).

| Cas | Ce qui est montré | Chemins courts pris (optimisé) |
|---|---|---|
| écritures | octets d'origine ; 10 détours vers le bon symbole ; 1 125 octets changés, tous dans les écritures du tweak | — |
| D1 | accesseurs, écran MACHINES, potards, molette : 0..5 identiques ; hors limites, l'origine lit avant le tableau, le corrigé rend CHORD | — |
| D2 | 1 024 tops identiques ; l'origine reste à IPL 7 au 1 025ᵉ, le corrigé revient (1 026 tops) | — |
| defaut, 400 blocs, 18 trigs | identique à chaque bloc | saturateur 1 200 (3 paires × 400), delay et reverb 400, envois 1 600, PUNCH 2 400 |
| envois 40/40 | identique ; delay et reverb endormis seulement avant le 1ᵉʳ son (3 blocs) | saturateur 1 200, envois 0 |
| dist 100/80 | identique ; saturateur jamais sauté | saturateur 0 |
| glissements (potards, 60 trigs) | identique, raccourcis qui s'enclenchent et se relâchent | saturateur 900, delay 100, reverb 200, envois 600 |
| filtre (track-filter en marche, L24, réso 80, envois 30/30) | identique | saturateur 1 200 |
| arret, 800 blocs | codec, USB, voix et lignes identiques et exactement nuls ; les 6 voix arrêtées | tout, PUNCH 384 |
| silence, 1 950 blocs (DECAY 20, trigs aux blocs 100 et 1 750) | voix arrêtées aux blocs 240 à 1 626 ; 0 là où la base sort au plus 1 903 (-115,0 dB) ; au retrig, écart <= 1,95·10⁻⁶ de la crête (-114,2 dB) ; codec et USB à -116,2 et -116,7 dBFS de la base au plus | — |

Durée : 2 à 3 min par scénario de 400 blocs, 10 min pour « silence » ; preuve complète en 25 à 30 min par
combinaison. La preuve du filtre par piste (`test_track_filter.py`, comparée à un modèle en flottant) passe aussi
avec `m68k-elf-objdump` dans `emac.py`.

## 9. Reste à faire

- `[À FAIRE]` Test par Maxime du firmware du flasher : OS optimisé seul, puis avec ses mods habituels.
- `[À FAIRE]` Purge des restes du delay et de la reverb (§3), pour qu'ils se rendorment après usage.
- `[À FAIRE]` Version pour Model-TG, les moteurs du Syntakt, MACRO et ACID.
- `[À FAIRE]` D3 (bloc au-dessus de 100 %), D4 (budget de pile par mod), le temps libre de l'interface (§4.4).
