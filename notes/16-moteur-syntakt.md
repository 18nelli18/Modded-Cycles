# 16 · Le moteur audio du Syntakt, et le vrai SD VINTAGE en émulation

Travail du 29/09/2026, sur l'OS Syntakt 1.41 officiel (`Syntakt-OS-1.41.zip`, elektron.se), téléchargé avec l'accord de l'utilisateur et jamais versionné.
Suite de la [note 15 §4](15-demandes-reddit.md) : faire tourner le vrai SD VINTAGE du Syntakt dans un banc d'émulation, puis régler le nôtre ([note 14](14-machine-sd-vintage.md)) dessus.

## 0. En bref

| | État |
|---|---|
| Lire l'OS Syntakt (2 flux SysEx, conteneur ELE3 à 8 sections) | `[FAIT]` `tools/emu/syntakt.py` (§1) |
| Le Syntakt a **deux ColdFire** : interface (section 3) et **moteur audio** (section 7) | `[FAIT]` (§2) |
| Boucle des voix, tables de machines, init des voix du moteur audio | `[FAIT]` : **copie conforme du moteur Model:Cycles** (§3) |
| Paramètres de SD VINTAGE (noms, emplacements, plages, défauts) | `[FAIT]` depuis les descripteurs de l'interface (§4) |
| **Vrai SD VINTAGE en émulation** | `[FAIT]` `tools/emu/stengine.py` (§5) |
| Notre SD VINTAGE recalé sur le vrai (v2) | `[FAIT]` en émulation, à réécouter sur la machine (§6) |

## 1. Lire l'OS du Syntakt

- Même transport que les Models :
  - SysEx Elektron, produit `0x16`, paquets de 128 octets, 7 bits ;
  - constantes de checksum `V = 0x35`, `C0 = 0x2C`, trouvées par recherche exhaustive, qui valident tous les paquets.
- Particularité : **deux flux** de paquets (octet 7 = `0x00` puis `0x01`, le second avec `C0 - 1`). Mis bout à bout, ils forment un seul conteneur ELE3 de 2 028 880 o.
- `tools/emu/syntakt.py` vérifie le `.syx` officiel (SHA-256 `8e2488f4…`) et rend ses sections décompressées. `dsp_image()` renvoie la section 7 (SHA-256 `daf6451c…`).

> Source : dépaquetage de `Syntakt_OS1.41.syx` le 29/09/2026.

## 2. Deux processeurs

| Section | Taille | Chargée à | Rôle |
|---|---|---|---|
| 3 | 3 438 480 o | `0x40000400` | ColdFire principal : interface, séquenceur (noms de machines, descripteurs de paramètres) |
| 7 | 383 760 o | `0x40000400` | **second ColdFire : moteur audio**. Aucune chaîne de caractères, entrée à `0x40001070` |

- **Adresse de chargement de la section 7** : 45 des 46 cibles de `jsr`/`jmp` absolus tombent sur un début de fonction si la section est chargée à `0x40000400`, contre 1 sur 46 pour les autres bases essayées.
- **Démarrage** (`0x400004bc`) :
  - copie `0x4004f6e0..0x40057670` en SRAM `0x80000000`, puis `0x40057670..0x4005df10` en `0x80008000`, et remet le reste à zéro ;
  - le BSS va jusqu'à `0x4404f980` : le processeur audio a lui aussi 64 Mo de SDRAM.
- La **table de sinus Q31 de 257 points** du moteur Cycles est à l'offset `0x53e54`. La copie au démarrage l'installe en SRAM `0x80004b74`.

## 3. La boucle des voix : celle du Model:Cycles

`0x40004324(out, params, trig_mask, release_mask)`, appelée par bloc de 32 trames. C'est la boucle `0x400a7d4a` du Cycles ([14 §2.3](14-machine-sd-vintage.md)) :
- `MACSR = 0xA0` pendant la boucle, `0x20` après ;
- **8 voix** de 1 800 o à `0x80000000 + 1800·i`, triées par type de machine en début de bloc ;
- drapeaux `+0x34` (trig du bloc), `+0x38` (bloc de trig), `+0x3c` (fin de note), comme sur le Cycles ;
- paramètres de la piste `i` : `params + 142·i`, type de machine (0..45) en `+0x3e`, borné puis traduit en moteur 0..11 par la table d'octets `0x40014950` ;
- au changement de machine : remise à zéro `0x40003ee0(voix)` ;
- chaque bloc : `update[m](pmod, voix, params + 0x1c + 142·i)` puis `render[m](out + 128·i, voix)`. Tables `update` `0x40014920` et `render` `0x400148f0`, 12 entrées ; `pmod` de la piste `i` à `0x80008150 + 4·i` (note en demi-tons `<< 16`) ;
- init (`0x40000fd6`) : pour chaque voix, `0x40002544()`, puis `voix+0x56c = 0x80008a60 + 0x30·i` (petit tampon SRAM, comme `voix+0x318` sur le Cycles), puis remise à zéro.

Moteurs dédiés de la table :

| Type | Machine | Moteur (`update` / `render`) |
|---|---|---|
| 0–5 | BD MODERN, SD BASIC, CY ALLOY, PC CARBON, SY TONE, SY CHORD | 0–5 |
| **6** | **SD VINTAGE** | **6** : `0x40008074` / `0x4000847a` |
| 7 | CP VINTAGE | 7 |
| 36–38, 44 | SY TOY, SY BITS, SY SWARM, SP TWINSHOT | 8–11 |

Les autres types (machines analogiques, machines numériques plus anciennes) ne passent pas par cette boucle.

## 4. Les machines « FM » du Syntakt sont celles du Model:Cycles

Les descripteurs de paramètres de l'interface (section 3, table `0x4022eb90..0x40233c00`, 397 enregistrements de `0x34` o : emplacement, min, max, défaut en 8.8, noms) donnent, pour les types 0 à 7, la **disposition exacte des machines du Cycles**.
Le paramètre d'emplacement `s` est un mot 8.8 à `p + 2·s`, avec `p = params + 0x1c`, la même convention que le Cycles ([14 §2.2](14-machine-sd-vintage.md)) :

| Emplacement | Syntakt | Cycles (emplacement) |
|---|---|---|
| 18 | TUNE (40..88) | PITCH (`0x0a`) |
| 19, 20, 21, 22 | 4 potards propres à la machine | COLOR, SHAPE, SWEEP, CONTOUR (`0x0b`..`0x0e`) |
| 23 | PNCH (0..1) | PUNCH (`0x0f`) |
| 24 | **caché** : drapeau de maintien de l'enveloppe | GATE (`0x10`) |
| 25 | DEC | DECAY (`0x12`) |
| 26 | OVER (saturation) | — |

**Les défauts trahissent l'origine** :
- BD MODERN (10, 16, 16, 24) = KICK du Cycles ;
- SD BASIC (0, 127, 8, 0) = SNARE ;
- CY ALLOY, PC CARBON, SY TONE et SY CHORD suivent METAL, PERC, TONE et CHORD.

**Les 6 machines du Model:Cycles existent dans le Syntakt, sous d'autres noms.** SD VINTAGE et CP VINTAGE sont deux machines de plus, écrites pour ce même moteur.

**SD VINTAGE** (descripteurs `0x4022ff78..`, manuel du Syntakt OS 1.30 p. 89) :

| Potard | Nom | Emplacement | Plage | Défaut | Manuel |
|---|---|---|---|---|---|
| A | TUNE | 18 | 40..88 | 64 | décalage de la note, bipolaire |
| B | SWEP | 21 | 0..127 | 74 | balayage de la hauteur fondamentale |
| C | PNCH | 23 | 0..1 | 0 | enveloppe type compresseur |
| D | DEC | 25 | 0..127 | 33 | décroissance de l'enveloppe d'ampli interne |
| E | INHM | 19 | 0..127 | 0 | rapport des opérateurs |
| F | FCMP | 20 | 0..127 | 110 | « caractère de la force des modes de la caisse » |
| G | MENV | 22 | 0..127 | 80 | décroissance et profondeur de l'enveloppe de modulation |
| H | OVER | 26 | 0..127 | 0 | saturation numérique |

> Sources : descripteurs de l'OS Syntakt 1.41 (section 3) ; *Syntakt User Manual*, OS 1.30, annexe A « Machines », elektron.se.

- L'emplacement 24 n'est déclaré par aucune des 8 machines de cette famille.
- La boucle le recopie pourtant à chaque bloc dans `voix+0x3ec`, que la fonction d'enveloppe commune `0x40003d42` teste : s'il est non nul, l'enveloppe reste au maximum jusqu'à la fin de la note (GATE).
- Valeur retenue : **0**, le défaut.

## 5. Le banc : `tools/emu/stengine.py`

- Même principe que `mcengine.py` : Unicorn (m68k « ANY ») avec l'EMAC exacte de `tools/emu/emac.py` (2 289 instructions EMAC interceptées).
- Il charge la section 7, fait les copies du démarrage, initialise les 8 voix comme `0x40000fd6`, puis appelle la **vraie boucle des voix** bloc par bloc.
- `set(t, tune=…, p1=…, …)` écrit les paramètres en valeurs d'interface. `SDVN_DEFAULTS` = défauts de SD VINTAGE.
- Environ 0,05 s par bloc sur un Mac récent : 300 ms de son en 25 s.

**Le vrai SD VINTAGE aux réglages d'usine, note 60** :
- **Corps** accordé sur la note, qui la suit exactement : 133 / 264 / 529 Hz pour les notes 48 / 60 / 72.
- **Balayage** de hauteur : de 367 Hz (0–8 ms) à 310 Hz (10–30 ms), puis 264 Hz.
- **Amas aigu** dense et inharmonique entre 2 et 6 kHz (centre vers 5,3 kHz), **fixe quelle que soit la note**, à -3 dB sous le corps sur les 50 premières ms.
- Durées : -60 dB en 171 ms ; corps à -20 dB en 51 ms, amas en 60 ms.

> Source : rendus du banc, 29/09/2026 (`st_refs`, mesures de `sdv_metrics`).

## 6. Notre SD VINTAGE v2, recalé sur le vrai `[FAIT]`

Principe : **clean-room par la mesure**.
- On ne recopie ni le code ni les tables du Syntakt. SD VINTAGE y est une machine FM à 4 opérateurs, avec ses propres tables d'enveloppes indexées par DEC.
- On mesure son son dans le banc (§5), puis on règle les constantes de notre moteur C ([14 §3](14-machine-sd-vintage.md)) pour obtenir les mêmes mesures.
- Outil : `tools/emu/compare_sdvintage.py`. Il rend les deux moteurs avec les mêmes réglages, affiche les mesures côte à côte et écrit des WAV A/B.

**Ce que les mesures ont appris** (rendus du vrai, 29/09/2026) :

| Paramètre | Mesure | Dans la v2 |
|---|---|---|
| TUNE, note | corps exactement sur la note : 261,6 Hz pour la note 60, TUNE 64 | PITCH sans décalage (la v1 jouait 5 demi-tons plus bas) |
| SWEP | balayage `f = f0·(1 + D·e^(-t/T))` : D = 0,12 / 0,52 / 1,04 et T ≈ 50 / 18 / 49 ms pour SWEP 30 / 74 / 127 | SWEEP : table D = 1,04·(x/127)^1,4, T = 18 ms jusqu'à 74 puis jusqu'à 49 ms |
| DEC | durée à −40 dB : 29 / 84 / 117 / 172 / 269 / 564 ms pour DEC 0 / 20 / 45 / 75 / 100 / 127 | DECAY lit la table d'origine (le Syntakt a **la même**, octet pour octet) à un index recalé : 25, 35, 41, 45, 49, 53, 59, 68, 78 pour DEC 0, 16, …, 128 |
| corps / amas | le corps s'éteint un peu avant l'amas, et sonne plus longtemps quand DEC monte | décroissance propre du corps : τ 50 ms à DECAY 0, plus aucune à 127 |
| amas aigu | bruit passe-bande 1,5 – 8 kHz (centre 5,3 kHz), fixe quelle que soit la note, −3,2 dB sous le corps | 2 passe-haut 1,5 kHz + 2 passe-bas (g = 0,37) ; même centre, même niveau |
| FCMP | amas −7,0 / −9,9 / −3,2 dB pour 0 / 64 / 110 : **non monotone** | SHAPE : table de gains qui reproduit ces trois points |
| INHM | déplace les partiels, change peu le niveau | COLOR : 2e mode du corps de x2 à x2,8, amas +1,9 dB |
| MENV | harmoniques du corps (500 – 1 300 Hz) sur les 25 premières ms : ×2 entre 0 et 127 | CONTOUR : niveau (0,45 → 0,20) et durée (15 → 6 ms) du 2e mode |
| OVER | aucun effet sur la sortie de la machine : la saturation est appliquée plus loin | — |
| PNCH | raccourcit le son, comme le PUNCH du Cycles | chaîne PUNCH d'origine |

**Résultat aux réglages d'usine** (Syntakt → Cycles v2) :
- hauteur 367 → 310 → 264 Hz contre 366 → 307 → 264 Hz ;
- corps −20 dB en 51 contre 49 ms ; tout −40 dB en 110 contre 107 ms ;
- amas −3,2 contre −3,2 dB ; centre 5 291 contre 5 290 Hz.

Sur DEC 10 à 90, les durées restent à ±15 %. SWEP 127 : 512 contre 511 Hz au départ. FCMP 0 : amas −7,0 contre −6,9 dB. Tableau complet : `tools/emu/compare_sdvintage.py --cases all`.

Écarts connus :
- l'amas du vrai est fait de partiels FM, le nôtre est un bruit filtré de même spectre moyen ;
- à DEC ≥ 100, le vrai coupe l'amas vers 290 ms alors que le corps continue, ce que la v2 ne reproduit pas ;
- CONTOUR agit un peu plus fort que MENV (×2,8 contre ×2,0).

**Potards au sens du Syntakt**, défauts identiques :

| Cycles | = Syntakt | Défaut |
|---|---|---|
| PITCH | TUNE | 64 |
| COLOR | INHM | 0 |
| SHAPE | FCMP | 110 |
| SWEEP | SWEP | 74 |
| CONTOUR | MENV | 80 |
| DECAY | DEC | 33 |
| PUNCH, GATE | PNCH, (GATE caché) | 0 |

**Validation** :
- `tools/emu/test_sdvintage.py` passe (seuils tirés des mesures du Syntakt) : 5 615 instructions par bloc, contre 8 790 pour le SNARE d'origine.
- Code : 916 + 638 o dans les deux caves de 1 024 o.
- Compilation : `m68k-elf-gcc` 16.2 de Homebrew, désormais pris automatiquement par `tools/gen_sdvintage.py`.
- **À réécouter sur la machine** : la v1 a été validée sur le matériel, pas encore la v2.
