# 30 · Régulateur : couper sur la charge soutenue, pas sur les moments denses

Travail du 01/10/2026, après le relevé de l'utilisateur avec le firmware de diagnostic v8 ([29 §5](29-voix-syntakt-en-sram.md)).

## 0. En bref

| | État |
|---|---|
| Relevé v8 (version 6 canaux) | `[FAIT]` 91/71 sur le motif à 6 pistes, la dernière piste toujours coupée (§1) |
| Cause des coupures | `[FAIT]` le régulateur réagissait aux moments denses (moyenne sur 5 ms, blocs au-dessus de 90 %), pas à la charge soutenue (§1) |
| Nouvelle règle | `[FAIT]` charge soutenue sur environ 170 ms, pic à 93 %, voix du Syntakt plus comptées pour moitié (§2) |
| Preuve en émulation | `[FAIT]` (§3) |
| Essai sur la machine | `[À FAIRE]` firmware de diagnostic v9 (§5) |

## 1. Relevé du diagnostic v8 (01/10/2026)

Retour de l'utilisateur : la **version 6 canaux** de la v8 (`…_v8_6ch.syx`), le même motif à 6 pistes qu'en v7 ([29 §1](29-voix-syntakt-en-sram.md)).
- « La dernière est toujours coupée. La valeur est 91/71. » (pic/moyenne, en % de la durée d'un bloc)
- La v7 essayée avant était la version **sans** 6 canaux.

**6 canaux ou pas** :
- Le mod 6 canaux ([01](01-ms-multi-output.md), [13](13-6ch-upgrade-usb.md)) fait copier les 6 pistes vers l’USB, par le pilote USB.
- Le compteur mesure la durée réelle de la fonction audio, du début à la fin : une interruption qui la coupe (l'USB, par exemple) s'y ajoute.
- Les relevés avec et sans 6 canaux ne se comparent donc pas directement : il faudrait le même motif sur les deux versions pour connaître le coût du mod 6 canaux.

**Pourquoi la dernière piste est coupée** :
- La moyenne sur 0,5 s n'est que de 71 %, avec une voix coupée la plupart du temps : la demande soutenue est d'environ 71 + 9 ≈ **80 %**. Il y a de la marge.
- Mais le régulateur ([25](25-regulateur-de-charge.md)) réagissait à des moments, pas à la charge soutenue :
  - sa « moyenne » glissante (1/8 par bloc) ne porte que sur **environ 5 ms** : dans les moments où les 6 voix sonnent ensemble, elle dépasse 86 % ;
  - et **tout bloc au-dessus de 90 %** déclenchait une extinction. Le pic relevé est 91 %, **sans craquement entendu**.
- Le choix de la voix à couper comptait les voix du Syntakt pour moitié. C'était justifié quand elles coûtaient deux fois plus ([25 §2](25-regulateur-de-charge.md)), plus maintenant (6 à 9 % contre 8 % pour KICK, [29 §1](29-voix-syntakt-en-sram.md)). La voix du Syntakt la plus faible partait donc toujours la première.

**Ce qu'on sait des limites** :
- Le son craque quand un bloc approche 100 % : micro-gels avec des pics à 99 %, diagnostic v3 ([25 §5](25-regulateur-de-charge.md)).
- L'interface ralentit quand la charge **soutenue** est trop haute. Elle était encore fluide vers 86 % (diagnostic v6, [28 §1](28-code-syntakt-en-sram.md)).
- Un bloc à 91 % ne fait pas craquer (ce relevé).

## 2. Nouvelle règle

`bridge_engines.c`, seuils dans `GOV` de `gen_syntakt_engines.py`, en % de la durée d'un bloc :

| Ce qui déclenche une extinction | Avant | Maintenant |
|---|---|---|
| Charge soutenue (l'interface manquerait de temps) | moyenne sur environ 5 ms au-dessus de 86 %, retour à 82 % | **moyenne lente** (1/256 par bloc, environ 170 ms) au-dessus de 86 %, retour à 82 % |
| Un bloc trop long (le son pourrait craquer) | au-dessus de 90 %, retour à 82 % | au-dessus de **93 %**, retour sous **89 %** (93 − 4) |
| Fondus courts (2 blocs) et notes de plus de 4 blocs | un bloc au-dessus de 92 % | un bloc au-dessus de **96 %** |
| Voix choisie | la plus faible, voix du Syntakt comptées pour moitié | **la plus faible** |

- La moyenne rapide (environ 5 ms) sert toujours à l'arrêt anticipé des fins de notes sous −66 dB (au-dessus de 72 %), inaudible.
- Un bloc au-dessus de 93 % ne fait plus éteindre que le nécessaire pour repasser sous 89 % : en général une voix, au lieu de tout ce qui dépasse 82 %.
- Les notes de moins de 16 blocs (11 ms) restent protégées. Le bloc d'un trig, souvent le plus chargé, ne peut donc pas faire couper la note qui démarre.

## 3. Preuve en émulation

`tools/emu/test_governor.py`, réécrit pour cette règle (`audio_end()` réel, minuteur simulé) :
- 50 % : sortie identique, aucune voix éteinte ;
- 80 %, puis **91 % pendant 300 blocs** (moyenne lente partie de 0) : seules les voix restées sous −66 dB s'arrêtent, **aucune extinction de force** ;
- **charge soutenue** à 88 % (moyenne lente déjà à 88 %) : au bloc 18, extinction des 2 voix les plus faibles, juste assez pour revenir à 82 %, fondu de 8 blocs ;
- **bloc à 95 %** : idem, pour repasser sous 89 % ;
- **bloc à 97 %** : dès le bloc 3, fondus de 2 blocs ;
- dans tous les cas : fondu linéaire puis silence, autres voix identiques, plus rien quand la charge retombe, et la voix éteinte repart à son trig.

**Tests**, sur les 31 tweaks régénérés : tout passe.
- `test_governor.py` : 6 vérifications.
- `test_syntakt_machines.py` sur 9 combinaisons (moteurs identiques au Syntakt), `test_sram_code.py`, `test_sram_scratch.py`, `test_idle.py`, `test_meter.py`.
- Flasher web : 511 combinaisons, `webflash_smoke.sh` ALL OK (588 vérifications). Le test attend maintenant que les scripts de la page soient chargés : avec `tweaks.js` à 1,2 Mo, 300 ms ne suffisaient plus sur une machine occupée.

## 4. Ce qui reste à vérifier

- Les blocs entre 90 et 93 % ne font plus couper. Si le son craquait déjà dans cette zone, on l'entendra en v9 : il faudrait alors redescendre le seuil.
- La charge soutenue peut maintenant dépasser 86 % pendant quelques dizaines de millisecondes : l'interface devrait le supporter (moyenne lente).
- Le coût du mod 6 canaux reste inconnu (§1).

## 5. Firmware de diagnostic v9 `[À FAIRE]`

Construit localement, affichage « pic/moyenne » comme la v8 :
- `build/diag/model-cycles_OS1.13_diagnostic-charge_v9.syx` (MAIN OS `7e6dcf23…`) ;
- `…_v9_6ch.syx` avec l'audio USB 6 canaux (MAIN OS `87f87420…`).

À relever, sur le motif à 6 pistes :
1. Avec la version 6 canaux : y a-t-il encore des coupures ? Le son craque-t-il ? Valeur pic/moyenne ? L'interface reste-t-elle fluide ?
2. Si possible, la même chose avec la version sans 6 canaux : l'écart des deux moyennes donne le coût du mod 6 canaux.
