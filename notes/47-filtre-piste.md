# 47 — Un filtre par piste : passe-bas, OFF, passe-haut (`track-filter`)

Demande du serveur Discord (forum *feature-requests*, fil « High-pass filter per track / machine », 05/10/2026) : un
passe-haut par piste, puis un filtre bipolaire « DJ » : passe-bas d'un côté, rien au centre, passe-haut de l'autre.
Maxime (06/10/2026) : le développer, puis, une fois testé sur sa machine, retirer le filtre par piste de Model-TG, que
celui-ci remplace. Tweak `48-track-filter.json`, généré par `tools/gen_track_filter.py` depuis
`tools/machines/track_filter/` (`track_filter.S` le filtre, `tf_ui.S` les potards, l'affichage et la sauvegarde,
`track_filter.ld`), preuve `tools/emu/test_track_filter.py`. Étude préalable (OS Cycles 1.13, Samples 1.13,
Syntakt 1.42, Model-TG v1.1.0) dans `/mnt/project-files/filtre-piste/faisabilite.md`. Adresses : VA de l'OS 1.13.

**Crédit.** Idée créditée à **Kevin Shallvari** ([Kevin-Shallvari](https://github.com/Kevin-Shallvari)), à la
demande de Maxime (11/10/2026) : sa machine Acid (PR #65 de ce dépôt, 08/10/2026, non fusionnée) a le même filtre
DJ sur un seul potard (passe-bas d'un côté, rien au centre, passe-haut de l'autre), avec une résonance qui peut
auto-osciller. La demande sur Discord vient de Tom (05/10/2026), Simone y cite le filtre du Model:Samples. Aucun code
de Kevin n'est repris ici : le filtre de ce mod est écrit pour ce projet (§5).

## En bref

Testé sur la machine (11/10/2026) dans sa deuxième version (§10). **De nouveau expérimental** : résonance bien plus
forte en haut de course et enveloppe qui arrive en douceur près du centre, après l'essai de Maxime avec Model-TG
(§12).

- **MACHINES tenu + SWEEP = Filter Cutoff** : L64 … L1, **OFF**, H1 … H63. Passe-bas à gauche (5 Hz à 20 kHz),
  passe-haut à droite (5 Hz à 19 kHz), la loi du potard du Model:Samples. **+ CONTOUR = Filter Reso** (Q 0,5 à 1 000, sifflante en haut de course),
  **+ COLOR = Filter Env** (quantité d'une enveloppe, bipolaire), **+ SHAPE = Env Decay** (5 ms à 10 s). L'enveloppe
  repart à chaque note de la piste.
- Quatre **vrais paramètres de toutes les machines** (k 28 à 31, descripteurs 1 à 4 de l'OS, des emplacements
  « Error » inutilisés) : p-locks, destinations du LFO et de la vélocité, CC 74 et 71, NRPN 1:20 et 1:21, valeurs par
  défaut d'un son neuf, sauvegarde avec le son et le pattern.
- Le filtre est un **SVF 2 pôles trapézoïdal** (12 dB/oct), appliqué **après Volume + Dist** et avant le panoramique,
  le niveau et les envois (l'ordre du Model:Samples) : l'audio USB 6 canaux reçoit les pistes filtrées.
- **Au centre, la piste n'est pas touchée, bit pour bit** (prouvé sur le vrai code, avec les autres mods).
- Corrige au passage la sauvegarde des **p-locks des paramètres k ≥ 23** dans le pattern : l'OS d'origine les rangeait
  sur LFO Speed, LFO Multiplier… ou les perdait (§4.3).
- Place : 3 029 o de code, tables et état dans **quinze masques de sprites 35×35** libérés (§6). Coût : §9.
- **Avec Model-TG** (étape 2, §11) : le filtre de piste de Model-TG est retiré, ce filtre prend sa place (versions
  `48-track-filter-tg*.json`), côté stéréo du Sampler compris. Expérimental avec Model-TG.

## 1. Sur la machine

| Geste | Paramètre (nom court) | Affichage | Défaut |
|---|---|---|---|
| MACHINES tenu + SWEEP | Filter Cutoff (FREQ) | `L64` … `L1`, `OFF`, `H1` … `H63` | OFF |
| MACHINES tenu + CONTOUR | Filter Reso (RESO) | 0 … 127 | 0 |
| MACHINES tenu + COLOR | Filter Env (FENV) | −64 … OFF … +63 | OFF |
| MACHINES tenu + SHAPE | Env Decay (FDEC) | 0 … 127 | 64 |

C'est le geste de l'Attack de Model-TG, et la place des potards CUTOFF / RESONANCE du Model:Samples. MACHINES appuyé
seul ouvre toujours le menu des machines. Un pas de potard (256 en 8.8) vaut environ 2 demi-tons de fréquence (64 pas
de chaque côté). Entre OFF et le pas voisin (L1, H1), la sortie passe de l'entrée au filtre (w = |C − centre| / 256,
pour les valeurs fines du lissage des paramètres, d'un NRPN ou d'un LFO ; elles s'affichent `L0` / `H0`) : le
passage par le centre ne claque pas.

## 2. Où brancher le filtre `[FAIT]`

Fonction audio par bloc `0x4005979e` (32 trames à 48 kHz, 1 500 blocs par seconde ; pistes mono Q31 en SRAM,
`0x80001858 + 128 t`) :

| Site | Appel | Rôle |
|---|---|---|
| `0x400597a8` | `0x40058474` | lisse les mots des paramètres (les 33 mots k 0..32 des 6 pistes) ; rend a2 = `0x8000100c` |
| `0x4005981e` | `0x400a7d4a(0x80001858, a2, déclenchées, relâchées)` | boucle des 6 voix ; a3 = contexte : +16 pistes déclenchées dans le bloc, +20 relâchées |
| `0x4005982a` | `0x40056d9c` | gain de vélocité |
| **`0x40059852`** | **`0x40056f58(0x80001858, a2)`** | **Volume + Dist** (k 19), en place |
| `0x4005985c` | `0x40056ea8` | comptabilité du bloc ; accumule dans l'EMAC sans le vider avant |
| `0x40059872` | `0x400567ba` | mixeur : niveau, panoramique, envois delay/reverb |

L'accroche est **H3** : `jsr 0x40056f58` → `jsr tf_post`, qui appelle Volume + Dist avec les deux mêmes arguments puis
filtre les 6 pistes. Aucun tweak n'écrit ce site ; il voit les 6 pistes dans toutes les configurations (moteurs du
Syntakt, audio USB). Contrat : garder d2-d7/a2-a6, rendre MACSR (0x20 à cet endroit) et laisser **acc0-acc3 à
zéro** (`0x40056ea8` accumule ensuite). `tf_post` passe MACSR à 0xa0 (fractionnaire, saturé) pour le filtre.

Les mots lissés d'une piste sont à `a2 + 14 + 66 t + 2 k` : les potards tournés glissent déjà (lissage de l'OS), et
un p-lock, un LFO ou la vélocité y arrivent comme pour les autres paramètres.

## 3. Les paramètres `[FAIT]`

### 3.1 Descripteurs

Table `0x4010dce0`, 0x38 o par entrée (notes/14 §2.1). Les entrées 1 à 4 sont des « Error » du groupe −1, que le
constructeur des tables saute ; leurs objets d'interface sont verrouillables d'origine (+0 = 0). Réécrites :

| Desc. | k | Groupe | Défaut | CC | NRPN | Tri | Nom long / court |
|---|---|---|---|---|---|---|---|
| 1 | 28 | 7 (toutes les machines) | 16 384 (OFF) | 74 | 1:20 | 72 | Filter Cutoff / FREQ |
| 2 | 29 | 7 | 0 | 71 | 1:21 | 73 | Filter Reso / RESO |
| 3 | 30 | 7 | 16 384 | — | — | 74 | Filter Env / FENV |
| 4 | 31 | 7 | 16 384 | — | — | 75 | Env Decay / FDEC |

Plage 0..32 512 (0..127), drapeaux 0x600 (destinations du LFO et de la vélocité), groupe affiché « Amp »
(`0x40129882`). CC 74 / 71 et NRPN 1:20 / 1:21 : ceux du filtre du Model:Samples, libres sur le Cycles.

### 3.2 Le geste : MACHINES tenu

Le slot 124 de la vtable de `ParameterPageView` (`0x401005a8`, d'origine `0x4001e814`) rend le descripteur sous un
potard ; les trois appels de l'OS passent par lui (potard tourné `0x4001f6ee`, TRACK + potard `0x4001d716`, popup au
changement de piste `0x4001f090`). `tf_knob` appelle la recherche d'origine, puis, si le potard est COLOR, SHAPE,
SWEEP ou CONTOUR (4..7) et que MACHINES (touche 5, `0x4007faf4`) est tenu, rend 3, 4, 1 ou 2.

### 3.3 Affichage

Objets d'interface `0x40a71754 + 100 i` : formateur à +0x20 (appelé avec +0x14, la valeur et le tampon, par
`0x4000a70e`), dessin spécial à +0x2c (les « Error » dessinent une image à la place du texte). `tf_knob` (via
`tf_objs`) installe à chaque appel : `tf_fmt_cut` (`L`/`H` + |v − 0x4000| >> 8 par `sprintf "%s%d"`, `OFF` au
centre), `0x400456c8` (entier), `0x40045bd6` (`OFF` au centre, ±n) et `0x400456c8` ; et efface +0x2c.

L'écran ne montre que **trois caractères** de la valeur, comme ceux des formateurs de l'OS (Pan : `L64`, `CEN`,
`R63` ; défaut : `ERR`). La première version écrivait `LP64` : sur la machine, `LP10` à `LP64` se lisaient `LP1` à
`LP6` (essai de Maxime, 10/10/2026, §10.1). Les tampons passés au formateur (16 o à `0x4001e4d0`, 12 o à
`0x4001d890`) contenaient bien les 5 octets : c'est l'affichage qui coupe, pas un débordement.

### 3.4 Tables construites au démarrage, son neuf

`0x4005a274`, appelé une fois depuis `0x4004486c`, construit depuis les descripteurs : k → descripteur par machine
(`0x4005a692`), CC (`0x4005a8ce`), NRPN (`0x4005a92e`), liste des destinations du LFO (drapeaux 0x600, triée sur la clé).
Les moteurs du Syntakt (notes/28) remplacent l'opérande de `lea 0x4010dce0,a4` (`0x4005a2de`) par une copie de la
table dans leur charge utile, faite sur la table d'origine : `tf_boot` (accroché à `0x4004486c`) y recopie nos quatre
entrées quand l'opérande ne pointe plus sur `0x4010dce0`, puis saute au constructeur.

Un son initialisé (`0x400618f2` → `0x40061866` : nouveau projet, son effacé, changement de machine) prend pour chaque
k le défaut de son descripteur : Filter Cutoff au centre. Sans descripteur, le mot serait 0, un passe-bas fermé à
5 Hz : c'est pour cela que les quatre paramètres passent par des descripteurs, et que la sauvegarde range Cutoff
en XOR 0x4000 (§4.1).

## 4. Sauvegarde `[FAIT]`

### 4.1 Le son

Enregistrement de 100 o (`0x4005afa0` version 2, `0x4005b054` version 1, chargement `0x4005aecc`). La sauvegarde
efface +28..+91 (32 emplacements de 16 bits) puis ne range que k 0..22 par la table `0x4010ee4c` ; le chargement
efface k 0..32 puis relit les emplacements 0..23 par `0x4010eea8` (l'emplacement 18 va sur k 0, inutilisé). Les
trois fonctions commencent par `lea -12(sp),sp ; movem.l a2-a4,(sp)` : l'accroche (`jmp`, 6 o) refait ces deux
instructions, empile une copie des arguments et sa suite comme adresse de retour, et saute 8 o plus loin.

| Emplacement | Octets | Contenu |
|---|---|---|
| 30 | +88 | Filter Cutoff XOR 0x4000 : un son d'avant le mod (zéro) se charge **OFF** |
| 31 | +90 | Filter Reso |
| 18 | +64 / +65 | Filter Env / Env Decay, entiers 0..127 XOR 64 (zéro = 64) ; le chargement remet k 0 à zéro |
| 27 | +82 / +83 | destination du LFO / de la vélocité quand c'est l'un des nôtres (28..31), sinon 0 |

Les emplacements 24..29 restent libres (Model-TG s'y range : §11). Cutoff et Reso gardent la valeur fine (NRPN),
Env et Decay l'entier du potard (ils n'ont ni CC ni NRPN).

### 4.2 Destinations du LFO et de la vélocité

Le LFO (octet haut de k 4, +28 du son) et la vélocité (long +88) passent par les mêmes tables k → emplacement, lues
**sans borne** : pour k ≥ 23 l'OS d'origine range un index pris au-delà de la table. Le chargement relit ce qu'il
peut ; notre suite rétablit la destination quand +82 / +83 porte 28..31.

### 4.3 P-locks du pattern : un défaut de l'OS d'origine

Fichier des p-locks : jusqu'à 80 enregistrements de 130 o `[index, piste, 64 mots]`. La sauvegarde complète
`0x4005b95c` et la mise à jour d'un p-lock `0x4005ba90` lisent l'index dans la table `0x4010ee4c` (opérandes
`0x4005b998` et `0x4005baca`), **sans borne** : k 23 → index 0, k 24 → 1 (LFO Speed), k 25 → 2 (LFO Multiplier)…
Le chargement `0x4005b766` repasse l'index par `0x4005aa1a` (index ≤ 23, sinon 0) et refuse les index > 32. Prouvé
en émulation sur l'OS d'origine : un p-lock de k ≥ 23 revient sur LFO Speed, ailleurs, ou se perd, et la mise à jour
d'un tel p-lock **écrase les p-locks de LFO Speed** de la piste. Le filtre de Model-TG (k 24) en souffre aujourd'hui.

Correction : les deux opérandes pointent sur `tf_ptab` (33 entrées : k 0..22 comme l'OS ; 23..31 → 24..32, des index
que l'OS n'écrit jamais ; 32 → 0) et `0x4005aa34` (pistes 0..5) saute à `tf_conv`, qui rend k = index − 1 pour
24..32. Le format du fichier ne change pas ; relu par l'OS d'origine, un tel enregistrement tombe sur k 0, inutilisé.

### 4.4 Le récepteur des changements

`0x4001461c` (slot 17 de la vtable de `Sound`) recopie chaque changement dans une copie rangée par emplacements, avec
`0x4005aa54` (k ≤ 22, sinon emplacement 0) : pour k ≥ 23 il écrit l'emplacement 0, sans effet (k 0). La persistance
de nos paramètres repose donc sur la sauvegarde complète (kit, réserve de sons, copier-coller), comme l'Attack de
Model-TG, qui reste avec le projet. `[HYP]` à confirmer sur la machine (§10).

## 5. Le filtre

### 5.1 Lois

- Fréquence : index i = C pour le passe-bas (C < 0x4000), i = C − 0x4000 pour le passe-haut ;
  fc = 5 Hz × 4 400^(i / 16 384), plafonnée à 20 kHz (L1 : 19,3 kHz ; H63 : 19,3 kHz). Celle du Model:Samples.
- Résonance (troisième version, §12) : Q = 0,5 × 2 000^((R′ / 32 512)^1,5), de 0,5 à 1 000, avec R′ = R ×
  réduction(i). Réduction : rien sous 10 Hz (pas de bosse subsonique, un défaut du Model:Samples), tout à 30 Hz,
  moins vers 20 kHz (1 − (fc / 24 000)^2,5), et bornée pour qu'un coup ne sonne pas plus de 2 s (60 dB en
  ln(1 000) Q / (π fc)) : Q au plus 0,9 fc, soit 37 à 100 Hz, 155 à 300 Hz, 1 000 au-dessus de 1,1 kHz. À 1 kHz :
  Q 1,3 à 32, 7 à 64, 67 à 96, 240 à 112, 870 à 127 ; un coup y sonne 16 ms à 64, 0,15 s à 96, 0,5 s à 112, 1,9 s à
  127. La première version suivait le Model:Samples (Q 0,501 × (22,36 / 0,501)^(R′ / 32 512)), la deuxième allait de
  0,5 à 50 (0,5 × 100^(R′ / 32 512)) : trop discrètes à l'essai (§10.1, §12).
- Enveloppe : e = 1 à la note (bit t de a3+16), puis e × exp(−1 / (1 500 τ)) par bloc, τ = 5 ms × 2 000^(D / 32 512) ;
  arrêtée sous 2⁻¹⁵. Décalage d'index = (A − 0x4000) × e × f², ajouté à i et borné au côté choisi (0..0x3fff) : la
  quantité monte ou baisse la fréquence, sans changer de côté. f = |C − 0x4000| / 0x800, borné à 1 : l'enveloppe
  arrive sur les 8 premiers pas de chaque côté (1,6 % à H1, 6 % à H2, 25 % à H4, entière à L8 / H8), pour qu'en
  quittant OFF avec une enveloppe réglée le filtre ne saute pas d'un coup (§12).

Quatre tables de 65 points (Q31) calculées par le générateur et interpolées linéairement : G = tan(π fc / 48 000) / 4
(i = 256 j), réduction de la résonance (i = 256 j), K = 1 / (2Q) (R′ = 512 j), décroissance par bloc (D = 512 j).

### 5.2 Le SVF en espace d'état

SVF trapézoïdal (Zavalishin) écrit pour que tout se fasse dans les accumulateurs de l'EMAC :

```
ic1' = b1 ic1 + b2 (x − ic2)          b1 = 2 a1 − 1, b2 = 2 a2
ic2' = c2 ic2 + b2 ic1 + 2 a3 x        c2 = 1 − 2 a3
y    = gx x + hl (ic2 + ic2') + hb (ic1 + ic1')
a1 = 1 / (1 + g (g + k)), a2 = g a1, a3 = g a2, g = tan(π fc / fs), k = 1 / Q
LP : gx = 1 − w, hl = w / 2, hb = 0          HP = x − k BP − LP : gx = 1, hl = −w / 2, hb = −w k / 2
```

18 instructions par trame (11 `mac`/`msac`, 3 `movclr`). Les coefficients sont recalculés quand (C, R, décalage de
l'enveloppe) change, une fois par bloc au plus : 1 / (1 + g (g + k)) par normalisation et trois pas de Newton. Au
premier bloc filtré, le passe-bas part du niveau de l'entrée (pas de clic), le passe-haut du repos ; un bloc nul avec
un état retombé (< 2⁻¹⁹) ne coûte presque rien. Saturation par l'EMAC (MACSR 0xa0) : à Q 870 une sinusoïde à fc
monterait de 59 dB, elle sature sans repli du signe (le défaut du Model:Samples). Les états (Q31) saturent aussi : sur un son fort à
forte résonance, le filtre écrête (il distord) au lieu de suivre le modèle linéaire, puis retombe au silence à la
vitesse de sa loi, sans oscillation entretenue (§8).

Au centre exact (C = 0x4000), la piste reste telle quelle et l'état est oublié ; l'enveloppe continue de tourner.

## 6. Place : quinze masques 35×35 `[FAIT]`

Dix-neuf sprites 35×35 ont des masques identiques de 280 o (35 colonnes opaques, `ff ff ff ff e0 00 00 00` par ligne).
On garde celui de `0x4014a660` ; `tools/sprites.py` les déclare (`SHARED_35`) et chaque masque utilisé est redirigé
(constante 32 bits du constructeur réécrite). Une section par masque, appels absolus de l'une à l'autre :

| Section | Masque | Octets | Contenu |
|---|---|---|---|
| `.tf_post` | `0x4014ab5c` | 152 | accroche H3, boucle des 6 pistes |
| `.tf_track` | `0x4014b85c` | 178 | enveloppe, son arrivée près du centre, clé des coefficients |
| `.tf_kern` | `0x4014d74c` | 164 | départ, repos, boucle des 32 trames |
| `.tf_coef1` | `0x401542f8` | 162 | index, G, résonance, K ; `tf_interp` |
| `.tf_coef2` | `0x401548b4` | 206 | réciproque, b1 b2 c2 a3, gx hl hb |
| `.tf_gtab` … `.tf_dtab` | `0x4015b8f8`, `0x4015f50c`, `0x401601fc`, `0x40160864` | 4 × 260 | tables |
| `.tf_kst` | `0x40160b6c` | 216 | état et coefficients, 6 × 36 o |
| `.tf_cst` | `0x40160e6c` | 256 | commande, 6 × 20 o, `tf_trig`, `tf_ptab` |
| `.tf_knob` | `0x401625bc` | 136 | `tf_knob`, `tf_objs` |
| `.tf_fmt` | `0x40163fb8` | 147 | `tf_fmt_cut`, chaînes |
| `.tf_save` | `0x4016616c` | 164 | `tf_save1/2`, `tf_save_post` |
| `.tf_load` | `0x40166760` | 208 | `tf_load`, `tf_conv`, `tf_boot` |

Encore libres : `0x40167c50`, `0x401696a0`, `0x401699a8`, `0x4016aa28`. L'état (`.data`) est écrit dans l'image avec
ses valeurs de départ : rien n'efface ces zones au démarrage.

## 7. Le tweak

Écritures (toutes avec leurs octets d'origine) : six accroches (`0x40059852` jsr tf_post, `0x4004486c` jsr tf_boot,
`0x4005aecc` / `0x4005afa0` / `0x4005b054` jmp, `0x4005aa34` jmp tf_conv), trois pointeurs (`0x401005a8`,
`0x4005b998`, `0x4005baca`), les descripteurs 1 à 4 (224 o à `0x4010dd18`), quinze redirections de sprites et le code.
40 écritures en tout.

`conflicts` : `model-tg`, `model-tg-st` (mêmes accroches de sauvegarde `0x4005aecc`, `0x4005afa0`, `0x4005b054`, même
geste ; les `syntakt-tg-*` demandent `model-tg-st`). Recouvrement vérifié octet par octet avec tous les tweaks du
dépôt et ceux des branches en cours (sample-preview, multiline-browser, chord-keys, level-pan-values,
trigless-dim) : aucun autre. Les masques 35×35 ne sont utilisés par aucun autre tweak.

## 8. Preuve en émulation

`tools/emu/test_track_filter.py`, sur le MAIN OS officiel, seul et avec
`--with 6ch-usbup,syntakt-sd-cp-toy-bits-swarm,arp,trig-hold,tempo-max,boot-anim,latching-mute,trig-preview,browser-scroll`
(`--syntakt Syntakt_OS1.42.syx`). Le son : la vraie boucle des voix puis le vrai site H3 (`0x4005984a..0x40059858`).

Chaque essai compare l'image avec le filtre à l'OS d'origine, sur le même motif (6 pistes, KICK SNARE METAL PERC
TONE CHORD, trois séries de notes aux blocs 1, 100 et 180) :

| Essai | Résultat |
|---|---|
| Centre (Filter Cutoff OFF), Volume + Dist 64 et 108, enveloppe et résonance réglées | les 6 pistes identiques bit pour bit à l'OS d'origine sur 240 blocs |
| Contrat de l'appel, à chaque bloc | d2-d7/a2-a6 gardés, `0x80001858` et a2 laissés sur la pile comme l'appel d'origine, MACSR rendu à 0x20, accumulateurs à zéro, aucun accès hors de la mémoire émulée |
| Six réglages fixes (LP 332 Hz, HP 332 Hz, LP près de 20 kHz, HP 41 Hz enveloppe −32, LP 116 Hz résonance 112 enveloppe +63, HP 5 Hz) | sortie comparée à un modèle flottant (SVF en double, mêmes lois) : écart max −111 à −167 dB sous la crête ; KICK et SNARE nettement changés |
| Balayage à chaque bloc, de LP à HP en passant par le centre | écart au modèle −110 à −120 dB sous la crête |
| Enveloppe, Decay 0 à 127 | relancée à chaque note (bit t de a3+16), τ de 5 ms à 10 s, écart à la loi < 10⁻⁷, décalage = quantité × enveloppe exactement |
| Résonance au maximum (Q 800 et 953 depuis le §12) : signal plein échelle (carré, sinus à fc, bruit, impulsions, balayage, échelon) après Volume + Dist 108, puis silence ; LP 947 Hz et HP 2,7 kHz | contrat tenu, sortie saturée à 1 FS sans repli (LP : aucun saut de plus de 1,5 FS d'une trame à l'autre) ; après le signal, décroissance régulière à la vitesse de la loi (3,23 et 7,60 dB par 100 ms, loi 3,23 et 7,74, à 3 % près) jusqu'à zéro exactement, en 4,4 et 1,8 s au plus |
| Lois | 170 réglages, 5 Hz à 20 kHz des deux côtés, Q 0,5 à 1 000 : fréquence à 0,01 cent près, Q à 0,39 % près (tirés des coefficients calculés par le code) |
| Enveloppe près du centre (§12) | H1, H2, H4, H8, L2, L6, Filter Env au maximum, 40 blocs : décalage = quantité × enveloppe × (\|d\| / 0x800)², au pas d'index près |
| Potards | MACHINES tenu : SWEEP, CONTOUR, COLOR, SHAPE → paramètres 1 à 4 ; les 8 autres potards et tout sans MACHINES : la recherche d'origine, mêmes arguments |
| Affichage (vrai constructeur, vrai `sprintf`) | les 128 pas : `L64` … `L1`, `OFF` au centre, `H1` … `H63`, trois caractères au plus ; Reso et Decay 0..127 ; Env −64..OFF..+63 ; l'image « Error » n'est plus dessinée |
| Tables construites au démarrage | descripteurs 1 à 4, k 28..31 sur les 6 machines, CC 74/71 sur les pistes 1 à 6, NRPN 1:20 et 1:21, rien d'autre ; un son neuf : Cutoff OFF, Reso 0, Env OFF, Decay 64, le reste comme sans le filtre |
| Sauvegarde du son, versions 2 et 1 | même enregistrement plus 7 octets (emplacements 18, 27, 30, 31) ; relu : valeurs, LFO → Filter Reso, vélocité → Filter Env ; un son d'avant le filtre se charge filtre OFF |
| P-locks du pattern | aller-retour complet et mise à jour d'un seul p-lock : tout revient (sur l'OS d'origine, 7 pistes de p-locks k ≥ 23 se perdaient ou changeaient de paramètre) ; p-locks d'origine : fichier identique octet pour octet |
| Avec les autres mods et le Syntakt | tous les essais ci-dessus refaits : mêmes résultats que seul (écarts au modèle identiques) ; descripteurs trouvés dans la table déplacée par les moteurs du Syntakt (`0x43034000`), k 28..31 et son initialisé sur les 11 machines |
| Avec MACRO (11/10/2026, après la fusion de main) | mêmes essais, mêmes résultats, avec `macro` (7 machines) puis `syntakt-sd-cp-toy-bits-swarm-macro` (12 machines), chacun avec `6ch-usbup`, `chord-keys`, `level-pan-values`, `trigless-dim`, `multiline-browser`, `midi-both` ou `midi-live-both`, `arp`, `trig-hold`, `tempo-max`, `boot-anim` et les trois de drumkilla ; k 28..31 et son initialisé sur toutes les machines |

## 9. Coût

Instructions exécutées dans le code du filtre, par bloc, 6 pistes ; part d'un bloc audio au modèle de la note 27
(1,54 cycle par instruction, 250 MHz, 166 667 cycles par bloc) :

| Cas | Instructions par bloc | Part d'un bloc |
|---|---|---|
| 6 pistes au centre (OFF) | 350 | 0,32 % |
| 1 piste filtrée, 5 au centre | 993 | 0,92 % |
| 6 pistes filtrées, réglages fixes | 4 208 | 3,9 % |
| 6 pistes filtrées, enveloppe en cours | 4 949 (max 5 114) | 4,7 % |
| 6 pistes filtrées, réglages changés à chaque bloc | 5 197 (max 5 220) | 4,8 % |
| 6 pistes filtrées, notes finies (Decay 10) | 3 983 | 3,7 % |

Une piste filtrée coûte 643 instructions de plus qu'au centre (0,6 % d'un bloc), jusqu'à 812 (0,75 %) quand les
coefficients sont recalculés à chaque bloc (enveloppe, LFO, potard qui tourne). Pour comparer, la charge lourde
mesurée en note 36 (moteurs Syntakt, Model-TG, régulateur) prend environ 44 % d'un bloc : six pistes filtrées et
modulées y ajoutent moins de 5 %, borne vérifiée par l'essai.

## 10. Sur la machine

### 10.1 Premier essai (10/10/2026)

Maxime, build « filtre seul » (MAIN OS `bf1f9fb3…`) : « c'est pas mal », mais :

- **Affichage** : en tournant à gauche, `LP8` puis de nouveau `LP1`, alors que le son continue de se fermer. Cause :
  l'écran ne montre que trois caractères (§3.3) ; `LP10` à `LP19` se lisaient `LP1`. Corrigé : `L64` … `OFF` …
  `H63`, comme Pan (`L64` … `R63`) ; la preuve vérifie les 128 pas.
- **Résonance** « qui ne s'entend pas beaucoup » : la loi du Model:Samples ne donne que +11 dB à mi-course. Passée
  à Q 0,5 à 50 (§5.1), environ 10 dB de plus par quart de tour. À réessayer : builds `-v2` envoyés le 11/10/2026
  (filtre seul : MAIN OS `f5db0133…` ; avec les autres mods : `f0d77915…`).

### 10.2 Second essai : testé sur la machine (11/10/2026)

Maxime, builds `-v2` : « ça marche nickel sur la machine ». Le mod passe de « expérimental » à « testé ».

### 10.3 Limites, et points à surveiller

- Le geste : MACHINES tenu + SWEEP / CONTOUR / COLOR / SHAPE, l'affichage (`L32`, `OFF`, `H20`…), le menu des
  machines qui s'ouvre toujours sur un appui seul.
- Le son : passe-bas, passe-haut, résonance (jusqu'à Q 1 000 depuis le §12 : un son fort pile sur fc sature le
  filtre, à écouter ; sinon une marge interne ou un Q plus bas), l'enveloppe à chaque note, le passage par le centre
  sans clic, un LFO qui balaie de LP à HP.
- La sauvegarde : son (kit), projet rechargé, réserve de sons, copier-coller d'un son, p-locks rechargés ; le
  récepteur des changements (§4.4) ne range pas k ≥ 23 : si un chemin de l'OS recharge un son depuis cette copie
  plutôt que par la sauvegarde complète, nos réglages y reviendraient à leur dernière sauvegarde. `[HYP]`
- Sur un `SoundConfigChangedInfo`, le même récepteur réécrit l'octet +94 de sa copie (destination de la vélocité)
  par la table bornée : pour nos destinations il y range un autre index. La sauvegarde complète le refait et range
  la nôtre en +83 ; `[HYP]` une vélocité vers FREQ survit donc aux mêmes chemins que nos réglages.
- Coefficients par bloc : une enveloppe ou un LFO très rapides à forte résonance avancent par marches de 0,67 ms.
- Un son relu sur l'OS d'origine (ou un autre firmware) perd son filtre, sans autre effet ; ses p-locks k ≥ 23 y
  tombent sur k 0, inutilisé.

## 11. Avec Model-TG (étape 2, 11/10/2026)

Maxime, après le second essai (11/10/2026) : « fusionne et attaque l'étape 2 ». Le filtre de piste de Model-TG
s'en va, celui-ci prend sa place et les deux se cochent ensemble.

### 11.1 Model-TG sans son filtre de piste `[FAIT]`

`RM_PATCHES` de `tools/gen_model_tg.py`, ajoutés à `MC_PATCHES` (les deux builds, `30-model-tg.json` et
`30-model-tg-st.json`) : des retouches **à taille constante** de sa source. Chaque symbole global garde son adresse
(comparé symbole par symbole aux builds d'avant ; seules deux étiquettes locales de `snd_load_post` bougent), donc
les tweaks posés sur Model-TG (`33-sample-preview*`, `32-macro-tg`, `31-syntakt-tg-*`) et leurs octets « old »
restent valables.

| Endroit | Avant | Après |
|---|---|---|
| `ap_done` (fin du paramètre Attack, par bloc) | `jsr gflt_coef` : coefficients du filtre de piste | trois `nop` |
| `ah_mid` (le filtre dans le rendu de la piste) | `movel %d3,%sp@-` … appel du filtre | `bras ah_nofl`, le filtre n'est plus appelé |
| `dh_pass` (descripteurs tenus avec MACHINES) | SWEEP → 0x0c (Filtre), CONTOUR → 0x0b (Résonance) | six `nop` : SWEEP et CONTOUR gardent la machine ; seul DECAY → 0x0d (Attack) |
| `snd_save_post` | Filtre et Résonance rangés avec le son | `bras ss_nofl` par-dessus, onze `nop` |
| `snd_load_post` | Filtre et Résonance relus | non relus ; une destination de LFO ou de vélocité autre qu'Attack (23) est remise à 0 |
| `build.py` (de Model-TG) | lignes 0x0c et 0x0b de la table des paramètres, `jmp` en `0x4005a6d0` (`sampler_com_gate`) | rien : les lignes « Error » et l'instruction d'origine restent |

Restent : Attack (k 23, DECAY avec MACHINES), le filtre du Sampler (ses propres paramètres de page) et le filtre des
effets master (page de retrig). Les mots k 24 et 25 des pistes ne servent plus (32 512 et 0). Les moteurs du Syntakt
avec Model-TG (`gen_syntakt_engines.py`, `tg_records`) et MACRO avec Model-TG (`gen_macro.py`, qui reprend
`tg_records`) ne posent plus que l'Attack dans leurs descripteurs tenus : les 31 `31-syntakt-tg-*`, les
31 `31-syntakt-tg-*-macro`, `32-macro-tg` et les firmwares de diagnostic `91`/`92` sont régénérés. Un projet fait avec
l'ancien filtre s'ouvre sans lui : la piste joue sans filtre.

`TF_SYMBOLS` : Model-TG exporte aussi `snd_save2_hook`, `snd_save1_hook`, `snd_load_hook`, `sx_on` et `sx_side`
(mêmes adresses dans les deux builds : `0x401b3c0e`, `0x401b3c28`, `0x401b3ca6`, `0x401b9b00`, `0x401b9f10`).

### 11.2 Le filtre par-dessus Model-TG `[FAIT]`

Deux tweaks de plus, aux écritures identiques, l'un sur `model-tg` (`48-track-filter-tg.json`), l'autre sur
`model-tg-st` (`48-track-filter-tg-st.json`, avec les moteurs du Syntakt ou MACRO) ; `48-track-filter.json` restait
octet pour octet le même, testé (jusqu'au §12), et déclare toujours `conflicts` avec Model-TG. Le flasher prend la bonne version
(clés « with » `model-tg`, `model-tg+syntakt`, `model-tg+macro`) ; la carte se dit expérimentale quand une version
avec Model-TG s'applique (`with_exp`).

- **Sauvegarde chaînée.** Model-TG accroche les trois mêmes sites que nous (`0x4005aecc` chargement,
  `0x4005afa0` et `0x4005b054` sauvegarde v2 et v1), par un `jmp` vers ses propres accroches. Notre version TG
  (`-DWITH_TG`, `tf_ui.S`) remplace ces `jmp` (les octets « old » sont ceux de Model-TG) : elle empile les arguments
  et l'adresse de notre suite, puis saute dans l'accroche de Model-TG, qui rejoue le prologue d'origine. Sa suite
  tourne d'abord (Attack), puis la nôtre (nos 7 octets, emplacements 30, 31, 18). L'emplacement 27 (+82/+83 :
  destinations du LFO et de la vélocité) est partagé : notre suite n'y écrit que si la destination est l'une des
  nôtres (28..31), sinon celle d'Attack reste.
- **Sampler stéréo.** Model-TG calcule le côté droit d'un sample stéréo à part (`sx_side`, 6 × 128 o, drapeau
  `sx_on` par piste) et le mélange après notre accroche. `tf_side` (220 o, dans le masque de réserve `0x40167c50`,
  le seizième) filtre ce côté avec les mêmes coefficients que la piste et son propre état (`tf_sst`, 16 o par piste :
  ic1, ic2, actif). À la première utilisation, l'état démarre comme celui de la piste ; quand le côté s'arrête ou que
  le filtre est à OFF, l'état est oublié.
- **Place** : 3 239 o dans seize masques 35×35 (le seizième, `0x40167c50`, était une réserve, §6) ; 42 écritures.
- **Slide trigs** : ceux de Model-TG font glisser les mots 1 à 25 (`SLD_ELIG`) ; nos paramètres (k 28..31) sautent à
  la valeur du slide trig, sans glisser.

### 11.3 Preuve

`tools/emu/test_track_filter.py --with model-tg,…` choisit la version TG, charge le bloc de Model-TG et fait tous
les essais du §8 sur la boucle des voix de Model-TG (gains du mixeur et Attack à 0 fournis par le banc), plus :

| Essai | Résultat |
|---|---|
| Côté stéréo du Sampler (`sx_on`, `sx_side`) | à OFF, les six côtés laissés tels quels ; filtrés (SNARE HP résonant, TONE LP enveloppe montante), bit pour bit comme une piste nourrie du même signal (mêmes coefficients, même départ, son propre état) ; pistes mono et blocs sans `sx_on` : côté intact ; les 6 pistes identiques avec ou sans côtés filtrés |
| Descripteurs tenus (vraie fonction `0x4004df5c`, MACHINES tenu) | lignes 0x0b et 0x0c à « Error » (-1), DECAY → Attack (0x0d) ; `0x4005a6d0` d'origine |
| Sauvegarde et chargement chaînés | LFO → Attack et vélocité → Filter Env, puis LFO → Filter Cutoff et vélocité → Attack : Attack (emplacement 24), nos réglages et les deux destinations (emplacement 27) reviennent, tout le reste comme Model-TG seul ; un son sauvé avec l'ancien filtre de Model-TG se charge sans lui (k 24 / 25 à zéro, destinations qui le visaient à zéro), notre filtre OFF |
| Model-TG lui-même | `test_model_tg.py`, `test_model_tg_syntakt.py` (descripteurs : seulement Attack), `test_sample_preview.py`, `test_macro_syntakt.py --only tg` |

Tous les essais du §8 donnent les mêmes résultats sur la boucle des voix de Model-TG : au centre, les 6 pistes
identiques bit pour bit à Model-TG sans le filtre (Volume + Dist 64 et 108) ; écarts au modèle flottant, lois,
résonance au maximum, potards, affichage, tables, sauvegarde, p-locks comme seul ; coût : 416 instructions par bloc
pour 6 pistes au centre, 1 063 pour une piste filtrée, 5 310 au pire (6 pistes modulées, 4,9 % d'un bloc). Faits avec
`model-tg,6ch-usbup,sample-preview,arp,trig-hold,tempo-max,boot-anim,level-pan-values,trigless-dim,multiline-browser`
(complet), puis avec `model-tg-st` et `syntakt-tg-sd-cp-toy-bits-swarm` (complet), `macro-tg` et
`syntakt-tg-sd-cp-toy-bits-swarm-macro` (`--quick`), chacun avec `sample-preview-st` et les mêmes autres mods. Chord
Keys et les trois tweaks de drumkilla n'en sont pas : le premier exclut Model-TG, les autres y sont déjà.

Model-TG lui-même, après le retrait : `test_model_tg.py` (machines d'origine identiques, note mutée), 
`test_model_tg_syntakt.py --engines sd,cp,toy,bits,swarm` (enregistrements tenus : seulement l'Attack),
`test_sample_preview.py --with 6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm,arp,trig-hold`,
`test_macro_syntakt.py --only tg` : TOUT OK. Les générateurs (`gen_model_tg`, `gen_syntakt_engines --tg` combinaison par
combinaison et `--meter`, `gen_macro`, `gen_macro_syntakt`, `gen_sample_preview`, `gen_track_filter`) sont à jour.

**À essayer sur la machine** (expérimental avec Model-TG) : le geste MACHINES tenu (DECAY = Attack, SWEEP / CONTOUR
/ COLOR / SHAPE = notre filtre), le filtre sur une piste Sampler en stéréo, la sauvegarde d'un son avec Attack et
filtre, un projet fait avec l'ancien filtre de Model-TG.

## 12. Troisième essai, avec Model-TG : progressivité et résonance (11/10/2026)

**Source : Maxime, dans le fil du projet (11/10/2026, 16:26 UTC), build de l'étape 2 avec Model-TG** : « il est très
peu progressif. Genre on observe une grosse différence de volume et de filtre entre le OFF et H2 par exemple. Et la
résonance est vraiment trop subtile, on peut à peine la faire siffler. »

### 12.1 OFF → H2 : mesuré en émulation `[FAIT]`

Sur la vraie boucle des voix (6 pistes, Volume + Dist 64 et 127, Reso 0 et 127, enveloppe au centre), écart de
niveau RMS avec OFF : H1 −0,12 dB, H2 −0,14 dB, H4 −0,23 dB au plus (le KICK, que H4 = 8,6 Hz entame à peine) ;
L1 +1,0 dB, L2 +2,8 dB sur METAL à Reso 127 (la bosse vers 19 kHz), moins de 0,3 dB ailleurs. Sans enveloppe, le
filtre ne saute donc pas entre OFF et H2 : H1 à H8 sont des passe-haut de 5,7 à 14 Hz.

`[HYP]` Ce qui saute : **l'enveloppe** (COLOR avec MACHINES). Son décalage s'ajoutait entier dès H1 : avec Filter
Env à +32, chaque note mettait le passe-haut à environ 330 Hz à H1 comme à H20, d'où un grand écart de volume et de
filtre entre OFF et H1/H2. Un LFO ou la vélocité vers FREQ feraient le même effet ; à demander à Maxime.

**Changement** : le décalage de l'enveloppe est multiplié par f² (f = |C − 0x4000| / 0x800, borné à 1) : elle arrive
sur les 8 premiers pas de chaque côté (1,6 % à H1, 6 % à H2, 25 % à H4, 56 % à H6, entière à L8 / H8), sans changer
la loi de la fréquence ni le fondu du premier pas. `tf_track` (178 o, masque `0x4014b85c`) fait quatre ou cinq
instructions de plus par piste filtrée et par bloc, onze sur les 8 premiers pas. Ce qui est perdu : une enveloppe entière depuis H1 à H7 (5,7 à 12 Hz, inaudibles) ou depuis L1 à L7
(19 à 9 kHz) ; une enveloppe qui part du tout en bas ou du tout en haut se règle à H8 ou L8.

### 12.2 La résonance `[FAIT]`

À Q 50 (deuxième version), la bosse fait +34 dB, mais un coup ne sonne que 0,1 s à 1 kHz (60 dB en
ln(1 000) Q / (π fc)) : sur des sons de batterie, la résonance « pique » sans siffler. Pour siffler, il faut que la
résonance sonne longtemps après le coup, donc un Q de plusieurs centaines. Nouvelle loi (§5.1) : Q = 0,5 ×
2 000^((R′ / 32 512)^1,5), de 0,5 à 1 000, la course en puissance 1,5 pour garder la première moitié douce, et une
borne qui limite la durée d'un coup à 2 s (Q ≤ 0,9 fc) pour que le grave ne bourdonne pas des dizaines de secondes.

| Reso | Q à 100 Hz | Q à 300 Hz | Q à 1 kHz | Q à 3 kHz | Q à 8 kHz | un coup sonne (1 kHz) |
|---|---|---|---|---|---|---|
| 32 | 0,9 | 1,0 | 1,3 | 1,3 | 1,2 | 3 ms |
| 64 | 2,3 | 3,9 | 7,2 | 7,4 | 5,9 | 16 ms |
| 96 | 8,5 | 22 | 67 | 71 | 46 | 0,15 s |
| 112 | 18 | 58 | 241 | 257 | 149 | 0,53 s |
| 127 | 37 | 155 | 868 | 939 | 487 | 1,9 s |

Pas d'auto-oscillation : le filtre est après le Volume + Dist de la piste, une résonance qui s'entretient sifflerait
sans fin entre les notes. Au maximum, un son fort pile sur fc ferait +59 dB : les états saturent (EMAC en mode saturé),
le filtre écrête comme un filtre analogique poussé, sans repli du signe, puis retombe au silence à la vitesse de sa
loi (§12.3). Ce que Kevin Shallvari fait dans sa machine Acid (PR #65 : échelle 4 pôles qui auto-oscille, bornée par
un coude) reste possible ici si cela ne siffle toujours pas assez, au prix d'un étage non linéaire.

### 12.3 Preuve `[FAIT]`

- `fade_tests` (nouveau) : H1, H2, H4, H8, L2, L6 avec Filter Env au maximum, sur 40 blocs : décalage = quantité ×
  enveloppe × f², au pas d'index près.
- `law_tests` : 170 réglages, Q 0,5 à 1 000 : fréquence à 0,01 cent près, Q à 0,39 % près.
- `ringdown_tests` : résonance au maximum sur un signal plein échelle, la fenêtre d'observation suit la loi (jusqu'à
  144 dB de décroissance) : LP 947 Hz (Q 800) et HP 2,7 kHz (Q 953), sortie saturée à 1 FS sans repli, puis
  décroissance à 3,23 et 7,60 dB par 100 ms (loi 3,23 et 7,74) jusqu'à zéro exactement, en 4,4 et 1,8 s au plus :
  pas d'oscillation entretenue, même à Q 950.
