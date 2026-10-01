# 25 · Régulateur de charge

Travail du 01/10/2026. Retour de l'utilisateur sur le firmware de diagnostic v2 (arrêt des voix muettes, [23 §7](23-optimisation-charge.md)) :
« C'est beaucoup mieux, mais des fois il y a quand même quelques bugs ponctuels dans le son, et l'interface ralentie. Essaie d'implémenter une solution robuste. »

## 0. En bref

| | État |
|---|---|
| Régulateur de charge dans tous les tweaks générés | `[FAIT]` (§2), rendu plus réactif après le 1er essai (§5) |
| Preuve en émulation | `[FAIT]` `tools/emu/test_governor.py` et les tests existants (§3) |
| 1er essai sur la machine (v3) | `[FAIT]` beaucoup moins de bugs, encore quelques micro-gels (§5) |
| Test sur la machine de la version réactive (v4) | `[FAIT]` plus de micro-gels ; les coupures de notes restent un peu gênantes (§6) |

## 1. Pourquoi il en faut un

Mesures sur la machine ([23 §6 bis](23-optimisation-charge.md)), en % de la durée d'un bloc audio :
- mixage et effets : environ 30 % ;
- chaque voix d'origine qui sonne : environ 8 % ;
- chaque voix du Syntakt qui sonne : environ 15 %.

L'arrêt des voix muettes supprime le coût des voix qui se taisent, mais pas celui des voix qui sonnent. Dès que trop de voix sonnent ensemble :
- la fonction audio dépasse la durée d'un bloc, et le son accroche ;
- en moyenne au-delà d'environ 85 %, l'interface n'a plus assez de temps.

Rien ne peut l'empêcher à coup sûr, sauf **limiter ce qui est calculé en fonction de la charge mesurée** : c'est ce que font les synthés avec leur polyphonie (« vol de voix »).

## 2. Fonctionnement

Tout est dans `tools/machines/syntakt_bridge/bridge_engines.c` (C), avec deux détours en assembleur générés par `gen_syntakt_engines.py`.

**Mesure**
- La sonde de l'appel de la fonction audio par l'interruption (`jsr 0x4005979e` en `0x40059382`), validée sur la machine avec le compteur de charge ([23 §5](23-optimisation-charge.md)), est maintenant dans tous les tweaks générés.
- Après chaque bloc, `audio_end()` calcule la charge du bloc (minuteur DMA 0, 135,168 MHz, 90 112 ticks par bloc) et une moyenne glissante (1/8 par bloc, environ 5 ms).

**Décision**, pour chaque piste, dans le détour de la boucle des voix (`0x400a7dfe`) :
- `voice_gate()`, avant update/render : un trig remet la voix en service ; une voix éteinte ou restée faible trop longtemps n'est pas calculée (sortie à zéro).
- `voice_after()`, après render : fondu éventuel, crête des 32 échantillons, compteur de blocs faibles.

**Trois régimes** selon la charge moyenne :

| Charge moyenne | Une voix n'est plus calculée quand… | Voix éteintes de force |
|---|---|---|
| sous 72 % | elle est restée sous −108 dB pendant 64 blocs (43 ms), sans trig | aucune |
| 72 à 82 % | elle est restée sous −66 dB pendant 16 blocs (11 ms), sans trig | aucune |
| au-dessus de 82 %, ou un bloc au-dessus de 95 % | idem | la voix calculée la plus faible, par un fondu |

**Extinction de force**
- La voix choisie est celle de plus faible crête. Celle d'une voix du Syntakt compte pour moitié, puisqu'elle coûte deux fois plus.
- Jamais une note de moins de 16 blocs (11 ms).
- Fondu linéaire sur 8 blocs (5 ms), puis la voix n'est plus calculée jusqu'à son prochain trig.
- Une seule à la fois : la suivante n'est choisie qu'après la fin du fondu, si la charge est toujours trop haute.

**Mise en place**
- Toutes les variables de la passerelle sont en BSS (à zéro au démarrage) : la charge utile ne recopie pas de données initialisées.
- Le générateur refuse désormais une section `.data` non vide dans la passerelle.

## 3. Preuve en émulation

`tools/emu/test_governor.py` : le vrai `audio_end()` est appelé après chaque bloc, avec un minuteur simulé réglé sur la charge voulue. Référence : le même firmware sans régulation.
- **50 %** : sortie identique, aucune voix éteinte.
- **80 %** : une voix s'arrête dès qu'elle reste sous −66 dB. Sortie identique jusque-là, aucune extinction de force.
- **90 %**, 4 voix (SDVtg, SNARE, SYSwm, TONE, DECAY 100) :
  - 1er fondu au bloc 19, sur SYSwm, la plus faible (clés comparées au moment du choix) ;
  - puis SDVtg, TONE, SNARE, une à la fois ;
  - fondu linéaire de 1 à 0 à 1 % près, puis silence ; les voix non éteintes restent identiques ;
  - plus aucune extinction quand la charge redescend à 50 % ; SDVtg repart à son trig suivant.

Les tests existants passent toujours avec le régulateur : `test_syntakt_machines.py` sur plusieurs combinaisons, `test_idle.py` (arrêt des voix muettes, charge nulle en émulation) et `test_meter.py` (compteur).

## 4. Test sur la machine `[À FAIRE]`

1. Firmware de diagnostic v3 (compteur + régulateur + 5 moteurs), construit localement : `build/diag/model-cycles_OS1.13_diagnostic-charge_v3.syx` et `…_v3_6ch.syx`.
2. Rejouer les cas difficiles (plusieurs moteurs du Syntakt, sons longs).
3. Vérifier :
   - que le son n'accroche plus ;
   - que l'interface reste fluide ;
   - que « pic/moyenne » reste sous environ 95/82 ;
   - si des fins de notes disparaissent de façon audible.
4. Si des voix s'éteignent trop tôt, ou si le son accroche encore, les seuils (72 / 82 / 95 %) se règlent dans `bridge_engines.c`.

## 5. 1er essai, et un régulateur plus réactif

**Retour de l'utilisateur (01/10/2026)**, firmware de diagnostic v3 : « Avec 6 pistes custom engine, j'ai un ratio atteignant jusqu'à 99/67. Il y a beaucoup moins de bugs mais toujours quelques petits freezes audio. »
- La moyenne (67 %) est bonne ; ce sont des **blocs isolés** qui débordent (99 est le maximum affiché).
- Six voix du Syntakt qui sonnent ensemble demandent environ 30 % + 6 × 15 % = 120 % d'un bloc.

**Pourquoi la v3 laissait passer des gels** : elle n'éteignait qu'une voix à la fois, avec un fondu de 8 blocs pendant lesquels la voix coûte encore, et attendait la fin du fondu pour en éteindre une autre. Il fallait donc environ 16 blocs (11 ms) pour libérer 2 voix : autant de blocs en surcharge.

**Version réactive** (`bridge_engines.c`)
- **Coût réel de chaque voix** : `voice_gate()` et `voice_after()` lisent le minuteur autour d'update/render. Moyenne glissante (1/4) en ticks, sur la machine, cache compris.
- **Temps à libérer** : (charge − 78 %) × durée du bloc, moins le coût des voix déjà en cours d'extinction.
- **Extinction** : on éteint, des plus faibles aux plus fortes (Syntakt compté pour moitié), autant de voix qu'il faut pour couvrir ce temps. Au plus 2 par bloc, puis on remesure.
- **Déclenchement** : charge moyenne au-dessus de 82 %, ou un bloc au-dessus de 90 %.
- **Surcharge sévère** (un bloc au-dessus de 92 %) : fondu de 2 blocs (1,3 ms), et une note de plus de 4 blocs (2,7 ms) peut être éteinte. Sinon, fondu de 8 blocs et notes de plus de 16 blocs.
- Les voix pas encore arrêtées mais muettes (piste jamais jouée) sont les plus faibles : elles partent en premier. Elles coûtent pourtant environ 8 % chacune pour les machines d'origine.
- Rien n'est pris sur les pistes déjà arrêtées.

**Preuve en émulation** (`test_governor.py`, chaque voix calculée coûte un temps simulé) :
- 50 % et 80 % : comme avant.
- **90 %** : au bloc 18, extinction simultanée des 2 voix les plus faibles, SDVtg et SYSwm (les voix du Syntakt, comptées pour moitié), fondu de 8 blocs ; les autres suivent aux blocs suivants tant que la charge simulée reste haute ; plus rien quand elle retombe.
- **95 %** : dès le bloc 3, les 2 voix muettes pas encore arrêtées (pistes 5, 6), fondu de 2 blocs ; puis les autres par 2 ; fondus linéaires ; voix non éteintes identiques ; retrig correct.

**Limite physique** : quand 6 notes du Syntakt partent sur le même pas, le 1ᵉʳ bloc reste au-dessus de 100 % (une note déclenchée doit être calculée). Le régulateur ramène la charge en 3 ou 4 blocs (2 à 3 ms) au lieu de 11 ms, au prix de fins de notes coupées sur les voix les plus faibles.

## 6. Test sur la machine de la version réactive `[FAIT]`

Firmware de diagnostic v4 (`build/diag/model-cycles_OS1.13_diagnostic-charge_v4.syx`), 01/10/2026.
- Retour de l'utilisateur : plus de micro-gels.
- Mais « les coupures des notes sont un petit peu gênantes, même si c'est déjà beaucoup mieux ».
- Décision : publier le flasher web (PR #11), puis retravailler la gestion de la charge.

## 7. Pistes pour couper moins de notes

- **Rendre les voix du Syntakt moins chères** (`[FAIT]` en émulation, [26](26-sram-empruntee.md)) : chacune coûte environ 2 voix d'origine, à cause de la mémoire (SDRAM au lieu de la SRAM interne, [23 §4](23-optimisation-charge.md)). Piste : emprunter, pendant le calcul d'une voix du Syntakt, la zone de travail commune des machines d'origine en SRAM (environ 2 Ko, réécrite à chaque bloc par chaque voix d'origine).
- **Mieux choisir et mieux fondre** : préférer les voix les plus anciennes ; allonger le fondu quand la surcharge est modérée ; réserver le fondu court aux vrais débordements.
- **Seuils** : partir plus près de 100 % (le Cycles d'origine tient 87 % en pic) en surveillant les débordements avec le compteur.
