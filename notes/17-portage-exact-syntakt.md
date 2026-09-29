# 17 · Le VRAI moteur SD VINTAGE du Syntakt dans le Model:Cycles

Travail du 29/09/2026, à la demande de l'utilisateur : « précisément les mêmes moteurs du Syntakt dans le Model:Cycles ».
L'utilisateur fournit son propre `Syntakt_OS1.41.syx`. Le dépôt ne publie aucun firmware Elektron, comme pour les autres mods : seulement nos outils, notre code et une recette appliquée au moment du build.

## 0. En bref

| | État |
|---|---|
| Inventaire de ce qu'utilise SD VINTAGE dans le programme audio du Syntakt | `[FAIT]` 21 fonctions, 5 200 o de code, tables, SRAM (§2) |
| Place libre dans l'OS Cycles | `[FAIT]` SDRAM de 128 Mo, rien au-dessus du BSS (`0x423380b0`) (§3) |
| Tweak `sdvintage-exact` : charge utile, crochet de démarrage, passerelle | `[FAIT]` `tools/gen_sdvintage_exact.py`, `tools/machines/syntakt_bridge/` (§4) |
| `build.py --syntakt` : recette sur TON fichier, OS agrandi | `[FAIT]` (§5) |
| **Preuve : même sortie, échantillon par échantillon** | `[FAIT]` en émulation, `tools/emu/test_sdvintage_exact.py` (§6) |
| Test sur la vraie machine | `[À FAIRE]` (§7) |
| Autres moteurs, 7ᵉ machine, flasher web | `[À FAIRE]` (§8) |

## 1. Principe

- On copie **tel quel** le programme audio du Syntakt (sa section 7, code et données : `0x40000400..0x4004f6e0`) en SDRAM du Cycles, à `0x46000000`.
- On relocalise **uniquement** les adresses absolues contenues dans les fonctions dont SD VINTAGE a besoin. Les adresses relatives au PC restent justes, puisque tout le programme est déplacé d'un seul bloc.
- Autour de lui, on recrée ce qu'il attend :
  - une **réplique de sa SRAM** (`0x80000000..0x8000ffff` → `0x46050000`), remplie comme le fait son démarrage (`0x400004bc`) : ses 8 voix de 1 800 o, ses tables (dont le sinus) et ses tampons de travail y vivent ;
  - une fenêtre de son **BSS** (`0x4404f000..` → `0x46060000`), dont la graine aléatoire `0x4404f954` ;
  - une **passerelle** (notre code C) qui reproduit ce que fait sa boucle des voix `0x40004324` ([16 §3](16-moteur-syntakt.md)).

## 2. Ce qu'utilise SD VINTAGE `[FAIT]`

- **Fermeture** calculée par `gen_sdvintage_exact.py` depuis les racines :
  - `update` `0x40008074`, `render` `0x4000847a` ;
  - remise à zéro `0x40003ee0`, `0x4000255e` (appelée par la boucle à chaque bloc) ;
  - `0x40002544` (init des voix : graine aléatoire).
- Elle suit les appels directs, relatifs au PC et indirects (`lea f,aN ; jsr (aN)`, aucune table de pointeurs). Résultat : **21 fonctions, 5 200 o**.
- **Données** :
  - table croisée DEC × MENV de 64 Ko (`0x40028438`) ;
  - 16 tables de 512 o (`0x40038438..0x4003a238`) ;
  - `0x40014980`, le 1er mot de `0x40014b7c` ;
  - en SRAM : le sinus `0x80004b70`, des tables `0x8000a080`, `0x8000a484`, `0x8000a888`, et des **tampons de travail** vides au démarrage (`0x80008c60`, `0x8000945c`, `0x80009580`, `0x800096a4`, `0x800097c8`), écrits par le rendu avant d'être lus (seul le code des machines les cite).
- **54 relocalisations** : 33 vers le code et les tables, 13 vers la SRAM, 8 vers le BSS.
  - Les immédiats de la forme d'une adresse sont classés **à la main** (liste `IMM_ADDR` / `IMM_NUM` du générateur) : `#0x80000000` y est la constante Q31 −1,0, alors que les pointeurs de tables SRAM rangés dans la voix sont bien des adresses.
  - Tout autre immédiat ambigu fait échouer la génération.

## 3. Où le mettre : la SDRAM au-dessus du BSS `[FAIT]`

Démarrage du MAIN OS Cycles (`0x400004e8`) :
- pile à `0x48000000` ;
- ACR0 `0x4007e020` (cache sur `0x40000000..0x47ffffff`) : **128 Mo de SDRAM** ;
- `0x4000045c` copie `.data` en SRAM ;
- `0x400004b2` remet le **BSS `0x4019b590..0x423380b0`** à zéro, soit 35 Mo, états des voix compris.

**Aucun code de l'OS ne cite d'adresse entre `0x423380b0` et la pile.** Les seules valeurs de cette plage dans l'image sont des flottants ou du texte (vérifié en §3 des scripts du 29/09).
La charge utile va donc à `0x46000000`, à 29 Mo sous la pile.

| Adresse | Contenu | Taille |
|---|---|---|
| `0x46000000` | programme audio du Syntakt (copie de `0x40000400..0x4004f6e0`, décalage `0x05fffc00`) | 324 Ko |
| `0x46050000` | réplique de sa SRAM | 64 Ko |
| `0x46060000` | fenêtre de son BSS | 4 Ko |
| `0x46061000` | passerelle (492 o), puis ses données | |

**Chargement** :
- la charge utile (401 808 o) est **ajoutée à la fin de la section 3**, qui passe de 1 744 192 à 2 146 000 o ;
- le **crochet** remplace les 8 premiers octets de `0x400004b2` (`lea -16(sp),sp ; movem.l d4-d7,(sp)`) par `jmp` vers un petit code logé dans le masque de sprite libéré `0x4016cae8` ([14 §5](14-machine-sd-vintage.md)) ;
- ce code recopie la charge utile de `0x401aa140` vers `0x46000000`, **avant** que le BSS (qui la contient) ne soit remis à zéro, puis refait les deux instructions et reprend à `0x400004ba`.

L'état du cache est le même que pour la remise à zéro du BSS elle-même : le `movec cacr` vient après.

## 4. La passerelle `[FAIT]`

`tools/machines/syntakt_bridge/bridge.c`, branchée dans les tables de machines du Cycles à la place de SNARE (`0x40118614` / `0x4011862c`). Pour la voix `i` du Cycles, elle utilise la voix `i` du Syntakt (dans la réplique de SRAM) :
1. **Première fois** : l'init du processeur audio du Syntakt, pour ses 8 voix (`0x40002544`, `voix+0x56c`, remise à zéro).
2. **Machine choisie** : une marque dans la voix du Cycles (`+0x2c`, effacée par sa remise à zéro `0x400a7ab8`) détecte le changement de machine. Au déclenchement suivant, remise à zéro de la voix Syntakt, comme sa boucle.
3. **À chaque bloc** :
   - drapeaux `+0x34` / `+0x38` / `+0x3c` recopiés ;
   - paramètres traduits (Cycles `p + 0x14..0x24` → Syntakt emplacements 18..26) ;
   - `voix+0x3ec` ← GATE ;
   - puis `0x4000255e`, `update(note, voix, p)`, `render(sortie, voix)`, et `+0x38` ← `+0x34`.
4. Tant que la machine n'a jamais été déclenchée, elle rend du silence.

| Potard Cycles | Syntakt | Défaut (descripteurs SNARE réécrits) |
|---|---|---|
| PITCH | TUNE | 64 |
| COLOR | INHM | 0 |
| SHAPE | FCMP | 110 |
| SWEEP | SWEP | 74 |
| CONTOUR | MENV | 80 |
| PUNCH | PNCH | 0 |
| GATE | GATE (caché sur le Syntakt) | 0 |
| DECAY | DEC | 33 |
| FINE | ajouté à la note (sans effet à 64) | 64 |

OVER n'a pas de potard : il vaut 0, le défaut, et il n'agit de toute façon pas sur la sortie de la machine ([16 §6](16-moteur-syntakt.md)).

## 5. Build

```sh
python3 tools/build.py -i model-cycles_OS1.13.syx -t sdvintage-exact --syntakt Syntakt_OS1.41.syx
python3 tools/build.py -i model-cycles_OS1.13.syx -t 6ch-usbup,sdvintage-exact --syntakt Syntakt_OS1.41.syx
```

- `build.py` vérifie le `.syx` Syntakt officiel et sa section 7 (SHA-256), exécute la recette du tweak (plages à copier et relocalisations, **ancienne valeur vérifiée à chaque fois**), puis ajoute la charge utile à la section 3.
- La recompression de l'OS agrandi (`tools/aplib_grow.py`) reprend le flux d'origine et compresse la partie ajoutée avec un compresseur glouton ; elle est **relue** avant écriture.
- `.syx` : 1 245 216 o, contre 890 016 : environ 40 % de temps de transfert en plus.
- MAIN OS patché (`sdvintage-exact` seul) : `43e9d15f…`.
- `tools/gen_sdvintage_exact.py --syntakt …` régénère le tweak. Il faut `m68k-elf-gcc` et `m68k-elf-objdump` pour la passerelle et l'analyse, seulement chez le développeur.

## 6. Preuve en émulation `[FAIT]`

`tools/emu/test_sdvintage_exact.py` :
- rend le vrai SD VINTAGE dans le moteur du Syntakt (`stengine.py`) ;
- rend le même dans l'OS Cycles patché (`mcengine.py`, qui charge la charge utile comme le crochet) ;
- même note, mêmes réglages, même instant de déclenchement.

La boucle du Cycles divise la sortie par 2, donc on compare Cycles × 2 et Syntakt.

**Résultat : identique au Syntakt dans les 12 cas** (200 blocs, soit 6 400 échantillons chacun, 76 800 au total).
Aucun échantillon différent, écart maximal 1 LSB, qui est l'arrondi de la division par 2.

| Cas | Crête | Échantillons différents |
|---|---|---|
| réglages d'usine | 1,52·10⁹ | 0 |
| note 48 / note 72 | 1,84 / 1,88·10⁹ | 0 / 0 |
| TUNE 76 | 1,88·10⁹ | 0 |
| SWEP 127 / SWEP 0 | 1,97 / 1,54·10⁹ | 0 / 0 |
| INHM 127 | 1,88·10⁹ | 0 |
| FCMP 0 | 7,17·10⁸ | 0 |
| MENV 0 | 1,56·10⁹ | 0 |
| DEC 90 / DEC 5 | 1,65 / 1,37·10⁹ | 0 / 0 |
| PNCH | 1,53·10⁹ | 0 |

Le test exécute aussi **la vraie remise à zéro du BSS `0x400004b2` de l'OS patché**. Le crochet recopie la charge utile intacte vers `0x46000000`, puis le BSS, qui la contenait, est bien remis à zéro, et la fonction revient normalement.

Coût : **9 730 instructions par bloc** (voix seule, boucle comprise), contre 8 767 pour la SNARE d'origine (+11 %).

## 7. Risques pour le premier flash `[À FAIRE]`

- **Taille de la section 3** : le bootstrap du Cycles accepte-t-il 2,1 Mo au lieu de 1,7 ? Inconnu. En cas de refus, le bootloader n'est pas touché : retour par le MIDI IN.
- **Zone `0x46000000`** : aucune référence statique, mais un usage dynamique ne peut pas être exclu en émulation.
- **Temps processeur** : SDRAM (cache) au lieu de SRAM pour les voix et les tables, et un processeur partagé avec l'interface. Tester six pistes en SD VINTAGE, pattern dense, effets.
- **Pile** : les fonctions du Syntakt utilisent environ 100 o de pile de plus que la SNARE.

Protocole : interface MIDI prête sur le MIDI IN, projets sauvegardés, flash par USB (`CONFIG › UPGRADE`) ou par le menu de démarrage.
Écouter : une piste sur SNARE doit sonner exactement comme le SD VINTAGE d'un Syntakt, aux mêmes réglages.

## 8. Suite `[À FAIRE]`

- CP VINTAGE (moteur 7), SY TOY / SY BITS / SY SWARM (8–10) et SP TWINSHOT (11) : même méthode. Il faut élargir les racines, relocaliser, et une passerelle par machine.
- Les autres machines numériques du Syntakt (SY RAW, SY CHIP, BD HARD…) ne passent pas par cette boucle : à localiser.
- Ajouter plutôt que remplacer : 7ᵉ machine ([14 §8](14-machine-sd-vintage.md)).
- Flasher web : porter en JavaScript la recette (lecture du `.syx` Syntakt, relocalisation, OS agrandi).
