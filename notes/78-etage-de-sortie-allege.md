# 78 — L'étage de sortie allégé : delay, reverb, Dist et envois sautés quand ils ne servent pas

Demande de Maxime (24/10/2026) : « commence par le point 1 puis enchaîne avec le chantier de l'étage de sortie en une
passe » (le point 1 : [74 §5.5](74-machine-modal.md) ; le chantier : notes/77 §6, point 2). Générateur
`tools/gen_out_sleep.py`, sources `tools/machines/out_sleep/`, tweak `71-out-sleep.json`, preuve
`tools/emu/test_out_sleep.py`.

## En bref

| | État |
|---|---|
| Ce que coûte l'étage de sortie | `[HYP]` modèle (notes/77) : 25 % d'un bloc après les voix ; la reverb 7,4 %, Volume + Dist 4,4 % ; Maxime mesure OUTPUT 20 % (§1) |
| D'abord : sauter ce qui ne sert pas | `[FAIT]` les raccourcis de l'étage de sortie de l'OS optimisé (notes/70), repris tels quels (§2) |
| Compatible avec l'OS | `[FAIT]` aucune écriture partagée, aucune référence dans les octets remplacés, masques libres (§3) |
| Son identique | `[FAIT en émulation]` dans l'OS complet, Model-TG et les machines ajoutées compris (§4) |
| Gain | `[HYP]` modèle : −11,2 points avec les réglages par défaut, −2,1 avec les effets en service ; le même code a donné −10 sur la machine avec l'OS d'origine (§5) |
| La passe unique | à faire : elle ne paie que quand les effets servent (§6) |

## 1. Où part le temps

Modèle du coût sur la machine (`tools/emu/hwcost.py`, notes/77), le projet du relevé de Maxime (MODAL, SNARE, METAL,
ACID, KICK, CPVtg), réglages par défaut, OS 2.1 avant ce travail :

| Poste | % d'un bloc | Instructions par bloc |
|---|---|---|
| Reverb `0x400579c4` | 7,4 | 8 214 |
| Volume + Dist `0x40056f58` | 4,4 | 6 071 (le saturateur calculé avec la Dist à 0) |
| Delay, par l'enveloppe de Model-TG `0x401b7198` | 2,8 | 2 791 |
| Mixeur, master, anneau du codec (`0x40056ea0`, `0x400567ba`, `0x400565c6`…) | 4,6 | |
| Effets master de Model-TG `0x401b4324`, après les voix `0x401b40f8` | 2,4 | |
| Envois delay `0x40056716` et reverb `0x40056698` | 1,8 | 2 360 |
| Pointeurs de la reverb `0x40057942`, divers | 1,6 | |
| **En tout** | **25,0** | |

- Maxime mesure OUTPUT 20 % (l'appel de `0x40059872`, sans Volume + Dist) : le modèle donne environ 19 % pour la même part.
- Comme l'étude du 18/10/2026 (tag `etude-optimisation-os-2026-10-18`, `etudes/optimisation-os/sortie/rapport.md`) :
  le coût ne dépend pas de ce qui joue ; avec les réglages par défaut, plus de la moitié ne sert à rien (delay et
  reverb sans entrée, saturateur avec la Dist à 0, envois à gain nul).
- La reverb d'Elektron est déjà de l'assembleur serré (MAC avec chargement à chaque échantillon) : la réécrire en une
  passe gagnerait peu à côté de la sauter quand elle n'a rien à faire.

## 2. Ce qui est fait : les raccourcis de l'OS optimisé

**Décision** : le chantier commence par les raccourcis exacts de l'étage de sortie de l'OS optimisé (notes/70, sur la
branche de la PR #98).
Ils ont été mesurés sur la machine le 18/10/2026 avec l'OS d'origine (son identique ; delay et reverb endormis
−7 points, saturateur −2, envois −1). L'OS optimisé n'allait pas avec l'OS actuel à cause de sa partie voix (mix2,
voix muettes, PUNCH), que Model-TG et nos machines remplacent ; sa partie sortie n'y touche pas.

| Raccourci | Source | Détour | Ce qu'il saute |
|---|---|---|---|
| Saturateur de Dist | `vd_skip.S`, masque `0x4016dab8` | `0x40057062` (8 o) | le saturateur d'une paire de pistes quand le wet de fin du bloc précédent est nul et VOL+DIST lissé <= 60 sur les deux |
| Envois | `send_skip.S`, masque `0x40170c48` | `0x40056716`, `0x40056698` (8 o) | les 32 trames quand `acc0`, les gains et les pentes sont nuls : 32 zéros écrits |
| Delay | `fx_dly.S`, `fx_lib.S`, masques `0x40189618`, `0x4016fae8` | `0x40057516` (6 o) | tout le delay quand tout ce qu'il lit est nul ; gains avancés de 32 pas exactement, attente de DONE du canal 30 |
| Reverb | `fx_rev.S`, masque `0x4018d918` | `0x40057ac8`, `0x40057dc6` (6 o) | le calcul du son quand l'entrée, les états et les 17 tampons de l'eDMA sont nuls ; la modulation reste celle de l'OS |

- Les 16 écritures sont celles de `70-os-optimise.json` (PR #98), **octet pour octet** : mêmes masques, mêmes
  adresses, mêmes sources (`tools/machines/os_optimise/` copié tel quel).
- Pas repris : la partie voix (mix2, voix muettes, PUNCH) ; les deux correctifs de gels D1 et D2 (une autre PR : un
  changement visible de plus).
- Limite connue (notes/70 §3) : une fois servis, le delay et la reverb ne se rendorment plus avant le prochain
  allumage, leurs restes ne revenant jamais exactement à zéro. Leur purge (non exacte, −111 dBFS) attend l'accord de
  Maxime.

## 3. Compatibilité avec le Modded Cycles OS

- `[FAIT]` Aucun tweak de `os.json` n'écrit aux six détours ; les cinq masques sont libres (`REGISTRY.md` §1).
- `[FAIT]` Aucune constante de 32 bits ne vise les octets remplacés, ni dans l'OS, ni dans le bloc de Model-TG, ni dans
  la charge utile (seulement l'OS d'origine y saute, par ses entrées et ses branchements relatifs).
- `[FAIT]` Model-TG appelle le delay (`jmp 0x40057488`) et la reverb (`jsr 0x400579c4`) d'origine depuis ses
  enveloppes : nos détours, à l'intérieur, servent aussi. Son propre sommeil des effets (après 16 384 blocs de silence
  total, rapport « sortie » de l'étude, §3.7) passe avant : il n'appelle plus rien.
- `check_overlaps.py` et `registry.py` : rien à signaler.

## 4. Preuve en émulation

`tools/emu/test_out_sleep.py` : l'OS de `os.json` sans `out-sleep` contre avec, côte à côte sur le banc de
l'interruption complète (`osbanc.py`), comparés à chaque bloc : anneau du codec, USB, sortie des 6 voix, SRAM entière
(sauf `0x8000bc98..0x8000bd98`, la sortie du saturateur non réécrite, lue × 0), EMAC ; lignes du delay et de la
reverb tous les 10 blocs.

`[FAIT en émulation]` le 24/10/2026, **TOUT OK**, 400 blocs par scénario, identique à chaque bloc :

| Scénario | Chemins courts pris (allégé) |
|---|---|
| defaut : les 6 machines d'origine, un trig tous les 40 blocs | delay et reverb endormis 400/400, saturateur 1 200 (3 paires × 400), envois 1 600 |
| projet : MODAL, SNARE, METAL, ACID, KICK, CPVtg | les mêmes |
| envois : delay 40 et reverb 40 sur les 6 pistes | delay et reverb endormis 3 blocs, jusqu'au 1er son ; envois jamais sautés |
| dist : VOL+DIST 100 / 80 | saturateur jamais sauté |
| glissements : potards tournés, Delay Time et Reverb Size changés | les raccourcis s'enclenchent et se relâchent (delay 100, reverb 200, saturateur 900) |
| machines : les 15 machines tour à tour, envois 30/30 sur une piste | delay 151, reverb 150, saturateur 1 200, envois 600 |

Et : 762 octets changés dans l'image, tous dans les 16 écritures ; `test_payload_pack.py` TOUT OK ; le firmware de
mesure se construit toujours dessus.

## 5. Gain

Modèle du coût sur la machine, le projet du §1, l'étage après les voix :

| Réglages | Avant | Après |
|---|---|---|
| Par défaut (envois à 0, VOL+DIST 60) | 25,1 % | 13,9 % (−11,2 points) |
| Envois delay et reverb à 40 | 25,1 % | 23,0 % (−2,1 : le saturateur) |

Avec l'OS d'origine, la machine a donné environ −10 points pour les mêmes raccourcis (notes/70 §4.2) : le modèle
compte un peu large pour les gros raccourcis (notes/70 §4.3).

## 6. La suite du chantier : une passe

- Quand les effets servent, l'étage reste à 23 % : reverb 7,4, delay 2,8, mixeur et master 4,6, Volume + Dist (la Dist
  qui distord) 4,4, effets master de Model-TG 2,4. C'est là que la réécriture en une passe paie (mélange, envois,
  master et anneau du codec dans la même boucle, moins de lignes de code relues) ; estimation −2 à −4 points, pour
  beaucoup de travail.
- Exact aussi, plus simple : la préparation de l'eDMA avant les voix (attente cachée, étude §5.4), la vérification
  réduite du sommeil de la reverb (étude §5.5).

## 7. Sur la machine (25/10/2026)

Firmware de la PR #112 (MAIN OS `84455c19…afd0` : MODAL et son sample excitateur, cet étage allégé, la sortie MIDI
sans gel). Maxime, juste après l'allumage, aucune note jouée : « Charge juste après l'allumage 19% CPU 26% PEAK, et
tout les track à 0% ».

- `[FAIT]` relevé sur la machine : CPU 19 %, PEAK 26 % sur la page System de Model-TG ; 0 % pour chaque piste.
- `[FAIT en émulation]` le modèle (`hwcost.py`, le projet du §1, aucune note, 60 blocs ; `build/idle_model.py`) hors
  voix : **30,4 % sans cet étage allégé, 19,1 % avec**. Le banc calcule six voix KICK muettes (38,5 %) que la machine
  ne montre pas (0 % par piste) : on compare hors voix. Le relevé tombe sur le modèle avec l'étage allégé.
- `[HYP]` le gain sur la machine à l'arrêt, envois à 0 : environ −11 points. Pas de relevé avant / après sur la
  machine : l'OS 2.1 sans cet étage (`e5a333c9…cf77`) donnerait environ 30 % au même endroit.
- `[À FAIRE]` le son identique, monter un envoi (pas de clic, la charge remonte et reste jusqu'au prochain
  allumage), VOL+DIST au-dessus de 60 et retour ; la charge en lecture avec le projet du §1.

## Chronologie

- 24/10/2026 : demande ; coût de l'étage mesuré au modèle ; raccourcis de l'OS optimisé repris, preuve.
- 25/10/2026 : premier relevé sur la machine, à l'allumage : 19 % (§7).
