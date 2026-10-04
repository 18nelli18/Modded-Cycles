# 38 — Tempo au-delà de 300 BPM : jusqu'où, et le tweak `tempo-max` (546 BPM)

Demande d'un utilisateur : débloquer la limite de 300 BPM. Analyse sur le MAIN OS 1.13, tweak `42-tempo-max.json`
(`tools/gen_tempo_max.py`), preuve en émulation (`tools/emu/test_tempo_max.py`). Adresses : VA de l'OS 1.13.

## Réponse courte

- **546 BPM** (546,0 exactement) est le plafond **sans changer le format des projets** : le projet enregistre le tempo en
  1/120 de BPM sur **16 bits** (65 535 / 120 = 546,1).
- Le reste de l'OS suit : l'heure musicale du séquenceur est sur 32 bits et tiendrait jusqu'à **3 750 BPM** (une
  impulsion d'horloge MIDI par bloc audio au plus). Deux calculs ont une marge prévue pour **351,6 BPM** seulement :
  le pas de phase du LFO (corrigé ici) et la durée de note la plus courte (pas atteinte, voir §4).
- Au-delà de 546, il faudrait changer l'unité du tempo dans les projets : un projet serait relu à un autre tempo par
  l'OS d'origine et par Transfer. Pas fait.

## 1. Le tempo dans l'OS `[FAIT]`

| Où | Quoi |
|---|---|
| `0x40149310` | tempo courant, en **1/120 de BPM** (120 BPM = 14 400 ; 300 BPM = 36 000). Même unité qu'Elektroid (« pattern tempo * 120 »). Lu par `0x40058bf4` |
| `0x40140a84` / `0x40140a88` | tempo en attente / « appliquer tout de suite » (`0x40058bb4`, `0x40058b62`) |
| `0x40091780(mode, tempo, notifier)` | applique le tempo (écrit `0x40149310`, prévient l'interface) |
| projet, champ **+18** (16 bits, `mvz.w`) | lu par `0x4000c816`, écrit par `0x4000c846` (menu Tempo, tap tempo) |
| objet `0x4000eb90`, champ +0 (32 bits) | tempo de pattern (`0x40012356` / `0x4001238e`), 14 400 par défaut |
| `0x8000184c` | **heure musicale** : +2 × tempo à chaque bloc audio (32 échantillons, 0,67 ms), donc 240 × BPM par bloc ; une noire = 21,6 millions d'unités, une impulsion d'horloge MIDI = 900 000 (`0x40059438`) |

Les bornes 30–300 BPM sont des constantes 3 600 / 36 000, en six endroits :

| Adresse | Fonction | Rôle |
|---|---|---|
| `0x4000c86e` | `0x4000c846` | écriture du tempo dans le projet (16 bits) |
| `0x400123cc` | `0x4001238e` | tempo de pattern (32 bits) |
| `0x4003d4bc` | `0x4003d4b8` | molette du menu Tempo (BPM × 120 + dixièmes × 12, `0x4003d8ea`) |
| `0x40058b94`, `0x40058b9c` | `0x40058b62` | moteur : tempo appliqué |
| `0x40058bc6`, `0x40058bce` | `0x40058bb4` | moteur : tempo en attente (chargement, tap tempo) |
| `0x4008064c`, `0x40080654` | horloge MIDI reçue | tempo = 1 900 800 000 × 512 / (somme des 24 derniers intervalles, minuteur DMA 0) |

Et deux contrôles **au chargement** : `tempo − 3 600 ≤ 32 400` (non signé), sinon **120 BPM** :
`0x4005aac0` (message du séquenceur, champ 16 bits +4) et `0x4005b3f6` (copie du champ +18 du projet). Sur l'OS
d'origine, un projet enregistré à 400 BPM se rouvre donc à 120 BPM.

## 2. Ce qui dépend du tempo `[FAIT]`

Tous les lecteurs de `0x40149310` (11 références) et des champs du projet :

| Où | Calcul | Au-delà de 300 BPM |
|---|---|---|
| interruption audio `0x40058c60`…`0x400594ee` | heure musicale += 2 × tempo ; compte à rebours de l'impulsion suivante (`0x80001854`) −= 2 × tempo ; décomptes des 6 pistes (`0x800017b4`, `0x800017cc`) −= tempo | sûr : 32 bits, comparaisons signées (l'heure reboucle toutes les 22 s à 546 BPM, les écarts restent sous 2³¹) ; une impulsion d'horloge par bloc au plus jusqu'à 3 750 BPM |
| `0x400586a0` (début de note) | décompte de durée = (heure du trig − maintenant)/2 + longueur (`0x4010d814`) − tempo | sûr |
| `0x40058836` (avancement de la note, chaque bloc) | progression += tempo × taux (`0x4010d610`[longueur + 1]) / 4, plafonnée à 2³¹ − 1 | `muls.l` : taux ≤ 25 451 (l'entrée 0, 50 903, n'est jamais lue : l'index est longueur + 1), produit < 2³¹ jusqu'à **703 BPM** : sûr à 546 |
| `0x400581b4` (temps de delay synchronisé) | … × 900 / tempo, plafonné à 384 000 | division : sûr |
| `0x40091ab2` (les 6 LFO) | pas de phase = (vitesse − 16 384) × 2 × tempo, décalé de 11 − multiplicateur ; cycle de 1 382 400 000 | produit < 2³¹ jusqu'à 65 536 ; mais le **pas dépasse un cycle** au-delà de 42 187,5 (351,6 BPM) avec la vitesse au maximum et le plus grand multiplicateur synchronisé (index 11) : voir §3 |
| `0x4009602e(t, 120, 1, 1)` | affichage BPM + dixième (menu Tempo, tap tempo `0x4006dbf8`) | trois chiffres (« 999 » sert de gabarit) : 546.0 s'affiche |
| Model-TG (`vendor/Model-TG/src/model_tg.s`) | mesure = 1 382 400 000 / tempo (étirement synchronisé, stutter), durée d'un slide en blocs | divisions : sûr |

Autres limites qui ne bougent pas : 30 BPM en bas, horloge MIDI envoyée (218 impulsions/s à 546 BPM, loin des 3 125
octets/s du fil), retrigs (à 546 BPM et vitesse de piste 2×, un retrig 1/80 tombe toutes les ~2 blocs).

## 3. Le LFO au-delà de 351,6 BPM

En `0x40091ba4`, si la nouvelle phase dépasse un cycle (comparaison non signée), l'OS retire **un** cycle (ou en ajoute
un si le LFO va à l'envers et que la phase est passée sous 0). C'est juste tant que le pas reste sous un cycle, ce que
garantit la borne de 300 BPM (pas maximal 32 768 × 36 000 = 1,18 × 10⁹ < 1,3824 × 10⁹). À 546 BPM le pas atteint
2,15 × 10⁹ : la phase reste hors de sa plage, grandit et reboucle, et le LFO devient erratique (mesuré en émulation :
315 sorties sur 1 800 mises à jour à 400 BPM).

Correctif, à la même place (`0x40091bd8`, 18 octets → 16 + `nop`) : la remise dans le cycle devient une boucle qui
revient au test :

```
move.l #1382400000,d1 ; tst.l d7 ; bge.s 1f ; neg.l d1
1: sub.l d1,d2 ; bra.s 0x40091ba4 ; nop
```

`d1` est rechargé juste après (`0x40091bea`). Le repérage d'événement du mode à un tour (`0x40091bac`) est gardé par
l'indicateur `a3@`, qu'il met à 1 : il ne se refait pas. La boucle s'arrête en au plus 3 tours pour toute phase 32 bits.
En dessous de 351,6 BPM, elle ne fait qu'un tour : rien ne change.

## 4. Le tweak `42-tempo-max.json`

- Maximum **65 520 = 546,0 BPM** (un pas exact de la molette : 1 BPM = 120, 0,1 BPM = 12) dans les six bornes ;
  contrôles au chargement à 65 520 − 3 600 = 61 920.
- La boucle du LFO (§3).
- 12 écritures, **aucune place libre** ; aucune adresse commune avec les autres tweaks (6ch, Model-TG et sa version
  combinée, moteurs du Syntakt, arpégiateur, effacement des trigs).
- Dans le flasher web : carte « Tempo jusqu'à 546 BPM » ; 4 607 combinaisons de référence (le double).

## 5. Preuve en émulation (`tools/emu/test_tempo_max.py`)

Sur le MAIN OS d'origine et sur le MAIN OS modifié, le vrai code :

| Test | D'origine | Modifié |
|---|---|---|
| `0x40058bb4` / `0x40058b62`, 10 à 833 BPM demandés | 30–300 | 30–546,0 |
| projet (16 bits), pattern, molette du menu Tempo | 30–300 | 30–546,0 |
| horloge MIDI reçue à 120 / 300 / 400 / 546 / 700 BPM | 120, 300, 300, 300, 300 | 120, 300, 400, 546, 546 |
| chargement à 400 et 546 BPM | remis à 120 | gardés (hors 30–546 : 120) |
| affichage | — | 30.0, 120.0, 300.0, 400.1, 546.0 |
| les 6 LFO (vraie fonction, EMAC exacte), 300 mises à jour, 120 à 546 BPM | juste jusqu'à 351,5 ; hors cycle à 400 et 546 | phase = (ancienne + pas) mod cycle, toujours |

## 6. Testé sur la machine (04/10/2026)

L'utilisateur a flashé le tweak par le flasher web (méthode USB rapide) et confirme : « ça marche nickel ». La carte
passe de « Expérimental » à « Testé ».
