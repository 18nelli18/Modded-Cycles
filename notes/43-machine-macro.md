# 43 — Machine MACRO : les 47 modèles de synthèse de Braids sur le Model:Cycles

Demande de la communauté (forum « feedback » du Discord du projet, « Adding mutable instruments engines as machines
(Braids, Plaits, etc) », 5 votes, idée de dan303 : les macros de Plaits sur COLOR, SHAPE et SWEEP, CONTOUR pour le low
pass gate), relevée par le point hebdo du 06/10/2026 ; Maxime a choisi le même jour « Braids d'abord » : une machine
MACRO avec les modèles de Braids, les moteurs de Plaits plus tard, un par un, s'ils tiennent en charge. Tweaks
`25-macro.json` (seul) et `32-macro-tg.json` (avec Model-TG), générateur `tools/gen_macro.py`, passerelle
`tools/machines/macro/`, preuve `tools/emu/test_macro.py` (référence `tools/emu/braids_ref.cc`). Adresses : VA de l'OS
1.13.

## Réponse courte

- **Braids tourne tel quel sur le Cycles** : son code est en entiers 16 bits, fait pour un processeur sans FPU. Plaits
  calcule en flottant partout ; le ColdFire du Cycles n'a pas de FPU : chaque moteur de Plaits serait à réécrire en
  virgule fixe (§1).
- **Une seule machine ajoutée, MACRO, dont SHAPE choisit le modèle** (0 à 46, verrouillable par pas), plutôt que 47
  machines : la mécanique des machines ajoutées en accepte 6 (§2), et un modèle par pas reste un simple p-lock.
- **Le son est celui du code de Braids, à l'échantillon près** `[FAIT en émulation]` : Braids rend à 96 kHz comme sur
  le module, un filtre demi-bande ramène à 48 kHz (passe-bande 0..19 kHz à 0,05 dB près, −46 dB dès 29 kHz). DECAY,
  GATE et PUNCH sont la chaîne d'ampli d'origine, réglée comme TONE.
- **Charge** : une voix MACRO coûte environ 2 fois une voix TONE en instructions, de 0,8 fois (CLOCKED NOISE) à 3,4 fois
  (WAVE MAP) selon le modèle (§8). Pas de régulateur de charge : quelques pistes MACRO lourdes jouées ensemble peuvent
  dépasser le temps d'un bloc (son qui craque, écran ralenti, comme les moteurs du Syntakt avant leur régulateur,
  [25](25-regulateur-de-charge.md)). À écouter sur la machine.
- **Licence** : MIT, crédit à Émilie Gillet ; ni le nom du module ni celui de Mutable Instruments sur la machine.

## 1. Faisabilité : Braids ou Plaits `[FAIT en émulation, 06/10/2026]`

Mesures sur le code d'origine (`pichenettes/eurorack`, commit `08460a6`, stmlib `e3bd7c9`), compilé pour le ColdFire
du Cycles (`-mcpu=54418 -O2`), exécuté dans Unicorn par blocs de 32 échantillons ; sorties identiques à l'échantillon
près à la même voix compilée pour l'ordinateur (le banc est juste).

| | Plaits | Braids |
|---|---|---|
| Calcul | flottant partout | entier (16 bits), fait pour un processeur sans FPU |
| Tel quel sur le ColdFire | 8 000 à 73 000 instructions **plus 1 200 à 11 700 opérations flottantes** par bloc, chacune une routine logicielle : plus que tout le processeur | tourne tel quel |
| Sur sa propre puce (Cortex-M4F, avec FPU) | 4 604 (Speech) à 25 896 (Modal) instructions par bloc, ~13 000 en général | — |
| Travail | réécrire chaque moteur en virgule fixe (24 moteurs) | brancher sur la boucle des voix, 96 → 48 kHz |
| Place | ~48 Ko de code + 91 Ko de tables, ~25 Ko de RAM par voix | ~98 Ko de code et tables (dont 33 Ko de tables d'ondes), ~17 Ko de RAM par voix |

Une réécriture de Plaits en virgule fixe ne descendrait pas sous son coût sur sa propre puce : ~2 voix du Cycles par
voix de Plaits. D'où le choix de Maxime : Braids d'abord.

## 2. Ce que l'OS impose `[FAIT]`

| Où | Quoi |
|---|---|
| `0x400a7d4a` | boucle des voix ([14 §2](14-machine-sd-vintage.md)) : pour chaque piste, `update[m](pmod, voix, params)` puis `render[m](out, voix)`, par les tables `0x40118628` / `0x40118610` ; une machine ≥ au nombre de machines n'est pas calculée |
| `voix + 0` / `+4` | machine courante / précédente ; la machine ne change qu'au bloc qui suit un trig (`+0x38`) ; remise à zéro de la voix `0x400a7ab8` |
| `voix + 0x34` / `+0x38` | trig de ce bloc / du bloc précédent |
| `pmod` | note du trig en demi-tons `<< 16` ; toutes les machines : note = PITCH − 64 + note du trig + FINE, bornée à 0..127, 440 Hz à 69 |
| `params + 0x14..0x24` | PITCH, COLOR, SHAPE, SWEEP, CONTOUR, PUNCH, GATE, FINE, DECAY (mots 8.8) |
| `0x400a9252` / `0x400a9430` / `0x400a967a` | enveloppe d'ampli, VCA, PUNCH : fonctions feuilles, appelées par le `render` de TONE |
| `voix + 0x230..0x2a4` | état de l'enveloppe et de PUNCH, réglé par l'`update` de TONE (`0x400aa7b8`) au trig |

Les machines ajoutées reprennent la mécanique des moteurs du Syntakt ([20](20-moteurs-syntakt-a-cocher.md),
[31](31-model-tg.md)) : tables des descripteurs, des rangées, des noms et de `update`/`render` déplacées dans la charge
utile, bornes `moveq` relevées, détours de l'écran MACHINES, de la molette et des enregistrements. Elle accepte 6
machines ajoutées : MACRO en prend une, et la même place (charge utile à `0x43000000`, `0x46700000` avec Model-TG) que
les moteurs du Syntakt, d'où leur incompatibilité (§6).

## 3. Conception

### 3.1 Les potards

| Potard du Cycles | Nom affiché | Ce que reçoit Braids |
|---|---|---|
| PITCH, FINE, touches | — | note = PITCH − 64 + note du trig + FINE (±2 demi-tons), en 1/128 de demi-ton : la même convention, 440 Hz à 69 (mesuré : 439,99 Hz, SINE/TRIANGLE à la note 69) |
| COLOR | Timbre (TIMB) | TIMBRE = COLOR + CONTOUR × enveloppe |
| SHAPE | Model (MODL), 0..46 | le modèle, dans l'ordre de Braids (CSAW, MORPH, … DIGITAL MODULATION ; sans QUESTION MARK) |
| SWEEP | Color (COLR) | COLOR de Braids |
| CONTOUR | Env Timbre (ENVT) | quantité d'enveloppe d'ampli ajoutée à TIMBRE (son niveau au bloc précédent, plein au trig) ; 0 : rien |
| DECAY, GATE, PUNCH | (communs) | la chaîne d'ampli d'origine, réglée comme TONE (mêmes constantes au trig, même table de DECAY `0x4011d84c`) |

Un potard 8.8 de 0..127 devient 0..32 766 (`x + (x >> 7)`). Un trig appelle `Strike()` (les modèles percussifs et
physiques sont frappés). L'image de la machine (écran MACHINES, petite icône) est celle de TONE : l'OS n'en a que 6.

### 3.2 De 96 à 48 kHz

Braids est fait pour 96 kHz (tables de hauteur, de filtres, d'ondes) et, sur le module, rend des blocs de 24
échantillons, 4 000 fois par seconde (`kBlockSize` de `braids/braids.cc`). Une partie de son état avance d'un pas par
bloc, pas par échantillon : la décroissance des partiels de STRUCK BELL et STRUCK DRUM (`digital_oscillator.cc`), la
consonne de VOWEL (160 blocs), les lissages de paramètres sur la durée d'un bloc. La passerelle garde donc des blocs de
24 : il lui faut 64 échantillons par bloc de 32 trames, soit 3, 3 puis 2 rendus de 24 (8 × 24 = 3 × 64, 4 000 rendus
par seconde comme sur le module) ; ce qui dépasse (8 ou 16 échantillons, 0,17 ms au plus) attend le bloc suivant.
`[FAIT en émulation]` La première version rendait 24 + 24 + 16 à chaque bloc, 4 500 rendus par seconde : les cloches
et les tambours de STRUCK BELL/DRUM s'éteignaient ~11 % trop vite (relevé à la relecture du 07/10/2026, corrigé
avant la PR). Puis un filtre demi-bande de 23 coefficients
(minimax, Q15, `{10327, −3131, 1579, −820, 434, −197}`, ½ au centre ; somme 1 : gain 1 en continu) garde un
échantillon sur deux : passe-bande 0..19 kHz à 0,04 dB près, −46,2 dB au-delà de 29 kHz (ce qui se replierait sous
19 kHz), retard 5,5 échantillons à 48 kHz. Un filtre de 19 coefficients plafonnait à −39,7 dB. Sortie : la pleine
échelle de Braids donne la moitié de la pleine échelle Q31 du Cycles.

### 3.3 État, initialisation, voix muette

- Une voix de Braids par piste (`MacroOscillator`, 22 échantillons d'historique du filtre et l'avance de 16 au plus :
  17 192 o), dans le BSS de la charge utile, mis à zéro au démarrage.
- Initialisée à la première note sur la machine : repère `'MCR1'` en `voix + 0x2c`, effacé par la remise à zéro de la
  voix (`0x400a7ab8`) à chaque changement de machine.
- **Voix muette non calculée** : sans trig et avec l'enveloppe d'ampli sous 2^14 (−102 dB), la sortie est nulle et
  Braids ne tourne pas. C'est ce qui permet de mêler MACRO aux autres machines sans régulateur.
- Le générateur aléatoire de Braids (`stmlib::Random`, statique) est commun aux 6 pistes : deux pistes de bruit
  s'entremêlent ses tirages. Inaudible ; c'est pourquoi la vérification des 6 pistes ensemble prend des modèles
  analogiques (§7).
- Au changement de modèle, Braids efface l'état de sa voix numérique (194 o) et, pour BOWED, BLOWN et FLUTED, leurs
  lignes à retard (4 à 5 Ko), dans l'interruption audio : `memset` par mots de 32 bits (`rt.c`), ~2 000 instructions
  au lieu de ~25 000 octet par octet.

### 3.4 Avec Model-TG

MACRO est la 8e machine, après le Sampler de Model-TG. Un détour (`dispatch_tg_asm`) en `0x400a7dfe` envoie les
machines 0..6 au dispatch de Model-TG et MACRO à nos `update`/`render`, puis à la fin de l'étage d'amplitude de
Model-TG (`ah_noenv` : Attack, filtre, résonance) ; le temps de MACRO s'affiche sur la page System de Model-TG
(`prof_trk`). Comme pour les moteurs du Syntakt, la version combinée s'ajoute après `model-tg-st` ([31 §4](31-model-tg.md)).

## 4. Place

| | Seul (`macro`) | Avec Model-TG (`macro-tg`) |
|---|---|---|
| Charge utile au démarrage | `0x43000000..0x4304f2f0` | `0x46700000..0x4674f2f0` |
| Code, tables et données de Braids et de la passerelle | 98 230 o à `+0` | idem (33 relocalisations) |
| Détours, données, descripteurs, rangées, enregistrements | `+0x33000..0x36000` (`gs.LAYOUT`) | idem |
| Variables (6 voix de Braids) | 103 152 o à `+0x36000` | idem |
| Ajouté à l'image (morceaux tassés, stub `PACK`) | 103 552 o | 103 964 o |
| Fin de l'image décompressée (limite `0x40200000`) | `0x401c35c0` | `0x401d8edc` |
| Crochet de démarrage | masque de sprite `0x4016cae8` : à `0x400004b2` (remise à zéro du BSS) | idem, appelé par le `jsr` de `0x40000530` puis chaîné à `boot_extra_hook` de Model-TG |

Le crochet (`tools/machines/syntakt_bridge/stub.S`, `PACK`) met la zone de la charge utile à zéro puis y recopie les
morceaux : les 100 Ko de variables ne prennent pas de place dans l'image. `stub.S` a été restructuré pour chaîner
`PACK` et `CHAIN_TO` ; les configurations existantes donnent les mêmes octets.

## 5. Le tweak et sa licence

- `25-macro.json` : 122 écritures, plus l'envoi à l'USB à heure fixe ([35](35-glitches-usb-multipiste.md)) et la boucle
  des voix de [36](36-regulateur-sans-coupures-inutiles.md), comme les moteurs du Syntakt seuls.
- `32-macro-tg.json` : 114 écritures, `requires` `model-tg-st`.
- Le code de Braids est compilé **sans modification** (`braids/macro_oscillator`, `analog_oscillator`,
  `digital_oscillator`, `resources`, `stmlib/utils/random`), avec `m68k-linux-gnu-g++` 13.3 (Ubuntu 24.04) ; un autre
  GCC donne d'autres octets (`--check` le dit). Aucun octet Elektron dans les JSON : la table des descripteurs est
  recopiée au build depuis le fichier de l'utilisateur (recette `cycles`).
- Licence MIT : `tweaks/model-cycles_OS1.13/LICENSE-Braids` (copiée en `docs/flasher/LICENSE-Braids.txt`), écrite par le
  générateur depuis l'en-tête des sources. La carte du flasher, le guide et le README créditent Émilie Gillet et
  disent d'où vient le code ; la machine s'appelle MACRO.

## 6. Incompatibilités

- **Moteurs du Syntakt** (toutes les combinaisons, seuls ou avec Model-TG) : même mécanique de machines ajoutées,
  même place. Le flasher rend les deux cartes exclusives (`excludes`). Les réunir demanderait une charge utile commune :
  [À FAIRE] si on le demande.
- **SD VINTAGE** (`sdvintage-*`, `syntakt-vintage`, `syntakt-meter`…, hors du flasher) : même crochet de démarrage
  (`0x4016cae8`) et même charge utile à `0x43000000`.
- `macro` seul ne va pas avec Model-TG : avec la carte Model-TG cochée, le flasher prend `model-tg-st` + `macro-tg`
  (son `with`), comme pour les moteurs du Syntakt.
- Avec tous les autres mods du flasher (6 canaux, arpégiateur, trig-hold, tempo, animation, drumkilla) : aucune
  écriture ne se chevauche ; les 9 503 combinaisons du flasher se construisent (`tools/ref_mainos.py`).

## 7. Preuve en émulation `[FAIT en émulation]`

`tools/emu/test_macro.py` : le vrai code de l'OS (Unicorn), avec la charge utile telle que le crochet la reconstitue ;
la référence est Braids compilé pour l'ordinateur (`g++ -O2`) depuis les mêmes sources, piloté bloc par bloc par
`braids_ref.cc` avec les réglages que la passerelle doit lui donner (calculés par le test d'après cette note), puis le
filtre demi-bande en Python.

| Vérification | Seule (`macro`) | Avec Model-TG (`macro-tg`) |
|---|---|---|
| Démarrage : le décompresseur du bootstrap relit l'OS agrandi ; le crochet reconstitue la charge utile (0xa5 partout avant), garde la SRAM, la pile et d2..d7/a2..a6 | ok, fin de l'image `0x401c3530` | ok, chaîné à `boot_extra_hook`, fin `0x401d8e4c` |
| Interface (vérifications de `test_syntakt_machines.py` / `test_model_tg_syntakt.py`) : tables, rangées, descripteurs (Model 0..46), écran MACHINES, molette, enregistrements, vrai changement de machine, potards, icône, machine hors limites | ok, 7 machines | ok, 8 machines sur 2 lignes, libellés et touche Attack de Model-TG |
| Son avant la chaîne d'ampli = Braids compilé pour l'ordinateur + filtre, échantillon par échantillon | **105 cas** : les 47 modèles et 58 variantes (COLOR, SWEEP aux bouts, CONTOUR, notes extrêmes, bornes de hauteur, PUNCH, GATE, voix qui se tait puis repart, modèle et potards qui bougent pendant la note, Model au-delà de 46) | **50 cas** : les 47 modèles, la voix qui se tait puis repart, le modèle qui change |
| Voix muette : sortie nulle, aucune instruction de Braids | 113 blocs | 113 blocs |
| Chaîne d'ampli : mêmes lectures de la voix que TONE (24 champs ; DECAY, PUNCH, GATE) | ok | même passerelle |
| Machines d'origine identiques, aucune instruction de Braids | à l'OS d'origine | à Model-TG seul |
| Sortie finale de la piste MACRO identique à MACRO seule (5 modèles) | — | ok |
| Machine locks SNARE → MACRO (FM) → TONE → MACRO (WAVETABLES) → KICK sur une piste | ok | ok |
| 6 pistes MACRO ensemble = chacune jouée seule | ok | ok |
| Filtre demi-bande : gain 1 en continu, 0,04 dB de 0 à 19 kHz, −46,2 dB au-delà de 29 kHz | ok | ok |
| `--with 6ch-usbup,trig-hold,arp,tempo-max,boot-anim` (et `model-tg-st`) : démarrage, machines d'origine identiques aux mêmes mods sans MACRO, sortie de MACRO identique, machine locks | ok | ok |

Durée : 42 min pour la preuve complète, ~25 min avec `--quick`. Et le flasher : les 9 503 combinaisons proposées par la
page, construites par la page sur le vrai OS (`tools/webflash_smoke.js`, en 8 parts), donnent toutes le MAIN OS de
`REF_MAINOS`, lui-même calculé comme `tools/build.py`.

## 8. Charge

Instructions par bloc de 32 trames d'une voix (la boucle des voix entière, moins la même boucle sans voix), mesurées
dans la vraie boucle des voix : 1er bloc (avec l'initialisation), typique, maximum.

| Modèle | 1er bloc | typique | maximum | typique / TONE |
|---|---|---|---|---|
| 0 CSAW | 7 652 | 7 079 | 7 112 | 1,3 |
| 1 MORPH | 12 352 | 11 842 | 11 899 | 2,2 |
| 2 SAW SQUARE | 12 577 | 12 058 | 12 105 | 2,3 |
| 3 SINE TRIANGLE | 16 474 | 15 850 | 15 850 | 3,0 |
| 4 BUZZ | 10 583 | 9 959 | 9 959 | 1,9 |
| 5 SQUARE SUB | 12 873 | 12 404 | 12 488 | 2,3 |
| 6 SAW SUB | 12 899 | 12 352 | 12 413 | 2,3 |
| 7 SQUARE SYNC | 12 579 | 12 110 | 12 191 | 2,3 |
| 8 SAW SYNC | 9 235 | 8 645 | 8 712 | 1,6 |
| 9 TRIPLE SAW | 12 050 | 11 442 | 11 496 | 2,2 |
| 10 TRIPLE SQUARE | 16 901 | 16 561 | 16 704 | 3,1 |
| 11 TRIPLE TRIANGLE | 12 560 | 11 928 | 11 928 | 2,3 |
| 12 TRIPLE SINE | 11 024 | 10 392 | 10 392 | 2,0 |
| 13 TRIPLE RING MOD | 9 549 | 8 941 | 8 941 | 1,7 |
| 14 SAW SWARM | 12 734 | 11 909 | 11 909 | 2,3 |
| 15 SAW COMB | 9 235 | 8 408 | 8 438 | 1,6 |
| 16 TOY | 8 056 | 7 274 | 7 274 | 1,4 |
| 17 DIGITAL FILTER LP | 12 056 | 11 320 | 11 344 | 2,1 |
| 18 DIGITAL FILTER PK | 12 120 | 11 383 | 11 406 | 2,2 |
| 19 DIGITAL FILTER BP | 11 608 | 10 872 | 10 896 | 2,1 |
| 20 DIGITAL FILTER HP | 11 608 | 10 871 | 10 894 | 2,1 |
| 21 VOSIM | 9 943 | 9 161 | 9 161 | 1,7 |
| 22 VOWEL | 8 996 | 8 174 | 8 174 | 1,5 |
| 23 VOWEL FOF | 12 634 | 11 891 | 11 981 | 2,2 |
| 24 HARMONICS | 17 325 | 16 543 | 16 543 | 3,1 |
| 25 FM | 7 073 | 6 291 | 6 291 | 1,2 |
| 26 FEEDBACK FM | 7 627 | 6 845 | 6 845 | 1,3 |
| 27 CHAOTIC FEEDBACK FM | 8 054 | 7 272 | 7 272 | 1,4 |
| 28 PLUCKED | 8 050 | 9 123 | 9 224 | 1,7 |
| 29 BOWED | 10 743 | 7 516 | 7 516 | 1,4 |
| 30 BLOWN | 10 683 | 8 066 | 8 076 | 1,5 |
| 31 FLUTED | 14 903 | 11 796 | 11 796 | 2,2 |
| 32 STRUCK BELL | 14 607 | 13 320 | 13 385 | 2,5 |
| 33 STRUCK DRUM | 13 679 | 12 933 | 12 947 | 2,4 |
| 34 KICK | 11 704 | 10 275 | 10 634 | 1,9 |
| 35 CYMBAL | 16 532 | 15 664 | 15 667 | 3,0 |
| 36 SNARE | 12 752 | 11 601 | 11 609 | 2,2 |
| 37 WAVETABLES | 10 743 | 9 965 | 9 965 | 1,9 |
| 38 WAVE MAP | 18 981 | 18 199 | 18 199 | 3,4 |
| 39 WAVE LINE | 14 711 | 13 929 | 13 929 | 2,6 |
| 40 WAVE PARAPHONIC | 18 414 | 17 600 | 17 600 | 3,3 |
| 41 FILTERED NOISE | 8 179 | 7 397 | 7 397 | 1,4 |
| 42 TWIN PEAKS NOISE | 6 887 | 6 097 | 6 117 | 1,2 |
| 43 CLOCKED NOISE | 4 789 | 4 007 | 4 024 | 0,8 |
| 44 GRANULAR CLOUD | 13 726 | 12 850 | 12 936 | 2,4 |
| 45 PARTICLE NOISE | 7 309 | 6 481 | 6 617 | 1,2 |
| 46 DIGITAL MODULATION | 7 826 | 7 040 | 7 040 | 1,3 |

- Boucle des voix sans voix : 1 232 instructions par bloc ; **TONE : 5 291** (une voix d'origine).
- **MACRO : 4 007 à 18 199, médiane 10 872** (2,1 fois TONE). Les plus lourds : les cartes d'ondes (WAVE MAP, WAVE
  PARAPHONIC, WAVE LINE), HARMONICS, TRIPLE SQUARE, SINE TRIANGLE, CYMBAL ; les plus légers : les bruits et la FM.
- Voix muette : 246 ; changement de modèle FM → BOWED (lignes à retard effacées) : 10 137 ; pile : 356 o sous la boucle
  des voix.
- Avec Model-TG (CSAW, VOWEL FOF, WAVETABLES) : 7 138, 11 950 et 10 024, TONE 5 669 (son étage d'amplitude), voix
  muette 305.

Braids rend ici 64 échantillons par bloc (96 kHz), deux fois plus que les mesures de faisabilité du 06/10 (blocs de 32
échantillons : 959 à 8 031 instructions selon le modèle), plus le filtre demi-bande et la chaîne
d'ampli d'origine.

Ce sont des instructions, pas des cycles : le ColdFire n'a que 8 Ko de cache d'instructions et 8 Ko de cache de
données, et la SDRAM (DDR2 sur un bus de 8 bits) coûte cher à chaque défaut. Le code de Braids atteint par un modèle
devrait tenir à peu près dans le cache, mais pas ses tables d'ondes (33 Ko) : les modèles à tables d'ondes peuvent
coûter plus que ce rapport sur la machine `[HYP]`. Le régulateur des moteurs du Syntakt ([25](25-regulateur-de-charge.md),
[30](30-regulateur-charge-soutenue.md), [36](36-regulateur-sans-coupures-inutiles.md)) n'est pas branché ici : plusieurs
pistes MACRO lourdes jouées ensemble peuvent dépasser le temps d'un bloc et faire craquer le son. Model-TG affiche le
temps de MACRO sur sa page System.

## 9. À vérifier sur la machine

1. Flasher MACRO seule, puis avec Model-TG : MACHINES montre MACRO en 7e (8e avec Model-TG), avec l'icône de TONE.
2. SHAPE parcourt les modèles 0..46 ; COLOR, SWEEP et CONTOUR changent le son ; la note suit PITCH, FINE et les touches
   (même hauteur que TONE à réglages égaux).
3. DECAY, GATE, PUNCH comme sur TONE ; p-lock de SHAPE (modèle par pas) ; machine locks MACRO ↔ machines d'origine.
4. Une piste MACRO sur un modèle lourd (WAVE MAP, HARMONICS, CYMBAL) avec les machines d'origine, puis deux, trois… :
   craquements, écran ralenti ? Avec Model-TG, la page System donne le temps de chaque piste.
5. Remettre les pistes MACRO sur une machine d'origine avant de reflasher un autre choix ou l'OS officiel.

## 10. Suite

- Un régulateur de charge (celui des moteurs du Syntakt) si la machine craque.
- Les moteurs de Plaits en virgule fixe, un par un, comparés au Plaits d'origine, dans la même machine s'ils tiennent
  en charge (candidats : les trois percussions analogiques, VA, FM, Chords, Speech, String, Modal).
- MACRO avec les moteurs du Syntakt (une charge utile commune), si on le demande.
