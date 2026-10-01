# 28 · Le code du Syntakt en SRAM, à la place des tables d'ondes de CHORD

Travail du 01/10/2026, piste 3.3 de [27](27-cinq-et-six-voix.md), après les relevés de l'utilisateur avec le firmware de diagnostic v6.

## 0. En bref

| | État |
|---|---|
| Relevés v6 sur la machine | `[FAIT]` chaque voix du Syntakt ajoutée coûte 9 à 13 points de moyenne ; l'interface reste fluide jusqu'aux coupures (§1) |
| Tables d'ondes de CHORD dans la charge utile | `[FAIT]` (§2) |
| Code du Syntakt et 3 de ses tables en SRAM interne | `[FAIT]` (§2) |
| Régulateur : coupures au-dessus de 86 % de moyenne (au lieu de 82 %) | `[FAIT]` dans tous les firmwares (§2) |
| Preuve en émulation | `[FAIT]` (§3) |
| Gain estimé | boucle des voix d'environ 63,5 à 52 % du bloc avec 5 moteurs différents (§4) |
| Mesure sur la machine | `[FAIT]` diagnostic v7 : chaque voix du Syntakt coûte autant qu'une voix d'origine ([29 §1](29-voix-syntakt-en-sram.md)) |

## 1. Relevés du diagnostic v6 (01/10/2026)

Retour de l'utilisateur, « moyenne/voix » lu sur l'écran MACHINES, en % de la durée d'un bloc :

| Pistes qui jouent | Relevé |
|---|---|
| SDVtg | 42/10 |
| SDVtg + KICK | 53/8 |
| SDVtg + CPVtg | 54/11 |
| + une 3ᵉ machine ajoutée | 63/11 |
| + SYToy (4 machines ajoutées) | 76/7 |
| + SYBit (5ᵉ) | coupures de fins de notes ; « l'interface reste fluide » |

- La 3ᵉ machine ajoutée est appelée « la perc » dans le retour. C'est sans doute SYSwm, la seule restante, ou une machine affichée avec l'image de PERC. À confirmer.
- Le 2ᵉ chiffre est le coût de la voix de la machine affichée (piste lue non précisée).
- **Ce qu'on en tire** :
  - Chaque voix du Syntakt ajoutée fait monter la moyenne de 9 à 13 points, plus que son propre coût (7 à 11 %).
    - Exemple : SYToy coûte 7 % mais ajoute 13 points.
    - Le reste est l'effet sur les autres voix : avec un moteur de plus, le code de chacun est chassé du cache d'instructions (8 Ko) avant le bloc suivant ([27 §2](27-cinq-et-six-voix.md)).
  - Une voix du Syntakt seule coûte autant qu'une voix d'origine : SDVtg + CPVtg (54) ≈ SDVtg + KICK (53).
  - **L'interface reste fluide** à la charge où le régulateur coupe : le seuil de charge moyenne peut monter (§2).

## 2. Ce qui change

**Tables d'ondes de CHORD** ([27 §3.3](27-cinq-et-six-voix.md)) :
- **`[FAIT]`** Les 30 tables de 1 028 o, en SRAM `0x80001c5c..0x800074b4` (22) et `0x8000cac0..0x8000eae0` (8), sont recopiées dans la charge utile, au build, depuis le MAIN OS de l'utilisateur.
  - Source : parties « cycles » du tweak, depuis le contenu de démarrage de la SRAM (`0x4019b590..`).
- **`[FAIT]`** On ne peut pas simplement viser ce contenu de démarrage dans l'image : **l'OS réutilise cette zone comme BSS** juste après l'avoir recopiée en SRAM (remise à zéro à partir de `0x4019b590`, `0x400004ba`).
- Les 31 pointeurs de la table `0x40118594..0x4011860c` sont réécrits vers ces copies. CHORD lit désormais ses tables en SDRAM : son son ne change pas, chaque voix CHORD coûte un peu plus.

**Code du Syntakt en SRAM** :
- La 1ʳᵉ zone libérée (22 616 o) reçoit, dans l'ordre :
  - les **fonctions atteintes du Syntakt**, tassées en blocs (13 810 o en 18 blocs pour les 5 moteurs) ;
  - **3 tables** lues à chaque bloc, chacune avec 16 o de garde de part et d'autre : les deux tables de SD VINTAGE (`0x8000a080..0x8000a888`) et la forme d'onde de SY SWARM (`0x80006f84..0x80007788`, l'une des 10 de SY BITS).
- La charge utile les contient en transit (`0x43000000..`). Le crochet de démarrage (`stub.S`) les recopie en SRAM, juste après la charge utile.
  - L'OS a déjà initialisé sa SRAM : il appelle `0x4000045c` en `0x4000052c`, puis la remise à zéro du BSS en `0x40000530`, où est notre crochet.
  - Une première version faisait cette copie au 1ᵉʳ trig d'une machine ajoutée, en plein bloc audio : environ 22 Ko lus en SDRAM, de quoi faire déborder ce bloc.
- **`[FAIT]`** La SRAM exécute du code : le bootstrap s'y exécute ([27 §3.3](27-cinq-et-six-voix.md)).
- **Générateur** (`layout()`, `code_patches()` de `gen_syntakt_engines.py`) :
  - les adresses absolues du code visent les adresses d'exécution en SRAM (relocalisation, comme avant) ;
  - les sauts relatifs au PC sont recalculés s'ils changent de bloc. Aucun ne change : le Syntakt appelle ses fonctions par adresse absolue (`jsr`) ;
  - toutes les corrections sont des remplacements de 4 o vérifiés : le flasher web n'a pas eu besoin de changer.
- La 2ᵉ zone libérée (`0x8000cac0..0x8000eae0`, 8 224 o) restait libre ; elle reçoit ensuite des états de voix ([29](29-voix-syntakt-en-sram.md)).

**Régulateur** :
- Coupures au-dessus de **86 %** de charge moyenne, jusqu'à revenir à 82 % (82 / 78 avant), dans tous les firmwares.
- Les protections contre les blocs isolés (90 %, 92 %) ne changent pas.

**Taille** : la charge utile passe de 238 080 à 269 056 o pour les 5 moteurs. L'OS agrandi finit à `0x401ebc40`, sous la zone de travail du bootstrap (`0x40200000`).

## 3. Preuve en émulation

**Nouveau test** `tools/emu/test_sram_code.py` :
- **Statique** :
  - la table de pointeurs `0x40118590` n'est lue que par `0x400a806c` (update de CHORD) ;
  - l'adresse d'une de ces 30 tables n'apparaît nulle part ailleurs dans l'OS, sauf un nombre dans une table numérique décroissante (`0x4010b2c8`) ;
  - dans le tweak, les 31 pointeurs visent des copies identiques au contenu de démarrage de la SRAM.
- **Émulation** : 3 pistes CHORD (réglages aléatoires, SHAPE et COLOR changés en cours de note), avec 3 pistes de machines du Syntakt déclenchées à partir du bloc 30 :
  - les sorties CHORD sont **identiques à l'OS d'origine**, avant comme après le 1ᵉʳ déclenchement du Syntakt ;
  - tout le code du Syntakt s'exécute en SRAM, rien dans la zone de transit ;
  - aucune machine d'origine ne touche l'ancienne place des tables.
- Avec 6 machines, aucune machine d'origine (CHORD compris) ne lit ces zones, sur 40 configurations aléatoires (script de travail).

**Crochet de démarrage** (`boot_hook_ok()` de `test_sdvintage_exact.py`, appelé par `test_syntakt_machines.py`) : le vrai code de remise à zéro du BSS, avec la SRAM telle que l'OS vient de l'initialiser.
- La charge utile est recopiée intacte, le BSS est remis à zéro, et la fonction revient normalement.
- Le code et les tables du Syntakt sont en `0x80001c5c` (22 616 o), et **le reste de la SRAM est intact**.
- Avec un ancien tweak (`syntakt-vintage`), la SRAM n'est pas touchée du tout.

**Tests existants**, sur les 31 tweaks régénérés : tout passe.
- `test_syntakt_machines.py`, sur SD, CP, SY TOY, SY BITS, SY SWARM, SD + CP, SD + CP + SY TOY, SY TOY + SY SWARM et les 5 moteurs : 26 à 30 vérifications.
  - Les 5 moteurs restent identiques au Syntakt (écart max 1 LSB), avec leur code en SRAM.
  - Le vrai décompresseur du bootstrap relit l'OS agrandi à l'identique.
- `test_sram_code.py` : sur les 5 moteurs (12 vérifications) et sur `syntakt-sd` (6).
- `test_sram_scratch.py`, `test_idle.py`, `test_governor.py` (TARGET 82 %), `test_meter.py`.
- Flasher web : les 511 combinaisons donnent les empreintes de référence (`webflash_smoke.sh`, ALL OK, 588 vérifications).
- Les anciens tweaks (`sdvintage-exact`, `sdvintage-7th`, `syntakt-vintage`) sont identiques à l'octet près.

## 4. Gain attendu

Simulation de cache de [27 §2](27-cinq-et-six-voix.md) : lignes de SDRAM par bloc et part de la boucle des voix, avant (diagnostic v5/v6) et après.

| Pistes 1 à 6 | Données | Code | Boucle des voix, modèle |
|---|---|---|---|
| 6 machines d'origine | 130 → 198 | 377 → 378 | 45,5 → 46,1 % |
| SDVtg, CPVtg, SYToy, SYBit, SYSwm, SNARE | 769 → 421 | **936 → 5** | 63,5 → 51,9 % |
| SDVtg, CPVtg, SYToy, SYBit, SYSwm, SDVtg | 833 → 415 | 645 → 0 | 62,3 → 52,8 % |

- Source : `cachesim.py`, `groups.py`, `groups2.py` (scripts de travail).
- Avec SDVtg, CPVtg, SYSwm, SYToy, KICK et CHORD : 54,1 % après (388 lignes de données, 153 de code).
- Le code du Syntakt ne passe plus par le cache d'instructions, et ne chasse plus le code des autres voix ni des effets.
- **Inconnue** : la SRAM sert à la fois le code et les données des voix du Syntakt (tampons, tables). Le modèle compte ces accès comme gratuits, mais la machine pourrait faire attendre l'un pour l'autre. Seule la mesure le dira.
- **Prix** : environ +0,6 point par voix CHORD (ses 2 tables lues en SDRAM).

## 5. Firmware de diagnostic v7 `[FAIT]`

Construit localement :
- `build/diag/model-cycles_OS1.13_diagnostic-charge_v7.syx` (MAIN OS `2574e1ec…`) ;
- `…_v7_6ch.syx` avec l'audio USB 6 canaux (MAIN OS `d0f139ce…`).

C'est la v6 (affichage « moyenne/voix », seuil de 86 %), plus le code du Syntakt en SRAM.

À relever, sur les mêmes motifs qu'au §1 :
- la suite SDVtg → + CPVtg → + 3ᵉ → + SYToy → + SYBit, puis une 6ᵉ voix ;
- y a-t-il encore des coupures, à partir de combien de voix ;
- un motif avec CHORD (son inchangé ? coût ?).

Relevés v7 et suite : [29](29-voix-syntakt-en-sram.md).
