# 82 — DELAY TIME et LFO SPEED en valeurs de notes du tempo (SETTINGS + potard)

Demande de Ruslan (29/10/2026, via la file des agents), après une première analyse d'agy : régler le temps du délai et
la vitesse des LFO en valeurs de notes (doubles, triolets, pointées, mesures) qui suivent le tempo, et passer d'un
mode à l'autre par SETTINGS + le potard du paramètre. Tweak `tweaks/model-cycles_OS1.13/61-tempo-sync.json`
(id `tempo-sync`), générateur `tools/gen_tempo_sync.py`, code `tools/machines/tempo_sync/tempo_sync.S`, preuve
`tools/emu/test_tempo_sync.py`. Adresses : VA de l'OS 1.13.

## En bref

- **SETTINGS tenu + DELAY TIME ou LFO SPEED tourné vers la droite** : le paramètre passe en **SYNC**, sur la valeur de
  note la plus proche (au rapport près) de celle d'avant. **Vers la gauche** : retour en **FREE**, sur la valeur
  d'origine la plus proche. Le relâchement de SETTINGS n'ouvre pas le Config Menu (`mod_used` de Model-TG).
- **En SYNC, le potard seul passe d'une valeur de note à l'autre**, un cran par valeur : celles du retrig de Model-TG
  (1/64 .. 1 BAR, `rtg_divs`), plus 1/128 et 1/96 en dessous, 4/3, 3/2, 2 BAR au-dessus pour le délai, et 4, 8,
  16 BAR pour les LFO. Pour un LFO, le signe est le sens (« -1/8 » tourne à l'envers) ; à gauche le plus rapide à
  l'envers, à droite le plus rapide à l'endroit, comme le potard d'origine (-64 .. +63). MULT ne compte pas en SYNC.
- **Gardé dans le mot du paramètre lui-même** (kit pour le délai, son pour LFO 1, LFO 2 dans les 4 octets de lfo-plus,
  tables de LFO 3/4) : 0 octet de plus, la valeur de note survit au changement de tempo, à la sauvegarde, au
  rechargement. Les anciens projets (mots d'origine, octet bas nul) restent en FREE et jouent comme avant, au bit
  près (§5).
- **Délai** : longueur = 900 000 × lu / tempo échantillons (lu en 1/1536 de mesure, tempo en 1/120 de BPM), soit
  exactement la valeur de note ; l'OS la borne à 384 000 (8,000 s) : 2 BAR est coupé sous 60 BPM, et la valeur
  affiche alors « > » (« 2 BAR > »). La ligne glisse vers sa nouvelle longueur par le filtre de l'OS, sans clic.
- **LFO** : un cycle par valeur de note (pas de phase par bloc ± 49 152 × tempo / lu) ; LFO 1, 2, 3, 4.
- `[FAIT en émulation]` tout cela, seul (avec Model-TG) et avec l'OS entier (§5). **À essayer sur la machine** (§7).

## 1. Ce que fait l'OS `[FAIT]`

Vérifications des faits de l'analyse d'agy : les formules et les nombres sont justes, mais **ses adresses du délai et
du LFO sont décalées de 0x3e8** (sa « 0x40057db8 » est `0x400581a0`, sa « 0x400916d8 » est dans `0x40091ab2`), **le
délai n'est pas en Kit +710** (voir 1.2) et **LFO 3/4 ne sont pas sauvés sur `main`** : le bloc « LF34 » du kit est
celui de la branche `pr93` / `lfo-plus-hold`, pas encore fusionnée ; sur `main`, LFO 3 et 4 vivent en mémoire
(tables `lfo34` de lfo-plus, `SCR` = `0x4233f000`).

### 1.1 La ligne de délai

| Adresse | Rôle |
|---|---|
| `0x4005979e` | fonction audio de chaque bloc (32 trames) : lissage `0x40058474(cibles)` → obj `0x8000100c`, LFO, voix, mixeur, puis `0x400567ba(sortie, obj)` (effets) |
| `0x400567ba` → `0x4005802e(obj)` | effets : délai et réverbe ; la ligne de délai est lue et écrite par l'eDMA (TCD `0xfc0453c0..`), dans `0x4a400000` (512 K mots) |
| `0x400581ae` | `mvs.w 428(a0),d0` : DELAY TIME, mot k = 9 du bloc FX (piste 6) dans obj |
| `0x400581b8..0x400581c8` | d0 = ((mot + 256) × 48 000 >> 10) × 900 / tempo (`0x40149310`, BPM × 120) : (mot + 256) = 8 192 est une noire, le pas de 256 vaut 1/128 de mesure |
| `0x400581cc..0x400581d4` | borne : `cmpi.l #384000` → 384 000 échantillons = 8,000 s |
| `0x400581da..0x400581fc` | filtre de la longueur (Q12, `0x8000b980`) : x' = (255 × (x >> 1) + 32 × (cible >> 1)) / 128 par bloc ; partie entière en `0x8000b984` = l'écart de lecture |
| `0x40058200..0x4005827c` | adresse de lecture de l'eDMA = ((écriture `0x8000b988` - écart) & 0x7ffff) × 8 + `0x4a400000` |

Le filtre s'arrête un peu court : venant d'une ligne plus courte, l'écart se fige 16 échantillons sous la cible
(17 pour une cible impaire, que `lsr #1` coupe), et sur la cible en venant d'une plus longue `[FAIT en émulation]`.
C'est le comportement d'origine, gardé : 0,33 ms.

### 1.2 Où le délai est rangé

| Où | Quoi |
|---|---|
| kit en mémoire + 628 | bloc FX : 33 mots k, DELAY TIME en k = 9 (kit + 646) ; recopié dans les cibles par `0x40058a64` (66 o en `0x8000173a`) |
| `0x4005b266(enregistrement + 632, kit + 628)` | sauvegarde du bloc FX : chaque mot à sa place (table `0x4010ee04`), **16 bits** ; DELAY TIME en + 6 de l'enregistrement (fichier kit + 638) |
| `0x4005b21a(kit + 628, enregistrement + 632)` | chargement : k = 9 ← + 6, 16 bits |
| descripteur 37 (`0x4010e4f8`) | Delay Time, groupe 0xb, k = 9, 0..0x7f00, défaut 0x1700 ; potard 15 de la page des paramètres (FUNC + 15 = Delay Fdbk) |

Les « Kit +710 » de l'analyse sont des octets des pistes du pattern (`0x4005c080`, conversion de formats), sans
rapport avec le délai.

### 1.3 Le LFO

| Adresse | Rôle |
|---|---|
| `0x40091ab2(obj, tempo, masque)` | les 6 LFO ; a4 = mots de la piste + 22 ; SPD = mot k = 1 (`-6(a4)`), MULT = octet fort de k = 2 |
| `0x40091ae8..0x40091b3c` | pas = (SPD - 16 384) × 2 × T >> (11 - m) ; m = MULT borné à 0..23 ; pour m > 11 : m - 12 et T = 14 400 (120 BPM, multiplicateurs libres), sinon T = le tempo |
| `0x40091b6e..0x40091be4` | phase sur ± 691 200 000 : un cycle = 1 382 400 000 |
| descripteur 29 (`0x4010e338`) | LFO Speed, k = 1, 0..0x7f00, défaut 0x7000 ; potard 10 |

lfo-plus (notes/56 §3) fait tourner la même fonction pour LFO 2, 3, 4 sur un faux obj : LFO 2 y prend k = 28..32 du
vrai obj (lissé), LFO 3/4 leurs tables. LFO 2 est rangé dans le son par `lfo_pack` en SPD >> 7 (8 bits).

### 1.4 Le potard et le texte

| Adresse | Rôle |
|---|---|
| `0x4000b7d6` | tour d'un potard : get (vtable[28]), pas vtable[20] (`0x4000c264`, `fine_hook` de Model-TG), borne et rangement `0x4000b274` (0..0x7f00 du descripteur) |
| `0x4000a980(this, id, valeur, delta)` | le pas commun : `0x4000c264` y finit pour tout id sauf 32 et 42, `0x4000c466` et les autres classes aussi ; FUNC + potard (chemin fin de l'enregistrement + 80) y passe aussi |
| `0x4000a984` | `moveq #75,d0` : borne des descripteurs, **réécrite par les machines ajoutées** (0x50 .. 0x6e) |
| `0x4004dfda` | texte de DELAY TIME : valeur + 256, puis le formateur `0x40a70708` (valeur >> 8) |
| `0x4004e00e` | texte de LFO SPEED : valeur - 16 384, même formateur |

Le lissage `0x40058474` rapproche **tous** les mots d'obj de leurs cibles (même disposition : k en 14 + 66t + 2k) ;
seul k = 4 est recopié brut. Pendant un glissement, l'octet bas d'un mot lissé prend n'importe quelle valeur, bit 7
compris : le mode ne peut donc pas se lire dans obj.

## 2. Conception

### 2.1 Le mot

| Paramètre | FREE | SYNC |
|---|---|---|
| DELAY TIME | mot d'origine, n - 1 << 8 (n = 1..128) | `H << 8 \| 0x80 \| idx`, idx 0..20, H = la valeur FREE la plus proche - 1 (0..126) |
| LFO SPEED (1, 2, 3, 4) | mot d'origine | `C << 8 \| 0x80`, C = idx 0..23, + 0x40 à l'envers |

- Bit 7 = SYNC. Le potard, les p-locks et le MIDI d'origine écrivent des multiples de 256 : FREE.
- Délai, octet fort = la valeur FREE la plus proche : un OS sans ce tweak joue un délai à 1/128 de note près
  (l'octet bas ajoute 0,5 à 0,6 pas de 1/128).
- LFO, l'index dans l'octet fort : `lfo_pack` de lfo-plus (SPD >> 7) garde l'octet fort et le bit 7, donc LFO 2 en
  SYNC est sauvé sans toucher à lfo-plus. Un OS sans ce tweak y lit une autre vitesse.
- Tous les mots restent dans 0..0x7f00 (H ≤ 0x7e, C ≤ 0x57) : la borne de `0x4000b274` ne les touche pas.

### 2.2 Les valeurs de notes (lu = 1/1536 de mesure)

| idx | nom | mesure | lu | délai à 120 BPM | délai à 50 BPM | délai | LFO |
|---|---|---|---|---|---|---|---|
| 0 | 1/128 | 1/128 | 12 | 750 | 1 800 | ✓ | ✓ |
| 1 | 1/96 | triolet de 1/64 | 16 | 1 000 | 2 400 | ✓ | ✓ |
| 2 | 1/64 | 1/64 | 24 | 1 500 | 3 600 | ✓ | ✓ |
| 3 | 1/48 | triolet de 1/32 | 32 | 2 000 | 4 800 | ✓ | ✓ |
| 4 | 1/32 | 1/32 | 48 | 3 000 | 7 200 | ✓ | ✓ |
| 5 | 1/24 | triolet de 1/16 | 64 | 4 000 | 9 600 | ✓ | ✓ |
| 6 | 1/16 | 1/16 | 96 | 6 000 | 14 400 | ✓ | ✓ |
| 7 | 1/12 | triolet de 1/8 | 128 | 8 000 | 19 200 | ✓ | ✓ |
| 8 | 1/8 | 1/8 | 192 | 12 000 | 28 800 | ✓ | ✓ |
| 9 | 1/6 | triolet de 1/4 | 256 | 16 000 | 38 400 | ✓ | ✓ |
| 10 | 3/16 | 1/8 pointée | 288 | 18 000 | 43 200 | ✓ | ✓ |
| 11 | 1/4 | 1/4 | 384 | 24 000 | 57 600 | ✓ | ✓ |
| 12 | 1/3 | triolet de 1/2 | 512 | 32 000 | 76 800 | ✓ | ✓ |
| 13 | 3/8 | 1/4 pointée | 576 | 36 000 | 86 400 | ✓ | ✓ |
| 14 | 1/2 | 1/2 | 768 | 48 000 | 115 200 | ✓ | ✓ |
| 15 | 2/3 | triolet de ronde | 1 024 | 64 000 | 153 600 | ✓ | ✓ |
| 16 | 3/4 | 1/2 pointée | 1 152 | 72 000 | 172 800 | ✓ | ✓ |
| 17 | 1 BAR | 1 | 1 536 | 96 000 | 230 400 | ✓ | ✓ |
| 18 | 4/3 | triolet de 2 mesures | 2 048 | 128 000 | 307 200 | ✓ | ✓ |
| 19 | 3/2 | mesure pointée | 2 304 | 144 000 | 345 600 | ✓ | ✓ |
| 20 | 2 BAR | 2 | 3 072 | 192 000 | 384 000 (460 800 demandés) « 2 BAR > » | ✓ | ✓ |
| 21 | 4 BAR | 4 | 6 144 | | | | ✓ |
| 22 | 8 BAR | 8 | 12 288 | | | | ✓ |
| 23 | 16 BAR | 16 | 24 576 | | | | ✓ |

Les 16 valeurs du retrig (idx 2..17), avec leurs noms de `rtg_names`. Le délai s'arrête à 2 BAR : la ligne en
contient 2 dès 60 BPM ; 1 BAR tient jusqu'à 30 BPM (384 000 tout juste). Au tempo maximal de `tempo-max` (546 BPM),
1/128 vaut 165 échantillons.

### 2.3 « Le plus proche »

- FREE → SYNC : la valeur de note de rapport le plus proche (x² comparé aux produits de voisins), délai : x = 12 n ;
  LFO : x = 49 152 × tempo / |pas d'origine| (le pas que l'OS ferait avec ce SPD et ce MULT, au tempo du moment).
  SPD 0 (immobile) → 16 BAR.
- SYNC → FREE : délai, n = arrondi(lu / 12), 1..128 ; LFO, la vitesse |v| = 1..63 (64 à l'envers) dont le cycle est le
  plus proche au rapport, avec le MULT et le tempo du moment.

## 3. Accroches, place et conflits

| Adresse | D'origine | Devient | Rôle |
|---|---|---|---|
| `0x400581ae` | `mvs.w 428(a0),d0 ; lea 0x40149310,a0` | `jsr ts_audio ; nop ; nop` | longueur de la ligne |
| `0x400584f6` | `move.l #0x8000100c,d0` | `jsr ts_smooth` | fin du lissage |
| `0x40091b38` | `move.w 6(a4),d3 ; asr.l d2,d7` | `jsr ts_lfo` | pas de phase des LFO |
| `0x4000a986` | `movem.l d2-d7/a2-a3,(sp) ; movea.l 48(sp),a2` | `jsr ts_hook ; nop` | pas d'un potard, après la borne réécrite |
| `0x4004dfda` | `move.l #256,d0` | `jmp ts_dfmt` | texte de DELAY TIME |
| `0x4004e00e` | `move.l #-16384,d0` | `jmp ts_lfmt` | texte de LFO SPEED |

- `ts_smooth` : une cible SYNC (DELAY TIME, LFO 1 SPD, LFO 2 SPD) est recopiée brute dans obj, et notée dans `tsf`
  (bit t : LFO 1 de la piste t ; bit 6 : délai). `ts_audio` et `ts_lfo` (sur les mots de l'OS) lisent `tsf`, pas le
  mot lissé : FREE reste le code d'origine au bit près, glissements compris. Le faux obj de lfo-plus ne montre que
  le mot : pour LFO 2 en FREE, le bit 7 du mot lissé est effacé (au plus 127/32 768 de SPD pendant un glissement) ;
  LFO 3/4 viennent de tables jamais lissées.
- `ts_hook` : `0x4000a984` (la borne) est réécrit par 129 tweaks des machines ajoutées : l'accroche est juste après,
  et le pas d'origine est refait avec l'opérande vivant de `0x4000a984` (`mvs.b 0x4000a985`).
- SETTINGS : `set_held` et `mod_used` de Model-TG (symboles ajoutés à `30-model-tg*.json` par `gen_model_tg.py`,
  `TS_SYMBOLS` ; le code de Model-TG ne change pas) : le tweak demande `model-tg-st`.
- Place : 1 627 o dans 11 masques 48 × 22 libérés (`0x40183408` .. `0x40192a24`, les derniers de la liste :
  les branches ouvertes prennent les premiers). Pas de mémoire de travail (`tsf` dans un masque, à 0 au démarrage).
- `check_overlaps.py` : aucune écriture partagée avec les 283 autres tweaks.

## 4. Le tweak

28 écritures : 11 masques et leurs 11 redirections, 6 accroches (`tsf` est dans un masque). Aucune charge utile,
aucun symbole d'un autre tweak déplacé : Model-TG, lfo-plus et les moteurs du Syntakt sont inchangés.

## 5. Preuve en émulation `[FAIT en émulation]`

`tools/emu/test_tempo_sync.py --cycles … --with <l'OS> --syntakt …` : TOUT OK avec l'OS entier (Model-TG, lfo-plus,
moteurs du Syntakt, tempo-max…) et avec Model-TG seul.

| Cas | OS sans le tweak | Avec |
|---|---|---|
| Délai FREE : 134 mots lissés (octet bas jusqu'à 0xff) × 30, 50, 97, 120, 300 BPM | — | longueur, filtre et écart identiques, bloc pour bloc |
| 1/4 à 120 BPM (mot 31 << 8 contre SYNC 1/4) | cible 24 000, écart 23 984 depuis 0, 24 000 depuis 48 000 | idem |
| SYNC 1/8 | (11/128 au mieux : 8 250 pour un triolet) | 12 000 à 120 BPM, 14 845 à 97 BPM ; écart de la ligne 11 984 / 14 828 |
| SYNC 1/12 (triolet de croches) | — | 8 000 / 9 896 ; ligne 7 984 / 9 880 |
| SYNC 3/16 (croche pointée) | — | 18 000 / 22 268 ; ligne 17 984 / 22 252 |
| SYNC 1/4, 1 BAR | — | 24 000 / 29 690 ; 96 000 / 118 762 ; rapport 97/120 à 3·10⁻⁵ près (arrondi à l'échantillon) |
| SYNC 2 BAR à 50 BPM | — | 460 800 demandés, 384 000 (8,000 s) ; texte « 2 BAR > » ; 60 BPM : 384 000 tout juste, sans « > » |
| Lissage, cibles FREE au hasard, 40 blocs | — | mots identiques (LFO 2 SPD : bit 7 effacé) |
| Lissage, cibles SYNC | — | dans obj dès le 1er bloc |
| LFO 1 FREE au hasard, retrigs, 2 tempos, 360 blocs | — | mots et état identiques |
| LFO 1 SYNC, 6 valeurs × MULT 1, 16, 8 libre × 120 et 97 BPM | — | pas = ± 49 152 × tempo / lu : 1 BAR à 120 BPM = 3 000 blocs = 2 000 ms ; 1/12 = 250 blocs = 166,67 ms ; à l'envers, pas négatif |
| LFO 2 (lissé), LFO 3/4 (tables) SYNC | — | mêmes pas |
| Potard FREE sans SETTINGS, DELAY TIME et LFO SPEED, 43 valeurs × 6 tours | — | pas d'origine |
| Autres paramètres (DEP, FDBK, PTCH, Start), SETTINGS tenu ou non | — | pas d'origine, `mod_used` intact |
| SETTINGS + droite, délai FREE 1..128 ; + gauche, les 21 SYNC | — | modèle Python exact ; ex. 11 → 1/12, 16 → 1/8, 24 → 3/16, 128 → 1 BAR ; 1/12 → 11, 1 BAR → 128 ; `mod_used` = 1 |
| SETTINGS + droite puis gauche, LFO, 128 vitesses × 8 MULT × 2 tempos | — | 2 048 cas exacts ; MULT 8 : +16 → 1 BAR, -64 → -1/4 |
| SYNC, un cran par valeur, bornes ; -16 BAR + 1 cran = +16 BAR | — | exact |
| Texte FREE (131 valeurs) | — | identique |
| Texte SYNC ; police de la fenêtre de valeur | — | 1/128 .. 2 BAR, -1/128 .. -16 BAR ; 7 caractères au plus (tampon de 16) ; chaque signe existe |
| Kit FX : sauvegarde → chargement | — | les 21 mots SYNC gardés, 16 bits |
| Son : LFO 1 SPD (48 valeurs), LFO 2 par lfo-plus | — | gardés |
| Coût par bloc | délai 54, lissage + LFO 3 090 | FREE +7 et +120 instructions ; SYNC +7 et +216 |

Non couvert : l'écran principal de la page des paramètres (le texte vient du même formateur ; sa largeur de case
n'est pas mesurée), le maintien réel de SETTINGS (seule la variable de Model-TG est posée), l'eDMA lui-même (l'adresse
qu'on lui donne est vérifiée), les p-locks et le MIDI (ils écrivent des valeurs FREE).

## 6. Limites

- Les p-locks de ces paramètres gardent des valeurs FREE (la rangée de p-locks ne range que l'octet fort).
- En SYNC, MULT du LFO n'a plus d'effet ; FUNC + SPD passe aussi d'une valeur de note à l'autre.
- Une valeur NRPN avec un octet bas ≥ 0x80 (14 bits) serait lue comme SYNC `[HYP]` : chemin MIDI non relu.
- Un OS sans ce tweak joue un délai SYNC à 1/128 de note près, et un LFO SYNC à une autre vitesse.

## 7. À essayer sur la machine

1. DELAY TIME (potard 15) à 24 : SETTINGS tenu, un cran à droite → « 3/16 » ; relâcher SETTINGS : pas de Config
   Menu. Tourner seul : 1/8, 1/6, 1/4… Écouter : les répétitions tombent sur la grille.
2. Changer le tempo pendant la lecture : le délai suit, glisse sans clic. 50 BPM, 2 BAR : « 2 BAR > », 8 s.
3. SETTINGS + gauche : retour à la valeur d'origine la plus proche (3/16 → 24).
4. LFO SPEED (potard 10) : SETTINGS + droite → la valeur de note la plus proche ; « -1/4 » tourne à l'envers ; changer
   MULT ne change rien ; pages LFO 2, 3, 4 pareil.
5. Sauver le pattern, en charger un autre, revenir : les valeurs de notes reviennent. Un ancien projet : identique.
6. Vérifier que la case de la page des paramètres affiche « 1 BAR », « 3/16 », « -16 BAR » sans déborder.

## 8. Mise à jour du 29/10/2026 : la typographie des valeurs de note (petite police)

**Le problème, mesuré et non plus à l'œil.** La fenêtre de valeur (`0x4001d818`, slot 144 de `ParameterPageView`)
dessine son texte avec la grande police 16×22 de l'OS (`0x401429ec`) : elle n'a que ~60 px de plaque (x 64..124) et
les valeurs de note débordent. Largeurs relevées à l'écran, texte seul, x 0x60 centré, dans le vrai `DRAW_TEXT`
(`0x40071a04`) :

| texte | grande 16×22 | petite 5×9 (`0x40140ab0`) |
|---|---|---|
| `3/16` | 48 px | 23 px |
| `1 BAR` | 65 px | 29 px |
| `-16 BAR` | 82 px (dès x 38, hors plaque) | 39 px |

D'où, sur la machine, « 1 BAR » et « -16 BAR » qui débordent de la case (constat du propriétaire).

**Ce qui a été fait.** La petite police 5×9 de l'OS (`0x40140ab0`, une *face* du même format que la grande : `0x40072260`
en construit l'objet en 8 octets) est utilisée **en SYNC seulement** ; en FREE la fenêtre reste exactement celle de
l'OS. Deux accroches dans la fenêtre, et un drapeau :

- `0x4001d8ae` (`move.l sp,d4 ; add.l #60,d4` → `jsr ts_face ; nop`) : la face a été empilée juste avant
  (`pea 0x401429ec` en `0x4001d8a8`) ; `ts_face` la remplace **en 4(sp)** — l'adresse de retour du `jsr` est en 0(sp),
  erreur qui a coûté un plantage pendant la mise au point — par la petite, puis refait `d4 = sp + 4 + 60` comme le
  stock.
- `0x4001d8d6` (`jsr 0x40071a04` → `jsr ts_draw`) : la ligne de 9 px se poserait en haut de la case de 22 px ;
  `ts_draw` fait `y + 6` (`pea 0x22` empilé en 16(sp)), soit y 40..48, centré sur la ligne de la grande (34..55).
- Le drapeau `small` est posé par `ts_dfmt` / `ts_lfmt` (1 en SYNC, 0 en FREE) : ces formateurs sont ceux que la
  fenêtre appelle juste avant (vt[60] du descripteur, `0x4001d8a2`), donc il est toujours frais, et `ts_draw` le
  remet à zéro pour la fenêtre suivante. Aucun autre paramètre ne change de police.

Place : +81 o, tous dans les 12 masques déjà réservés par le mod (1708 o au total, 12 masques de 192 o).

**Preuve `[FAIT en émulation]`** — `tools/emu/test_tempo_sync.py`, `TOUT OK` seul et avec les quatorze autres tweaks
de `os.json` :
- les 69 valeurs de note (21 du délai, 48 du LFO) sont tirées par le vrai `0x4001d818` et comparées à ce que l'OS
  dessine du même texte, petite police, `y + 6` : chaque pixel du texte attendu est là, 9 px de haut, y 40..48, dans
  x 64..124 ; le plus large fait 39 px pour une plaque de 61 ;
- en FREE, la fenêtre est **pixel pour pixel** celle de l'OS (délai et LFO, 4 valeurs chacun) ;
- le texte des formateurs, les caractères, le potard, le stockage, le coût : inchangés et verts.

**Point ouvert, à vérifier sur la machine** : avec les moteurs Syntakt, la fenêtre de valeur passe par
`0x4000a6b0` → `0x4004df40`, qui cherche un enregistrement d'interface par la valeur (`0x40a71754 + 100 × min(valeur,
76)`) puis lit les champs de cet enregistrement ; pour un mot de note (`0x8000 | idx`) ou une grande valeur FREE
(`0x7f00`) l'OS lit alors de la RAM qui se trouve être celle de la charge utile des moteurs (`0x46700000`, nulle au
démarrage) : l'émulateur d'interface ne la projette pas, la lecture y échoue, et la vérification de la fenêtre est
donc `SKIP` dans la passe combinée. Ce chemin existait avant cette mise à jour (même échec avec le tweak du 26/10) ;
sur la machine il lit des zéros. À contrôler : la case de DELAY TIME en SYNC avec tout l'OS doit afficher la valeur de
note, sans jauge parasite.

**Retour machine du 29/10 (soir), puis passage à la police 6×10.** Sur la machine (OS complet, `os-full5`) : les valeurs
tiennent dans la case et il n'y a pas de jauge parasite, mais la 5×9 a été jugée trop petite. La police de la case
« LFO 2-3-4 » (la grande 16×22) n'est pas possible : 28 valeurs sur 56 seulement y tiennent (les fractions sans
signe), et elle n'a pas tous les glyphes. Les faces de l'OS, mesurées dans le vrai `DRAW_TEXT` sur les 56 textes :

| face | `3/16` | `1 BAR` | le plus large (`-16 BAR`, `2 BAR >`) | hauteur |
|---|---|---|---|---|
| 5×9 `0x40140ab0` | 23 px | 29 px | 39–41 px | 9 px |
| **6×10 grasse `0x40143d28`** | — | — | **48 px** | 10 px |
| 7×9 `0x4014120c` | 31 px | 39 px | 54 px (x 69..123, collé au bord) | 9 px |
| 16×22 `0x401429ec` | 48 px | 65 px | 82 px | 22 px |

Choix du propriétaire : **6×10 grasse** (`FACE_SMALL`). Le `y + 6` de `ts_draw` est inchangé : la ligne de 10 px
(34..43) devient 40..49, centrée sur la ligne de la grande (34..55). Tous les glyphes utilisés (`0-9 / - B A R >`)
existent dans cette face. Preuve : `test_tempo_sync.py` `TOUT OK` seul (69 valeurs, 10 px, y 40..49, dans x 64..124,
le plus large 48 px pour 61) et avec tout `os.json` (fenêtre `SKIP` comme plus haut).
