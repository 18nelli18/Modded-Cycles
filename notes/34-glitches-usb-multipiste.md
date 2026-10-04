# 34 — Glitches de l'audio USB avec Model-TG : diagnostic et correctifs

Travail du 03-04/10/2026, à la demande de l'utilisateur : « quelqu'un a dit ça sur Reddit : *Usb multitrack + TG Cycles
makes glitches after 15-20 mins usage, specially when make some tracks muted.* Ça révèle quand même que le projet pousse un
peu le Model:Cycles à bout. J'aimerais que tu fasses un gros et lourd travail d'optimisation et de performance. »

Adresses : VA de l'OS 1.13. Code de l'OS lu sur l'image officielle ; tout ce qui est marqué « simulé » vient du banc
`tools/emu/test_usb_in.py` (vrai code du pilote, contrôleur et horloges modélisés, §5).

## 0. En bref

| | État |
|---|---|
| Cause principale : l'envoi USB suit le calcul de chaque bloc, et la file du mod 6 canaux ne tolère que 0,2 ms d'écart | `[FAIT]` lu dans l'OS, reproduit en simulation (§1, §2) |
| La charge de Model-TG varie beaucoup (pistes au repos, mutes, effets éteints) : trous et trames sautées sur les pistes USB | `[FAIT]` simulé : 3 passages sur 3 avec défauts, 7 603 trames touchées en 6 s (§2) |
| Le même défaut, rare, en stéréo (Model-TG ou moteurs du Syntakt, sans le 6 canaux) | `[FAIT]` simulé : une micro-trame vide de temps en temps (§2) |
| Second défaut : avec Model-TG, une piste mutée ou au volume 0 est coupée net sur sa piste USB, et sa note figée repart au démute | `[FAIT]` prouvé en émulation sur la vraie boucle des voix (§3) |
| Correctif : envoi au début de l'interruption suivante, à heure fixe ; file alignée au démarrage ; ring de 9 cases au lieu de 8 | `[FAIT]` dans 6ch-usbup, Model-TG et les moteurs du Syntakt ; simulé : 0 défaut (§4, §5) |
| Correctif des pistes USB coupées au mute | `[FAIT]` retouche de Model-TG de même taille (§3) |
| Copie des 6 pistes déroulée : environ 640 instructions de moins par bloc, mêmes octets | `[FAIT]` prouvé sur 594 cas (§4) |
| Essai sur la machine | `[À FAIRE]` protocole au §7 |

## 1. Le chemin USB vers l'ordinateur `[FAIT]`

**Qui envoie, et quand.**
- L'interruption DMA de l'audio (`0x400589c0`, haute priorité) marque le début de chaque bloc de 32 trames : elle lit le
  minuteur DMA 2 (`0xfc07800c`, 12,288 MHz = 256 × 48 kHz) dans `0x40a78e04`, compte le bloc (`0x40a78e08`) et déclenche
  l'interruption de rendu.
- L'interruption de rendu (`0x40058c5e`) traite les événements du séquenceur, lit l'audio venu de l'ordinateur
  (`0x40002ae0`, en `0x40059338`), calcule le bloc (`jsr 0x4005979e` en `0x40059382`), puis **seulement après** l'envoie à
  l'ordinateur : `0x40002912(0x40fe4b90, 32)` en `0x40059392`. Quand le son est coupé (fichier ouvert, `0x40a78e14`), elle
  envoie du silence à la place (`0x400593ce`).
- L'instant d'envoi est donc « début du bloc + temps de calcul ». Avec l'OS d'origine, ce temps est presque constant
  (77 % d'un bloc, même à l'arrêt, [23](23-optimisation-charge.md)) : toutes les pistes et les effets sont calculés à chaque bloc.

**Le remplissage** (`0x40002912`) :
- il range les trames dans des cases d'environ 6 trames : 6 en moyenne, 7 de temps en temps, d'après le débit mesuré
  (accumulateur 16.16 `0x404a05f0`, débit `0x4013e4e4` relu toutes les 1 024 cases dans la table `0x404a0654`) ;
- chaque case pleine reçoit un dTD (réserve de 32 dTD en `0x80008000`, `0x4000231c`) et part dans la file du contrôleur
  (`0x40003f94`, point d'accès 7) ; le contrôleur en envoie une par micro-trame de 125 µs ;
- cases : ring en `0x80009800`, 16 cases de 56 o à l'origine (indice `0x8000bc94`, `moveq #15` en `0x400029b8`).

**Le démarrage du flux** (`0x40002778`, quand l'hôte choisit l'interface audio) :
- 11 cases de silence amorcées (`moveq #11` en `0x4000281e`), la 1re avec un rappel (`0x4000264a`) ;
- quand elle part, le rappel calcule les trames à sauter (`0x404a0620`) d'après l'horodatage de la micro-trame 0 de la trame
  USB où elle est partie (`0x422ff024`, écrit par l'interruption SOF `0x40004318` : temps écoulé depuis le début du bloc),
  puis lance l'envoi (`0x404a0644`, `0x404a0640`). L'hôte commence ses transferts isochrones en début de trame (1 ms).

**La mesure du débit** (`0x4000238e`, rappel périodique) : minuteur DMA 2 contre le numéro de micro-trame, lissage
(82/4096) et report du reste à la mesure suivante, toutes les 1 024 micro-trames environ. Elle suit l'écart d'horloge entre
l'hôte et l'audio sans dérive, mais elle ne regarde jamais la longueur de la file.

## 2. Pourquoi ça craque `[FAIT]`

**La file.** Juste après un envoi, la file compte environ 32 + 48 × D trames, où D (en ms) est l'avance de l'envoi sur le
moment où le contrôleur aura besoin de ces trames. Elle ne doit jamais se vider (trou : l'ordinateur reçoit une micro-trame
vide), ni dépasser le ring (une case encore en file est réécrite : trames sautées ou en double).

| | Ring | Amorçage | Fenêtre de l'avance D |
|---|---|---|---|
| OS d'origine (stéréo) | 16 × 56 o (96 trames) | 11 | environ 1,2 ms |
| Mod 6 canaux d'origine (`6ch-multiout`, et `6ch-usbup` jusqu'ici) | 8 × 192 o (48 trames) | 6 | environ **0,2 ms** |

- D vaut « constante fixée au démarrage − temps de calcul ». Avec l'OS d'origine, le temps de calcul varie peu : même les
  8 cases du mod 6 canaux suffisent (simulé : file de 0 à 6 cases, collée au bord bas, 0 défaut).
- **Model-TG** fait varier ce temps de 20 % à 95 % d'un bloc : il ne calcule pas les pistes au repos ni les pistes mutées,
  il éteint le delay et la reverb après 10,9 s de silence ([31](31-model-tg.md)). Nos moteurs du Syntakt font de même
  (arrêt des voix muettes, [23](23-optimisation-charge.md)). Muter des pistes fait chuter la charge d'un coup : l'envoi
  avance de plusieurs dixièmes de milliseconde, la file déborde ; démuter la fait remonter, la file se vide.
- **« Après 15-20 minutes »** : rien ne compte le temps dans ce chemin. Le niveau de la file est fixé par rapport à la
  charge du moment où le DAW a lancé le flux ; les défauts arrivent quand la charge s'en éloigne assez (motif plus dense,
  pistes mutées), ce qui prend un moment dans une session. La mesure du débit, lissée, ajoute une lente oscillation de la
  file autour de ce niveau. `[HYP]` pour le délai exact rapporté.

**Simulé** (2 s par passage, 3 phases de démarrage, +30 ppm, vraie mesure du débit de l'OS) :

| Firmware | Charge stable (77 %) | Pics à 99 % | Charge de Model-TG (mutes) |
|---|---|---|---|
| OS d'origine, stéréo | 0 défaut, file 5..11 sur 16 | 0 défaut | 2 passages sur 3 avec un défaut (une micro-trame vide), file 0..14 |
| 6 canaux d'origine | 0 défaut, file 0..6 sur 8 | 0 défaut | **3 sur 3, 7 603 trames touchées**, file 0..10 |

Un trou fait perdre 6 trames sur toutes les pistes (un clic) ; un débordement mélange des trames de blocs différents.

## 3. Pistes USB coupées au mute (Model-TG) `[FAIT]`

- `voice_quiet` (Model-TG, `src/model_tg.s`) ne calcule plus une machine d'origine quand les 6 gains du mixeur de sa piste
  (principal G/D et envois, `0x40a78c08`, `…be8`, `…bd0`, `…bb8`, `…b9c`, `…b80`) sont tous sous -90 dB : c'est ce que font
  un mute d'origine (FUNC + piste) et un volume à 0. Sa piste reste alors à zéro, et sa voix est figée.
- Dans le mix stéréo, c'est inaudible (le gain est déjà nul). Mais l'audio USB multipiste prend les pistes **avant** le
  mixeur (`0x80001858`, [09 §6](09-analyse-firmware-1.13.md)) : la piste USB d'une note mutée est coupée net, et au démute
  la note figée repart d'un coup. Une piste au volume 0 ne laissait passer que ses 2 premiers blocs à chaque trig.
- **Retouche** (`MC_PATCHES` de `tools/gen_model_tg.py`, dans les deux tweaks de Model-TG) : avec un mod multipiste, le test
  des gains est sauté, la piste s'arrête quand sa propre sortie se tait (0,25 s sous 2 LSB, comme sans mute). Le mod est
  reconnu à l'octet `0x40002ceb` (MaxPacketLength du point d'accès IN) : `0x38` à l'origine, `0xa8` avec le 6 canaux.
  Sans mod multipiste, rien ne change.
  - Même taille : 5 branchements raccourcis compensent les 10 octets du test ; seul le label local `vq_nop` bouge, aucune
    adresse de Model-TG, donc les 31 tweaks `31-syntakt-tg-…` restent valables tels quels.
  - Un Sampler muté garde le fondu de 64 échantillons de Model-TG (dans `amp_hook`, avant les pistes USB).
- **Preuve** (`tools/emu/test_model_tg.py`, nouvelle partie) : une note de TONE, gains à zéro du bloc 40 au bloc 120.
  - Model-TG seul : la note, encore forte (crête 1,0e8), n'est plus calculée dès le bloc 41, puis repart figée au démute ;
  - Model-TG + 6ch-usbup : la piste reste identique, échantillon par échantillon, à la note jamais mutée (260 blocs).

## 4. Le correctif `[FAIT]`

**Envoi à heure fixe** (`tools/machines/usb6/feed.S`, écritures dans `tools/usb_steady.py`, 196 o en `0x4015c23c`) :
- `0x40059392` et `0x400593ce` appellent `feed_note`, qui note l'envoi (source, trames) au lieu de le faire ;
- au début de l'interruption de rendu suivante (`0x40058ca0`, à la place de `movel #32,%macsr`, refait), `feed_isr` fait
  les envois notés, avant les événements du séquenceur et le calcul. L'instant ne dépend plus de la charge.
- Les sources sont intactes à ce moment : le mix USB (`0x40fe4b90`) et les pistes (`0x80001858`) ne sont réécrits que par
  le calcul du bloc suivant ; la moitié de sortie remise à zéro pour le silence n'est relue qu'un bloc plus tard.
- Coût : un bloc de latence en plus sur l'USB (0,67 ms). Rien d'autre ne change dans le son.

**Alignement au démarrage** (`align`, dans `feed.S`) :
- l'alignement de l'OS suppose l'envoi après le calcul ; avec l'envoi au début du bloc suivant, un départ tout près du
  début d'un bloc décalait la file d'un bloc entier (simulé) ;
- au 1er envoi d'un nouveau flux, `align` compte les cases encore en file (bit Active des dTD de la réserve IN, effacé par
  le contrôleur quand une case part) et fixe les trames à sauter pour que la file compte 16 + 3 × (cases du ring) trames
  juste après l'envoi : 64 en stéréo, 43 avec le ring de 9 cases. La profondeur est lue dans le code de l'OS
  (`0x400029b9`) : **les mêmes octets servent en stéréo et en 6 canaux**.

**Ring du 6 canaux** (`RINGS` de `tools/relocate_6ch.py`), dans la même SRAM qu'à l'origine (`0x80009800..0x80009f00`,
1 792 o ; `0x80009f00` sert au pilote USB) :
- envoi : 9 cases de 168 o (au lieu de 8 de 192 o) ; 168 = 7 trames × 24 o, la taille maximale d'un paquet. L'adresse
  d'une case passe par `mulu.w #168` (`0x400027d4`, `0x400029d2`), la dernière case est `moveq #8` (`0x400027b2`,
  `0x400029b8`), 8 cases de silence amorcées au lieu de 6 (`0x4000281e`) ;
- réception (ordinateur → Cycles) : 5 cases au lieu de 4, en `0x80009de8` (`0x4000253a`, `0x40002564`).
- Simulé, cibles de file sûres : de 42 à 44 trames avec 8 cases, de 39 à 47 avec 9 : la 9e case double la marge.

**Copie des 6 pistes déroulée** (`tools/machines/usb6/tracks6.S`, à la place du stub `tracks6` de ms-multi-output, même
place, 96 o) : une trame en 23 instructions au lieu de 43 (et sans le branchement mal prédit de la petite boucle de 6). Mêmes
octets écrits, mêmes registres et mêmes indicateurs à la sortie.

**Où** :
- `11-6ch-usbup.json` (`tools/relocate_6ch.py`) : tout ce qui précède ;
- `30-model-tg.json` et `30-model-tg-st.json` (`tools/gen_model_tg.py`) : l'envoi à heure fixe, plus la retouche du §3 ;
  la version combinée l'a donc aussi ;
- les 31 `24-syntakt-…` et `90-syntakt-meter` (`gen_syntakt_engines.py`, `usb_steady.add_to`) : l'envoi à heure fixe.
  Faute de `m68k-elf-gcc` 16.2 ici, ces fichiers ont reçu la même fonction pure que le générateur leur applique désormais ;
  vérifié avec GCC 13.3 : le générateur sort exactement les mêmes écritures (123 pour `syntakt-sd`) et la même
  description, seul diffère le code C compilé, que la greffe ne touche pas.
- Les constructeurs (`build.py`, `builder.js`) acceptent une écriture déjà faite à l'identique : 6ch-usbup, Model-TG,
  trig-hold (qui libère le même masque de sprite) se combinent sans rien changer au flasher.
- `10-6ch-multiout` reste le build de référence de ms-multi-output, inchangé (et absent du flasher).

**Ce qui a été examiné sans être changé** :
- le lissage des paramètres (`0x40058474`, environ 1 550 instructions par bloc), le delay (`0x40057488`) et la reverb
  (`0x400579c4`) : de l'EMAC déjà serré, sans travail redondant comme celui que Model-TG avait trouvé dans le mixeur à
  2 entrées ; les réécrire au bit près coûterait beaucoup pour peu ;
- le code C (passerelle du Syntakt, régulateur, arpégiateur) : il est compilé par `m68k-elf-gcc` 16.2 et ne se reproduit
  pas avec un autre GCC (l'arpégiateur ne tient même plus dans sa place avec GCC 13.3).

## 5. Preuves `[FAIT]`

**`tools/emu/test_usb_in.py`** : le vrai pilote de l'OS (remplissage, démarrage, rappel d'alignement, réserve de dTD,
mesure du débit, stubs du 6 canaux, `feed.S`) dans Unicorn ; modélisés : le contrôleur (une case par micro-trame, bit
Active effacé à l'envoi), l'interruption SOF, le début des blocs, le temps de calcul. Chaque trame porte son numéro et sa
piste : côté ordinateur, toute trame manquante, en double, sautée ou mélangée est comptée.

| Vérification | Résultat |
|---|---|
| Accroches : l'envoi suit le calcul (`0x40059382` puis `0x40059392`) ; Model-TG porte les mêmes crochets, vers le même code | OK |
| `tracks6` déroulé contre le stub d'origine : 594 cas (0 à 8 trames, départ 0 à 63 et au-delà) | mêmes octets, registres, indicateurs ; 269 → 149 instructions par case de 6 trames |
| OS d'origine (stéréo) : charge stable, pics | 0 défaut |
| OS d'origine (stéréo), charge de Model-TG | défauts (2 passages sur 3) : le problème existe aussi en stéréo |
| 6 canaux d'origine, charge de Model-TG | défauts à chaque passage |
| 6ch-usbup, 6ch-usbup + Model-TG, Model-TG en stéréo : 3 charges × 8 phases de démarrage × 3 écarts d'horloge (−100, +30, +100 ppm) | **216 passages, 0 défaut** ; file 1..7 sur 9 (6 canaux), 4..11 sur 16 (stéréo) |
| 6ch-usbup, 60 s, charge de Model-TG, +60 ppm, vraie mesure du débit | 2 878 941 trames, 0 défaut, file entre 1 et 6 cases chaque seconde |

**Non-régression** (firmware complet 6ch-usbup + Model-TG + 5 moteurs + trig-hold + arpégiateur) :
`test_model_tg.py`, `test_model_tg_syntakt.py`, `test_trig_hold.py`, `test_arp.py` passent ; `ref_mainos.py` (2 303
combinaisons, 2 272 empreintes changées) ; `webflash_smoke.sh` avec les deux OS (chaque combinaison reconstruite dans la page
redonne son empreinte) ; `relocate_6ch.py --check`, `gen_model_tg.py --check`, `gen_trig_hold.py --check`.

## 6. Empreintes

| `-t` | MAIN OS patché (SHA-256) |
|---|---|
| `6ch-usbup` | `a7086bee…` |
| `model-tg` | `2a939b7f…` |
| `6ch-usbup,model-tg` | `de845665…` |
| `syntakt-sd-cp-toy-bits-swarm` (`--syntakt`) | `c4616b24…` |
| `6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm,trig-hold,arp` (`--syntakt`) | `2562fb2d…` |

Valeurs complètes : [`BUILD.md`](../BUILD.md) et `REF_MAINOS` de `docs/flasher/app.js`.

## 7. Essai sur la machine `[À FAIRE]`

1. Flasher 6ch-usbup + Model-TG (par le flasher web), enregistrer les 6 pistes dans le DAW pendant 30 minutes avec un motif
   chargé, en mutant et démutant des pistes souvent (FUNC + piste, et le mute verrouillé).
2. Écouter, et passer l'enregistrement à `analyse_dupes.py` de ms-multi-output ([01 §6](01-ms-multi-output.md)) : aucune
   trame en double ni manquante attendue.
3. Vérifier qu'une piste mutée sonne jusqu'au bout de sa note sur sa piste USB, et ne repart pas au démute.
4. Vérifier `CONFIG > UPGRADE` par USB (le 6ch-usbup le garde) et l'audio stéréo USB avec Model-TG seul.

## 8. Limites et suite

- **Audio de l'ordinateur vers le Cycles en mode 6 canaux** : le ring de réception passe de 4 à 5 cases (30 trames),
  toujours moins que les 32 trames lues par bloc. Cet audio reste haché avec le 6 canaux, comme avant. Il faudrait 6 cases
  ou plus, donc moins de place pour l'envoi : à décider (et à simuler) si quelqu'un en a besoin.
- La surcharge pure (un bloc qui dépasse 100 %) reste possible avec Model-TG seul, qui n'a pas de régulateur ; le nôtre
  n'existe qu'avec les moteurs du Syntakt ([25](25-regulateur-de-charge.md), [30](30-regulateur-charge-soutenue.md)).
- Toucher au code C demande `m68k-elf-gcc` 16.2 (paquet Homebrew), indisponible dans cet environnement.
