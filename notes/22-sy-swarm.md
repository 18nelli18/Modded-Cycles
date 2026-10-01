# 22 · SY SWARM en machine « SYSwm »

Travail du 30/09/2026, à la demande de l'utilisateur : « SYBit seul marche nickel, passe à SY Swarm ».
SY SWARM est le moteur 10 du Syntakt. Il devient la 5ᵉ case de la carte « Vrais moteurs du Syntakt » du flasher ([20](20-moteurs-syntakt-a-cocher.md), [21](21-sy-bits.md)).

Adresses : MAIN OS Cycles 1.13 et programme audio du Syntakt 1.41 (section 7), comme dans les notes [17](17-portage-exact-syntakt.md) à [21](21-sy-bits.md).

## 0. En bref

| | État |
|---|---|
| SYBit seul sur la machine | `[FAIT]` testé par l'utilisateur le 30/09/2026 (« marche nickel ») ; marqué « Testé » |
| SY SWARM copié et relocalisé | `[FAIT]` 48 fonctions, 247 relocalisations (§2) |
| Les firmwares déjà testés restent identiques à l'octet près | `[FAIT]` 255 empreintes inchangées (§3) |
| **Preuve en émulation** | `[FAIT]` SYSwm identique au Syntakt sur 13 cas ; 16 combinaisons, 26 à 30 vérifications (§4) |
| Flasher : 5ᵉ case, 511 empreintes | `[FAIT]` build `2026-09-30-16` (§5) |
| Test sur la machine | `[FAIT]` SYSwm seul, le 30/09/2026 : « SYSwm seul marche nickel » (§6) |

## 1. SY SWARM dans le Syntakt

- Moteur 10 (type de machine 38) : update `0x400092ec`, render `0x400096e8`.
  - Source : tables des moteurs du programme audio (update `0x40014920`, render `0x400148f0`, entrée 10) ; table type → moteur `0x40014950` (entrée 38 = 10).
- Paramètres de l'interface du Syntakt (groupe « SSAW », section 3, `0x402305f4..0x40230760`) :

| Slot du Syntakt | Sur le Cycles | Nom du Syntakt | Nom affiché | Plage | Défaut |
|---|---|---|---|---|---|
| p1 (`0x13`) | COLOR | Noise Modulation (NMOD) | Noise Mod | 0 à 127 | 20 |
| p2 (`0x14`) | SHAPE | Detune Animation (ANIM) | Detune Anim | 0 à 127 | 15 |
| p3 (`0x15`) | SWEEP | Detune (DET) | Detune | 0 à 127 | 70 |
| p4 (`0x16`) | CONTOUR | Oscillator Mix (MIX) | Osc Mix | 0 à 127 | 127 |
| `0x17` | PUNCH | Fundamental Sub (SUB) | (pas de potard) | 0 à 2 | 2 |
| DEC (`0x19`) | DECAY | Decay | Decay | 0 à 127 | 75 |

  - Source : descripteurs de l'interface (pas de `0x34`), champs type, slot, plage, défaut et noms.
  - Noms longs raccourcis à des mots de 8 lettres au plus (« Modulation », « Animation » et « Oscillator » sont trop longs pour la fenêtre des potards, [18 §10](18-septieme-machine.md)).
- Nom de la machine : « SYSwm » (5 lettres, comme SYToy et SYBit). Image : celle de CHORD (l'OS n'en a que 6).

**Fundamental Sub** n'a pas de potard sur le Cycles. Ce qu'il fait, mesuré sur le moteur du Syntakt en émulation (note 48, énergie du signal par bande de fréquences) :
- 2 (défaut) : l'essentiel entre 90 et 180 Hz, à la note jouée ;
- 1 : l'essentiel entre 50 et 90 Hz, une octave plus bas ;
- 0 : l'essentiel entre 20 et 50 Hz, deux octaves plus bas.

Choix : **PUNCH inactif = 2** (le son par défaut du Syntakt), **PUNCH actif = 1** (sous-octave). Constantes `punch_off` / `punch_on` du catalogue ; bloc `#ifdef UPD_10` de `bridge_engines.c`.

## 2. Copie et relocalisation

- 7 fonctions de plus (48 au total) ; le code copié s'étend jusqu'à `0x400097dc`.
- 9 tables de 512 o (`0x4003ee38..0x40040038`), placées après celles de SY BITS.
- 4 immédiats sont des adresses de tampons en SRAM (`0x80009c58`, `…9cec`, `…9d80`, `…9e14`, pas de `0x94`), rangées dans la voix (+288, +416, +668).
- Le garde-fou des pointeurs de fonction ([21 §2](21-sy-bits.md)) ne signale rien.
- Charge utile de 238 080 o ; l'OS décompressé finit à `0x401e4340`, sous la zone de travail du bootstrap (`0x40200000`).
- Source : `CATALOG["swarm"]` dans `tools/gen_syntakt_engines.py`.

## 3. Les firmwares déjà testés ne changent pas

La copie dépend du dernier moteur coché ([21 §3](21-sy-bits.md)) : les 255 empreintes d'avant ce travail sont retrouvées à l'identique, dont celles testées sur la machine (`247c8b46` SYToy seul, `8586b230` les trois moteurs, `7ace58bd` SYBit seul).
- Source : comparaison des blocs `REF_MAINOS` avant et après.

## 4. Preuve en émulation

`tools/emu/test_syntakt_machines.py --tweak …` sur les 16 combinaisons qui contiennent SY SWARM, et sur SYBit seul.
Cas de son de SYSwm, comparés au SY SWARM du Syntakt :
- défauts, note 48 ;
- chaque potard aux extrêmes (NMOD, ANIM, DET 0 et 127 ; MIX 0 et 64) ; DEC 90 ;
- PUNCH actif (Fundamental Sub 1), à la note 60 et à la note 36.

Résultats :
- **SYSwm identique au SY SWARM du Syntakt** sur les 13 cas, écart max 1 LSB, dans chacune des 16 combinaisons.
- Les 16 combinaisons passent toutes leurs vérifications (26 à 30 selon le nombre de moteurs), SYBit seul aussi.
- Avec les cinq moteurs : 11 machines, 11 repères de x = 48 à 122 ; changement de machine SYBit → SYSwm : 20 / 15 / 70 / 127, DECAY 75.
- Le vrai décompresseur du bootstrap relit l'OS agrandi à l'identique (fin `0x401e4340`).

## 5. Flasher web

- 5ᵉ case : **SYSwm — SY SWARM**. 31 choix de moteurs, 511 combinaisons avec les autres mods.
- Choix marqués « Testé » : SDVtg seul, SDVtg + CPVtg, SYToy seul, SDVtg + CPVtg + SYToy, SYBit seul.
- `docs/flasher/tweaks.js` fait maintenant 1 Mo (un tweak complet par choix de moteurs). Il reste servi en une fois ; on pourra partager les parties communes si le chargement devient lent.
- Build `2026-09-30-16`.

## 6. Test sur la machine `[FAIT]` (SYSwm seul)

**SYSwm seul : testé le 30/09/2026** (`MAIN OS 2738b055`) ; retour de l'utilisateur : « SYSwm seul marche nickel ».
Plusieurs moteurs joués ensemble ralentissent la machine : voir [23](23-optimisation-charge.md).

1. Sauvegarder les projets. Remettre sur une machine d'origine les pistes qui utilisent une machine ajoutée ([20 §5](20-moteurs-syntakt-a-cocher.md)).
2. Cocher **SYSwm seul** : code `MAIN OS 2738b055`. Menu MACHINES : 7 machines, SYSwm en dernier (image de CHORD).
3. Choisir SYSwm : valeurs 20 / 15 / 70 / 127, DECAY 75. Potards : « Noise Mod », « Detune Anim », « Detune », « Osc Mix ».
4. Jouer : supersaw du Syntakt. Activer PUNCH : la sous-octave s'ajoute.
5. Ensuite, **les cinq moteurs** (`MAIN OS cbd55eca`) : 11 machines, 11 repères sur la ligne du haut de l'écran MACHINES, de x = 48 à 122.

## 7. Suite

SP TWINSHOT (moteur 11) joue des samples : il faut d'abord voir où le Syntakt range ses samples et ce que le moteur en attend.
