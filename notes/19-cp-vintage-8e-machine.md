# 19 · CP VINTAGE en 8ᵉ machine « CPVtg », avec SDVtg

Travail du 30/09/2026, à la demande de l'utilisateur : « passe à l'engine Syntakt suivant », après le succès de SDVtg sur la machine ([18](18-septieme-machine.md)).
Tweak `syntakt-vintage` : les vrais moteurs **SD VINTAGE** (7ᵉ machine « SDVtg ») et **CP VINTAGE** (8ᵉ machine « CPVtg ») du Syntakt, à côté des 6 machines d'origine.
Le tweak `sdvintage-7th` (SDVtg seule, testé) reste disponible et inchangé.

Adresses : MAIN OS Cycles 1.13 et programme audio du Syntakt 1.41 (section 7), comme en [17](17-portage-exact-syntakt.md) et [18](18-septieme-machine.md).

## 0. En bref

| | État |
|---|---|
| CP VINTAGE dans le programme audio du Syntakt | `[FAIT]` moteur 7 : update `0x40008580`, render `0x40008988` (§1) |
| Paramètres et défauts (interface du Syntakt) | `[FAIT]` BODY, BAL, SPCR, BENV ; 24 / 25 / 46 / 37, DEC 32 (§1) |
| Copie et relocalisation des deux moteurs | `[FAIT]` 30 fonctions, 8 258 o, 116 relocalisations vérifiées (§2) |
| OS Cycles à 8 machines | `[FAIT]` 117 écritures (§3) |
| **Preuve en émulation** : 26 vérifications sur le vrai code de l'OS | `[FAIT]` `tools/emu/test_syntakt_machines.py` (§4) |
| Flasher web : 3ᵉ variante de la case « Vrais moteurs du Syntakt » | `[FAIT]` 63 combinaisons comparées à leur empreinte (§5) |
| Test sur la machine | `[À FAIRE]` (§6) |

## 1. CP VINTAGE dans le Syntakt

- Tables des moteurs du programme audio : update `0x40014920`, render `0x400148f0`. Le moteur 7 (type de machine 7) est CP VINTAGE.
- Descripteurs de l'interface du Syntakt (section 3, `0x40230114..0x40230280`, groupe « CPVN ») :

| Slot du Syntakt | Potard du Cycles | Nom | Défaut |
|---|---|---|---|
| p1 (`0x13`) | COLOR | Body Character (BODY) | 24 |
| p2 (`0x14`) | SHAPE | Balance (BAL) | 25 |
| p3 (`0x15`) | SWEEP | Spacing/Crunch (SPCR) | 46 |
| p4 (`0x16`) | CONTOUR | Body Envelope (BENV) | 37 |
| DEC (`0x19`) | DECAY | Decay | 32 |

Même disposition que SD VINTAGE (p1..p4 = COLOR..CONTOUR) : la passerelle traduit les potards de la même façon.
Noms longs affichés, coupés en mots de 8 lettres au plus ([18 §10](18-septieme-machine.md)) : « Body Char », « Balance », « Spacing Crunch », « Body Envelope ».

## 2. Moteur : copie, relocalisation, passerelle

- **Fermeture** depuis les racines de SD VINTAGE et CP VINTAGE : 30 fonctions, 8 258 o, toujours contiguës (`0x40002544..0x40008ae8`).
- **Tables** : CP VINTAGE en lit davantage que SD VINTAGE, repérées par l'analyse (les références hors copie font échouer la génération) :
  - 14 tables de 512 o après celles de SD VINTAGE (`0x4003a238..0x4003be38`) ;
  - une table de 8 Ko centrée sur `0x4000f48c` et deux de 4 Ko (`0x40014b80`, `0x40015b80`), passées par `movea.l #…` (classées adresses à la main).
- **Nouvelle disposition** de la charge utile (218 560 o, recopiée au démarrage) :

| Adresse | Contenu |
|---|---|
| `0x43000000` | les 30 fonctions |
| `0x43006600` | table `0x4000e488..0x40010490` |
| `0x43008800` | constantes et tables `0x40014980..0x40016b90` |
| `0x4300ac00` | tables `0x40028438..0x4003be38` |
| `0x43020000`, `0x43030000` | réplique de sa SRAM, fenêtre de son BSS |
| `0x43031000` | passerelle `bridge_multi.c` |
| `0x43033000` | détours `machine8.S` |
| `0x43033800` | 8 noms, tables update/render à 8 entrées, table [1..8], chaînes |
| `0x43034000` | 86 descripteurs |
| `0x43035300`, `0x43035400` | rangées par machine et de CC (8 × 32 o) |
| `0x43035500`, `0x43035560` | enregistrements par machine de SDVtg et CPVtg |

- **Passerelle** `bridge_multi.c` : copie de `bridge.c` dont le moteur est un paramètre, avec une paire d'entrées par machine. Elle appelle update/render **du moteur de la machine** (premier essai : CPVtg appelait par erreur l'update de SD VINTAGE ; trouvé en émulation en suivant qui écrit dans la voix du Syntakt).

## 3. OS Cycles à 8 machines

Tout ce qui a été fait pour SDVtg ([18](18-septieme-machine.md)), étendu à 8 machines :
- bornes 5 → 7 : boucle des voix, recherche (slot, machine), réglage de la machine, molette, écran MACHINES ; octets `0x40118646..47` = 6, 7 ;
- 86 descripteurs (bornes 76/75 → 86/85) ; état par descripteur : 76..85 → objets de SNARE ;
- 8 rangées par machine et de CC ; enregistrements par machine 7 (SDVtg) et 8 (CPVtg) ; table machine → enregistrement [1..8] ;
- écran MACHINES : 8 noms, **8 repères** (le 1ᵉʳ repère part de x = 73 au lieu de 80 pour que le 8ᵉ tienne dans les 128 pixels), image de SNARE pour SDVtg et de PERC pour CPVtg (l'OS n'a que 6 images) ;
- `Algorithm` : max 7.

**Nouveauté : le champ « machine » des descripteurs**
- Il vaut 0..5 pour une machine et **7 pour « toutes les machines »** (PITCH, DECAY…). La 8ᵉ machine, d'index 7, ne peut donc pas y écrire 7.
- Solution : les descripteurs de CPVtg (81..84) portent 6 (« propre à une machine », comme ceux de SDVtg), et deux détours les rattachent à la machine 7 :
  - `builder_row` (constructeur des tables, `0x4005a340`) les range dans la rangée 7 ;
  - `desc_machine` (`0x4005a50a`, seul utilisé par le test d'applicabilité `0x4000aa9a`) répond 7 pour eux.
- Les autres lectures directes du champ ne font que classer par catégorie (bits 0..9 = machines de batterie) : 6 y est traité comme 7.

## 4. Preuve en émulation `[FAIT]`

`tools/emu/test_syntakt_machines.py` : 26 vérifications, toutes sur le vrai code de l'OS (stock et modifié).
- **Démarrage** : décompression par le bootstrap ; crochet ; constructeur des tables (BSS identique au stock, rangées 0..5 identiques, rangées 6 et 7 de SDVtg et CPVtg).
- **Recherches** : slot/machine, « propre à une machine », machine d'un descripteur, CC reçu.
- **Accesseurs et état** : bornes, 10 nouveaux descripteurs (noms, plages, défauts), `Algorithm` jusqu'à 7, état par descripteur.
- **Écran MACHINES** : 8 noms ; 8 repères entre x = 69 et 122 ; images de SNARE et PERC.
- **Réglage de la machine et molette** : 6 et 7 atteints, 8 refusé.
- **Enregistrements par machine et changement de machine réel** : Chord → SDVtg écrit 0/110/74/80/33, SDVtg → CPVtg écrit 24/25/46/37/32.
- **Potards de l'écran principal** : SDVtg et CPVtg donnent leurs descripteurs.
- **Son** :
  - SDVtg identique à SD VINTAGE (1 LSB) ;
  - **CPVtg identique à CP VINTAGE** (8 cas : défauts, note 48, BODY, BAL 0/127, SPCR, BENV, DEC ; 1 LSB) ;
  - SNARE identique au stock ;
  - au repos, aucune instruction du Syntakt ;
  - machine locks SNARE → SDVtg → CPVtg.

Les tests de `sdvintage-exact` et `sdvintage-7th` passent toujours. L'émulateur décode désormais le code de la charge utile jusqu'à `0x430065a4`.

## 5. Flasher web

La case « Vrais moteurs du Syntakt » a trois variantes :
- « SDVtg, 7ᵉ machine » (par défaut, testée) ;
- « SDVtg et CPVtg, 7ᵉ et 8ᵉ machines » (nouvelle) ;
- « SD VINTAGE à la place de SNARE » (testée).

Empreintes du MAIN OS : `b4de3ec5…` (seul), `6ca76aa9…` (avec 6 canaux), `47cb625a…` (5 mods). Build `2026-09-30-11`.

## 6. Test sur la machine `[À FAIRE]`

1. Sauvegarder les projets (Transfer).
2. Flasher par USB la variante « SDVtg et CPVtg ». Vérifier le code `MAIN OS b4de3ec5` (seul).
3. Menu MACHINES : 8 machines, CPVtg en dernier (image de PERC), 8 repères tous visibles.
4. Choisir CPVtg : valeurs 24 / 25 / 46 / 37, DECAY 32. Potards : « Body Char », « Balance », « Spacing Crunch », « Body Envelope ».
5. Jouer : clap du Syntakt. Vérifier SDVtg et SNARE, et un machine lock vers CPVtg.
