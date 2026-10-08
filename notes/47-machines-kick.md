# 47 — Machines Kick2 et Kick3 : deux kicks de zicBox sur le Model:Cycles

Proposition d'apiel (auteur de [zicBox](https://github.com/apiel/zicBox), 08/10/2026) : ajouter au Model:Cycles deux
machines de kick portées de ses moteurs, `PotKick.h` (Kick2) et `KickWave.h` (Kick3). Tweak `26-kick.json`, générateur
`tools/gen_kick.py` (et `34-kick-tg.json`, avec Model-TG), sources `tools/machines/kick/`, preuve `tools/emu/test_kick.py`. Adresses : VA de l'OS 1.13.

## Réponse courte

- **Deux machines ajoutées**, Kick2 (7e) et Kick3 (8e), après les 6 d'origine, avec la mécanique des machines ajoutées de
  MACRO ([43](43-machine-macro.md)) pour N = 2 machines : mêmes détours (`gs.detours_asm`), mêmes tables déplacées, mêmes
  adresses dans la charge utile (`gs.LAYOUT`). Avec Model-TG, la version `34-kick-tg.json` (par-dessus `model-tg-st`,
  comme `32-macro-tg.json`) met Kick2 et Kick3 en 8e et 9e machines, après le Sampler. Les moteurs du Syntakt et MACRO
  ajoutent des machines au même endroit : le tweak les déclare dans `conflicts` et la carte du flasher les exclut (§6).
- **Tout en entiers.** Le ColdFire du Cycles n'a pas d'unité flottante, et la seule libgcc fournie par
  `m68k-linux-gnu-gcc` est compilée pour le 68020 : ses routines de flottant logiciel contiennent des instructions
  absentes du ColdFire et plantent la machine (§2). L'édition de liens se fait donc **sans libgcc** : un float égaré
  fait échouer le build au lieu de planter la machine. Les moteurs sont en Q31 par l'EMAC (Q28 et Q24 là où il faut de la
  marge), sinus et tanh par tables.
- **Kick3** construit sa forme d'onde avec 4 potards (COLOR = WAVE, SHAPE = FOLD, SWEEP = SKEW, CONTOUR = HARM), PITCH
  règle le caractère de la chute de hauteur, PUNCH est le drive (§3). La hauteur suit la note du trig (52 Hz à C4).
- **Kick2** : COLOR = MRPH (5 formes), SHAPE = SHPR (waveshaper), SWEEP = SW.SH (4 courbes de chute, dont la double
  chute gabber), CONTOUR = RESO (résonateur), PUNCH = drive (§4).
- **Preuve** `[FAIT en émulation]` : tout l'interface (tables, descripteurs, écran MACHINES à 8 noms, molette, machine
  réelle changée, potards, icônes), Kick3 contre un modèle en flottant de KickWave.h, et les deux moteurs à tous les
  réglages (§7).
- **Pas encore testé sur la machine** : la carte du flasher est « expérimentale ».

## 1. Ce que l'OS demande à une machine ajoutée `[FAIT]`

Rien de nouveau : tout est dans [43 §2](43-machine-macro.md) et [20](20-moteurs-syntakt-a-cocher.md). Une machine est
une paire `update(pmod, voix, params)` / `render(sortie, voix)` ; `render` doit finir par la chaîne d'ampli de l'OS
(`0x400a9252` enveloppe, `0x400a9430` VCA, `0x400a967a` PUNCH), sans quoi la machine est muette ; `update` pose les
constantes de l'étage PUNCH au trig (comme SNARE). L'état d'une voix tient dans la zone des opérateurs FM de la voix
(`+0x70..+0xbc`), inutilisée par ces machines.

## 2. Pourquoi tout en entiers `[FAIT]`

Un premier essai de Kick3 en flottant (compilé `-mcpu=54418`, donc en flottant logiciel) jouait son et se laissait régler,
mais plantait à la première note : les routines de la libgcc (`__addsf3`, `__mulsf3`, …) du paquet
`gcc-m68k-linux-gnu` d'Ubuntu viennent de la bibliothèque 68020 et utilisent des instructions que le ColdFire n'a pas.
Les deux moteurs sont donc en entiers. Les corrections de la forme d'onde qui en découlent :

- sinus : table de l'OS (`0x8000eee4`, 256+1 points Q31), interpolée ; tanh : table de 257 points, interpolée ;
- fréquence : phase 32 bits (2^32 = un cycle), incrément d'une note par `note_inc` (celui de SD VINTAGE) ;
- les bornes Q31 de l'EMAC saturent : les produits qui sortent de [-1, 1[ (harmonique, drive) se calculent en Q28.

## 3. Kick3 (KickWave.h) `[FAIT en émulation]`

| Potard | Écran | Rôle (port de KickWave.h) |
|---|---|---|
| PITCH | PITCH | caractère de la chute de hauteur : 4 réglages fondus (glissé doux : profondeur 1,2 et tau 30 ms ; classique : 3,5 et 7 ms, le réglage par défaut de KickWave ; gabber : 7, 0,65 × 5 ms + 0,35 × 45 ms, plongeon rapide puis longue queue ; plongeon long : 10 et 90 ms) |
| COLOR | WAVE | `waveShape` : sinus → triangle → scie → carré (un tiers du potard chacun) |
| SHAPE | FOLD | `fold` : repli d'onde `sin(x × (1 + 3,5 fold) × π/2)`, en fondu sur les 6 premiers % |
| SWEEP | SKEW | `skew` (5 à 95 %, le milieu est symétrique) : déformation de la phase |
| CONTOUR | HARM | `harmonic2` (−1 à +1, le milieu n'ajoute rien) |
| PUNCH | — | drive de KickWave (`applyDrive` à 35 %) : `tanh(x × 6,25) × 6,25`, puis le compresseur de colle (seuil 0,65) |
| DECAY | — | durée 50 ms à 1,5 s (`duration` de KickWave), enveloppe `(1 − t)^5` |

Différences voulues avec KickWave.h :

- le triangle et la scie **partent de 0 et montent comme le sinus** (ceux de KickWave partent de ±1) : le morphing ne
  saute plus de phase (un saut s'entendait en tournant COLOR) ;
- le repli d'onde **entre en fondu** sur ses 6 premiers % (KickWave le met d'un coup dès 0,1 %) ;
- `harmonic3` et `phaseOffset` sont fixés (0), pour ne pas dépasser les 4 potards ; la modulation de fréquence est fixe
  (35 %, modulateur à 1,5 fois) ; ni résonateur ni crush dans cette version ;
- la hauteur : PITCH ne règle plus la fréquence (c'est la note du trig, 52 Hz à C4) ; la chute est KickWave en deux
  exponentielles.

## 4. Kick2 (PotKick.h) `[FAIT en émulation]`

COLOR = MRPH : VCO à 5 formes (sinus, triangle, scie, carré, scie écrêtée par tanh) ; SHAPE = SHPR : waveshaper (propre →
drive tanh sur les 35 premiers %, puis fondu vers un repli d'onde) ; SWEEP = SW.SH : 4 courbes de chute de hauteur
(`p²`, double chute `0,75 p⁸ + 0,25 p`, smoothstep, `p^1,5`) ; CONTOUR = RESO : résonateur à variable d'état suivant la
hauteur ; PUNCH = drive (`tanh(4,15 x)`) ; PITCH 30 à 100 Hz ; DECAY 50 ms à 3 s ; compresseur de colle. La profondeur de
la chute est fixe (13 fois la fréquence de base, 70 ms).

## 5. Charge utile et place `[FAIT]`

Même disposition que MACRO (`gs.LAYOUT`) : code et tables des deux moteurs à `0x43000000` (8,7 Ko, dont 2 tables de tanh
de 1 Ko), détours à `0x43033000`, données à `0x43033800`, 86 descripteurs à `0x43034000`, rangées, enregistrements.
Rangé en 14 616 o dans l'image (crochet de démarrage `stub.S` en mode PACK, comme MACRO), l'image décompressée finit à
`0x401ada58` (limite `0x40200000`). Pas d'état global : tout l'état est dans la voix, il n'y a pas de BSS.

## 6. Conflits `[FAIT]`

`26-kick.json` déclare `conflicts` avec tout ce qui ajoute des machines ou un bloc après l'image : MACRO, les moteurs du
Syntakt, SD VINTAGE, Model-TG (et `model-tg-st`, avec qui il faut prendre `34-kick-tg.json`, qui `requires`
`model-tg-st`). La carte du flasher a `excludes: macro, syntakt` et `with: model-tg → 34-kick-tg` (Model-TG et
l'écoute des samples prennent leur version « -st » quand la carte est cochée). Elle se combine avec les autres tweaks (testé en émulation avec `6ch-usbup`, `trig-hold`, `arp`, `tempo-max`, `boot-anim`, §7).
Comme MACRO seule, elle prend l'envoi USB à heure fixe (`usb_steady.py`, [35](35-glitches-usb-multipiste.md)) et la
boucle des voix plus courte (`voice_loop.py`, [36](36-regulateur-sans-coupures-inutiles.md)).

## 7. Preuve en émulation `[FAIT en émulation]`

`tools/emu/test_kick.py` (le vrai code de l'OS, dans Unicorn) :

- **démarrage** : décompresseur du bootstrap, crochet (zone remise à zéro, morceaux recopiés, SRAM et registres
  intacts) ;
- **interface** : les vérifications de `test_syntakt_machines.py` pour 2 machines : rangées, recherches, descripteurs,
  écran MACHINES (8 noms, 8 repères sur 2 lignes), molette, enregistrements, changement de machine réel, potards,
  machine hors limites, icône ;
- **code** : aucune instruction flottante, aucun appel hors de la charge utile sauf la chaîne d'ampli ;
- **Kick3 contre KickWave.h** : modèle en flottant calculé dans le test (mêmes réglages, mêmes choix de §3) ; corrélation
  normalisée au meilleur décalage (la chaîne d'ampli de l'OS retarde de 35 à 39 échantillons) sur 10 réglages : les 4
  formes d'onde, skew et harmonique 2, repli d'onde, drive, les 4 caractères de la chute ;
- **les deux machines à tous les réglages** (chaque potard à 0, 64 et 127, PUNCH, DECAY, notes 36, 60, 84) : sans accès
  hors mémoire, niveau borné ;
- **machines d'origine inchangées** (échantillon par échantillon) et sans une instruction des kicks ; machine locks
  Kick2 → Kick3 → SNARE → Kick3 → Kick2 ; 6 pistes en kick ensemble ; kicks mêlés aux machines d'origine ;
- **avec les autres mods** (`--with`) : démarrage, machines d'origine identiques, kicks identiques à eux seuls.

Limite : Kick2 n'a pas de modèle de référence en flottant (la preuve vérifie qu'il joue à tous les réglages et que
l'interface est juste, pas qu'il égale `PotKick.h` à l'échantillon près).

## 8. À vérifier sur la machine `[À FAIRE]`

- le son des deux machines (le port est en virgule fixe : très proche de zicBox, pas identique) ;
- le coût en charge : mesuré en instructions par bloc dans l'émulateur (§7, sortie de `test_kick.py`), pas de régulateur
  de charge pour ces machines ;
- l'icône (celle de KICK) et le nom de 5 lettres sur l'écran MACHINES ;
- `PUNCH` : le niveau baisse d'environ moitié (le drive écrête puis le compresseur et l'étage PUNCH de l'OS ramènent).

## 9. Licence `[À CONFIRMER]`

zicBox est sous GPL-3.0 ; le code des deux machines est un portage d'apiel, auteur de zicBox, qui le contribue à ce
dépôt. La licence sous laquelle le dépôt le reprend est à confirmer avec Maxime et apiel avant la fusion
(`PROVENANCE.md`).
