# 81 — Aucune machine ajoutée au-dessus de 13 % du processeur

Demande de Maxime, le 26/10/2026 : « J'aimerai qu'aucune engine de modded cycles ne puisse dépasser 13% de charge
CPU ». Plan accepté le même jour : une mesure permanente (`tools/emu/test_budget.py`), MACRO allégée modèle par modèle
(M1), MODAL calculée à 24 kHz (R1) puis avec des lignes de cordes en 16 bits (R2) ; pas de MODAL limitée à 2 voix,
mais « Si 4 polyphonie sont impossible, tu peux reduire à 3 », et « N'hésite pas à modifier le code même si ça revient
à être un peu moins fidèle au rings. le plus important c la stabilité et l'agréabilité du son ».

Cette note couvre la mesure et MACRO (branche `claude/macro-48k`). MODAL suit sur sa propre branche (§8).
Générateurs `tools/gen_macro.py`, `tools/gen_macro_syntakt.py`, `tools/gen_acid_combos.py` ; sources
`tools/machines/macro/` (`macro.cc`, `macro_asm.S`, `braids_fast_digital.inc`, `braids_semantic.inc`) ; références
`tools/emu/braids_ref.cc` et `build/braids_cf/` (banc) ; preuves `tools/emu/test_macro.py`, `test_macro_syntakt.py`,
`test_acid_combos.py`, `test_budget.py`. Tous les tweaks qui portent MACRO sont régénérés (`25-macro`, `32-macro-tg`,
les combinaisons `syntakt-…-macro`, `…-acid`, et `31-syntakt-tg-…-modal` de l'OS).

## En bref

- **La mesure** : la charge d'une piste comme la page System de Model-TG l'affiche (sa moyenne), prise par le modèle
  du coût sur la machine (`tools/emu/hwcost.py`, [77](77-cout-sur-la-machine.md)), sur tout l'OS, son tenu (DECAY 110),
  une piste qui joue et cinq muettes. Pour chaque machine : ses réglages par défaut, les extrêmes des potards qui
  changent le calcul, une note aiguë, BITS au plus fort, un potard qui bouge à chaque bloc ; pour MODAL, 1, 2 et 4 voix
  qui sonnent toutes. Seuil : 13,0 %.
- **Avant** : 11 modèles de MACRO au-dessus de 13 % (HARMONICS 18,8 %, WAVE PARAPHONIC 17,3 %, SINE TRIANGLE 16,5 %,
  CYMBAL 16,4 %, TRIPLE SQUARE 15,7 %…), et MODAL de 17 à 41 %. ACID (7,5 %) et les moteurs du Syntakt (10,3 % au pire)
  passaient déjà ; les machines d'origine prennent de 6,8 à 8,6 %.
- **Après, MACRO** : les 47 modèles sous 13 %, de 6,5 % (CSAW) à **12,9 %** au pire (STRUCK BELL quand PITCH bouge
  à chaque bloc) `[FAIT en émulation]`. Le détail au §6.
- **Ce qui s'entend** : rien pour 24 modèles, qui donnent les mêmes échantillons qu'avant (les boucles réécrites le
  sont au bit près). Les 9 modèles que Braids calcule déjà à 48 kHz sont rendus à 48 kHz sans passer par 96 kHz, et
  SINE TRIANGLE rejoint les modèles allégés : même spectre à moins de 1 dB par tiers d'octave en médiane. Sur les
  notes très aiguës, les 14 modèles allégés restent à 48 kHz au lieu de repasser à 96 kHz : WAVE PARAPHONIC et
  WAVE MAP se replient un peu au-dessus de la note 104.
- **À tester sur la machine** : la charge de quelques modèles (HARMONICS, CYMBAL, STRUCK DRUM, FLUTED, MORPH) sur la
  page System, et l'oreille sur les modèles qui changent (§4).

## 1. La mesure : `tools/emu/test_budget.py` `[FAIT en émulation]`

Le modèle du coût de [77](77-cout-sur-la-machine.md) compte, pour la boucle des voix de l'OS émulée bloc par bloc, les
instructions, les attentes de l'EMAC, les lignes de code et de données absentes des caches (8 Ko, 4 voies) et les
écritures de lignes modifiées. Il retrouve les relevés de Maxime : MODAL vers 30 % sur quatre voix le 23/10/2026, 19 %
à l'allumage le 25/10/2026 (19,1 % au modèle).

`test_budget.py` en fait un contrôle : chaque cas joue une note, laisse passer l'attaque, puis fait la moyenne de la
piste sur des dizaines de blocs, et échoue au-dessus de `BUDGET = 13.0`. Le pire bloc est affiché, sans contrôle : la
page System montre la moyenne. Les cas par machine :

| Machine | Cas |
|---|---|
| MACRO, ×47 modèles | défaut ; TIMBRE et COLOR à 127, à 0, 127 et 0 ; note 110 ; BITS au plus fort (FUNC + PITCH à droite) ; PITCH qui bouge ; TIMBRE qui bouge |
| MODAL, ×4 SHAPE | défaut, brillant, sombre, COLOR qui bouge ; 1, 2 et 4 voix, cinq notes pour que toutes sonnent |
| ACID | défaut, potards à 127 |
| Moteurs du Syntakt | défaut, potards à 127, à 0 |
| Machines d'origine | défaut, pour comparaison, sans contrôle |

Les processus de mesure se partagent les cas (`--jobs`, 4 à 6 sur une machine de 11 cœurs) ; `--quick` ne garde que
les cas par défaut et les extrêmes.

## 2. MACRO : où partait le temps `[FAIT en émulation]`

Le détail par fonction (le banc `build/braids_cf/`, Braids compilé pour le ColdFire et comparé à Braids compilé pour
l'ordinateur, et le modèle du coût sur le firmware) :

- les boucles par échantillon de quelques modèles, que gcc compile mal pour le ColdFire (état relu et réécrit en
  mémoire à chaque échantillon, divisions, mises à l'échelle répétées) : CYMBAL, SNARE, STRUCK BELL, STRUCK DRUM,
  HARMONICS, FLUTED, MORPH ;
- le filtre demi-bande 96 → 48 kHz : 1 660 instructions par bloc en C ;
- `ComputeDelay` (une division par rendu), calculé pour tous les modèles alors que seuls BOWED, BLOWN et FLUTED lisent
  `delay_` ;
- les 9 modèles qui ne calculent qu'un échantillon sur deux à 96 kHz (VOWEL FOF, HARMONICS, PLUCKED, BOWED, STRUCK BELL,
  STRUCK DRUM, SNARE, TWIN PEAKS NOISE, PARTICLE NOISE) : la moitié de leurs rendus et tout le filtre demi-bande
  servent à des échantillons recopiés ;
- les modèles allégés à 48 kHz repassaient à 96 kHz sur les notes aiguës ([55](55-macro-allegee-et-lofi.md) §1), et
  SINE TRIANGLE n'en était pas.

## 3. Les réécritures exactes `[FAIT en émulation]`

Même calcul entier que Braids, dans le même ordre là où il compte : les échantillons sont les mêmes au bit près
(`test_macro.py` contre Braids compilé pour l'ordinateur, et le banc sur 4 réglages et plusieurs notes).

| Où | Quoi | Gain |
|---|---|---|
| `macro_halfband` (`macro_asm.S`) | le demi-bande 96 → 48 kHz sur l'EMAC, en entiers, un produit par paire | 1 660 → 625 instructions par bloc ; vérifié sur 200 cas aléatoires (`build/braids_cf/hb_test.py`) |
| SNARE | `FastSvf` : les filtres d'état variable en registres le temps d'un rendu | |
| CYMBAL | `macro_cymbal` : toute la boucle en assembleur | 56 % du calcul d'avant |
| STRUCK BELL | `macro_sine_acc` (un partiel, amplitude fixe le temps d'un rendu) et les pas de phase gardés tant que la hauteur et COLOR ne bougent pas | |
| STRUCK DRUM | `macro_drum_render` : bruit, partiels et mélange en un appel ; deux partiels de même phase et même pas partagent un sinus ; la rampe d'amplitude en somme courante ; les pas gardés par hauteur | |
| HARMONICS, BELL, DRUM | `balance` sorti des boucles de décroissance | |
| tous | `ComputeDelay` seulement pour BOWED, BLOWN, FLUTED | une division par rendu |
| FLUTED | `macro_fluted` : la boucle par échantillon en assembleur | 9 874 → 6 693 instructions par bloc, 13,0 → 10,2 % |
| MORPH | `macro_morph` : la boucle par échantillon (mélange, passe-bas, saturation, mélange) en assembleur | 12,8 → 12,1 % |

Deux écritures du même calcul servent souvent : `Mix(a, b, f) = (a (65535 − f) + b f) >> 16` vaut aussi
`a + (((b − a) f − a) >> 16)` (`a << 16` n'a pas de bits bas), avec une multiplication de moins, tant que `(b − a) f`
tient sur 32 bits (FLUTED : des échantillons de 8 bits ; pas MORPH, en pleine échelle, qui garde les deux produits).
De même `lp = (−fc bv + (4096 − fc) lp) >> 12 = lp + ((−fc (bv + lp)) >> 12)`.

**Un raté, rattrapé** : le premier `ComputeDelay` réservé testait `shape_` entre `OSC_SHAPE_BOWED` et
`OSC_SHAPE_FLUTED`. Mais l'énumération `OSC_SHAPE_` de Braids n'est pas dans l'ordre de `fn_table_` (BOWED y est la
17ᵉ fonction, `OSC_SHAPE_BOWED` vaut 25) : les trois modèles qui lisent `delay_` ne le recalculaient plus. Le contrôle
au bit près de `test_macro.py` l'a trouvé (BOWED, BLOWN, FLUTED différents dès le 2ᵉ ou 3ᵉ bloc) ; le test compare
maintenant la fonction de rendu elle-même. Le banc a été passé sur les 47 modèles, 4 réglages chacun : tous identiques
à la référence, sauf WAVE LINE à TIMBRE et COLOR à 127, où Braids d'origine diffère déjà entre le compilateur de
l'ordinateur et celui du ColdFire (sans nos retouches, `bench_orig`) ; `test_macro.py` ne joue pas ce réglage.

## 4. Ce qui change le calcul (`SEMANTIC_EDITS`, `braids_semantic.inc`) `[FAIT en émulation]`

Ces retouches sont faites dans le firmware **et** dans la référence de `test_macro.py`, qui reste exacte au bit près
contre elles ; un contrôle à part compare leur spectre à Braids d'origine à 96 kHz.

**48 kHz natifs (`macro.cc`, `NATIVE`)** : les 9 modèles qui ne calculent qu'un échantillon sur deux sont rendus avec
un drapeau (`g_native48`) qui leur fait écrire chaque échantillon calculé une seule fois. La passerelle garde les
échantillons impairs et les passe par (1 14 1) / 16 (VOWEL FOF, PLUCKED, BOWED, STRUCK BELL, STRUCK DRUM) ou
(1 30 1) / 32 (SNARE, TWIN PEAKS NOISE, PARTICLE NOISE, dont le son est tenu entre deux calculs). Même spectre
qu'à 96 kHz puis demi-bande : **0,7 dB en médiane par tiers d'octave, 0,9 dB à 95 %, niveau à 0,4 dB**.

**HARMONICS (mode 3)** : un seul rendu par bloc (64 échantillons à l'échelle de 96 kHz, au lieu de deux ou trois
rendus de 24 ; son coût est surtout par rendu), puis comme les autres un échantillon sur deux et (1 14 1) / 16, et
autrement calculé :

- sin(kφ) et cos(kφ) par rotations sur l'EMAC (les produits Q31 de MODAL), sin φ et cos φ lus dans la table de
  Braids : moins de −69 dB d'écart à la table (une récurrence de Tchebychev a été écartée : −23 dB près de φ = 0 ou π) ;
- les harmoniques jusqu'à 9,75 kHz calculées à 24 kHz, remontées à 48 kHz par un demi-bande de 43 coefficients
  (Kaiser β 6,2 : ±0,006 dB jusqu'à 9,75 kHz, −63 dB dès 14,25 kHz) ; au-delà (une ou deux harmoniques, les notes
  aiguës), à 48 kHz par la table, retardées comme le filtre (20 échantillons) : la même coupure à 12 kHz que Braids ;
- les amplitudes lissées une fois par rendu, au rythme de Braids, avec son arrêt à moins de 256 de la cible (sans lui,
  les harmoniques très faibles remontaient) ;
- les gains (24 divisions) recalculés seulement quand TIMBRE ou COLOR bougent, la coupure quand la note bouge.

18,8 % → 11,7 % au pire ; spectre à 0,82 dB au plus de Braids.

**SINE TRIANGLE** rejoint les modèles allégés de [55](55-macro-allegee-et-lofi.md), avec l'atténuation de son repli
calculée sur la vraie note (`g_pitch_offset`) : 0,1 / 0,9 / 0,2 dB aux notes 36 / 60 / 84.

**Le plafond des oscillateurs** monte d'une octave en rendu allégé (la table des pas de Braids la couvre déjà) : les
14 modèles allégés restent à 48 kHz sur toutes les notes au lieu de repasser à 96 kHz (avant : dès la note 92 pour
les TRIPLE, 97 pour WAVE PARAPHONIC, 116 pour les autres). Les TRIPLE restent à 2,4 dB au plus de leur son à 96 kHz
entre les notes 96 et 120 ; WAVE PARAPHONIC et WAVE MAP se replient au-dessus de la note 104 (4 à 8 dB d'écart dans
les aigus). Les rendre à 96 kHz là-haut les ferait passer au-dessus de 13 %.

Les 14 modèles allégés ensemble : 1,1 dB en médiane, 2,4 dB à 95 %, niveau à 0,6 dB.

## 5. Écartés

- CYMBAL allégée à 48 kHz : le filtre de Chamberlin de Braids devient instable au-dessus d'environ un sixième de la
  fréquence d'échantillonnage.
- `-Os` pour STRUCK DRUM : plus lent (13,3 contre 13,0 %).
- Des boucles C en plusieurs passes, ou réordonnées : gcc en tire un code ColdFire plus mauvais.

## 6. Avant, après `[FAIT en émulation]`

`test_budget.py --engines macro,syntakt,acid --jobs 4` (393 mesures, `TOUT OK`), le pire cas de chaque modèle
(avant : la même mesure sur la version de la note 80) :

| Modèle | Avant | Après |
|---|---|---|
| HARMONICS | 18,8 % (BITS au plus fort) | 11,6 % (PITCH qui bouge) |
| WAVE PARAPHONIC | 17,3 % (note 110) | 11,3 % (BITS au plus fort) |
| SINE TRIANGLE | 16,5 % (note 110) | 11,1 % (note 110) |
| CYMBAL | 16,4 % (BITS au plus fort) | 11,5 % (BITS au plus fort) |
| TRIPLE SQUARE | 15,7 % (note 110) | 10,9 % (note 110) |
| STRUCK DRUM | 14,6 % (BITS au plus fort) | 12,6 % (PITCH qui bouge) |
| STRUCK BELL | 14,0 % (BITS au plus fort) | 12,9 % (PITCH qui bouge) |
| SNARE | 13,6 % (BITS au plus fort) | 11,2 % (PITCH qui bouge) |
| GRANULAR CLOUD | 13,5 % (BITS au plus fort) | 12,6 % (TIMBRE et COLOR à 127) |
| FLUTED | 13,4 % (BITS au plus fort) | 10,3 % (BITS au plus fort) |
| MORPH | 13,2 % (note 110) | 12,1 % (BITS au plus fort) |
| SQUARE SYNC | 13,0 % (note 110) | 12,4 % (note 110) |
| VOWEL FOF | 13,0 % (BITS au plus fort) | 12,0 % (TIMBRE et COLOR à 127) |
| DIGITAL FILTER LP | 12,3 % (BITS au plus fort) | 11,7 % (BITS au plus fort) |
| DIGITAL FILTER PK | 12,3 % (BITS au plus fort) | 11,8 % (BITS au plus fort) |
| SAW SWARM | 12,2 % (BITS au plus fort) | 11,9 % (BITS au plus fort) |
| KICK | 12,2 % (BITS au plus fort) | 10,3 % (BITS au plus fort) |
| TRIPLE SAW | 12,1 % (note 110) | 8,7 % (note 110) |
| DIGITAL FILTER BP | 12,0 % (BITS au plus fort) | 11,4 % (BITS au plus fort) |
| DIGITAL FILTER HP | 12,0 % (BITS au plus fort) | 11,4 % (BITS au plus fort) |
| les 27 autres | 6,1 à 11,8 % | 6,5 à 11,0 % |

ACID et les moteurs du Syntakt ne changent pas (ACID 7,5 %, le pire moteur SY SWARM 10,3 %).

## 7. Preuves `[FAIT en émulation]`

- `test_macro.py` : MACRO seule et avec Model-TG, identique échantillon par échantillon à Braids compilé pour
  l'ordinateur (ses sources et `SEMANTIC_EDITS`), les 47 modèles, potards qui bougent, verrous de modèle, RATE et BITS ;
  nouveaux cas : TRIPLE SAW aux notes 100 et 115, CSAW à la note 120, SINE TRIANGLE à la note 100, HARMONICS aux notes
  100 puis 118, HARMONICS avec la note et TIMBRE qui bougent, STRUCK DRUM puis STRUCK BELL ; et les deux contrôles de
  spectre (§4) : 90 contrôles, `TOUT OK`.
- `test_macro_syntakt.py` (92 contrôles), `test_acid_combos.py --macro yes` (125), `test_modal.py` (101) : MACRO avec
  les moteurs, ACID et MODAL, sur l'OS entier : `TOUT OK`.
- Le banc (`build/braids_cf/run.py`) : les 47 modèles, 4 réglages chacun, identiques à Braids compilé pour
  l'ordinateur (sauf WAVE LINE au maximum, §3) ; FLUTED et MORPH aussi sur 5 et 7 notes, 120 à 200 blocs.
- `test_budget.py` : §6.

## 8. MODAL : à suivre

À 24 kHz (R1), MODAL ne descend que de 25 à 36 % : 13 % au plus pour le modèle modal, mais 18 à 25 % pour les cordes.
Le travail continue sur la branche `claude/modal-24k`, dans cette note.

## 9. Reste à vérifier

- `[À FAIRE]` La charge sur la machine (page System de Model-TG) : HARMONICS, CYMBAL, STRUCK DRUM, STRUCK BELL,
  FLUTED, MORPH, SQUARE SYNC sur une note aiguë, chacun seul sur une piste, son tenu. Au modèle, la marge la plus
  mince est STRUCK BELL quand PITCH bouge (12,9 %) : la disposition du code en mémoire déplace ces chiffres de
  ±0,3 point d'une compilation à l'autre.
- `[À FAIRE]` L'oreille : VOWEL FOF, PLUCKED, BOWED, STRUCK BELL, STRUCK DRUM, SNARE, TWIN PEAKS NOISE, PARTICLE NOISE,
  HARMONICS, SINE TRIANGLE (doivent sonner comme avant) ; WAVE PARAPHONIC et WAVE MAP sur les notes très aiguës.
