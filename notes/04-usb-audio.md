# 04 · USB audio du Model:Cycles : pilote, descripteurs, ring, bande passante

Sources : ms-multi-output (README, `.s`, tables de patch), mon décodage des octets. La connaissance générale USB 2.0 / UAC2 / EHCI est signalée comme telle.

---

## 1. Contrôleur et structures (`[HYP]` forte)

Le vocabulaire du dépôt (*queue-head*, `MaxPacketLength`, dTD, *token*, bit Active `0x80`, terminateur `0xdead0001`)
correspond au **contrôleur device de type ChipIdea/ARC** (dQH/dTD, famille « EHCI device »). C'est celui qu'intègrent les ColdFire
MCF5441x (USB OTG) et beaucoup de SoC Freescale/NXP.

**dTD** (*transfer descriptor*), connaissance générale :
```
+0x00  next dTD pointer      bit0 = T (terminate)      -> 0xdead0001 = "pas de suivant"
+0x04  token                 bits30:16 = total bytes, bit15 = IOC, bits11:10 = MultO, bits7:0 = status (0x80 = Active)
+0x08..+0x18  buffer page pointers 0..4
+0x20  [spécifique Elektron] longueur du transfert, relue par 0x40003f10 pour calculer les octets transférés
```
**dQH** (*queue head*) : mot de capacités avec `MaxPacketLength` en bits 26:16 (11 bits, ≤ 1024), `Mult` en bits 31:30 et IOS en bit 15.
Le patch `0x40002ceb` (`0x38` → `0xa8`) modifie le `MaxPacketLength` de l'endpoint audio IN.

## 2. Géométrie du flux : d'origine et patché (`[FAIT]` sauf mention)

| Grandeur | Stock (stéréo) | Patch 6 canaux | Formule |
|---|---|---|---|
| Canaux | 2 | 6 | N |
| Octets par trame | 8 | 24 | 4·N (32 bits) |
| Trames par micro-trame HS (125 µs) | 6 | 6 | 48000 / 8000 |
| Octets par transfert (token dTD) | 48 (`0x30`) | 144 (`0x90`) | 6 · 4N |
| `wMaxPacketSize` / `MaxPacketLength` | 56 (`0x38`) | 168 (`0xa8`) | 7 · 4N (1 trame de marge pour l'adaptation de débit) |
| Stride d'une case du ring | 56 | 192 | ≥ 7·4N, choisi « shift-friendly » |
| Profondeur du ring | 16 (masque 15) | 8 (masque 7) | `[HYP]` forte |
| Taille du ring | 896 o (`0x380`) | 1536 o (`0x600`) | profondeur × stride |
| Capacité du ring | 96 trames (2 ms) | 48 trames (1 ms) | profondeur × 6 |

**Contrainte temporelle (`[FAIT]`)** : le moteur produit **32 trames d'un coup toutes les 0,667 ms**, l'USB en consomme 6 toutes les 125 µs.
**Capacité du ring > 32 trames**, sinon les cases périmées sont renvoyées (doublons exacts au lag = capacité).
Profondeur 4 (24 trames) : ❌ 25 % de doublons. Profondeur 8 (48 trames) : ✅.

## 3. Descripteurs

- **Format** : USB Audio Class 2.0, un seul format de capture (**48 kHz, sous-trame de 4 o / 32 bits**), plus des jacks USB-MIDI dans la même configuration.
  Pas de repli stéréo ni 44,1 kHz (`[FAIT]` README).
- **Blobs d'origine** : voir [01 §4.b](01-ms-multi-output.md#4b-table-des-modes-usb-fait-valeurs-hyp-sémantique).
  CDC-ACM ×2 (75 o), USB-MIDI seule ×2 (101 o, EP bulk 512 o), audio+MIDI HS (328 o, `0x4019b2b6`).
- Décodage de la config USB-MIDI d'origine (blob `0x4019b1da`, `[FAIT]`) :
  ```
  09 04 00 00 00 01 01 00 00        Interface 0 : Audio Control (sans endpoint)
  09 24 01 00 01 09 00 01 01        AC header (bcdADC 1.00, 1 interface MS)
  09 04 01 00 02 01 03 00 00        Interface 1 : MIDIStreaming, 2 endpoints
  07 24 01 00 01 41 00              MS header
  06 24 02 01 01 00 / 06 24 02 02 02 00        MIDI IN jacks (embedded, external)
  09 24 03 01 03 01 02 01 00 / 09 24 03 02 04 01 01 01 00   MIDI OUT jacks
  09 05 01 02 00 02 00 00 …         EP 0x01 OUT bulk, wMaxPacketSize 512 (High Speed)
  ```
- **La config audio HS de 328 o n'est connue que par 3 octets** (voir [01 §4.c](01-ms-multi-output.md#4c-descripteur-de-configuration-hs-audiomidi-0x4019b2b6-328-o)).
  **`[À FAIRE]`** La dumper et la décoder entièrement depuis l'image (snippet dans [07](07-snippets.md#4-dumper-la-table-des-modes-usb-et-les-descripteurs-à-tester)).
- **Conséquence du patch `[HYP]`** : les configurations Full Speed et CDC sont écrasées. **Un hôte (ou un hub) Full Speed seul n'est plus supporté** ;
  `CONFIG → UPGRADE` par USB est perdu (`[FAIT]` README).
  La variante `6ch-usbup` loge les stubs dans une cave et laisse ces configurations d'origine ([13](13-6ch-upgrade-usb.md)).

## 4. Bande passante : l'USB n'est pas le facteur limitant

En High Speed isochrone, un endpoint accepte jusqu'à 1024 o par micro-trame (3 × 1024 en *high-bandwidth*). Avec 7 trames × 4N octets :

| Variante | Canaux | Octets/µtrame max | Marge | Stride du ring proposé | Ring (profondeur 8) |
|---|---|---|---|---|---|
| actuel | 6 (pistes mono) | 168 | ✅ | 192 = (x<<7)+(x<<6) | 1536 o |
| 6 pistes + mix | 8 | 224 (`0xE0`) | ✅ | 256 = x<<8 | 2048 o |
| 6 pistes stéréo | 12 | 336 (`0x150`) | ✅ | 384 = (x<<8)+(x<<7) | 3072 o |
| 6 stéréo + mix | 14 | 392 (`0x188`) | ✅ | 448 = (x<<8)+(x<<7)+(x<<6) | 3584 o |
| 6 stéréo + FX + mix | 16 | 448 (`0x1C0`) | ✅ | 512 = x<<9 (compteur en registre) | 4096 o |

Les vraies contraintes sont ailleurs :
- **la RAM libre** pour agrandir le ring : la zone après `0x…9e00` n'est pas prouvée libre ;
- **l'espace de code** : les blobs libérés font ~350 o au total ;
- **le temps CPU dans le feeder** : environ 5 instructions par échantillon, soit ~1,5 M instructions/s pour 6 canaux, moins de 1 % de 385 MIPS.
  Le coût reste faible, mais tout s'exécute **dans le contexte d'interruption du pilote USB** `[HYP]`, donc sans rien de bloquant ;
- **la compatibilité hôte** : Windows impose 48 kHz et FlexASIO ; au-delà de 255 o, `wMaxPacketSize` s'écrit sur 2 octets LE.

## 5. Recette : changer le nombre de canaux N (liste de toutes les constantes)

Pour N canaux de 32 bits (F = 4N octets par trame) :

1. **Descripteurs** (config HS `0x4019b2b6`) :
   - `bNrChannels` de l'Input Terminal (+68) et de l'AS_GENERAL (+209) = N ;
   - `wMaxPacketSize` (+225, LE16) = 7·F ;
   - éventuellement `bmChannelConfig` (+210, LE32) pour nommer L/R.
2. **dQH** : `MaxPacketLength` = 7·F (`0x40002ceb`, **ne jamais l'oublier**).
3. **Amorçage** (prime) : token = `(6·F) << 16 | 0x80`, champ privé `+0x20` = 6·F.
4. **Fin de case** (token) : longueur = trames·F et `d4` = (trames·F) << 16.
5. **Offset destination** (dstoff) : `[SLOT_BASE]` + trames·F.
6. **Stride des cases** ≥ 7·F, **aux deux sites** (`0x400027ce`/`0x400027d3` et `0x400029d2`).
7. **Profondeur et masque du ring** (`0x400027b3`, `0x400029b9`) : profondeur × 6 > 32, avec une marge.
8. **Taille ou borne du ring** (`0x40002564`, `[HYP]`) = profondeur × stride. **Vérifier que la RAM est libre.**
9. **Stub de copie** : boucle de trame qui écrit F octets (N sources, `byterev` sur chacune, masque mod 32 sur l'index des blocs de piste).
10. **Comprendre d'abord** les deux constantes non expliquées : `0x4000253b` (15 → 3) et `0x4000281f` (11 → 6). Elles dépendent peut-être de la géométrie.

## 6. Source du mix stéréo (pour un mode « 6 pistes + mix »)

- **`[FAIT]`** La boucle d'origine lit `a0 = 36(sp) + d5` et copie `d0` mots longs (L, R entrelacés, BE) avec `byterev`.
- Dans le stub, **après** le prologue `lea -44(sp),sp`, cette source est à **`80(sp)`**. `d5` (l'offset) reste dans le registre jusqu'à ce qu'on l'écrase.
- **`[HYP]`** à vérifier : le buffer de mix est-il lui aussi un bloc de 32 trames, qui boucle au même masque que les blocs de piste ?
  Quel est le lien entre `d5` et `d3` (offset de trame) ? S'agit-il du mix **après** saturation du bus et retours FX ? C'est probable, puisque c'est ce que l'USB envoie en stock.

## 7. Côté hôte (`[FAIT]` README)

- macOS : natif, 6 entrées. Windows : `usbaudio2.sys` fonctionne via **FlexASIO** (MME, DirectSound ou WASAPI partagé) à 48 kHz. Linux : non testé.
- Blocage (« wedge ») sous Windows : l'appareil s'énumère mais ne streame plus. **Éteindre et rallumer l'instrument**, puis recommencer.
- Contrôles d'une capture (voir [07](07-snippets.md#6-vérifier-une-capture-multicanal-numpy)) : `analyse_dupes.py` (doublons exacts), test de mute canal par canal, corrélation entre canaux.
