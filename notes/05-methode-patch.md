# 05 · Méthode : patcher le MAIN OS sans casser l'instrument

Synthèse des pratiques de **ms-multi-output** (Models), **octamax** (Octatrack, rétro-ingénierie complète, 127 commits) et
**octa-bt-pt** (Octatrack, patchs de valeurs). Les règles marquées 🔥 viennent d'un **crash réel documenté**.

---

## 1. Technique du détour et de la code cave

```
site du hook (code d'origine)                 code cave (stub)
┌──────────────────────────────┐              ┌──────────────────────────────────┐
│ jmp  stub          (6 o)     │ ───────────▶ │ (sauvegarde des registres)        │
│ nop ; nop ; …   (remplissage │              │ nouvelle logique                  │
│  jusqu'à la fin du bloc      │              │ + sémantique du bloc déplacé      │
│  déplacé)                    │              │ (restauration des registres)      │
│ <reprise> ◀──────────────────┼──────────────│ jmp  reprise                      │
└──────────────────────────────┘              └──────────────────────────────────┘
```

- Le bloc déplacé doit faire **au moins 6 octets** (`jmp abs.l`). Les octets restants deviennent des `nop` (`4e71`).
- Le stub **reproduit tout ce que faisait le bloc écrasé**, avec les modifications voulues. Il rend la main avec les registres dans l'état attendu en aval (le **contrat**).
  ms-multi-output documente ce contrat en tête de chaque `.s` : faire pareil.
- Variante « prologue » (octamax) : hook à l'**entrée** d'une fonction. Le stub exécute les instructions d'entrée déplacées puis `jmp fonction+N`.
  Variante « return-hook » : remplacer l'adresse de retour dans la pile pour reprendre la main à la sortie. ⚠️ Voir 🔥R6.
- **Où loger le code** :
  1. **Données mortes rendues inutiles** : c'est le choix de ms-multi-output. Les 4 blobs de descripteurs sont libérés après redirection de la table des modes USB.
     Environ 350 o, mais au prix de la perte de l'upgrade USB et du Full Speed ;
  2. **Cave de zéros non référencée** : octamax en a trouvé une de 5986 o sur l'OT (`0x400d64da`).
     **`[À FAIRE]`** Chercher dans l'image Cycles des plages de zéros **qu'aucun pointeur (opérande ou table) ne référence** (cf. `scan_hole.py`),
     et vérifier que ce n'est pas du BSS initialisé à l'exécution. Cela permettrait de **garder l'upgrade USB** ;
  3. Agrandir la section 3 : **à éviter** tant qu'on ne sait pas ce qui suit l'image en RAM (BSS ?).

## 2. Règles de sûreté

| # | Règle | Origine |
|---|---|---|
| R1 | **Toujours construire depuis l'image d'origine**, avec un hash figé. Jamais par-dessus un build précédent. | octamax `build.py`, ms-multi-output |
| R2 | Chaque run de patch porte ses octets **`expect`** ; refuser en cas de différence. | ms-multi-output, octa-bt-pt |
| R3 🔥 | **Dériver les cibles de détour de la table de symboles** (`m68k-elf-nm`), jamais d'une adresse codée en dur. Sinon un stub décalé de 10 o fait sauter au milieu d'un autre, et l'**unité gèle sur le logo**. | octamax |
| R4 🔥 | **hookcheck** : aucun branchement, saut ou pointeur stocké (table, callback) ne doit viser l'**intérieur** d'un trou de hook. Sinon **`VEC:04` instruction illégale**. | octamax `hookcheck.py` |
| R5 | Vérifier que la cave est **vraiment libre** (zéros, ou données prouvées non référencées) et que les stubs ne se chevauchent pas. | octamax `build.py` |
| R6 🔥 | **Réentrance** : un stub atteignable en imbrication (ou depuis une interruption) ne doit pas sauver son état dans **une seule** variable globale. Crash `EXCEPTION VEC:0B`. | octamax (`patch_gui2.s`) |
| R7 | **Vérifier après empaquetage** : ré-extraire la section 3 du `.syx` produit et contrôler chaque patch (PRESENT / MISSING / UNKNOWN). | octa-bt-pt `master_patch.py verify` |
| R8 | **Hash de sortie reproductible** : figer le commit d'`elektron-firmware-tool` et le niveau `-l`. | déduit de ms-multi-output et octa-bt-pt |
| R9 | **Émuler** (Unicorn) le stub seul, **et** l'image composée : chaque détour vise exactement un symbole, et le contrôle atteint la reprise attendue. | octamax `emu_image.py` |
| R10 | Sur matériel : **un seul changement à la fois**, interface DIN et OS officiel prêts, builds numérotés. | tous |
| R11 | **Géométrie USB** : ne jamais réduire la profondeur du ring sous la taille d'un bloc moteur (32 trames), garder le **masque mod 32**, toujours mettre à jour le **`MaxPacketLength` du dQH**. | ms-multi-output |
| R12 | Stubs courts, **sans attente ni appel bloquant** : le feeder tourne probablement en contexte d'interruption. Sauver et restaurer tous les registres touchés (`lea -N(sp),sp ; movem.l …,(sp)`). | déduit de ms-multi-output |
| R13 | **Aucune image Elektron** (originale ou modifiée) dans le dépôt : `.gitignore` sur `*.syx`, `*.zip`, `build/`, `vendor/`, `*.wav`. Distribuer uniquement des tables d'octets et des sources ASM. | les trois dépôts |

## 3. Build reproductible (modèle à suivre)

```
1. vérifier sha256(.syx officiel) == référence
2. extraire section 3            (elektron-firmware-tool -d 3)
3. vérifier sha256(section 3) == référence
4. assembler les stubs à leur adresse fixe (m68k-elf-as / ld -Ttext / objcopy -O binary / nm)
5. appliquer la table (expect → write) + les stubs + les détours (cibles venant de nm)
6. hookcheck (cibles intérieures) + vérification des caves libres et des chevauchements
7. vérifier sha256(section 3 patchée) == référence du build testé
8. reconditionner (elektron-firmware-tool -c 3 … -o out.syx), conteneur = OS officiel de la MÊME machine (0x11)
9. vérification aller-retour : ré-extraire la section 3 de out.syx, contrôler tous les patchs
10. vérifier sha256(out.syx) == référence   → sinon NE PAS FLASHER
```

Figer l'outil comme octa-bt-pt :
```sh
git clone https://github.com/mischa85/elektron-firmware-tool vendor/elektron-firmware-tool
git -C vendor/elektron-firmware-tool checkout a5bce9a   # commit analysé le 25/09/2026 (octa-bt-pt fige 065d18f)
make -C vendor/elektron-firmware-tool
```
**`[À VÉRIFIER]`** Avec quel commit d'`elektron-firmware-tool` les SHA-256 de référence de ms-multi-output ont-ils été produits ?
Commits du 18-19/09, outil au `a5bce9a` du 08/09 : c'est probablement celui-là. À confirmer en reproduisant le build.

## 4. Format de registre de patchs proposé pour ce projet

Il fusionne les JSON de ms-multi-output (`off`/`va`/`expect`/`write`) et le registre d'octa-bt-pt (`id`/`group`/`desc`), plus la certitude :

```json
{
  "target": "model-cycles",
  "os": "1.13",
  "base_va": "0x40000400",
  "section3_sha256_stock": "cc99d4f0175d34d1e91d046e6ec85a5e8ab58ab9edbb3c24406acd48cb99ee98",
  "patches": [
    {"id": "usb.dqh.mpl", "group": "usb-geometry", "va": "0x40002ceb",
     "expect": "38", "write": "a8",
     "desc": "dQH MaxPacketLength 56 -> 168 (7 trames x 24 o)", "certainty": "fait"}
  ],
  "stubs": [
    {"id": "tracks6", "src": "asm/tracks6.s", "at": "0x4019b1e0",
     "detour": {"site": "0x40002a06", "len": 24, "symbol": "tracks6_stub", "rejoin": "0x40002a26"}}
  ]
}
```

## 5. Diagnostics éprouvés

- **Doublons exacts** (`analyse_dupes.py`) : l'égalité de mots 32 bits entre trames décalées d'un lag L ne demande **ni seuil ni modèle**.
  Si L = profondeur × trames par transfert, c'est un **sous-remplissage du ring**. Exclure les passages quasi silencieux.
  Un canal constant (DC) est normal pour une piste mutée. Capturer en **`pcm_s32le`**, pas en float.
- **Carte des canaux** : muter les pistes une à une et vérifier que le bon canal s'éteint.
- **Gain et distorsion** : sinus sur une piste, THD selon LEVEL. Référence M:S : ~10 % à 100, ~23 % à 127.
- Sur l'appareil : noter le code `EXCEPTION VEC/SR/ADDR` affiché en cas de crash (voir [03 §6](03-plateforme-coldfire.md#6-outils-de-rétro-ingénierie)).

## 6. Leçons « process » d'octa-bt-pt et octamax

- **CI sans firmware** : compilation Python, `bash -n`, validité des JSON, tests unitaires des conversions. Cela n'attrape pas une mauvaise adresse, mais évite un commit cassé.
- **Épingler aussi le zip téléchargé** (SHA-256) : Elektron peut republier un fichier.
- **Tamponner la version** (`-V PATCH001`) pour savoir quel build tourne. Sur l'OT, champ de 10 caractères. Sur ELE3, largeur = celle du texte existant ([02 §8](02-format-os-syx.md#8-implications-pour-le-projet)).
- **Fonctions désactivées par défaut** : octamax ajoute des bascules dans un menu (PERSONALIZE). Avec la bascule éteinte, le comportement est identique au stock.
  Si notre mod devient configurable, viser un réglage dans SETTINGS, cohérent avec la philosophie Model du dossier §7.5.
- **Persistance des réglages** : octamax a dû patcher la longueur de restauration du bloc de réglages en SRAM sauvegardée.
  Sur les Models, l'état n'est sauvé qu'à l'extinction propre (dossier §7.1).
