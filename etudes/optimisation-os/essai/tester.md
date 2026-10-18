# Essai sur la machine : ce que valent les optimisations de l'OS 1.13

Deux firmwares d'essai pour ton Model:Cycles. Ce ne sont pas des mods du flasher : pas de carte, rien dans le dépôt.
À flasher l'un après l'autre, avec le même projet, pour mesurer l'écart.

| Fichier | Contenu | SHA-256 du MAIN OS |
|---|---|---|
| `model-cycles_OS1.13_essai-reference.syx` | OS 1.13 officiel + compteur de charge | `a5ba4798d2a1131e0866ec2bbd7c523c2e0d9041c6aed322da0916d9a7286131` |
| `model-cycles_OS1.13_essai-optimise.syx` | le même compteur + correctifs de gel D1 (MACHINES) et D2 (horloge MIDI) + saturateur de Dist sauté quand Dist est à 0, envois nuls sautés, sommeil du delay et de la reverb, mix2 sans sa boucle morte, PUNCH à 0 par un chemin court, arrêt des voix muettes | `b9b85a7623ff8e2cb7fd1556149ab13bdd1882fc0d8161ec76d821ac22855adc` |

Le compteur est le même code, aux mêmes adresses, dans les deux fichiers. Seule la section 3 (MAIN OS) change :
bootloader, updater et menu de démarrage sont ceux de l'officiel, octet pour octet.

## 1. Flasher

1. Flasher web (<https://18nelli18.github.io/Modded-Cycles/>), onglet **Mods**, machine **Model:Cycles**.
2. Étape 2 : dépose le fichier d'essai à la place de l'OS officiel. La page affiche « … pas le fichier d'OS 1.13
   officiel. Il sera envoyé tel quel » : c'est voulu ; les mods cochés sont ignorés.
3. Étape 3 : comme d'habitude (méthode rapide, ou CONFIG › UPGRADE), puis flasher.

## 2. Lire le compteur

Ouvre **MACHINES** sur n'importe quelle piste, **sans tourner la molette**. À la place du nom de la machine :
**`pic/moyenne/libre`**, en % de la durée d'un bloc audio (0,67 ms), sur la dernière demi-seconde :

- **pic** : le bloc le plus long ;
- **moyenne** : la charge moyenne du son ;
- **libre** : le temps où l'interface n'avait plus rien à faire.

`--/--/--` : pas encore de mesure. 99 au plus. Si l'écran ne se rafraîchit pas, referme et rouvre MACHINES.
Les noms des machines ne s'affichent plus dans MACHINES ; l'ordre ne change pas (KICK, SNARE, METAL, PERC, TONE,
CHORD), mais tu n'en as pas besoin pour l'essai.

Ce compteur part de l'entrée de l'interruption audio (séquenceur compris) : il lit environ 1 point de plus que les
firmwares de diagnostic des notes 23 et 29, qui ne prenaient que la fonction audio (77 % de moyenne à l'arrêt).

## 3. Protocole

Prépare un projet et sauve-le : 6 pistes aux machines par défaut (KICK, SNARE, METAL, PERC, TONE, CHORD), réglages
par défaut, **un trig sur les 16 pas des 6 pistes**, 120 BPM, envois delay et reverb à 0, VOL+DIST à 60 (défaut).

Avec chaque fichier, dans cet ordre, en partant d'un **allumage** (le delay et la reverb ne doivent pas avoir servi
depuis l'allumage) :

1. **À l'arrêt** : charge le projet, ne lance pas la lecture, attends 5 s, lis MACHINES.
2. **6 pistes** : lance la lecture, attends 2 s, lis.
3. **Avec Dist** : en lecture, VOL+DIST à 100 sur les 6 pistes, lis ; puis ramène-les à 60 ou moins.
4. **Avec delay et reverb** : en lecture, envois delay 40 et reverb 40 sur les 6 pistes, lis.
5. *(facultatif)* **À l'arrêt après les effets** : stoppe, attends 10 s, lis.

Les effets en dernier : une fois servis, le delay et la reverb ne se rendorment plus avant le prochain allumage.

**À écouter** : le son doit être **le même** avec les deux fichiers, à chaque étape (attaques, fins de notes, Dist,
delay, reverb). Rien de nouveau ne doit apparaître : ni craquement, ni coupure, ni note qui manque.

**À noter**, pour chaque fichier et chaque étape : les trois nombres (relis 2 ou 3 fois, ils bougent un peu), et
toute différence de son, craquement ou blocage.

| Étape | référence pic/moy/libre | optimisé pic/moy/libre | son identique ? |
|---|---|---|---|
| 1 à l'arrêt | | | |
| 2 6 pistes | | | |
| 3 avec Dist | | | |
| 4 avec delay et reverb | | | |
| 5 à l'arrêt après les effets | | | |

Les correctifs D1 et D2 ne changent rien tant qu'on n'est pas dans le cas du gel (un projet fait sous un firmware à
plus de 6 machines ouvert dans MACHINES ; une longue surcharge pendant que l'horloge MIDI sort) : rien à tester.

## 4. Ce que prédit le modèle

Modèle de cache des notes 27-28, sur le vrai code des deux fichiers, en émulation (`sources/preuves/preuve_charge.py`).
Fourchette = caches chauds – caches vidés à chaque bloc ; « pic » = le bloc du trig.

| Étape | référence : moyenne (pic) | optimisé : moyenne (pic) | écart du modèle |
|---|---|---|---|
| 1 à l'arrêt | 78,5 – 82,0 | 16,4 – 20,6 | −62 points |
| 2 6 pistes | 79,4 – 82,0 (83 – 85) | 61,0 – 63,7 (65 – 67) | −18 |
| 3 avec Dist | 79,4 – 82,0 (83 – 85) | 65,0 – 67,7 (69 – 71) | −14 |
| 4 avec delay et reverb | 79,4 – 82,0 (83 – 85) | 72,1 – 74,7 (76 – 78) | −7 |
| 5 à l'arrêt après les effets | 79,2 – 81,8 | 27,4 – 31,6 | −52 |

**À quoi t'attendre** : la référence devrait lire à peu près ce que lisaient les firmwares de diagnostic, plus 1 point
(77 → ~78 de moyenne, 80 à 87 de pic). Le modèle a déjà surestimé un gain (note 28) : compte **70 à 100 % de l'écart**,
soit, depuis ce que tu lis sur la référence : −43 à −62 points à l'arrêt, −13 à −18 avec 6 pistes, −10 à −14 avec
Dist, −5 à −7 avec delay et reverb, −36 à −52 à l'arrêt après les effets. « libre » n'est pas modélisé ; il devrait
monter à peu près d'autant que la moyenne baisse.

## 5. Revenir au firmware normal

Flasher web : onglet **Mods** avec ton fichier officiel et tes mods habituels, ou onglet **Firmware officiel**.
Aucune piste à remettre sur une autre machine : l'essai n'en ajoute pas.

**Secours**, si la machine ne démarre plus : éteindre, **maintenir FUNC**, allumer, **TRIG 4** (OS UPGRADE), puis
envoyer le `.syx` officiel par le **MIDI IN** (interface MIDI). Le menu de démarrage n'est pas touché par ces fichiers.

## 6. Preuves (émulation, aucun résultat sur la machine)

Tout est dans `sources/` : sources, tweaks de travail (leurs écritures et les octets `old` qui vérifient le fichier
officiel, comme les tweaks du dépôt), scripts et journaux (`preuves/logs/`). `preuves/lancer.sh` rejoue tout.

- **Fichiers** [FAIT, `verifier_syx.log`] : construits par `tools/build.py` depuis l'officiel ; paquets, somme, HMAC
  valides ; sections autres que la 3 identiques à l'officiel ; section 3 = officiel + les écritures des tweaks, rien
  d'autre ; le vérificateur du flasher accepte chaque fichier et refuse une copie abîmée.
- **Son exact** [FAIT, `audio_defaut/envois/dist/glissements.log`] : 400 blocs chacun (6 pistes à 120 BPM ; envois
  40/40 ; Dist 100/80 ; réglages tournés), officiel = référence et référence = optimisé, à chaque bloc : codec, USB,
  6 voix, SRAM entière (sauf 256 o que le saturateur sauté ne réécrit pas, lus × 0), EMAC, lignes du delay et de la
  reverb ; toute la mémoire tous les 10 blocs.
- **Arrêt des voix muettes** [FAIT, `audio_arret.log`, `audio_silence.log`] : à l'arrêt, codec, USB et voix
  exactement 0 et identiques (800 blocs) ; après des notes (DECAY 20) : une voix arrêtée sort 0 là où la référence sort
  au plus −115 dB ; au retrig, écart ≤ 2·10⁻⁶ de la crête (−114 dB) ; codec et USB à −116 dBFS au plus de la référence.
- **D1 et D2** [FAIT, `gels.log`] : preuves de l'étude « stabilité » rejouées sur le fichier optimisé (contre
  l'officiel et contre la référence) : MACHINES lit CHORD au lieu d'avant le tableau ; l'horloge MIDI jette l'octet au
  lieu de figer à IPL 7.
- **Compteur** [FAIT, `compteur.log`] : entrée et sonde laissent registres et pile comme l'officiel ; fenêtres
  simulées affichées justes (`90/50/20`, `7/5/90`, pause, débordement du minuteur, borne 99) ; vrai dessin de
  MACHINES avec la vraie police : le pire cas `99/99/99` tient dans la moitié gauche (colonnes 1 à 63, sans marge) ;
  temps libre compté à 0,3 point près.
- **Pas prouvé** : tout ce qui dépend de la machine (temps réels, caches réels, rendu exact sur l'écran) ; la boucle
  du temps libre lit le minuteur sans arrêt quand l'interface n'a rien à faire (l'original tournait sur place) : effet
  sur le bus non mesuré, le même dans les deux fichiers.
