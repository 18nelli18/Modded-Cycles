# 50 — Motifs génératifs : Random, Undo et une page GEN dans le séquenceur d'origine

Contribution de Combust (GitHub), tirée de son propre projet, mené du 04/10 au 07/10/2026 : un générateur de motifs
qui écrit dans le **séquenceur d'origine**, avec les voix d'origine (rythmes euclidiens, carte de styles de batterie,
mélodies et suites d'accords), sans rien changer au moteur audio. Le projet a été conçu sur Model-TG, que son auteur
garde sur sa machine : le tweak s'applique par-dessus `model-tg`. Tweak `49-generative.json` (`tools/gen_generative.py`,
sources `tools/machines/generative/`), preuve en émulation (`tools/emu/test_generative.py`). Adresses : VA de l'OS 1.13 ;
celles de Model-TG sont celles de sa v1.1.0 (commit `70b39dd`) telle que l'écrit `30-model-tg.json`.

## 0. En bref

Ce que le musicien obtient :
- **SETTINGS + PATTERN = Random**, depuis n'importe quel écran : nouveaux réglages pour chaque piste non verrouillée,
  et le pattern en cours est réécrit tout de suite (trigs, longueurs, vélocités, notes, accords).
- **SETTINGS + TEMPO = Undo**, un seul niveau : le pattern revient à l'état d'avant le dernier Random (trigs, notes,
  vélocités, longueurs, p-locks) avec les réglages GEN d'alors.
- **SETTINGS + PAGE** ouvre une page **GEN** plein écran : les pads choisissent la piste (un 2e appui sur la piste
  choisie la verrouille contre Random), les 12 potards règlent la piste choisie et la tonalité, les LED des trigs
  montrent les 16 premiers pas de la piste ; PUNCH / FUNC + PUNCH = Random / Undo ; RETURN ferme.
- Trois couches : **EUC** (rythmes réguliers sur un cycle de 1 à 16 pas), **MAP** (carte de 7 styles de batterie, de
  FOUR à JUNGLE, avec remplissage, chaos et accents) pour les pistes 1 à 4, **Tone / Chord** (mélodies et suites
  d'accords diatoniques, dans une tonalité commune) pour les pistes 5 et 6.

| | État |
|---|---|
| Écrire dans le pattern par les setters de l'OS (trigs, longueurs, vélocité, note, p-locks) | `[FAIT]` §1 |
| Touches, page plein écran, potards, pads et LED, à côté de Model-TG | `[FAIT]` §2 |
| Place pour le code : en place après Model-TG, un 7e bloc du cache de fichiers retiré | `[FAIT]` §4 ; risque analysé, `[HYP]` sur l'effet ressenti |
| Le générateur en C identique à la référence JS de l'auteur | `[FAIT]` §7 |
| Preuve en émulation (démarrage, touches, Random/Undo, page, LED, écran) | `[FAIT en émulation]` §7 |
| Essais sur la machine de l'auteur | v0 à v1.3 (Random, Undo, page GEN, rythmes EUC) et v2 (MAP) : fonctionnent ; v3 (notes et accords, 7e bloc) : pas encore essayée (§8) |
| Essai de Maxime, carte du flasher, guide | `[À FAIRE]` §9 ; statut `experimental` |

## 1. Ce que fait l'OS : écrire dans un pattern `[FAIT]`

Rien n'est écrit en mémoire brute pendant Random : tout passe par les setters de l'OS, qui préviennent l'interface et
le séquenceur (événement « pas modifié » `vtable[4](piste, &{0x400ff59c, pas})`, « piste modifiée » `{0x400ff5ac}`).
Tous s'appellent depuis la tâche de l'interface.

### 1.1 Objets

| Appel | Rend |
|---|---|
| `0x400cf866()` | contexte de l'interface |
| `0x4000f208(ctx)` | pattern en cours (objet de l'interface) |
| `0x4000cfcc(pat, t)` | objet de la piste t (`pat + 0x70 + 88 × t`, t borné à 0..5) |
| `0x4000d0dc(pat)` | `pat + 44`, réglages du pattern ; ses données (`vtable[10]`) : +20 longueur maître (mot), +25 mode d'échelle (0 pattern, 1 par piste), +26 vitesse |
| `objet->vtable[10]` | les 722 o de la piste (`0x400d639e` rend `objet + 16`) |

La piste (722 o, notes/32 §4) : +0 drapeaux des 64 pas (mots ; bit 0 = trig), +128 vélocité par pas (-1 = celle de la
piste), +192 longueur par pas, +512 octet de l'arpégiateur, +580 note par pas (-1 = celle de la piste, +712),
+713 longueur de la piste (mot, en mode par piste).

### 1.2 Setters

| Adresse | Arguments | Rôle |
|---|---|---|
| `0x40016402` | `(piste)` | longueur effective ; **tous les setters de pas ignorent un pas au-delà** |
| `0x400157d6` | `(piste, pas, masque)` | lit les drapeaux du pas |
| `0x40017b48` | `(piste, pas, 1)` | pose un trig de note (comme la grille) |
| `0x40017c4e` | `(piste, pas, 0)` | efface le trig ; l'OS remet alors la note à zéro et **efface ses p-locks** (`0x400164f2`) |
| `0x40016aec` | `(piste, n)` | longueur de la piste, bornée à **2..64** (1 devient 2) |
| `0x4000cba6` | `(réglages, mode)` | mode d'échelle 0 / 1, réapplique longueur et vitesse |
| `0x4000c9c4` | `(réglages, n)` | longueur maître : 2..64 en mode pattern, 1..1 024 en mode par piste |
| `0x400166c2` | `(piste, pas, vélocité)` | vélocité du pas, -1 = celle de la piste |
| `0x40016642` | `(piste, pas, note)` | note du pas : **note MIDI absolue** 0..127, -1 = celle de la piste ; l'écran affiche 60 comme « C5 » |
| `0x4001591e` / `0x4001646a` / `0x400164b0` | `(piste, pas, case[, valeur])` | p-lock : lire (-1 = aucun) / poser (rend un booléen) / effacer |

Convention d'appel : arguments en mots longs empilés de droite à gauche, l'appelant dépile, résultat dans `d0`,
**pointeurs compris**. `m68k-linux-gnu-gcc` lit un pointeur rendu dans `a0` : toutes les fonctions de l'OS qui rendent
un pointeur sont déclarées rendre un entier, puis converties (sinon plantage, trouvé sur le premier essai en émulation).

### 1.3 P-locks, notes et machine Chord

- Une case de p-lock est le champ +4 de l'entrée de la table des paramètres (`0x4010dce0`, 76 entrées de 56 o) :
  9 machine, 10 PITCH, 11 COLOR, **12 SHAPE**, 13 SWEEP, 14 CONTOUR, 18 DECAY… La valeur est le mot 8.8 du paramètre :
  **valeur << 8**. Chaque pas a 34 mots dans le magasin des p-locks (33 cases, -1 = aucune, plus leur nombre).
- Hauteur jouée = note du pas + (PITCH − 64) + (FINE − 64)/32 demi-tons (`0x400a7f66`) : un PITCH de piste autre que 64
  transpose tout.
- **Machine Chord** (`0x400aae88`) : la note du pas est bornée à 0..96 et devient la fondamentale, en position
  fondamentale ; **SHAPE est le numéro de l'accord, 0 à 37** (38 accords, dans l'ordre du manuel ; seul l'octet entier
  est lu), table d'intervalles `0x4012142c + 16 × numéro`. COLOR près de 32 (le défaut) donne l'accord complet ; on n'y
  touche pas. Un p-lock change l'accord net sur son pas (`0x400583da`), là où le potard glisse par les accords voisins.

| SHAPE | Accord | Demi-tons |
|---|---|---|
| 3 | mineur | 0 3 7 12 |
| 4 | majeur | 0 4 7 12 |
| 7 | m7 | 0 3 7 10 |
| 8 | M7 (septième de dominante) | 0 4 7 10 |
| 10 | Maj7 | 0 4 7 11 |
| 17 | mb5 (quinte diminuée) | 0 3 6 12 |
| 19 | m7b5 (demi-diminué) | 0 3 6 10 |

## 2. Touches, page, potards, pads et LED `[FAIT]`

### 2.1 Touches

- Tous les lecteurs de touches passent par l'accesseur `0x4007240c` (code de touche en +12 de l'événement, drapeaux en
  +16 : bit 0 appui, 3 répétition, 5 appui long). Model-TG le remplace par `jmp key_hook` (`0x401ae968`) et prend
  SETTINGS comme modificateur : `set_held` (`0x401b235c`), `mod_used` (`0x401b2360`, le relâchement de SETTINGS
  n'ouvre alors pas le Config Menu).
- Codes : PATTERN 3, PUNCH 6, RETURN 12, SETTINGS 13, TEMPO 14 (déduit : FUNC + 14 = tap tempo, `0x4006dc82`),
  PAGE 15. Model-TG prend SETTINGS + PRESET, PUNCH, RECORD, RETRIG, RETURN et les touches de pas ; SETTINGS + PATTERN,
  TEMPO et PAGE sont libres. Aucun n'est une touche de transport : un raté ne lance ni n'arrête la lecture.
- Pour prendre une touche, on fait comme Model-TG : bit 3 (répétition) mis dans l'événement, puis code 0 pour cette
  lecture et les suivantes, appui et relâchement.
- Le travail se fait **dans la tâche de l'interface**, par un message de type 6 (le `sv_post` de Model-TG) :
  `0x40001fba(0x404a9154, &msg)`, rappel en +0x10, gestionnaire `0x4002f136`, +0x18 remis à 0 par la tâche une fois le
  rappel fait (`0x40008236`). L'accesseur est appelé de l'intérieur de n'importe quelle vue : on n'y écrit rien.

### 2.2 Page plein écran

Comme les pages de Model-TG : un clone de `DrumSelect` (constructeur `0x400a22b0`, 0xd0 o, `new` `0x400802e0`) avec
une copie de sa table virtuelle où six entrées changent (deux destructeurs, touches +0x10, dessin +0x18, potards +0x4c
et leur entrée +0x60). Elle est empilée sur le contrôleur de vues racine (`0x400060d8(0x400d0974())`) par
`0x4007700e`, avec le bloc de contrôle `{0x401000c4, 1, 1, page}` ; fermeture différée `0x40076126`.

- Dessin : chaque vue de la pile dessine, la nôtre en dernier ; elle efface les 128 × 64 points (`0x40070dea`),
  écrit avec `0x40071a04` (petite police `0x40ea14cc`) ; **y = 0 en bas** (notes/39 §2). Redessin : `0x40076082`.
- Potards : `0x4006f73a(év, 1, 1)` donne le nombre de crans ; index 1 = DATA, index 2 à 13 = potards 1 à 12. Sur la
  page, aucun cran n'atteint un paramètre du son.
- Pads : ce ne sont pas des touches. Ils arrivent à la méthode `0x4001d180` de `PadsView`, que Model-TG remplace par
  `jmp pad_hook` (`0x401b3ffc`). FUNC + pad fait apparaître la vue des mutes, qui prend les pads avant nous : il garde
  son sens d'origine (essai de l'auteur, §8).

### 2.3 LED

Image des LED `0x40006a4a` : les demandes de l'image sont effacées, puis `0x40076ca2(racine)` fait peindre chaque vue
(de haut en bas), puis tout ce qui n'est pas demandé s'éteint. **La première demande d'une LED dans une image gagne**
(`0x40005f86`, `0x40005fe6`) : en passant avant `0x40076ca2`, on tient les 16 LED des trigs (`0x4000608c`) et les
6 des pads (`0x400060bc`), couleur `0x404a8cb8`.

## 3. Conception

### 3.1 Random et Undo

- **Random** (tâche de l'interface) : photo pour Undo, réglages tirés pour chaque piste non verrouillée, génération,
  puis par piste : mode par piste (`0x4000cba6(…, 1)`), longueur 64 pour ouvrir les 64 pas, trigs posés ou effacés
  **seulement là où ils changent** (un trig gardé garde sa note et ses p-locks), vélocités, notes et p-locks SHAPE,
  puis la vraie longueur de la piste (le cycle, 2 au moins) ; longueur maître 64.
- Le pattern passe donc en mode d'échelle par piste, longueur maître 64.
- **Undo**, un niveau, seulement pour le dernier Random : la photo (sur le tas, environ 30 Ko, allouée une fois) garde
  les 6 pistes (722 o), les 6 × 64 × 33 cases de p-lock (lues par `0x4001591e`), les 48 réglages GEN, les pistes
  générées, le mode d'échelle et la longueur maître. Retour : trigs par les setters, puis copie des octets `[0, 712)`
  de chaque piste (drapeaux, vélocités, longueurs, conditions, notes…), puis les p-locks qui diffèrent, reposés ou
  effacés par les setters, puis longueurs, mode et longueur maître, dans cet ordre (la borne de la longueur maître
  dépend du mode).
- La copie brute suppose que les données de la piste vues par l'interface sont celles que lit le séquenceur (la banque
  `0x406fa040`). `[HYP]` : Model-TG (slide trigs) et l'émulation le montrent, notes/32 §10 disait le contraire avant
  la correction de son adresse de banque ; l'auteur utilise Undo sur sa machine sans problème signalé.

### 3.2 Couche 2 : rythmes EUC

- **Colliers binaires** : pour chaque cycle n de 1 à 16 et chaque nombre de coups k, toutes les rotations distinctes ;
  **8 923 masques** de 16 bits, construits au premier Random dans le tas (17 846 o, plus 27 Ko de travail rendus
  aussitôt ; environ 30 millions d'instructions, 0,1 à 0,25 s une seule fois).
- **Régularité** : classement du plus régulier au plus groupé par S₁, S₂, …, où S_w est la somme des carrés des
  longueurs de toutes les fenêtres de w écarts consécutifs ; l'index 0 est toujours le rythme euclidien, le dernier un
  seul bloc. Chaque collier est rangé dans la rotation qui recouvre le mieux son voisin : un cran de régularité change
  au plus 8 pas sur 16 (moyenne 3,26).
- Potards : **CYC** (cycle 1 à 16, longueur native de la piste ; un cycle de 1 est écrit sur 2 pas), **DEN** (coups),
  **EVN** (régularité), **SFT** (décalage). Le cycle est répété sur les 64 pas.
- **Style de densité** (global) : **EVEN** (colliers ci-dessus) ou **NEST** (les pas sont classés en coupant toujours
  le plus grand écart : 0, 8, 4, 12, 2…, et 16 positions de régularité vers un bloc) : un cran de densité change
  exactement 1 pas, un cran de régularité au plus 2, au prix de 16 rythmes par densité au lieu de tous.
- **Random** tire par rôle de piste :

| Piste | Coups pour 16 pas | Régularité au plus | Décalage qui met un coup sur |
|---|---|---|---|
| 1 Kick | 2 à 6 | 6 | le pas 1, 15 fois sur 16 |
| 2 Snare | 1 à 4 | 4 | le pas 5 (2e temps), 11 fois sur 16 |
| 3 Metal | 4 à 12 | 24 | le pas 1, 2 fois sur 16 |
| 4 Perc | 2 à 7 | 24 | le pas 1, 4 fois sur 16 |
| 5 Tone | 2 à 8 | 40 | le pas 1, 8 fois sur 16 |
| 6 Chord | 1 à 4 | 12 | le pas 1, 10 fois sur 16 |

  Cycles surtout de 16 (34/64) et de 8 (12/64), parfois impairs ; régularité = la plus petite de trois tirages ;
  une piste est retirée (16 fois au plus) si ses 16 premiers pas copient ceux d'une autre. Sur 2 000 tirages : toutes
  les lignes différentes, kick sur le premier temps plus de 90 % du temps, snare sur le 2e temps plus de 60 %.

### 3.3 Couche 1 : carte de styles MAP (pistes 1 à 4)

- **Carte originale** de 7 styles de 32 pas : **FOUR → HOUSE → 2STEP → ELECTRO → BOOMBAP → BREAKS → JUNGLE**, une
  force par pas (niveaux 1 à 9, × 28) pour Kick, Snare, Metal et Perc. Elle n'est pas tirée de Grids (§10).
- **STY** (0 à 96, pour tout le kit) : 16 pas de fondu linéaire entre deux styles voisins.
- **FIL** (0 à 127, par piste) : un pas sonne si sa force dépasse 255 − 2 × FIL ; monter le remplissage ne fait
  qu'ajouter des coups.
- **CHS** (0 à 127, pour tout le kit) : ± (r − 128) × CHS / 64, r tiré **à chaque pas quel que soit CHS**, pour que
  les tirages ne se décalent jamais.
- **SFT** : rotation de la ligne de 32 pas. La carte couvre les 64 pas ; à CHS 0, la 2e moitié répète la 1re.
- **Vélocité** = 24 + force × 100 / 256 : 122 au niveau 9 (accent), 45 au niveau 2 (ghost), par `0x400166c2`.
- Random : un style pour le kit (0 à 96), un chaos bas (le plus petit de trois tirages, 48 au plus), un remplissage par
  rôle (Kick 56–80, Snare 56–84, Metal 48–100, Perc 30–80), parfois un décalage d'une croche.

### 3.4 Couche 3 : Tone (piste 5) et Chord (piste 6)

- Tonalité commune : **ROOT** (C à B) et **SCALE** : MAJ, MIN, DOR, MIX, HMI (mineur harmonique), PMA, PMI
  (pentatoniques). Défaut : do mineur.
- **Tone** : chaque trig tire un degré, en triangle autour de **BIA** (centre) avec la largeur **SPR** ; avec la chance
  **STP**, il avance par degrés (± 2) ; avec la chance **DJV** (déjà vu), à partir du 9e trig, il reprend la note
  jouée 8 trigs plus tôt. Note de base 60.
- **Chord** : fondamentales pondérées par fonction (I 6, ii 3, iii 2, IV 5, V 5, vi 4, vii 1 ; gammes de 5 notes :
  5, 1, 3, 4, 2), ou uniformes avec la chance **ADV** ; qualité diatonique, triade ou septième avec la chance **CPX** ;
  **DJV** reprend l'accord 4 trigs plus tôt ; **OCT** de −2 à +2 octaves. Base 48. La fondamentale va dans la note du
  pas (`0x40016642`), la qualité dans un **p-lock SHAPE** (case 12, `numéro << 8`) : majeur 4, mineur 3, mb5 17,
  Maj7 10, M7 8, m7 7, m7b5 19.
- Chances : `r < v + v/64` (0 = jamais, 127 = toujours). Une note hors de 0..127 bouge d'une octave : elle reste dans
  la tonalité.
- Les notes suivent le tirage : Random donne de nouvelles mélodies et suites sans toucher aux potards de notes.
- Limite : les p-locks SHAPE supposent que la piste 6 joue la machine Chord (défaut d'usine). Sur une autre machine,
  ils font bouger son SHAPE (0..127) à chaque pas.

### 3.5 La page GEN

| Commande | Effet |
|---|---|
| SETTINGS + PAGE | ouvre (ou ferme) la page ; laissé à Model-TG si l'une de ses pages est ouverte |
| pad, DATA | choisit la piste ; un 2e appui sur le pad de la piste choisie la verrouille contre Random (ou la déverrouille) ; les pads ne jouent pas |
| FUNC + pad | sens d'origine (vue des mutes) |
| potards 1–4 | piste EUC : CYC, DEN, EVN, SFT ; piste MAP : STY (kit), FIL, CHS (kit), SFT ; écrits tout de suite |
| potard 5 | style de densité EVEN / NEST (pistes EUC générées et non verrouillées) |
| potard 6 | piste 1 à 4 choisie : EUC ou MAP |
| potards 7–10 | Tone : SPR, BIA, STP, DJV ; Chord : ADV, CPX, DJV, OCT |
| potards 11, 12 | ROOT, SCALE (réécrivent Tone et Chord générés et non verrouillés) |
| PUNCH / FUNC + PUNCH | Random / Undo (sur la page seulement ; ailleurs, PUNCH garde son sens) |
| RETURN | ferme ; l'écran d'origine revient tel quel |
| LED des trigs, bande à l'écran | les 16 premiers pas de la piste choisie, lus dans le pattern |

- Une piste compte comme « générée » après Random ou un réglage sur la page : un réglage global (STY, CHS, style de
  densité, tonalité) ne réécrit jamais une piste faite à la main.
- Écran : en-tête (GEN, piste, verrou, style ou tonalité), un trait, les libellés et valeurs de la rangée de potards
  tournée en dernier (rythme ou notes), la bande des 16 pas avec les temps marqués.

### 3.6 Hasard

Graine = hachage de la précédente et du minuteur libre DTIM0 (`0xfc07000c`, 135,168 MHz) à chaque Random ; chaque
usage a son propre flux (xorshift 32 bits). La même graine et les mêmes réglages donnent toujours le même pattern :
c'est ce que comparent les preuves.

## 4. Où vit le code, place prise

### 4.1 En place après Model-TG

- Model-TG v1.1.0 ajoute à l'image un bloc exécuté en place en `0x401ab750..0x401bf8c0`, dans les blocs 0 à 5
  (16 Ko chacun) du **cache du système de fichiers** (`0x401ab750..0x401eb750`), qu'il retire au cache en réécrivant
  deux constantes de son initialisation (`0x400792f2`, `0x400792bc`, notes/31). Il reste 16 016 o libres dans son
  bloc 5.
- Notre partie est ajoutée **à la suite, en place**, en `0x401bf8c0` (`append` avec `dest` = `at`), et **un 7e bloc**
  (le 6, `0x401c3750..0x401c7750`) est retiré par la même formule que Model-TG (`nres` = 7) : 32 400 o au total, jusqu'à
  `0x401c7750`.

| VA | Ancien | Nouveau | Rôle |
|---|---|---|---|
| `0x400792f2` | `401eb7c8` | `401eb7dc` | tête de la liste LRU = entrée 7 |
| `0x400792bc` | `401eb7ec` | `401eb800` | début de la boucle des liens arrière = entrée 8 + 16 |

- **Risque** (lu dans le code, pas émulé) : chaque entrée de 20 o (+4 compteur, +8 valide, +12/+16 liens) ; une entrée
  retirée n'est jamais atteinte et le parcours par index (`0x40079310`) la saute. Le cache **n'écrit pas en différé** :
  l'écriture (`0x40079696`) va tout de suite à l'eMMC, l'éviction n'écrit rien ; aucune perte de données possible,
  usure de l'eMMC inchangée. Le Sampler de Model-TG lit ses échantillons sans passer par lui. Le `nres <= 6` de son
  `build.py` est un budget de taille, pas une vérification : rien d'autre ne dépend du nombre de blocs. Une opération
  de fichiers épingle 3 à 4 blocs au plus, sous un verrou : 9 blocs sur 16 au lieu de 10 laissent de la marge.
  `[HYP]` effet ressenti : au plus quelques relectures de 16 Ko en parcourant de gros dossiers ou en chargeant un projet.
- **Démarrage** : le crochet de Model-TG (`boot_extra_hook`, `0x401bf3d8`, appelé en `0x40000530`) remet le BSS à zéro
  sauf `[0x401ab750, 0x401bf8c0)` : notre code serait effacé. Notre `ours_boot` (le `jsr` pointe sur lui, écriture en
  `0x40000532`) écrit en RAM la fin de notre partie (`ours_res_end`) dans l'opérande de cette borne (`0x401bf402`), puis
  saute au crochet de Model-TG, inchangé. Les caches ne sont pas encore actifs à ce moment (CACR écrit en
  `0x40000542`) ; notre `.bss`, au-dessus, est remis à zéro par le même effacement, avant le montage du système de
  fichiers.
- Taille (v3 du 04/10/2026, `m68k-linux-gnu-gcc` 13.3) : environ 13,1 Ko dans l'image et 1 Ko de `.bss`, soit
  environ 18 Ko encore libres avant `0x401c7750` ; `gen_generative.py` affiche les chiffres exacts.
- **Tas** (`0x400802e0`) : les masques des colliers (17 846 o), le résultat de la génération (1,5 Ko) et la photo
  d'Undo (environ 30 Ko), alloués au premier usage et gardés ; la page (0xd0 o) et son bloc de contrôle à chaque
  ouverture, rendus par l'OS à la fermeture, comme pour Model-TG.

### 4.2 Crochets

| Où | Avant | Après | Contrat |
|---|---|---|---|
| `0x40000532` | `401bf3d8` (Model-TG) | `ours_boot` | élargit la borne de l'effacement, puis le crochet de Model-TG (ne revient pas) |
| `0x4007240e` | `401ae968` (Model-TG) | `ours_key_hook` | `(KeyEvent *)` en 4(sp), code dans `d0`, seulement `d0/d1/a0/a1` touchés ; ce qui n'est pas à nous va à `key_hook` de Model-TG, pile intacte |
| `0x4001d182` | `401b3ffc` (Model-TG) | `ours_pad_hook` | page ouverte : l'événement est à nous (`d0` = 1), la méthode d'origine (son, choix de piste) ne tourne pas ; sinon `pad_hook` de Model-TG |
| `0x40006a76` | `jsr 0x40076ca2` | `jsr ours_led_frame` | page ouverte : nos 22 LED demandées, puis `0x40076ca2` |

Trois de ces crochets réorientent un `jmp`/`jsr` déjà écrit par Model-TG : leur ancien contenu est celui de Model-TG,
et le tweak s'applique après lui (ordre 44 > 30). `gen_generative.py` vérifie dans `30-model-tg.json` chaque octet de
Model-TG dont ils dépendent (fin du bloc, borne et suite de l'effacement, début de `key_hook`, `set_held`, `mod_used`,
`rtg_on` `0x401b6d8c`, `sle_on` `0x401bcaec`, `pad_hook` et sa table des pads, `mm_obj` `0x401b2088`, les deux
constantes du cache à 6 blocs) : une autre version de Model-TG fait échouer la génération au lieu de donner un firmware
faux.

## 5. Conflits

- **Requiert `model-tg`** : le code s'accroche à Model-TG et se place à la fin de son bloc.
- **Incompatible avec `model-tg-st`, tous les `syntakt-tg-*`, `syntakt-tg-meter` et `syntakt-tg-profile`** : ils
  réécrivent aussi `0x40000532` (crochet de démarrage des moteurs du Syntakt) et ajoutent leur charge utile en
  `0x401bf8c0`. Un chaînage serait possible (notre `ours_boot` appellerait leur crochet), pas fait.
- `[FAIT]` relevé sur tous les tweaks du dépôt : à part Model-TG, aucun n'écrit aux adresses ci-dessus (`6ch-usbup`,
  drumkilla, `arp`, `trig-hold`, `tempo-max`, `boot-anim`). L'accroche de l'arpégiateur dans la méthode des pads
  (`0x4001d25e`) n'est pas atteinte quand la page est ouverte, ce qui est voulu (les pads ne jouent pas).
- Données : Random ne touche pas l'octet +512 (arpégiateur) ; un trig effacé perd son bit 12 (slide trig de Model-TG)
  comme avec la grille, et Undo le rend.

## 6. Le tweak `49-generative.json`

- `id` `generative`, `order` 49, `requires` `["model-tg"]`, `conflicts` ci-dessus. Expérimental : pas encore dans le
  flasher (§9), donc pas de carte ni de `status`.
- 6 écritures (les quatre crochets, les deux constantes du cache) et un `append` en place en `0x401bf8c0`, sans
  relocalisation. `symbols` exporte l'état utile aux preuves.
- MAIN OS de `model-tg,generative` : `41f44b960a588059e1631e0f9dabce9589dd356ce996d81555b861055addb78e` (BUILD.md).

## 7. Preuve en émulation

### 7.1 Le générateur `[FAIT]`

Le générateur en C (`tools/machines/generative/`) est un portage de la référence JavaScript de l'auteur (non versée
ici). Dans son projet, les deux ont été comparés octet pour octet : 20 000 jeux de réglages (trigs, longueurs,
vélocités, notes et accords, les deux styles de densité, les trois couches) et 20 000 tirages de Random. Dans ce dépôt,
cette comparaison devient des vecteurs dorés produits par le JavaScript (`tools/machines/generative/vectors/`) : la
preuve les compare à l'exécutable hôte du même cœur C (`host/gen_cli.c`), puis compare ce que le tweak écrit dans
l'émulateur à ce même exécutable.

### 7.2 Le tweak (`tools/emu/test_generative.py`) `[FAIT en émulation]`

Image `model-tg` + `generative` construite par `build.py`, vrai code de l'OS et de Model-TG ; objets de l'interface
factices dont les données **sont** les vraies adresses de la banque (`0x406fa040 + pattern × 30 710 + 722 × t`), sur
lesquelles tournent les vrais setters de l'OS.

| Test | `model-tg` seul | `model-tg` + `generative` |
|---|---|---|
| Démarrage, de `0x40000530` à `0x4000053a`, BSS rempli au hasard | bloc de Model-TG gardé, le reste remis à zéro | bloc de Model-TG **et notre code** gardés, le reste remis à zéro (notre `.bss` compris) |
| PATTERN seul | code 3 | code 3, rien posté |
| SETTINGS + PATTERN / SETTINGS + TEMPO | à Model-TG et à l'OS | pris à chaque lecture, appui et relâchement ; un seul message de type 6 ; pas de Config Menu au relâchement de SETTINGS |
| SETTINGS + TRACK, SETTINGS + touche de pas | Model-TG | Model-TG, inchangé |
| Random (rappel dans la tâche de l'interface) | — | réglages tirés = référence ; trigs sur 64 pas, longueurs, vélocités, notes et p-locks SHAPE (`<< 8`) = référence ; mode par piste, longueur maître 64 ; les trigs effacés perdent leurs p-locks |
| Undo | — | les 30 710 o du pattern **identiques** à avant Random, magasin des p-locks compris |
| SETTINGS + PAGE | à Model-TG | page empilée (clone de `DrumSelect`, exactement 6 entrées de la table virtuelle changées), relâchement de PAGE pris ; laissé à Model-TG si sa page de retrig est ouverte |
| Pads sur la page | son et choix de piste | piste choisie, verrouillée au 2e appui ; la méthode d'origine ne tourne pas ; une piste verrouillée garde ses trigs au Random |
| Potards sur la page | paramètres du son | tous les crans pris ; un réglage ne réécrit que la piste choisie (= référence) ; STY réécrit les pistes MAP générées non verrouillées ; ROOT réécrit Tone et Chord (= référence) |
| Image des LED (`0x40006a4a` entier) | LED de l'OS | nos 16 + 6 demandes avant que les vues peignent ; le reste éteint |
| Dessin dans un tampon d'écran | — | bande des 16 pas, libellés et valeurs sans chevauchement, bas de l'écran libre |
| RETURN | — | fermeture différée, destructeurs d'origine, LED repeintes ; les touches retournent à Model-TG |
| Accès mémoire | — | aucun hors des zones prévues |

Coût mesuré en émulation : premier Random environ 30 millions d'instructions (construction des colliers), puis environ
60 000 plus les notifications de l'OS (environ 7 300 par Random) ; la photo des p-locks environ 1 million (≈ 4 ms).

Non émulé : la vraie police à l'écran, le matériel des LED, la vue des mutes de FUNC, le séquenceur qui joue le pattern
réécrit, le coût réel des notifications sur la machine, l'enregistrement dans la mémoire interne.

## 8. Essais de l'auteur sur sa machine (04/10/2026)

Ces essais sont ceux de l'auteur, sur sa propre Model:Cycles, avec des firmwares construits par `build.py`
(`model-tg` + ses versions du tweak, ordre 50 et générateur de son dépôt), pas avec le MAIN OS de ce dépôt. Ils ne
comptent pas comme le test de Maxime.

- **v0** (Random / Undo, couche 2) : « works like a dream », aucun accroc en enchaînant les Random.
- **v1 à v1.3** (page GEN, pistes EUC) : la page fonctionne ; ordre des potards confirmé à l'usage. Corrigé après ses
  essais : FUNC + pad mutait au lieu de verrouiller (la vue des mutes prend les pads), d'où le verrou au 2e appui
  (v1.2) ; écran trop chargé, réorganisé (v1.1, v1.3). Il se sert de SETTINGS + PATTERN / TEMPO plutôt que de PUNCH.
- **v2** (carte MAP, vélocités) : « fun and pleasant » à l'écoute.
- **v3** (notes, accords, 7e bloc du cache) : **pas encore essayée sur la machine** au moment de cette note.

## 9. Reste à faire

- `[À FAIRE]` **Essai de Maxime** (firmware `model-tg,generative`) : démarrage ; Model-TG intact (Sampler, accords
  SETTINGS, slide trigs) ; SETTINGS + PATTERN pendant la lecture (changement entendu au pas suivant), puis
  SETTINGS + TEMPO (notes, vélocités et p-locks revenus) ; SETTINGS + PAGE : potards, pads muets, verrou au 2e appui,
  LED des trigs, RETURN ; Tone et Chord (piste 6 sur la machine Chord) ; enregistrer puis recharger le pattern ;
  naviguer dans les projets (le cache de fichiers à 9 blocs). Puis l'étiquette « testé ».
- `[À FAIRE]` Carte du flasher web (`FEATURES`, `REF_MAINOS`, textes en/fr), section du guide, notes de version.
- `[FAIT en émulation]` Preuve avec les autres tweaks appliqués (`--with arp,trig-hold,tempo-max,boot-anim,6ch-usbup`) :
  tout passe ; ces combinaisons se construisent aussi une à une et toutes ensemble.
- `[À FAIRE]` **Réglages GEN par pattern** : les 48 réglages (et les verrous) sont en RAM, communs à tous les patterns
  et perdus à l'extinction ; seul ce qui est écrit dans le pattern est enregistré par l'OS. Il faudrait des octets
  inutilisés du pattern ou du projet, prouvés libres (l'octet +512 et le bit 12 des pas sont déjà pris).
- `[HYP]` Longueur maître : 64 est un choix sûr ; la valeur qui veut dire « jamais remis au début » en mode par piste
  n'est pas connue.
- `[À FAIRE]` Chaînage avec les moteurs du Syntakt (`model-tg-st`), si demandé.

## 10. Auteur, licence, inspirations

- Écrit par **Combust**. Sources nouvelles sous licence MIT (`tools/machines/generative/LICENSE`).
- Conception inspirée de Mutable Instruments **Grids** et **Marbles** et du Delptronics **Trigger Man**, sans code ni
  table repris. Grids est sous GPL-3 : la carte des styles de batterie (§3.3) est originale.
