# 03 · Plateforme ColdFire du Model:Cycles

Sources : forum (dossier §2), ms-multi-output (adresses), elektron-firmware-tool (sections), octamax (méthodes de rétro-ingénierie ColdFire, sur l'Octatrack).

---

## 1. Processeur

- **`[FAIT]`** (Ess, forum #122) « Coldfire MCF5441 », 385 MIPS Dhrystone @ **250 MHz**. C'est le même CPU que Digitakt, Digitone, AR, A4 et M:S ; l'Octatrack est l'exception.
  **`[HYP]`** Famille **NXP MCF5441x** (MCF54410 à 54418), cœur ColdFire V4 avec EMAC (MAC/MSAC/ACC0-3).
  **`[À FAIRE]`** Lire le marquage de la puce et récupérer le *MCF5441x Reference Manual* (MCF54418RM) : carte des périphériques, contrôleur USB, SRAM.
- **`[FAIT]`** Tout le DSP est écrit **en assembleur ColdFire** (Ess), sans puce DSP dédiée. L'Octatrack, lui, a un DSP56300 à part : **la partie DSP d'octamax et d'octa-bt-pt ne s'applique pas ici.**
- **Big-endian.** Les échantillons en RAM sont des entiers 32 bits BE. L'USB audio veut du LE, d'où le `byterev` à chaque échantillon.

## 2. Carte mémoire connue (OS 1.13 Cycles)

| Zone | Adresses observées | Contenu | Certitude |
|---|---|---|---|
| DDR, code | `0x40000400` → | MAIN OS (section 3 : `VA = offset + 0x40000400`) | `[FAIT]` |
| DDR, avant l'image | `0x40000000`–`0x400003ff` | 1 Ko réservé : table des vecteurs (256 × 4 o) ? Octamax : « SDRAM 0x40000000 + 0x400 de cabecera/vectores » | `[HYP]` |
| Pilote USB | `0x400025xx`–`0x40003fxx` | code du device controller et du feeder audio (hooks en `0x40002…`) | `[FAIT]` |
| Données et tables | `0x4013e544` | table des modes USB (4 entrées × 0x28) | `[FAIT]` |
| Descripteurs USB | `0x4019b132`–`0x4019b3fd` | CDC ×2, MIDI ×2, audio+MIDI HS (328 o) | `[FAIT]` |
| Globales et BSS | `0x404a05e8` | `SLOT_BASE` : pointeur vers la case courante du ring USB | `[FAIT]` |
| Ring USB (?) | vers `0x404a9b80` / `0x404a9e00` | fin du ring d'origine et fin du ring patché ? | `[HYP]` (cf. patch `0x40002564`) |
| RAM rapide | `0x80001858`–`0x80001b57` | **6 blocs de rendu par piste**, 32 trames × 32 bits, stride `0x80` | `[FAIT]` |
| RAM rapide | `0x80000000` → | `[HYP]` SRAM interne (RAMBAR). Sur l'OT, cette fenêtre héberge l'état des voix, les TCB du noyau et les buffers partagés | `[HYP]` |
| Bootstrap | charge à `0x80010000` | en-tête de la section 2 (`[u32 taille][u32 0x80010000]`) | `[FAIT]` (valeur), `[HYP]` (mémoire cible) |
| Périphériques | `0xFC000000` / `0xEC000000` | espaces IPS du MCF5441x | `[HYP]`, à vérifier dans le RM |

## 3. Moteur audio : ce qu'on sait

- **`[FAIT]`** 48 kHz. Le moteur rend **32 trames par tick**, soit **1500 ticks/s** (0,667 ms).
- **`[FAIT]`** Chaque piste est rendue dans **son propre bloc mono** en RAM rapide, puis les 6 blocs sont **sommés en stéréo**
  (pan = coefficient appliqué à la sommation). Les envois FX sont « dérivés du bus principal sommé ».
- **`[FAIT]`** (forum) Le mix interne peut saturer, ce qui crée une interaction entre pistes. Chaque piste a aussi un étage Volume+Dist numérique.
- **`[HYP]`** La fonction de sommation lit `0x80001858`. **Chercher les références à `0x80001858`** (et à `0x80001858 + n*0x80`)
  pour trouver le mixeur, les coefficients de pan et l'origine des bus FX. C'est la clé des extensions stéréo et FX ([08](08-feuille-de-route.md)).
- **`[HYP]`** Le DSP utilise probablement l'EMAC (`mac.l`, `msac.l`, `ACC0-3`). Le désassembleur doit le gérer : Ghidra « Coldfire » le fait.

## 4. Aide-mémoire d'encodage ColdFire (vérifié sur les octets réels des patchs)

| Instruction | Encodage | Exemple réel |
|---|---|---|
| `jmp abs.l` | `4EF9 aaaaaaaa` (6 o) | `4ef94019b1e0` = `jmp 0x4019b1e0` |
| `jsr abs.l` | `4EB9 aaaaaaaa` | |
| `nop` / `rts` | `4E71` / `4E75` | |
| `moveq #n,Dx` (−128..127) | `(0x70 | x<<1) nn` | `7212` = `moveq #18,d1` |
| `lsl.l #k,Dy` (k = 1..8) | `0xE188 | (k&7)<<9 | y` | `e788` #3,d0 · `ed88` #6,d0 · `ef8a` #7,d2 · `e988` #4,d0 |
| `lsr.l #k,Dy` | `0xE088 | (k&7)<<9 | y` | `e288` = `lsr.l #1,d0` |
| `lsl.l Dx,Dy` (compteur en registre) | `0xE1A8 | x<<9 | y` | `e3ac` = `lsl.l d1,d4` |
| `add.l Dx,Dy` | `0xD080 | y<<9 | x` | `d081` = `add.l d1,d0` ; `d285` = `add.l d5,d1` |
| `sub.l Dx,Dy` | `0x9080 | y<<9 | x` | `9285` = `sub.l d5,d1` ; `9480` = `sub.l d0,d2` |
| `move.l abs.l,Dn` | `0x2039 | n<<9` + adresse | `2239404a05e8` = `move.l 0x404a05e8,d1` |
| `movea.l #imm,An` | `0x207C | n<<9` + imm | `247c80001858` = `movea.l #0x80001858,a2` |
| `move.l #imm,Dn` | `0x203C | n<<9` + imm | `203c00900080` |
| `byterev Dn` (ISA_A+/C) | `0x02C0 | n` | `02c2` = `byterev d2` ; `02c5` = `byterev d5` |
| `swap Dn` / `clr.w Dn` | `0x4840|n` / `0x4240|n` | `4844` / `4244` |
| Prologue et épilogue d'un stub | `4fef ffd4` + `48d7 07ff` … `4cd7 07ff` + `4fef 002c` | `lea -44(sp),sp ; movem.l d0-d7/a0-a2,(sp)` |

## 5. Pièges de l'ISA ColdFire (connaissance générale, à confirmer dans le *ColdFire Family Programmer's Reference Manual*)

- **Presque tout en `.l`.** Beaucoup d'opérations arithmétiques et logiques n'existent qu'en taille longue sur les registres.
- **Décalage immédiat limité à 1..8.** Au-delà, compteur dans un registre : l'OS d'origine fait `moveq #19,d1 ; lsl.l d1,d4`.
  **Pas de rotations** (`rol`/`ror` absents). Les multiplications par une constante se font par shifts et additions : ×24 = (x<<4)+(x<<3), ×192 = (x<<7)+(x<<6).
- **`moveq` limité à −128..127.** 144 s'obtient par `moveq #18` puis `lsl #3` (c'est ce que fait prime6), ou par `move.l #imm` (6 o).
- **`movem` n'accepte ni `-(An)` ni `(An)+`** : on écrit `lea -N(sp),sp ; movem.l …,(sp)` et l'inverse.
- **Pas de `dbra`** : `subq.l #1,dN ; bne`.
- Instructions propres au ColdFire que capstone M68K ne décode pas : `byterev`, `bitrev`, `ff1`, `mvs`, `mvz`, `mov3q`, `sats`, EMAC…
- **Assembleur** : octamax utilise `m68k-elf-as -mcpu=5407` (ISA_B). `byterev` n'y existe pas, d'où le `.short 0x02c2` de ms-multi-output.
  **`[À TESTER]`** `-mcpu=54418` (ou `-mcpu=5441x`) pour obtenir les mnémoniques ISA_C, si le binutils installé le supporte (`m68k-elf-as --help`).

## 6. Outils de rétro-ingénierie

| Outil | Usage | Commande |
|---|---|---|
| **Ghidra** (≥ 11, octamax : v12 headless) | décompilation. Langage **`68000:BE:32:Coldfire`** (gère EMAC, `mvs`/`mvz`) | import brut de `section_3_MAIN_OS.bin`, base `0x40000400` |
| **radare2** | exploration rapide | `r2 -a m68k -b 32 -e cfg.bigendian=true -m 0x40000400 section_3_MAIN_OS.bin` |
| **capstone** (Python, **déjà installé** : `capstone 5.0.7`) | désassemblage scripté | `Cs(CS_ARCH_M68K, CS_MODE_BIG_ENDIAN | CS_MODE_M68K_040)` ; ⚠️ nommer son script autrement que `dis.py` (conflit avec le module standard) |
| **binutils m68k** | assembler, lier et extraire les stubs | `brew install m68k-elf-binutils` (existe dans Homebrew, tout comme `m68k-elf-gcc`) |
| **Unicorn** (Python) | émuler un stub ou un chemin de l'image réelle (octamax `tools/emu_*.py`) | `pip install unicorn` |
| `find_base.py` (octamax) | retrouver la base de chargement par corrélation pointeur → chaîne | inutile ici : base connue |
| `string_func_map.py` (octamax) | associer les fonctions aux chaînes d'interface | utile pour trouver les menus (SETTINGS) |

Sur l'appareil, en cas de crash (vu sur l'Octatrack, probablement pareil sur les Models) : l'écran affiche
`EXCEPTION VEC:xx SR:xxxx ADDR:xxxxxxxx`.
`VEC:04` = instruction illégale (saut au milieu d'une instruction, ou code corrompu).
`VEC:0B` = vecteur 11, *unimplemented line-F*. Chez octamax, un retour sur une adresse morte.
`ADDR:0` = déréférencement d'un pointeur nul.
`SR:27xx` = IPL 7, typique du contexte audio.

## 7. Points de repère à étiqueter dans Ghidra (Cycles 1.13)

```
0x400027e8  hook prime (dans FUN_40002778, amorçage des dTD)
0x400029e4  hook dstoff (calcul du pointeur destination)
0x40002a06  hook copie (boucle du feeder, source = 36(sp)+d5 = mix stéréo)
0x40002a42  hook token (FUN_40002912, fin de case)
0x40002ceb  constante MaxPacketLength du dQH
0x40003f10  lit le champ privé +32 du dTD (octets transférés)
0x4013e544  table des modes USB (4 × 0x28)
0x4019b132  blobs de descripteurs (CDC, CDC, [18 o], MIDI, MIDI, [18 o], AUDIO+MIDI HS @0x4019b2b6)
0x404a05e8  SLOT_BASE (variable)
0x80001858  TRACK_BASE : 6 blocs × 0x80
```
`[HYP]` Les trous de 18 o entre blobs (`0x4019b1c8`, `0x4019b2a4`) ont la taille exacte d'un descripteur de périphérique USB.
