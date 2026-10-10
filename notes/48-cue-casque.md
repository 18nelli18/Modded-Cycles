# 48 — Écouter les samples au casque seulement (cue) : le tweak `sample-cue`

Demande de la communauté : fil Discord « headphone cue / audition bus » (07/10/2026), relayé par Maxime dans le
projet : « main outputs = live performance ; headphones = performance + sample audition », comme le PFL d'une table de
mixage DJ. La même demande est ouverte chez Model-TG ([issue #7](https://github.com/TinyGregAudio/Model-TG/issues/7)).
Maxime : « je pense qu'on peut avoir une sortie différente sur l'USB et les jacks […] je ne sais pas si c'est possible
entre MAIN L/R et le casque ». Tweaks `34-sample-cue.json` (sur `sample-preview`) et `34-sample-cue-st.json` (sur
`sample-preview-st`, mêmes écritures), générés par `tools/gen_sample_cue.py` depuis `tools/machines/sample_cue/`
(`sample_cue.S`, `sample_cue.ld`), preuve en émulation `tools/emu/test_sample_cue.py`. Adresses : VA de l'OS 1.13 ;
celles de Model-TG sont celles de sa v1.1.0 (identiques dans ses deux versions).

**Statut : expérimental. Premier test sur la machine (07/10/2026) : couper OUT1_R n'a rien coupé, MAIN OUT R joue toujours (§9). Le cue split tel qu'il est écrit ne marche pas sur la machine de Maxime tant que le diagnostic (§9.1) n'a pas montré une autre coupure possible.**

## Réponse courte

- **Un vrai cue casque stéréo (MAIN OUT intact, écoute seulement au casque) est impossible, même par firmware**
  `[FAIT pour le processeur, HYP forte pour la puce]`. Le processeur n'envoie que deux canaux (G, D) à la puce audio ;
  dans cette puce (très probablement une Dialog DA7210), la sortie ligne (MAIN OUT) et l'ampli casque prennent le même
  mélange, côté par côté. Seuls leurs volumes diffèrent (réglage HP MAX). §1.
- **Jacks et USB sont deux copies séparées du mix** `[FAIT, émulé]` : l'OS s'en sert déjà (le clic du métronome ne va
  qu'aux jacks, `INT OUT = OFF` coupe les jacks en gardant l'USB). §2.
- **Le cue « split » des tables DJ était l'idée** : couper la sortie ligne droite dans la puce (registre `0x1F`) devait
  rendre MAIN OUT R muet sans toucher à l'oreille droite du casque. Le canal G porte alors la perf en mono (MAIN OUT L
  et oreille gauche), le canal D la perf en mono plus l'écoute (oreille droite seulement). Le prix : MAIN OUT en mono
  sur L. §4. **Sur la machine, couper `0x1F` n'a pas coupé MAIN OUT R** (07/10/2026) : diagnostic en cours, §9.
- **L'écoute des samples (notes/46) ne suffit pas** : elle joue sur la voix de la piste, donc dans le mix, l'USB et le
  rééchantillonnage. Le tweak ajoute un **petit lecteur à part** dans l'interruption audio, après l'étage de sortie et
  après le rééchantillonnage de Model-TG. §3, §4.
- 730 o dans cinq masques de sprites 48×22 libérés, 16 écritures ; prouvé en émulation, seul et avec les autres mods
  (§7). Le même source sait ajouter l'écoute aux jacks seulement ou à l'USB seulement (§6).

## 1. Le matériel `[FAIT]`

Lu dans le code (initialisation `0x400441de..0x40044344`, pilote de la puce `0x400443ba`), comparé au pilote Linux de
Dialog (`sound/soc/codecs/da7210.c`) ; deux relectures contradictoires ont refait les vérifications clés.

**Un seul flux audio numérique.** SSI0 seulement (SSI1 n'est jamais touché, ni dans l'OS ni dans le bootloader) :

| Registre | Valeur | Sens |
|---|---|---|
| CR | `0xB0`, puis `\|1`, `\|2` | synchrone, maître, horloge MCLK en sortie ; émission seulement |
| TCR | `0xE8` | horloges internes, FIFO 0 seulement, cadrage à gauche (format de Linux « left-justified ») |
| CCR | 24 bits, 2 mots par trame | **2 canaux** : ni mode réseau (TDM), ni mode deux canaux |
| eDMA canal 50 (TCD `0xFC045640`) | ring de 512 o en `0x4A3ED080`, 8 o par requête (G puis D) | interruption toutes les 32 trames |

L'OS du Syntakt, sur la même famille de puce, règle lui son SSI1 en mode réseau à 8 canaux : le Cycles ne le fait pas.
Les DAC internes du processeur (DAC0/DAC1) ne portent que des niveaux fixes (luminosité, batterie), le PWM n'est pas
utilisé : rien d'autre ne sort du son.

**La puce audio**, adresse I2C `0x1A` (bus I2C0, le seul). Toutes ses écritures (`0x400443ba` n'est appelée que depuis
`0x4004462e`, `0x400445ec`, `0x40044734` et `0x40044754`), lues avec le pilote DA7210 :

| Registre | Valeur | Sens (DA7210) |
|---|---|---|
| `0x2B` PLL_DIV3 / `0x2C` PLL | `0x50` / `0x0B` | 48 kHz, PLL contournée (valeurs exactes de l'init Linux) |
| `0x26` / `0x28` DAI_CFG | `0x06` / `0x81` | mots de 24 bits, trame de 64 bits, cadrage à gauche |
| `0x17` DAC_SEL | `0xDC` | DAC G ← canal G, DAC D ← canal D (identique à Linux) |
| `0x1C` / `0x1D` OUTMIX_L / R | `0x90` | mélangeur de sortie = DAC seulement |
| `0x1E` / `0x1F` OUT1_L / R | `0x80 \| (v + 16)` | **sortie ligne G / D** (MAIN OUT) : bit 7 = marche, volume `v` = 0..38 |
| `0x22` HP_R_VOL | min(v, HP MAX) + 16 | volume casque (le registre G `0x21` n'est jamais écrit, voir §8) |
| `0x23` HP_CFG | `0xAA` | casque G et D en marche |

Aucune autre puce essayée (DA7212/7213/7218, WM8731/8960, SSM2603, NAU8822) ne colle à ces valeurs. Le marquage du
boîtier n'a pas été lu (boîtier à billes U17, notes/21).

**Dans la DA7210, OUT1 et l'ampli casque sont branchés au même point** (sortie du mélangeur, côté par côté) : aucun
registre ne donne une autre source au casque. Le bouton de volume (`0x400248e0`) règle OUT1 = volume
(`0x400447b6` → `0x400445ec`) et le casque = min(volume, HP MAX) (`0x40044754`).

Donc : **casque G = MAIN OUT L, casque D = MAIN OUT R**, au volume près. Un cue stéréo est impossible ; couper OUT1_R
seul (`0x1F` bit 7 = 0) garde l'oreille droite et rend MAIN OUT R muet, si MAIN OUT est bien branché sur OUT1 et le
casque sur l'ampli casque de la puce `[HYP, §9]`.

## 2. Jacks et USB `[FAIT, émulé]`

L'étage de sortie `0x400567ba(moitié du ring, état)` (seul appelant : `0x4005979e`, en `0x40059872`, une fois par bloc
de 32 trames dans l'interruption de rendu `0x40058c5e`, niveau 5) fait deux copies du bus maître `0x8000b990` (après le
×4 de `0x400565c6`) :

- **jacks** : −bus / 256 (+ l'entrée USB × gain USB, + le clic du métronome), écrêté à ±2²³, dans la moitié du ring que
  le DMA ne lit pas (`0x4A3ED080 + 256 × p[40]`) ; polarité inverse du bus ;
- **USB** : `0x40fe4b90` ← copie brute du bus, envoyée par `0x40002912` (ou au début du bloc suivant avec l'envoi à heure
  fixe de Model-TG, notes/35 : une modification faite pendant le rendu part quand même).

Précédents dans l'OS d'origine : le clic ne va qu'aux jacks ; `INT OUT` (`0x404e9b54`) = OFF retire le son interne des
jacks et le laisse sur l'USB. Avec `6ch-usbup`, le pilote USB ignore `0x40fe4b90` et envoie les six pistes avant le
mixeur (`0x80001858`) : une écoute « USB seulement » n'y a pas de sens. Pendant une sauvegarde de fichier, le rendu est
sauté et les jacks sont à zéro (`0x4005939c..0x400593ce`).

## 3. Pourquoi l'écoute des samples ne suffit pas

`sample-preview` (notes/46) désigne un son « SMP » + empreinte, et la note suivante du pad le joue **sur la voix de la
piste** : le Sampler de Model-TG la rend dans `0x80001858 + 128 × piste`, donc dans le mix (MAIN OUT, casque, USB) et
dans le rééchantillonnage, et la piste perd sa note en cours. Pour un cue, il faut que cette note n'aille pas au moteur
audio, et qu'un lecteur à part lise le sample et l'ajoute à **une seule sortie**, **après** le mix.

## 4. Le tweak

### 4.1 Ce que voit le musicien

Une piste Sampler, FUNC + MACHINES, le curseur sur un fichier de sample : tenir le pad de la piste (ou une de ses touches
en mode clavier) fait entendre le sample dans l'oreille droite du casque, à sa hauteur d'origine, tant qu'on tient.
Relâcher, bouger le curseur, charger le fichier ou fermer le navigateur l'arrête (fondu de 0,7 ms). La piste continue
son pattern ; MAIN OUT L porte la perf en mono, MAIN OUT R est muet ; l'USB garde le mix stéréo, sans l'écoute. Les
presets s'écoutent comme avant, sur la piste.

### 4.2 Accroches

| VA | Octets d'origine | Écrit | Rôle |
|---|---|---|---|
| `0x4008180e` | `4aae0018 6664` (`tst.l 24(fp) ; bne.s 0x40081878`) | `jmp cue_dec` | note jouée (`0x4008171e`, après `pv_note`) |
| `0x4008145e` | `4e56ff84 707f` (`link.w ; moveq #127`) | `jmp cue_off` | relâchement |
| `0x40081bd6` | `41ef0004 23d0` | `jmp cue_arm` | seul écrivain du son désigné `ARMED` (`0x40fb5a04`) |
| `0x400a6bec` | `400a64fa` (constante) | `cue_load` | fonction de chargement d'un fichier, installée par le navigateur |
| `0x40059878` | `4fef0014 245f` (`lea 20(sp),sp ; movea.l (sp)+,a2`) | `jmp cue_out` | fin de `0x4005979e` : le lecteur |
| `0x40044614` | `2f02` (`move.l d2,-(sp)`) | `42a7` (`clr.l -(sp)`) | split : OUT1_R (`0x1F`) = 0 au démarrage et à chaque volume |

Aucune n'est écrite par un autre tweak (main et branches ouvertes) ; aucun branchement de l'OS ne vise leurs octets
(relevé des images d'origine, Model-TG, 6ch-usbup + Model-TG + sample-preview). `0x4008171e` lui-même n'est pas
touché : c'est la chaîne OS → Model-TG (`pad_load_hook`) → `pv_note`, qui doit charger le sample avant `cue_dec`.

**`cue_dec`** (tâche de l'interface) : si la note est « sans envoi » (chargement raté dans `pv_note`), la suite
d'origine. Sinon, seulement pour la piste active, la source `0x40` (pads, touches), un son désigné **identique octet
pour octet à `pv_src`** (le son que `pv_parse` construit pour un fichier de sample : un preset garde son écoute
d'origine), qui nomme un sample (`tok_of`) qui n'est pas une prise du rééchantillonnage (`0x524d00nn`) et qui est en
mémoire. Alors : paramètres publiés interruptions masquées (case, empreinte, adresse, nombre, plan stéréo, gain),
`GO` = 1 en dernier ; la note est retenue (128 bits par piste) ; le compteur de notes tenues `0x40fb5c0c[(piste << 7) +
note]` que `0x4008171e` vient d'incrémenter est défait ; sortie par l'épilogue `0x4008190e`. La note n'existe pas pour
l'OS : ni moteur audio, ni message d'enregistrement (live rec), ni arpège.

**`cue_off`** : le relâchement d'une note retenue (même piste, source `0x40`) ne part pas non plus ; celui de l'appui qui
joue demande l'arrêt. Sinon les deux instructions déplacées, puis `0x40081464`.

**`cue_arm`** : un autre son désigné (curseur, fermeture du navigateur : `0x40081bd6(0)`) demande l'arrêt ; garde
d0, d1 et a1 (des appelants rendent d0 après l'avoir appelé par `jmp`). **`cue_load`** : demande l'arrêt sans toucher un
registre (`addq.l #1, STOP`), puis `0x400a64fa`.

### 4.3 Le lecteur (`cue_out`, `cue_play`)

À `0x40059878`, `0(sp)` = la moitié des jacks que `0x400567ba` vient de remplir, **après** `rs_out` de Model-TG (le
rééchantillonnage lit le bus et teste son seuil de départ sur cette moitié : l'écoute n'y entre jamais). d2-d7/a4-a6 sont
gardés, a2/a3 rechargés de la pile.

1. Split : G = D = (G + D) / 2 sur les 32 trames (la perf en mono), à chaque bloc.
2. Si `GO` : la case doit contenir toujours ce sample (`slot_hash[case]` = empreinte **et** `slot_base[case]` = adresse
   du départ), sinon arrêt, sans lire un octet ; nombre = min(nombre du départ, `slot_count[case]`) ; k = min(32,
   restants).
3. Pour chaque échantillon s du plan « milieu » (16 bits, `slot_base + 64 + 2 × pos`) : D = écrêté(D − (s × gain) / 256)
   (jacks = −bus / 256 : même phase que la perf). Gain = vélocité × 106 (× gain d'une prise Q12, plafonné à 32 767) :
   une vélocité de 100 donne le niveau d'une piste Sampler par défaut (s16 × 10 640 sur le bus, mesuré en émulation,
   à 0,4 % près).
4. Arrêt demandé : le gain descend jusqu'à 0 sur ce bloc, puis `GO` = 0.

Règles de sûreté avec Model-TG (son chargeur peut chasser une case à tout moment depuis la tâche de l'interface, mais
l'interruption le préempte toujours) : jamais de recherche par empreinte dans l'interruption (Model-TG publie
`slot_hash` avant `slot_base`) ; contrôle des deux à chaque bloc ; lectures bornées par `slot_count`. Reste un cas
rare : `rebuild_slots` / `rs_keep` (défragmentation) recopie des prises par-dessus des cases de fichiers encore
marquées valides ; l'écoute en cours ferait alors un bruit au casque jusqu'au bloc où la case change, jamais une
lecture hors de la zone des samples `[HYP, jamais vu]`.

**Coût** (émulé, instructions par bloc de 32 trames) : split 239 au repos (la somme mono), 719 en lecture ; à
1 500 blocs par seconde, moins de 1 % du processeur en lecture.

## 5. Place et conflits

| Masque 48×22 (192 o) | Constante redirigée | Contenu |
|---|---|---|
| `0x40152d38` | `0x400b9726` | `cue_dec` + `cue_off` (182 o) |
| `0x401592bc` | `0x400b7404` | `cue_start` + `cue_arm` + `cue_load` (180 o) |
| `0x4015943c` | `0x400b73e4` | `cue_out` (148 o) |
| `0x4015f38c` | `0x400b504a` | `cue_play` (88 o) |
| `0x40165fec` | `0x400b28b4` | `cue_held` + `cue_data` (132 o) |

43 sprites 48×22 ont le même masque de 192 o ; on garde celui de `0x4014b364` (`SHARED_48` de `tools/sprites.py`) et
leurs constructeurs pointent dessus. Trois autres masques du groupe sont réservés pour ce mod (`0x40168a84`,
`0x40168da4`, `0x4016bcd8`, libres). `gen_sample_cue.check_overlaps` : aucune écriture ne recouvre un tweak qui peut
aller avec (tous ceux du catalogue sauf ceux que Model-TG ou l'écoute des samples excluent). Le tweak demande
`sample-preview` (qui demande `model-tg`) : le flasher coche les trois ensemble.

## 6. Les trois sorties

`sample_cue.S` s'assemble pour trois sorties (`CUE_MODE`), toutes prouvées en émulation (§7) ; seul le split est
généré, en attendant le choix de Maxime (carte de décision du 07/10/2026) :

| Sortie | Casque | MAIN OUT | USB | Prix |
|---|---|---|---|---|
| 1 split | G : perf mono ; D : perf mono + écoute | L : perf mono ; R muet | stéréo, sans l'écoute | MAIN OUT mono |
| 2 jacks | perf + écoute (stéréo) | perf + écoute | sans l'écoute | le public entend l'écoute si la sono est sur MAIN OUT |
| 3 USB | perf | perf | perf + écoute | pas avec `6ch-usbup` ; l'écoute à l'ordinateur seulement |

## 7. Preuve en émulation `[FAIT en émulation]`

`tools/emu/test_sample_cue.py`, le vrai code de l'OS, de Model-TG et de l'écoute des samples (banc de
`test_sample_preview.py`), origine = Model-TG + sample-preview :

| Cas | Origine | Modifié |
|---|---|---|
| pad, sample sous le curseur en mémoire | note d'écoute envoyée à la piste, message d'enregistrement | rien d'envoyé ; compteurs rendus ; écoute démarrée (case, empreinte, gain 10 600) ; registres et niveau rendus |
| relâchement de cet appui | fin de note envoyée | rien ; arrêt demandé |
| MIDI (source `0x80`), autre piste, « sans envoi », preset désigné, prise du rééchantillonnage | — | identique à l'origine, pas d'écoute |
| sample pas en mémoire, chargement raté / réussi | rien / la note | rien / écoute sur la case chargée |
| vélocité 127, gain de prise 0,5 et 3 | — | 13 462, 5 300, 32 767 (plafond) |
| curseur bougé, fermeture, même son, chargement | — | arrêt / arrêt / rien (d0, d1, a1 gardés) / arrêt, registres et pile intacts |
| lecteur, 12 cas × 3 sorties (repos, lecture, fin, case vidée ou déplacée, nombre réduit, fondu, écrêtage, plan stéréo) | jacks et USB intacts | exact face au modèle numpy ; lectures dans les échantillons du bloc ; écritures dans la moitié des jacks (USB) et `cue_data` |
| `0x400445ec`, `0x400447b6` (volume) | `0x1F` = (v + 16) \| `0x80` | `0x1F` = 0 ; `0x1E` inchangé |
| de bout en bout : navigateur, pad, 3 blocs, relâchement, fondu, silence, nouvel appui | écoute dans le mix | écoute à droite seulement, perf mono, fondu, silence, repart du début |

Avec `--with 6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm,arp,trig-hold,tempo-max,boot-anim` et avec
`6ch-usbup,arp,trig-hold,tempo-max,boot-anim` (les deux versions de Model-TG) : tout OK. Avec la machine MACRO
(notes/43, fusionnée le 07/10/2026), Model-TG prend sa base `model-tg-st` et l'écoute `sample-preview-st` : le cue
prend `34-sample-cue-st` (clé `macro` de sa carte, comme l'écoute) ; aucun recouvrement avec `25-macro` ni
`32-macro-tg`, et `--with model-tg-st,macro-tg` puis `--with 6ch-usbup,model-tg-st,macro-tg,arp,trig-hold,tempo-max,
boot-anim` : tout OK (la charge utile de MACRO copiée à sa place, comme dans le banc de l'écoute).

## 8. Limites et points à vérifier sur la machine

- **Câblage** `[HYP]` : MAIN OUT sur la sortie ligne de la puce, casque sur son ampli casque (§9).
- **HP_L_VOL (`0x21`) n'est jamais écrit** : le bit 5 de HP_CFG (`0xAA`), absent du pilote Linux, est probablement le
  suivi stéréo (le volume D règle les deux oreilles). Si l'oreille gauche du casque ne suivait pas le volume, ce serait
  aussi vrai sur l'OS d'origine.
- Les **pads envoient toujours leur note MIDI** pendant une écoute (le message part après `0x4008171e`, `0x4001d0ec`) ;
  à couper plus tard si gênant (accroches `0x4001d0ee`, `0x40019f36`).
- Une seule écoute à la fois, **sans hauteur** : toutes les touches jouent le sample à sa hauteur d'origine ; une
  nouvelle touche relance le sample du début.
- Sur une **piste Sampler** seulement (comme l'écoute des samples) ; les presets ne passent pas par le cue.
- `INT OUT = OFF` coupe la perf des jacks, pas l'écoute.
- Le défragmenteur de Model-TG (§4.3) : un bruit possible au casque pendant une écoute, jamais vu en émulation.

## 9. Firmware de test du câblage

`/mnt/project-files/cue-casque/test-split-casque_model-cycles_OS1.13.syx` (envoyé à Maxime le 07/10/2026, jamais dans
le dépôt) : l'OS officiel 1.13 avec seulement `0x40044614` `2f02` → `42a7` (OUT1_R = 0), sections 2, 4 et 5
identiques, MAIN OS `8623f45136ef84481fdf3bc1b307840339ce1bfd6eab77d53f45ef36e47bfe94`. Un son qui joue :

- MAIN OUT R muet, MAIN OUT L normal, casque normal des deux côtés : câblage attendu, le split marche ;
- l'oreille droite du casque se tait aussi : le casque est pris sur la sortie ligne, pas de split possible (rester sur
  la sortie « jacks » ou « USB », §6) ;
- rien ne change : la puce n'est pas une DA7210.

**Résultat sur la machine (Maxime, 07/10/2026)** : « Headphone marche dans les deux oreilles, et dans les mains j'ai
le L qui marche et le R qui marche aussi ». Rien n'a changé.

Relecture `[FAIT, émulé]` : l'image de test diffère de l'officielle seulement en `0x40044614`, et tous les chemins qui
écrivent le registre `0x1F` envoient `34 1F 00` (démarrage `0x400054ba` → `0x400441de` → `0x4004462e`, volume
rappelé au démarrage `0x400057de` → `0x400248e0`, bouton, HP max, `0x400514c8`/`0x40051504`, réinitialisation par la
surveillance `0x40044188`). Aucune autre écriture I2C n'existe dans les sections 2 à 5 (seul I2C0 est utilisé, à
l'adresse `0x1A`). La troisième lecture ci-dessus est fausse : le jeu d'écritures ne s'explique que sur une DA7210/7211
(registre `0x01` relu et comparé à `0x17`, données sur 8 bits). Restent `[HYP]` :

- le firmware de test n'a pas tourné (il n'avait pas de marque visible) ;
- MAIN OUT sort de l'ampli casque de la puce (HPL/HPR, par le DRV632), comme le casque : pas de cue split possible ;
- MAIN OUT R suit le registre de gauche `0x1E` (bit non documenté, ou câblage) : pas de split par `0x1F`.

Les photos de la carte ne tranchent pas : quatre condensateurs de 10 µF entre U17 et le DRV632 (U18) collent avec la
sortie ligne différentielle OUT1, mais les pistes passent par les couches internes.

### 9.1 Diagnostic en cours

Procédure envoyée à Maxime (`/mnt/project-files/cue-casque/diagnostic.md`) :

1. Avant `test-split`, ses mods avaient-ils disparu (preuve que l'image a tourné) ?
2. Sans flasher : HP max au minimum (registre `0x22` = `0x10`, casque muet). Si MAIN OUT se tait aussi, il sort de
   l'ampli casque et le cue split est impossible.
3. Sinon, `diag-volume_model-cycles_OS1.13.syx` (jamais dans le dépôt) : l'OS officiel avec, en place dans
   `0x400445fa..0x4004461b` (34 o), `0x1F` = `0x90` (sortie active, gain muet : la valeur de l'OS au volume 0) sur
   les crans de volume impairs, la valeur d'origine sur les pairs (`btst #0,d3`), et « HP max » → « HPdiag »
   (`0x40127011`) comme marque visible. MAIN OS `eb8089b0f485c0600346adcaae4380d356f94981e2bc4d596956d3c1c7053f3f`.
   Émulé : seules les écritures de `0x1F` diffèrent de l'OS d'origine. Si MAIN OUT R se coupe un cran sur deux, le
   split marche (avec `0x90` plutôt que `0x00`) ; sinon, il reste les sorties « jacks » ou « USB » (§6).
