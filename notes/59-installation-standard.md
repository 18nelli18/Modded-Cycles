# 59 — Installation standard par défaut, mode avancé pour choisir ses mods

Demande de Maxime (11/10/2026, fil du projet « Quelle direction prendre pour la modularité du projet ? ») : « que la
page du flasher soit par défaut une page qui flashe tous les mods que je propose d'un coup, donc ça paraît unifié, mais
un switch permet de passer en advanced mode pour choisir précisément ses mods ».
Fichiers : `tools/gen_flasher_tweaks.py` (`STANDARD`, `STANDARD_OUT`, `STANDARD_TESTED`, `check_standard`),
`tools/ref_mainos.py` (`standard_ids`, groupe « standard » de `REF_MAINOS`), `docs/flasher/` (`app.js`, `index.html`,
`style.css`). Preuves : `tools/emu/test_standard.py`, `tools/emu/test_mods_for_samples.py` (le paquet emballé pour un
Model:Samples), `tools/webflash_smoke.js` §1d et §6b. Pas de tweak, pas d'adresse : rien ne change dans les firmwares
eux-mêmes.

## En bref

- L'onglet Mods s'ouvre sur l'**installation standard** : les mods testés sur la machine qui vont tous ensemble, cochés
  d'office, dans un seul firmware. Rien à choisir : on charge son OS, on flashe. La page dit ce qu'il y a dedans, ce qui
  n'y est pas et pourquoi.
- Un interrupteur **Mode avancé** ouvre le choix mod par mod habituel ([notes 49](49-verification-mod-par-mod.md),
  PR #54), en partant des mods standard. L'éteindre revient au paquet standard en gardant le choix avancé de côté.
- Le paquet est **une seule liste**, `STANDARD` dans `tools/gen_flasher_tweaks.py`, que le générateur vérifie (§1). Un
  mod qui passe « tested » va soit dans `STANDARD`, soit dans `STANDARD_OUT` avec sa raison ; le générateur signale un
  mod testé et compatible rangé nulle part.
- Aujourd'hui 14 mods (§2), MAIN OS `ffe39899…` (§4). `[FAIT en émulation]` : chaque preuve de mod tourne avec les 13
  autres installés, le paquet s'emballe pour un Model:Samples, la page le construit et l'envoie octet pour octet.
  **Pas encore flashé tel quel sur la machine** : la page le marque « Testé en partie » tant que `STANDARD_TESTED` n'est
  pas exactement `STANDARD` (§5).

## 1. La règle du paquet

Une carte de `FEATURES` entre dans `STANDARD` si (vérifié par `check_standard()`, le générateur refuse sinon) :

1. elle est `"status": "tested"` (règle 3 de `AGENTS.md`) ;
2. elle ne demande pas d'autre fichier (`needs`) et n'est pas la carte des moteurs du Syntakt ;
3. aucune autre carte du paquet ne l'exclut ni ne l'inclut (`excludes`, `includes`), et la carte qu'elle demande
   (`requires`) est dans le paquet ;
4. elle ne change rien pour qui ne s'en sert pas. C'est le seul critère que le code ne vérifie pas : il range dans
   `STANDARD_OUT` les cartes testées et compatibles laissées dehors exprès, avec leur raison (`std_out` dans `FEAT`,
   `docs/flasher/app.js`, en + fr).

`ref_mainos.py` met la combinaison dans `REF_MAINOS` (groupe « standard », la page refuse un MAIN OS différent) et
`Cards.standard_sel()` refuse une liste que la page ne cocherait pas telle quelle (une carte qui en appellerait une
autre). `standard_tested` de `tweaks.js` est vrai seulement si `STANDARD_TESTED` (le paquet que Maxime a flashé en
entier) est exactement `STANDARD` : ajouter un mod au paquet le repasse en « Testé en partie ».

## 2. Ce qui est dedans, ce qui n'y est pas

Dans le paquet (ordre des cartes, qui est l'ordre du build) :

| Carte | Tweak | Testé sur la machine |
|---|---|---|
| Mute verrouillé, Écoute d'un pas, Noms qui défilent | `latching-mute`, `trig-preview`, `browser-scroll` | par drumkilla ([15 §1](15-demandes-reddit.md)) ; par Maxime à travers Model-TG, qui contient `trig-preview` et `browser-scroll` octet pour octet et une variante de `latching-mute` (5 octets diffèrent en `0x40148696` : trois NOP ici, un `jsr` vers sa propre fonction dans Model-TG, [31](31-model-tg.md)) |
| Effacer un trig | `trig-hold` | 03/10 ([33](33-effacer-un-trig.md)) |
| Arpégiateur | `arp` | 03/10 ([32](32-arpegiateur.md)) |
| Tempo jusqu'à 546 BPM | `tempo-max` | 04/10 ([38](38-tempo-546-bpm.md)) |
| Animation de démarrage | `boot-anim` | 05/10 ([39](39-animation-demarrage.md)) |
| Navigateur sur plusieurs lignes | `multiline-browser` | 10/10 ([40](40-navigateur-multiligne.md)) |
| Volume et pan en chiffres, Trigless trigs atténués | `level-pan-values`, `trigless-dim` | 07/10 avec Model-TG ([44](44-volume-pan-en-chiffres.md), [45](45-trigless-trigs-attenues.md)) |
| Basculer MIDI OUT + THRU en direct | `midi-live-both` | par AveyCole, sur sa version ([53 §9](53-midi-thru-aveycole.md)) |
| Machine MACRO | `macro` | 07/10 et 11/10 ([43](43-machine-macro.md), [55](55-macro-allegee-et-lofi.md)) |
| Chord Keys | `chord-keys` | 07/10 et 10/10 ([42](42-clavier-accords-diatoniques.md)) |
| Filtre par piste | `track-filter` | 11/10 ([47](47-filtre-piste.md)) |

Hors du paquet (la page affiche la raison et un bouton « Ajouter », qui ouvre le mode avancé avec ce mod coché) :

| Carte | Raison |
|---|---|
| Model-TG | encore « experimental » ; exclut Chord Keys et le filtre par piste |
| Moteurs du Syntakt | demandent le fichier d'OS du Syntakt ; testés seulement avec Model-TG (HW_TESTED vide sans lui) |
| Écoute des samples | demande Model-TG |
| Audio USB 6 canaux | `STANDARD_OUT` : remplace le mix stéréo USB par six canaux ; un membre de la communauté signale qu'un téléphone n'a plus de son USB |
| MIDI OUT pendant THRU | `STANDARD_OUT` : l'une des deux cartes MIDI qui s'excluent ; la bascule en direct garde le THRU d'origine tant qu'on ne la bascule pas |

Les noms, rubriques et raisons de la page sont tirés de ces listes et des règles des cartes (`stdWhy()` dans `app.js`) :
compléter `STANDARD` suffit, rien d'autre à réécrire dans la page.

## 3. La page

- **Par défaut** (`pick.mode = "standard"`) : `#std-pane` à la place du choix. Titre et étiquette (« Testé » ou « Testé
  en partie », §1), les mods par rubrique avec un lien vers leur section du guide (`GUIDE_OF`), « Bon à savoir » (les
  `note` des mods du paquet : charge de MACRO, numéro de machine…), « Hors de l'installation standard » (§2). Les
  `selection` des cartes sont celles du paquet (`selectStandard()`), donc le build, `REF_MAINOS`, l'étape 2 et le reste
  de la page marchent sans changement.
- **Mode avancé** (`#adv-switch`, `role="switch"`) : `#adv-pane`, le choix habituel, qui part des cartes du paquet.
  Revenir au standard met le choix avancé de côté (`pick.saved`) ; le rallumer le rend. « Ajouter » oublie le choix
  gardé et part du paquet plus ce mod (avec ses exclusions et l'Annuler habituel). La page retient le mode
  (`localStorage` `mc-mods-mode`), pas la sélection.
- **Le fichier** : `model-cycles_OS1.13_modded-standard-<version du flasher>.syx` quand la sélection est exactement le
  paquet (aussi en mode avancé), sinon le nom habituel avec la clé ; l'étape 2 et le résumé disent « Modded Cycles
  standard (14 mods) ».
- **Model:Samples** ([57](57-os-cycles-quelle-que-soit-la-machine.md)) : le choix de la machine reste au-dessus de
  l'interrupteur. Le paquet s'emballe comme n'importe quel build (`…_modded-standard-<version>_for-samples_smp-os.syx`,
  `_cyc-os`). Mais l'OS Cycles n'a de sampler qu'avec Model-TG, hors du paquet : sur un Model:Samples, le panneau le dit
  (`std_smp`, avec les cartes que Model-TG exclut) et propose « Ajouter Model-TG ».

## 4. Vérifications

| Vérification | Résultat (11/10/2026) |
|---|---|
| `gen_flasher_tweaks.py` (`check_standard`) | 14 cartes testées, aucune exclusion entre elles, pas d'avertissement |
| `ref_mainos.py` | groupe « standard » ajouté : 817 combinaisons, 145 mods ; MAIN OS du paquet `ffe398996b74a8d8d7960d2be259a1f86e6d9a4cada6b69014bec4e9b7d8117c` |
| `build.py` | 120 429 octets changés ; charge utile MACRO 324 576 o rangée en 104 728 o, copiée en `0x43000000` au démarrage ; `.syx` de 1 044 640 o |
| `test_standard.py` : chaque preuve avec les 13 autres (`--with`) | toutes OK (tableau ci-dessous) |
| `test_mods_for_samples.py` | le paquet emballé : l'OS Samples l'accepte, le bootstrap le pose sous `0x40200000`, l'OS installé accepte le retour et un autre `_cyc-os` ; `_smp-os` `e9dd7558…`, `_cyc-os` `0bceb38c…` |
| `webflash_smoke.js` §1d | vue par défaut, liste, raisons, interrupteur aller-retour, Ajouter, Model:Samples, FR |
| `webflash_smoke.js` §6b | avec l'OS officiel : construit sans rien cocher, empreinte de `REF_MAINOS`, nom du fichier, envoi rapide octet pour octet ; les deux emballages Model:Samples |

| Preuve (`--with` les 13 autres) | Contrôles | Durée |
|---|---|---|
| `test_trig_preview.py` | 12 ok | 1 s |
| `test_trig_hold.py` | 22 ok | 2 s |
| `test_arp.py` | 71 ok | 8 s |
| `test_tempo_max.py` (gagne `--with`) | 30 ok | < 1 min |
| `test_boot_anim.py` | 22 ok | 2 s |
| `test_multiline_browser.py` | 22 ok | 4 s |
| `test_level_pan.py` | 43 ok | 2 s |
| `test_trigless_dim.py` | 43 ok | 16 s |
| `test_midi_thru.py` | 49 ok | 4 s |
| `test_chord_keys.py` | tout ok | ~ 15 min |
| `test_chord_keys_release.py` | 41 ok | 1 s |
| `test_track_filter.py` | 62 ok | 25 min |
| `test_macro.py` (`--eurorack`) | voir §4.1 | ~ 1 h |

`latching-mute` et `browser-scroll` n'ont pas de preuve à eux (tweaks de drumkilla ; le second est octet pour octet
dans Model-TG, le premier y est en variante, tableau du §2) : `test_standard.py` le dit au lieu de les sauter en
silence, et refuse un mod du paquet qui n'a ni preuve (`PROOFS`) ni raison (`NO_PROOF`).

Deux corrections faites en route, qui ne changent aucun firmware :
- `test_chord_keys.py` posait dans le banc d'interface la charge utile **rangée** (compressée) de MACRO au lieu de celle
  copiée au démarrage : exception du CPU dès que MACRO était installée. Il prend maintenant `build.payload_runtime`,
  comme `test_track_filter.py`. Il ne compte plus comme chevauchement les tweaks qui demandent une carte que Chord Keys
  exclut (l'écoute des samples demande Model-TG) : ils ne sont jamais construits ensemble.
- `test_tempo_max.py` gagne `--with` (les bancs tournent sur l'OS avec les autres mods, avec et sans tempo-max).
- `test_macro.py` (section 5, MACRO avec d'autres mods) s'arrêtait sur une lecture hors mémoire dès que Chord Keys était
  installé : son getter lit ses réglages dans le BSS de l'OS, que le banc des voix ne pose pas
  ([55 §5](55-macro-allegee-et-lofi.md)). `Fw.engine()` pose maintenant ce BSS à zéro quand Chord Keys est là (Keys OFF sur les six pistes), comme
  `test_track_filter.py` et l'essai de [42 §17](42-clavier-accords-diatoniques.md).

Le test complet de la page (`webflash_smoke.js` avec les fichiers officiels du Model:Cycles, du Model:Samples et du
Syntakt, en 40 parts lancées deux par deux) : toutes les parts « ALL OK », les 817 combinaisons de `REF_MAINOS`
construites et conformes, le paquet standard compris.

### 4.1 MACRO avec le paquet

[À compléter avec le résultat de `test_macro.py --with …` (section 5 : MACRO avec les autres mods).]

## 5. Ce qui reste à vérifier sur la machine

`[À FAIRE]` Le paquet n'a jamais été flashé tel quel. Ce qu'on sait du matériel, mod par mod (relevé du 11/10/2026) :
aucun build sans Model-TG et sans les moteurs du Syntakt n'a été essayé avec plusieurs mods ; la MACRO seule (`macro`,
pas sa version avec les moteurs) n'a jamais été flashée avec un autre mod ; Chord Keys jamais avec MACRO, le filtre ou
les mods de djd_oz ; le filtre jamais avec MACRO ou Chord Keys ; `midi-live-both` n'a tourné que chez AveyCole, sur sa
version (code à une autre adresse). Points à essayer, par priorité :

1. **Projets** : la 7e machine du paquet est MACRO, la place du Sampler de Model-TG. Sur une copie d'un projet fait avec
   Model-TG et les moteurs, sélectionner les pistes Sampler et moteurs, appuyer sur MACHINES et tourner : pas de gel
   (une machine hors limites a gelé la machine le 30/09, [20 §5](20-moteurs-syntakt-a-cocher.md) ; le cas de MACRO n'est
   prouvé qu'en émulation, [43 §7](43-machine-macro.md)).
2. **Installation et secours** : animation à l'endroit, écran normal, FUNC à l'allumage ouvre toujours le STARTUP MENU,
   `CONFIG › UPGRADE` par USB avec l'OS officiel marche encore (règle 6).
3. **Charge** `[HYP]` : sans moteurs du Syntakt, pas de régulateur de charge. L'audio d'origine prend déjà environ 77 %
   d'un bloc ; une piste MACRO lourde (HARMONICS, WAVE MAP) ajoute environ 10 à 17 points, le filtre sur 6 pistes
   environ 5 %, 6 pistes Chord Keys en OPN3 environ 6 %, 16 trigless atténués environ 2 % (pris dans l'interruption des
   panneaux, niveau 6). Deux ou trois pistes MACRO lourdes avec les filtres modulés, une piste CHORD Keys ON et un arp
   vers 300 BPM : écouter s'il craque, regarder si l'écran rame. Chiffres d'émulation et de notes, jamais mesurés sur la
   machine.
4. **Gestes partagés** : FUNC + RETRIG sur une piste CHORD (Arp, Oct, Keys, Root, Scale, I–VII, 15 lignes) ; MACHINES +
   SWEEP sur une piste MACRO (filtre), relâcher rend les potards à MACRO ; FUNC + PITCH (RATE/BITS) ; trigs en mode
   grille sur une piste Keys ON (effacer, trigless atténué, écoute avec PAGE à l'arrêt) ; mute verrouillé puis TRIG et
   RETRIG ; volume et pan en chiffres sans écraser « Chord Voicing » ni les L/H du filtre ; bascule MIDI (THR, FUNC +
   appui sur LEVEL/DATA) avec un moniteur MIDI, et le MIDI OUT ordinaire (horloge et notes sur OUT) : la porte de
   `midi-live-both` est sur tous les chemins d'envoi MIDI ([53](53-midi-thru-aveycole.md)).
5. **Sauvegarde** : un projet avec arp, Chord Keys sur deux patterns, filtre et lo-fi de MACRO verrouillés, tempo 400 :
   éteindre, rallumer, tout revient.

Quand Maxime a essayé le paquet en entier : `STANDARD_TESTED = STANDARD` dans le générateur, `tweaks.js` regénéré, une
section « Testé sur la machine (JJ/MM/AAAA) » ici, la note de version.

## 6. Ajouter un mod au paquet

Quand un mod passe « tested » (PR #83, #78, #79, les moteurs de JM…) :

1. le mettre dans `STANDARD` s'il remplit le §1, sinon dans `STANDARD_OUT` avec `std_out` (en + fr) dans `FEAT` ;
2. `python3 tools/gen_flasher_tweaks.py`, puis `python3 tools/ref_mainos.py --cycles … --syntakt …` (la nouvelle clé du
   paquet entre dans `REF_MAINOS`) ;
3. sa preuve dans `PROOFS` de `tools/emu/test_standard.py`, puis `test_standard.py` et `test_mods_for_samples.py` ;
4. la note de version le nomme. **Une machine ajoutée change le numéro des machines ajoutées après elle** (MACRO vient
   en dernier) : le dire, car les projets enregistrés avec l'ancien paquet joueraient une autre machine.

Les PR ouvertes changeront le paquet ainsi : le filtre à la place de celui de Model-TG (#83) ne touche pas le paquet
tant que Model-TG reste hors du paquet ; ACID (#78) exclut MACRO et les moteurs du Syntakt, il irait donc dans
`STANDARD_OUT` ou à la place de MACRO, au choix de Maxime.
