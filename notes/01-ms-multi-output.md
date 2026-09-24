# 01 · ms-multi-output : le mod 6 canaux existant

Source : <https://github.com/scottmetoyer/ms-multi-output>, commit `3edf617` (19/09/2026), licence MIT.
Contenu : `README.md`, `build.py`, `patch/cycles6.json`, `patch/rung10.json`, 4 sources ASM (`patch/*.s`),
`tools/flash.py`, `tools/analyse_dupes.py`, `setup.sh`.

---

## 1. Ce que fait le mod

- **`[FAIT]`** Les 6 pistes partent **chacune sur un canal USB** : canal 1 = piste 1 … canal 6 = piste 6.
  Format : 48 kHz, 32 bits, USB High Speed, capture seule. La machine s'annonce toujours en OS `1.13`.
- **`[FAIT]`** Le mix stéréo **n'est plus envoyé en USB** : il faut mixer les stems dans le DAW.
- **`[FAIT]`** Trois builds sont disponibles :

| Cible | Pour | Table | Sortie | Testé |
|---|---|---|---|---|
| `samples` | Model:Samples | `patch/rung10.json` (41 runs) | `ms-multi-output.syx` | ✅ sur matériel |
| `cycles` | **Model:Cycles** | `patch/cycles6.json` (29 runs) | `mc-multi-output.syx` | ⚠️ **jamais flashé sur un vrai M:C** |
| `cycles-crossflash` | M:S qui devient un M:C 6 canaux | `patch/cycles6.json` | `mc-on-ms-multi-output.syx` | ✅ sur matériel |

- **`[FAIT]`** `cycles` et `cycles-crossflash` contiennent **exactement la même section 3 patchée**.
  Seul le conteneur `.syx` diffère : `0x11` (Cycles) ou `0x0F` (Samples).
  Le code est donc validé sur matériel. Ce qui n'a jamais été essayé, c'est l'appairage conteneur `0x11` / vrai Model:Cycles.
  C'est pourtant l'appairage naturel, celui des mises à jour officielles.

## 2. Nature des stems (à connaître avant de mixer)

| Propriété | Détail | Source |
|---|---|---|
| **Mono** | Prélevé avant l'étage de sommation, où le pan est appliqué sous forme de coefficient. **Le pan n'est pas dans les stems** ; il faudrait 12 canaux pour l'y mettre. | README |
| **LEVEL de piste** | Inclus et linéaire sur le M:S. **Non vérifié sur le M:C**. | README |
| **Delay / Reverb** | **Absents** : ils sont « dérivés du bus principal sommé », pas de chaque piste. | README |
| **Distorsion** | Un LEVEL élevé distord, sur les stems comme sur la sortie analogique. THD sur un sinus : ~10 % à LEVEL 100, ~23 % à 127. C'est la voie de la voix qui sature, déjà présente en stock. | README |
| **Pistes mutées** | Un léger DC (~−129 dBFS), pas un zéro exact : le verdict `CONSTANT/DC` est normal. | `analyse_dupes.py` |

> Lien avec le forum (dossier §5.1 et §5.3) : la distorsion par piste au-delà de ~70 et la saturation du bus de mix
> sont cohérentes. Les stems prélevés **avant** la somme n'ont pas la saturation croisée entre pistes du mix interne.

## 3. Principe technique (résumé du README, `[FAIT]`)

> Le moteur audio rend chaque piste dans son propre bloc mono en SRAM (6 blocs de 32 trames),
> puis les somme en stéréo. Le « feeder » USB d'origine lit le buffer stéréo sommé.

Le patch fait trois choses :
1. il **élargit les descripteurs USB audio de 2 à 6 canaux**, ainsi que le **`MaxPacketLength` du queue-head (dQH)** de l'endpoint.
   *« missing that one constant silently breaks the stream — it is the single most important value here »* ;
2. il **redimensionne le ring de transfert** pour 24 octets par trame (6 canaux × 4 octets) ;
3. il **remplace la boucle de copie du feeder** par un stub qui entrelace directement les 6 blocs de piste.

Les stubs sont logés dans l'**espace des descripteurs USB inutilisé sur un hôte High Speed**, après redirection de la table des modes USB.
Conséquence : `CONFIG → UPGRADE` par USB ne marche plus, car les deux descripteurs du bootloader ont été réutilisés.

## 4. Table de patchs Model:Cycles (`cycles6.json`) décodée

Offsets = offsets de fichier dans `section_3_MAIN_OS.bin` ; `VA = off + 0x40000400`.
Le décodage vient de mon désassemblage (capstone M68K) des octets `expect` et `write`.

### 4.a Pilote USB (adresses identiques sur M:S et M:C)

| VA | Stock → patch | Décodage | Rôle | Certitude |
|---|---|---|---|---|
| `0x4000253b` | `0f` → `03` | 2ᵉ octet d'une instruction (moveq ?) | constante 15 → 3 dans l'init du pilote | `[HYP]` rôle inconnu |
| `0x40002564` | `9b80` → `9e00` | déplacement ou immédiat 16 bits | **+0x280 = 640 o = (8×192) − (16×56)** : probablement la borne de fin du ring | `[HYP]` forte (l'arithmétique colle) |
| `0x400027b3` | `0f` → `07` | masque | masque d'index du ring : **profondeur 16 → 8** | `[HYP]` forte |
| `0x400027ce` | `e788` → `ed88` | `lsl.l #3,d0` → `lsl.l #6,d0` | calcul du stride (priming) | `[FAIT]` décodage |
| `0x400027d3` | `30 ed8a 9480` → `90 ef8a d480` | imm `0x30`→`0x90` ; `lsl.l #6,d2`→`#7` ; `sub.l d0,d2`→`add.l d0,d2` | **48 → 144 o par transfert** ; stride = (x<<6)−(x<<3) = **56** → (x<<7)+(x<<6) = **192** | `[FAIT]` décodage, `[HYP]` pour l'octet `0x30` |
| `0x400027e8` | bloc de 22 o → `jmp 0x4019b136` + nops | voir stub **prime6** | amorçage d'un dTD : 48 → 144 o | `[FAIT]` |
| `0x4000281f` | `0b` → `06` | ? | constante 11 → 6 | `[HYP]` rôle inconnu |
| `0x400029b9` | `0f` → `07` | masque | masque d'index du ring (2ᵉ site) | `[HYP]` forte |
| `0x400029d2` | `lsl.l #3,d5 ; lsl.l #6,d1 ; sub.l d5,d1` → `lsl.l #6,d5 ; lsl.l #7,d1 ; add.l d5,d1` | | base de case = index × stride : **56 → 192** | `[FAIT]` |
| `0x400029e4` | `lsl.l #3,d0 ; move.l 0x404a05e8,d1 ; add.l d0,d1` → `jmp 0x4019b244` | voir stub **dstoff6** | offset destination = trames × **8 → 24** | `[FAIT]` |
| `0x40002a06` | boucle de copie stéréo (24 o) → `jmp 0x4019b1e0` | voir stub **tracks6** | copie du mix → entrelacement des 6 pistes | `[FAIT]` |
| `0x40002a42` | `moveq #19,d1 ; movea.l d0,a0 ; move.l d4,d0 ; lsl.l d1,d4 ; lsl.l #3,d0` → `jmp 0x4019b182` | voir stub **token6** | longueur et token du dTD : trames × **8 → 24** | `[FAIT]` |
| `0x40002ceb` | `38` → `a8` | octet d'un immédiat | **`MaxPacketLength` du dQH : 56 → 168** (7 trames × 8 → 7 × 24) | `[FAIT]` valeur, `[HYP]` encodage exact |

Code d'origine désassemblé aux hooks, utile pour comprendre le contrat :

```asm
; 0x400027e8  (priming d'un dTD, a2 = dTD)          -> reprise 0x400027fe
move.l  #0x00300080,d0      ; token : 48 octets << 16 | Active(0x80)
moveq   #0x30,d1            ; 48
move.l  d0,4(a2)            ; dTD.token
move.l  #0xdead0001,(a2)    ; dTD.next = terminateur (bit T = 1)
move.l  d1,32(a2)           ; champ privé du driver : longueur (lu par 0x40003f10)

; 0x400029e4  (pointeur destination)                -> reprise 0x400029ee
lsl.l   #3,d0               ; trames * 8 (stéréo 32 bits)
move.l  0x404a05e8,d1       ; SLOT_BASE (Cycles)
add.l   d0,d1

; 0x40002a06  (boucle de copie du mix stéréo)       -> sortie 0x40002a26
movea.l 36(sp),a0           ; SOURCE = buffer stéréo sommé   <-- utile pour un mode 8 canaux
movea.l d1,a1               ; destination (ring USB)
clr.l   d1
adda.l  d5,a0               ; + offset
loop: cmp.l d1,d0 ; ble 0x40002a26
      move.l (a0)+,d5 ; addq.l #1,d1
      byterev d5            ; .short 0x02c5 : big-endian -> little-endian USB
      move.l d5,(a1)+ ; bra loop

; 0x40002a42  (token et longueur du dTD à la fin d'une case)  -> reprise 0x40002a4c
moveq   #19,d1
movea.l d0,a0               ; a0 = dTD (d0 contient le POINTEUR ici)
move.l  d4,d0               ; d0 = trames
lsl.l   d1,d4               ; d4 = (trames*8) << 16
lsl.l   #3,d0               ; d0 = trames*8
```

### 4.b Table des modes USB (`[FAIT]` valeurs, `[HYP]` sémantique)

4 entrées de **stride 0x28**. Champ pointeur (BE32) à `0x4013e544`, `…56c`, `…594`, `…5bc` (Samples : `0x4013a794` + n×0x28).

| Entrée | Pointeur stock → patch | Longueur stock → patch | Contenu stock pointé |
|---|---|---|---|
| 0 | `0x4019b23f` → `0x4019b2b6` | `0x0065` (101) → `0x0148` (328) | config **USB-MIDI seule** n°2 |
| 1 | `0x4019b1da` → `0x4019b2b6` | `0x0065` → `0x0148` | config **USB-MIDI seule** n°1 (EP bulk 512 o, donc HS) |
| 2 | `0x4019b17d` → `0x4019b2b6` | `0x004b` (75) → `0x0148` | config **CDC-ACM** n°2 (port série virtuel) |
| 3 | `0x4019b132` → `0x4019b2b6` | `0x004b` → `0x0148` | config **CDC-ACM** n°1 |

Toutes les entrées pointent désormais sur la **configuration audio+MIDI HS de 328 o** à `0x4019b2b6`.
Les 4 blobs libérés (CDC et MIDI seule) servent d'espace de code aux stubs.
`[HYP]` : les configs CDC sont celles du bootloader (upgrade USB), d'où la perte de `CONFIG → UPGRADE`.
Autre effet de bord `[HYP]` : un éventuel mode « MIDI seul » servirait lui aussi la config 6 canaux.

### 4.c Descripteur de configuration HS audio+MIDI (`0x4019b2b6`, 328 o)

| VA | Offset dans la config | Stock → patch | Champ UAC2 |
|---|---|---|---|
| `0x4019b2fa` | +68 | `02` → `06` | `bNrChannels`, probablement l'Input Terminal (offset 8 d'un IT de 17 o démarrant à +60) `[HYP]` |
| `0x4019b387` | +209 | `02` → `06` | `bNrChannels` de l'AS_GENERAL (offset 10) `[FAIT]` par cohérence |
| `0x4019b397` | +225 | `38 00` → `a8 00` | `wMaxPacketSize` (LE) de l'endpoint iso IN : **56 → 168** `[FAIT]` |

Vérification de cohérence : AS_GENERAL (16 o, `bNrChannels` à +10, puis `bmChannelConfig` sur 4 o et `iChannelNames`)
→ FORMAT_TYPE_I (6 o) → endpoint (7 o, `wMaxPacketSize` à +4). Le compte tombe juste : 209 + 6 = 215 (début de FORMAT_TYPE_I),
+ 6 = 221 (début de l'endpoint), + 4 = **225**.
`bmChannelConfig` n'est **pas modifié**, ce qui est acceptable en UAC2 : les canaux en surplus sont « non spatialisés ».

### 4.d Les 4 stubs (logés dans les blobs libérés)

| Stub | VA Cycles | Blob hôte | Appelé depuis | Reprise |
|---|---|---|---|---|
| prime6 | `0x4019b136` (`nop` d'alignement, code à `…b138`) | CDC n°1 | `0x400027e8` | `0x400027fe` |
| token6 | `0x4019b182` (`nop`, code à `…b184`) | CDC n°2 | `0x40002a42` | `0x40002a4c` |
| tracks6 | `0x4019b1e0` | MIDI n°1 | `0x40002a06` | `0x40002a26` |
| dstoff6 | `0x4019b244` | MIDI n°2 | `0x400029e4` | `0x400029ee` |

`[HYP]` Le `nop` initial de prime6 et token6 aligne le code sur 4 octets : sur le Samples, tous les stubs sont déjà alignés.
Sources ASM relogées pour le Cycles : voir [07-snippets.md](07-snippets.md#1-stubs-asm-relogés-pour-le-modelcycles-os-113).

Contrats de registres (d'après les `.s` et le désassemblage) :
- **prime6** : entrée `a2` = dTD à amorcer. Écrit `a2@(4)` = `0x00900080` (144 o, Active), `a2@(0)` = `0xdead0001`, `a2@(32)` = 144.
  *« 0x40003f10 lit ce champ pour calculer les octets transférés ; se tromper n'est pas cosmétique »*.
- **token6** : entrée `d0` = **pointeur** dTD, `d4` = trames. Sortie `a0` = dTD, `d4` = (trames×24)<<16, `d0` = trames×24.
  L'ordre compte : `a0` doit être pris depuis `d0` **avant** de recharger `d0`.
- **tracks6** : entrée `d0` = nombre de mots longs (= trames×2 dans l'échelle d'origine), `d1` = destination, `d3` = offset de trame.
  Sauvegarde et restaure `d0-d7/a0-a2` (44 o de pile). Ignore la source `sp@(36)` et `d5`.
- **dstoff6** : entrée `d0` = trames déjà présentes dans la case. Sortie `d1` = `[SLOT_BASE]` + trames×24. `d0` est mort ensuite.

## 5. Traduction d'adresses Samples ↔ Cycles (`[FAIT]`)

- **Pilote USB : mêmes adresses de code**, mais les variables diffèrent (`SLOT_BASE`).
- **Blobs de descripteurs : décalage constant `Samples = Cycles + 0x500c`**.
  Par exemple `0x4019b132` ↔ `0x401a013e`, `0x4019b2b6` ↔ `0x401a02c2`.
- **Table des modes : `Samples = Cycles − 0x3db0`** (`0x4013e544` ↔ `0x4013a794`).
- **Blocs de pistes (SRAM) : `0x80001858` (M:C) contre `0x80001b48` (M:S)**, stride `0x80` = 32 trames × 4 o.
  6 blocs occupent `0x80001858` à `0x80001b57`.

Méthode employée par l'auteur (README) : *« the Cycles port is almost entirely an address translation: the same four stubs, relocated »*.

## 6. Historique des itérations (« rungs ») et leçons

| Rung | Changement | Résultat |
|---|---|---|
| 4 | géométrie 6 canaux, 24 o/trame, stride 192 | ok, sauf l'**offset destination oublié** (resté ×16) : chevauchement et « tous les canaux identiques ». Corrigé par dstoff6. |
| 5 | stub qui lit directement les blocs de piste | base du stub final |
| 6-8 | ring de profondeur **4** (24 trames), puis copie « shadow » et décalage +12 | **~25 % de trames dupliquées** (lag 24), sonnerie « de cloche » sur les transitoires |
| 9 | masque mod-32 retiré | **jamais flashé**, à ne pas reprendre : fuite entre canaux |
| **10** | profondeur **8** (48 trames = 1,0 ms), retour au stub du rung 5, mémoire du shadow (768 o) libérée | ✅ 0,00 % de doublons |

Règles à retenir (`[FAIT]`) :
- **La profondeur du ring est porteuse.** Le moteur livre **32 trames toutes les 0,667 ms** (1500 ticks/s).
  Le ring doit en couvrir plus, sinon le contrôleur renvoie des cases périmées. 8 × 6 trames = 48 > 32 ✅, 4 × 6 = 24 < 32 ❌.
- **Le masque mod-32 est porteur.** `d3` ne commence pas forcément à 0. Sans masque, la lecture déborde du bloc n sur le bloc n+1 : fuite entre canaux.
- **`MaxPacketLength` du dQH** : l'oublier casse le flux en silence.
- **Diagnostic** : une duplication exacte à un lag = profondeur × trames par transfert signe un sous-remplissage du ring.
  Les métriques indirectes (spectre, phase) ont échoué ; l'égalité exacte d'échantillons 32 bits ne demande aucun seuil.
- **Carte des canaux** : la confirmer par un test de mute piste par piste (commit `c4900ae`).

## 7. Build (`build.py`)

- Vérifie le **SHA-256 du `.syx` d'entrée** (images officielles 1.13 exactes), puis celui de la **section 3 d'origine**.
- Contrôle les octets `expect` à **chaque** site de patch.
- Contrôle le SHA-256 de la section 3 patchée, puis celui du `.syx` final. Le packer est déterministe, d'où un build reproductible.
- Enchaînement : `elektron-firmware-tool -i <syx> -d 3 -o build/` → patch → `elektron-firmware-tool -i <container> -c 3 mainos_patched.bin -o <out>`.
- ⚠️ `setup.sh` clone `elektron-firmware-tool` **sans figer de commit** (`--depth 1`). Si l'amont change son compresseur,
  le SHA final change et `build.py` refuse (« hash differs »). **Figer le commit de l'outil** ([05](05-methode-patch.md#3-build-reproductible-modèle-à-suivre)).
- ⚠️ `tools/analyse_dupes.py` cite un `FIRMWARE.md` (« rule 12 ») **absent du dépôt**, sans doute des notes privées de l'auteur.

SHA-256 complets :
```
model-cycles_OS1.13.syx   44fe586269631a0ca7da25a3383fc6733c314809505fc3cc52f1e0ed9800640c
model-samples_OS1.13.syx  e11859b68deb7e5e3fe86ab32581212093849c4be5d3950add011eac398a2ce8
M:C section3 stock        cc99d4f0175d34d1e91d046e6ec85a5e8ab58ab9edbb3c24406acd48cb99ee98
M:C section3 patchée      65e24b50dd457444e87daea79dd41b82f61098cb8ae5cd27cbe0d91742f29555
mc-multi-output.syx       9c631bc276baaae52270a8256a0213b3c1e9076f9b192137bd6e06d887fe22f6
mc-on-ms-multi-output.syx 7929a251de4f464affecd78e8ac87918249006c1142612e91ba5f26eb5c99e52
M:S section3 stock        a351392c62ec1c6c3324a807baf46934690d54edfc76029a4b4882541cad1ab2
M:S section3 patchée      321b2ea663c67a620cac6e7b6d668319de475538ba3bee1dccda1aff9be61a69
ms-multi-output.syx       9ab326746903bd88a460914d08137e58e863d0acc814b1dc621949b009ec0169
```

## 8. Compatibilité hôte (`[FAIT]`, README)

- **macOS** : ✅ 6 canaux. Vérification : `system_profiler SPAudioDataType | grep -A4 "Model:"` doit afficher `Input Channels: 6`.
- **Windows 11** : ✅ via **FlexASIO** avec le backend MME, DirectSound ou WASAPI **partagé**, `channels = 6`, projet à **48 kHz**.
  WDM-KS est intermittent, WASAPI exclusif ne marche jamais.
  L'appareil n'expose **qu'un seul format** (48 kHz), sans repli stéréo. PortAudio annonce 44,1 kHz par défaut sous MME et DirectSound, ce qui fait échouer la négociation.
  Il arrive que l'appareil se bloque (« wedge ») : il s'énumère mais refuse de streamer. **Éteindre puis rallumer l'instrument avant tout diagnostic.**
- **Linux** : non testé (`arecord -l`).
- Les descripteurs respectent toutes les contraintes documentées de `usbaudio2.sys` : ce n'est pas un problème de descripteur.
