# 74 — Machine MODAL : un résonateur d'après Rings

Demande de Maxime (20/10/2026) : « un moteur Rings, fortement inspiré du Mutable Instruments Rings, le projet open
source d'Émilie Gillet », avec « les mêmes possibilités que le Rings, à part l'easter egg qui donne accès à un synthé
caché », et « la possibilité d'importer son propre sample en résonateur d'entrée, via le preset menu ». Tweak
`tweaks/model-cycles_OS1.13/31-syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-modal.json` (celui de l'OS, avec MODAL en
plus), générateur `tools/gen_modal.py`, sources `tools/machines/modal/`, preuves `tools/emu/test_modal_dsp.py` (le
cœur contre Rings) et `tools/emu/test_modal.py` (la machine dans l'OS). Plan de travail : `.pi/plans/` (non versionné).

## En bref

- **MODAL**, 15e machine, après ACID : les 6 modèles de Rings (modal, cordes sympathiques, corde, voix FM, cordes
  sympathiques en accord, corde et réverbe), la polyphonie 1, 2 ou 4, l'excitateur interne de chaque modèle. Le
  synthé caché (`StringSynthPart`) n'y est pas.
- Le cœur est **la `Part` de Rings réécrite en virgule fixe** (le ColdFire n'a pas de FPU) : mêmes calculs, dans le
  même ordre, au même rythme, sur des blocs de 32 trames au lieu de 24. Comparé au code même de Rings compilé pour
  l'ordinateur : 54 cas, médiane 77 dB de rapport signal / écart, le plus faible 36 dB (§6).
- Réglages « éco » (choix de Maxime) : la moitié des modes, 4 cordes au lieu de 8.
- **Pas encore d'entrée audio** : le sample comme excitateur, choisi dans le menu des presets, est l'étape suivante
  (§8). Cette version ne le contient pas.
- Lourd : de 10 300 à 61 000 instructions par bloc selon le modèle et la polyphonie, après l'allègement en
  assembleur (§5).
- `[FAIT en émulation]` (§6.3). Pas encore testé sur la machine (§7).

## 1. Ce que Maxime a choisi (20/10/2026)

Par les cartes de décision :

| Question | Réponse |
|---|---|
| Nom sur l'écran MACHINES | **MODAL** (pas le nom du module, comme MACRO pour Braids) |
| Potards | PITCH = FREQUENCY ; DECAY = DAMPING ; COLOR = BRIGHTNESS ; **SHAPE = MODEL** ; SWEEP = POSITION ; **CONTOUR = STRUCTURE** ; **FUNC + SHAPE = polyphonie** (1, 2, 4) |
| Le sample d'excitation | rejoué **à sa vitesse, depuis le début, à chaque trig** (comme l'entrée IN de Rings) |
| Charge | d'abord « fidèle + régulateur », puis, devant les mesures, **« éco pour tout »** : la moitié des modes, 4 cordes |
| Place dans l'image | **un meilleur compresseur** pour la charge utile (notes/50 §10, OS 2.0.1, PR séparée) |

## 2. Rings `[FAIT, source pichenettes/eurorack 08460a6]`

Rapport d'exploration : `build/ref/rings-scout.md` (non versionné). Ce qui compte ici :

- `rings/dsp/part.cc` : la `Part`. À chaque bloc : `ConfigureResonators` (au changement de modèle ou de
  polyphonie), filtre de note, attribution de la voix au strum (tour circulaire, motif « ping » en polyphonie 3, pas
  de vol de voix), puis chaque voix : filtre d'excitation (passe-bas d'état variable), rendu par modèle, sortie ODD /
  EVEN (en polyphonie 1, les deux micros ; au-delà, voix paires d'un côté, impaires de l'autre, chacune `out - aux`) ;
  réverbe pour le modèle 5 ; limiteur.
- 6 modèles dans `ResonatorModel` (`part.h:51`). L'« easter egg » n'en est pas un : c'est une autre classe,
  `StringSynthPart`, que le module choisit par un réglage caché.
- Excitateurs internes : une impulsion filtrée (modal), une rafale de bruit dans un peigne et un passe-bas
  (`plucker.h`, cordes), les enveloppes de la voix FM.
- Tout est en flottant ; les tables (`resources.cc`) sont produites par `rings/resources/lookup_tables.py`.
- Hors du DSP : `cv_scaler.cc` (lecture des potards et CV : l'hystérésis de l'accord), `strummer.h` (détection des
  attaques), `rings.cc` (porte de bruit de l'entrée). Sur le Cycles, le trig remplace le strum ; l'hystérésis de
  l'accord est reprise (§3.2).

## 3. La machine

### 3.1 Le cœur en virgule fixe (`modal_dsp.h`, `modal_fix.h`)

- **Formats** : signaux 1,0 = 2^24 ; potards et coefficients Q31 ; hauteurs en demi-tons << 16 ; retards en
  échantillons Q11.20.
- **Produits** par l'EMAC (`mac.l`, mode fractionnaire signé saturé, `MACSR = 0xa0` pendant la boucle des voix) :
  `qmul`, `qmac2`, et des versions arrondies (`qmulr`, `qmac2r` : un produit de plus, 2^15 × 2^15) dans les boucles
  des cordes, où la troncature dériverait. Sur l'ordinateur, la même arithmétique à l'octet près (comme `acid_dsp.h`).
- **Calculs par bloc** (coefficients des filtres, hauteurs, durées) : un flottant maison `xf` (mantisse de 31 bits,
  exposant), produit par l'EMAC, inverse par une division 32/32 et une itération de Newton (environ 30 bits justes).
  Ils ont la dynamique des flottants de Rings : Q jusqu'à 5 000 000, fréquences de 10 Hz à 24 kHz.
- **`SemitonesToRatio`** de stmlib refait avec la même troncature en 1/256 de demi-ton ; les tangentes « dirty »,
  « fast » et « accurate » de stmlib avec leurs coefficients.
- **Tables** (`modal_tables.h`, `gen_modal.py`) : `lut_stiffness`, `lut_4_decades`, `lut_svf_shift`,
  `lut_fm_frequency_quantizer`, les accords, recalculés par les formules de Rings, arrondis en float32 (identiques
  aux tables de `resources.cc`, vérifié), puis en entiers. Sinus (4 097 valeurs) et limiteur doux calculés au
  premier usage.
- **Ce qui diffère du module, et pourquoi** :
  - bloc de 32 trames : les constantes « par bloc » (filtre de note, LFO des cordes) sont recalculées pour 32 ;
  - réglages éco : `(64 / polyphonie - 4) / 2` modes, `4 / polyphonie` cordes par voix, la table d'accords de Rings
    pour ce nombre de cordes ;
  - un mode du résonateur éteint (états sous 2^-18, sans entrée) n'est plus calculé ;
  - les effacements que Rings fait d'un coup (64 Ko de réverbe, lignes des cordes, tables) prendraient un bloc
    entier : la réverbe s'efface par morceaux (4 Ko par bloc, 16 blocs, le son passe sec en attendant, mais son
    pointeur et ses LFO avancent comme dans Rings) ; les lignes des cordes, seulement là où elles seront lues
    (paresseusement), aussi avec la dispersion ; les tables, en une vingtaine de blocs à la toute première note
    (silence, puis la note part) ;
  - le filtre anti-continu (pôle `1 - 10/48000`) garde la partie fractionnaire de `y × pôle` d'un échantillon à
    l'autre. Arrondi à chaque échantillon, il avait une zone morte de 2 400 LSB : un reste continu ne s'éteignait
    jamais et entrait sans fin dans les cordes (trouvé par la preuve : le modèle 5 s'écartait de Rings à 4 dB) ;
  - `20 × (DAMPING - 0,95)` (passage à la résonance infinie des cordes) borné à 1,0 sans déborder.

### 3.2 La passerelle (`modal.c`)

| Potard | Paramètre de la piste | Rings |
|---|---|---|
| PITCH | `p+0x14` | la tonique (`tonic`) : do 60 au centre (PITCH 64) |
| note du trig | `pmod` | la V/OCT (`note`) : note du trig − 60 ; un trig au do 60, PITCH au centre, joue le do 60 |
| COLOR | `p+0x16` | BRIGHTNESS |
| SHAPE | `p+0x18` (descripteur 0..5) | le modèle |
| SWEEP | `p+0x1a` | POSITION |
| CONTOUR | `p+0x1c` | STRUCTURE ; l'accord du modèle 4 : STRUCTURE × 10 avec l'hystérésis de 0,1 de `cv_scaler.cc` |
| DECAY | `p+0x24` | DAMPING |
| FUNC + SHAPE | FINE, `p+0x22` | la polyphonie : `0x4000` 1 voix (le défaut de FINE), `0x5000` 2, `0x6000` 4 |

- **Hauteur bornée** à MIDI 0..127 (la tonique et la note jouée) : Rings n'est défini que là (`SemitonesToRatio`
  lit hors de ses tables sous −128 demi-tons du la 440), et le module n'en sort jamais (tonique ≥ 12).
- **Strum** : le trig, au bloc où la voix du Cycles a `+0x38` (le bloc après le trig, comme ACID : l'OS finit
  l'ancienne note au bloc du trig).
- **Vélocité = force de la frappe**, pas volume : au bloc du trig (`+0x34`), la passerelle garde le gain que l'OS
  vient d'écrire en `0x40fe4cd0` (notes/54 §2), et le donne à l'excitateur (impulsion, rafale de bruit, enveloppes
  FM) au bloc suivant. Les deux gains de vélocité (`0x40fe4c90`, `0x40fe4cd0`) restent à 127 : la sortie de la piste
  n'est plus multipliée, et les voix qui résonnent encore gardent leur niveau quand une note douce arrive.
- **Sortie** : `ODD − EVEN`, comme Rings les mélange quand une seule prise est branchée. Indice : la réverbe du
  modèle 5 inverse sa sortie EVEN (`aux = -aux`), ce qui n'a de sens que si le mélange est une différence ; et en
  polyphonie, la `Part` forme elle-même chaque voix par `out - aux`. 1,0 de Rings = ½ pleine échelle, comme MACRO.
- **Pas d'enveloppe d'ampli** : la résonance s'éteint d'elle-même (DAMPING). GATE, PUNCH : sans effet.
- **État** : une `Part` par piste (95 Ko avec 4 cordes) et sa réverbe (64 Ko), à `0x46800000 + 0x28000 × piste`
  (§4), remise à neuf à la 1re note après un changement de machine (marque `'RNG1'` en `v+0x2c`, effacée par l'OS).
  Tampons de calcul en variables, pas sur la pile (l'interruption audio tourne sur la pile de la tâche
  interrompue ; MACRO et ACID restent sous 350 o).

### 3.3 Interface : la 15e machine

- **Huit machines ajoutées** (`gen_syntakt_engines.py`, `MAX_EXTRA = 8`) : 116 descripteurs (`0x1960` o). Au-delà
  de 7, les rangements passent à `gs.ROWS8` : rangées `+0x35960`, rangées CC `+0x35b40`, enregistrements `+0x35d20`
  à 80 o chacun (76 o et le drapeau) au lieu de 96, copie d'Attack `+0x35fa0` (fin `+0x35fec`, sous les tables des
  moteurs `+0x36000`) ; les détours passent à 3 Ko (2 040 o déjà avec ACID), les données au dernier Ko
  (`+0x33c00`). Jusqu'à 7 machines, rien ne bouge : les tweaks déjà testés gardent leurs octets (vérifié par les
  `--check` de `gen_acid_combos.py`, `gen_macro_syntakt.py`, `gen_macro.py`, `gen_acid.py`, `gen_syntakt_engines.py`).
- **Écran MACHINES** : 15 repères, deux lignes de 8 (`marks_row`), de x = 73 à 122, dans la moitié droite.
- **FUNC + SHAPE** : la mécanique du lo-fi de MACRO (notes/55 §8), généralisée (`fine` de `detours_asm`) : sur la
  piste MODAL, FUNC tenu et le potard SHAPE (5), l'entrée lue devient 16 (FINE), et les fonctions de l'objet
  d'interface de FINE deviennent celles de MODAL (`modal_poly_step` : un cran par tour, 1, 2, 4 ;
  `modal_poly_fmt` : « 1 », « 2 », « 4 » ; `modal_poly_draw` : ce texte dans la fenêtre de valeur, dessiné comme
  l'OS dessine le texte d'un paramètre). Le bloc de MODAL passe avant celui de MACRO.
- Image : celle de Metal (2). Noms : Brightness (BRIG), Model (MODL), Position (POS), Structure (STRC).

## 4. Place et mémoire

| Où | Quoi |
|---|---|
| charge utile `+0x79000` | code et tables de MODAL, 36 576 o (C et `modal_asm.S`) |
| charge utile `+0x83000` | ses variables, 11 432 o (sinus, limiteur, état des passerelles, tampons) |
| `0x46800000..0x468effff` | l'état des 6 pistes, 160 Ko chacune |

- Charge utile : 548 008 o (492 288 sans MODAL), rangée compressée en 252 929 o (230 083 sans) ; l'image
  décompressée finit en `0x401fd4c1` : **11 071 o de marge** sous `0x40200000`. Possible grâce au compresseur de
  notes/50 §10 (sans lui, MODAL ne tenait pas).
- `0x46800000..` `[HYP]` : libre. La zone d'échantillons de Model-TG s'arrête à `0x46700000` (`REGION_END`,
  `ST_PATCHES`), le Mo suivant est notre charge utile ; au-dessus, Model-TG écrit que le Cycles « registers a 4 MiB
  region at 0x4a400000 and nothing above it » (vue sans cache, soit `0x42400000..0x42800000`), et aucune opérande
  absolue du code de l'OS ne pointe dans `0x46800000..0x47ffffff` ni dans sa vue sans cache (relevé sur l'image
  désassemblée : deux faux positifs dans des données). La RAM fait 128 Mo (ACR0 couvre `0x40000000..0x47ffffff`).
  En émulation, MODAL n'écrit que là et dans ses variables, et rien d'autre n'y écrit (§6). À confirmer sur la
  machine.
- Déclaré dans `REGISTRY.md` (§6, `DECLARED` de `tools/registry.py`).

## 5. Charge

Instructions de MODAL par bloc (`test_modal.py`, piste seule, DECAY 100, une note pendant la mesure), avant et après
l'allègement en assembleur (§5.1) :

| Modèle | 1 voix | 2 voix | 4 voix |
|---|---|---|---|
| 0 modal | 26 212 → 20 930 | 30 978 → 26 598 | 25 552 → 22 764 |
| 1 cordes sympathiques | 29 349 → 22 694 | 34 139 → 27 959 | 43 817 → 32 971 |
| 2 corde | 17 000 → 16 199 | 29 993 → 28 886 | 55 918 → 48 534 |
| 3 voix FM | 10 569 → 10 316 | 17 553 → 17 507 | 32 467 → 32 407 |
| 4 cordes en accord | 29 203 → 22 547 | 33 960 → 27 777 | 43 633 → 32 779 |
| 5 corde et réverbe | 30 252 → 28 676 | 43 268 → 41 382 | 69 218 → 61 052 |

Sur le banc du cœur seul (`build/`, une note puis 20 blocs de mise en route), les voix inactives finissent de
s'éteindre et les écarts sont plus grands en 4 voix : cordes sympathiques 42 600 → 26 900, corde 51 600 → 36 900,
corde et réverbe 63 700 → 49 300. Le modal quand la position bouge (SWEEP tourné, ou modulé par un LFO) :
36 700 → 22 400.

TONE : 5 291 ; MACRO : 11 000 en médiane (notes/43 §8). Une piste MODAL coûte donc de 2 à 12 voix de TONE ; le
modal en 1 voix, 4. Ce sont des instructions : les cordes lisent des lignes de 16 Ko, hors du cache de 8 Ko `[HYP]`
plus lent encore ; les noyaux en assembleur enchaînent leurs produits sur plusieurs accumulateurs de l'EMAC, ce que
le décompte d'instructions ne montre pas. Le régulateur de charge des moteurs veille sur MODAL (il l'éteint en fondu
sous la surcharge, §6) ; une voix qui ne résonne plus n'est plus calculée par lui. Pistes : une ou deux MODAL avec
le reste.

### 5.1 L'allègement (demande de Maxime, 20/10/2026 : « allège en assembleur »)

Profil sur le banc (le cœur compilé pour le ColdFire, Unicorn, instructions par ligne de source) : la boucle des modes
(19 instructions par mode et par échantillon), les trois passes des cordes sans dispersion (50, 37, 37 par
échantillon et par corde), la boucle de la corde avec dispersion (environ 160), la réverbe (environ 380), le
limiteur (61), et en polyphonie la chaîne d'excitation des voix inactives.

- **`modal_asm.S`** : cinq noyaux, chacun les mêmes opérations de l'EMAC que le C qu'il remplace (la preuve compare
  la machine à `modal.c` compilé pour l'ordinateur sans eux : identique octet pour octet) :
  - `modal_mode_run` : un mode, position fixe, 14 instructions par échantillon (registres tenus d'un bout à
    l'autre, `ic2` dans un registre d'adresse pour `lea (a5, d2*2)`, déroulé par 8, produits sur trois
    accumulateurs) ;
  - `modal_mode_run_lin` : le même, l'amplitude qui avance d'un pas par échantillon (position qui bouge) ;
  - `modal_str_read`, `modal_str_damp`, `modal_str_write` : les trois passes des cordes sans dispersion (28, 22 et
    21 instructions par échantillon) ; le passage de la ligne par son début découpé par le C (l'échantillon qui
    écrit en 0 fait sa lecture depuis `DLINE - 1`).
  L'OS se sert des quatre accumulateurs le temps d'une fonction et les rend vides : ses fonctions de rendu comptent
  sur des accumulateurs à zéro (relevé dans l'image). Les noyaux les rendent vides aussi.
- **Ce qui change dans le C de référence** (revérifié contre Rings, `test_modal_dsp.py`) :
  - le DampingFilter : `damping × h0` et `damping × h1` d'abord, puis une seule somme (un produit après la somme
    avant), pour que la passe 2 tienne dans les registres : un LSB d'écart ;
  - position qui bouge : les amplitudes des modes au début et à la fin du bloc, interpolées linéairement, au lieu
    de la récurrence de Rings refaite à chaque échantillon : plus proche de Rings (36,3 → 41,1 dB dans le cas des
    4 potards qui bougent), la récurrence en virgule fixe accumulant ses erreurs ;
  - la chaîne d'excitation d'une voix inactive (son entrée est nulle) restée sous −108 dB pendant 8 blocs n'est plus
    calculée jusqu'à sa prochaine note (`exc_quiet`) : le peigne du pincement, arrondi par défaut, oscillait sur un
    LSB au lieu de s'éteindre ; plus proche de Rings aussi (cordes en 4 voix : 76,5 → 90,9 dB) ;
  - en C seulement, sans changer un octet : la réverbe (débuts de lignes en constantes, compression sans branche,
    décalages des LFO calculés quand ils changent), la boucle de la corde avec dispersion spécialisée pour des
    réglages fixes, le mélange des voix, l'entrée absente (`NULL`) au lieu d'un tampon de zéros parcouru.
- **Pas en assembleur, et pourquoi** : le limiteur et le filtre anti-continu (GCC en fait déjà 60 et 16
  instructions) ; la réverbe (22 accès au tampon par échantillon : environ 250 à la main contre 300) ; la corde avec
  dispersion (110 à 120 à la main contre 130 pour le C spécialisé, pour le noyau le plus risqué) ; la voix FM (le
  modèle le plus léger).
- Place : code et tables 36 576 o (32 580 avant) ; l'image finit en `0x401fd4c1`, 11 071 o de marge.

## 6. Preuves `[FAIT en émulation]`

### 6.1 Le cœur contre Rings (`tools/emu/test_modal_dsp.py`)

Rings compilé pour l'ordinateur depuis une copie de ses sources (clone épinglé) où ne changent que le bloc (32) et
les réglages éco ; le cœur compilé pour l'ordinateur. Après 20 blocs de silence, des notes ; `ODD − EVEN` comparés
sur toute la durée. 54 cas : les 6 modèles en 1, 2 et 4 voix ; les 4 potards qui bougent (5 modèles) ; 4 accords en
1, 2 et 4 voix ; chaque modèle à MIDI 0 et 127 ; DAMPING au maximum ; potards aux bouts. **Tous au-dessus de
35 dB, médiane 76,9 dB** ; le plus faible, le modal avec les 4 potards en mouvement (36,3 dB : la position qui
bouge à chaque échantillon). Les longues résonances modales (DAMPING 0,5 à 1,0, 12 s) : 72 à 86 dB, enveloppes
identiques.

Ce que la preuve a trouvé en route (corrigé) : la zone morte du filtre anti-continu (§3.1), le débordement à DAMPING
maximum, la réverbe dont les LFO ne suivaient pas ceux de Rings pendant son effacement, le passage `src_phase` de la
corde sous 11,7 Hz.

### 6.2 La machine dans l'OS (`tools/emu/test_modal.py`)

L'OS de la version 2.1 construit comme par `build.py`, le vrai code émulé (EMAC exacte, `emac.py`) :

1. démarrage : le décompresseur du bootstrap relit l'OS agrandi, le crochet reconstitue la charge utile (MODAL
   compris), pile et registres intacts ; MODAL à `+0x79000`, après ACID ;
2. interface (`test_model_tg_syntakt.interface`) : 15 machines, rangées et enregistrements de `ROWS8`, CC 16..19,
   changement de machine réel, écran MACHINES sur 2 lignes de 8, noms et potards ;
3. FUNC + SHAPE (`lofi_ui`, le code de l'interface de l'OS) : FINE sous FUNC + SHAPE sur MODAL seulement, un cran
   par tour (1, 2, 4), texte et fenêtre de valeur pixel pour pixel comme l'OS dessine un texte ; les machines 1..14
   et les 14 potards, avec et sans FUNC, comme sans MODAL ; le lo-fi de MACRO inchangé ;
4. son : ce que reçoit la passerelle à chaque bloc rejoué sur `modal.c` compilé pour l'ordinateur
   (`modal_machine_host.c`) : **sortie identique octet pour octet** (6 modèles, polyphonie 1, 2, 4, potards qui
   bougent, modèle verrouillé par pas, polyphonie changée, vélocité, hauteurs extrêmes, DAMPING maximum, machine
   locks) ; gains de vélocité à 127 ; la note jouée juste (fondamentale mesurée à 1 % près) ;
5. les autres machines (les 6 d'origine ; SDVtg, SYBit, MACRO, Sampler, ACID, SYSwm) : sortie identique à l'OS
   sans MODAL ;
6. régulateur : 5 pistes MODAL (et le Sampler) sous 97 % : toutes éteintes, jamais le Sampler ; sous une charge qui
   suit les voix calculées : une partie seulement ; les autres identiques ;
7. mémoire : MODAL n'écrit que dans ses variables, l'état de ses pistes, la voix, les gains et la sortie ;
   personne d'autre dans l'état de ses pistes ;
8. coût (§5).

Résultat : voir §6.3.

### 6.3 Résultats (20/10/2026)

- `test_modal_dsp.py` : 54 cas, **TOUT OK**, médiane 76,9 dB, le plus faible 36,3 dB (§6.1).
- `test_modal.py` complet : **81 vérifications, TOUT OK**. Entre autres : écran MACHINES, 15 repères, les 8 premiers
  en haut, de x = 69 à 122 ; FUNC + SHAPE → 43 (FINE), SHAPE seul → 112 (Model de MODAL) ; 21 cas de son
  identiques octet pour octet à `modal.c` sur l'ordinateur (crêtes de 0,011 à 0,487 de la pleine échelle) ;
  surcharge à 97 % : les 5 pistes MODAL éteintes, jamais le Sampler ; sous une charge qui suit les voix : une
  seule (piste 5), les autres identiques ; coûts du §5.
- Avec MODAL dans l'OS, les preuves qui construisent l'OS depuis `os.json` passent encore : `test_payload_pack.py`
  (charge utile de 548 008 o décompressée au démarrage, marge 12 636 o), `test_step_rec.py`, `test_mod_settings.py`.
- Après l'allègement (§5.1) : `test_modal_dsp.py` TOUT OK (médiane 76,9 dB, le plus faible 37,4 dB) ; `test_modal.py`
  complet, **81 vérifications, TOUT OK** (la machine, noyaux en assembleur compris, identique octet pour octet à
  `modal.c` compilé pour l'ordinateur sans eux) ; `test_payload_pack.py` (marge 11 071 o) ; MAIN OS
  `26aa6e43…7d33`.

## 7. À vérifier sur la machine

Flasher l'OS 2.1, puis :

1. Démarrage normal ; MACHINES : 15 repères sur 2 lignes de 8, MODAL le dernier, icône de Metal.
2. Une piste MODAL : chaque modèle (SHAPE 0 à 5) sonne à la bonne hauteur ; COLOR, CONTOUR, SWEEP, DECAY changent
   le son comme décrit ; DECAY en haut : les cordes résonnent presque sans fin.
3. FUNC + SHAPE : la fenêtre affiche 1, 2, 4 ; en 4 voix, des notes rapprochées se superposent.
4. Vélocité : une note douce frappe moins fort, les notes qui résonnent ne baissent pas.
5. Deux pistes MODAL avec les autres pistes jouant : craquements ? (la page System de Model-TG donne la charge).
6. Six pistes MODAL longtemps (un pattern), puis changer de projet : pas de gel (la mémoire `0x46800000..`).
7. Les autres machines comme avant (un moteur du Syntakt, MACRO, ACID, le Sampler).

## 8. La suite : le sample comme excitateur

Demandé par Maxime, pas dans cette version. Ce qu'il faudra :

- le navigateur de Model-TG refuse un sample sur une piste qui n'est pas Sampler (`preset_fail_hook` → `any_sampler`,
  machine 6 en dur, « Select sample machine first! ») ; il faudra une retouche de sa source (`MC_PATCHES`,
  `tools/gen_model_tg.py`) ou un détour devant `preset_fail_hook`, et le nom du sample rangé dans le son de la piste
  (`name_store`, comme le Sampler) ;
- MODAL lirait la case du sample (`slot_hash`, `track_slot`, notes/46 §4) et le rejouerait à sa vitesse, depuis le
  début, à chaque trig, comme entrée de Rings (`internal_exciter` à 0 : filtre d'excitation de l'entrée externe,
  détection de strum par le trig) ;
- les samples sont à 48 kHz dans la zone de Model-TG (vue sans cache `0x4a800000..`) : lecture d'un échantillon par
  trame, sans rééchantillonnage.

## 9. Chronologie

- 20/10/2026 : demande, choix de Maxime (§1), cœur, passerelle, machine, preuves ; OS 2.1.
- 20/10/2026 : « allège en assembleur » (Maxime) : `modal_asm.S` et les retouches du §5.1.
