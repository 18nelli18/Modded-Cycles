# 85 — La résonance ne fait plus baisser le volume (Model-TG, toutes les machines)

Demande du propriétaire (29/10/2026), après écoute sur sa machine : Filtre grand ouvert, Résonance montée, le niveau
baisse nettement. Ça touche **toutes les machines** (le Sampler, les machines d'origine, les moteurs du Syntakt, MACRO),
pas seulement RETROSYN : elles passent toutes par le même filtre en échelle de Model-TG. Retouche de sa source dans
`tools/gen_model_tg.py` (`RES_PATCHES`, ajoutées à `MC_PATCHES`, donc dans `30-model-tg.json` et `30-model-tg-st.json`),
preuve `tools/emu/test_model_tg_res.py`. Adresses : VA du bloc de Model-TG (commit `70b39dd`, binutils m68k-elf 2.47).

## En bref

- Le filtre de Model-TG est une échelle à 4 pôles avec contre-réaction `fb` (Q12, `k = fb/4096`, jusqu'à 15 000) :
  dans sa bande passante, son gain vaut `1/(1+k)`, soit **0,21 (-13,3 dB)** à la résonance maximale. Model-TG n'en
  compensait que la moitié, **à l'entrée** (table `filt_mkt`, jusqu'à 2,1x) : il restait **-5,5 dB** à Résonance 127,
  -4,8 dB à 64. Le commentaire de sa source l'explique : la compensation entière (4,4x) à l'entrée envoyait le pic de
  résonance dans les bornes. `[FAIT]`
- Maintenant : la compensation est **entière et à la sortie**, `y4 · (1 + fb/4096)` — l'inverse exact du gain en
  continu, donc **0,00 dB** dans la bande passante quelle que soit la résonance — et le pic de résonance (jusqu'à
  ~14x la bande passante) passe par **`mc_sat`, un écrêtage doux** quadratique au lieu de la borne dure. `[FAIT en émulation]`
- L'échelle elle-même tourne comme avec un makeup de 1 : ses bornes internes travaillent moins qu'avant (où l'entrée
  était multipliée par 2,1). La multiplication à l'entrée disparaît, celle de la sortie la remplace. `[FAIT]`
- **Aucun octet ajouté, aucun symbole de Model-TG déplacé** : chaque retouche garde sa taille, `mc_sat` prend la
  place de la table `filt_mkt` devenue inutile. La chaîne 31-* (moteurs du Syntakt) ne voit aucune différence. `[FAIT]`
- Résonance 0 : sortie identique échantillon par échantillon (contourné grand ouvert, boucles rapides sinon) et même
  coût. Résonance 127 : +2,6 % d'instructions dans `gflt_run`. `[FAIT en émulation]`
- `[À FAIRE]` écoute sur la machine (§6).

## 1. Le filtre de Model-TG `[FAIT]`

Deux copies du même calcul, retouchées de la même façon :

| Où | Adresse | Rôle |
|---|---|---|
| `sp_flt_go` (dans `sampler_pre`) | `0x401ac7cc`..`0x401ac848` | coefficients du Sampler par bloc : `filt_f` (`filt_coef[cadran]`), `filt_q` = `fb`, `filt_mk` = makeup |
| `ladder_run` | `0x401ad36a` (boucle `sv_flt` `0x401ad3c0`, sortie `sv_f4l` `0x401ad4ae`, fin `lr_st` `0x401ad4e2`) | l'échelle du Sampler, 32 paires d'un tampon 2x, `x = s >> 13` |
| `gflt_coef` | `0x401babf8` (makeup `0x401bac62`) | les mêmes coefficients pour les machines d'origine (Filtre / Résonance en +48 / +50 de `trackData`) |
| `gflt_run` | `0x401bac8a` (boucle `gr2_loop` `0x401bad62`, sortie `gr2_4l` `0x401bae50`, fin `gr2_st` `0x401bae82`) | l'échelle dans `amp_hook`, 32 échantillons, `x = s >> 14` |
| `filt_fbmax` | `0x401bbeb4` | `fb` maximal stable par cadran (≤ 15 000) |

`fb = r/2 - r/32` (r = Résonance brute, 0..32 512), plafonné par `filt_fbmax`. Chaque pôle fait `Y += f·(prev - Y)`,
de gain 1 en continu ; avec la contre-réaction `u = x - k·y4`, le gain en continu vaut donc exactement `1/(1+k)`.
Au pic de résonance (chaque pôle à -45°), le gain vaut `1/(4-k)` : à `k = 3,66`, 2,9x, soit 13,7x la bande passante.

Avant : `x · filt_mkt[fb >> 7]` à l'entrée (Q12, demi-compensation, 4 096 .. 8 598). Compenser entièrement à cet
endroit déborde 32 bits (`131 072 · 19 096 > 2^31`) et pousse l'entrée de l'échelle contre sa borne (±262 143).

## 2. La retouche `[FAIT]`

| Endroit | Avant | Après | Taille |
|---|---|---|---|
| `sp_flt_go`, `0x401ac830` | `filt_mk = filt_mkt[fb >> 7]` (14 o) | `filt_mk = 4096` + `tpf.l` + `tpf` (14 o) | = |
| `gflt_coef`, `0x401bac62` | `gflt_mk = filt_mkt[fb >> 7]` (12 o, `lea` relatif au PC) | `gflt_mk = 4096` + `tpf.l` (12 o) | = |
| `sv_flt` (entrée) | `mulsl %a0@ ; asrl` (makeup) | rien | -6 o |
| `sv_f4l` (sortie) | borne dure ±131 068 (28 o) | `o = y4 >> 12 ; o += (o · fb) >> 12`, puis si `|o| > 98 304` : `jsr mc_sat` (abs.l) | +4 o |
| après `bnew sv_flt` | — | `tpf` (une fois par appel, hors boucle) | +2 o |
| `gr2_loop` / `gr2_4l` / avant `gr2_st` | idem | idem, `bsr.w mc_sat` (proche, écrit explicitement) et `tpf.w` | = |
| `filt_mkt`, `0x401bbdb4` | table de 128 mots (256 o) | `mc_sat` (68 o, `0x401bbdb4`..`0x401bbdf8`) + 188 o de remplissage | = |

- `o · fb` ne déborde pas : `y4` est borné à ±2^29 (Q12), donc `|o| ≤ 131 072`, et `fb ≤ 15 000` :
  `131 072 · 15 000 = 1,97·10^9 < 2^31`. Pas de table : le makeup se calcule depuis `fb`, déjà dans `d1`.
- La boucle rapide (Résonance 0) reste choisie par `fb == 0 && mk == 4096` : `filt_mk` / `gflt_mk` valent toujours
  4 096, et `fb == 0` exactement à Résonance 0. Le contournement grand ouvert (`filt_f` / `gflt_f` = 0) ne change pas.
- `mc_sat(d6)` : identité jusqu'à ±98 304 (3/4 de la pleine échelle, -2,5 dB) ; au-delà
  `v - ((v - 98 304)/2)^2 / 32 768` = `v - (v - T)^2 / 131 072`, qui rejoint 131 072 à pente nulle en ±163 840 ;
  borné à ±131 068 (`<< 14` doit tenir dans 32 bits). Impair (le négatif passe par `negl` / `bsr.s` / `negl`),
  continu, pente entre 0 et 1, aucune marche. Garde tous les registres sauf `d6` (`d0` sur la pile). Le test
  `|o| > 98 304` est fait dans la boucle : sous le coude, aucun appel.
- Symboles : seules bougent les étiquettes locales internes aux deux boucles (`sv_f1h`..`sv_flt_ol`,
  `gr2_ih`..`gr2_ol`), toutes appelées de l'intérieur de leur boucle (vérifié par `grep` sur la source). Tous les
  autres symboles, `ST_SYMBOLS`, `PV_SYMBOLS` et `reserved_end` (`0x401bf8c0`) compris, sont aux mêmes adresses
  (comparaison `nm` des deux builds) ; blob 82 282 o, tweak 87 936 o ajoutés, comme avant.
- `FLT_SYMBOLS` (générateur) : les symboles du filtre ajoutés à `30-model-tg.json` pour la preuve, qui appelle
  directement `ladder_run`, `gflt_run` et `mc_sat`.

## 3. Choix

- **Compenser à la sortie plutôt qu'à l'entrée** : le gain de la bande passante revient à 1 exactement, sans
  débordement, et l'échelle ne voit plus un signal amplifié (moins de bornes internes atteintes qu'avant).
- **Écrêtage quadratique plutôt qu'une table tanh** : aucune table (68 o de code), un seul `mulsl`, et la même
  forme qu'un tanh dans le coude. Au-delà de 1,25x la pleine échelle il est plat, comme tout limiteur.
- **Coude à 3/4** : à Résonance faible, un signal à pleine échelle perd au plus 0,56 dB sur ses crêtes
  (`131 072 → 122 880`) ; sous -2,5 dB, rien ne change.
- Conséquence voulue : un son clair monte avec la résonance (le pic, vers la coupure, s'ajoute à la bande passante
  rendue à 1) — comme un filtre analogique compensé. METAL grand ouvert : +8,7 dB à Résonance 127 (+3,0 dB avant).

## 4. Preuve en émulation `[FAIT en émulation]`

`python3 tools/emu/test_model_tg_res.py --cycles firmware/model-cycles_OS1.13.syx` (≈ 9 min). Avant = `30-model-tg.json`
au commit `2594419` ; les deux images tournent dans le moteur de la boucle des voix (`mcengine`).

### 4.1 Machines d'origine, de bout en bout (boucle des voix, `gflt_coef` + `gflt_run`), Filtre grand ouvert

Niveau RMS à Résonance 64 / 127, par rapport à Résonance 0 (dB), note 48, Decay 120 :

| Machine | avant 64 | avant 127 | après 64 | après 127 |
|---|---|---|---|---|
| KICK | -4,78 | -5,43 | 0,00 | 0,00 |
| SNARE | -4,23 | -4,60 | +0,61 | +0,91 |
| METAL | -0,60 | +3,03 | +4,25 | +8,67 |
| PERC | -4,83 | -5,50 | +0,01 | +0,01 |
| TONE | -4,53 | -4,23 | +0,31 | +1,29 |
| CHORD | -4,84 | -5,51 | 0,00 | 0,00 |

Critère : jamais plus de 1 dB de baisse, et jamais moins qu'avant. Les hausses (SNARE, METAL, TONE) sont le pic de
résonance vers 16 kHz, là où ces machines ont de l'énergie.

### 4.2 Résonance 0

Les six machines : sortie identique avant / après, grand ouvert (contourné) et à Filtre 64 (boucle rapide).
`ladder_run` et `gflt_run` directement, Résonance 0, bruit à -6 dB : identiques.

### 4.3 Les deux échelles appelées directement, Filtre grand ouvert, sinus 200 Hz à -6 dB

| Échelle | avant 0 / 64 / 127 | après 0 / 64 / 127 |
|---|---|---|
| `ladder_run` (Sampler) | 0,00 / -4,85 / -5,51 dB | 0,00 / 0,00 / 0,00 dB |
| `gflt_run` (machines) | 0,00 / -4,85 / -5,51 dB | 0,00 / 0,00 / 0,00 dB |

### 4.4 `mc_sat` seul

De -8x à +8x la pleine échelle, pas de 61 : identité jusqu'à ±98 304, puis exactement la courbe du §2, croissant,
impair, borné à ±131 068, pente jamais au-dessus de 1 ; `d0` et la pile rendus intacts.

### 4.5 Pic de résonance : Résonance 127, dent de scie 120 Hz

RESULTS_PEAK

Critère : crête ≤ 131 068 (aucun débordement) et sortie périodique comme l'entrée (écart d'une période à la
suivante < 1 % du RMS) : **pas de grondement**. Saturé = part des échantillons au-delà de 3/4 de la pleine échelle.
À -1 dB et coupure basse, la sortie est franchement saturée : la bande passante est rendue à 1 et le pic monte
13,7x au-dessus — c'est le prix d'une compensation entière, arrondi par `mc_sat` au lieu d'une borne dure.
Avant, le pic restait plus bas parce que tout le signal était 5,5 dB trop bas.

### 4.6 Coût de `gflt_run` (instructions par bloc de 32)

| Résonance | avant | après |
|---|---|---|
| 0 | 1 588 | 1 588 |
| 127 | 2 512 | 2 577 (+2,6 %) |

`ladder_run` a la même retouche (une paire sur deux du tampon 2x).

### 4.7 Le reste

`tools/emu/test_model_tg.py` et `tools/emu/test_model_tg_syntakt.py` (version combinée) : RESULTS_REG.
`gen_model_tg.py --check`, `gen_flasher_tweaks.py --check`, `registry.py --check`, `check_overlaps.py`,
`ref_mainos.py --check`, `build.py --os` : ok. `gen_acid_combos.py --tg --check` du tweak 31 de l'OS dit « ne
correspond pas » **avec et sans cette retouche** (même résultat sur `30-model-tg-st.json` de `2594419`) : écart de
compilateur préexistant, sans rapport ; le tweak 31 ne lit de model-tg-st que ses symboles, inchangés.

## 5. Limites

- Le coude de `mc_sat` s'applique dès qu'il y a de la résonance : un son à pleine échelle perd au plus 0,56 dB sur
  ses crêtes à faible résonance.
- Les bornes internes de l'échelle (±2^29 par pôle, ±262 143 à l'entrée) restent dures, comme dans Model-TG ; elles
  travaillent moins qu'avant.
- Un son clair monte avec la résonance (§3) ; si c'est trop, baisser le volume de la piste.

## 6. À vérifier sur la machine `[À FAIRE]`

1. Filtre grand ouvert (MACHINES + SWEEP au maximum), Résonance (MACHINES + CONTOUR) de 0 à 127 sur KICK, CHORD et
   un Sampler : le niveau ne doit plus baisser.
2. Résonance 127, Filtre balayé lentement de bas en haut sur TONE, METAL et un sample fort : le pic doit chanter et
   saturer doucement, sans grondement, craquement ni bruit.
3. Résonance 0 : rien ne doit changer.
4. Page System : la charge avec six pistes résonantes ne doit pas monter de façon visible (+2,6 % sur le filtre).
