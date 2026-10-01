# 24 · Moteurs du Syntakt restants : SP TWINSHOT et les machines analogiques

Travail du 30/09/2026, à la demande de l'utilisateur : « repars sur le prochain moteur syntakt » (après SY SWARM, [22](22-sy-swarm.md)).
Conclusion : **plus aucun moteur du Syntakt ne peut être porté par copie.** Les 11 moteurs numériques portables le sont (les 6 du Cycles, SD et CP VINTAGE, SY TOY, SY BITS, SY SWARM). SP TWINSHOT a besoin d'échantillons absents du fichier d'OS, et toutes les autres machines sont analogiques.

Sources : Syntakt OS 1.41 (`Syntakt_OS1.41.syx`), sections décompressées par `tools/emu/syntakt.py`.

## 1. Ce que calcule le programme audio du Syntakt (section 7)

- Sa boucle des voix n'a que **12 moteurs** : une seule table de fonctions dans ses données, les 12 render puis les 12 update (`0x400148f0`, 24 entrées).
  - Source : recherche de toutes les suites de pointeurs vers du code dans la section 7.
- Table type de machine → moteur (`0x40014950`) :
  - types 0 à 7 → moteurs 0 à 7 (les 6 machines du Cycles, SD VINTAGE, CP VINTAGE) ;
  - 36, 37, 38 → 8, 9, 10 (SY TOY, SY BITS, SY SWARM) ;
  - 44 → 11 (SP TWINSHOT) ;
  - tous les autres types → 0.
- Noms des 45 types de machine : table de l'interface, section 3, `0x4022aefc` + 35 × 4, un nom tous les 8 o.
  - Types 8 à 33 : BD HARD, BD CLASSIC, BD FM, BD PLASTIC, BD SILKY, BD SHARP, SD HARD, SD CLASSIC, SD FM, SD NATURAL, RS HARD, RS CLASSIC, SY DUAL VCO, CP CLASSIC, CH/OH/CY/CB CLASSIC, CH/OH/CY/CB METALLIC, CY RIDE, HH BASIC, UT NOISE, UT IMPULSE.
  - Types 39 à 43 : SY RAW, SY CHIP, BD ACOUSTIC, SD ACOUSTIC, HH LAB.

## 2. SP TWINSHOT : pas faisable

- Réglages (descripteurs « SAMP », section 3, `0x40233a90..0x40233bfc`) : Tune 1, Sample 1, Filter 1, Mix, Tune 2 (40 à 88), Sample 2, Overdrive, Decay 1.
- Le code du moteur tient en 5 fonctions (update `0x400097dc`, render `0x40009a8a`), mais il lit ses échantillons en mémoire.
- Au démarrage, le programme audio reçoit un **bloc d'échantillons** en `0x4004f750`, envoyé par le processeur principal (`0x40000d7e` → `0x40009f08`).
  - Il en tire une table de **64 échantillons** (`0x40000d06`) : pour chacun, une longueur sur 4 octets suivie des échantillons en 16 bits ; pointeurs en `0x4404f758`, longueurs en `0x4404f754`.
  - Le moteur y lit ses deux échantillons (`0x40009972..0x400099b8`), jusqu'à 524 287 valeurs chacun.
- **Ce bloc n'est dans aucune section du fichier d'OS** : aucune chaîne crédible de 64 blocs « longueur + données » dans les sections 1, 3 et 8.
  - Source : recherche exhaustive ; la seule chaîne de 64 trouvée (section 3, `0x126d04`) est un faux positif (un bloc de 288 514 valeurs puis 63 de 16).
  - Les échantillons viennent probablement de la mémoire de stockage du Syntakt (contenu d'usine), absente du fichier d'OS.
- Même trouvés, ils ne tiendraient pas : l'OS du Cycles modifié finit déjà à `0x401e4340`, et il ne reste qu'environ 110 Ko avant la zone de travail du bootstrap (`0x40200000`). 64 échantillons de batterie pèsent facilement plus d'un mégaoctet.

## 3. Les autres machines sont analogiques

- L'OS principal du Syntakt (section 3) connaît trois types de voix : `"voice_type":"Analog Drum"`, `"Analog Cymbal"` et `"Digital"` (`0x4024b2c6..0x4024b2fe`).
- Il contient tout un système d'étalonnage des circuits analogiques :
  - « UNIT NEEDS CALIBRATION », « PERFORMING ANALOG CALIBRATION », « UPDATE OSCILLATOR CALIBRATION » (`0x4024b99c..0x40250c57`) ;
  - vues `AnalogCalibrationMenuView`, `AnalogControlView`, `VCADebugView`.
- Il a bien du code de calcul (5 078 instructions `mac`), et des tables d'une trentaine de fonctions (`0x402a1b54..0x402a1be0`) : sans doute le pilotage des voix analogiques (enveloppes, commandes des circuits).
  - Ce pilotage ne produit pas le son : ce sont les circuits qui le produisent.
- La section 8 est le firmware d'un **microcontrôleur ARM** (code Thumb ; « USB PD Task », « MIDI task », « Calib OK »). Ce n'est pas un moteur audio.

Donc, pour BD HARD, BD CLASSIC, SY DUAL VCO, SY RAW, les CLASSIC et METALLIC, etc., il n'y a pas de code de synthèse à copier. Les recréer sur le Cycles demanderait une imitation écrite de zéro (comme la SD VINTAGE « clean-room », [16](16-moteur-syntakt.md)), sans garantie de fidélité.

## 4. Bilan du portage exact

| Moteur du Syntakt | Sur le Cycles |
|---|---|
| BD MODERN, SD BASIC, CY ALLOY, PC CARBON, SY TONE, SY CHORD | les 6 machines d'origine (mêmes moteurs) |
| SD VINTAGE, CP VINTAGE, SY TOY, SY BITS, SY SWARM | SDVtg, CPVtg, SYToy, SYBit, SYSwm |
| SP TWINSHOT | impossible : échantillons absents et trop gros |
| les 31 machines analogiques | impossible par copie : ce sont des circuits |
