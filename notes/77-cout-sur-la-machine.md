# 77 — Ce que coûte un bloc sur la machine : relevés et modèle étalonné

Relevés de Maxime (23/10/2026) avec l'OS 2.1, le code chaud en SRAM (PR #108, note 76 de cette PR) et le firmware de
mesure ([75](75-firmware-de-mesure.md)), puis un modèle du coût sur la machine (`tools/emu/hwcost.py`), étalonné sur ces
relevés.

## En bref

| | État |
|---|---|
| Relevés sur la machine | `[FAIT]` un projet MODAL, SNARE, METAL, ACID, KICK, CPVtg (§1) |
| Code chaud en SRAM | `[FAIT]` pas plus rapide sur la machine, un peu plus lent : pas livré (§2) |
| Modèle du coût, étalonné | `[FAIT]` en émulation ; reproduit MODAL (28 à 32 % contre 30 %) et l'étage de sortie (19 à 20 % contre 20 %) (§3) |
| Où passe le temps | `[HYP]` modèle : 56 % instructions, 24 % code relu en DDR2, 9 % attentes de l'EMAC, 8 % données (§4) |
| MODAL | `[HYP]` modèle : 17 % (modal, corde) à 28 % (cordes sympathiques, accords) sur 1 voix, 37 % la corde sur 4 voix (§5) |

## 1. Relevés (23/10/2026)

Retour de Maxime, mot pour mot : « J'ai charger modded-cycles-os_2.1.syx avec un projet 1 modal 1 Snare, 1 metal, 1 acid,
1 kick, 1 CpVtg. Resultat y'a tjr des bugs, des ralentissement des pas loupé etc. »

Même projet, firmware de mesure sans puis avec le code chaud (`…-mesure.syx`, `…-mesure-hot.syx`) :

| Écran | Sans code chaud | Avec |
|---|---|---|
| Model-TG, page 1 : CPU, PEAK | 80 %, 270 % | 81 %, 456 % |
| Model-TG, page 2 : T1 … T6 | 30, 1, 1, 5, 7, 0 % | 24, 3, 1, 3, 4, 5 % |
| Model-TG, page 2 : Tracks, Other, Total | 40, 38, 75 % | 41, 42, 80 % |
| AUDIO : TOTAL, VOICES, OUTPUT | 80, 41, 20 % | 86, 49, 21 % |
| BENCH : LINE, LINE SR, I-MISS, D-MISS | 8,04, 16,02, 22,81, 17 | 8,04, 16,02, 22,73, 22 |

- T1 est la piste MODAL (30 % : plus que les cinq autres ensemble).
- **PEAK de Model-TG** n'est pas « un bloc qui a duré 2,7 blocs » : c'est le pire rapport, depuis l'ouverture de la page,
  entre le travail d'un bloc et le temps écoulé depuis le début du bloc précédent (`prof_end`, `vendor/Model-TG`). Un
  bloc qui démarre en retard, ou juste après un bloc en retard, le fait monter très au-dessus de 100 %.
- **BENCH** (cycles du processeur) : une ligne de code de 16 o dans le cache coûte 8 cycles (1 par instruction), lue en
  SRAM 16, lue en DDR2 31 (8 + 22,8). Une ligne de données absente du cache : 17 à 22 cycles de plus.
- Pas encore relevés : la fréquence (CPU de BENCH), ALU, MAC, MEM, la page AUDIO entière (PEAK, IDLE, OTHER…), COLD.

## 2. Le code chaud en SRAM : plus lent

- `[FAIT]` Avec le code chaud, TOTAL 80 → 86 %, VOICES 41 → 49 % ; la charge de Model-TG 80 → 81 %. Pas de gain.
- **Pourquoi** (le modèle du §3 le reproduit : +2,4 points) :
  - le code en SRAM passe par le cache d'instructions (RAMBAR du bootstrap `0x80000235`, la valeur « données seulement » de NXP, MCF5441x RM §7.2.1 ; notes/75 §1.2) : une
    ligne qui manque y coûte 8 cycles au lieu de 23 en DDR2, pas 0 ;
  - avec un moteur du Syntakt (CPVtg) dans le projet, le code du Syntakt garde sa place : il ne reste que les deux fins
    de SRAM, 5,2 Ko ;
  - chaque détour coûte : son talon fait `move.l …,-(sp) ; rts`, et le ColdFire V4 prédit les `rts` par une pile de
    retour matérielle (2 cycles prédit, 9 sinon, MCF5441x RM §3.3.5.7) ; le talon la désaccorde. Les talons, les
    originaux déplacés et `hot_tab` sont en SDRAM : des lignes de code et de données de plus à chaque appel, y compris
    pour l'interface (Other 38 → 42).
- **Décision** : pas livré (PR #108 laissée en brouillon). À reprendre seulement si la SRAM peut servir le code sans
  le cache (§6) et sans talons.

## 3. Le modèle (`tools/emu/hwcost.py`)

Le vrai code de l'interruption audio (`osbanc.OsBanc`), et ce que le ColdFire V4 y ajoute :

| Quoi | Coût | Source |
|---|---|---|
| Instruction | 1 cycle ; divisions 32 bits 35, 16 bits 20 ; multiplications 4 ; `movem` 1 par registre ; `jsr`/`jmp` par registre 5 ; vers MACSR 8 | RM §3.3.5 |
| `rts` | 2 cycles, 9 si la pile de retour ne le prédit pas (8 entrées `[HYP]`) | RM §3.3.5.7 |
| Lecture d'un accumulateur | 3 cycles d'attente juste après un MAC vers lui (moins s'il y a des instructions entre) ; +1 avec saturation ou arrondi (MACSR `0xa0` dans la boucle des voix) | RM §5.3.3, table 3-18 |
| Ligne de code absente | 22,81 cycles en DDR2, 7,98 en SRAM ; cache 8 Ko, 4 voies, compteur tournant | BENCH, RM §6.3.1 |
| Ligne de données absente | 20 cycles ; ligne modifiée chassée 6 `[HYP]` ; SRAM 0 ; vue sans cache 20 `[HYP]` | BENCH |

- 250 MHz `[HYP]` (166 667 cycles par bloc) : à confirmer par la case CPU de BENCH.
- Ne voit pas : les branchements mal prédits, les attentes de calcul d'adresse, l'eDMA et l'USB sur la mémoire,
  l'interface entre deux blocs (caches gardés ou vidés : à peine 2 points d'écart).

| Poste | Mesuré | Modèle (les 6 pistes jouent, un trig tous les 24 blocs) |
|---|---|---|
| MODAL (T1) | 30 % | 28 à 32 % |
| Étage de sortie | 20 % | 19 à 20 % |
| Les 5 autres pistes | 1 à 7 % | 7 à 10 % chacune (Model-TG ne calcule pas une voix éteinte ; le modèle les fait toutes jouer) |
| Code chaud | +1 à +6 points | +2,4 points |

## 4. Où passe le temps (modèle, projet du §1, toutes les pistes jouant)

170 000 cycles par bloc :

| Part | Cycles | % du bloc |
|---|---|---|
| Instructions | 95 400 | 56 |
| Code relu en DDR2 (1 800 lignes) | 41 100 | 24 |
| Attentes de l'EMAC | 14 600 | 9 |
| Données absentes du cache | 14 000 | 8 |
| Code lu en SRAM (393 lignes, celui du Syntakt) | 3 100 | 2 |
| `rts` mal prédits | 1 700 | 1 |

- Les attentes de l'EMAC sont partout : MODAL 4 200, l'étage de sortie 2 600, SNARE 1 700, ACID 1 900.
- Le code relu en DDR2 est la plus grosse part après les instructions.

## 5. MODAL, modèle par modèle (piste seule, 1 trig tous les 96 blocs)

| SHAPE | Régime | Ce qui pèse |
|---|---|---|
| 0 modal | 16,8 % | `mode_fix` 8,1 % dont 2 800 cycles d'attente de l'EMAC ; `modal_render` 4,5 % |
| 1 cordes sympathiques | 28,3 % | `modal_render` 7,2 % (173 lignes de code par bloc) ; les cordes (lecture, amortissement, écriture) 10 % ; 226 lignes de données de l'état des pistes |
| 2 corde, 1 voix | 16,7 % | `str_process` 6,9 % |
| 2 corde, 4 voix | 37,5 % | `str_process` 23,8 %, dont 7 700 cycles d'attente de l'EMAC |
| 3 accords | 27,8 % | comme SHAPE 1 |

- Les données absentes viennent surtout des lignes à retard des cordes (état des pistes, en SDRAM) : chaque bloc lit et
  écrit 32 nouveaux échantillons par corde, des lignes qui ne sont jamais dans le cache.
- Exacts, sans changer le son : réordonner les noyaux en assembleur pour ne plus lire un accumulateur juste après un
  MAC (environ −3 000 cycles, 2 points) ; du code par bloc plus petit (moins de lignes relues).
- Avec l'accord de Maxime seulement : lignes à retard sur 16 bits (moitié moins de lignes), moins de modes, etc.

## 6. Suite proposée

1. MODAL : les noyaux sans attentes de l'EMAC (exact).
2. L'étage de sortie en une passe (chantier 3) : 20 % sur tous les projets.
3. Mesurer si la SRAM peut servir le code directement, sans le cache (RAMBAR « instructions et données », `0x21`,
   posé pendant l'essai LINE SR seulement) : si oui, le code chaud en SRAM, sans talons, redevient intéressant.
4. Les attentes de l'EMAC des machines d'origine et de l'étage de sortie (code d'Elektron).

## Chronologie

- 23/10/2026 : relevés de Maxime ; modèle étalonné ; le code chaud n'est pas livré.
