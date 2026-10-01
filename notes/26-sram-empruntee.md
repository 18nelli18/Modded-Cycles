# 26 · Voix du Syntakt moins chères : la SRAM interne empruntée

Travail du 01/10/2026, première piste de [25 §7](25-regulateur-de-charge.md) : « rendre les voix du Syntakt moins chères, en leur prêtant la zone de travail en mémoire rapide des machines d'origine pendant leur calcul ».

Adresses : MAIN OS Cycles 1.13 et programme audio du Syntakt 1.41, comme dans les notes [17](17-portage-exact-syntakt.md) à [25](25-regulateur-de-charge.md).

## 0. En bref

| | État |
|---|---|
| Cause du surcoût des voix du Syntakt | `[FAIT]` cache de données de 8 Ko seulement ; tampons et tables du Syntakt en SDRAM (§1) |
| Zone de travail des machines d'origine en SRAM | `[FAIT]` 2,6 Ko, réécrite par chaque voix d'origine (§2) |
| Tampons de travail du Syntakt dans cette zone | `[FAIT]` (§3, §4) |
| Table de sinus du Syntakt lue dans celle du Cycles | `[FAIT]` identique à l'octet près (§4) |
| Preuve en émulation | `[FAIT]` son identique au Syntakt, zone vérifiée comme simple brouillon (§5) |
| Gain estimé | `[FAIT]` −35 à −63 % de lignes de données en SDRAM par voix du Syntakt (§6) |
| Essai sur la machine | `[FAIT]` « beaucoup mieux » : 4 voix du Syntakt sur tous les pas sans note coupée ; des coupures dès la 5ᵉ (§8) |

## 1. Pourquoi une voix du Syntakt coûte deux voix d'origine

- **`[FAIT]`** Le processeur du Model:Cycles, un MCF54415, n'a que **8 Ko de cache d'instructions et 8 Ko de cache de données**.
  - Source : *MCF5441x ColdFire Microprocessor Data Sheet*, page 1 : « 8 KB instruction cache and 8 KB data cache » ([NXP][DS-MCF]) ; puce identifiée sur les photos du PCB ([21 §3.1](21-architecture-materielle.md)).
- **`[FAIT]`** La SDRAM est un seul boîtier DDR2 relié en **8 bits** : chaque ligne de cache manquante se lit octet par octet.
  - Source : même fiche, page 1 : « SDRAM controller supporting full-speed operation from a single x8 DDR2 component » ; boîtier U3 ([21 §3.2](21-architecture-materielle.md)).
- **`[FAIT]`** Les machines d'origine calculent dans la **SRAM interne** (64 Ko en `0x80000000`, un cycle par accès, hors cache). Les moteurs du Syntakt, eux, lisent et écrivent la **réplique de leur SRAM**, posée en SDRAM à `0x43020000` ([17](17-portage-exact-syntakt.md)) : tout passe par le cache.
- **`[FAIT]`** En émulation, une voix du Syntakt touche à chaque bloc :

| Voix | Lignes de 16 o de données en SDRAM, par bloc |
|---|---|
| SNARE (machine d'origine) | 73 |
| SDVtg | 230 |
| CPVtg | 185 |
| SYToy | 230 |
| SYBit | 239 |
| SYSwm | 365 |

  - Source : `UC_HOOK_MEM_*` sur un bloc en régime établi (bloc 10, 6 pistes déclenchées au bloc 1), tweak `syntakt-sd-cp-toy-bits-swarm` d'avant ce travail.
  - Le cache de données (512 lignes) ne peut pas garder tout cela d'un bloc à l'autre, avec 6 voix, le mixage, les effets et l'interface : presque chaque ligne est relue en SDRAM à chaque bloc.
- Ces lignes se répartissent en :
  - **tampons de travail** (61 à 156 lignes, 30 à 43 %) : écrits puis relus pendant le calcul de la voix. En cache, chaque ligne coûte une lecture et une réécriture en SDRAM ;
  - **tables** (sinus, formes d'onde) : lues seulement ;
  - **état de la voix** (1 800 o par voix) : doit être conservé d'un bloc à l'autre.

## 2. La zone de travail des machines d'origine

- **`[FAIT]`** La remise à zéro d'une voix du Cycles (`0x400a7ab8`) donne à chacune de ses 4 sous-voix deux tampons de 292 o (73 mots) :
  - A'ₖ = `0x8000bf38` + 292 k et B'ₖ = `0x8000c3c8` + 292 k, k = 0..3 (boucle `0x400a7b20..0x400a7bd6`) ;
  - les mêmes adresses pour les 6 voix : c'est **une zone commune**, réécrite par chaque voix.
  - Source : désassemblage de `0x400a7b3e..0x400a7bd6`.
- **`[FAIT]`** KICK y ajoute un tampon en `0x8000beb8`, TONE utilise `0x8000c858..0x8000c8e8`. La zone empruntée est donc **`0x8000beb8..0x8000c8e8` (2 608 o)**.
- **`[FAIT]`** Dans tout le code de l'OS, ses **40 références** sont dans la remise à zéro des voix et les moteurs d'origine (`0x400a7b3e..0x400ab78c`). Ni le mixage, ni les effets, ni l'interface ne la désignent.
  - Source : `tools/emu/test_sram_scratch.py`, partie « statique » (constantes 32 bits du code, `0x40000400..0x40118000`).
- **`[FAIT]`** En émulation, chaque voix d'origine **écrit chaque octet de la zone avant de le lire**, sauf un mot (`0x8000c3c8`) lu d'abord par METAL, PERC et CHORD : l'entrée de modulation de la 1ʳᵉ sous-voix, sans effet (§5).
- **`[FAIT]`** Le Syntakt a exactement la même routine (`0x40003ee0`, boucle `0x40003f4e..0x4000402c`), avec **7 sous-voix** au lieu de 4 :
  - Aₖ = `0x80008c60` + 292 k et Bₖ = `0x8000945c` + 292 k, k = 0..6 ;
  - plus 4 tampons C de 148 o pour SY SWARM (`0x80009c58` + 148 j).
  - Source : désassemblage de `0x40003f6c..0x4000402c` (Syntakt, section 7).

## 3. Les tampons de travail du Syntakt

**Éléments utilisés**, en émulation (bloc 2 et bloc 10, réglages par défaut) :

| Moteur | Tampons |
|---|---|
| SDVtg | A₀..A₃, B₀..B₃ |
| CPVtg | A₀, A₁, B₀..B₂ (et une structure de 288 o en `0x80004a50`, non déplacée) |
| SYToy | A₀..A₄, B₀..B₄ |
| SYBit | A₀..A₃, B₀..B₃ |
| SYSwm | A₀..A₆, B₀..B₆, C₀..C₃ |

- Seuls les **128 premiers octets** de chaque élément servent (32 échantillons de 32 bits). Les machines d'origine utilisent parfois tout l'élément (TONE suréchantillonne), pas les moteurs du Syntakt.
  - Source : `test_sram_scratch.py`, essais aléatoires (§5) ; trace des accès des 5 moteurs.
- **Le pas de 292 o doit être gardé** : SY SWARM additionne ses 7 voix en lisant B₀ + 292 k (`0x4000978a..0x400097aa`, déplacements 288, 580, 872…).
- Comme sur le Syntakt, ces tampons sont communs à toutes les voix, et écrits avant d'être lus. Exception : le 1ᵉʳ mot de B₀, lu d'abord par SY TOY et SY SWARM, comme le mot `0x8000c3c8` du Cycles (§2).

## 4. Disposition en SRAM

`SRAM_MAP` dans `tools/gen_syntakt_engines.py` :

| Données du Syntakt | Où, en SRAM interne du Cycles |
|---|---|
| Aₖ (`0x80008c60` + 292 k) | `0x8000beb8` + 292 k |
| Bₖ (`0x8000945c` + 292 k) | `0x8000bf38` + 292 k, entrelacés avec les Aₖ |
| Cⱼ (`0x80009c58` + 148 j) | `0x8000c690` + 148 j |
| table de sinus `0x80004b70..0x80004f74` (257 mots) | `0x8000eee4`, celle du Cycles |

- Les **18 tampons de 128 o** tiennent dans la zone (`0x8000beb8..0x8000c8cc`), sans se chevaucher : le générateur le vérifie à chaque build (`check_sram_map()`).
- **Table de sinus** : celle du Syntakt est identique, sur 1 028 o, à celle du Cycles en `0x8000eee4`. Les deux remises à zéro la donnent à leurs sous-voix au même endroit (+176..+188 pour le Syntakt, +168..+180 pour le Cycles).
  - Le générateur compare les deux tables dans les fichiers de l'utilisateur, à chaque build.
  - Source : contenu initial des deux SRAM (Cycles `0x4019b590..`, Syntakt `0x4004f6e0..`), comparés par `check_sram_map()`.
- **Mise en œuvre** : 44 adresses du code copié changent de destination (relocalisation, comme le reste de la SRAM du Syntakt). Les autres sont calculées par la remise à zéro, à partir des bases relocalisées.
- **Pas déplacés**, faute de place :
  - la structure de 288 o de CP VINTAGE ;
  - l'état des voix (conservé d'un bloc à l'autre) ;
  - les autres tables (formes d'onde de SY BITS et SY SWARM : absentes du Cycles).

## 5. Preuve en émulation

**Nouveau test** `tools/emu/test_sram_scratch.py` (tweak à 5 moteurs) :
- **Statique** : les 40 références à la zone (§2) ; les 18 tampons dans la zone, sans chevauchement ; la table de sinus identique.
- **Brouillon** : 12 essais, 6 pistes, machines d'origine et du Syntakt mêlées au hasard, réglages et trigs au hasard, 150 blocs.
  - Avant le calcul de **chaque voix**, la zone est remplie de valeurs aléatoires : les 6 sorties restent **identiques, échantillon par échantillon**.
  - La zone n'est donc qu'un brouillon, pour les voix d'origine comme pour celles du Syntakt ; les mots lus avant d'être écrits (§2, §3) n'ont pas d'effet.
- Les voix du Syntakt ne touchent, dans la zone, que les 128 premiers octets de leurs tampons ; jamais la table de sinus en écriture ; plus jamais l'ancienne place de ces données en SDRAM.

Résultat : **tout passe** (14 vérifications), par exemple :
- essai 3 : PERC, CPVtg, SYBit, CHORD, SDVtg, SYSwm, 6 pistes sonores ;
- essai 10 : SYBit, SYToy, SDVtg, SYBit, SYSwm, KICK.

**Tests existants**, sur les tweaks régénérés :
- `test_syntakt_machines.py`, sur SD, CP, SY TOY, SY BITS, SY SWARM, SD + CP, SD + CP + SY TOY, SY TOY + SY SWARM et les 5 moteurs : 26 à 30 vérifications, tout passe.
  - Les 5 moteurs restent **identiques aux moteurs du Syntakt** (écart max 1 LSB, comme avant).
  - SNARE reste identique à l'OS d'origine.
- `test_idle.py` (arrêt des voix muettes), `test_governor.py` (régulateur), `test_meter.py` (compteur) : tout passe.
- Flasher web : les 511 combinaisons reconstruites dans la page donnent les empreintes de référence (`webflash_smoke.sh`, ALL OK).
- La charge utile garde sa taille (238 080 o pour les 5 moteurs) : rien ne change pour le démarrage.

## 6. Gain attendu

**Lignes de 16 o de données en SDRAM par voix et par bloc** (même mesure qu'au §1) :

| Voix | Avant | Après | En SRAM interne, après |
|---|---|---|---|
| SDVtg | 230 | 149 (−35 %) | 87 |
| CPVtg | 185 | 105 (−43 %) | 84 |
| SYToy | 230 | 84 (−63 %) | 151 |
| SYBit | 239 | 133 (−44 %) | 112 |
| SYSwm | 365 | 208 (−43 %) | 161 |
| SNARE (d'origine) | 73 | 73 | 137 |

**Simulation de cache** : 8 Ko de données et 8 Ko d'instructions, lignes de 16 o, 4 voies, LRU, allocation en écriture. Seule la boucle des voix est simulée. Lignes de SDRAM transférées par bloc, en régime établi :

| Cas | Données, avant | Données, après | Instructions (inchangé) |
|---|---|---|---|
| 6 machines d'origine | 130 | 130 | 377 |
| SYSwm + 5 d'origine | 792 | 332 | 598 |
| SDVtg, CPVtg, SYSwm + 3 d'origine | 1 138 | 602 | 941 |
| 6 voix du Syntakt | 1 477 | 839 | 645 |

- Source : simulation sur les accès de l'émulateur (script de travail, non versionné).
- Le trafic de **données** des voix du Syntakt baisse de 40 à 60 %. Celui du **code** ne change pas : il pèse autant, mais il n'y a pas de place en SRAM pour le code.
- La simulation ignore le mixage, les effets et l'interface, et le vrai temps d'une ligne en SDRAM n'est pas connu : **seule la mesure sur la machine dira le gain en temps.**

## 7. Mesure sur la machine `[FAIT]`

Firmware de diagnostic v5 (compteur « pic/moyenne » + régulateur + 5 moteurs + SRAM empruntée), construit localement :
- `build/diag/model-cycles_OS1.13_diagnostic-charge_v5.syx` (MAIN OS `7b7a357e…`) ;
- `…_v5_6ch.syx` avec l'audio USB 6 canaux (MAIN OS `c8c13175…`).

Machines ajoutées : 7 = SDVtg, 8 = CPVtg, 9 = SYToy, 10 = SYBit, 11 = SYSwm. Lecture comme avant : pendant que le motif joue, ouvrir MACHINES sans tourner la molette et lire « pic/moyenne » ([23 §6](23-optimisation-charge.md)).

À comparer avec la v4 ([25 §5](25-regulateur-de-charge.md)), sur les mêmes motifs :
- 6 pistes custom : la v4 atteignait 99/67 ;
- 5 d'origine + SDVtg : 94/84 avec la v2 ([23 §6 bis](23-optimisation-charge.md)).

Écouter aussi s'il reste des coupures de notes, et si le son des moteurs du Syntakt est inchangé.

## 8. Résultat sur la machine (01/10/2026)

Retour de l'utilisateur, firmware de diagnostic v5 :
- « elle marche beaucoup mieux » ;
- **4 voix du Syntakt**, actives en même temps sur tous les pas de la mesure : **aucune note coupée** ;
- **à partir de la 5ᵉ voix du Syntakt** : des notes coupées (le régulateur intervient).

Décision : fusionner (PR #16), puis chercher comment tenir 5 et 6 voix du Syntakt ([27](27-cinq-et-six-voix.md)).

[DS-MCF]: https://www.nxp.com/docs/en/data-sheet/MCF54418.pdf
