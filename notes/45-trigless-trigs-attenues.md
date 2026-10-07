# 45 — Les trigless trigs atténués sur les touches de pas : le tweak `trigless-dim`

Mod de **djd_oz** (communauté), envoyé à Maxime le 06/10/2026 avec un premier mod (note 44) : l'archive
`Cycle_PAN_TriglessTrig_Mods.zip`, ici le fichier `model-cycles_OS1.13_Trigless-Trigs-LED-36pct-v4-experimental.syx`,
un OS 1.13 complet déjà modifié. Demande de Maxime : « Vérifie-les, dis-moi comment les tester sur ma machine pour
ensuite les intégrer au webflasher ». Tweak `47-trigless-dim.json` (`tools/gen_trigless_dim.py`, sources dans
`tools/machines/trigless_dim/`), preuve en émulation `tools/emu/test_trigless_dim.py`. Adresses : VA de l'OS 1.13.

## En bref

- **En mode grille, une touche de pas qui porte un trigless trig (lock trig, FUNC + touche) s'allume à environ 36 %**
  au lieu de pleine lumière, comme un trig de note. Elle garde son clignotement d'origine (éteinte 0,35 s toutes les
  2 s). Trigs de note, trigs avec p-locks, lumière de lecture, pads et autres LED : inchangés.
- Comment : le mode grille donne à ces touches leur propre état de LED, 260, que le reste de l'OS traite comme 4 ;
  l'horloge des LED (120 Hz) les éteint en plus 16 ticks sur 25.
- Ce découpage est lent (des impulsions vers 43 Hz) : **un scintillement est possible**, à juger sur la machine.
- Le fichier de djd_oz est sain et se flashe seul (§1), mais ne se combine pas en l'état (même raison que la note 44).
  **Réécrit ici pour s'exécuter en place, dans un masque de sprite libéré**, avec une correction : les touches à
  atténuer sont relevées à la fin de chaque image de l'interface. Chez lui, un tick tombé au milieu d'une image les
  rallumait à fond (§3). En régime établi, mêmes LED que son fichier, tick par tick (§7).

## 1. Le fichier de djd_oz `[FAIT]`

Seule la section 3 (MAIN OS) diffère de l'officiel ; sections 2, 4 et 5 et en-tête identiques, HMAC valide. 312 o
ajoutés après l'image (`0x401aa140`), recopiés au démarrage en `0x42339000..0x42339107` par la même accroche
`0x4000045c` que son autre mod (note 44 §1).

| Écriture | Où | Quoi |
|---|---|---|
| T1 | `0x4000045c` | recopie de son code en `0x42339000` au démarrage |
| T2 | `0x40005f36` | clignotement (`0x40005efc`, 2 Hz) : l'état 260 clignote comme 4 |
| T3 | `0x40021f52` | mode grille, pas qui porte un trigless trig : `movea.w #4,a5` → `movea.w #260,a5` |
| T4 | `0x4008e754` | envoi d'une rangée de LED : l'octet envoyé perd les bits du masque |
| T5 | `0x4008e7a8` | comparaison des 7 rangées : la valeur à afficher perd les bits du masque |
| T6 | `0x4008e7ca` | tick des LED (120 Hz) : motif +9 modulo 25 ; sur un tick éteint, le masque reçoit les LED dans l'état 260 |
| T7 | `0x4008e82e` | `beq` → `nop` : les rangées sont comparées et envoyées à chaque tick, plus seulement quand un minuteur de LED expire |

Analyse, émulation et relecture contradictoire (400 tirages au hasard des états, minuteurs, registres, pointeur nul) :
aucun plantage, aucune écriture hors des LED, de son état et de la pile, registres rendus. **Verdict : se flashe seul
sans risque.**

## 2. Ce que fait l'OS `[FAIT]`

| Où | Quoi |
|---|---|
| `*0x40fe4200` | l'objet des LED (constructeur `0x40005e76`) ; `+40` : l'état des 54 LED logiques (mots longs) |
| `0x4010abf8` | LED logique → bit des 7 octets de LED (octet = bit / 8, bit = bit % 8 ; -1 = pas de LED). Les 16 touches de pas sont les LED logiques 1 à 16 |
| états | 0 : pas d'état (passe à 1 en fin d'image) ; 1 : éteinte ; 2 : allumée (trig de note) ; 3 : allumée, éteinte 50 ms toutes les 0,5 s (trig avec p-locks) ; 4 : allumée, éteinte 0,35 s toutes les 2 s (trigless trig) |
| `0x40006a4a` | une image de l'interface (30 Hz, tâche de l'interface, priorité 6) : `0x4000602a` remet les 54 états à 0, les vues posent les leurs (`0x40076ca2`), puis `0x40006044` |
| `0x40005f86(obj, led, état, …)` | pose l'état si la LED n'en a pas encore (le premier gagne) et le bit de base de la LED |
| `0x40006044(obj)` | fin de l'image : les LED sans état passent à 1, puis `jmp 0x4008e77e` (en `0x40006086`) |
| `0x40021d22` | mode grille (`PatternGridView`), boucle des pas `0x40021ed6..0x40021f8a` : a5 = 2 (trig de note), 3 (p-locks), 4 (trig qui ne joue pas la note : le trigless trig posé par `0x40017bb0`), puis `0x40005f86`. 260 n'est écrit qu'en `0x40021f52` par le mod |
| `0x40005efc` | clignotement (2 Hz, `0x4009109e(…, 2, …)`) : état 3 → `0x4008e8c4(led, 6)` ; état 4 → `0x4008e8c4(led, 42)` une fois sur quatre (phase `0x404a90f4`) |
| `0x4008e8c4(led, n)` | inverse la LED pendant n ticks de 120 Hz (minuteurs des LED) |
| `0x4008e7ca` | tick des LED (120 Hz, tâche des minuteurs `0x400020e6`, priorité 10, la plus haute), sous le verrou `0x40fde2e8` : minuteurs ; si l'un expire, `0x4008e77e` |
| `0x4008e77e` | compare les 7 rangées (base ⊕ minuteurs) au dernier envoi ; une rangée changée part par `0x4008e732(rangée)` → `*0x401492f8` = `0x40059fd2`, qui écrit l'octet inversé dans la copie `0x40140aa8` lue par l'interruption du panneau |

La tâche des minuteurs (priorité 10) interrompt la tâche de l'interface (priorité 6) n'importe où : un tick des LED
peut tomber entre la remise à zéro des états (`0x4000602a`) et leur écriture par le mode grille.

## 3. La réécriture

| Accroche | Origine | Mod |
|---|---|---|
| `0x40005f36` | `cmp.l 40(a4),d1 ; beq.s 0x40005f6c` | `jmp td_blink` : 4 et 260 clignotent pareil |
| `0x40006086` | `jmp 0x4008e77e` | `jmp td_frame` : relevé des LED dans l'état 260 (`td_lock`), puis `jmp 0x4008e77e` |
| `0x40021f54` | `0004` | `0104` : `movea.w #260,a5` |
| `0x4008e754` | `eor.l d0,d3 ; mvz.b d3,d0 ; move.l d0,-(sp)` | `jmp td_send` |
| `0x4008e7a8` | `mvz.b (a2,d2.l),d1 ; mvz.b d0,d0` | `jmp td_cmp` |
| `0x4008e7ca` | `lea -12(sp),sp ; movem.l d2-d3/a2,(sp)` | `jmp td_tick ; nop` : motif ; masque = `td_lock` sur un tick éteint, vide sinon |
| `0x4008e82e` | `beq.s 0x4008e834` | `nop` |

Mêmes accroches que djd_oz (plus `0x40006086`), même motif : `td_cnt += 9`, tick allumé au passage de 25
(`0010010010010100100100101`, 9 sur 25).

**La correction.** Chez djd_oz, le tick cherchait les LED dans l'état 260 à chaque tick éteint. Un tick qui tombe entre
la remise à zéro des états et le mode grille n'en trouve aucune : le masque est vide et la touche s'allume à fond
pendant ce tick (8,3 ms) ; la preuve le montre (§7). Les deux horloges viennent de la même horloge du bus, presque
exactement dans le rapport 4 pour 1 (minuteur des LED : 4 × 17 601 × 64 = 4 505 856 cycles par image ; DTIM3 de
l'interface : 281 601 × 16 = 4 505 616) : la place du tick dans l'image dérive lentement, donc un tick qui tombe dans
cette fenêtre peut y rester plusieurs secondes, et la touche s'éclaircit nettement `[HYP]` : la durée de la fenêtre
n'a pas été mesurée, et le décalage du début de l'image peut aussi éparpiller ces ticks. Ici, `td_frame` relève les LED
dans l'état 260 à la fin de chaque image, quand les états sont complets ; le tick n'applique que ce relevé, qui ne
change pas pendant la fenêtre. Contrepartie : quand on pose ou retire un trigless trig, le masque suit au plus une
image plus tard (33 ms).

Autres détails : le relevé et le masque sont construits sur la pile puis écrits en deux mots longs (djd_oz remettait
le masque à zéro puis le remplissait en place, qu'un envoi de la tâche de l'interface pouvait lire à moitié fait) ; un
mélange de l'ancien et du nouveau relevé ne peut durer qu'un tick. `td_tick` ne lit plus l'objet des LED.

## 4. Effets de bord

- `[FAIT]` T7 : les rangées sont comparées et envoyées à chaque tick, pour toutes les LED. Un changement de LED arrive
  au plus un tick plus tôt qu'à l'origine ; seules des valeurs déjà décidées partent.
- `[FAIT]` L'état 260 est vu par tous les lecteurs du tableau des états, qui le traitent comme 4 : `0x40005f86`
  (« ≠ 0 », « = 1 »), `0x40005ff6` (« ≠ 0 »), `0x40006044` (« = 0 »), `0x4000602a` (remise à zéro) ; la lecture
  `0x40006016` n'a pas d'appelant. Model-TG (`sld_led`, accroché juste après, en `0x40021f56`) transmet a5 tel quel.
- `[HYP]` Scintillement : 9 ticks sur 25 à 120 Hz donnent des impulsions vers 43 Hz ; avec le rafraîchissement des
  rangées toutes les 7 ms, un battement lent vers 2,5 Hz. En dessous des 60 à 100 Hz habituels pour une LED atténuée
  sans scintillement : à juger à l'œil.
- `[FAIT en émulation]` Coût : tick des LED de 412 à 565..765 instructions (16 trigless trigs), fin d'image de 365 à
  831 ; environ 0,05 M instructions par seconde en tout. Rien dans le chemin audio.

## 5. Place et conflits

- Code et état dans le masque de sprite 47 × 47 libéré `0x4018dba8` (284 o sur 376), identique au masque gardé
  `0x40172220` et désigné seulement par la constante de son constructeur (`0x400accfe`), redirigée. `td_cnt` en
  `0x4018dcb0`, `td_mask` en `0x4018dcb4`, `td_lock` en `0x4018dcbc`.
- Masque attribué le 07/10/2026 avec les autres branches en cours (le premier choisi, `0x4018d4a8`, est pris par
  chord-keys). Aucune écriture commune avec les 81 autres tweaks du dépôt, ni avec chord-keys (PR #46 et #50) ;
  `46-level-pan-values` (note 44) se combine avec. Model-TG écrit en `0x40021f56` et `0x40021f67`, à côté de
  `0x40021f54` sans le toucher.

## 6. Le tweak

`47-trigless-dim.json`, 9 écritures : le masque (code et état), la constante de son constructeur, les cinq accroches,
`movea.w #260,a5` et le `nop`. Les octets d'origine viennent du MAIN OS officiel et sont vérifiés par le générateur.

## 7. Preuve en émulation `[FAIT en émulation]`

`tools/emu/test_trigless_dim.py`, vrai code de l'OS (image de l'interface, clignotement, tick des LED jusqu'à la copie
`0x40140aa8`), MAIN OS d'origine contre MAIN OS modifié, `--djd` contre le fichier de djd_oz, `--with` sur les autres
mods. 50 ticks, LED 1 = trig de note, 2 = p-lock, 3 = trigless trig :

| Cas | Origine | Modifié | djd_oz |
|---|---|---|---|
| Trig de note, trig avec p-locks | allumés | identiques à l'origine | identiques |
| Trigless trig | `1111…` | `00100100100101001001001010…` (18 sur 50) | identique au modifié |
| 16 trigless trigs | — | les 16 suivent le motif ; masque = bits 6, 16, 19 à 23, 28, 29, 31, 37, 38, 40, 44, 46, 47 | identique |
| Clignotement 2 Hz, phase 0 | `0x4008e8c4` (3, 42) pour l'état 4 | mêmes appels pour l'état 260 | — |
| Clignotement sur un trigless atténué | éteint 41 ticks puis allumé | éteint 41 ticks puis atténué | identique |
| Tick au milieu d'une image (10 ticks, remise à zéro des états, 25 ticks) | allumé | `0010010010 \| 0101001001001010010010010` : reste atténué | `0010010010 \| 1111111111111111111111111` : à fond |
| Toutes les autres LED | — | identiques à l'origine, tick par tick | — |
| Avant l'objet des LED (pointeur nul) | rien | rien | — |
| Registres et pile (tick, fin d'image) | — | rendus | — |

Avec `--with 6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm,arp,trig-hold,tempo-max,boot-anim,level-pan-values
--syntakt Syntakt_OS1.42.syx`, et avec `chord-keys` (PR #50) à la place de Model-TG : tout ok.

Non émulé : la vraie vue de la grille (`0x40021d22`, qui demande un pattern en mémoire) ; l'écriture de 260 y est
vérifiée octet par octet et par la lecture du code.

## 8. À vérifier sur la machine `[À FAIRE]`

- Arrêté, une piste : des trigs de note, un trigless trig (FUNC + touche sur un pas vide), un trig avec un p-lock. Le
  trigless trig nettement plus sombre, avec son clignotement de 2 s ; les autres comme à l'origine.
- Le scintillement : regarder une touche atténuée de côté, balayer le panneau des yeux, en lumière faible. Le juger.
- Regarder une touche atténuée 3 à 5 minutes, à l'arrêt : pas de salves où elle s'éclaircit (la correction du §3).
- 16 trigless trigs sur une page : atténués pareil ; changer de piste et de page : l'atténuation suit.
- PLAY : la lumière de lecture passe toujours sur chaque pas ; sur un trigless trig, elle l'éteint puis il revient
  atténué.
- Transformer un trigless trig en trig de note, l'effacer ; enregistrement en direct de p-locks (de nouveaux trigless
  trigs apparaissent atténués).
- Hors du mode grille (clavier, choix de pattern, mute, menus) : touches et pads comme à l'origine.

## 9. Crédit

Idée, motif et accroches de djd_oz ; réécriture et correction de ce projet. Crédit sur la carte du flasher et dans
`PROVENANCE.md`. Sa licence n'est pas encore connue : Maxime la lui demande avant la fusion.
