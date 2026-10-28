# 81 — Aucune machine ajoutée au-dessus de 13 % du processeur

Demande de Maxime, le 26/10/2026 : « J'aimerai qu'aucune engine de modded cycles ne puisse dépasser 13% de charge
CPU ». Plan accepté le même jour : une mesure permanente (`tools/emu/test_budget.py`), MACRO allégée modèle par modèle
(M1), MODAL calculée à 24 kHz (R1) puis avec des lignes de cordes en 16 bits (R2) ; pas de MODAL limitée à 2 voix,
mais « Si 4 polyphonie sont impossible, tu peux reduire à 3 », et « N'hésite pas à modifier le code même si ça revient
à être un peu moins fidèle au rings. le plus important c la stabilité et l'agréabilité du son ».

Cette note couvre la mesure et MACRO (branche `claude/macro-48k`, §1 à §7), puis MODAL (branche `claude/modal-24k`,
§8 ; générateur `tools/gen_modal.py`, sources `tools/machines/modal/`, preuves `tools/emu/test_modal_dsp.py` et
`test_modal.py`).
Générateurs `tools/gen_macro.py`, `tools/gen_macro_syntakt.py`, `tools/gen_acid_combos.py` ; sources
`tools/machines/macro/` (`macro.cc`, `macro_asm.S`, `braids_fast_digital.inc`, `braids_semantic.inc`) ; références
`tools/emu/braids_ref.cc` et `build/braids_cf/` (banc) ; preuves `tools/emu/test_macro.py`, `test_macro_syntakt.py`,
`test_acid_combos.py`, `test_budget.py`. Tous les tweaks qui portent MACRO sont régénérés (`25-macro`, `32-macro-tg`,
les combinaisons `syntakt-…-macro`, `…-acid`, et `31-syntakt-tg-…-modal` de l'OS).

## En bref

- **La mesure** : la charge d'une piste comme la page System de Model-TG l'affiche (sa moyenne), prise par le modèle
  du coût sur la machine (`tools/emu/hwcost.py`, [77](77-cout-sur-la-machine.md)), sur tout l'OS, son tenu (DECAY 110),
  une piste qui joue et cinq muettes. Pour chaque machine : ses réglages par défaut, les extrêmes des potards qui
  changent le calcul, une note aiguë, BITS au plus fort, un potard qui bouge à chaque bloc ; pour MODAL, 1, 2 et 3 voix
  qui sonnent toutes, en régime établi. Seuil : 13,0 %.
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
- **Après, MODAL** : ses 60 cas sous 13 %, de 6,0 % à **12,8 %** au pire (l'accord sur 3 voix, COLOR qui bouge à chaque
  bloc) `[FAIT en émulation]` ; avant, 17 à 41 %. Calculée à 24 kHz, elle a d'abord été allégée sans rien changer
  au son (§8.2), puis selon le choix de Maxime, « le plus léger » (§8.3) : lecture linéaire des cordes, cordes
  sympathiques sans peigne, 3 voix au plus (2 pour la corde, SHAPE 2), 3 cordes sur une voix des modèles
  sympathiques et une par voix au-delà, potards repris un bloc sur 16 (32 en 3 voix) quand ils bougent sans trig ;
  les voix tour à tour (§8.6, après le retour de Maxime du 28/10).
- **À tester sur la machine** : la charge de quelques modèles de MACRO (HARMONICS, CYMBAL, STRUCK DRUM, FLUTED, MORPH)
  et de MODAL sur la page System, et l'oreille sur ce qui change (§4, §8.3).

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

## 8. MODAL `[FAIT en émulation]`

Avant (MODAL à 48 kHz, réglages par défaut, toutes les voix qui sonnent) :

| SHAPE | 1 voix | 2 voix | 4 voix |
|---|---|---|---|
| 0 modal | 17,8 % | 18,5 % | 18,7 % |
| 1 cordes sympathiques | 25,8 % | 27,8 % | 31,8 % |
| 2 corde | 17,4 % | 25,9 % | 41,3 % |
| 3 cordes en accord | 24,6 % | 27,9 % | 31,8 % |

### 8.1 Rings à 24 kHz (R1)

- Le cœur calcule Rings à 24 kHz, par blocs de 16 trames (`modal_cfg.h` : `MB`, `DLINE` 1 024, `SLINE` 512, `HBN`,
  partagés par le C et l'assembleur). Ce qui compte en échantillons est recalé pour garder ses durées en secondes et
  ses fréquences en hertz (la liste `SR24` de `test_modal_dsp.py`, appliquée à la référence) : coupures des filtres
  d'excitation et du pincement (tangente exacte, Q qui tend vers 0,707 près de la moitié de la fréquence
  d'échantillonnage), Q des modes × cos(πf), peigne et bruit du pincement, FIR et passe-bas d'amortissement des
  cordes, temps du limiteur.
- La passerelle remonte la sortie à 48 kHz par un demi-bande de 27 coefficients (Kaiser β 5 : à 0,01 dB près
  jusqu'à 8 kHz, −0,5 dB à 10 kHz, −54 dB dès 15 kHz ; 12 trames de retard), `modal_up` en assembleur, et descend le
  sample excitateur à 24 kHz par le même filtre.
- Limites, communes à Rings à 24 kHz et à MODAL : le résonateur sonne jusqu'à la note 126 ; les cordes suivent la
  hauteur jusqu'à 6 kHz environ et se taisent au-dessus de la note 118.
- Gain : 25 à 36 % seulement (le modèle modal à 13 %, les cordes de 18 à 26 %). Le reste du temps n'était pas dans les
  boucles par échantillon mais dans le code relu à chaque bloc : près de 500 lignes de 16 octets, plus que le cache
  d'instructions (8 Ko), et le code de liaison autour des noyaux.

### 8.2 Allègements sans changer le son

Mêmes octets que le C du cœur sur l'ordinateur (`test_modal.py`), et contre Rings la même mesure qu'avant
(`test_modal_dsp.py`), sauf la glissade des cordes sympathiques (dernier point), à 65 dB ou plus :

- la dispersion : son bruit, l'anti-continu et le chevalet courbe ne sont calculés que lorsqu'ils servent (`na`, `ac`) ;
  le générateur aléatoire, partagé avec le pincement, saute ses 16 tirages d'un coup (`M_LCG16A`, `M_LCG16C`) ;
- une corde au repos (rien ne bouge que sa position et, sans dispersion, son retard) prend un chemin court
  (`str_fast`, préparé par `str_plan`) : une boucle en assembleur pour la lecture, l'amortissement et l'écriture
  (`modal_str_run`), le peigne à part (`modal_str_comb`, avec l'ancien contenu de la place que l'échantillon suivant
  écrit quand il la lit), par morceaux du retard le plus court pour les cordes aiguës ; les lectures à retard modulé
  (`modal_str_read_nz` : le bruit de dispersion ; `modal_str_read_cb` : le chevalet courbe) suivies de
  `modal_str_dw` ;
- les modèles à cordes, quand rien n'a changé depuis le bloc précédent (`ps.same`, posé par la passerelle) :
  `modal_fast`, sans refaire ce qui ne bouge pas ;
- le limiteur de Rings et la différence de la passerelle en une passe en assembleur (`modal_lim`) ; son gain repart du
  1 / m précédent au relâchement, sans division ; le filtre de note reporte ses pas tant que la note ne bouge pas ;
- le code rare (initialisations, calculs par bloc quand un réglage change, le chemin complet des cordes) marqué
  froid et rangé à part (`MODAL_COLD`, `unlikely`, `-freorder-blocks-and-partition`) : le code relu à chaque bloc
  tient dans moins de lignes du cache ;
- `iabs` sans comportement indéfini à −2³¹ ; le facteur du retard de la dispersion borné à 1/2 (`disp_fm`), un plancher
  que le son n'atteint pas, sur lequel compte l'assembleur (aussi dans la référence) ;
- la glissade des cordes sympathiques ne refait que leur retard tant qu'elle reste à moins de 1/32 de la fréquence du
  dernier calcul complet (`str_delay`).

Écarté : `-Os` (le code passe de 38 à 29 Ko, mais les lignes relues à chaque bloc ne baissent presque pas) ; les lignes
des cordes en 16 bits (R2) : les défauts de données ne pèsent que 1 à 3 points, et la charge est passée sous 13 %
sans elles.

Après ces allègements, potards fixes : 12,1 % (modal, 3 voix), 15,5 % (cordes sympathiques, 2 voix), 14,1 % (corde,
3 voix), 15,4 % (accord, 2 voix) ; avec COLOR qui bouge à chaque bloc, 25 à 34 %.

### 8.3 Le choix de Maxime : le plus léger (27/10/2026)

Quatre fichiers d'écoute (`build/ecoute-choix`, hors dépôt) : le son du moment, la lecture linéaire des cordes, les
cordes sympathiques sans peigne, les deux. Maxime : « j'ai ecouter tout les ecoute choix et en vrai tout me va, avec un
leger penchant pour le sans peigne, mais dans tout les cas je veux surtout le plus légé ». D'où, définis dans la
référence (`LITE` de `test_modal_dsp.py`) et dans MODAL :

- la lecture des lignes des cordes linéaire (`Read` de stmlib) au lieu de l'interpolation d'Hermite de Rings, le
  produit arrondi pour que la boucle ne dérive pas ;
- les cordes sympathiques (excitées par la première) sans peigne : leur sortie `aux`, la seule où joue leur position,
  n'est pas calculée, ni les LFO de Rings qui la font bouger ; leur entrée × √2, car sans peigne elles perdent en
  moyenne la moitié de leur puissance ;
- les modèles sympathiques : 3 cordes sur une voix (la jouée et deux sympathiques), une seule par voix sur deux voix
  (Rings : 8 cordes ; éco : 4, 2, 1). Sur deux voix, ils n'ont donc plus de cordes sympathiques : chaque voix est une
  corde sans dispersion, à la note jouée (une octave plus bas pour le dernier accord, la 1re note de la table de Rings
  pour 2 cordes par voix) ; ils sonnent alors comme la corde (SHAPE 2) sans sa dispersion. Deux cordes par voix y
  coûtaient 13,9 % ;
- 3 voix au plus (FUNC + SHAPE : 1, 2, 3 ; `0x6000` donne 3 au lieu de 4), et 2 pour les modèles à cordes (la
  passerelle ; la fenêtre affiche toujours 3) ;
- les potards et la modulation de hauteur qui bougent sans trig sont repris un bloc sur 16 (10,7 ms) (`HOLD`, la
  passerelle) ; un trig les reprend tout de suite ;
- la chaîne d'excitation de la voix active s'arrête aussi quand elle est restée sous −108 dB pendant 8 blocs, jusqu'à
  la note suivante.

Ce que `LITE` change au son, contre Rings à 24 kHz sans lui (`lite_spectrum`, par tiers d'octave, bandes à moins de
50 dB du maximum) :

| Cas | Écart médian | Au plus | Niveau |
|---|---|---|---|
| cordes sympathiques, 1 voix | 2,8 dB | 7,6 dB | −1,0 dB |
| cordes sympathiques, 1 voix, brillantes | 2,2 dB | 8,0 dB | −0,2 dB |
| cordes en accord, 1 voix | 1,2 dB | 5,9 dB | −2,9 dB |
| corde, 1 voix, grave et brillante | 0,3 dB | 2,4 dB | −0,9 dB |
| corde, 2 voix, aiguë | 1,2 dB | 7,9 dB | −3,7 dB |

### 8.4 Charge après

`test_budget.py --engines modal` (60 cas, en régime établi : un trig, puis cinq notes une fois les lignes des cordes
écrites, la moyenne après la cinquième), `TOUT OK`, le pire cas de chaque modèle, au 27/10/2026 (pour la version
du 28/10, §8.6) :

| SHAPE | Pire cas | Réglage |
|---|---|---|
| 0 modal | 12,3 % | 2 ou 3 voix, COLOR qui bouge à chaque bloc |
| 1 cordes sympathiques | 11,4 % | 1 voix, notes aiguës |
| 2 corde | 12,8 % | 2 voix, COLOR, CONTOUR et SWEEP à 127 |
| 3 cordes en accord | 11,8 % | 1 voix, COLOR, CONTOUR et SWEEP à 0 |

Le moins cher : 6,0 % (modal, 1 voix, brillant ou aigu). Le pire bloc, quand un potard qui bouge est repris : 26 %
environ (le PEAK de la page System).

### 8.5 Preuves

- `test_modal_dsp.py` (27/10/2026) : 61 cas contre Rings à 24 kHz avec `LITE`, médiane 88,0 dB, le plus faible 34,4 dB (SHAPE 0,
  sample en entrée, les 4 potards qui bougent, l'écart connu de la note 74 §5.1) ; et le contrôle `LITE` ci-dessus :
  `TOUT OK`.
- `test_modal.py` : le code de MODAL dans l'OS, identique octet pour octet au même C compilé pour l'ordinateur ; cas
  ajoutés : cordes aiguës, corde à STRUCTURE 0 et 127, COLOR qui bouge à chaque bloc, 3 voix : 107 contrôles,
  `TOUT OK`.

### 8.6 Retour de Maxime : les voix (28/10/2026)

Maxime, sur la version du 27/10 : « niveau charge on est bon. Par contre je vois aucune diff entre le mode 3 voix et 2
voix. Dans tout les cas j'ai limpression que la premier note se coupe quand j'en joue une troisieme ».

Deux causes `[FAIT en émulation]` :

- sur les modèles à cordes, « 3 » jouait comme 2 (le plafond du §8.3) : la 3e note y reprend la voix de la 1re ;
- sur le modèle modal, les voix suivaient le motif de Rings pour une polyphonie impaire (`kPingPattern`,
  `rings/dsp/part.cc` : 1, 0, 2, 1, 0, 2, 1, 0, sur un compteur de 8) : au bout du motif, la voix 1 revient après
  deux notes seulement (…, 1, 0, 1, …) et coupe une note qui sonne. Sur les deux sorties de Rings, le motif répartit
  les voix ; sur la sortie unique de MODAL, il n'apporte rien.

Corrigé :

- les voix tour à tour (0, 1, 2), en 3 voix aussi : sur 3 voix, la 4e note coupe la 1re, jamais la 3e (aussi dans la
  référence, `LITE`) ;
- 3 vraies voix pour les modèles sympathiques et en accord (SHAPE 1 et 3, une corde par voix) ; seule la corde
  (SHAPE 2, avec sa dispersion) reste à 2 voix : à 3 voix, elle coûtait 15 à 16,3 % aux deux bouts de CONTOUR.

Pour tenir ces 3 voix sous 13 % :

- le pincement : sa chaîne (peigne, passe-bas, anti-continu) tournait environ 0,7 s après chaque note, le temps que
  la traîne de l'anti-continu (une constante qui décroît, 100 ms par facteur e) passe sous −108 dB. Maintenant, dès
  que le pincement est sous −72 dB et le filtre d'excitation sous −108 dB pendant 8 blocs, la traîne seule est
  calculée (`dc_tail`, son entrée à zéro), puis plus rien. Ce qui est coupé du peigne du pincement (−5 dB par période)
  n'apporte plus à la corde qu'une énergie négligeable ; contre Rings, la médiane des 61 cas passe de 88 à 76 dB ;
- la hauteur d'une voix n'est recalculée que si sa note change, son filtre d'excitation que si sa coupure change
  (celle d'une voix inactive est fixe) ;
- `modal_str_run` sert aussi aux cordes aiguës (son ordre est celui de la boucle C, valable pour tout retard) ;
- en polyphonie, la corde d'une voix écrit directement `out − aux` dans la sortie (`modal_str_combn`), sans les
  tampons `ob` et `ab` (la même somme modulo 2³²) ;
- en 3 voix, les potards qui bougent sont repris un bloc sur 32 (21 ms ; 16, 11 ms, sinon).

`test_modal_dsp.py` contrôle maintenant les voix : 4 notes de hauteurs différentes, le niveau de la 1re (sa
fondamentale) après chaque note suivante :

| | Après la 3e note | Après la 4e note |
|---|---|---|
| modal, 2 voix | −26 dB (coupée) | −39 dB |
| modal, 3 voix | −2 dB (elle sonne) | −28 dB (coupée) |
| sympathiques ou accord, 2 voix | −29 dB (coupée) | −21 dB |
| sympathiques ou accord, 3 voix | −1 dB (elle sonne) | −29 dB (coupée) |

Charge (`test_budget.py --engines modal`, 60 cas, `TOUT OK`), le pire cas de chaque modèle :

| SHAPE | Pire cas | Réglage |
|---|---|---|
| 0 modal | 12,3 % | 2 voix, COLOR qui bouge à chaque bloc |
| 1 cordes sympathiques | 12,7 % | 3 voix, COLOR qui bouge à chaque bloc |
| 2 corde | 12,5 % | 2 voix, COLOR, CONTOUR et SWEEP à 127 |
| 3 cordes en accord | 12,8 % | 3 voix, COLOR qui bouge à chaque bloc |

Le moins cher : 6,0 %. Le pire bloc, quand un potard qui bouge est repris en 3 voix : 31 % environ (le PEAK).

Preuves : `test_modal_dsp.py` 61 cas, le contrôle `LITE` et celui des voix, `TOUT OK` (médiane 76,3 dB) ;
`test_modal.py` : 107 contrôles, `TOUT OK`.

## 9. Reste à vérifier

- `[À FAIRE]` La charge sur la machine (page System de Model-TG) : HARMONICS, CYMBAL, STRUCK DRUM, STRUCK BELL,
  FLUTED, MORPH, SQUARE SYNC sur une note aiguë, chacun seul sur une piste, son tenu. Au modèle, la marge la plus
  mince est STRUCK BELL quand PITCH bouge (12,9 %) : la disposition du code en mémoire déplace ces chiffres de
  ±0,3 point d'une compilation à l'autre.
- `[À FAIRE]` L'oreille : VOWEL FOF, PLUCKED, BOWED, STRUCK BELL, STRUCK DRUM, SNARE, TWIN PEAKS NOISE, PARTICLE NOISE,
  HARMONICS, SINE TRIANGLE (doivent sonner comme avant) ; WAVE PARAPHONIC et WAVE MAP sur les notes très aiguës.
- `[À FAIRE]` MODAL sur la machine : la charge d'une piste (page System) sur les quatre modèles, 1 à 3 voix, avec un
  LFO sur COLOR ; en 3 voix (SHAPE 0, 1, 3), la 3e note ne coupe plus la 1re, la 4e oui ; l'oreille sur les cordes (plus douces dans l'aigu), les modèles sympathiques sur 1 et 2 voix, un
  potard tourné pendant une note (par pas d'environ 11 ms).
