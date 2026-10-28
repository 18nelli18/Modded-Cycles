# 84 — Machine RETROSYN : des voix chiptune (Game Boy, NES, SNES), 15e machine de l'OS

Portage dans l'OS unique ([71](71-os-unique.md)) de la machine RETROSYN du fork
[AveyCole/Modded-Cycles](https://github.com/AveyCole/Modded-Cycles) (`tools/machines/retrosyn/`, sa note 96).
Étape 1 (commit `2205858`) : sources du cœur figées contre le fork, tables identiques octet pour octet. Étape 2 (cette
note) : générateur `tools/gen_retrosyn.py`, tweak
`31-syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn.json`, preuve `tools/emu/test_retrosyn.py`. Adresses : VA de
l'OS 1.13, charge utile à `PAY_TG = 0x46700000` (avec Model-TG).

## En bref

- **Une machine ajoutée, RETROSYN, la 15e et la dernière** (index 14), après ACID, avec la mécanique d'ACID dans les
  versions combinées ([54](54-machine-acid.md) §11, `gen_acid_combos.build_engines`) : la passerelle des moteurs,
  MACRO et ACID gardent leurs octets et leur place ; RETROSYN est lié au-dessus. 8e machine ajoutée :
  `gs.MAX_EXTRA` passe de 7 à 8.
- **Potards** : SHAPE choisit l'onde (0 PULSE, 1 TRI NES, 2 WAVE Game Boy, 3 bruit LFSR 15 bits, 4 bruit LFSR 7 bits,
  5 boucle SNES à interpolation gaussienne) ; COLOR le rapport cyclique / la table / la boucle / la cadence du bruit ;
  SWEEP le balayage de hauteur (64 : rien ; cadence 128 Hz ; au-delà de C9 la note se tait) ; CONTOUR un des 8
  accords joués en arpège à 60 Hz ; PUNCH écrase la sortie à 4 bits ; DECAY et GATE : l'enveloppe de TONE.
- **5 descripteurs** comme les autres machines ajoutées : Color (COLR, 0), Shape (SHAP, 0, plage 0..5), Sweep (SWEP,
  64), Contour (CONT, 0), DECAY 50. Icône : celle de TONE (image 4).
- **Statut : expérimental.** Prouvé en émulation sur le vrai code de l'OS ; pas d'essai sur la machine.
- **Licence : non déclarée.** La note 96 §5 du fork dit : « Le coeur fourni ne contenait aucune declaration de
  licence ni nom d'auteur ». La mention « MIT License » des en-têtes de `tools/machines/retrosyn/` a été ajoutée par
  ce projet à l'étape 1. Il faut la confirmer avec AveyCole avant la fusion. `os.json` ne cite donc aucun fichier de
  licence (pas de `LICENSE-Retrosyn`), seulement le crédit `by AveyCole`.

## 1. Le cœur et la passerelle

`retrosyn_dsp.h` (cœur), `retrosyn.c` (passerelle, contrat `update` / `render` de MACRO), `retrosyn_tables.h`
(écrit par `gen_retrosyn_tables.py`, vérifié par `gen_retrosyn.py --check`) : inchangés depuis l'étape 1.

- `retrosyn_update(pmod, v, p)` : une fois par bloc de 32 échantillons. Marque `'RSY1'` (`0x52535931`) en
  `voix + 0x2c` : absente, le cœur de la piste est remis à zéro (changement de machine, verrou MACHINE). Au trig
  (`voix + 0x38`), mêmes valeurs d'enveloppe que TONE en `voix + 0x274..0x2a4`, DECAY par `LUT_DECAY`
  (`0x4011d84c`) en `voix + 0x250`.
- `retrosyn_render(out, v)` : une voix muette (ni note, ni trig, niveaux `voix + 0x230/0x234` sous 2^14) n'est pas
  calculée, le bloc est mis à zéro ; sinon le cœur, puis `AMP_ENV` (`0x400a9252`) et `VCA` (`0x400a9430`), la chaîne
  d'ampli de TONE.
- État par piste : `tracks[6]` en BSS, 60 o par piste, indexé par `(v - 0x42308828) / 0x31c` (`VOICE0`, `VSTRIDE`
  de `mcengine.py`). Pas de borne : la boucle des voix n'appelle la table des machines qu'avec les 6 voix. Ajouter
  une borne changerait les octets du fork, donc on ne le fait pas.

Compilé par `m68k-linux-gnu-gcc` 13.3 (Ubuntu 24.04), drapeaux d'ACID (`gen_acid.CFLAGS`). Le GCC 14.2 de Debian
donne d'autres octets (text 2 536 o) : `--check` le signale.

| Section | Adresse | Taille |
|---|---|---|
| `.text` | `0x46779000` (`PAY + RS_AT`, `RS_AT = 0x79000`) | 2 652 o |
| `.rodata` | à la suite, alignée sur 4 | 3 056 o |
| code + tables | `0x46779000..0x4677a64c` | 5 708 o |
| `.data` | — | 0 o (refusée par le générateur : le crochet de démarrage ne la copierait pas) |
| `.bss` | `0x4677b000..0x4677b168` (`PAY + RS_BSS`) | 360 o |

ACID finit plus bas : ses variables vont jusqu'à `PAY + 0x782e8`. `gen_macro_syntakt.build_tweak` refuse une
machine qui commencerait avant la fin de la précédente.

## 2. Place dans la charge utile : 8 machines ajoutées (`gs.ROWS8`)

Avec 8 machines ajoutées et Model-TG, il y a 15 machines et 116 descripteurs (`0x1960` o). `ROWS7` ne suffit plus :
les descripteurs couvriraient les rangées placées juste après eux (`0x35860`). `gs.set_rows` passe à `ROWS8`
au-delà de 7 machines ajoutées. En dessous, rien ne bouge (vérifié par `--check` des générateurs, §6).

| Zone (offset depuis `PAY`) | 7 ajoutées (`ROWS7`) | 8 ajoutées (`ROWS8`) |
|---|---|---|
| détours `STUBS` | `0x33000..` (< `0x33800`) | `0x33000..` (0x84c o, < `0x33900`) |
| `DATA` (noms, update/render, VEC, chaînes) | `0x33800` | `0x33900` (≈ 0x2c0 o, < `0x33c00`) |
| rangées `ROWSN` | `0x35860` | `0x33c00` (15 × 32 o) |
| rangées CC `CCROWSN` | `0x35a20` | `0x33e00` (15 × 32 o, < `DESCN 0x34000`) |
| descripteurs `DESCN` | `0x34000` | `0x34000..0x35960` (< `RECS 0x35c00`) |
| enregistrements `RECS` | `0x35c00` | `0x35c00..0x35f00` (= `REC_ATK`, plein) |

`check_room` vérifie chaque borne ; il n'y a plus de marge pour une 9e machine sans déplacer d'autres zones.

## 3. Écran MACHINES : 8 repères par ligne

Avertissement du plan de portage : avec 15 machines, la 2e ligne de repères (7 par ligne, `x = 80 + 7k`) aurait
débordé. `gs.marks_row(nm)` vaut 7 jusqu'à 14 machines, 8 au-delà. La ligne commence alors un pas plus à gauche
(`gs.marks_x` : bord droit du 1er repère à `x = 73`, repère de 69 à 73) ; le dernier reste à `x = 122` (< 128),
toujours dans la moitié droite (`x >= 64`), sans toucher l'image ni le nom. Jusqu'à 14 machines, mêmes octets
qu'avant (`marks_asm` reçoit `nm`). Preuve : `test_model_tg_syntakt.interface` (repris par `test_retrosyn.py`),
15 repères sur 2 lignes, les 8 premiers en haut, le plein sur la machine choisie.

## 4. Régulateur de charge et `GOV_SKIP`

Avertissement du plan : ACID est compilé avec `GOV_SKIP` (une voix que le régulateur a cessé d'appeler plus de
3 blocs est marquée tuée, pour ne pas glisser depuis une note périmée). RETROSYN ne l'est pas, et c'est voulu :

- il n'a pas de slide ; chaque trig (`in->trig`) remet la phase, le balayage, l'arpège et le drapeau de silence
  (`retrosyn_dsp.h`) ;
- une note tenue que le régulateur a coupée reste coupée jusqu'au trig suivant, qui repart de zéro.

Preuve (`test_retrosyn.py`, « load governor ») : sous surcharge, le régulateur coupe aussi les pistes RETROSYN,
jamais le Sampler ; une note tenue coupée puis un trig : la piste est identique, échantillon pour échantillon, à la
référence qui part de ce trig.

## 5. Pas de recouvrement

Le plan comptait des recouvrements entre le tweak autonome du fork (`27-retrosyn.json`) et les tweaks de l'OS. Ce
portage n'a pas de tweak autonome : RETROSYN n'existe que dans la version combinée, qui remplace
`syntakt-tg-sd-cp-toy-bits-swarm-macro-acid` dans `os.json` (mêmes 117 écritures sur l'OS, conflits déclarés avec
toutes les autres combinaisons). `tools/check_overlaps.py` : 284 tweaks, aucune écriture partagée entre deux mods
installables ensemble, hors cas prévus.

## 6. Place dans l'image et vérifications

| | sans RETROSYN | avec RETROSYN |
|---|---|---|
| charge utile | 492 288 o | 504 168 o |
| rangée (aPLib) | 247 441 o | 252 238 o (+4 797) |
| fin de l'image | `0x401fbf51` | `0x401fd20e` |
| libre sous `END_LIMIT 0x40200000` | 16 559 o | **11 762 o** |
| descripteurs | 111 | 116 |

- `gen_retrosyn.py --check` : tables et tweak à jour (toolchain exacte, conteneur `dsh-ru`).
- `gen_acid_combos.py --check`, `gen_macro_syntakt.py --check`, `gen_acid.py --check`, `gen_macro.py --check`,
  `gen_syntakt_engines.py --all --check` (m68k-elf 16.2) : aucun tweak existant ne change.
  `gen_syntakt_engines.py --all --tg --check` s'arrête sur « zones de SRAM » aussi sur `2205858` sans ces
  changements : défaut connu de `main`, corrigé par #113, sans lien avec RETROSYN.
- `registry.py --check`, `gen_flasher_tweaks.py --check`, `ref_mainos.py --check` : à jour.
- `build.py --os` : MAIN OS patché `956bbd4190bb716bee4b49d04a68ec5aa938318091951f65053418a8afd8f5c3`.

## 7. Preuve en émulation (`tools/emu/test_retrosyn.py`)

Sur `30-model-tg-st` + le tweak, contre la même combinaison sans RETROSYN, le vrai code de l'OS (Unicorn) :

1. Démarrage : la charge utile est reconstruite (décompression, cache) ; MACRO et ACID à leur place, avec leurs
   octets ; RETROSYN à `RS_AT`, ses variables à `RS_BSS`.
2. Interface : RETROSYN dans MACHINES (15e), son nom, son image, ses 5 descripteurs et leurs défauts, les rangées
   (`ROWS8`), le changement de machine, 15 repères.
3. Son : avant la chaîne d'ampli, identique au cœur compilé pour l'ordinateur (`retrosyn_ref.c`) sur les 6 ondes,
   les tables, PUNCH, SWEEP, les accords et des potards qui bougent ; une voix muette n'est pas calculée ; chaîne
   d'ampli lue comme pour TONE ; les 6 machines d'origine, les moteurs, MACRO et ACID identiques à l'OS sans
   RETROSYN ; 6 pistes RETROSYN ensemble ; verrous de machine (chaque entrée dans RETROSYN repart d'un cœur remis à
   zéro) ; régulateur (§4).

Le harnais de `test_acid_combos.Fw` lit la table des machines à `gs.ROWS8["DATA"]` au-delà de 7 machines
ajoutées.

## 8. À faire

- Essai sur la machine (programme : notes/96 §5 du fork : les 6 SHAPE, COLOR/SWEEP/CONTOUR, PUNCH, FINE,
  DECAY/GATE, retrigs, 6 pistes ensemble, l'écran MACHINES à 15 repères).
- Licence **MIT** (`LICENSE-Punch.txt` du dépôt amont, vérifié le 28/10/2026 ; le dépôt s'appelle désormais AveyCole/Supermodel, l'ancien nom redirige).
- Section du guide (`docs/guide/`) : pas encore écrite, d'où l'absence de `guide` dans `os.json`.
