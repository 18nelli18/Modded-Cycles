# 20 · Moteurs du Syntakt à cocher, et SY TOY « SYToy »

Travail du 30/09/2026, à la demande de l'utilisateur, après le succès de CPVtg sur la machine ([19](19-cp-vintage-8e-machine.md)) :
- « dans le flasher […] on coche les engine qu'on veut rajouter » ;
- « retirer l'option de remplacer la snare, garder seulement les options de rajouts supplémentaires » ;
- « passer au suivant » : SY TOY, moteur 8 du Syntakt.

Adresses : MAIN OS Cycles 1.13 et programme audio du Syntakt 1.41 (section 7), comme en [17](17-portage-exact-syntakt.md), [18](18-septieme-machine.md) et [19](19-cp-vintage-8e-machine.md).

## 0. En bref

| | État |
|---|---|
| Générateur pour n'importe quel choix de moteurs | `[FAIT]` `tools/gen_syntakt_engines.py` (§1) |
| Même comportement que le tweak testé SD + CP | `[FAIT]` 26 vérifications en émulation sur sa version générée (§1) |
| SY TOY en machine « SYToy » | `[FAIT]` identique au Syntakt en émulation, 11 cas (§2) |
| Flasher : une case par moteur, plus d'option « à la place de SNARE » | `[FAIT]` 7 combinaisons, 127 empreintes (§3) |
| 1ᵉʳ essai de SYToy seul : gel à l'appui sur MACHINES | `[CORRIGÉ]` piste restée sur une machine qui n'existe plus (§5) |
| Test sur la machine de SYToy seul | `[FAIT]` le 30/09/2026 : « ça marche nickel » (§4) |
| Test sur la machine des trois moteurs ensemble | `[FAIT]` le 30/09/2026 : « J'ai testé l'ajout des 3 moteurs et ça marche » (§4) |
| Moteur suivant : SY BITS | voir [21](21-sy-bits.md) |

## 1. Générateur de combinaisons

`tools/gen_syntakt_engines.py` généralise `gen_syntakt_machines.py` ([19](19-cp-vintage-8e-machine.md)) à N machines ajoutées.

- **Catalogue** (`CATALOG`) : SD VINTAGE, CP VINTAGE, SY TOY.
  - Les moteurs cochés deviennent les machines 6, 7, 8… dans l'ordre du catalogue.
  - Source : `CATALOG` dans `tools/gen_syntakt_engines.py`.
- **Combinaisons déjà testées** : elles gardent leur tweak d'origine (`LEGACY`).
  - SD seul : `sdvintage-7th` ([18](18-septieme-machine.md)).
  - SD + CP : `syntakt-vintage` ([19](19-cp-vintage-8e-machine.md)).
  - Les autres combinaisons sont générées sous le nom `syntakt-<moteurs>` (fichiers `tweaks/model-cycles_OS1.13/24-*.json`).
  - Source : `LEGACY` et `subset_id()` dans `tools/gen_syntakt_engines.py`.
- **Détours** générés en assembleur pour N machines : mêmes fonctions que `machine8.S`, avec des bornes et des tables qui dépendent de N.
  - Source : `detours_asm()` dans `tools/gen_syntakt_engines.py` ; modèle : `tools/machines/syntakt_bridge/machine8.S`.
- **Passerelle** `bridge_engines.c` : une paire d'entrées `bridge_update_E` / `bridge_render_E` par moteur du Syntakt E, compilée seulement pour les moteurs choisis.
  - Source : `tools/machines/syntakt_bridge/bridge_engines.c`.
- **Table machine → moteur** de la boucle des voix (8 octets, `0x40118640`) : recopiée dans la charge utile, avec une entrée par machine.
  - Le tweak `syntakt-vintage` écrivait dans les 2 octets libres de cette table ; au-delà de 8 machines, elle ne suffit plus.
  - Source : `MAP` dans `tools/gen_syntakt_engines.py` ; 1 seule référence dans l'OS (vérifiée par le générateur).
- **Écran MACHINES** : avec N machines ajoutées, le 1ᵉʳ repère part de x = 80 − 7·(N − 1), pour que les 6 + N repères tiennent dans l'écran.
  - Avec 3 moteurs : 9 repères de x = 62 à 122.
  - **Depuis le 02/10/2026 : sur 2 lignes au-delà de 7 machines** (demande de l'utilisateur : la ligne débordait sur la moitié gauche de l'écran et se superposait à l'image et au nom de la machine).
    - L'écran : moitié gauche (x 0..63) pour la grande image et le nom ; moitié droite pour les repères (y 8..12) et la petite image, à partir de y = 17. Relevé en émulation, par les appels de dessin de `0x400a25e0`.
    - Le détour `marks` (`marks_asm` de `tools/gen_syntakt_engines.py`) remplace la boucle `0x400a26a2..0x400a26f2`. Il dessine 7 repères au plus par ligne, aux mêmes x que les 7 d'origine (76 à 122), à y = 4..8 puis 11..15, au-dessus de la petite image.
    - Jusqu'à 7 machines, rien ne change (une ligne en y = 8..12).
    - Vérifié en émulation (`test_syntakt_machines.py`, `test_model_tg_syntakt.py`) : tous les repères dans la moitié droite, 2 lignes, le repère plein sur la machine choisie.
  - Source : sortie de `tools/emu/test_syntakt_machines.py` (tweak `syntakt-sd-cp-toy`).
- **Vérification** : la version générée de SD + CP (`--engines sd,cp --generic`) passe les 26 vérifications de `test_syntakt_machines.py`, comme le tweak testé sur la machine.
  - Source : `tools/emu/test_syntakt_machines.py --tweak …`, généralisé à n'importe quel tweak de moteurs.

## 2. SY TOY en machine « SYToy »

**Dans le Syntakt**
- Moteur 8 (type de machine 36) : update `0x40008ae8`, render `0x40008d58`.
  - Source : tables des moteurs du programme audio, update `0x40014920` et render `0x400148f0`, entrée 8 ; table type → moteur `0x40014950` (entrée 36 = 8).
- Paramètres de l'interface du Syntakt (groupe « TOY », section 3, `0x402302b4..0x40230420`) :

| Slot du Syntakt | Potard du Cycles | Nom du Syntakt | Nom affiché | Défaut |
|---|---|---|---|---|
| p1 (`0x13`) | COLOR | Form (FORM) | Form | 24 |
| p2 (`0x14`) | SHAPE | Impact (IMP) | Impact | 60 |
| p3 (`0x15`) | SWEEP | Brightness (BRIG) | Bright | 110 |
| p4 (`0x16`) | CONTOUR | Partial Decay (PART) | Partial Decay | 64 |
| DEC (`0x19`) | DECAY | Decay | Decay | 60 |

  - Source : descripteurs de l'interface (pas de `0x34`), champs type, slot, plage, défaut et noms.
  - « Brightness » (10 lettres) devient « Bright » : la fenêtre des potards affiche un mot par ligne, 8 lettres au plus ([18 §10](18-septieme-machine.md)).
  - PNCH (`0x17`) va de 0 à 1, comme pour SD et CP VINTAGE ; TUNE va de 40 à 88.

**Copie**
- Seulement 2 fonctions de plus (33 au total) ; le code copié s'étend jusqu'à `0x40008e0c`.
  - Source : fermeture calculée par `analyse()` dans `tools/gen_syntakt_engines.py`.
- 15 tables de 512 o (`0x4003c038..0x4003de38`).
  - Source : références absolues du code de SY TOY hors des plages copiées jusque-là.
- Un immédiat `move.l #0x800098ec` est rangé dans la voix (+412) : c'est une adresse (tampon SRAM), à relocaliser.
  - Source : `0x40008b68` dans le programme audio. Il suit la série `0x8000945c`, `0x80009580`, `0x800096a4`, `0x800097c8` (pas de `0x124`), déjà classée en adresses dans `gen_sdvintage_exact.py`.

**Nouvelle disposition** de la charge utile (229 376 o) :

| Adresse | Contenu |
|---|---|
| `0x43000000` | les 33 fonctions |
| `0x430068c8`, `0x430088d0`, `0x4300aae0` | tables de SD et CP VINTAGE, à la suite (même alignement modulo 8 que la source) |
| `0x43020000`, `0x43030000` | réplique de la SRAM du Syntakt, fenêtre de son BSS (inchangées) |
| `0x43031000` | passerelle `bridge_engines.c` |
| `0x43033000` | détours générés |
| `0x43033800` | noms, tables update/render, table [1..6+N], table machine → moteur, chaînes |
| `0x43034000` | 76 + 5·N descripteurs |
| `0x43035800`, `0x43035a00` | rangées par machine et de CC |
| `0x43035c00` | enregistrements par machine ajoutée (`0x60` o chacun) |
| `0x43036000` | tables de SY TOY |

- Source : `layout()` dans `tools/gen_syntakt_engines.py`.
- Les tables de SY TOY ne tiennent plus sous la réplique de la SRAM : elles vont au-dessus des enregistrements.
- Le vrai décompresseur du bootstrap relit l'OS agrandi à l'identique ; il finit à `0x401e2140`, sous la zone de travail `0x40200000`.
  - Source : `test_syntakt_machines.py`, vérification « décompresseur du bootstrap ».

**Preuve en émulation** (`tools/emu/test_syntakt_machines.py --tweak …`)
- **SYToy identique au SY TOY du Syntakt** sur 11 cas, écart max 1 LSB :
  - défauts, note 48 ;
  - chaque potard à 0 puis à 127 ;
  - DEC 90.
- Changement de machine CPVtg → SYToy : 24 / 60 / 110 / 64, DECAY 60.
- Machine locks SNARE → SDVtg → CPVtg → SYToy sur une piste : les quatre jouent.
- Combinaisons testées : SY TOY seul (25 vérifications), SD + CP + SY TOY (27), CP seul (25).
- Les tests de `sdvintage-exact`, `sdvintage-7th` et `syntakt-vintage` passent toujours.

## 3. Flasher web

- La carte « Vrais moteurs du Syntakt » a une **case par moteur** : SDVtg (cochée par défaut), CPVtg, SYToy.
  - Décocher le dernier moteur décoche la carte.
  - Une ligne indique si le choix a été testé sur un vrai Model:Cycles. Les choix testés sont listés dans `HW_TESTED` de `gen_syntakt_engines.py` : aujourd'hui SD seul, SD + CP, SY TOY seul et SD + CP + SY TOY.
  - Sinon, l'étiquette passe à « Expérimental ».
- L'option **« SD VINTAGE à la place de SNARE »** (`sdvintage-exact`) n'est plus proposée dans la page. Elle reste disponible avec `build.py`.
- `tools/gen_flasher_tweaks.py` construit la carte depuis le catalogue : moteurs, combinaisons, tweak de chaque combinaison.
- **Empreintes** : `tools/ref_mainos.py` recalcule le MAIN OS de chaque combinaison proposée et réécrit `REF_MAINOS` dans `app.js` (`--check` pour vérifier).
  - 127 combinaisons : 16 sans moteur du Syntakt, puis 16 par choix de moteurs.
  - Les 47 empreintes déjà présentes avant ce travail sont retrouvées à l'identique.
  - Source : `tools/ref_mainos.py` ; `tools/webflash_smoke.sh` reconstruit les 127 dans la page et les compare (ALL OK).
- Build `2026-09-30-14` (correction du §5 depuis le build -13 ; SYToy seul marqué « Testé »).

## 4. Test sur la machine `[EN COURS]`

**SYToy seul : testé le 30/09/2026.** Flashé par l'utilisateur depuis le flasher web (build `2026-09-30-13`, avec la correction du §5) ; son retour : « ça marche nickel ».
C'est aussi le premier firmware produit par `gen_syntakt_engines.py` à tourner sur la machine : le générateur, sa disposition de la charge utile et la correction du §5 sont donc validés sur le matériel.
**Les trois moteurs ensemble : testés le 30/09/2026** (`MAIN OS 8586b230`) ; retour de l'utilisateur : « J'ai testé l'ajout des 3 moteurs et ça marche ».
Les autres combinaisons (CP seul, SD + SY TOY, CP + SY TOY) ne sont vérifiées qu'en émulation.

1. Sauvegarder les projets (Transfer).
2. Dans le flasher, cocher « Vrais moteurs du Syntakt », puis **SYToy seul**. Vérifier le code `MAIN OS 247c8b46` (build `2026-09-30-13`, avec la correction du §5).
3. Menu MACHINES : 7 machines, SYToy en dernier (image de TONE).
4. Choisir SYToy : valeurs 24 / 60 / 110 / 64, DECAY 60. Potards : « Form », « Impact », « Bright », « Partial Decay ».
5. Jouer, et vérifier que le son rappelle le SY TOY du Syntakt.
6. Ensuite, **les trois moteurs** (`MAIN OS 8586b230`) : 9 machines, 9 repères, tous visibles sur l'écran.
7. Si tout va bien, ajouter les choix testés à `HW_TESTED` (ils passeront à « Testé » dans la page).

Retour en arrière : onglet *Official firmware*, par USB (CONFIG › UPGRADE). Remettre **d'abord** sur une machine d'origine les pistes qui utilisent une machine ajoutée (§5).

## 5. Gel à l'appui sur MACHINES avec SYToy seul `[CORRIGÉ]`

**Symptôme** (message de l'utilisateur, 30/09/2026) : SYToy seul flashé (`MAIN OS f0013b73`), « la machine freeze immédiatement dès que j'appuie sur le bouton pour changer de moteur ».

**Cause** : une piste du projet restée sur une machine que ce firmware n'a pas.
- Avec SD + CP (flashé et joué juste avant), CPVtg est la machine 7. Avec SYToy seul, les machines vont de 0 à 6 : une piste sur CPVtg garde le numéro 7, qui n'existe plus.
- Pour une machine au-delà de la dernière, l'accesseur des enregistrements par machine (`0x4004df76`) renvoie `0x40a714f4`, soit 76 o **avant** le tableau `0x40a71540` : d'autres données, lues comme deux chaînes C++ et 17 numéros de descripteurs. C'est la cause du gel de SDVtg à son 4ᵉ essai ([18 §10](18-septieme-machine.md)).
  - Source : `record_of` dans le tweak `syntakt-toy` d'avant la correction, exécuté en émulation avec une piste sur la machine 7 ; le tweak `syntakt-vintage` renvoie son vrai enregistrement pour 7.
- Même chose pour la table machine → enregistrement des potards de l'écran principal (lue au-delà de ses 7 entrées).
  - Source : en émulation, avec les 76 o avant le tableau remplis de pointeurs vers une zone non mappée, les potards de la machine 7 rendent ces pointeurs (`0xa0000020…`) au lieu de numéros de descripteurs.

**Correction** (`detours_asm()` de `tools/gen_syntakt_engines.py`) : une machine ou un index d'enregistrement hors limites donne celui de **KICK**.
- Concerne `record_of`, `record_at` et `knob_vec`. Pour les numéros valides, rien ne change.
- Source : vérification « machine hors limites » de `test_syntakt_machines.py`. Elle échoue sur l'ancien tweak et passe sur les 5 tweaks générés et sur SD + CP généré. Pour une piste sur 7, 8 ou 100 : enregistrement et potards de KICK, la molette ramène sur la dernière machine, aucun accès hors mémoire.

**Ce qui n'est pas protégé**
- Les tweaks d'origine `sdvintage-7th` et `syntakt-vintage` (testés, laissés tels quels).
- Le **firmware officiel** : son accesseur fait la même lecture avant le tableau pour toute machine au-delà de CHORD.
- Source : `records` de `test_sdvintage_7th.py` (stock : enregistrement « avant le tableau » pour la machine 7).
- Donc, avant de changer de choix de moteurs ou de revenir au firmware officiel, il faut remettre sur une machine d'origine les pistes qui utilisent une machine ajoutée. Le flasher l'indique dans la carte et après le flash.
- Les machines ajoutées sont numérotées dans l'ordre des moteurs cochés : une piste sur la machine 7 joue CPVtg avec SD + CP, mais SYToy avec SD + SYToy.
