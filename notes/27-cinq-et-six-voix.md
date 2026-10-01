# 27 · Tenir 5 et 6 voix du Syntakt

Travail du 01/10/2026. Retour de l'utilisateur sur le firmware de diagnostic v5 ([26 §8](26-sram-empruntee.md)) : 4 voix du Syntakt sur tous les pas de la mesure sans note coupée, mais des notes coupées dès la 5ᵉ. « J'aimerais que tu cherches comment on pourrait résoudre ça. »

## 0. En bref

| | État |
|---|---|
| Pourquoi les notes sont coupées | `[FAIT]` le régulateur coupe dès que la charge moyenne dépasse 82 % ; avec des notes sur chaque pas, la plus faible est coupée à chaque pas (§1) |
| Où passe le temps d'une voix du Syntakt | `[FAIT]` en émulation : le **code** (cache d'instructions de 8 Ko) est maintenant le premier poste (§2) |
| Coût réel de chaque voix sur la machine | `[FAIT]` relevés du diagnostic v6 ([28 §1](28-code-syntakt-en-sram.md)) |
| Régulateur moins pressé sur la charge moyenne | `[FAIT]` interface fluide à 86 % : adopté ([28 §2](28-code-syntakt-en-sram.md)) |
| Code du Syntakt en SRAM, à la place des tables d'ondes de CHORD | `[FAIT]` en émulation ([28](28-code-syntakt-en-sram.md)) |

## 1. Pourquoi les notes sont coupées à partir de 5 voix

- Le régulateur ([25](25-regulateur-de-charge.md)) éteint des voix dès que la **charge moyenne** dépasse 82 % (`STEAL`), jusqu'à revenir à 78 % (`TARGET`).
- Avec des notes sur chaque pas, la voix éteinte repart au trig suivant, la charge remonte, et elle est éteinte de nouveau 16 blocs (11 ms) plus tard : **une note coupée à chaque pas**.
- **Ordre de grandeur** :
  - mesures de [23 §6 bis](23-optimisation-charge.md) : mixage et effets ≈ 30 % du bloc, voix d'origine ≈ 8 % ;
  - 4 voix du Syntakt passent sous 82 %, 5 non : une voix du Syntakt coûte donc entre 10,4 et 12,75 % (30 + 4 S < 82 ≤ 30 + 5 S) ;
  - **6 voix du Syntakt qui sonnent en continu demandent environ 92 à 106 %** : impossible sans les rendre nettement moins chères, ou sans réduire le mixage et les effets.
- Le Cycles d'origine est lui-même à 77 % de moyenne avec ses 6 voix ([23 §6 bis](23-optimisation-charge.md)).

## 2. Où passe le temps d'une voix du Syntakt (émulation, après [26](26-sram-empruntee.md))

**Instructions par bloc**, en régime établi (`UC_HOOK_CODE`, 6 pistes déclenchées au bloc 1) :

| Voix | Moteur | Passerelle (C) | Détours (asm) |
|---|---|---|---|
| SNARE (d'origine) | 7 145 | 309 | 30 |
| SYToy | 6 613 | 446 | 30 |
| SYBit | 7 221 | 449 | 30 |
| SDVtg | 8 025 | 437 | 30 |
| CPVtg | 8 384 | 436 | 30 |
| SYSwm | 10 389 | 447 | 30 |

- La passerelle coûte environ 140 instructions de plus par voix du Syntakt que pour une voix d'origine : peu.

**Lignes de 16 o lues en SDRAM par voix et par bloc** (même mesure) :

| Voix | Code | Données (dont écrites) |
|---|---|---|
| SNARE | 223 | 72 (39) |
| SYToy | 227 | 83 (45) |
| SYBit | 232 | 132 (35) |
| SYSwm | 212 | 207 (64) |
| SDVtg | 279 | 148 (53) |
| CPVtg | 346 | 104 (68) |

- Source : `UC_HOOK_CODE` et `UC_HOOK_MEM_*` sur le bloc 10 ; registre du minuteur exclu. Code : moteur, passerelle (61 lignes par voix du Syntakt, 26 par voix d'origine) et détours.
- Le code de chaque moteur du Syntakt pèse comme celui d'une machine d'origine. Mais le **cache d'instructions ne fait que 8 Ko** ([26 §1](26-sram-empruntee.md)) : avec 5 moteurs différents, chacun relit tout son code à chaque bloc.
- Les données restantes : l'état de la voix (1 800 o, comme les 796 o d'une voix d'origine) et les tables qui ne sont pas dans le Cycles (formes d'onde de SY BITS et SY SWARM, table de 2 Ko de SD VINTAGE en `0x8000a080`).

**Simulation de cache** (8 Ko + 8 Ko, lignes de 16 o, 4 voies, LRU ; boucle des voix seule) :
- Modèle de temps : 1,54 cycle par instruction et 15 cycles par ligne transférée, à 250 MHz.
- Étalonnage :
  - 6 voix d'origine, 47 % du bloc mesurés sur la machine ;
  - SDVtg à la place d'une voix d'origine, +7 points mesurés ([23 §6 bis](23-optimisation-charge.md)).
- C'est un ordre de grandeur, pas une mesure : le mixage, les effets et l'interface ne sont pas simulés.

| Pistes 1 à 6 | Lignes de code lues | Lignes de données (lues + écrites) | Boucle des voix, modèle |
|---|---|---|---|
| 6 machines d'origine | 377 | 130 | 45,5 % |
| SDVtg, CPVtg, SYToy, SYBit, SYSwm, SNARE | **936** | 769 | 63,5 % |
| 5 × SDVtg, SNARE | 219 | 328 | 52,5 % |
| 5 × SYSwm, SNARE | 168 | 556 | 65,1 % (SY SWARM fait 10 400 instructions) |
| SYSwm, SDVtg, SYSwm, SDVtg, SYSwm, SNARE | 515 | 657 | 64,8 % |
| SYSwm × 3, SDVtg × 2, SNARE | 426 | 642 | 63,8 % |

- Source : `cachesim.py` et `groups.py` (scripts de travail, non versionnés), sur le tweak à 5 moteurs.
- **Avec des moteurs différents, le code devient le premier poste** : 936 lignes par bloc, contre 377 pour le Cycles d'origine.
- **Le même moteur sur plusieurs pistes coûte beaucoup moins**, surtout sur des pistes voisines : son code reste dans le cache d'une voix à la suivante.

## 3. Pistes

### 3.1 Régulateur moins pressé sur la charge moyenne `[À FAIRE]` (essai dans le diagnostic v6)

- Une charge moyenne élevée ne fait pas craquer le son : elle laisse moins de temps à l'interface. Ce sont les **blocs isolés** au-dessus d'environ 92 % qui font craquer ([25 §5](25-regulateur-de-charge.md)), et ceux-là restent surveillés (`PEAK` 90 %, `SEVERE` 92 %).
- Essai : couper seulement au-dessus de **86 %** de moyenne, jusqu'à revenir à 82 %, au lieu de 82 / 78.
  - Avec 5 voix du Syntakt (≈ 82 à 94 % d'après le §1), une partie des coupures devrait disparaître, au prix d'une interface un peu plus lente.
  - À juger sur la machine : l'utilisateur avait trouvé l'interface lente vers 89 % ([23 §6 bis](23-optimisation-charge.md)).

### 3.2 Le même moteur sur des pistes voisines (sans rien changer)

- D'après le modèle, 5 × SDVtg coûte environ 11 points de moins que 5 moteurs différents.
- À vérifier sur la machine avec le diagnostic v6.

### 3.3 Le code du Syntakt en SRAM, à la place des tables d'ondes de CHORD `[HYP]`

- **`[FAIT]`** Environ **30 Ko de la SRAM** contiennent 30 tables d'ondes de 1 028 o (`0x80001c5c..0x800074b4` et `0x8000cac0..0x8000eae0`) :
  - elles sont désignées par une table de 32 pointeurs (`0x40118590`), lue par une seule fonction (`0x400a8060`) ;
  - celle-ci est appelée par une seule autre (`0x400a8080`), elle-même appelée par l'update de CHORD (`0x400ab15e`) ;
  - **seul CHORD s'en sert**, et une voix CHORD en lit 2 par bloc (2 Ko).
  - Source : désassemblage de `0x400a8060..0x400a807e` ; trace des 6 machines d'origine.
- **`[FAIT]`** Le contenu initial de ces tables reste dans l'image de l'OS en SDRAM (`0x4019b590..`, recopié dans la SRAM au démarrage) : il suffirait de faire pointer la table `0x40118590` sur ces copies, **sans rien recopier**.
- **`[FAIT]`** La SRAM peut exécuter du code : le bootstrap s'y exécute (`0x80000000`, décompresseur `0x800006bc`), et l'OS ne change jamais ce réglage (aucun `movec` vers RAMBAR dans le MAIN OS).
- **`[HYP]`** On libérerait ainsi 22,6 Ko contigus en `0x80001c5c`, pour y placer :
  - les fonctions du Syntakt (13,8 Ko pour les 5 moteurs, regroupées ; les sauts relatifs entre elles sont à recalculer) ;
  - et la passerelle ;
  - le reste (8 Ko en `0x8000cac0`) servirait aux tables de SD VINTAGE, SY SWARM et en partie SY BITS.
- **Gain estimé** (modèle du §2), avec 5 moteurs différents :
  - environ 690 lignes de code et 250 lignes de données en moins par bloc, soit environ **8 % du bloc** ;
  - une voix du Syntakt passerait d'environ 11,5 à 9,8 % : 5 voix tiendraient sous 82 % ; 6 voix seraient vers 89 %.
- **Coût** : une voix CHORD lirait ses 2 tables en SDRAM, environ 130 lignes, soit +1,2 % par voix CHORD.
- **À vérifier avant** : qu'aucun autre chemin ne lit ces tables. Les 627 mots de l'image qui tombent dans ces adresses sont à trier ; les premiers sont des instructions, pas des pointeurs.

### 3.4 Le mixage et les effets (≈ 30 %)

- Ils coûtent autant que 4 voix d'origine, à chaque bloc, même à l'arrêt.
- Pas émulables en l'état :
  - la fonction audio complète (`0x4005979e`) tourne sans fin en émulation, faute de l'état de l'OS : `0x40091ab2`, puis la fonction de sortie et effets `0x400567ba` ;
  - le mixage seul (`0x40056f58`) ne fait que 6 000 instructions.
- Piste à étudier plus tard : ne plus calculer les effets quand ils ne reçoivent rien et que leur queue s'est éteinte, comme pour les voix ([23 §7](23-optimisation-charge.md)). Le gain dépendrait du projet.

### 3.5 Écartées

- **Fréquence du processeur** : le minuteur DMA 0 compte à 135,168 MHz ([23 §5](23-optimisation-charge.md)). Le cœur tourne déjà à sa vitesse nominale, ou au-dessus ; reprogrammer la PLL toucherait la DDR2, l'audio et l'USB. Trop risqué sans interface MIDI de secours.
- **Alléger les moteurs eux-mêmes** (moins d'oscillateurs pour SY SWARM, etc.) : le son ne serait plus celui du Syntakt.

## 4. Firmware de diagnostic v6 `[FAIT]`

Construit localement :
- `build/diag/model-cycles_OS1.13_diagnostic-charge_v6.syx` (MAIN OS `c9b60d1c…`) ;
- `…_v6_6ch.syx` avec l'audio USB 6 canaux (MAIN OS `72daa317…`).

**Ce qui change par rapport à la v5** :
- Le nom de **chaque machine** devient « moyenne/voix », par exemple `84/11` :
  - charge moyenne de la fonction audio ;
  - coût mesuré de la voix qui joue cette machine (la plus chère si plusieurs pistes la jouent) ;
  - les deux en % de la durée d'un bloc, mis à jour toutes les 0,5 s ; `--` si aucune piste ne la joue.
  - Le pic n'est plus affiché.
- Régulateur : coupures seulement au-dessus de **86 %** de moyenne (82 % dans les firmwares du flasher). Les protections contre les blocs isolés (90 %, 92 %) ne changent pas.
- Le son et tout le reste sont ceux de la v5 ; les firmwares du flasher ne changent pas (les 31 tweaks sont identiques à l'octet près).

**Preuve en émulation** :
- `test_meter.py` : 6 pistes réglées sur 6 moteurs et 6 coûts connus ; après 750 blocs à 50 %, les 11 noms sont exactement ceux attendus (`50/7`, `50/8`, `50/11`, `50/9`, `50/15` pour une machine jouée par deux pistes à 13 et 15 %, `50/--` sinon) ; sortie identique avec et sans compteur.
- `test_governor.py --target 82` sur ce tweak : tout passe.

**À relever sur la machine** :
1. Le motif à 5 voix du Syntakt qui coupait : y a-t-il encore des coupures ? L'interface est-elle utilisable ?
2. Sur chaque piste : ouvrir MACHINES sans tourner la molette, noter « moyenne/voix ».
3. Si possible, les mêmes relevés avec 6 voix du Syntakt, et avec 5 fois le même moteur sur des pistes voisines (§3.2).

Relevés de l'utilisateur et suite : [28](28-code-syntakt-en-sram.md).
