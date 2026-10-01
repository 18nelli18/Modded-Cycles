# 21 · SY BITS en machine « SYBit »

Travail du 30/09/2026, à la demande de l'utilisateur : « J'ai testé l'ajout des 3 moteurs et ça marche. Donc passe à SY Bits ».
SY BITS est le moteur 9 du Syntakt. Il devient la 4ᵉ case de la carte « Vrais moteurs du Syntakt » du flasher ([20](20-moteurs-syntakt-a-cocher.md)).

Adresses : MAIN OS Cycles 1.13 et programme audio du Syntakt 1.41 (section 7), comme dans les notes [17](17-portage-exact-syntakt.md) à [20](20-moteurs-syntakt-a-cocher.md).

## 0. En bref

| | État |
|---|---|
| Les trois moteurs SD + CP + SY TOY sur la machine | `[FAIT]` testé par l'utilisateur le 30/09/2026 (« ça marche ») |
| SY BITS copié et relocalisé | `[FAIT]` 41 fonctions, 196 relocalisations (§2) |
| Les firmwares déjà testés restent identiques à l'octet près | `[FAIT]` 127 empreintes inchangées (§3) |
| **Preuve en émulation** | `[FAIT]` SYBit identique au Syntakt sur 16 cas ; 8 combinaisons, 26 à 29 vérifications (§4) |
| Flasher : 4ᵉ case, 255 empreintes | `[FAIT]` build `2026-09-30-15` (§5) |
| Test sur la machine | `[FAIT]` SYBit seul, le 30/09/2026 : « SYBit seul marche nickel » (§6) |

## 1. SY BITS dans le Syntakt

- Moteur 9 (type de machine 37) : update `0x40008e0c`, render `0x400091e0`.
  - Source : tables des moteurs du programme audio (update `0x40014920`, render `0x400148f0`, entrée 9) ; table type → moteur `0x40014950` (entrée 37 = 9).
- Paramètres de l'interface du Syntakt (groupe « BITS », section 3, `0x40230454..0x402305c0`) :

| Slot du Syntakt | Sur le Cycles | Nom du Syntakt | Nom affiché | Plage | Défaut |
|---|---|---|---|---|---|
| p1 (`0x13`) | COLOR | Detune (DET) | Detune | **40 à 88** | 52 |
| p2 (`0x14`) | SHAPE | Balance (BAL) | Balance | 0 à 127 | 102 |
| p3 (`0x15`) | SWEEP | Sample Rate Redux (SRR) | Rate Redux | 0 à 127 | 0 |
| p4 (`0x16`) | CONTOUR | Waveform (WAVE) | Waveform | 0 à 127 | 21 |
| `0x17` | PUNCH | Bit Redux (BR) | (pas de potard) | 0 à 127 | 0 |
| DEC (`0x19`) | DECAY | Decay | Decay | 0 à 127 | 60 |

  - Source : descripteurs de l'interface (pas de `0x34`), champs type, slot, plage, défaut et noms.

**Deux différences avec les moteurs précédents**
- **Detune va de 40 à 88**, comme TUNE. Le descripteur du potard COLOR de SYBit porte cette plage (champs min et max), au lieu de 0 à 127.
  - Si une piste arrive sur SYBit avec une valeur hors plage (réglage d'un autre moteur), la passerelle la borne à 40..88 avant de la donner au moteur.
  - Affichage sur le Cycles : non vérifié. L'écran montre probablement la valeur brute (40 à 88).
- **L'emplacement `0x17` est Bit Redux (0 à 127)**, et non PNCH (0 ou 1). Le Cycles n'a pas de potard pour lui : **PUNCH actif met Bit Redux à 80**, PUNCH inactif à 0 (défaut du Syntakt).
  - Choix de 80, d'après le moteur du Syntakt en émulation (écart du signal avec Bit Redux à 0) : 2 % à 32, 10 % à 48, 34 % à 64, **72 % à 80**, 113 % à 96.
  - C'est la constante `punch_on` du catalogue de `tools/gen_syntakt_engines.py`.
  - Source : `bridge_engines.c` (bloc `#ifdef UPD_9`).

## 2. Copie et relocalisation

- 8 fonctions de plus (41 au total) ; le code copié s'étend jusqu'à `0x400092ec`.
- 8 tables de 512 o (`0x4003de38..0x4003ee38`), placées après celles de SY TOY.
- **11 immédiats sont des adresses en SRAM**, à relocaliser :
  - 10 tables d'ondes de `0x804` o (`0x80004f74`, `…5778`, `…5f7c`, `…6780`, `…6f84`, `…7788`, `0x8000c888`, `…d08c`, `…d890`, `…e094`), rangées dans la voix (+176, +180) ;
  - un tampon (`0x8000a064`), pris dans un registre d'adresse en `0x40006276`.
  - Les deux séries se terminent à la fin des deux zones de données initialisées de la SRAM du Syntakt (`0x80007f90` et `0x8000e8a0`, à quelques octets près).
- **Piège : une fonction appelée par pointeur.**
  - L'update de SY BITS fait `lea 0x40006646,%fp` (`0x40008fd8`), puis l'appelle. L'analyse ne suivait ce cas que pour les registres `a0..a5`.
  - Cette fonction (qui règle la 2ᵉ table d'ondes) n'était donc ni dans la fermeture ni relocalisée : avec WAVE élevé, le moteur lisait la vraie SRAM du Cycles.
  - Trouvé en émulation : le son différait pour WAVE 127, et la voix contenait des pointeurs `0x8000xxxx` non relocalisés.
  - Correction : `roots` dans le catalogue, et un garde-fou dans `analyse()` : toute adresse de code prise par `lea` doit être dans la fermeture, sinon la génération échoue.
- Source : `CATALOG["bits"]` et `analyse()` dans `tools/gen_syntakt_engines.py`.

## 3. Les firmwares déjà testés ne changent pas

- La copie dépend maintenant du **dernier moteur coché** (ordre du catalogue) : elle contient ce qu'il faut aux moteurs jusqu'à lui, et au moins jusqu'à SY TOY.
  - Sans SY BITS coché : même code, mêmes tables et même disposition qu'avant (229 376 o).
  - Avec SY BITS : code jusqu'à `0x400092ec`, tables de SY BITS à `0x43038000`, charge utile de 233 472 o.
- Les 127 empreintes du flasher d'avant ce travail sont retrouvées à l'identique, dont `247c8b46` (SYToy seul) et `8586b230` (les trois moteurs), testées sur la machine.
  - Source : `generation()` et `layout()` dans `tools/gen_syntakt_engines.py` ; comparaison des blocs `REF_MAINOS` avant et après.
- Le vrai décompresseur du bootstrap relit l'OS agrandi à l'identique ; il finit à `0x401e3140`, sous la zone de travail `0x40200000`.

## 4. Preuve en émulation

`tools/emu/test_syntakt_machines.py --tweak …`, sur les 8 combinaisons qui contiennent SY BITS : tout passe (26 à 29 vérifications selon le nombre de moteurs).
- **SYBit identique au SY BITS du Syntakt** sur 16 cas, écart max 1 LSB :
  - défauts, note 48 ;
  - Detune 40, 64, 88 ; Balance 0, 127 ; Rate Redux 64, 127 ; Waveform 0, 64, 127 ; DEC 90 ;
  - PUNCH actif = Bit Redux 80 ;
  - COLOR à 0 puis à 127 (hors plage) = Detune borné à 40 puis 88.
- Descripteur de Detune : plage 40..88, défaut 52.
- Changement de machine SYToy → SYBit : 52 / 102 / 0 / 21, DECAY 60.
- Avec les quatre moteurs : 10 machines, 10 repères de x = 55 à 122, sur la ligne du haut de l'écran MACHINES.
- Machine hors limites : enregistrement et potards de KICK ([20 §5](20-moteurs-syntakt-a-cocher.md)).
- Les tests des firmwares précédents passent toujours.

## 5. Flasher web

- 4ᵉ case : **SYBit — SY BITS**. 15 choix de moteurs, 255 combinaisons avec les autres mods.
- Choix marqués « Testé » : SDVtg seul, SDVtg + CPVtg, SYToy seul, SDVtg + CPVtg + SYToy. Les autres sont « Expérimental ».
- `tools/webflash_smoke.sh` reconstruit les 255 combinaisons dans la page et les compare à `REF_MAINOS`.
- Build `2026-09-30-15`.

## 6. Test sur la machine `[FAIT]` (SYBit seul)

**SYBit seul : testé le 30/09/2026** (`MAIN OS 7ace58bd`) ; retour de l'utilisateur : « SYBit seul marche nickel ». Les quatre moteurs ensemble n'ont pas été testés à part.

1. Sauvegarder les projets (Transfer). Remettre sur une machine d'origine les pistes qui utilisent une machine ajoutée : les numéros changent avec le choix de moteurs ([20 §5](20-moteurs-syntakt-a-cocher.md)).
2. Cocher **SYBit seul** : code `MAIN OS 7ace58bd`. Menu MACHINES : 7 machines, SYBit en dernier (image de TONE).
3. Choisir SYBit : valeurs 52 / 102 / 0 / 21, DECAY 60. Potards : « Detune », « Balance », « Rate Redux », « Waveform ».
4. Noter ce que l'écran affiche pour Detune (40 à 88 attendu) et vérifier que le potard s'arrête bien aux deux bouts.
5. Activer PUNCH : le son doit devenir plus granuleux (Bit Redux).
6. Ensuite, **les quatre moteurs** (`MAIN OS 9fa6a7de`) : 10 machines, 10 repères tous visibles sur la ligne du haut.

Retour en arrière : onglet *Official firmware*, par USB, après avoir remis les pistes sur des machines d'origine.

## 7. Suite

- SY SWARM (moteur 10) : quelques fonctions de plus, une dizaine de tables de 512 o, 4 immédiats en SRAM (pas de `0x94`) ; son emplacement `0x17` est « Fundamental Sub » (0 à 2).
- SP TWINSHOT (moteur 11) joue des samples : probablement plus difficile.
