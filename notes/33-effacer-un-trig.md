# 33 — Effacer un trig : le délai de maintien des touches de pas

Un défaut de l'OS d'origine, signalé par des utilisateurs : il faut souvent appuyer plusieurs fois sur une touche de pas pour
effacer un trig. Analyse sur le MAIN OS 1.13, correctif `41-trig-hold.json`, preuve en émulation. Adresses : VA de l'OS 1.13.

## Le problème signalé

- **Reddit, r/Elektron** (message transmis le 03/10/2026, lien [reddit.com/r/Elektron/s/Mad3fWDwU4](https://www.reddit.com/r/Elektron/s/Mad3fWDwU4)) :
  il faut « appuyer plusieurs fois, fort », pour effacer des pas. L'auteur le relie au comportement peu clair des pas p-lockés ;
  les réglages de sensibilité de l'appareil n'y changent rien. Le même message demande aussi deux fonctions (§6).
- **Elektronauts, « Removing trigs bug? »** ([t/135144](https://www.elektronauts.com/t/removing-trigs-bug/135144)) :
  - la fenêtre avant qu'un trig tenu passe en mode p-lock au lieu d'être effacé est jugée « ridiculement courte » ;
  - les touches souples (« squishy ») du Model:Cycles s'enfoncent plus lentement que les touches mécaniques des autres Elektron.
- **Elektronauts, « Model cycles trig delete? »** ([t/167469](https://www.elektronauts.com/t/model-cycles-trig-delete/167469)) :
  l'utilisateur ne pouvait effacer aucun pas ; il appuyait « trop fort et trop longtemps ».

Aucun de ces fils ne mentionne de correction par Elektron. L'OS 1.13 est la dernière version.

## 1. Des touches aux événements `[FAIT]`

| Étage | Où | Ce qu'il fait |
|---|---|---|
| Panneau | minuteur en `0xfc08c000`, 12 kHz (`PMR` 11 264, sans prédiviseur), cycle de 12 phases (`0x40059cd0`, `0x40059d2c`, `0x40059db8`) | lit les octets des touches sur la logique du panneau (`0x8c000002`) vers `0x40a791cc`, une fois par milliseconde |
| Anti-rebond | `0x40059e64`, 1 kHz | un appui est signalé **tout de suite** ; un relâchement l'est après **19 ms** stables ; appelle `0x4007fbde(octet, état)` |
| Événements | `0x4007fbde` | pour chaque bit changé : type 0, code (table `0x4010aef8`), indicateurs, heure (minuteur DMA 0, `0xfc07000c`, 135,168 MHz), postés dans la boîte `0x40148cd0` (`0x40001fba`) |
| Maintien | `0x4007f914`, appelée à chaque tick du minuteur en `0xfc088000` | voir ci-dessous |
| Interface | boucle `0x40007f80` → `KeyEvent` (`0x4007238c`) → `0x400060fe` → `ViewController::handleKeyEvent` (`0x40077720`) | |

- Indicateurs : bit 0 appui, bit 1 FUNC tenu, bit 2 double appui (même touche, moins de 32 ticks), bit 3 maintien, bit 4
  relâchement, bit 5 maintien long. `KeyEvent` : `+8` heure, `+12` code, `+16` indicateurs, `+20` vélocité (`0x7f`).
- Touches de pas : codes 16 à 31 (touches 14 à 29 de la matrice). FUNC : code 1.
- **Horloge de maintien : 120 Hz.** Minuteur en `0xfc088000` : `PCSR` `0x0636 | 9` (prédiviseur 2⁶), `PMR` 17 600 ;
  135,168 MHz / 64 / 17 600 = 120 Hz. Le fil `0x400020e6` appelle chaque rappel inscrit par `0x40002144` quand son bit du
  compteur change ; `0x4007f914` est inscrite avec le masque 1 (`0x4007fe5e`), donc à chaque tick (8,33 ms).
- **Le maintien** : à l'appui, `0x4007fbde` arme un compte à rebours (`0x40f942f4`) avec `0x40148cc8` = **24 ticks = 200 ms**,
  et un second compteur (`0x40f942f0`) à 64. À zéro, `0x4007f914` poste un événement « indicateurs de l'appui | 8 », puis
  recommence tous les `0x40148cc4` = 8 ticks (66,7 ms), tant que personne ne l'arrête ; à 64 ticks (533 ms) il ajoute `0x20`.
  Seule la **dernière touche appuyée** (`0x40148cd4`) reçoit ces événements.
- Les autres constantes voisines : `0x40148ccc` = 32 ticks (double appui), `0x40148cc0` = 4 (encodeurs). Elles ne sont
  écrites que par des fonctions jamais appelées (`0x4007faba`, `0x4007fad0`) : ce sont les valeurs de l'image.

## 2. Le mode grille `[FAIT]`

`PatternGridView::consumeKeyEvent` (`0x40022382`, entrée 2 de la vtable `0x40100ae8`) envoie les codes 16 à 31 en
`0x400223fa`. Le pas est `page × 16 + code − 16` (registre `a3`). L'état est dans `UIStates` (singleton `0x40fe4218`) :
pas tenus en `+348` (64 bits), une **action en attente** par pas en `+92 + 4 × pas` (`0x4006b8fe` / `0x4006b91a`),
le **maintien** en `+356` (`0x4006b736` / `0x4006b740`).

| Événement | Code | Effet |
|---|---|---|
| Appui sur un pas vide | `0x40022c22` (sans FUNC), `0x40022cda` (avec) | trig de note (`0x40017b48`) ou de lock (`0x40017bb0`) posé tout de suite, action 0 |
| Appui sur un trig | idem | action en attente : 1 effacer (`0x40017c4e`) ; 2 trig de lock → note ; 3 note → lock (avec FUNC) ; FUNC sur un trig de lock : 1 |
| Maintien (bit 3) | `0x40022d44` → `0x40022d50` | action annulée, maintien marqué (`0x4006b740(1)`), répétitions arrêtées (`0x400724c6`) |
| Relâchement | `0x40022da6` | si maintien marqué : rien ; sinon l'action en attente |

- Le maintien est aussi marqué par un tour de potard pendant l'appui (`0x4001e96a`, `0x4001ea24` : création et changement
  d'un p-lock) et par la copie, le collage ou l'effacement des locks d'un pas tenu (`0x40022670`, `0x400227dc`, `0x40022a00`).
  Le trig reste alors, quelle que soit la durée de l'appui.
- `[HYP]` Le maintien est ce qui fait afficher les réglages du trig : les méthodes de `NoteVelocityView` lisent `+356`
  (`0x400299f6`, `0x40029c14`, `0x40029d48`), et les fils Elektronauts décrivent l'affichage de la note, de la vélocité et
  de la longueur au moment où l'effacement n'est plus possible.

**Conclusion : relâcher avant 200 ms après l'appui efface le trig ; après, il reste.** Avec les 19 ms de l'anti-rebond au
relâchement, il faut que le contact dure moins d'environ 180 ms. C'est le défaut signalé.

## 3. Le correctif : `41-trig-hold.json`

Trois accroches dans `PatternGridView::consumeKeyEvent`, à la place de trois `jsr` (6 octets chacune) :

| Adresse | D'origine | Accroche | Rôle |
|---|---|---|---|
| `0x4002249c` | `jsr 0x40072490` (FUNC ?) | `th_press` | note l'heure de l'appui de la touche, même réponse |
| `0x40022d44` | `jsr 0x40072460` (maintien ?) | `th_hold` | maintien accepté au bout de **500 ms** si le pas a une action en attente ; avant, l'événement est consommé sans rien faire et les suivants arrivent toujours (tous les 66,7 ms) |
| `0x40022da6` | `jsr 0x4006b736` (maintien marqué ?) | `th_release` | le trig reste aussi si l'appui a duré plus de 500 ms |

- **L'heure** est celle de l'événement (`+8`), en unités de 65 536 coups du minuteur DMA 0 (0,485 ms) sur 16 bits, une
  case par touche de pas (`code & 15`) : 32 octets. 16 bits rebouclent au bout de 31,8 s, sans gêne : passé 500 ms, le
  maintien est déjà marqué.
- **Pourquoi l'accroche du relâchement** : la dernière touche appuyée reçoit seule les maintiens. Pas 1 tenu, pas 5 appuyé
  à 300 ms : le pas 1 ne recevra plus de maintien ; à son relâchement, la durée de son appui décide.
- **Pas vide** : rien n'est en attente, le maintien est accepté à 200 ms comme avant (les réglages du nouveau trig
  s'affichent aussi vite qu'avant).
- **Pourquoi pas la constante `0x40148cc8`** : elle règle le maintien de **toutes** les touches (pads, TRACK, FUNC…).
- **Place** : 134 o de code et 32 o d'heures au début du masque de sprite libéré `0x4015c044` (`tools/sprites.py`), devant
  les stubs de `6ch-usbup` (`0x4015c116..0x4015c23a`). Les deux tweaks réécrivent de la même façon le pointeur du sprite.
- **Démarrage** : rien n'est exécuté au démarrage ; les accroches ne servent qu'aux touches de pas en mode grille.
  `CONFIG › UPGRADE` par USB n'est pas touché.
- Source : `tools/machines/trig_hold/` ; générateur `tools/gen_trig_hold.py` (vérifie les octets d'origine et la place).

## 4. Preuve en émulation : `tools/emu/test_trig_hold.py`

La vraie chaîne de l'OS, à la milliseconde, sur l'OS d'origine et sur l'OS modifié : l'interruption d'anti-rebond, la
fonction des événements, l'horloge de maintien à 120 Hz, le constructeur de `KeyEvent`, `PatternGridView::consumeKeyEvent`
et les méthodes de `UIStates`. Interceptés : la boîte aux lettres (événements rendus tout de suite), les trigs de la piste,
l'accès au projet, l'écran. Durées = contact de la touche (le relâchement arrive 19 à 20 ms plus tard).

| Appui sur un trig | OS d'origine | OS modifié |
|---|---|---|
| 100, 150, 170 ms | effacé | effacé |
| 190, 250, 350, 450, 470 ms | gardé (réglages affichés à 194 ms) | **effacé** |
| 520, 600, 1 000, 1 500 ms | gardé (194 ms) | gardé (réglages affichés à 527 ms) |

Et aussi, sur les deux : pas vide (trig posé, affiché à 194 ms), tour de potard pendant un appui de 120 ou 300 ms (gardé),
pas 1 tenu 800 ms avec le pas 5 appuyé à 300 ms (les deux gardés). Sur l'OS modifié : deux appuis courts qui se
chevauchent (les deux effacés), FUNC + trig de note de 300 ms (changé en trig de lock ; gardé à l'origine), trig de lock de
300 ms (changé en trig de note) et de 800 ms (gardé), minuteur qui reboucle pendant l'appui.

**TOUT OK** seul, avec `6ch-usbup`, avec Model-TG (sa charge utile chargée : il intercepte `0x4007240c`, la lecture du
code des événements), avec `6ch-usbup,model-tg`, avec les trois tweaks de drumkilla et l'arpégiateur, avec
`6ch-usbup,model-tg-st,arp,syntakt-tg-sd-cp-toy-bits-swarm` et avec `6ch-usbup` + drumkilla + arpégiateur + les 5 moteurs.

Flasher web : carte « Effacer un trig plus facilement », testée sur la machine (§5) ; `REF_MAINOS` passe à 2 303 combinaisons
(`tools/ref_mainos.py`, 1 min) ; `build.py` et `builder.js` acceptent la zone (référence du sprite réécrite).

## 5. Essai sur la machine `[FAIT]`

**Testé le 03/10/2026** sur un vrai Model:Cycles, avec `6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm,arp,trig-hold`
(MAIN OS `6cf5d636…`, celui que construit le flasher) : les points 2 à 5 ci-dessous, plus deux pas tenus avec un p-lock et
le reste (lecture, arpégiateur, mutes, Sampler, audio USB) : « tout marche nickel ». Carte passée en « testé ».

Protocole suivi :

1. Flasher par le flasher web la carte seule (ou avec les cartes habituelles).
2. Sur un pas qui a un trig, appuyer normalement et relâcher : le trig doit s'effacer du premier coup.
3. Tenir un trig : ses réglages s'affichent au bout d'une demi-seconde environ, et le trig reste au relâchement.
4. Tenir un trig et tourner un potard aussitôt, puis relâcher : le trig reste avec son p-lock.
5. Pas vide : le trig se pose tout de suite.
6. FUNC + touche de pas sur un trig, appui court (moins d'une demi-seconde) : le même changement qu'un appui très bref avec
   l'OS d'origine (en émulation : un trig de note devient un trig de lock).

Si 500 ms se révèle trop long ou trop court : `T_MS` de `tools/gen_trig_hold.py`, puis regénérer (§3).

## 6. Les deux autres demandes du message Reddit

- **Écouter un pas déjà posé** : c'est déjà le tweak `trig-preview` de drumkilla (séquenceur à l'arrêt, pas tenu + PAGE),
  dans le flasher (carte « Écoute d'un pas ») et dans Model-TG.
- **Choisir la hauteur au clavier du Model:Cycles, puis la donner aux pas posés ensuite** (aujourd'hui, il faut un clavier
  MIDI) : `[À FAIRE]` à étudier (note jouée en mode clavier, puis p-lock de note au placement d'un trig dans
  `PatternGridView`, en `0x40022c22`).
