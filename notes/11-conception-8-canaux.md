# 11 · Conception du mode 8 canaux (6 pistes + mix stéréo)

Travail du 25/09/2026, **sans matériel**. But : canaux USB 1-6 = pistes (comme le 6 canaux), canaux 7-8 = **mix stéréo** (avec effets) que le firmware calcule déjà et envoie en stock.
Ainsi le DAW reçoit les stems **et** le mix complet.

État : **partiellement conçu.** Le code neuf (stubs) est écrit et vérifié statiquement. Plusieurs éditions sont à haute confiance.
Un point de conception (le dimensionnement mémoire des rings) reste à finaliser — de préférence **en itérant sur la machine** (flash → capture → `analyse_dupes` → ajuste), car il dépend d'un agencement RAM difficile à lever à l'aveugle.

> ⚠️ Ce n'est pas encore un patch prêt à flasher. C'est la conception + les briques vérifiées. Ne pas construire de `.syx` 8 canaux tant que la section « rings » n'est pas tranchée.

---

## 1. Décision de conception : 8 canaux **en capture seule** (IN-only)

Le firmware a **deux chemins audio USB** :
- **IN** (machine → hôte) : la capture. C'est là que vivent nos stems. Feeder `FUN_40002912`, ring de base `0x80009800`.
- **OUT** (hôte → machine) : la lecture depuis l'ordinateur. Fonction `FUN_400024f2`, ring de base `0x80009b80`. `[FAIT]` (0x40002500 est dans cette fonction).

Le patch 6 canaux a resizé **les deux** rings (car il déclare 6 canaux de façon symétrique). Pour le 8 canaux, on **recommande de ne toucher qu'au IN** : 8 canaux en capture, lecture hôte inchangée (stéréo). Cela **évite tout le casse-tête du ring OUT** et reste dans ce qu'on maîtrise.
- **`[À CONFIRMER]`** que les deux éditions `bNrChannels` du 6 canaux (`0x4019b2fa`, `0x4019b387`) sont bien sur l'interface **AudioStreaming IN** (capture). Si l'une est côté OUT, il faudra trouver le `bNrChannels` IN correct. À vérifier en décodant la config de 328 o à `0x4019b2b6`.

## 2. Contrat de registres au point d'accroche (vérifié)

Au hook `0x40002a06` (boucle de copie du feeder IN), état confirmé par désassemblage :
- `d0` = nombre de mots longs = **trames × 2** (échelle stéréo) → `frames = d0 >> 1`.
- `d1` = pointeur destination (case du ring, déjà calculée).
- `d3` = index de trame de ce bloc.
- **source du mix stéréo = `0x24(a7)`** (36 déc), indexée par trame (`+ d3×8`), lue séquentiellement `(a0)+` — c'est **exactement** ce que le stock envoie en USB. En reproduisant cette lecture pour les canaux 7-8, on garantit un mix identique au stock.

## 3. Stub `tracks8` — VÉRIFIÉ (capstone)

96 octets, tient dans une cave libre. Par trame : 6 échantillons de piste (`0x80001858`, stride `0x80`, byterev) + mix L + mix R (byterev, lecture séquentielle du mix).

- Placement proposé : `0x401483c6` (cave de 142 o, `refs=[]`, **non** utilisée par les tweaks drumkilla).
- Hook : `0x40002a06` → `jmp 0x401483c6` + nops (24 o écrasés, `0x40002a1e` préservé), reprise `0x40002a26`. Trous identiques au 6 canaux → hookcheck déjà validé par le 6 canaux.

```
@0x401483c6 (96 o) :
4fefffcc 48d71fff 206f0058 2241 2a03 e78d d1c5 781f 2c03 cc84 e288 6f000034
247c80001858 45f26c00 7e06 2412 02c2 22c2 45ea0080 5387 6600fff2
2418 02c2 22c2 2418 02c2 22c2 5286 cc84 5380 6e00ffd0
4cd71fff 4fef0034 4ef940002a26
```
(désassemblage complet vérifié : prologue 13 registres, source mix à `0x58(a7)` = `0x24`+52, boucle pistes masquée mod-32, mix séquentiel, rejoint `0x40002a26`.)

## 4. Stub `prime8` — VÉRIFIÉ (capstone)

30 octets. Amorce un dTD pour un transfert de 8 canaux : token = 192 o (6 trames × 32), longueur privée = 192.

- Placement proposé : `0x40147e94` (cave de 140 o, `refs=[]`, libre).
- Hook : `0x400027e8` → `jmp 0x40147e94` + nops (22 o écrasés), reprise `0x400027fe`.

```
@0x40147e94 (30 o) :
203c00c00080 25400004 24bcdead0001 7218 e789 25410020 4ef9400027fe
```

## 5. Éditions inline — haute confiance

Grâce au fait que **×32 est un simple décalage** (`lsl #5`) et **stride 256 = `lsl #8`**, plusieurs sites qui exigeaient un stub au 6 canaux deviennent de simples éditions d'un ou deux octets au 8 canaux :

| Site (VA) | Rôle | Stock → 8 canaux | Note |
|---|---|---|---|
| `0x4019b2fa` | `bNrChannels` (terminal) | `02` → `08` | descripteur IN |
| `0x4019b387` | `bNrChannels` (AS_GENERAL) | `02` → `08` | descripteur IN |
| `0x4019b397` | `wMaxPacketSize` (LE) | `3800` → `e000` | 56 → 224 (7×32) |
| `0x40002ceb` | dQH `MaxPacketLength` | `38` → `e0` | 56 → 224 |
| `0x400029e4` | offset destination (dstoff) | `e788…` → `eb88…` | `lsl #3` → `lsl #5` (×32), inline, **pas de stub** |
| `0x40002a43` | token, `moveq #19` | `13` → `15` | → `moveq #21` (×32 décalé de 16) |
| `0x40002a4a` | token, `lsl #3` | `e788` → `eb88` | → `lsl #5` (×32) |
| `0x400027d3` | stride priming | `30ed8a9480` → `c0e18a4e71` | memset 192 ; `lsl #8` (×256) ; sub→nop |
| `0x400029d2` | stride slot-base | `e78ded899285` → `e78de1894e71` | `lsl #8` (×256) sur d1 ; sub→nop |

`[FAIT]` chaque valeur « stock » ci-dessus a été relue dans l'image ; les transformations sont vérifiées par désassemblage.

## 6. Rings IN — à finaliser (le point ouvert)

Le ring IN est à `0x80009800`. Le buffer suivant (`0x80009f00`) est utilisé par un autre chemin → **le ring IN ne peut pas dépasser `0x80009f00`** (`[FAIT]`, `mcfw.code_refs`). Marge = `0x700` = 1792 o.

- stride 8 canaux = **256** (marge > `wMaxPacketSize` 224). depth × 256 ≤ 1792 → **depth ≤ 7**.
- **depth 7** (capacité 7×6 = 42 trames > 32 requises ✓). Wrap d'index par `moveq #(depth-1)`.

| Site (VA) | Rôle | Stock → 8 canaux (proposé) | Confiance |
|---|---|---|---|
| `0x400027b3` | limite d'index ring IN | `0f` → `06` | 🟡 depth 7 |
| `0x400029b9` | limite d'index ring IN (2ᵉ site) | `0f` → `06` | 🟡 depth 7 |
| `0x40002564` | borne mémoire du ring IN | `9b80` → `9f00` | 🟠 à valider (agencement) |
| `0x4000281f` | nombre de dTD pré-amorcés | `0b` (11) → `05` ou `06` | 🟠 incertain |

`[HYP]` Ces 4 valeurs sont mon meilleur choix, mais l'agencement exact des buffers (`0x9800` / `0x9b80` / `0x9f00`) et le rôle précis de `0x4000281f` ne sont pas tranchés à l'aveugle. C'est **le** point à finaliser.

**Ce qu'il ne faut PAS toucher (choix IN-only)** : `0x4000253b` (`moveq #15`, ring OUT depth) et la partie OUT de `0x40002564` — on laisse la lecture hôte en stéréo. `[À CONFIRMER]` que `0x40002564` concerne bien le ring IN et non OUT ; si c'est OUT, la borne IN est ailleurs.

## 7. Comment finaliser (deux voies)

**Voie A — plus de rétro-ingénierie maintenant** : désassembler entièrement `FUN_40002778` (IN start) et `FUN_400024f2` (OUT) pour cartographier sans ambiguïté les bases/profondeurs/bornes des deux rings et le rôle de `0x4000281f`. Faisable, mais laborieux et toujours non testable.

**Voie B — itérer sur la machine (recommandée)** : une fois le Model:Cycles reçu et le **6 canaux validé** (jalon 1), assembler un candidat 8 canaux avec les valeurs de §6, le flasher, capturer, et lancer `analyse_dupes` + test de mute par canal. Ajuster depth/borne/pré-amorçage selon les doublons observés. Le brick est impossible (récupération par le MIDI IN), l'itération est rapide.

## 8. Résumé de l'état

| Élément | État |
|---|---|
| Contrat de registres | ✅ vérifié |
| `tracks8` (mix L/R) | ✅ assemblé + vérifié |
| `prime8` | ✅ assemblé + vérifié |
| Descripteurs, MPL, dstoff, token, strides | ✅ dérivés + vérifiés |
| Dimensionnement des rings IN | 🟠 candidat, à valider (voie A ou B) |
| IN-only vs symétrique | 🟡 choix IN-only recommandé, une confirmation de descripteur à faire |

**Conclusion** : le mode 8 canaux est à ~80 %. Le code neuf est prêt et vérifié ; il reste à trancher le dimensionnement mémoire des rings, ce qui se fera le mieux **machine en main** (itération rapide et sûre). C'est cohérent avec le chemin critique : valider d'abord le 6 canaux, puis finaliser le 8, puis le 12 (pan).
