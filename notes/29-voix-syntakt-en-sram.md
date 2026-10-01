# 29 · Les états des voix du Syntakt en SRAM

Travail du 01/10/2026, après les relevés de l'utilisateur avec le firmware de diagnostic v7 ([28 §5](28-code-syntakt-en-sram.md)).

## 0. En bref

| | État |
|---|---|
| Relevés v7 sur la machine | `[FAIT]` chaque voix du Syntakt coûte maintenant autant qu'une voix d'origine ; 6 pistes : notes coupées de temps en temps (§1) |
| États des 6 voix du Syntakt en SRAM | `[FAIT]` (§2) |
| Preuve en émulation | `[FAIT]` (§3) |
| Gain estimé | environ −3 points de bloc avec 5 ou 6 voix du Syntakt (§4) |
| Mesure sur la machine | `[À FAIRE]` firmware de diagnostic v8, affichage « pic/moyenne » (§5) |

## 1. Relevés du diagnostic v7 (01/10/2026)

Retour de l'utilisateur, « moyenne/voix » en % de la durée d'un bloc, comparé à la v6 ([28 §1](28-code-syntakt-en-sram.md)) :

| Pistes qui jouent | v6 | v7 |
|---|---|---|
| SDVtg | 42/10 | 40/7 |
| + CPVtg | 54/11 | 50/7 |
| + KICK | — | 60/8 |
| + SYToy | 76/7 (sans KICK, avec une 3ᵉ machine ajoutée) | 68/6 |
| + SYBit | coupures | 78/8 |
| + SYSwm (6 pistes) | — | 74/9, « les notes se coupent quelquefois » |

- « La machine CHORD fonctionne normalement » : ses tables d'ondes, lues en SDRAM, ne changent rien à son son.
- **Ce qu'on en tire** :
  - Chaque voix du Syntakt ajoutée coûte maintenant **8 à 10 points**, au lieu de 9 à 13 : autant que KICK (+10).
  - Avec 6 pistes, la moyenne affichée (74) **baisse** parce que le régulateur coupe des voix. La demande est d'environ 78 + 10 = **88 %**, au-dessus du seuil de coupure (86 %).
  - Le coût d'une voix est maintenant fait surtout d'**instructions** (6 600 à 10 400 par bloc et par voix, [27 §2](27-cinq-et-six-voix.md)), que la mémoire ne réduit pas. Il ne reste à gagner que quelques points.

## 2. Ce qui change

- **`[FAIT]`** L'état d'une voix du Syntakt (1 800 o) est lu et réécrit à chaque bloc : de 34 à 66 lignes de 16 o, dont la plupart modifiées. Elles devaient donc être relues puis réécrites en SDRAM ([27 §2](27-cinq-et-six-voix.md)).
- Les états des **6 voix des pistes** passent en SRAM, dans la place libérée par les tables d'ondes de CHORD ([28 §2](28-code-syntakt-en-sram.md)) :
  - 2 dans la 1ʳᵉ zone, après le code et les tables (`0x800062b4`, `0x800069bc` pour la génération à 5 moteurs) ;
  - 4 dans la 2ᵉ zone, jusque-là libre (`0x8000cac0` + 1 800 k).
- Leur contenu de départ est celui de la SRAM du Syntakt (comme dans la réplique). Le crochet de démarrage recopie maintenant les deux zones, 22 616 + 8 224 o, depuis le début de la charge utile.
- La passerelle (`st_voice()`) donne ces adresses aux 6 voix. Les voix 6 et 7 du Syntakt, initialisées comme sur le Syntakt mais jamais jouées, restent dans la réplique.
- La taille de la charge utile ne change pas : la zone de transit grandit, mais les tables du bas tiennent toujours sous la réplique de la SRAM.

## 3. Preuve en émulation

- `test_sram_code.py` vérifie en plus qu'aucune voix du Syntakt ne lit ni n'écrit l'ancienne place des états des 6 voix dans la réplique.
- `boot_hook_ok()` vérifie les deux zones recopiées par le crochet de démarrage, et que le reste de la SRAM est intact.
- La sortie des 6 pistes (5 moteurs du Syntakt et CHORD) est identique, échantillon par échantillon, à celle du firmware de la note 28.

**Tests**, sur les 31 tweaks régénérés : tout passe.
- `test_syntakt_machines.py` sur 9 combinaisons : les 5 moteurs restent identiques au Syntakt (écart max 1 LSB) ; crochet de démarrage et décompresseur du bootstrap vérifiés.
- `test_sram_code.py` (5 moteurs : 12 vérifications ; `syntakt-sd` : 6), `test_sram_scratch.py`, `test_idle.py`, `test_governor.py`, `test_meter.py` (« pic/moyenne »).
- Flasher web : 511 combinaisons, `webflash_smoke.sh` ALL OK (588 vérifications). Les anciens tweaks sont identiques à l'octet près.

## 4. Gain attendu

Simulation de cache de [27 §2](27-cinq-et-six-voix.md), boucle des voix seule :

| Pistes 1 à 6 | Note 28 | Note 29 |
|---|---|---|
| SDVtg, CPVtg, KICK, SYToy, SYBit, SYSwm (relevé v7) | données 400, code 33 lignes : 52,2 % | données 82, code 33 : **49,4 %** |
| SDVtg, CPVtg, SYToy, SYBit, SYSwm, SDVtg | données 408, code 0 : 52,7 % | données 43, code 0 : **49,4 %** |

- Source : `cachesim.py`, `groups3.py` (scripts de travail).
- Les voix du Syntakt ne lisent presque plus rien en SDRAM. Il reste surtout leurs instructions.
- Sur le motif à 6 pistes du §1, la demande passerait d'environ 88 à 85 %, juste sous le seuil de coupure (86 %).
- Il resterait des coupures quand les 6 notes partent sur le même pas : un bloc isolé au-dessus de 90 % déclenche aussi le régulateur (`PEAK`). D'où l'affichage du pic dans le diagnostic v8.

## 5. Firmware de diagnostic v8 `[À FAIRE]`

Construit localement :
- `build/diag/model-cycles_OS1.13_diagnostic-charge_v8.syx` (MAIN OS `19f43218…`) ;
- `…_v8_6ch.syx` avec l'audio USB 6 canaux (MAIN OS `6ae4718e…`).

Le nom de toutes les machines redevient **« pic/moyenne »**, comme en v5 (`METER_VOICE = False` dans `gen_syntakt_engines.py`). Les coûts par voix sont connus (§1).

À relever :
1. Le motif à 6 pistes de la v7 : pic/moyenne, et y a-t-il encore des coupures ? Le son craque-t-il ?
2. Si possible, 6 voix du Syntakt (par exemple SDVtg sur la 6ᵉ piste à la place de KICK).
3. L'interface reste-t-elle fluide ?
