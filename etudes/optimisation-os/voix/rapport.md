# Boucle des voix et machines d'origine : où part le temps, ce qui est refait pour rien, ce qu'on peut gagner

Agent « voix », 17/10/2026. OS 1.13 d'origine (`sec3.bin`, VA = offset + 0x40000400). Périmètre : la fonction audio
`0x4005979e` sans le mixeur ni les effets (lissage des paramètres, LFO, boucle des voix `0x400a7d4a`, gain de
vélocité), et les 6 machines KICK, SNARE, METAL, PERC, TONE, CHORD.

Étiquettes : **[FAIT]** vérifié (code désassemblé, émulation, commande et sortie), **[DÉDUIT]** calculé à partir de
faits, **[HYP]** plausible, non vérifié. Rien ici n'a été mesuré sur la machine : tous les « % d'un bloc » viennent
du modèle des notes 27-28 (166 667 cycles par bloc, 1,54 cycle par instruction, 15 cycles par ligne de 16 o lue ou
écrite en SDRAM), donc **1 % d'un bloc ≈ 1 082 instructions**.

Tous les fichiers cités sans chemin sont dans
`/tmp/claude-0/-home-user-Modded-Cycles/4cafd55d-d242-5df3-ad6a-3e64ee54ea56/scratchpad/optim/voix/` (scripts,
sorties, prototypes sous `proto/`). Aucun fichier du dépôt n'a été modifié.

---

## 0. En bref

1. **L'OS calcule les 6 voix à chaque bloc, qu'elles jouent ou non, et le cas le plus cher est l'arrêt complet.**
   Une voix jamais déclenchée depuis le démarrage calcule un KICK (machine 0) de silence : à l'arrêt, la fonction
   audio exécute **49 709 instructions par bloc** (6 KICK), contre 46 020 quand les 6 machines jouent et 45 986
   quand leurs notes sont retombées [FAIT, émulation `seqprof.py`, §2.1]. Modèle : ~52 % d'un bloc dans les trois cas,
   cache froid compris. Le render fait 92 à 96 % d'une voix ; l'opérateur `0x400a8204` à lui seul 26 à 37 % de la
   boucle ; le code d'un bloc (686 lignes de 16 o) déborde le cache d'instructions (512 lignes) ; les tables en SDRAM
   ne pèsent presque rien (≤ 0,8 %), les états des voix (248 lignes) un peu plus (0 à 4 %).
2. **Prototype prouvé : l'arrêt des voix muettes pour l'OS d'origine seul** (204 o dans un masque libre, deux
   détours de 6 o, sans C, sans régulateur, sans moteurs du Syntakt ni Model-TG). Son identique échantillon par
   échantillon tant qu'une voix est calculée ; la voix arrêtée sort des zéros là où l'OS sort des valeurs sous
   −108 dB ; au retrig, écart ≤ 2,5·10⁻⁶ de la crête (−112 dB). À l'arrêt, la boucle des voix passe de **45 989 à
   560 instructions** ; 1,6 s après des notes aux réglages par défaut, la fonction audio passe de 45 986 à 17 614
   (avec 4.2 et 4.3) [FAIT, émulation].
3. **Deux prototypes prouvés à l'octet près (sorties ET états des 6 voix identiques)** : la boucle morte de `mix2`
   (−598 instructions par voix KICK/SNARE/METAL/PERC : −2,2 à −3,3 % d'un bloc) et un chemin court de PUNCH éteint
   (−218 par voix : −1,0 à −1,2 %). **Les trois ensemble** : modèle 52,1 → **5,4 %** d'un bloc à l'arrêt, 52,0 →
   21,4 % 1,6 s après des notes, 52,1 → 48,4 % quand les 6 jouent (sortie identique à l'octet près dans ce dernier
   cas) [DÉDUIT du modèle ; rien mesuré sur la machine].
4. Autres pistes chiffrées, non prototypées : lissage des paramètres sauté à son point fixe (prouvé exact,
   ≤ 1,5 %), opérateur `0x400a8204` réécrit (−0,8 %), états des voix en SRAM (0 à 4 %), piste mutée non calculée
   (une voix entière par piste mutée, son non identique au démute), moitié du cache d'instructions verrouillée
   (≤ 4,6 %, à voir avec l'agent « système »).
5. Piège d'outillage trouvé : avec unicorn 2.1.4, un crochet de lecture posé en cours de route ne voit pas les
   lectures du code déjà traduit (§1).

---

## 1. Méthode

- **Émulation** : `tools/emu/mcengine.py` (boucle des voix seule) et `tools/emu/seqrig.py` (vrai corps de
  l'interruption, séquenceur compris, mixeur/effets/codec sautés). EMAC émulé par `tools/emu/emac.py`.
- **Profileur** `prof.py` (non versionné) : crochet `UC_HOOK_CODE` avec pile d'appels fantôme (l'adresse de retour
  est lue sur la pile à l'entrée de l'appelé, la taille d'instruction donnée par unicorn n'étant pas fiable), compte
  par adresse / exclusif / inclusif ; crochets mémoire par région et par ligne de 16 o, plus les chargements des MAC
  avec chargement (faits en Python par `emac.py`, donc invisibles des crochets : `emac._ea` est enveloppé).
  - **Piège trouvé et corrigé** [FAIT, `t_rd3.py`] : avec unicorn 2.1.4, un crochet de **lecture** ajouté après la
    traduction d'un bloc de code ne voit pas les lectures de ce bloc tant que le cache de traduction n'est pas vidé
    (lectures d'un bloc de voix : 90 sans vidage, 10 538 après `uc.ctl_flush_tb()`). Les écritures, elles, sont
    vues. `prof.py` vide maintenant le cache à l'activation ; les chiffres de lignes de données de ce rapport viennent
    du relevé corrigé. **À retenir pour les autres bancs du dépôt qui comptent des lectures avec un crochet posé en
    cours de route** [HYP : je n'ai pas vérifié lesquels le font].
- **Cache** `cachesim.py` : 8 Ko I + 8 Ko D, 4 voies, lignes de 16 o, LRU, D en copyback avec allocation en
  écriture ; la SRAM n'est pas cachée (1 cycle) ; « froid » = caches vides au début du bloc (l'interface, le mixeur
  et les effets ont tout chassé), « chaud » = le même bloc rejoué derrière lui-même (borne basse).
- **Réglages** : machines aux réglages par défaut de `mcengine.DEFAULTS`, PUNCH 0, GATE 0, note 60, vélocité 100.
- Le modèle colle à la machine : il donne 48 à 52 % pour la fonction audio sans mixeur quand les 6 voix jouent ; la
  machine mesure ~47 % pour la boucle des voix (notes/23 §6 bis) et ~52 % avec Model-TG (notes/31 §7) [DÉDUIT].

---

## 2. Profil

### 2.1 La fonction audio `0x4005979e` (mixeur et effets sautés) [FAIT, `seqprof.py` → `seqprof.out`]

6 pistes KICK, SNARE, METAL, PERC, TONE, CHORD, réglages par défaut, séquenceur réel (`seqrig`).
« joue » : bloc 10 après un trig des 6 ; « muette » : bloc 2 400 (1,6 s) après ce trig ; « arrêt » : jamais de trig.

| | joue | muette | arrêt |
|---|---:|---:|---:|
| `0x4005979e` entière (instructions) | 46 020 | 45 986 | 49 709 |
| dont boucle des voix `0x400a7d4a` | 42 300 | 42 266 | 45 989 |
| dont avant la boucle : lissage `0x40058474` | 1 834 | 1 834 | 1 834 |
| LFO `0x40091ab2` (inclusif) | 1 025 | 1 025 | 1 025 |
| modulation de vélocité `0x40056e24` | 182 | 182 | 182 |
| après la boucle : gain de vélocité `0x40056d9c` | 598 | 598 | 598 |
| crête des 6 sorties (pleine échelle 2³¹) | 0,9 à 2,3·10⁸ | 1 à 8·10⁵ | 0 |
| lignes de code distinctes (16 o) | 686 | 683 | 308 |
| modèle, cache froid / chaud | 52,1 % / 47,9 % | 52,0 % / 47,9 % | 52,1 % / 46,7 % |

- **Avant la boucle : ~3 040 instructions (2,8 %)**, ce que la machine mesure aussi (« fonction audio avant les voix
  3 % », notes/31 §7) [DÉDUIT].
- **Une voix muette coûte exactement autant qu'une voix qui joue** (42 266 contre 42 300) ; une voix jamais
  déclenchée coûte un KICK (machine 0, la plus chère après CHORD) [FAIT].
- La division par 2 de chaque piste (`0x400a7e2a..0x400a7e36`, 7 instructions par échantillon) fait 1 344 des 1 658
  instructions propres de la boucle (1,2 % d'un bloc) [FAIT, notes/36 §2].

### 2.2 Par machine : update contre render [FAIT, `machines2.py` → `machines2.out`, piste 0 seule calculée]

| machine | update | render | voix entière¹ | % d'un bloc | lignes de code | lignes de SDRAM cachée² |
|---|---:|---:|---:|---:|---:|---:|
| KICK | 416 | 7 001 | 7 693 | 7,1 % | 216 | 84 |
| SNARE | 502 | 6 643 | 7 421 | 6,9 % | 212 | 86 |
| METAL | 525 | 5 894 | 6 695 | 6,2 % | 187 | 77 |
| PERC | 511 | 5 556 | 6 343 | 5,9 % | 163 | 98 |
| TONE | 317 | 4 962 | 5 555 | 5,1 % | 165 | 64 |
| CHORD | 367 | 7 921 | 8 564 | 7,9 % | 208 | 81 |

¹ update + render + division par 2 (224) + tour de boucle (~52).
² lues ou écrites par bloc, relevé corrigé (états de la voix, tables, paramètres).

- **render fait 92 à 96 % d'une voix ; update 4 à 8 %** [FAIT]. Le gros du travail est par échantillon.
- Coût par machine identique entre « joue » et « muette » (KICK 9 039 / 9 007, SNARE 8 767 / 8 768, CHORD 9 910 /
  9 910 au total de la boucle) [FAIT, `machines2.out`].

### 2.3 Les boucles par échantillon [FAIT, `loops.py` sur `seq_joue.pkl`, 6 voix qui jouent]

Instructions des adresses exécutées au moins 31 fois par appel, divisées par 32 :

| fonction | qui l'appelle | appels / bloc | instr. / échantillon | hors boucle / appel | total / bloc |
|---|---|---:|---:|---:|---:|
| opérateur `0x400a8204` | KICK ×3, SNARE ×3, METAL ×3, PERC ×4 | 13 | 27 | 74 | 12 194 |
| opérateur `0x400a8722` | CHORD ×4 | 4 | 41 | 134 | 5 784 |
| `mix2` `0x400a9884` | KICK, SNARE, METAL, PERC | 4 | 27 (2 boucles) | 33 | 3 588 |
| PUNCH `0x400a967a` | toutes sauf TONE | 5 | 13 | ~60 | 2 328 |
| opérateur `0x400a8adc` | KICK, SNARE, METAL | 3 | 24 | 77 | 2 535 |
| opérateur `0x400a835e` | TONE | 1 | 56 | 81 | 1 873 |
| opérateur `0x400a8fc2` | TONE | 1 | 50 | 78 | 1 678 |
| VCA `0x400a9430` | toutes | 6 | 7 | 20 | 1 464 |
| filtre `0x400a9d4e` | KICK ×2, SNARE, CHORD ×2 | 5 | 7 | ~20 | 1 220 |
| filtre `0x400a9cf6` | SNARE | 1 | 21 | 8 | 680 |
| `0x400a9daa` (filtre du KICK, finit dans `0x400a9d4e`) | KICK | 1 | 16 | 19 | 531 |
| `0x400a9ebe` | METAL | 1 | 13 | 32 | 448 |
| `0x400a9a32` | CHORD | 1 | 10 | 44 | 364 |
| `0x400a956c` | KICK | 1 | 8 | 6 | 262 |
| division par 2 (boucle) | toutes | 6 | 7 | 3 | 1 344 |
| gain de vélocité `0x40056d9c` | 6 pistes | 1 | 2,75 par piste | | 598 |
| interpolation `0x400a9ca8` | update | 34 | — | 30 | 1 022 |
| lissage `0x40058474` | 238 paramètres | 1 | 7 par paramètre | | 1 834 |

- **`0x400a8204` est le cœur du coût : 26 % de la boucle des voix quand les 6 jouent, 37 % à l'arrêt (18 appels
  pour 6 KICK, 16 884 instructions)** [FAIT, `seqprof.out`]. Sa boucle (`0x400a82d6..0x400a832c`, 27 instructions)
  relit 4 incréments sur la pile à chaque échantillon (`addl %sp@(104),%d4`, `addal %sp@(108),%fp`,
  `addl %sp@(84),%d7`, `addl %sp@(88),%d1`), refait 3 masques `andil #0xffffff` / `#0xffff` et un `moveq #16,%d3`
  constant, alors que `%a4` n'y sert pas [FAIT, désassemblage].

### 2.4 Mémoire et cache [FAIT, `seqprof.py` corrigé, `cachesim.py`, `sdramro.py`]

| | joue | muette | arrêt |
|---|---:|---:|---:|
| lignes de code distinctes | 686 | 683 | 308 |
| SDRAM cachée : lignes touchées (dont écrites) | 347 (205) | 341 (204) | 351 (251) |
| dont états des voix `0x42308828..` | 248 | 248 | 278 |
| SRAM : lignes touchées (dont écrites) | 555 (271) | 550 (271) | 304 (226) |
| SDRAM non cachée (`0x48..0x4f`) | 0 | 0 | 0 |
| défauts cache froid : I / D / réécritures | 686 / 369 / 10 | 683 / 363 / 13 | 308 / 373 / 5 |
| défauts cache chaud : I / D / réécritures | 507 / 61 / 26 | 501 / 69 / 31 | 28 / 38 / 23 |
| coût du cache, froid / chaud | 9,6 % / 5,3 % | 9,5 % / 5,4 % | 6,2 % / 0,8 % |

- Accès d'un bloc « joue » hors SRAM : 1 869 lectures et 867 écritures en SDRAM cachée, 5 294 lectures et 1 540
  écritures de pile (la pile de l'émulation est à `0x90000000` ; celle de l'interruption sur la machine n'a pas été
  localisée ici [HYP : SDRAM cachée]).
- **Le cache d'instructions coûte plus que le cache de données** : même au bloc chaud, 507 défauts d'instructions
  (4,6 %) contre 61 de données (§3.11).
- La SRAM (1 cycle, non cachée) porte les tampons de 32 échantillons, le brouillon des voix et les tables d'onde
  de la plupart des opérateurs (pas celle de `0x400a8204`, en SDRAM, §3.8 ; §3.9) : les passes répétées sur les
  tampons y coûtent des instructions, pas des défauts.

### 2.5 Ce qui change entre « voix qui joue », « voix muette », « séquenceur à l'arrêt »

- **Rien dans le calcul** : mêmes fonctions, mêmes nombres d'instructions à ±0,1 % [FAIT, §2.1]. La seule
  différence est la machine des voix jamais déclenchées : la voix part en machine 0 (KICK) et n'en change qu'au bloc
  qui suit son premier trig (`0x400a7dac..0x400a7dde` : la machine n'est relue que si `voix + 0x38`, le trig du bloc
  précédent, est posé) [FAIT].
- **L'enveloppe d'amplitude d'origine ne revient jamais à zéro** (déclin exponentiel, `0x400a92e4 msacl`) : une note
  retombée reste à un niveau infime sans jamais sortir exactement 0 (crêtes de 1 à 8·10⁵ sur 2³¹ au bloc 2 400, §2.1 ;
  une SNARE reste à 1-3 LSB des milliers de blocs, `kicktail.out`) [FAIT].
  Une voix d'origine n'est donc jamais « exactement muette » après une note : un arrêt des voix muettes ne peut pas
  être identique à l'octet près après l'arrêt (§4.1), seulement avant.
- **Une piste mutée est calculée en entier** : le mute d'origine (FUNC + piste) et le volume 0 agissent sur les gains
  du mixeur, pas sur la voix (notes/35 §3, `0x40a78c08..`) [FAIT d'après la note ; non revérifié ici].

---

## 3. Le travail inutile ou refait

### 3.1 Les voix muettes, et celles qui n'ont jamais joué, sont calculées en entier [FAIT]

- Boucle `0x400a7d4a` : pour chaque piste, `jsr %a1@` en `0x400a7e0e` (update, table `0x40118628`) puis en
  `0x400a7e1e` (render, table `0x40118610`), sans aucun test de niveau ni de trig ; seule une machine > 5 est sautée
  (`0x400a7dfe cmpl %d4,%d0 ; 0x400a7e00 bcss 0x400a7e24`).
- Coût d'une voix muette = coût d'une voix qui joue (§2.1, §2.2) : **5,1 à 7,9 % d'un bloc par piste** selon la
  machine, **~42 % pour les 6** (modèle, sans le cache), et **~46 % à l'arrêt total** (6 KICK de silence).
- Pistes concernées dans la vraie vie : toutes à l'arrêt ; une piste sans trig dans le motif ; une piste dont la
  note est retombée (sous −108 dB après 0,05 à 0,5 s à DECAY 20 ; 1 à plus de 2 s pour KICK, TONE et CHORD à leur
  DECAY par défaut, `kicktail.out`, §4.1) ;
  une piste mutée qui ne reçoit plus de trig [HYP : je n'ai pas vérifié si le mute empêche le trig ou seulement le
  son ; d'après notes/35 §3 il agit au mixeur, donc une note mutée continue de sonner avant le mixeur].

### 3.2 La division par 2 de chaque piste : une passe à part [FAIT]

- `0x400a7e2a..0x400a7e36` : `movel %a1@,%d1 ; asrl #1,%d1 ; addql #1,%d0 ; movel %d1,%a1@+ ; moveq #32,%d1 ;
  cmpl %d0,%d1 ; bnes` : 7 instructions par échantillon, **1 344 par bloc (1,24 %)**, une relecture et une réécriture
  complètes des 6 × 32 échantillons.
- Le dépôt a déjà une version plus courte, mêmes valeurs (`tools/voice_loop.py`, 5 instructions, −384) écrite par
  6ch-usbup, Model-TG, ACID, MACRO et les moteurs du Syntakt.
- Le prototype d'arrêt des voix muettes la refait **en même temps que le test de silence** (4 échantillons par
  `movem`, §4.1) : la mesure de crête ne coûte plus une passe de plus, elle remplace celle-ci.
- La replier dans le gain de vélocité `0x40056d9c` (gain / 2 au lieu de x / 2) ne serait **pas** exact :
  `floor(x/2)·g` et `x·(g/2)` diffèrent au dernier bit [DÉDUIT de `0x40056dca msacl %d4,%a1,...`].

### 3.3 `mix2` (`0x400a9884`) calcule son mélange deux fois [FAIT, prouvé à l'octet près]

- 1ʳᵉ boucle `0x400a98c4..0x400a9902` : mélange de deux sources dans la sortie (`0x400a98e8 movel %d1,%a5@(0,%d0:l)`)
  avec deux gains qui avancent d'un pas par échantillon (`0x400a98f0 addl %d3,%a0@(18,%d1:l:4)`, `0x400a98f8`).
- 2ᵉ boucle `0x400a991c..0x400a992e` : refait le mélange avec MAC à chargement et **réécrit la même sortie depuis
  le début** (`0x400a992a movel %d2,%a5@+`, `%a5` n'ayant pas bougé).
- De la 1ʳᵉ boucle ne reste que l'avance des gains de 32 pas : **598 instructions par appel jetées**, un appel par
  voix KICK, SNARE, METAL, PERC.
- Model-TG l'a vu aussi (il écrit 8 o en `0x400a98c4`, `tweaks/model-cycles_OS1.13/30-model-tg.json`).

### 3.4 PUNCH éteint : 13 instructions par échantillon pour une multiplication par une constante [FAIT, prouvé]

- `0x400a967a` est appelée par toutes les machines sauf TONE, PUNCH allumé ou non.
- PUNCH éteint (`voix + 0x48` nul) : `0x400a96f6..0x400a9700` pose le niveau à `0x7fffffff`, donc le pas
  d'enveloppe `%d5 = (a1 − a2) >> 5` est nul, et le gain « ×4 saturé » `%d6 = voix + 0x2a0` vaut `0x20000000`.
- La boucle `0x400a971c..0x400a9742` refait pourtant à chaque échantillon le produit constant `%a2 × %d7`, quatre MAC
  `×0,25` et deux transferts d'accumulateur : `y = c·x`, avec `c` constant sur le bloc.

### 3.5 Le lissage des paramètres refait le même calcul quand rien ne bouge [FAIT, `smooth_fp.py`]

- `0x40058474` lisse 238 paramètres à chaque bloc (2 par tour, 14 instructions, `0x400584aa..0x400584d0`) : état
  `0x800011e8`, cibles `0x800015a0`, valeurs `0x8000100c`, puis recopie 6 valeurs en `0x80001022 + 66 t`.
- **Point fixe exact** : cibles au hasard (y compris extrêmes), MACSR = 0x20 comme dans la fonction audio ; l'état
  ne change plus d'un bloc à l'autre à partir du bloc 610, et les 238 sorties valent alors exactement les cibles
  (`état stationnaire au bloc 610 ; sorties différentes de la cible : 0 []`).
- Donc, tant qu'aucune cible ne bouge depuis que l'état est stationnaire, **1 834 instructions par bloc (1,7 %) sont
  refaites à l'identique**.

### 3.6 Les update recalculent des coefficients dont les réglages n'ont pas bougé [FAIT pour le coût, HYP pour la part évitable]

- 34 appels à l'interpolation de tables `0x400a9ca8` par bloc quand les 6 jouent (1 022 instructions, 0,9 %) :
  table de 128 `int32`, index = réglage >> 8, interpolation linéaire par MAC (`0x400a9ce6`, `0x400a9cea`).
  Tables lues : `0x4011aa4c`, `0x4011ac4c`, `0x4011ae4c`, `0x4011b04c`, `0x4011b44c`, `0x4011b64c`… (KICK.update
  `0x400aa0a8..0x400aa234`), jusqu'à `0x40123c8c`.
- Les update entiers pèsent 2 638 instructions pour 6 voix (2,4 %, §2.2). Une partie dépend de modulations qui
  bougent à chaque bloc (LFO, enveloppes de hauteur) ; le reste ne change qu'au geste sur un bouton [HYP : pas fait
  la séparation fonction par fonction].

### 3.7 Plusieurs passes sur le même tampon de 32 échantillons [FAIT pour les passes, HYP pour le gain]

Pour une voix KICK : opérateurs (×3) → `0x400a8adc` → `mix2` (2 boucles) → `0x400a9daa` → filtre `0x400a9d4e` →
VCA `0x400a9504` et `0x400a9430` → PUNCH → `0x400a956c` → division par 2 → gain de vélocité → mixeur. Chaque passe
relit et réécrit 32 `int32` en SRAM (1 cycle, pas de défaut de cache) : le coût est en instructions de chargement,
de rangement et de boucle, ~3 à 4 par échantillon et par passe. Fusionner VCA + PUNCH + division ferait gagner de
l'ordre de 2 passes × 3,5 × 32 × 6 ≈ 1 300 instructions (1,2 %) [HYP], au prix d'une réécriture du chemin de sortie de
chaque machine.

### 3.8 Ce qui est lu en SDRAM [FAIT, relevé corrigé, `sdramro.py joue`]

Quand les 6 jouent, la fonction audio touche **347 lignes de SDRAM cachée** (205 écrites, 142 seulement lues), et
aucune ligne non cachée (`0x48000000..0x4fffffff`) :

| quoi | lignes | qui |
|---|---:|---|
| états des voix `0x42308828..0x42309ad0` | 248 | update, render, boucle |
| tables d'interpolation `0x4011aa4c..0x40123d30` | 60 | `0x400a9ca8` et les update |
| table d'onde `0x401202d0..0x401203c0` | 15 | `0x400a8204` (`movel %a5@(0,%d2:l:4)`, pour une partie de ses appels ; les autres lisent la SRAM) |
| LFO `0x40fde830..0x40fde900`, gains `0x40fe4c90..0x40fe4cf0` | 16 | LFO, gain de vélocité |
| tables de la boucle `0x40118610..0x40118640`, divers | 8 | boucle des voix, CHORD |

- **Les tables lues en SDRAM ne pèsent presque rien** : 84 lignes seulement lues, soit au pire (cache
  froid) 84 × 15 = 1 260 cycles = **0,8 % d'un bloc**, et 0 quand elles restent en cache [DÉDUIT]. Recopier en
  SRAM la table d'onde de `0x400a8204` (1 Ko, 15 lignes lues) ferait gagner au mieux 0,13 % : **pas rentable**.
- **Les états des voix sont l'essentiel** : 248 lignes lues et 205 réécrites (§3.10).

### 3.9 La SRAM interne de 64 Ko [FAIT, `sram_voix.txt`, `sramscan.out`]

- Remplie au démarrage par `0x4000045c` (appelée en `0x4000052c`) : `0x4019b590..0x401a2a50 → 0x80000000..0x800074c0`
  (29 888 o) puis zéros jusqu'à `0x80008000` ; `0x401a2a50..0x401aa140 → 0x80008000..0x8000f6f0` (30 448 o) puis
  zéros jusqu'à `0x80010000`. La source est ensuite effacée par la remise à zéro du BSS (`0x400004b2`).
- La voie des voix y touche **9,2 Ko** par bloc (`sramheat.out`, relevé corrigé ; `sram_voix.txt` disait 6,5 Ko,
  compté avant la correction des lectures) : lissage et LFO `0x80001000..0x80001780`, sorties des 6 pistes
  `0x80001858..0x80001b58`, brouillon commun des voix `0x8000be50..0x8000c8f0` (~2,7 Ko), tables d'onde des
  opérateurs `0x8000eae0..0x8000f6e0` (dont le sinus 257 × Q31 en `0x8000eee4`), lues surtout par `0x400a8204`.
- **Froid** : les 30 tables d'onde de CHORD (30 × 1 028 o, `0x80001c5c..0x800074b4` et `0x8000cac0..0x8000eae0`),
  lues par CHORD seul via les 32 pointeurs `0x40118590` (`0x400a8060`) : **30 Ko de SRAM inutiles quand aucune piste
  ne joue CHORD**, et une voix CHORD n'en lit que quelques lignes par bloc. Les moteurs du Syntakt les sortent déjà
  vers la charge utile pour y mettre leur code et leurs états de voix (notes/28, 29 ; `tools/emu/test_sram_code.py`).
- La zone `0x8000a100..0x8000bd18` est désignée par le code de sortie (`0x400567ba..0x400580c2` : mix, delay,
  reverb) : domaine de l'agent « sortie ».

### 3.10 Les états des voix sont en SDRAM [FAIT]

- 6 × `0x31c` = 4 776 o à `0x42308828` (cache copyback). Désignés directement par 5 constantes seulement :
  `0x400a7d78`, `0x400a7d7e`, `0x400a7d84`, `0x400a7d92` (boucle des voix) et `0x40059762` (pointeur de tampon
  `voix + 0x318`, posé par `0x4005974c`) [FAIT, recherche des constantes 32 bits de `0x40000400..0x40118000`].
  D'autres accès par une structure parente ne sont pas exclus [HYP].
- Par bloc, quand les 6 jouent : **248 des 299 lignes** des états sont lues, 205 réécrites [FAIT, relevé corrigé].
  Cache froid : 248 défauts × 15 = 3 720 cycles (**2,2 %**), plus jusqu'à 205 réécritures copyback plus tard
  (**1,8 %**) si l'interface, le mixeur ou les effets chassent ces lignes entre deux blocs : **0 à 4 % d'un bloc**
  selon ce qui tourne entre deux blocs, ce que l'émulation ne dit pas [DÉDUIT].

### 3.11 Le code d'un bloc ne tient pas dans le cache d'instructions [FAIT, `cachesim.py`]

- 686 lignes de 16 o de code distinctes par bloc quand les 6 machines jouent, pour **512 lignes** de cache
  d'instructions (8 Ko). Même sans rien d'autre entre deux blocs, le modèle LRU 4 voies donne **507 défauts
  d'instructions par bloc** (7 605 cycles, 4,6 % d'un bloc) : les machines se chassent l'une l'autre.
- À l'arrêt (6 KICK) : 308 lignes, qui tiennent ; 28 défauts au bloc chaud.
- Toute réduction du nombre de machines calculées réduit donc aussi ces défauts (§4.1).

---

## 4. Pistes d'optimisation

Chaque piste : ce qu'elle change ; gain (méthode) ; son ; preuve ; risque et conflits (`REGISTRY.md`, recouvrements
calculés par `proto/overlaps.py`, même règle que `tools/check_overlaps.py`) ; effort.

### 4.1 Arrêt des voix muettes pour l'OS d'origine seul — **prototype prouvé** (`proto/idle_stock.S`)

- **Ce qu'il change** : deux détours dans la boucle des voix. Avant update/render (`0x400a7dfe`), une piste sans trig
  (`voix + 0x34` et `+ 0x38` nuls) restée faible pendant 64 blocs n'est plus calculée : sortie à zéro, état figé.
  Après render (`0x400a7e24`), la division par 2 d'origine est refaite avec le test de silence (tous les échantillons
  divisés dans [−4 096, 4 096[, c'est-à-dire sortie de render sous 2¹³ = −108 dB, la règle des moteurs du Syntakt,
  `tools/gen_syntakt_engines.py:431-432`). 204 o de code et 8 compteurs dans le masque libre `0x40185f48`.
- **Gain** [FAIT en instructions, émulation ; DÉDUIT en % d'un bloc] :

| cas (fonction audio entière, `seqprof2.py`, seqrig) | origine | prototype¹ | modèle, cache froid | chaud |
|---|---:|---:|---:|---:|
| arrêt, rien joué depuis le démarrage (bloc 80) | 49 709 | **4 280** (boucle des voix 45 989 → **560**) | 52,1 → **5,4 %** | 46,7 → 4,0 % |
| 1,6 s après un trig des 6 pistes (réglages par défaut) | 45 986 | **17 614** (4 voix arrêtées sur 6 ; CHORD encore à −67 dB, TONE sous le seuil depuis moins de 64 blocs) | 52,0 → 21,4 % | 47,9 → 17,3 % |
| les 6 jouent (bloc 10 après le trig) | 46 020 | 41 792 (aucune arrêtée) | 52,1 → 48,4 % | 47,9 → 44,2 % |

¹ arrêt des voix muettes + `mix2` + PUNCH (§4.2, 4.3), tous trois ensemble ; lignes de code par bloc 308 → **111**
à l'arrêt, 683 → 415 à 1,6 s.

L'arrêt seul, boucle des voix seule (`proto/test_proto2.py 2`, mcengine, 6 voix KICK..CHORD, DECAY 20, trig au
bloc 1) : **−0,8 à −0,9 %** des instructions de la boucle tant que les 6 jouent (≈ −380, −0,35 % d'un bloc : la division refaite
4 par 4 coûte moins que celle d'origine, la mesure de crête est gratuite) ; SNARE s'arrête au bloc 142, CHORD 413, METAL 460, TONE 461, PERC 538 ;
avec 5 voix arrêtées et le KICK encore audible, **42 266 → 8 068 (−80,9 %)**. Une voix arrêtée coûte ~90
instructions par bloc (boucle comprise), contre 5 300 à 8 600 calculée.

Rapporté à la machine (notes/23 §6 bis : 77 % d'un bloc en moyenne à l'arrêt, dont ~47 % pour la boucle des voix),
l'arrêt des 6 voix rendrait **de l'ordre de 40 à 45 points** de bloc à l'arrêt et pendant les silences d'un motif
[DÉDUIT du modèle ; **à mesurer** avec le compteur de diagnostic]. Le gain est nul quand les 6 voix sonnent sans
cesse : c'est le cas le plus chargé qui décide si le son craque, et lui ne gagne que les 3,7 points de 4.2 + 4.3.

- **Durée des queues** (piste seule, dernier bloc au-dessus du seuil après un trig ; `kicktail.py`) [FAIT, `kicktail.out`] ; la voix s'arrête 64 blocs (43 ms) plus tard.

| machine | DECAY par défaut : sous −108 dB après | DECAY 20 |
|---|---|---|
| KICK | 28 : 1,46 s | 0,98 s |
| SNARE | 40 : 0,25 s | 0,05 s |
| METAL | 20 : 0,26 s | 0,26 s |
| PERC | 26 : 0,53 s | 0,32 s |
| TONE | 42 : 1,58 s | 0,26 s |
| CHORD | 64 : plus de 2,1 s (encore −75 dB à 2,1 s) | 0,23 s |

Conséquence : une piste qui reçoit un trig plus souvent que sa queue n'est jamais arrêtée (doubles croches à
120 BPM = 0,125 s) ; le gain vient de l'arrêt, des silences, des pistes sans trig et des sons courts [DÉDUIT].
- **Son** : identique échantillon par échantillon tant que la voix est calculée ; une fois arrêtée, la voix sort 0
  là où l'OS sort des valeurs sous −108 dB ; au trig suivant, écart ≤ 2,5·10⁻⁶ de la crête (−112 dB) parce que
  l'état figé n'a pas continué de décroître [FAIT, `proto/test_proto.out`, `proto/test_proto2_1.out`]. **Pas identique à l'octet près** après
  l'arrêt ; **identique** pour une voix jamais déclenchée (elle sort exactement 0 dans l'OS d'origine aussi).
- **Preuve** : `proto/test_proto.py` (1) chaque machine, 3 réglages (DECAY, PUNCH, COLOR… au hasard), piste seule,
  1 100 blocs, deux trigs ; (2) les 6 voix, DECAY 20, 1 200 blocs, coût bloc par bloc ; (3) 2 motifs de 1 000 blocs,
  machines, trigs et réglages au hasard, COLOR tourné pendant que des voix sont arrêtées. **Tout passe** [FAIT] : partie 1, 18 cas sur 18 (`proto/test_proto.out`
  pour les 10 premiers, `proto/test_proto2_1.out` pour les 8 autres, mêmes graines ; écart au 2ᵉ trig ≤ 2,5·10⁻⁶ de
  la crête, −112 dB ; les 5 autres pistes identiques) ; partie 2 (`proto/test_proto2_2.out`) : identiques jusqu'à
  l'arrêt puis référence sous le seuil — la dernière vérification de ce fichier, « muettes : moins d'un dixième au
  bloc 1 199 », échoue parce que **le KICK n'est pas encore sous −108 dB au bloc 1 199** (sa queue y reste 0,98 s à
  DECAY 20 et 1,46 s à DECAY 28, `kicktail.out`) : c'est l'attente du test qui était fausse, la voix est calculée,
  identique à l'origine ; partie 3 (`proto/test_proto2_3.out`, 2 motifs de 1 000 blocs, 2 à 6 trigs par piste,
  20 changements de COLOR) : 1 522 et 614 blocs-pistes arrêtés, la référence y est sous le seuil, ailleurs écart
  ≤ 5,3·10⁻⁷ de la crête ; 346 et 503 blocs sur 1 000 identiques à l'octet près (les autres ne diffèrent que par les
  valeurs sous le seuil des voix arrêtées et par les écarts infimes après un retrig). La 1ʳᵉ version de
  `test_proto.py` a été arrêtée par sa limite de temps (machine partagée) : `test_proto2.py` reprend les mêmes cas.
- **Risque** : faible pour la stabilité (moins de charge, aucun accès nouveau hors du masque ; seuls `d0, d1, a0, a1`
  changent, comme dans le code d'origine) ; récupération intacte (section 3 seule, rien au démarrage).
  Cas limites : l'enveloppe d'amplitude (`0x400a9252`) n'a d'attaque qu'après un trig (étage `voix + 0x23c` = 0,
  `0x400a92b8 addl %a0@(584),%d0 ; satsl`), et le compteur repart de zéro à chaque trig : une voix est donc calculée
  au moins 64 blocs après chaque trig, et une attaque, même très lente, dépasse −108 dB bien avant 43 ms [DÉDUIT] ;
  GATE tient le niveau plein (étage 2), donc la voix n'est pas faible ; le déclin (étage 1, `0x400a92e4 msacl`) est
  exponentiel et n'atteint jamais 0, d'où l'écart sous le seuil. Un réglage tourné pendant l'arrêt n'est vu qu'au
  trig suivant (update est refait au bloc du trig, avant render, comme l'OS) — couvert par la partie 3.
- **Conflits** : les tweaks qui ont **déjà** leur arrêt des voix muettes : `syntakt-*` (256 tweaks écrivent
  `0x400a7dfe`, dont 126 `syntakt-tg-*` aussi `0x400a7e24`), `model-tg`, `model-tg-st`, `acid-tg`, `macro-tg`,
  `macro-acid-tg` (`0x400a7dfe` ou `0x400a7e02`). Aucun recouvrement avec `acid`, `macro`, `macro-acid`, `6ch-usbup`,
  ni avec le masque et sa redirection (`0x40185f48`, `0x400ad9c4`, libres dans `REGISTRY.md:127`).
- **Effort** : moyen (le code est écrit et prouvé ; restent le générateur, la note, le banc du dépôt, le flasher).

### 4.2 `mix2` sans sa boucle morte — **prototype prouvé à l'octet près** (`proto/mix2.S`)

- **Ce qu'il change** : les 64 o de la 1ʳᵉ boucle (`0x400a98c4..0x400a9904`) deviennent `g0 += pas0 << 5 ;
  g1 += pas1 << 5 ; movclr %acc0,%d0` (l'effet de la boucle sur les gains et l'accumulateur, mêmes valeurs modulo
  2³²), puis un saut vers la 2ᵉ boucle. Écrit en place : pas de masque, pas de détour.
- **Gain** : **−598 instructions par voix KICK, SNARE, METAL ou PERC** (897 → 299 par appel) [FAIT] : −2,2 % d'un
  bloc quand les 6 machines d'origine jouent (4 appels), **−3,3 %** avec 6 voix de ces machines, dont l'arrêt (6 KICK)
  quand 4.1 n'est pas là [DÉDUIT].
- **Son** : **identique à l'octet près**, sorties et états complets des 6 voix (`6 × 0x31c` o) comparés bloc par bloc
  [FAIT, `proto/test_mix2.py` → `proto/test_mix2.out`, 5 essais de 300 blocs (arrêté par sa limite de temps
  après le 5ᵉ), machines/réglages/trigs au hasard, 60 changements de réglages par essai, chaque fois −3 588
  instructions par bloc pour 6 voix concernées : `43536 -> 39948`…].
- **Risque** : très faible (fonction feuille, même entrée/sortie). **Conflit** : `model-tg` et `model-tg-st` écrivent
  `0x400a98c4` (8 o) — ils font déjà l'équivalent ; il faudrait donc que ce tweak soit dans la base commune ou
  déclare `conflicts` avec eux.
- **Effort** : faible.

### 4.3 PUNCH éteint en chemin court — **prototype prouvé à l'octet près** (`proto/punch.S`)

- **Ce qu'il change** : détour en `0x400a9714` (6 o) vers 88 o dans le masque libre `0x40186238`
  (`REGISTRY.md:128`). Si `%d5 = 0` et `%d6 = 0x20000000` (PUNCH éteint), le 1ᵉʳ échantillon est calculé par les
  instructions d'origine, les 31 suivants par `mac.l %d2,%d1,4(%a3),%d1,%acc0 ; movclr ; move` (5 instructions au
  lieu de 13) ; sinon, la boucle d'origine. Le test est fait à chaque appel : aucune hypothèse sur les réglages.
- **Gain** : **−218 instructions par voix PUNCH éteint** (464 → ~246 par appel) [FAIT, essai 0 : machines KICK..CHORD,
  PUNCH éteint partout, 42 366 → 41 278 par bloc, 5 appels] : −1,0 % d'un bloc pour les 6 machines d'origine PUNCH
  éteint, −1,2 % pour 6 voix ; rien quand PUNCH est allumé (+4 à +6 instructions pour le test). Sur les 6 essais (PUNCH
  au hasard) : 264 001 → 259 685 instructions, −1,6 %.
- **Son** : **identique à l'octet près** (sorties et états des 6 voix), PUNCH allumé ou éteint, changé en cours de
  route [FAIT, `test_exact.py punch` → `proto/test_punch.out`].
- **Risque** : faible. **Conflits** : aucun tweak n'écrit `0x400a967a..0x400a9756`, ni le masque `0x40186238` et sa
  redirection `0x400ad988` [FAIT, `proto/overlaps.py`]. Avec Model-TG, je n'ai pas vérifié si `0x400a967a` est
  encore appelée par ses machines d'origine réécrites [HYP] : sans effet sur le son dans les deux cas (le détour est
  exact), seulement sur le gain.
- **Effort** : faible à moyen.

### 4.4 La division par 2 plus courte (existe déjà : `tools/voice_loop.py`)

- −384 instructions (−0,35 %), exacte, déjà prouvée et déjà écrite par 6ch-usbup, Model-TG, ACID, MACRO et les
  moteurs du Syntakt. Pour l'OS d'origine seul, c'est le gain le moins cher qui soit : une écriture de 14 o.
- Avec 4.1, elle est remplacée par la division faite dans le test de silence (~155 instructions par voix au lieu de
  224 d'origine ou 162 de `voice_loop.py`) [DÉDUIT du code : 8 tours de 17 instructions + ~20].

### 4.5 Opérateur `0x400a8204` réécrit [HYP, non prototypé]

- **Ce qu'il change** : la boucle de 27 instructions (`0x400a82d6..0x400a832c`) garde 4 incréments sur la pile.
  Sans toucher aux MAC : `movel %acc1,%d2 ; andil #0xffffff,%d2 ; moveq #16,%d3 ; asrl %d3,%d2` (index 0..255) devient
  `movel %acc1,%d2 ; swap %d2 ; mvzb %d2,%d2` (mêmes valeurs : `(x & 0xffffff) >> 16 = (x >> 16) & 0xff`) ; déroulée
  par 2, la boucle paie `subql/bnew` une fois pour deux échantillons ; `%a4`, inutilisé dans la boucle, peut porter un
  des 4 incréments (à sauver et rendre autour). Le masque `andil #0xffffff,%d7` de la phase doit rester : sans lui
  `%acc1` pourrait saturer à la relecture (MACSR = 0xa0, OMC) et le son changerait [DÉDUIT].
  Bilan : 2 instructions de moins par échantillon (27 → 25), plus 1 accès pile de moins.
- **Gain** : 416 tours par bloc quand les 6 jouent (13 appels × 32) : −832 instructions, **−0,8 %** (un peu plus en
  cycles, l'accès pile en moins) ; 576 tours à l'arrêt (6 KICK) : −1,1 %, mais rien à l'arrêt si 4.1 est installé
  [DÉDUIT : tours × instructions gagnées / 1 082]. La boucle déroulée ne tient plus en place : masque de sprite et
  détour, ou réécriture de toute la fonction (346 o, dont un prologue qui range sur la pile des valeurs aussitôt
  relues).
- **Son** : identique si l'arithmétique est la même (mêmes MAC, mêmes masques) — à prouver comme 4.2, sorties et états
  à l'octet près.
- **Risque** : faible (feuille) ; **conflits** : aucun tweak n'écrit `0x400a8204..0x400a835e` [FAIT, recherche dans
  les tweaks] ; Model-TG ne la réécrit pas. **Effort** : moyen (pression de registres).

### 4.6 Lissage des paramètres sauté à son point fixe [FAIT pour le point fixe, HYP pour l'implémentation]

- **Ce qu'il change** : un détour en tête de `0x40058474` qui saute le calcul quand l'état est stationnaire et que
  les 238 cibles `0x800015a0` n'ont pas changé depuis (comparaison avec une copie, ~120 instructions avec `movem`).
- **Gain** : ≤ 1 834 − ~150 ≈ **1,5 % d'un bloc** quand on ne touche à rien (cas courant, à l'arrêt comme en lecture).
- **Son** : identique (le calcul sauté aurait rendu exactement les mêmes valeurs : point fixe exact, §3.5). Preuve :
  comme `smooth_fp.py`, plus des cibles qui bougent au hasard pendant le lissage.
- **Risque** : faible ; il faut une copie de 476 o des cibles et un drapeau « stationnaire » (détecté en comparant
  l'état avant/après un calcul, 952 o), donc ~1,4 Ko de place : **pas dans un masque de sprite, il faut une autre
  zone** [HYP]. **Effort** : moyen.

### 4.7 Une piste mutée n'est plus calculée (comme Model-TG) [DÉDUIT, non prototypé]

- **Gain** : une voix entière par piste mutée (5,1 à 7,9 %).
- **Son** : identique dans le mix (gain nul), mais **pas** à la piste avant le mixeur (USB multipiste) et, au démute,
  la note figée repart d'un coup (notes/35 §3). Model-TG le saute quand un mod multipiste est là.
- **Risque** : moyen (artefact audible au démute pendant une note longue). **Effort** : moyen (le test des 6 gains
  `0x40a78c08..` existe dans Model-TG, MIT, à créditer).

### 4.8 États des voix en SRAM [DÉDUIT, non prototypé]

- **Ce qu'il change** : les 4 776 o de `0x42308828` en SRAM (5 constantes à changer, §3.10), à la place des tables de
  CHORD sorties vers la SDRAM comme le font déjà les moteurs du Syntakt.
- **Gain** : nul si le cache de données garde les états d'un bloc à l'autre ; jusqu'à ~4 % si tout est chassé entre
  deux blocs (248 lignes lues puis 205 réécrites en copyback, × 15 cycles, §3.10).
- **Son** : identique (mêmes calculs). **Risque** : moyen (tout accès indirect oublié lit l'ancienne place) ;
  **conflit** : les moteurs du Syntakt occupent déjà cette SRAM (notes/28, 29). **Effort** : élevé.

### 4.9 Update mis en cache [HYP]

- Refaire un update seulement quand un de ses réglages ou une de ses modulations a bougé. Gain ≤ 2,4 % (les 6 update
  entiers), plutôt ~1 %. Son identique si l'invalidation est complète, ce qui est difficile à garantir (états
  internes, LFO, enveloppes de hauteur). Risque moyen à élevé, effort élevé. **Pas recommandé** avant les autres.

### 4.10 Passes fusionnées (VCA + PUNCH + division) [HYP]

- ~1,2 % (§3.7), son identique possible, effort élevé (une réécriture du chemin de sortie par machine) : c'est le
  chemin qu'a pris Model-TG ; à faire seulement après 4.1 à 4.6.

### 4.11 Cache d'instructions : moitié verrouillée [HYP, pour l'agent « système »]

- 686 lignes de code par bloc pour 512 de cache (§3.11). Le MCF54415 permet de verrouiller la moitié du cache
  d'instructions (CACR) ; y garder l'opérateur `0x400a8204`, `mix2`, PUNCH, VCA et la boucle des voix (le code
  commun) supprimerait une partie des 507 défauts par bloc (jusqu'à 4,6 %). Non vérifié : effet sur l'interface et
  les autres interruptions inconnu.

---

## 5. Ce qu'il faut pour l'arrêt des voix muettes seul (OS d'origine, sans moteurs du Syntakt ni Model-TG)

Aujourd'hui l'arrêt n'existe que dans la passerelle des moteurs du Syntakt (`dispatch_asm`,
`tools/gen_syntakt_engines.py:421-432` ; `voice_gate` / `voice_after`, `tools/machines/syntakt_bridge/bridge_engines.c:253-369`,
en C, avec régulateur) et dans Model-TG (`voice_quiet`). Pour l'OS d'origine seul, **rien de cela n'est nécessaire** :

1. **Deux détours de 6 o** (`jmp abs.l`), ancien contenu vérifié :
   - `0x400a7dfe` : `b084 6522 2046` (`cmpl %d4,%d0 ; bcss 0x400a7e24 ; moveal %d6,%a0`) → `4ef9 <gate>` ;
   - `0x400a7e24` : `2695 2243 4280` (`movel %a5@,%a3@ ; moveal %d3,%a1 ; clrl %d0`) → `4ef9 <after>`.
   `gate` rejoue les instructions déplacées et revient en `0x400a7e04` (appel update/render inchangé, mêmes registres,
   même pile) ou en `0x400a7e38` (voix sautée) ; `after` revient en `0x400a7e38` (après la division d'origine, qu'il
   refait).
2. **204 o de code et 8 o de compteurs** dans un masque libre de 34 × 34 (`0x40185f48`, `REGISTRY.md:127`), avec sa
   redirection (`sprites.redirect_write(0x40185f48)`, une écriture de 4 o en `0x400ad9c4`). Les compteurs vivent dans
   le masque, en SDRAM cachée et inscriptible (ACR0 = `0x4007e020`, W = 0), à zéro au démarrage puisqu'ils font partie
   de l'image — le même procédé que level-pan (notes/44 §4).
3. **Assemblé** avec `m68k-linux-gnu-as -mcpu=54418`, sans relogement (sauts absolus, compteurs en `(d16,%pc)`) :
   le style de `tools/gov_asm.py`. Le prototype est construit par `proto/build_proto.py` / `proto/protos.py` au format
   des tweaks du dépôt (`off`, `old`, `new`).
4. **Pas de régulateur** : seuil fixe 2¹³ sur la sortie de render (4 096 après la division), 64 blocs, comme
   `IDLE_THR` / `IDLE_BLOCKS` sans `gov_pressure`.
5. **Registres** : `gate` ne touche que `d0, a0` (et `d1, a0` sur le chemin « voix sautée », où l'OS les recalcule
   ensuite) ; `after` sauve et rend `d2-d6` ; `d0, d1, a0, a1` sortent comme de la division d'origine
   (`0x400a7e40` recharge `d0`, le haut de boucle recalcule `d1` et recharge `a0`, `a1`). `d1` (modulation de note)
   reste intact avant update — un premier essai qui le cassait a été corrigé.
6. **Compatibilité** :
   - ACID, MACRO, MACRO + ACID sans Model-TG (écritures `0x400a7d6c`, `0x400a7dba`, `0x400a7dc4`, `0x400a7df4`,
     `0x400a7e16`, `0x400a7e2a`) : aucun recouvrement ; `gate` lit la borne des machines dans `d0` (posée par
     `0x400a7df4`, qu'ils changent) et la table des update dans `d6` (`0x400a7d6c`), et revient avant `0x400a7e14`
     (table des render) : leurs machines passent par le même chemin [DÉDUIT du code ; **non émulé** avec ACID ni
     MACRO, à prouver — leurs états de voix et leur arrêt doivent être vérifiés comme ceux des machines d'origine].
   - 6ch-usbup (`0x400a7e2a`) : pas de recouvrement ; sa division plus courte est contournée (faite par `after`,
     mêmes valeurs). La piste USB (prise avant le mixeur, `0x80001858`) d'une voix arrêtée vaut 0 au lieu de valeurs
     sous −108 dB [DÉDUIT].
   - **À déclarer en `conflicts`** : tous les `syntakt-*`, `model-tg`, `model-tg-st`, `acid-tg`, `macro-tg`,
     `macro-acid-tg` (ils ont déjà leur arrêt et écrivent `0x400a7dfe` / `0x400a7e02` / `0x400a7e24`).
     `tools/check_overlaps.py` le refuserait sinon.
7. **Ce qui reste à faire pour en faire un mod** (chemin habituel d'AGENTS.md) : note `notes/58-…`, générateur
   `tools/gen_idle_stock.py` (`--check`), banc `tools/emu/test_idle_stock.py` (reprendre `proto/test_proto.py`,
   ajouter ACID/MACRO et `--with 6ch-usbup,level-pan,arp,trig-hold…`), `registry.py` (le masque passe « pris »),
   `FEATURES` en `experimental`, textes en/fr, guide, notes de version. Essai sur la machine par Maxime : charge à
   l'arrêt (compteur de diagnostic de notes/23 §6 bis), son des 6 machines, retrig après un long silence.

Pour mémoire, la passerelle des moteurs du Syntakt mesure 42 278 → 9 571 instructions par bloc quand les 6 voix
d'origine se taisent (−77 %, notes/23 §7) ; ce prototype, sans C ni régulateur : 45 989 → 560 pour la boucle des voix quand les 6 sont arrêtées (−98,8 %, seqrig, jamais déclenchées), et ~90 instructions par voix arrêtée.

---

## 6. Classement

Gains en % d'un bloc du modèle (1 % ≈ 1 082 instructions), jamais mesurés sur la machine.

| # | piste | gain | son identique | risque | effort | état |
|---|---|---|---|---|---|---|
| 1 | Arrêt des voix muettes, OS d'origine seul (§4.1, §5) | **−42 à −47 points à l'arrêt** ; −30 points 1,6 s après des notes ; ~−0,35 % quand les 6 jouent | non après l'arrêt (valeurs < −108 dB mises à 0, retrig ≤ −112 dB) ; oui avant l'arrêt et pour une voix jamais déclenchée | faible ; à déclarer en conflit avec `syntakt-*`, `model-tg*`, `acid-tg`, `macro-tg`, `macro-acid-tg` (ils l'ont déjà) | moyen | **prototype prouvé** |
| 2 | `mix2` sans sa boucle morte (§4.2) | −2,2 % (6 machines d'origine), −3,3 % (6 voix KICK/SNARE/METAL/PERC) | **oui, à l'octet près** | très faible ; recouvre `model-tg`, `model-tg-st` (qui le font déjà) | faible | **prototype prouvé** |
| 3 | PUNCH éteint en chemin court (§4.3) | −1,0 à −1,2 % (PUNCH éteint) | **oui, à l'octet près** | faible ; aucun recouvrement | faible à moyen | **prototype prouvé** |
| 4 | Lissage des paramètres sauté à son point fixe (§4.6) | ≤ −1,5 %, à l'arrêt comme en lecture | oui (point fixe exact prouvé) | faible ; ~1,4 Ko de place à trouver | moyen | point fixe prouvé, pas de prototype |
| 5 | Opérateur `0x400a8204` réécrit (§4.5) | −0,8 % quand les 6 jouent | oui (à prouver) | faible ; aucun recouvrement | moyen | chiffré |
| 6 | Division par 2 courte (`tools/voice_loop.py`, §4.4) | −0,35 % | oui | nul (déjà dans le dépôt) | trivial | existe ; remplacée par 1 |
| 7 | États des voix en SRAM (§4.8) | 0 à −4 % selon le cache | oui | moyen ; la SRAM libérable est déjà prise par les moteurs du Syntakt | élevé | chiffré |
| 8 | Piste mutée non calculée (§4.7) | −5,1 à −7,9 % par piste mutée | non (USB avant mixeur ; note figée au démute) | moyen | moyen | Model-TG le fait (MIT) |
| 9 | Passes fusionnées VCA + PUNCH + division (§4.10) | ~−1,2 % | possible | moyen | élevé | estimé |
| 10 | Update mis en cache (§4.9) | ≤ −2,4 % (plutôt −1 %) | seulement si l'invalidation est complète | moyen à élevé | élevé | déconseillé pour l'instant |
| 11 | Moitié du cache d'instructions verrouillée (§4.11) | ≤ −4,6 % | oui | inconnu (interface, autres interruptions) | faible à essayer | pour l'agent « système » |

**Écartées** : replier la division par 2 dans le gain de vélocité (pas exacte, §3.2) ; recopier en SRAM les tables lues
en SDRAM (≤ 0,13 % pour la plus lue, §3.8).

**Ordre conseillé** : 2 et 3 d'abord (exacts, petits ; 2 ne recouvre que Model-TG, qui le fait déjà ; preuve à
l'octet près réutilisable :
`proto/test_exact.py`), puis 1 (le gros gain, qui change la nature du travail à l'arrêt et pendant les silences),
puis 4 et 5. Les trois premiers ensemble sont prouvés en émulation sur la fonction audio entière (`seqprof2.out`).
Pour la stabilité, 1 est la piste qui compte : elle rend du temps à l'interface quand la machine ne joue pas ou
peu ; le cas le plus chargé (6 voix qui sonnent sans arrêt) ne gagne, lui, que 2 + 3 + 5 + 6 (~4 points).

---

## 7. Fichiers et commandes

Dossier : `/tmp/claude-0/-home-user-Modded-Cycles/4cafd55d-d242-5df3-ad6a-3e64ee54ea56/scratchpad/optim/voix/`.

| fichier | rôle |
|---|---|
| `prof.py` | profileur (instructions par fonction, pile fantôme, accès mémoire par région/ligne, simulateur de cache) |
| `seqprof.py` → `seqprof.out`, `seqprof.json`, `seq_*.pkl` | `0x4005979e` par `seqrig`, états joue / muette / arrêt |
| `machines.py`, `machines2.py` → `machines.out`, `machines2.out` | chaque machine seule, update / render |
| `loops.py` | instructions par échantillon des boucles |
| `cachesim.py`, `sdramro.py` | cache 8 + 8 Ko, lignes SDRAM lues par fonction |
| `sramscan.py` → `sramscan.out`, `sramheat.py`, `sram_voix.txt` | qui désigne et qui touche la SRAM |
| `smooth_fp.py` | point fixe exact du lissage |
| `t_rd3.py` | le piège des crochets de lecture d'unicorn (cache de traduction) |
| `seqprof2.py` → `seqprof2.out` | fonction audio entière, origine contre prototypes, 3 états |
| `proto/idle_stock.S`, `proto/build_proto.py` | arrêt des voix muettes (OS d'origine), tweak `idle-stock-proto.json` |
| `proto/mix2.S`, `proto/punch.S`, `proto/protos.py` | `mix2` sans boucle morte, PUNCH éteint ; image combinée |
| `proto/test_proto.py` → `proto/test_proto.out` | preuve de l'arrêt des voix muettes (son, coût, motifs ; arrêtée après 10 cas) |
| `proto/test_mix2.py` | preuve de `mix2` (sorties et états à l'octet près) |
| `proto/test_exact.py` → `proto/test_punch.out` | preuve de PUNCH (et de tout prototype exact) |
| `proto/overlaps.py` | recouvrements avec les 282 tweaks du dépôt |
| `proto/test_proto2.py` → `proto/test_proto2_1.out`, `_2.out`, `_3.out` | suite de `test_proto.py` (mêmes cas), coût, motifs |
| `proto/test_mix2.out` | sortie de la preuve de `mix2` (5 essais) |
| `kicktail.py` → `kicktail.out` | durée des queues de chaque machine au-dessus du seuil |
| `sramheat.out` | SRAM touchée par plage et par fonction (relevé corrigé) |

Commandes (depuis le dossier, Python 3 + unicorn 2.1.4 + numpy, `m68k-linux-gnu-as`) :

```sh
python3 seqprof.py; python3 cachesim.py; python3 sdramro.py joue arret
python3 loops.py; python3 smooth_fp.py
python3 kicktail.py; python3 sramheat.py
cd proto && for p in 1 2 3; do python3 test_proto2.py $p; done
python3 test_mix2.py; python3 test_exact.py punch; python3 overlaps.py
cd .. && python3 seqprof2.py
```
