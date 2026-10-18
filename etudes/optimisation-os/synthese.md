# Optimiser l'OS d'origine du Model:Cycles : synthèse

Étude du 17-18/10/2026, à la demande de Maxime : « y'a forcément un travail d'organisation lourd et efficace qui
permettrait d'économiser et d'améliorer la stabilité, même dans l'optimisation de l'OS natif. Creuse cette partie-là. »

Quatre études en parallèle sur le vrai code de l'OS 1.13 officiel, désassemblé et exécuté en émulation (Unicorn).
Leurs rapports complets sont dans ce dossier :

| Étude | Rapport | Ce qu'elle couvre |
|---|---|---|
| Voix | [voix/rapport.md](voix/rapport.md) | boucle des voix, 6 machines, lissage, LFO |
| Sortie | [sortie/rapport.md](sortie/rapport.md) | Volume + Dist, mixeur, envois, delay, reverb, master, codec |
| Système | [systeme/rapport.md](systeme/rapport.md) | interruptions, tâches, écran, caches, SRAM, séquenceur |
| Stabilité | [stabilite/rapport.md](stabilite/rapport.md) | gels, débordements, piles, MIDI, carte SD |

**Aucun résultat sur la machine.** Les gains sont ceux du modèle de cache des notes 27-28 (1,54 cycle par instruction,
15 cycles par ligne de SDRAM). Le modèle tient la route : le bloc entier émulé donne 79 %, la machine mesure 77 % ; delay
et reverb donnent 11,7 %, la machine environ 12 %. Mais il a déjà surestimé un gain (note 28 : −11,5 points prédits,
environ −8 mesurés) : compter **environ 70 % des gains annoncés** tant qu'ils ne sont pas mesurés.

## 1. Où part le temps (OS d'origine, 6 pistes qui jouent, réglages par défaut)

| Poste | % d'un bloc (modèle) | Remarque |
|---|---|---|
| Boucle des voix | ~52 | les 6 voix sont calculées à chaque bloc, même muettes, même jamais déclenchées |
| Étage de sortie | 28,7 | **constant** : même coût en silence, avec 1 ou 6 pistes, avec ou sans effets |
| Début d'interruption, séquenceur, lissage, LFO | ~3 | séquenceur 0,4 % à vide, 3,4 à 6 % au pire (6 trigs, 10 p-locks) |
| Interruptions qui coupent l'audio (panneau 12 kHz, USB, DMA) | 1 à 1,5 | peu à gagner |
| **Total** | **~79** | la machine mesure 77 % de moyenne, même à l'arrêt |

Deux constats d'organisation :
- **L'OS fait tout le travail tout le temps.** À l'arrêt, il calcule 6 KICK de silence, un delay et une reverb qui ne
  reçoivent rien, un saturateur de Dist à 0, des envois à gain nul.
- **Le code audio ne tient pas dans le cache.** Un bloc exécute 17,4 Ko de code différent pour un cache d'instructions de
  8 Ko : presque chaque ligne de code est relue en SDRAM à chaque bloc (environ 10 % d'un bloc perdu).

## 2. Les optimisations, classées

« Exact » = sortie identique à l'échantillon près, prouvée en émulation contre l'OS d'origine.

| # | Optimisation | Gain (modèle) | Son | État |
|---|---|---|---|---|
| 1 | **Arrêt des voix muettes** pour l'OS seul : une voix sous −108 dB et sans trig n'est plus calculée | −42 à −47 points à l'arrêt ; −30 points 1,6 s après des notes ; ~0 quand les 6 voix sonnent sans arrêt | exact tant que la voix tourne ; ensuite 0 au lieu de moins de −108 dB | prototype prouvé (204 o, masque libre `0x40185f48`) |
| 2 | **Sommeil du delay et de la reverb** quand rien n'y entre ni n'en sort | −8 à −9 points | exact | prototype prouvé ; ne s'endort que si l'effet n'a pas servi depuis l'allumage (voir 3) |
| 3 | Purge des restes du delay et de la reverb, pour que le n° 2 serve aussi après usage | −8 points, 1 à 3 s après la fin de l'entrée | non exact : restes à −111 dBFS mis à 0 | conçu, sans prototype |
| 4 | **Saturateur de Dist sauté quand Dist est à 0** | −3,9 points | exact | prototype prouvé |
| 5 | **Envois sautés quand leur gain est nul** | −1,9 point | exact | prototype prouvé |
| 6 | **mix2 sans sa boucle morte** : la 1ʳᵉ boucle écrit une sortie que la 2ᵉ réécrit en entier | −2,2 à −3,3 points | exact à l'octet près | prototype prouvé (Model-TG fait déjà l'équivalent) |
| 7 | **PUNCH éteint par un chemin court** | −1,0 à −1,2 point | exact à l'octet près | prototype prouvé |
| 8 | **SRAM réorganisée** : les 30 Ko de tables de CHORD en SDRAM (comme la note 28), le code chaud de l'OS à leur place | −5 à −9 points, tout le temps | exact | modélisé ; incompatible avec les moteurs du Syntakt, qui occupent déjà cette SRAM |
| 9 | Lissage des paramètres sauté à son point fixe | jusqu'à −1,5 point | exact (point fixe prouvé) | conçu |
| 10 | Opérateur `0x400a8204` réécrit (26 à 37 % de la boucle des voix) | −0,8 point | exact à prouver | chiffré |
| 11 | Moitié du cache verrouillée | −1,7 à −4,6 points | exact | à mesurer : l'interface perdrait la moitié des caches |
| 12 | Écran : horloge SPI doublée | interface seulement (jusqu'à 0,75 ms par image redessinée) | sans effet sur le son | idée ; vitesse maximale de l'écran inconnue |

Écartées : aligner ou réordonner le code (le cache manque de place, ce n'est pas un conflit), descendre le panneau sous
le niveau de l'audio (scintillement des LED), regrouper l'USB, recopier des tables en SRAM (≤ 0,13 %).

### Ce que ça donne ensemble (modèle, OS d'origine)

| Situation | Aujourd'hui | Avec 1, 2, 4, 5, 6, 7 | Avec aussi 8 |
|---|---|---|---|
| À l'arrêt, effets jamais utilisés | ~80 % | ~20 % | moins encore |
| 6 pistes qui jouent, Dist à 0, effets jamais utilisés | ~79 % | ~61 % | ~52-56 % |
| 6 pistes qui jouent, Dist à 0, delay et reverb en service | ~79 % | ~70 % | ~61-65 % |

À comparer avec 44,1 kHz : 6 à 8 points, et tout désaccordé. Même dans le cas le plus chargé, les optimisations exactes
font mieux, sans rien changer au son.

Pour les firmwares avec moteurs du Syntakt ou Model-TG : ils ont déjà leur arrêt des voix muettes, et Model-TG a déjà
son propre sommeil des effets (non exact) et l'équivalent du n° 6. Les n° 2, 4, 5 et 7 s'y ajouteraient, à vérifier
mod par mod (les détours ne touchent aucune écriture des 282 tweaks actuels).

## 3. Stabilité

| # | Défaut | Gravité | Correctif | État |
|---|---|---|---|---|
| D1 | **MACHINES gèle** quand une piste a une machine que le firmware n'a pas (projet fait avec MACRO, ACID, moteurs du Syntakt, rouvert ailleurs). Bug de l'OS d'Elektron, présent dans l'OS officiel et recopié dans Model-TG : les accesseurs `0x4004df5c` et `0x4004df76` renvoient l'entrée −1, 76 o avant le tableau des machines | haute (constaté par Maxime le 12/10) | `moveq #-1` → `moveq #6` en `0x4004df66` et `0x4004df80` (4 octets), 3 de plus dans la copie de Model-TG | prouvé en émulation |
| D2 | **Gel complet** (son compris) après une longue surcharge : l'horloge MIDI sortante attend à IPL 7 (`0x4000123a..0x40001246`) une place dans un anneau que seul le niveau 4, masqué, peut vider | moyenne (1 024 tops sans service : 4,7 s à 546 BPM, 21 s à 120 BPM) | `bgt.s` → sortie en `0x40001246` (2 octets) : l'octet est perdu au lieu de tout figer | prouvé en émulation |
| D3 | Un bloc au-dessus de 100 % est perdu sans trace ; l'heure musicale et l'USB restent en retard d'un bloc pour toujours. Avec l'audio USB 6 canaux, un seul retard laisse la file hors de son anneau : flux abîmé jusqu'à son redémarrage | moyenne | compteur de dépassements et rattrapage ; régulateur de file dans `feed.S` | simulé sur le vrai pilote USB ; correctif à écrire |
| D4 | Piles : les interruptions s'empilent sur la tâche en cours ; la plus petite a 2 Kio, avec les globales du noyau juste en dessous | faible à moyenne pour les mods qui ajoutent du code profond | budget de pile vérifié en émulation pour chaque mod | mesure partielle |
| D5 | Carte SD/eMMC : erreurs ni activées ni traitées, attentes sans délai, y compris à l'extinction | faible | gros travail | lecture du code |

Pas de chien de garde dans l'OS : déconseillé d'en ajouter un (un redémarrage perdrait l'état non sauvegardé).

Corrections à reporter dans les notes : notes/18 l.174 (« aucun plantage attendu » est faux, D1).

## 4. Ce qu'il faudrait mesurer sur la machine

Un firmware de mesure de l'OS d'origine :
- un compteur de temps libre de 44 octets à la place de la boucle d'attente `0x4000543a` (prototype prouvé) : il dit
  combien il reste vraiment à l'interface ;
- des sondes sur l'attente du DMA des effets (`0x4005697e`), l'écran et la flash ;
- la charge avec et sans les optimisations exactes, sur un projet sans effets ni Dist, puis avec.

## 5. Ordre proposé

1. **Correctifs de gel D1 et D2** : quelques octets chacun, prouvés, sans effet sur le son ni la charge.
2. **Optimisations exactes et petites** : 4, 5, 6, 7, puis 2.
3. **Arrêt des voix muettes** pour l'OS seul (1), et la purge des effets (3) : les plus gros gains au repos.
4. **SRAM réorganisée** (8) : le plus gros gain quand tout joue, mais le plus gros travail.
5. Mesurer sur la machine entre chaque étape.

Rien n'a été modifié dans le dépôt. Les prototypes (`*/proto/*.S`) et les bancs de preuve (`*.py`) sont dans ce dossier.
