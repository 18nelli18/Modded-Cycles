# 74 — Machine MODAL : un résonateur d'après Rings

Demande de Maxime (20/10/2026) : « un moteur Rings, fortement inspiré du Mutable Instruments Rings, le projet open
source d'Émilie Gillet », avec « les mêmes possibilités que le Rings, à part l'easter egg qui donne accès à un synthé
caché », et « la possibilité d'importer son propre sample en résonateur d'entrée, via le preset menu ». Tweak
`tweaks/model-cycles_OS1.13/31-syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-modal.json` (celui de l'OS, avec MODAL en
plus), générateur `tools/gen_modal.py`, sources `tools/machines/modal/`, preuves `tools/emu/test_modal_dsp.py` (le
cœur contre Rings) et `tools/emu/test_modal.py` (la machine dans l'OS). Plan de travail : `.pi/plans/` (non versionné).

## En bref

- **MODAL**, 15e machine, après ACID : 4 modèles de Rings (modal, cordes sympathiques, corde, cordes sympathiques en
  accord ; ni la voix FM ni la corde et réverbe, retirées le 22/10/2026 à la demande de Maxime, §5.4), la polyphonie
  1, 2 ou 4, l'excitateur interne de chaque modèle. Le
  synthé caché (`StringSynthPart`) n'y est pas.
- Le cœur est **la `Part` de Rings réécrite en virgule fixe** (le ColdFire n'a pas de FPU) : mêmes calculs, dans le
  même ordre, au même rythme, sur des blocs de 32 trames au lieu de 24. Comparé au code même de Rings compilé pour
  l'ordinateur : 54 cas, médiane 77 dB de rapport signal / écart, le plus faible 36 dB (§6).
- Réglages « éco » (choix de Maxime) : la moitié des modes, 4 cordes au lieu de 8.
- **Un sample comme excitateur**, choisi dans le menu des presets, depuis le 25/10/2026 (§8,
  [80](80-sample-excitateur-modal.md)) ; sans sample, l'excitateur interne.
- Lourd : de 9 400 à 42 000 instructions par bloc selon le modèle et la polyphonie, après trois passes
  d'allègement (§5.1 à §5.3) ; de 10 600 à 69 200 au départ. **Depuis le 27/10/2026 (§5.6, [81](81-budget-de-13-pourcent.md)
  §8)** : calculée à 24 kHz et allégée selon le choix de Maxime, sous 13 % du processeur dans tous les cas (6,0 à
  12,8 %) ; 3 voix au plus (2 pour la corde, SHAPE 2), 3 cordes sur une voix des modèles sympathiques.
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
| Modèles (22/10/2026) | les 3 de la façade de Rings et les cordes en accord ; « je ne veux pas du model corde + réverb ni de la voix FM » (§5.4) |

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
| SHAPE | `p+0x18` (descripteur 0..3) | le modèle : 0 modal, 1 cordes sympathiques, 2 corde, 3 cordes en accord (les modèles 0, 1, 2 et 4 de Rings, `SHAPE_MODEL`) |
| SWEEP | `p+0x1a` | POSITION |
| CONTOUR | `p+0x1c` | STRUCTURE ; l'accord des cordes en accord (SHAPE 3) : STRUCTURE × 10 avec l'hystérésis de 0,1 de `cv_scaler.cc` |
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
  modèle 5 de Rings inverse sa sortie EVEN (`aux = -aux`), ce qui n'a de sens que si le mélange est une différence ; et en
  polyphonie, la `Part` forme elle-même chaque voix par `out - aux`. 1,0 de Rings = ½ pleine échelle, comme MACRO.
- **Pas d'enveloppe d'ampli** : la résonance s'éteint d'elle-même (DAMPING). GATE, PUNCH : sans effet.
- **État** : une `Part` par piste (94 400 o avec 4 cordes), à `0x46800000 + 0x18000 × piste`
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
- Image : celle de Metal (2). Noms : Bright (BRIG), Model (MODL), Position (POS), Struct (STRC). Au départ
  « Brightness » et « Structure » : ils débordaient de l'écran (§5.2).
- **Le nom sous FUNC + SHAPE** : « Voices » (au départ « Pitch », le nom de FINE dans l'OS, relevé par Maxime).
  `knob_vec` pose ce nom dans le descripteur de FINE (`DESCN + 43 × 0x38 + 0x2c`) pour ce réglage, et remet
  « Pitch » à toute autre recherche de potard. Avec Model-TG, chaque lecture d'un enregistrement de machine
  (`tg_sync`) recopie les noms de sa table (`param_table`) dans `DESCN`, juste après `knob_vec` : elle repose
  ensuite le nom gardé dans `fine_name` (0 hors de ce réglage).

## 4. Place et mémoire

| Où | Quoi |
|---|---|
| charge utile `+0x79000` | code et tables de MODAL, 34 916 o (C et `modal_asm.S`) |
| charge utile `+0x86000` | ses variables, 12 084 o (sinus, limiteur, état des passerelles, tampons) ; à `+0x83000` jusqu'au 21/10/2026, déplacées pour laisser 52 Ko au code |
| `0x46800000..0x4688ffff` | l'état des 6 pistes, 96 Ko chacune (160 Ko avec la réverbe, jusqu'au 22/10/2026) |

- Charge utile : 560 948 o (492 288 sans MODAL ; les variables à `+0x86000` la font aller jusque-là), rangée
  compressée en 252 502 o (230 083 sans) ; l'image décompressée finit en `0x401fd316` : **11 498 o de marge** sous
  `0x40200000`. Possible grâce au compresseur de
  notes/50 §10 (sans lui, MODAL ne tenait pas).
- L'état d'une piste (la `Part`, 94 400 o) tient dans ses 96 Ko : vérifié à la compilation (`modal_track_fits`,
  `modal.c`), 3 904 o de marge.
- `0x46800000..` `[HYP]` : libre. La zone d'échantillons de Model-TG s'arrête à `0x46700000` (`REGION_END`,
  `ST_PATCHES`), le Mo suivant est notre charge utile ; au-dessus, Model-TG écrit que le Cycles « registers a 4 MiB
  region at 0x4a400000 and nothing above it » (vue sans cache, soit `0x42400000..0x42800000`), et aucune opérande
  absolue du code de l'OS ne pointe dans `0x46800000..0x47ffffff` ni dans sa vue sans cache (relevé sur l'image
  désassemblée : deux faux positifs dans des données). La RAM fait 128 Mo (ACR0 couvre `0x40000000..0x47ffffff`).
  En émulation, MODAL n'écrit que là et dans ses variables, et rien d'autre n'y écrit (§6). À confirmer sur la
  machine.
- Déclaré dans `REGISTRY.md` (§6, `DECLARED` de `tools/registry.py`).

## 5. Charge

Instructions de MODAL par bloc (`test_modal.py`, piste seule, DECAY 100, une note pendant la mesure) : au départ
(OS 2.1, `33802b6`), après la première passe en assembleur (§5.1, `813bfaa`) et après la deuxième (§5.2) :

| Modèle | 1 voix | 2 voix | 4 voix |
|---|---|---|---|
| 0 modal | 26 212 → 20 930 → **16 083** | 30 978 → 26 598 → **18 846** | 25 552 → 22 764 → **17 238** |
| 1 cordes sympathiques | 29 349 → 22 694 → **19 541** | 34 139 → 27 959 → **22 471** | 43 817 → 32 971 → **25 493** |
| 2 corde | 17 000 → 16 199 → **11 360** | 29 993 → 28 886 → **19 253** | 55 918 → 48 534 → **32 247** |
| 3 voix FM (retirée, §5.4) | 10 569 → 10 316 → 9 373 | 17 553 → 17 507 → 15 713 | 32 467 → 32 407 → 27 972 |
| 4 cordes en accord | 29 203 → 22 547 → **19 529** | 33 960 → 27 777 → **22 477** | 43 633 → 32 779 → **25 498** |
| 5 corde et réverbe (retirée, §5.4) | 30 252 → 28 676 → 21 022 | 43 268 → 41 382 → 28 936 | 69 218 → 61 052 → 41 943 |

TONE : 5 291 ; MACRO : 11 000 en médiane (notes/43 §8). Ce sont des instructions : les cordes lisent des lignes de
16 Ko, hors du cache de 8 Ko `[HYP]` ; les noyaux en assembleur enchaînent leurs produits sur plusieurs
accumulateurs de l'EMAC, ce que le décompte d'instructions ne montre pas. Le régulateur de charge des moteurs veille
sur MODAL (il l'éteint en fondu sous la surcharge, §6) ; une voix qui ne résonne plus n'est plus calculée par lui.

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

### 5.2 Optimisation intense (demande de Maxime, 21/10/2026)

Retours de Maxime sur l'OS du 20/10 (`26aa6e43…`) : « en model 2 et 5, mode polyphonie 4 voix le son est juste un
click nul » ; FUNC + SHAPE « change bien la polyphonie, mais à l'écran c'est affiché Pitch » ; « brightness ne
rentre pas dans l'écran faut le réduire, structure aussi ». Puis : « passe en phase d'optimisation intense.
Actuellement la machine peut prendre jusqu'à 16 % du CPU juste pour elle-même. Je veux qu'elle prenne 2× moins,
max 10 % ».

- **Le clic `[HYP]`** : la charge. Les modèles 2 et 5 en 4 voix coûtaient 48 500 et 61 000 instructions par bloc
  (47 000 à 63 000 avec des notes rapprochées, `build/modal_cf/dense.py`) ; à 1,54 cycle par instruction
  (notes/31 §6), de 45 à 58 % d'un bloc, en plus du reste de l'OS (environ 45 % avec des pistes, notes/31) : au-delà
  des seuils du régulateur (82 à 86 %, notes/27, 36), qui éteint MODAL dès l'attaque. Les modèles légers en 4 voix
  (33 000 à 41 000) passaient. Ce qui reste du clic sur la machine dira si la deuxième passe suffit.
- **Les noms** : la fenêtre du potard (`0x4001e40a`) coupe le nom aux espaces (`0x40096320`) et centre chaque mot
  (police `0x4014120c`) sur des cases de 8 points en x = 32 (dessin relu dans l'émulateur : « Position », 8 lettres,
  de x = 1 à 63 ; « Structure », 9, de 5 à 67 ; « Brightness », 10, de 1 à 71) : 8 lettres au plus par mot.
  `gen_syntakt_engines.check_names` refuse désormais un mot plus long (tous les noms existants passent).
- **Le cœur** (`modal_dsp.h`, `modal_asm.S`), profilé modèle par modèle, polyphonie par polyphonie
  (`build/modal_cf` : `lines2.py`, coût par ligne de l'appelant ; `dense.py`, notes rapprochées ; `modcost.py`,
  potard qui bouge ; `peak.py`, le bloc d'une nouvelle note ; `eq2.py`, ColdFire = ordinateur sur 36 cas) :
  - **les modes** (modèle 0) : les états `ic1`, `ic2` du filtre d'état variable de Rings tenus dans deux
    accumulateurs de l'EMAC pendant le bloc (8 bits sous le LSB), la sortie d'un mode `v1 = (ic1 + ic1')/2` sommée
    sur les modes (`sc.so`, `sc.sa` : `s[k] += amp ic1 / 2`, puis `o[k] = s[k] + s[k + 1]` une fois pour tous) :
    10 instructions par mode et par échantillon au lieu de 14, et plus proche de Rings (1 voix : 47,5 → 98,5 dB).
    Écartée en route : une forme de Chamberlin aux mêmes pôles et zéros (9 instructions), exacte à réglages fixes
    mais pas quand ils bougent (4 potards qui bougent : 41,1 → 22,9 dB). Ce noyau se sert du facteur d'échelle de
    `mac.l` (`<<`, `>>`), que l'OS du Cycles n'emploie pas (le code du Syntakt, si). `emac.py` décale le produit puis
    le tronque à 2^-39 `[HYP]` : pour `>>`, l'ordre ne change rien ; pour `<<`, si la machine tronquait avant de
    décaler, un produit différerait de 2^-39 au plus, et l'émulation ne serait plus exacte au LSB près (l'écart
    resterait sous −180 dB) ;
  - **les calculs par bloc** gardés tant que leurs entrées ne changent pas (`struct vcache`) : hauteur, filtre
    d'excitation, notes des cordes sympathiques, glissade, coefficients de dispersion (`disp_coefs`) ; les mêmes
    nombres ;
  - **le limiteur** : son gain au-dessus de 1,0 par une division 32/32 et une itération de Newton (`lim_gain`)
    au lieu du flottant maison à chaque échantillon (1 LSB d'écart) ;
  - **la chaîne d'excitation des cordes** : le filtre d'excitation sauté quand son entrée et son état sont nuls
    (sa sortie est nulle) ; le peigne du pincement, son filtre et l'anti-continu en un noyau (`modal_pluck`, hors
    de la bouffée de bruit) ;
  - **la corde avec dispersion** (modèles 2 et 5) : sans modulation du retard ni mélange de l'anti-continu (STRUCTURE
    de 31 à 103 environ), les passes de la corde simple, la lecture avec le passe-tout de l'étirement
    (`modal_str_read_ap`), l'anti-continu et le bruit de dispersion à part (leur état seul sert aux blocs suivants) ;
  - **la réverbe** : étage par étage sur le bloc (chaque ligne fait plus de 32 échantillons et chaque boucle passe
    par une ligne : les mêmes nombres), des pointeurs sans masque quand aucune prise ne repasse par le début du
    tampon (sinon, l'ancienne boucle), les passe-tout, l'entrée des branches et leur sortie en assembleur
    (`modal_rv_ap`, `modal_rv_in`, `modal_rv_tail` : GCC faisait 16 instructions par compression en 16 bits) ;
  - **la voix FM** : les enveloppes, qui ne dépendent pas des oscillateurs, dans une boucle à part ;
  - le filtre d'état variable passe-bas en assembleur (`modal_svf_lp`).
  Chaque noyau fait les mêmes opérations de l'EMAC que le C de référence ; tout le reste rend les mêmes octets
  (vérifié à chaque étape : `modal_host` d'avant et d'après sur les 6 modèles, 3 polyphonies, réglages fixes et
  mobiles).
- **Pas fait, et pourquoi** : la boucle des oscillateurs FM (GCC en fait 66 instructions par échantillon, autant qu'à
  la main) ; le limiteur en assembleur (environ 75 contre 80) ; une forme des modes plus courte (exacte seulement à
  réglages fixes).
- Place : code et tables 42 356 o (36 576 avant), variables à `+0x86000` (§4).

### 5.3 Les potards qui bougent (21/10/2026)

Mesuré après le §5.2 (`build/modal_cf/modcost.py` : un potard qui suit un LFO, un pas par bloc ; `peak.py` : le
bloc d'une nouvelle note) : le modal en 1 voix montait à 35 000 (BRIGHTNESS) et 41 000 (STRUCTURE, DAMPING)
instructions par bloc, en permanence, et à 43 000 sur le bloc d'une nouvelle note : les 30 modes refaits en flottant
maison (`reso_compute`, environ 900 instructions par mode, 22 opérations). La corde (modèles 2 et 5) avec
STRUCTURE qui bouge : 22 500 et 31 800 (les coefficients de dispersion refaits à chaque échantillon, comme dans
Rings).

- **`reso_compute`** : les opérations du flottant maison en ligne (`xmul_i`… : la même arithmétique que les
  fonctions, sans l'appel ni le retour d'une structure) et, toutes les grandeurs étant positives, sans le traitement
  du signe (`xmulp`, `xaddp`, `xrecipp`, `xtop`) ; deux passes : les fréquences des partiels et leur nombre sous
  0,49, puis les coefficients des seuls modes calculés (`(num + 1) & ~1`) ; `b = 1 − a1` au lieu de `e a1` (2 LSB au
  plus) ; la 1re passe et les tangentes gardées tant que fréquence et structure ne changent pas (BRIGHTNESS et
  DAMPING ne refont que les facteurs de qualité). `MAXMODES` passe de 64 à 32 (30 modes au plus en éco) : la place
  de ces tables.
- **`disp_apg`** : le gain du passe-tout de l'étirement, `−0,618 d / (0,15 + |d|)`, en virgule fixe (une division
  32/32 et une itération de Newton) : 8 LSB au plus de la formule exacte.
- **Les cordes qui bougent** (glissade des cordes sympathiques, filtre d'amortissement qui suit BRIGHTNESS ou
  DAMPING) : les trois passes en assembleur aussi quand le retard et le filtre avancent à chaque échantillon
  (`modal_str_read_mv`, `modal_str_damp_mv`, `modal_str_write_mv`).
- `str_block` en ligne, essayé : 3,6 Ko de code pour un millier d'instructions, seulement quand un potard bouge ;
  écarté (la place de l'image, 6 204 o de marge).

Résultats (instructions par bloc, 1 voix, le pire potard ; avant → après) : modal 41 000 → 26 100 (BRIGHTNESS :
35 100 → 17 400) ; corde 22 500 → 16 400 ; corde et réverbe 31 800 → 25 700 ; cordes sympathiques 27 900 → 27 200 ;
le bloc d'une nouvelle note du modal 43 000 → 28 900. Mêmes preuves (§6.3).

### 5.4 Quatre modèles (22/10/2026)

Question de Maxime : « dans le module Rings de Mutable Instruments il n'y en a que 3 normalement ». Réponse `[FAIT,
source]` : la façade en montre 3 (le bouton des modèles les fait tourner) ; un appui de 3 s (`kLongPressDuration`,
`rings/ui.cc`) bascule vers le modèle « Bonus! » du même rang (`rings/dsp/part.h`) : modal → voix FM, cordes
sympathiques → cordes en accord, corde → corde et réverbe, la LED clignotant ; présent dès le premier commit de Rings
(2016). Ce n'est pas l'easter egg (« Disastrous Peace », un autre synthé). Puis : « je ne veux pas du model corde +
réverb ni de la voix FM ».

- SHAPE 0..3 : modal, cordes sympathiques, corde, cordes en accord (`SHAPE_MODEL` dans `modal.c` : les modèles 0, 1,
  2 et 4 de Rings, numéros que garde le cœur ; la preuve contre Rings compare les mêmes). Un SHAPE plus grand (un son
  fait avant) est borné à 3.
- Retirés : la voix FM et son suiveur, la réverbe (ses noyaux `modal_rv_*`, son tampon), leurs tables
  (`gen_modal.py`) ; l'état d'une piste passe de 160 à 96 Ko (`TRACK_SIZE` `0x18000`) : 576 Ko pour les 6 pistes au
  lieu de 960, `0x46800000..0x4688ffff` (`REGISTRY.md`).
- Les 4 modèles gardent leurs octets : `modal_host` d'avant et d'après sur les 4 modèles, 3 polyphonies, réglages
  fixes et réglages qui bougent, identiques.
- `reso_process` gardé hors de `modal_process` (`noinline`) : sans la FM et la réverbe, GCC 13 le mettait en ligne
  et le modal coûtait de 2 à 10 % de plus dans l'OS (16 451 / 19 653 / 18 756 instructions par bloc en 1, 2, 4 voix,
  contre 16 044 / 18 840 / 17 043 une fois séparé ; 16 083 / 18 846 / 17 075 avant le retrait).
- Place : code et tables 34 916 o (44 308 avant) ; l'image finit en `0x401fd316`, 11 498 o de marge (6 204 avant).

### 5.5 Ce que coûte MODAL sur la machine (23 et 24/10/2026)

Relevé de Maxime (notes/77 §1) : une piste MODAL prend 30 % sur la page System de Model-TG, plus que les cinq autres
pistes ensemble. Le décompte d'instructions ne le montrait pas. Le modèle du coût sur la machine (`tools/emu/hwcost.py`,
notes/77 §3) le reproduit : à chaque bloc, MODAL relit en DDR2 presque tout le code qu'il exécute (180 à 400 lignes de
16 o, 23 cycles chacune), attend l'EMAC, et lit ses lignes à retard hors du cache.

Demande de Maxime (24/10/2026) : « commence par le point 1 » (notes/77 §6 : sans changer le son). Ce qui est fait :

- **Lecture et écriture des cordes, deux échantillons à la fois** (`modal_str_read`, `modal_str_read_mv`,
  `modal_str_write`, `modal_str_write_mv`) : la lecture d'un accumulateur juste après un MAC vers lui attend 3 cycles
  (MCF5441x RM §5.3.3) ; chaque échantillon y enchaîne 3 produits arrondis (Hermite) ou 2 (le peigne). Deux
  échantillons se croisent sur les 4 accumulateurs, l'arrondi de chaque `qmulr` entre avant son produit (la même somme
  exacte). Lecture : les deux fenêtres de 4 mots se recouvrent (5 mots lus). Écriture : les écritures et lectures
  dans l'ordre du C (le peigne peut lire ce que l'échantillon d'avant vient d'écrire). Le dernier d'un nombre impair,
  seul. Attentes de l'EMAC des cordes sympathiques et en accord : 2 900 → 1 500 cycles par bloc.
- **`modal_update` sans calcul quand rien ne bouge** : ni trig, ni potard, ni note depuis le dernier calcul complet,
  et ce calcul a redonné le même état (l'hystérésis de l'accord en place) ; seul `strum` retombe. 24 lignes de code de
  moins relues par bloc.
- Essayé, rejeté : tout MODAL en `-Os` (26,5 Ko au lieu de 35, mais autant de lignes exécutées par bloc et plus
  d'instructions : +1,5 à +3 points).
- Ce qui reste n'est pas exact à enlever : la saturation de l'EMAC (MACSR `0xa0`) coûte un cycle à chaque lecture
  d'accumulateur (table 3-18), 700 à 2 000 cycles par bloc ; un mode qui résonne peut dépasser la pleine échelle, la
  saturation reste.

Modèle du coût sur la machine (piste MODAL seule, les défauts de MODAL : COLOR 64, SWEEP 40, CONTOUR 36, DECAY 64 ;
en % d'un bloc à 250 MHz) :

| SHAPE | Avant | Après |
|---|---|---|
| 0 modal | 16,7 % | 16,3 % |
| 1 cordes sympathiques | 26,3 % | 25,4 % |
| 2 corde, 1 voix | 17,8 % | 17,5 % |
| 3 cordes en accord | 26,1 % | 25,0 % |
| 2 corde, 4 voix | 33,8 % | 33,4 % |

- Moins que les 2 points annoncés : les noyaux plus longs ajoutent des lignes de code relues à chaque bloc (environ
  30), qui reprennent la moitié du gain.
- **Preuves** : le banc ColdFire du cœur (`build/modal_cf/eq2.py`, 140 blocs : les 3 modèles à cordes, 1, 2 et 4 voix,
  réglages fixes et qui bougent) identique à l'octet près, chaque instruction des quatre noyaux exécutée (le dernier
  échantillon impair aussi, au passage de la tête d'écriture en 0) ; dans l'OS, l'ancien tweak contre le nouveau sur
  6 projets tirés au hasard (4 pistes MODAL, tous les modèles et polyphonies, trigs, potards tournés, changements de
  modèle, 160 blocs) : la sortie des 6 pistes identique ; `test_modal.py` complet.
- Plus de gain demanderait d'approcher le son (avec l'accord de Maxime) : lignes à retard sur 16 bits, moins de modes,
  ou la boucle par échantillon de la corde (SHAPE 2) en assembleur, qui ne sert qu'aux STRUCTURE très basses ou très
  hautes et aux réglages qui bougent.

### 5.6 Le budget de 13 % (26 et 27/10/2026)

Demande de Maxime (26/10/2026) : aucune machine ajoutée au-dessus de 13 % du processeur. Tout est dans la note
[81](81-budget-de-13-pourcent.md) §8 : Rings calculé à 24 kHz (R1), les allègements qui ne changent pas le son, puis le
choix de Maxime, « le plus léger » (27/10/2026) : lecture linéaire des cordes, cordes sympathiques sans peigne,
3 voix au plus (2 pour la corde, SHAPE 2, depuis le 28/10 ; pour tous les modèles à cordes le 27/10), 3 cordes sur
une voix des modèles sympathiques et une seule par voix au-delà, potards repris un bloc sur 16 (32 en 3 voix) quand
ils bougent sans trig, les voix tour à tour (81 §8.6). Charge au pire : 41,3 % → 12,8 %. Ce qui
précède dans cette note (tailles, polyphonie 1, 2 ou 4, 32 trames par bloc) décrit MODAL avant ce changement.

## 6. Preuves `[FAIT en émulation]`

### 6.1 Le cœur contre Rings (`tools/emu/test_modal_dsp.py`)

Rings compilé pour l'ordinateur depuis une copie de ses sources (clone épinglé) où ne changent que le bloc (32) et
les réglages éco ; le cœur compilé pour l'ordinateur. Après 20 blocs de silence, des notes ; `ODD − EVEN` comparés
sur toute la durée. Depuis le 22/10/2026, 41 cas : les 4 modèles en 1, 2 et 4 voix ; les 4 potards qui bougent ;
4 accords en 1, 2 et 4 voix ; chaque modèle à MIDI 0 et 127 ; DAMPING au maximum ; potards aux bouts (54 cas avec les
6 modèles). **Tous au-dessus de 35 dB, médiane 78,5 dB** (76,9 avec les 6) ; au départ, le plus faible, le modal avec les 4 potards en mouvement (36,3 dB : la position qui
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
   par tour (1, 2, 4), texte et fenêtre de valeur pixel pour pixel comme l'OS dessine un texte ; le nom « Voices »
   sous FUNC + SHAPE, « Pitch » dès la recherche suivante (MACRO comprise) ; les noms des potards de 8 lettres au
   plus par mot ; les machines 1..14 et les 14 potards, avec et sans FUNC, comme sans MODAL ; le lo-fi de MACRO
   inchangé ;
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
- Après l'optimisation du 21/10 (§5.2) : `test_modal_dsp.py` TOUT OK (médiane 76,9 dB, le plus faible 37,4 dB ; le
  modal en 1 voix de 47,5 à 98,5 dB) ; `build/modal_cf/eq2.py` : 36 cas (6 modèles, 1, 2, 4 voix, réglages fixes
  et réglages qui bougent), le cœur compilé pour le ColdFire identique à celui de l'ordinateur ; `test_modal.py`
  complet, **83 vérifications, TOUT OK** (coûts du §5) ; `test_payload_pack.py` (marge 7 667 o) ; MAIN OS
  `60badb3c…52bd`.
- Après les potards qui bougent (§5.3) : `test_modal_dsp.py` TOUT OK (médiane 76,9 dB) ; `eq2.py` 36 cas
  identiques ; `test_modal.py` complet, **83 vérifications, TOUT OK** ; `test_payload_pack.py` (marge 6 204 o) ;
  MAIN OS `4c37e00b…3154`.
- Quatre modèles (§5.4, 22/10/2026) : `test_modal_dsp.py` 41 cas TOUT OK (médiane 78,5 dB, le plus faible 41,1 dB) ;
  `eq2.py` (4 modèles, 1, 2, 4 voix, réglages fixes et mobiles) identiques ; `test_modal.py` complet, **83
  vérifications, TOUT OK** (dont « SHAPE au-delà de 3 : borné à 3 », 6 pistes MODAL dans `0x46800000..0x46890000`) ;
  coûts en 1, 2, 4 voix : modal 16 044 / 18 840 / 17 043, cordes sympathiques 19 501 / 22 425 / 25 365, corde
  11 322 / 19 203 / 32 175, cordes en accord 19 499 / 22 439 / 25 380 ; `test_payload_pack.py` (marge 11 498 o) ;
  MAIN OS `e5a333c9…cf77`.

## 7. À vérifier sur la machine

Flasher l'OS 2.1 (MAIN OS `e5a333c9…cf77`, 22/10/2026), puis :

1. Démarrage normal ; MACHINES : 15 repères sur 2 lignes de 8, MODAL le dernier, icône de Metal.
2. Une piste MODAL : chaque modèle (SHAPE 0 à 3) sonne à la bonne hauteur ; COLOR, CONTOUR, SWEEP, DECAY changent
   le son comme décrit ; DECAY en haut : les cordes résonnent presque sans fin.
3. FUNC + SHAPE : la fenêtre affiche « Voices » et 1, 2, 4 ; en 4 voix, des notes rapprochées se superposent ;
   la corde (SHAPE 2) en 4 voix sonne (plus seulement un clic). Les noms Bright, Model, Position et Struct
   tiennent dans l'écran.
4. Vélocité : une note douce frappe moins fort, les notes qui résonnent ne baissent pas.
5. Deux pistes MODAL avec les autres pistes jouant : craquements ? La page System de Model-TG donne la charge :
   noter le modèle, la polyphonie et le pourcentage, pour relier les instructions du §5 aux cycles.
6. Six pistes MODAL longtemps (un pattern), puis changer de projet : pas de gel (la mémoire `0x46800000..`).
7. Les autres machines comme avant (un moteur du Syntakt, MACRO, ACID, le Sampler).

### 7.1 Premier retour sur la machine (25/10/2026)

Firmware de la PR #112 (MAIN OS `84455c19…afd0`, avec §5.5 et le sample excitateur). Maxime : « Modal marche.
seulement, il prends beaucoup de charge, environ 30% en mode 4 voix. »

- `[FAIT]` MODAL marche sur la machine ; environ 30 % pour une piste en 4 voix (le modèle de Rings n'est pas précisé).
- `[FAIT en émulation]` le modèle du coût (`hwcost.py`, `build/modal4_model.py`) : MODAL seule en 4 voix, ses
  réglages par défaut, 5 notes à 12 blocs d'écart (les 4 voix sonnent ensemble), part de la piste :

| SHAPE | DECAY 64 | DECAY 110 |
|---|---|---|
| 0 modal | 18,1 % | 18,3 % |
| 1 cordes sympathiques | 31,1 % | 31,2 % |
| 2 corde | 39,2 % | 40,8 % |
| 3 cordes en accord | 31,1 % | 31,3 % |

- Le relevé est dans la fourchette du modèle (cordes sympathiques ou en accord, ou la corde avec moins de 4 voix qui
  sonnent). En 4 voix, MODAL calcule 4 résonateurs à la fois : pour SHAPE 1, environ 20 points d'instructions et
  d'attentes de l'EMAC, 11 points de défauts de cache (code relu, lignes des cordes). §5.5 n'y a gagné que 0,3 à
  1,1 point, comme prévu.
- `[À FAIRE]` le reste du §7 et le sample excitateur ([80 §6](80-sample-excitateur-modal.md)).

## 8. Le sample comme excitateur

Demandé par Maxime avec MODAL, fait le 25/10/2026 : [80](80-sample-excitateur-modal.md). Un sample choisi dans le
menu des presets d'une piste MODAL (trois tests « machine = 6 » de Model-TG acceptent aussi 14) est rejoué depuis le
début à chaque trig, à sa vitesse, comme l'entrée de Rings (`internal_exciter` à 0) ; sans sample, l'excitateur
interne.

## 9. Chronologie

- 20/10/2026 : demande, choix de Maxime (§1), cœur, passerelle, machine, preuves ; OS 2.1.
- 20/10/2026 : « allège en assembleur » (Maxime) : `modal_asm.S` et les retouches du §5.1.
- 21/10/2026 : retours de Maxime (le clic des modèles 2 et 5 en 4 voix, « Pitch », les noms trop longs), puis
  « phase d'optimisation intense » : §5.2.
- 21/10/2026 : les potards qui bougent (§5.3).
- 22/10/2026 : les 3 modèles cachés de Rings expliqués ; la voix FM et la corde et réverbe retirées (§5.4).
- 24/10/2026 : le coût sur la machine (Maxime : 30 % pour une piste) ; les cordes sans attente de l'EMAC, `modal_update`
  sans calcul quand rien ne bouge (§5.5).
- 25/10/2026 : le sample comme excitateur ([80](80-sample-excitateur-modal.md)).
- 25/10/2026 : premier retour sur la machine : MODAL marche, environ 30 % en 4 voix (§7.1).
- 26 et 27/10/2026 : le budget de 13 % : Rings à 24 kHz, allègements, choix de Maxime « le plus léger » (§5.6,
  [81](81-budget-de-13-pourcent.md) §8).
- 28/10/2026 : retour de Maxime (aucune différence entre 2 et 3 voix, la 1re note coupée par la 3e) : les voix tour à
  tour au lieu du motif de Rings, 3 voix pour les modèles sympathiques ([81](81-budget-de-13-pourcent.md) §8.6).
