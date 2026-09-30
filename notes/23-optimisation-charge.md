# 23 · Ralentissements avec plusieurs moteurs du Syntakt : mesures et compteur de charge

Travail du 30/09/2026, à la demande de l'utilisateur, après le test réussi de SYSwm seul :
« quand un engine venant du mod est joué en même temps que d'autres, on observe des ralentissements, des bugs. Pareil dès qu'il y a 3 engines custom ou plus qui jouent en même temps, la machine est ultra lente, bug et ralentit. »

Adresses : MAIN OS Cycles 1.13 et programme audio du Syntakt 1.41, comme dans les notes [17](17-portage-exact-syntakt.md) à [22](22-sy-swarm.md).

## 0. En bref

| | État |
|---|---|
| Coût en instructions des moteurs du Syntakt, en émulation | `[FAIT]` comparable aux machines d'origine (§1) |
| Interférence EMAC, mode, calcul flottant, divisions | `[FAIT]` aucune (§2) |
| Empreinte mémoire (cache) | `[FAIT]` nettement plus grande que les machines d'origine (§3) |
| Cause probable | temps d'accès mémoire (cache) sur la vraie machine, que l'émulateur ne chronomètre pas (§4) |
| Compteur de charge sur la vraie machine | `[FAIT]` firmware de diagnostic `syntakt-meter` : « pic/moyenne » à la place du nom de toutes les machines, vérifié en émulation (§5) |
| Mesures sur la machine | `[FAIT]` le Cycles d'origine prend déjà 77 % du temps pour l'audio, même à l'arrêt (§6) |
| Arrêt des voix muettes | `[FAIT]` en émulation : −77 % d'instructions quand les 6 voix se taisent (§7) |
| Test sur la machine de l'arrêt des voix muettes | `[À FAIRE]` (§8) |

## 1. Coût en instructions (émulation)

Instructions par bloc de 32 échantillons, pour toute la boucle des 6 voix (`0x400a7d4a`), piste 1 déclenchée, les 5 autres sur KICK au repos.
- Source : compteur d'instructions de `tools/emu/mcengine.py`, tweak `syntakt-sd-cp-toy-bits-swarm`.

| Piste 1 | Bloc du 1ᵉʳ déclenchement | Pendant le son | Écart avec une voix KICK au repos |
|---|---|---|---|
| 6 KICK au repos | — | 45 842 | 0 |
| SNARE | 46 214 | 45 738 | −100 |
| CHORD | 47 341 | 46 904 | +1 060 |
| SDVtg | 55 121 | 46 746 | +900 |
| CPVtg | 55 432 | 47 123 | +1 280 |
| SYToy | 53 640 | 45 335 | −510 |
| SYBit | 54 203 | 45 947 | +100 |
| SYSwm | 57 619 | 49 116 | +3 270 |

- Une voix d'origine coûte environ 7 600 instructions par bloc, qu'elle joue ou non : les 6 voix tournent à chaque bloc.
- Une voix du Syntakt coûte de −7 % (SYToy) à +43 % (SYSwm) d'une voix d'origine.
- Le surcoût d'environ 9 000 instructions au 1ᵉʳ déclenchement n'a lieu qu'**une fois** (initialisation des 8 voix du Syntakt). Un redéclenchement coûte 150 à 300 instructions.
- Les queues de son durent plus d'une seconde (SY BITS à DEC 60 : −30 dB après 1 s). Sauter les voix muettes ne ferait gagner que sur des motifs clairsemés.

## 2. Pas d'interférence de calcul

- Aucune instruction du code copié ne touche MACSR, le registre d'état ni les registres de contrôle. Il ne fait que charger les accumulateurs.
  - Source : fermeture de `gen_syntakt_engines.py`, 3 971 instructions.
- Pas de division ni de calcul flottant dans les boucles : les deux « instructions FPU » repérées sont `ff1` (recherche de bit, entière).
- Les machines d'origine commencent par accumuler dans `acc0` sans le remettre à zéro (`macl …,%acc0`). Elles comptent donc sur des accumulateurs vides en entrée.
  - En émulation, une SNARE, une TONE ou une CHORD jouée après chacun des 5 moteurs du Syntakt sort **exactement** le même son qu'après KICK.
  - L'émulateur ne modèle pas les drapeaux de dépassement (PAV) du vrai processeur.
- L'interruption audio (`0x40058c5e`) sauvegarde et restaure MACSR.
- La mémoire `0x40000000..0x47ffffff` est en cache « copyback » (ACR0 = `0x4007e020`), charge utile comprise. Le MMU n'est pas activé (aucun `movec` vers MMUBAR).

## 3. Empreinte mémoire par bloc (émulation)

Lignes de 16 o distinctes touchées pendant un bloc (le cache travaille par lignes).
- Source : `UC_HOOK_CODE` et `UC_HOOK_MEM_*` sur un bloc.

| Cas | Code | Données en SDRAM | Données en SRAM interne |
|---|---|---|---|
| 6 machines d'origine | 602 | 189 | 267 |
| 1 SYSwm (+ 5 KICK) | 402 | 418 | 151 |
| 3 moteurs du Syntakt (SD, CP, SWARM) | 772 | 462 | 151 |
| 5 moteurs du Syntakt | 945 | 462 | 151 |

- Les machines d'origine lisent leurs tables surtout dans la **SRAM interne** : un cycle par accès, sans passer par le cache.
- Une voix du Syntakt touche, en SDRAM (donc via le cache), 34 à 57 lignes de son état de voix, et 60 à 157 lignes de tampons et de tables partagés. Sur le Syntakt, tout cela est dans la SRAM de son processeur audio.
- La SRAM interne du Cycles (64 Ko) est entièrement prise par l'OS : deux banques de 32 Ko, remplies au démarrage (`0x4000045c`).

## 4. Hypothèse

- En instructions, les moteurs du Syntakt ne coûtent guère plus que les machines d'origine ; l'émulation ne reproduit donc pas l'effondrement observé.
- Sur la vraie machine, chaque bloc (1 500 par seconde) fait passer les données et le code des moteurs du Syntakt par les caches.
  - Chaque défaut de cache coûte des dizaines de cycles de SDRAM.
  - Les données et le code du reste de l'OS (interface, séquenceur) sont chassés du cache, et tout le reste ralentit aussi.
- L'effet grandit avec le nombre de moteurs différents, ce qui colle avec « 3 moteurs ou plus, ultra lent ».
- L'émulateur ne chronomètre pas ces attentes : il faut **mesurer sur la machine**.

## 5. Compteur de charge (firmware de diagnostic)

Tweak `syntakt-meter` : les 5 moteurs, plus un compteur de charge (`gen_syntakt_engines.py --engines sd,cp,toy,bits,swarm --meter`).

**Horloge**
- Le minuteur DMA 0 (`0xfc07000c`) compte à 135,168 MHz. L'OS divise ses ticks par 135 168 pour obtenir des millisecondes (`0x400532e0`).
- Un bloc de 32 échantillons à 48 kHz dure donc 90 112 ticks.

**Sonde**
- L'appel de la fonction audio par l'interruption (`jsr 0x4005979e` en `0x40059382`) passe par une sonde en assembleur.
- La fonction audio couvre les voix, le mixage et les effets. L'interruption `0x40058c5e` sauvegarde et restaure MACSR.
- La sonde met de côté l'adresse de retour, lit le minuteur, appelle la fonction avec la pile inchangée, puis compte la durée du bloc et l'écart avec le précédent.

**Affichage**
- Toutes les 750 blocs (0,5 s), le texte « pic/moyenne » de la charge audio, en % de la durée d'un bloc (99 au plus), est écrit dans un petit tampon.
- **Toutes** les machines de l'écran MACHINES, d'origine et ajoutées, portent ce tampon comme nom (« --/-- » avant la 1ʳᵉ mesure).
- Première version (retirée avant tout essai) : des valeurs M, A, V, S à la place des noms des machines 7 à 10. Il fallait changer la machine d'une piste pour les lire, impossible quand les 6 pistes jouent (remarque de l'utilisateur).

**Preuve en émulation** (`tools/emu/test_meter.py`, minuteur simulé) :
- les 5 moteurs donnent la même sortie avec et sans compteur ;
- avec une fonction audio factice, la sonde lui présente les mêmes arguments et la même pile, rend `d0`, et compte le bloc ;
- sur un scénario connu (blocs à 50 %, un bloc à 90 %), le nom devient `90/50` ;
- l'écran MACHINES affiche ce nom pour les machines 1, 6, 7 et 11.

Les tweaks normaux ne changent pas : le compteur n'est compilé que dans `syntakt-meter` (les 29 tweaks générés restent identiques à l'octet près).

## 6. Mesures sur la machine `[À FAIRE]`

Fichiers construits localement (dossier `build/diag/`, ignoré par git) :
- `model-cycles_OS1.13_diagnostic-charge.syx` (MAIN OS `b139162e…`) ;
- `…_6ch.syx` avec l'audio USB 6 canaux (MAIN OS `3bd5de11…`).

Protocole :
1. Sauvegarder les projets. Flasher le fichier de diagnostic par le flasher web, onglet *Mods*, étape 2.
   - Un `.syx` non officiel est envoyé tel quel : pas de case à cocher, pas de fichier Syntakt.
2. Machines ajoutées : 7 = SDVtg, 8 = CPVtg, 9 = SYToy, 10 = SYBit, 11 = SYSwm.
3. Pour lire : pendant que le motif joue, ouvrir MACHINES sur n'importe quelle piste, **sans tourner la molette**, lire « pic/moyenne », refermer. Rouvrir pour une nouvelle lecture si l'écran ne se rafraîchit pas.
4. Relever « pic/moyenne » pour, dans l'idéal, le même motif :
   - avec 6 machines d'origine ;
   - avec 1 moteur du Syntakt ;
   - avec 3 moteurs du Syntakt ;
   - avec 5 moteurs du Syntakt.
   Noter aussi si l'interface est lente.
5. Revenir ensuite à un firmware normal (remettre d'abord les pistes sur des machines d'origine).

## 6 bis. Résultats (30/09/2026)

Mesures de l'utilisateur avec le firmware de diagnostic (« pic/moyenne » de la fonction audio, en % d'un bloc) :

| Cas | Pic | Moyenne |
|---|---|---|
| 6 machines d'origine, lecture à l'arrêt | 80 | 77 |
| 6 machines d'origine, en lecture | 87 | 77 |
| 5 d'origine + SDVtg | 94 | 84 |
| 4 d'origine + SDVtg + CPVtg | 92 | 89, son dégradé, interface ralentie |

Avec la 1ʳᵉ version du compteur (5 pistes d'origine, 1 sacrifiée) : M 92 %, A 83 %, V 47 %, S 11 %.

Ce qu'on en tire :
- **Le Cycles d'origine est déjà presque plein.** L'audio prend 77 % du temps, **même à l'arrêt** : les 6 voix sont calculées à chaque bloc, qu'elles jouent ou non. L'interface ne dispose que d'environ 20 % du processeur.
- **La boucle des voix pèse environ 47 %**, soit environ 8 % par voix d'origine. Le reste (≈ 30 %) est le mixage et les effets.
- **Une voix du Syntakt coûte environ deux fois une voix d'origine** en temps réel : +7 points de moyenne pour SDVtg, +12 pour SDVtg + CPVtg. En instructions, l'écart n'était que de +12 % et +16 % (§1) : la différence vient bien de la mémoire (§4).
- Au-delà d'environ 85 % de moyenne, l'interface étouffe ; quand un bloc dépasse 100 %, le son casse.

## 7. Arrêt des voix muettes `[FAIT]` en émulation

Le levier le plus fort n'est pas de rendre les moteurs du Syntakt moins chers, mais de ne plus calculer les voix qui ne jouent pas, **pour les 6 machines d'origine comme pour les machines ajoutées**.

**Principe** : dans la boucle des voix, l'appel update/render de chaque piste (`0x400a7dfe..0x400a7e24`) passe par un détour (`dispatch_asm()` de `gen_syntakt_engines.py`).
- Après chaque render, on mesure la crête des 32 échantillons de la voix.
- Une voix restée sous `IDLE_THR` = 2¹³ (−108 dB sous la pleine échelle) pendant `IDLE_BLOCKS` = 64 blocs (43 ms), et sans trig, n'est plus calculée : sa sortie est mise à zéro.
- Au trig suivant (voix + 0x34 ou + 0x38), elle repart normalement. Les appels update/render sont faits exactement comme par l'OS (mêmes registres, même pile).
- Tous les tweaks générés en profitent. SD seul et SD + CP passent maintenant eux aussi par le générateur (`syntakt-sd`, `syntakt-sd-cp`) ; les anciens `sdvintage-7th` et `syntakt-vintage` restent disponibles avec `build.py`.

**Preuve en émulation** (`tools/emu/test_idle.py`, référence : le Cycles d'origine) :
- Les 6 machines d'origine, DECAY 20 : son **identique** échantillon par échantillon tant que la voix est calculée.
  - Elles s'arrêtent entre les blocs 146 (SNARE) et 547 (PERC). Ensuite, le Cycles d'origine ne produit plus que des valeurs sous le seuil.
  - Au trig suivant, l'écart est d'au plus 1,7·10⁻⁶ de la crête (−115 dB).
- **Coût, 6 voix d'origine muettes : 42 278 → 9 571 instructions par bloc (−77 %).** Quand les 6 jouent : 42 302 → 42 415 (+0,3 % pour la mesure de crête).
- **SYToy, DECAY 10 : identique jusqu'à l'arrêt (bloc 200) ; coût −95 % ensuite.**
  - Au trig suivant, le son diffère de 11 % de la crête : un moteur du Syntakt ne remet pas ses oscillateurs à zéro au trig, et la phase n'est plus la même. C'est la même variation qu'entre deux notes jouées à des moments différents.
  - Le test vérifie que la note rejouée a le même niveau (à 1 dB près) que la référence et que la 1ʳᵉ note.
- Les tests complets (`test_syntakt_machines.py`) passent sur SD, SD + CP, CP, SY TOY, SY BITS, SY SWARM, SD + CP + SY TOY et les 5 moteurs.

**Limites**
- Une voix qui joue coûte toujours autant ; une voix du Syntakt coûte toujours environ deux fois une voix d'origine.
- Les moteurs du Syntakt ont des queues longues avec leurs réglages par défaut (plus d'une seconde pour SY BITS et SY SWARM) : ils ne s'arrêtent qu'une fois vraiment silencieux.
- Le gain dépend donc du motif : maximal à l'arrêt et avec des sons courts ; nul si les 6 voix sonnent en permanence.

## 8. Test sur la machine `[À FAIRE]`

Firmware de diagnostic v2 (compteur + arrêt des voix muettes + 5 moteurs), construit localement :
- `build/diag/model-cycles_OS1.13_diagnostic-charge_v2.syx` (MAIN OS `4bfe715c…`) ;
- `…_v2_6ch.syx` (MAIN OS `80260796…`).

À relever comme au §6 bis, pour comparer :
- à l'arrêt ;
- 6 machines d'origine en lecture ;
- avec 1, 2, 3 et 5 moteurs du Syntakt.

Écouter aussi : pas de son coupé trop tôt, pas de différence sur les notes rejouées.

## 9. Suite

Selon les mesures :
- Réduire le coût réel d'une voix du Syntakt qui joue (≈ 2 voix d'origine) : ses tampons de travail sont en SDRAM, là où les machines d'origine utilisent la SRAM interne. Piste : emprunter pendant son calcul des tampons de SRAM qui ne servent qu'au calcul d'une voix d'origine. À étudier.
- Proposer l'arrêt des voix muettes aussi sans moteur du Syntakt : il allège le Cycles d'origine (77 % à l'arrêt).
