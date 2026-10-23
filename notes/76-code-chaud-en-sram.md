# 76 — Le code chaud en SRAM interne, chargé selon les machines du projet

Demande de Maxime (22/10/2026), « chantier 2 » des dix pistes d'allègement du processeur : « Fait le firmware de
mesure, puis le chantier 2 ». Le firmware de mesure est la [note 75](75-firmware-de-mesure.md). Ce chantier recopie en
SRAM interne le code que l'interruption audio exécute à chaque bloc, selon les machines des 6 pistes, pour qu'il ne
soit plus relu en DDR2.

Générateur `tools/gen_sram_hot.py` (appelé par `tools/gen_modal.py` : le chargeur fait partie du tweak des moteurs,
`31-syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-modal.json`), chargeur `tools/machines/sram_hot/` (`hot.c`,
`hot_asm.S`), profil `tools/emu/profile_hot.py` → `tools/machines/sram_hot/profile.json`, preuve
`tools/emu/test_sram_hot.py`, banc de l'interruption complète `tools/emu/osbanc.py`, inventaire
`tools/emu/inventory_code.py`.

## En bref

| | État |
|---|---|
| Le code relu à chaque bloc | `[FAIT]` en émulation : 17 à 27 Ko par bloc, le cache d'instructions (8 Ko) n'en garde presque rien (§1) |
| La place en SRAM | `[FAIT]` le code et les tables du Syntakt (17,5 Ko) quand aucune piste ne s'en sert ; `[HYP]` deux fins de SRAM (5,2 Ko) que rien ne désigne (§2) |
| Le code en SRAM passe par le cache d'instructions | `[FAIT]` RAMBAR du bootstrap ; il faut vider ce cache après chaque recopie (§3) |
| Chargeur : unités, corrections, détours, régions rendues | `[FAIT]` en émulation (§4, §5) |
| Son identique, chargeur inerte contre chargeur lancé | `[FAIT]` en émulation, toutes les machines, changements de machine compris (§6) |
| Gain | `[HYP]` modèle : 1 488 → 441 lignes lues en DDR2 par bloc sur un projet d'origine, les autres lues en SRAM ; à mesurer (§7) |
| Sur la machine | à tester (§9) |

## 1. Pourquoi : le code relu à chaque bloc

Banc `tools/emu/osbanc.py` : le vrai code de l'interruption audio, du début du rendu (`0x40058ca0`) à la mise en file
de l'envoi USB (`0x40059398`), étage de sortie compris (mixeur, envois, delay, reverb, master, anneau du codec), avec
l'eDMA simulé et la SDRAM vue avec et sans cache. Repris du banc de l'étude du 18/10/2026 (tag
`etude-optimisation-os-2026-10-18`), pour l'OS complet.

- **`[FAIT]`** Lignes de 16 o de code exécutées par bloc (`inventory_code.py`, 6 pistes, un trig tous les 6 blocs) :

| Projet | Lignes distinctes par bloc | Défauts du cache d'instructions par bloc (cache vidé / gardé) |
|---|---|---|
| 6 machines d'origine | 1 343 (21 Ko) | 1 389 / 1 377 |
| SDVtg, CPVtg, SYToy, SYBit, SYSwm, Sampler | 1 725 (27 Ko, le code du Syntakt déjà en SRAM) | 949 / 932 |
| MACRO, ACID, MODAL | 1 544 (24 Ko) | 1 984 / 2 010 |

- Modèle du cache : 8 Ko, 4 voies, lignes de 16 o (MCF5441x RM, §1.7.2), remplacement par compteur tournant (§6.3.1).
- Le cache gardé d'un bloc à l'autre ne fait presque pas mieux que vidé : il ne garde rien. Environ 1 000 lignes sont
  communes à toutes les machines (étage de sortie : 325 lignes à lui seul).

## 2. La place

La SRAM interne (64 Ko en `0x80000000`) est déjà pleine (notes/26, 28, 29) ; les tables d'ondes de CHORD libérées
(`0x80001c5c..0x800074b4` et `0x8000cac0..0x8000eae0`) portent le code du Syntakt (13,8 Ko), trois de ses tables
(4,2 Ko avec leurs gardes), les états des 6 voix du Syntakt (10,8 Ko) et les fonctions chaudes de la passerelle
(2 Ko).

Régions du chargeur (`regions()` de `gen_sram_hot.py`) :

| Région | Taille | En place quand |
|---|---|---|
| Code du Syntakt `0x80001c5c..0x80005268` | 13 836 o | une piste a un moteur du Syntakt (machines 08 à 12) |
| Tables de SD VINTAGE `0x80005268..0x80005a90` | 2 088 o | une piste a SDVtg |
| Forme d'onde de SY SWARM (l'une de SY BITS) `0x80005a90..0x800062b4` | 2 084 o | une piste a SYBit ou SYSwm |
| Fin de la 1ʳᵉ zone `0x800074c0..0x80008000` | 2 880 o | jamais (toujours au chargeur) |
| Fin de la 2ᵉ zone `0x8000f6f0..0x80010000` | 2 320 o | jamais |

- Une région « en place » qui a servi au chargeur est rendue depuis la zone de transit de la charge utile
  (`0x46700000..`, l'image que le crochet de démarrage recopie en SRAM), 2 Ko par bloc.
- **`[FAIT]`** La zone de transit n'est jamais réécrite (preuve, §6).
- **Les deux fins de SRAM** :
  - `[FAIT]` l'OS les remet à zéro au démarrage (boucles `0x4000047c` jusqu'à `0x80008000`, `0x400004a4` jusqu'à
    `0x80010000`), après ses données initialisées (`0x800074c0`, `0x8000f6f0`) ;
  - `[FAIT]` aucune constante de 32 bits du code de l'OS (`0x40000400..0x40118000`), du bloc de Model-TG ni du code de
    la charge utile n'y pointe (les seules valeurs trouvées sont dans des tables de nombres et des images) ; l'objet le
    plus haut de chaque zone finit avant (tables d'ondes de CHORD en `0x800074b4`, table de 1 028 o
    `0x8000f2e8..0x8000f6ec`) ; les tampons USB s'arrêtent à `0x80009f00` (`0x40002dac`) ;
  - `[FAIT]` en émulation, l'audio n'y lit ni n'y écrit rien (5 projets, 40 blocs chacun) ;
  - `[HYP]` l'interface non plus : rien ne les désigne, mais seule la machine le confirmera.
- Pas utilisés ici : les états des voix du Syntakt (le 1er trig d'une machine du Syntakt depuis le démarrage les
  réécrit tous, `st_init` de la passerelle) et la zone de travail des voix d'origine (réécrite à chaque bloc).

## 3. Le code en SRAM passe par le cache d'instructions

- **`[FAIT]`** Le bootstrap règle RAMBAR à `0x80000235` (section 2, offset 3 552 : `movec d0,rambar`) ; l'OS ne
  l'écrit jamais. C'est la valeur « données seulement » de NXP : les accès au code (SC, UC) sont masqués, donc
  « traités comme toute autre référence ».
  - Source : *MCF5441x Reference Manual* rev. 5, §7.2.1 (table 7-2, table 7-3 « Data Only 0x35 ») ([NXP][RM-MCF]).
- **`[FAIT]`** Le CACR de l'OS (`0xa50ce100`, `0x40000548`) a IDCM = 0 : une instruction lue hors des ACR (la SRAM,
  `0x8000xxxx`) est cachable.
  - Source : même manuel, §6.3.1.
- Une instruction en SRAM passe donc par le cache d'instructions, et une ligne absente est lue par la porte arrière de
  la SRAM (crossbar), pas en DDR2. Deux conséquences :
  - **le chargeur vide le cache d'instructions** (et celui des branchements) après avoir recopié du code, avant qu'il
    serve : sinon le processeur pourrait exécuter des lignes de ce qu'il y avait avant à ces adresses
    (`hot_icinv_run` : le CACR de l'OS sans DCINVA, comme le firmware de mesure) ;
  - **le gain n'est pas le prix entier d'une ligne lue en DDR2**, mais la différence entre une ligne lue en DDR2 et
    une lue en SRAM. Le firmware de mesure donne les deux (LINE SR contre I-MISS, notes/75 §1.2).
- Autoriser le code à lire directement la SRAM (RAMBAR « instructions et données », `0x21`) le sortirait du cache
  d'instructions, mais le code et ses données (états des voix, tampons) se disputeraient alors la SRAM. Pas fait sans
  mesure (§10).

## 4. Le chargeur (`hot.c`, `hot_asm.S`)

Dans la charge utile du tweak des moteurs, à `0x4678a000` (code), `0x4678c000` (tables), `0x4678e000` (variables, à
zéro au démarrage) ; 2,7 Ko de code (dont 146 talons de 8 o), 4,8 Ko de tables.

- **Unités** (`hot_units`, triées par lignes chaudes par octet) : une ou plusieurs fonctions contiguës. Copiées telles
  quelles, puis corrigées :
  - aucune référence relative au PC ne sort d'une unité (sinon les fonctions sont réunies, ou l'unité est refusée) ;
  - un champ de 32 bits absolu (`jsr`, `jmp`, `lea`…) qui vise une instruction d'une autre unité chargée est corrigé
    vers sa copie (`hot_fixes`) ; vers une unité absente, il garde l'original. Le chargeur vérifie que la valeur lue
    est bien dans l'unité visée avant de la corriger (une autre version de l'OS, comme le firmware de mesure, peut y
    avoir mis autre chose).
- **Détours** (`hot_dets`) : au démarrage (`hot_boot`, 2ᵉ étage du crochet, cache de données coupé), l'entrée de
  chaque fonction chaude devient `jmp talon` ; le talon (`hot_stubs`, 8 o) fait `move.l hot_tab+4i,-(sp) ; rts`.
  - `hot_tab[i]` vaut la copie pendant le calcul audio, l'original sinon (`hot_orig[i]` : les instructions déplacées,
    puis `jmp entrée + k`). Les tables sont recopiées deux fois par bloc (`hot_copy`, par `movem`).
  - L'interface et les autres interruptions n'entrent donc jamais dans une copie : une copie n'est recouverte qu'en
    dehors du calcul audio, quand personne n'y est.
  - Instructions déplacées : 6 o au moins, ni relatives au PC, ni EMAC, ni branchement, sans cible de saut connue
    dedans, sans octet écrit par un tweak de l'OS. Pas dans le bloc de Model-TG.
  - Une somme des octets d'origine est vérifiée au démarrage ; si elle ne correspond pas, pas de détour.
  - Les 65 entrées dans la section 3 sont déclarées `runtime` (`check_overlaps.py` refuse qu'un autre mod y écrive).
- **Racine** : `0x40059382` appelle `hot_probe` au lieu de la sonde de la passerelle (`audio_probe`) ; `hot_probe`
  appelle `hot_step` (le chargeur), puis la sonde ou sa copie, puis `hot_after`.
- **Signature** : les machines des 6 pistes, d'après le paramètre MACHINE (`0x8000102c + 0x42 t`, borné, puis la
  table de la passerelle, comme `0x400a7db0`) **et** la machine de la voix (`0x42308828 + 0x31c t`) : Model-TG garde
  celle de la note en cours jusqu'au trig suivant (relevé en émulation).
- **Plan** : à chaque nouvelle signature, plus rien n'est actif ; les unités des machines du projet sont placées par
  ordre de valeur dans les régions libres (même alignement modulo 4 que l'original) ; les régions dont une machine a
  besoin sont rendues d'abord. 2 Ko recopiés par bloc ; une fois tout en place : cache d'instructions vidé, copies
  actives.
- **Pause** : `st_away`, un bit par machine, vaut les machines dont une région n'est pas en place. Le dispatch des
  voix (`gen_syntakt_engines.py`, `dispatch_tg_asm`) laisse leur piste muette, sans la calculer, quoi que la boucle des
  voix choisisse. Une machine du Syntakt choisie alors que son code avait laissé la place se tait donc le temps qu'il
  revienne (7 blocs, 5 ms, pour SDVtg).
- Le 2ᵉ étage du crochet de démarrage (`stub.S`, `BOOT2`) appelle `hot_boot` à sa fin.

## 5. Le générateur et le profil

- `profile_hot.py` : chaque machine seule sur les 6 pistes (MACRO : 18 modèles, MODAL : ses 4 modèles et ses
  polyphonies), chargeur inerte ; les lignes exécutées dans l'appel de `0x40059382` et les cibles des appels et des
  sauts. Profil versionné (`--check` le refait).
- `gen_sram_hot.py` : sur l'image de l'OS construit (os.json avec ce tweak), désassemblage depuis les entrées du profil
  (tables de sauts de GCC comprises), unités, corrections, détours, masque des machines et priorité.
- Chiffres (OS 2.1) : 140 unités, 73 Ko en tout (19 Ko de l'OS, 54 Ko de nos machines et de la passerelle), 197
  corrections, 146 détours (65 dans l'OS, 81 dans la charge utile). Refusées : les fonctions de Model-TG qui lisent
  ou écrivent leurs variables relativement au PC (une copie lirait les siennes), et ce qu'elles appellent par `bsr` ;
  il n'en reste aucune de Model-TG.
- Deux passes : le tweak est construit avec les points d'entrée fixes du chargeur (`hot_boot` à `0x4678a000`,
  `hot_probe` à `+6`, `st_away` à `0x4678e000`), puis le chargeur et ses tables sont compilés sur cette image et
  ajoutés à la fin de la charge utile (rien d'autre ne bouge).

## 6. Preuve en émulation

`test_sram_hot.py`, sur l'OS construit, chargeur inerte (l'OS sans le démarrage du chargeur) contre lancé :

1. démarrage : 146 détours posés, chacun avec ses instructions d'origine et son retour ; talons. Et
   `test_payload_pack.py` fait tourner le vrai démarrage (décompression, 2ᵉ étage, `hot_boot`) : les 146 détours
   posés (65 dans l'OS, 81 dans la charge utile), rien d'autre de changé dans l'OS ;
2. son : les 6 voix, l'anneau du codec, la copie pour l'USB et les états des voix identiques, bloc par bloc :
   6 machines d'origine (70 blocs), MACRO/ACID/MODAL (70), 5 moteurs du Syntakt et le Sampler (60), un projet mêlé
   (60), et 170 blocs de changements de machine (le Syntakt arrive, repart ; MODAL, SY BITS, SY SWARM) ; chaque machine
   jouée était dans la signature du chargeur ;
3. pause : SDVtg choisie quand son code avait laissé la place : piste muette 7 blocs malgré ses trigs, puis elle
   joue ; code du Syntakt rendu octet pour octet ;
4. zone de transit intacte ; dans les fins de SRAM, seul le chargeur écrit ;
5. modèle du cache (§7).

Le banc pose les crochets EMAC sur ce que le chargeur recopie (`hot_note`, `emac.py` : `rescan`).

## 7. Gain attendu

Modèle du cache d'instructions (§1), le code en SRAM compris (§3), cache gardé d'un bloc à l'autre, copies en place :

| Projet | Lignes lues en DDR2 par bloc | Lignes lues en SRAM par bloc | Instructions par bloc |
|---|---|---|---|
| 6 machines d'origine | 1 488 → 441 | 61 → 1 229 | 73 322 → 74 047 |
| MACRO, ACID, MODAL | 2 556 → 1 993 | 83 → 933 | 111 172 → 112 542 |
| 5 moteurs du Syntakt et le Sampler | 1 052 → 906 | 985 → 1 239 | 80 788 → 81 603 |
| Projet mêlé (KICK, SNARE, SDVtg, MACRO, ACID, CHORD) | 1 667 → 1 382 | 322 → 753 | 80 344 → 81 363 |

- Le gain, en cycles, est (lignes qui ne sont plus lues en DDR2) × (prix d'une ligne DDR2) − (lignes de plus en SRAM)
  × (prix d'une ligne SRAM) − (instructions de plus) × 1,5. Avec 30 et 10 cycles `[HYP]` : environ 18 500 cycles par
  bloc sur un projet d'origine (11 points), 6 000 avec MACRO/ACID/MODAL (4 points), 3 000 sur le projet mêlé
  (2 points), rien de sûr avec 5 moteurs du Syntakt. Les vrais prix viendront du firmware de mesure (I-MISS, LINE SR).
- Coût du chargeur, une fois tout en place : la signature, deux recopies de 146 mots de `hot_tab`, et un passage par
  un talon à chaque appel d'une fonction détournée depuis le code resté en SDRAM : 725 à 1 371 instructions de plus
  par bloc (0,7 à 1,3 point) ; davantage quand une machine a des fonctions détournées mais pas recopiées (le détour
  passe alors par l'original déplacé).
- Pendant un chargement (environ 20 blocs, 13 ms, après un changement de machine ou de projet), rien n'est actif et
  2 Ko sont recopiés par bloc : environ 3 points de plus sur ces blocs.
- Peu de place avec beaucoup de moteurs du Syntakt (leur code reste en place) : seules les deux fins de SRAM.
- MODAL gagne peu : ses deux plus grosses fonctions (9 et 10 Ko, dont un tiers de lignes chaudes) passent après le
  reste (§10).

## 8. Taille

- Charge utile : 560 948 → 598 016 o en mémoire ; rangée compressée en 257 552 o (+5 Ko) : l'image finit à
  `0x401fe6d0`, 6 448 o avant la limite (`0x40200000`).

## 9. À tester sur la machine

1. Démarrage, interface, chargement d'un projet : rien ne doit changer.
2. Un projet des 6 machines d'origine, puis un projet MACRO/ACID/MODAL, puis un projet avec des moteurs du Syntakt :
   le son, et le pourcentage de la page System de Model-TG, à comparer avec l'OS 2.1 d'avant.
3. Changer la machine d'une piste en jouant, surtout vers SDVtg, SYBit ou SYSwm quand aucune piste n'en avait : la
   piste peut se taire 5 ms, pas de bruit ni de plantage.
4. Le firmware de mesure (notes/75), avec et sans ce chargeur : AUDIO (TOTAL, VOICES, OUTPUT) et BENCH (I-MISS,
   LINE SR).

## 10. Suite

- Les états des voix du Syntakt des pistes qui n'en ont pas (1,8 Ko chacun) : il faut que la passerelle n'écrive
  plus toutes les voix au 1er trig (`st_init`).
- MODAL en unités plus fines (ses boucles chaudes hors des grosses fonctions).
- Selon la mesure : RAMBAR « instructions et données » (§3), `hot_tab` en SRAM.

## Chronologie

- 22/10/2026 : demande de Maxime ; inventaire, prototype en Python (sortie identique, défauts du cache 1 377 → 141
  dans un modèle qui comptait la SRAM hors cache).
- 23/10/2026 : chargeur en C, profil, générateur, preuve ; RAMBAR du bootstrap relu : le code en SRAM passe par le
  cache d'instructions (§3), modèle refait, cache vidé après chaque recopie (ici et dans le firmware de mesure).

[RM-MCF]: https://www.nxp.com/docs/en/reference-manual/MCF54418RM.pdf
