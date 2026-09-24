# 02 · Format des OS Elektron (`.syx`) et elektron-firmware-tool

Source : <https://github.com/mischa85/elektron-firmware-tool>, commit `a5bce9a` (08/09/2026), C11, licence MIT,
auteur Marcel Bierling. Implémentation indépendante ; aucune clé n'est stockée dans le dépôt.
Fichiers : `transport.[ch]`, `container.[ch]`, `aplib.[ch]`, `integrity.[ch]`, `firmware.[ch]`, `report.[ch]`, `device.[ch]`, `main.c`.

---

## 1. Les couches d'un OS `.syx` (modèles récents, conteneur ELE3)

```
.syx  = suite de messages SysEx F0 … F7            (transport, 7 bits)
  └─ flux décodé = [preamble 8 o][conteneur ELE3]
       preamble  = [u32 BE taille conteneur][u32 BE checksum de contenu]
       ELE3      = en-tête texte + table de sections + sections (alignées sur 16) + trailer HMAC-SHA256
         └─ section = [u32 BE longueur][u32 BE somme des octets] + flux aPLib (ou brut)
              └─ section 3 = MAIN OS (code ColdFire)  → chargé à VA 0x40000400
```

**`[FAIT]`** Les checksums et le HMAC sont recalculables : la clé HMAC se **re-dérive depuis l'image elle-même**.
Rien n'empêche donc de reconstruire une image acceptée par le bootloader.

## 2. Transport SysEx (moderne)

Chaque message est encadré par `F0 … F7`. Les offsets ci-dessous sont comptés dans le **corps**, c'est-à-dire entre F0 et F7.

| Message | Corps | Taille du corps |
|---|---|---|
| Marqueur de début | `00 20 3C dev 00 7F 01 info[7]` | 14 |
| Paquet de données | `00 20 3C dev 00 7E blk_hi blk_lo seq payload[116] cksum` | 126 |
| Marqueur de fin | `00 20 3C dev 00 7F 02 info[7]` | 14 |

- `00 20 3C` = identifiant fabricant Elektron. `dev` = product id (**`0x11` Model:Cycles**, `0x0F` Model:Samples).
- **Payload 8-in-7, MSB en premier** : chaque groupe = 1 octet de MSB (bit 6 = MSB du 1ᵉʳ octet de donnée) + 7 octets de 7 bits.
  116 octets encodés = 14 groupes complets + 1 partiel = **101 octets décodés par paquet**.
- **Checksum par paquet (octet 125)** :
  `base` = `info[0]` du marqueur de début ; `acc = Σ_{i=0..118} body[6+i] XOR (base+i)` ; `cksum = (base + acc) & 0x7F`.
  Attention : `base+i` n'est **pas** tronqué à 8 bits.
- **Infos du marqueur** : `info[0]` = graine du checksum, `info[1..2]` = bloc de départ (`info[1]<<7 | info[2]`),
  `info[3]` = seq de départ, `info[4..6]` = nombre de paquets (3 × 7 bits). Gabarit par défaut : `10 00 01 72 01 06 6b`.
- **Compteur bloc/seq** : un seul compteur 7 bits. `cum = seq0 + k` ; `bloc = bloc0 + (cum >> 7)` ; `seq = cum & 0x7F`.
- `npkt = (8 + taille_conteneur) / 101 + 1` : il y a toujours un dernier paquet, éventuellement vide, complété de zéros.
- Legacy (hors sujet ici) : Octatrack (ELEK, en-tête de 14 o, checksum sur des quartets) ; Machinedrum et Monomachine (2+7+7).

## 3. Preamble et checksum de contenu

```
preamble[0:4] = taille du conteneur (BE32)
preamble[4:8] = Σ_{k=0}^{n/4-1} ((k+1) XOR mot_BE32[k])  mod 2^32   (mots complets seulement)
```

## 4. Conteneur ELE3

| Offset | Champ |
|---|---|
| `0x00` | magic `"ELE3"` |
| `0x07` | chaîne de build ou de modèle (texte) |
| ~`0x13` | version (repérée par le motif `chiffre.chiffre` entre 0x07 et 0x1C ; position variable selon l'appareil) |
| `0x1C` | nombre de sections (BE32, ≤ 64) |
| `0x20` | table : n entrées de 16 o `{id, offset, comp_len, dest}` (BE32 chacun) |

- Sections stockées dans l'ordre des offsets, **chacune alignée sur 16 o**. La table est réécrite au repaquetage.
- **Trailer** : zéros de bourrage, puis **4 octets nuls**, puis **HMAC-SHA256 de 32 o** à un offset aligné sur 16.
  `hmac_off = align16(fin_sections + 4)` ; `digest = HMAC(key, conteneur[0:hmac_off])` ; taille totale = `hmac_off + 32`.
- **Dérivation de la clé** (`integrity.c`) :
  1. chercher dans une section décompressée l'ancre `be f9 a3 f7 c6 71 78 f2`.
     `[HYP]` Ce sont les deux dernières constantes K de SHA-256 (`0xbef9a3f7`, `0xc67178f2`) : la matière de clé suit la table SHA-256 du firmware ;
  2. juste après : une chaîne ASCII `s` (≤ 64 caractères) terminée par NUL, puis une constante `C` de 32 o ;
  3. `key = SHA256(s) XOR SHA256(reverse(s)) XOR C` ;
  4. candidat accepté **seulement s'il reproduit le digest** de l'image.
  Avec `-v`, l'outil affiche la « derivation string ».

### Identifiants de section (étiquettes inférées par l'auteur, pas une spécification)

| Id | Nom | Remarque |
|---|---|---|
| 1 | FPGA | |
| 2 | **bootstrap** | Code ColdFire. En-tête `[u32 taille][u32 0x80010000]` (adresse de chargement). Chaînes « BOOTSTRAP UPGRADE », « OS UPGRADE », « STARTUP MENU », « PLEASE RESTART ME ». Anciennement étiqueté « DSP ». |
| 3 | **MAIN OS** | Le code applicatif. **C'est la seule section que ms-multi-output remplace.** |
| 4 | updater | |
| 5 | meta | |
| 6 | boot | Stub ColdFire d'environ 1,5 ko, sans chaînes |
| 7 | blob | |

**`[À FAIRE]`** Lancer `elektron-firmware-tool -i model-cycles_OS1.13.syx -v` pour lister les sections réellement présentes dans l'OS Cycles.

## 5. Compression : variante aPLib (`aplib.c`)

- LZ77 + Elias-gamma entrelacé. Chaque section commence par l'en-tête `[u32 longueur][u32 somme des octets]`.
- Biais d'offset **767** (`rawoff == 767` = marqueur de fin). Gamma = 2 : réutilise le dernier offset.
- Au-delà d'un offset de 3328 : longueur +1 (match minimum de 3, sinon 2).
- Offset maximal émis : **2^20**. Aucun flux Elektron d'origine ne l'atteint ; rester dans cette enveloppe protège le dépaqueteur de l'appareil.
- Le packer de l'outil compresse **mieux** qu'Elektron (−2 à −6 %). Un `-c` ne donne donc **pas** un fichier identique à l'officiel, mais il est **déterministe**.
- Niveaux `-l 0..3` (défaut 3 ; niveau 0 environ 18 × plus rapide et 3 % plus gros). ⚠️ **Le niveau change les octets de sortie**, donc les hashs de référence.

## 6. Vérifications faites par `fw_verify`

1. checksum de chaque paquet SysEx ;
2. nombre de paquets déclaré dans le marqueur = nombre de paquets reçus ;
3. checksum de contenu du preamble (ELE3) ;
4. somme des octets de chaque section compressée ;
5. HMAC-SHA256 du trailer (consulté seulement si tout le reste est bon).

Le résumé affiche `checksums : ok` ou `MISMATCH`.

## 7. Ligne de commande

```sh
make                                               # compile (C11, -Wall -Wextra)
T=./elektron-firmware-tool

$T -i model-cycles_OS1.13.syx                      # résumé : device, version, sections, verdict checksums
$T -i model-cycles_OS1.13.syx -v                   # rapport complet de chaque couche (+ chaîne de dérivation de clé)
$T -i model-cycles_OS1.13.syx -d 3 -o out/         # -> out/section_3_MAIN_OS.bin
$T -i model-cycles_OS1.13.syx -o out/              # sans -d : extrait TOUTES les sections
$T -i model-cycles_OS1.13.syx -c 3 patched.bin -o new.syx      # remplace la section 3, recompresse, recalcule tout
$T -i model-cycles_OS1.13.syx -r -o repack.syx && cmp model-cycles_OS1.13.syx repack.syx   # auto-test sans perte
$T -i model-cycles_OS1.13.syx -c 3 patched.bin -V 1.13 -o new.syx   # fixe le texte de version (largeur du champ existant)
$T -i new.syx --emit-container ele3.bin            # écrit aussi le conteneur brut (couche bin)
```

- Nom des fichiers extraits : `section_<id>_<nom>.bin` si la section est compressée (espaces → `_`), `.raw` si elle est stockée brute.
- `-c` échoue si la section n'existe pas, ou si le conteneur a un trailer non reconnu sans clé retrouvée.
- `-r` recopie les sections telles quelles. L'outil reproduit à l'octet près 22 des 23 images testées ; l'exception a un `0x0A` parasite après le dernier F7.

## 8. Implications pour le projet

- **Bootloader et conteneur** : le bootloader **ignore sans erreur** une image dont le device id ne correspond pas.
  Pour un Model:Cycles, il faut un conteneur `0x11`, c'est-à-dire l'OS Cycles officiel comme gabarit.
- **Remplacer uniquement la section 3** suffit à tout le mod. Bootstrap et bootloader restent intacts, ce qui garantit la récupération.
- **Version affichée** : ms-multi-output garde `1.13`. `-V` permettrait d'identifier nos builds sur l'appareil.
  `[HYP]` Risque : l'updater compare peut-être un code de version (sur l'Octatrack, c'est un code interne `0178` distinct du texte affiché).
  À tester prudemment, ou à laisser tel quel.
- **Reproductibilité** : figer le commit de l'outil **et** le niveau `-l` si l'on publie des SHA-256 de référence.

## 9. Table des product ids (`device.h`)

`0x02` Machinedrum · `0x03` Monomachine · `0x05` Octatrack · `0x06` Analog Four · `0x07` Analog Rytm · `0x08` Analog Heat ·
`0x0a` Digitakt · `0x0b` A4 MKII · `0x0c` AR MKII · `0x0d` Digitone · `0x0e` Heat MKII · **`0x0f` Model:Samples** ·
**`0x11` Model:Cycles** · `0x13` Heat +FX · `0x14` Digitakt II · `0x15` Digitone II · `0x16` Syntakt.
