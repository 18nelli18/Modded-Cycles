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
| Compteur de charge sur la vraie machine | `[FAIT]` firmware de diagnostic `syntakt-meter`, vérifié en émulation (§5) |
| Mesures sur la machine | `[À FAIRE]` (§6) |
| Optimisations | après les mesures (§7) |

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

**Sondes**
- L'appel de la fonction audio par l'interruption (`jsr 0x4005979e` en `0x40059382`) et celui de la boucle des voix (`jsr 0x400a7d4a` en `0x4005981e`) passent par deux sondes en assembleur.
- Chacune met de côté l'adresse de retour, lit le minuteur, appelle la fonction avec la pile inchangée, puis compte le temps écoulé.
- La passerelle compte aussi le temps passé dans les moteurs du Syntakt.

**Affichage**
Toutes les 750 blocs (0,5 s), les noms des machines ajoutées 7 à 10 deviennent :
- **M** : pic de la fonction audio (voix, mixage, effets), en % de la durée d'un bloc ;
- **A** : moyenne de la fonction audio ;
- **V** : moyenne de la boucle des voix ;
- **S** : moyenne des moteurs du Syntakt.

**Preuve en émulation** (`tools/emu/test_meter.py`, minuteur simulé) :
- les 5 moteurs donnent la même sortie avec et sans compteur ;
- la sonde de la boucle des voix donne la même sortie et rend la pile intacte ;
- sur un scénario connu, les noms deviennent `M90%`, `A50%`, `V30%`, `S10%`.

Les tweaks normaux ne changent pas : le compteur n'est compilé que dans `syntakt-meter` (les 29 tweaks générés restent identiques à l'octet près).

## 6. Mesures sur la machine `[À FAIRE]`

Fichiers construits localement (dossier `build/diag/`, ignoré par git) :
- `model-cycles_OS1.13_diagnostic-charge.syx` (MAIN OS `c8cf386b…`) ;
- `…_6ch.syx` avec l'audio USB 6 canaux (MAIN OS `4aa826e4…`).

Protocole :
1. Sauvegarder les projets. Flasher le fichier de diagnostic par le flasher web, onglet *Mods*, étape 2 : un `.syx` non officiel est envoyé tel quel.
2. Machines ajoutées : 7 = SDVtg (M), 8 = CPVtg (A), 9 = SYToy (V), 10 = SYBit (S), 11 = SYSwm.
3. Pour lire une valeur : sur une piste **sans trig**, ouvrir MACHINES et tourner jusqu'à la machine 7, 8, 9 ou 10. Si le nombre ne bouge pas, repartir d'une machine et revenir.
4. Relever M, A, V et S pour, dans l'idéal, le même motif joué :
   - avec 6 machines d'origine ;
   - avec 1 moteur du Syntakt ;
   - avec 3 moteurs du Syntakt ;
   - avec 5 moteurs du Syntakt.
   Noter aussi si l'interface est lente.
5. Revenir ensuite à un firmware normal (remettre d'abord les pistes sur des machines d'origine).

## 7. Suite

Selon les mesures :
- **Si la fonction audio approche ou dépasse 100 %** : le processeur manque de temps. Il faut réduire le coût réel des moteurs du Syntakt, par exemple en les faisant travailler dans la SRAM interne, ce qui demanderait d'y libérer de la place.
- **Si la charge audio reste modérée alors que l'interface rame** : c'est la pollution du cache qui ralentit le reste de l'OS. Il faudra réduire l'empreinte mémoire des moteurs.
- Dans les deux cas, le compteur permettra de vérifier chaque optimisation sur la machine.
