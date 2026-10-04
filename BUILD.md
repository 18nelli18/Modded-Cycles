# Construire un firmware modifié

> ⚠️ Aucune image firmware Elektron n'est fournie ici. Tu apportes **ta propre** copie de l'OS officiel,
> téléchargée sur elektron.se. Flasher un firmware modifié se fait **à tes risques** (garantie, brick possible).
> Une **interface MIDI reliée au MIDI IN** de l'appareil (jack TRS : câble jack stéréo depuis une sortie TRS,
> ou adaptateur DIN fourni) est obligatoire pour pouvoir revenir en arrière (STARTUP MENU).

## Chaîne d'outils

Python 3 uniquement, aucune dépendance externe, aucun compilateur. Le moteur bas niveau
(`tools/mtlib/`, transport SysEx + codec aPLib + conteneur ELE3/HMAC) vient de
[`drumkilla/elektron-model-tweaks`](https://github.com/drumkilla/elektron-model-tweaks) (MIT, voir `tools/mtlib/LICENSE`).
L'orchestration (`tools/build.py`) et les tables de patchs (`tweaks/`) sont propres à ce dépôt.

## Étapes

1. Télécharge `model-cycles_OS1.13.zip` sur elektron.se, dézippe-le pour obtenir `model-cycles_OS1.13.syx`
   (SHA-256 attendu `44fe5862…9800640c`).
2. Liste les patchs disponibles :
   ```sh
   python3 tools/build.py --list
   ```
3. Construis l'image. Il y a deux variantes du 6 canaux, **incompatibles entre elles** :
   ```sh
   python3 tools/build.py -i model-cycles_OS1.13.syx -t 6ch-multiout   # référence (casse l'upgrade USB)
   python3 tools/build.py -i model-cycles_OS1.13.syx -t 6ch-usbup      # garde l'upgrade USB (celle du flasher web)
   ```
   Et la machine **SD VINTAGE** (à la place de SNARE, [note 14](notes/14-machine-sd-vintage.md)), seule ou avec un 6 canaux :
   ```sh
   python3 tools/build.py -i model-cycles_OS1.13.syx -t sdvintage-snare
   python3 tools/build.py -i model-cycles_OS1.13.syx -t 6ch-usbup,sdvintage-snare
   ```
   Et les trois tweaks de [drumkilla](https://github.com/drumkilla/elektron-model-tweaks) (fichiers `01`–`03` de `tweaks/`,
   repris sans modification, MIT) : `latching-mute`, `trig-preview`, `browser-scroll`. Notre build donne le **même MAIN OS,
   octet pour octet**, que leur propre `tweak.py` (vérifié pour chacun et pour les trois ensemble).
   ```sh
   python3 tools/build.py -i model-cycles_OS1.13.syx -t 6ch-usbup,latching-mute,trig-preview,browser-scroll
   ```
   Et le **vrai moteur SD VINTAGE du Syntakt** ([note 17](notes/17-portage-exact-syntakt.md)), extrait au build de **ton** fichier Syntakt
   (aucun octet Elektron dans le dépôt : le tweak ne contient qu'une recette de copie et une table de relocalisation).
   L'OS Syntakt 1.42 ou 1.41 : même programme audio, donc même résultat ([note 16 §1](notes/16-moteur-syntakt.md#os-142--même-programme-audio)) :
   ```sh
   python3 tools/build.py -i model-cycles_OS1.13.syx -t 6ch-usbup,sdvintage-exact --syntakt Syntakt_OS1.42.syx
   ```
   Ou le même moteur en **7ᵉ machine « SDVtg »**, SNARE restant la SNARE d'origine ([note 18](notes/18-septieme-machine.md)) :
   ```sh
   python3 tools/build.py -i model-cycles_OS1.13.syx -t 6ch-usbup,sdvintage-7th --syntakt Syntakt_OS1.42.syx
   ```
   Ou n'importe quel choix de moteurs du Syntakt en machines ajoutées ([note 20](notes/20-moteurs-syntakt-a-cocher.md)) :
   `sdvintage-7th` (SD), `syntakt-vintage` (SD + CP), et `syntakt-<moteurs>` pour les autres choix parmi `sd`, `cp`, `toy`,
   `bits`, `swarm` (dans cet ordre : `syntakt-toy`, `syntakt-bits`, `syntakt-swarm`, `syntakt-sd-cp-toy-bits-swarm`…
   [notes 21](notes/21-sy-bits.md) et [22](notes/22-sy-swarm.md)). Un seul à la fois :
   ```sh
   python3 tools/build.py -i model-cycles_OS1.13.syx -t 6ch-usbup,syntakt-sd-cp-toy-bits-swarm --syntakt Syntakt_OS1.42.syx
   ```
   → écrit `model-cycles_OS1.13_mod.syx` à côté. `-t a,b` combine plusieurs patchs compatibles.
   `--all` applique tout, mais refuse si deux patchs sont incompatibles (c'est le cas de ces deux variantes).

Le build vérifie chaque octet `old` avant écriture, contrôle le SHA-256 de la section 3 d'origine,
et recalcule tous les checksums + le HMAC-SHA256. Seule la **section 3 (MAIN OS)** est touchée :
bootloader et updater sont conservés à l'identique.

Pour un patch qui écrit dans une zone `0xFF` (une « cave »), comme `6ch-usbup` ou `sdvintage-snare`, le build affiche la zone :
du début du bloc `0xFF` à la fin des octets écrits.
Il **refuse** si l'image d'origine contient un pointeur vers elle : `--force-cave` passe outre, après vérification à la main.
Exception : un pointeur que les patchs choisis réécrivent eux-mêmes, vers une adresse hors de la zone, est affiché « neutralisé » et ne bloque pas.
Autre exception, vérifiée à la main et listée dans `device.json` (`cave_refs_ok`) : une référence dont seule une partie de la
zone est lue. C'est le cas de `browser-scroll` : il écrit dans la table caractère → glyphe de la petite police de chiffres
(`0x401485ee`, 256 entrées de 16 bits, `0xFFFF` = pas de glyphe), aux entrées des caractères de contrôle 1 à 8, jamais dessinés.
La référence ne bloque plus tant que toutes les écritures restent dans la partie déclarée libre ; une écriture qui en sort est refusée.
C'est le cas des sprites dont on libère le masque `0xFF` en les redirigeant vers un masque identique
([note 14 §5](notes/14-machine-sd-vintage.md#5-place-libre--les-caves-0xff-étaient-des-masques-de-sprites), `tools/sprites.py`).
Les références relatives (`(d16,PC)`, branchements) sont seulement signalées, car une donnée peut les imiter.
Détails : [`notes/13-6ch-upgrade-usb.md`](notes/13-6ch-upgrade-usb.md) §4.

### Vérification de reproductibilité

Le patch 6 canaux doit produire un **MAIN OS décompressé** de SHA-256
`65e24b50dd457444e87daea79dd41b82f61098cb8ae5cd27cbe0d91742f29555`
(identique au résultat connu-bon de `ms-multi-output`). Pour l'exiger :
```sh
python3 tools/build.py -i model-cycles_OS1.13.syx -t 6ch-multiout \
    --expect-mainos 65e24b50dd457444e87daea79dd41b82f61098cb8ae5cd27cbe0d91742f29555
```
Le hash du `.syx` lui-même varie selon le packer ; c'est le MAIN OS décompressé qui fait foi.

Les autres patchs n'ont pas de résultat connu-bon extérieur. Voici ce que donne `build.py` sur l'OS 1.13 officiel
(le flasher web exige les mêmes valeurs pour celles qu'il propose) :

| `-t` | MAIN OS patché (SHA-256) |
|---|---|
| `6ch-usbup` | `a7086beef0aa10427248e0b191ee97ddc249b2460804422df7b17100febf1158` |
| `sdvintage-snare` (v2, recalée sur le Syntakt) | `11049726efa102028f7365b0a672c8a244b98edcef5e7c8b5e0aafba369f60d3` |
| `6ch-multiout,sdvintage-snare` | `80d0d717c5054f9277c2ddadb588e3578968cc1427610c7367ee408fa8ffd2de` |
| `6ch-usbup,sdvintage-snare` | `caac2918d7b7ce85849ff9814a75549b03091199de202ae05b648f2fbef0fcb9` |
| `latching-mute,trig-preview,browser-scroll` | `71fef138b1ae16f3ad440ecaa6a6327c1a987ce2c8a86b74329f68159981a15c` (= `tweak.py` de drumkilla) |
| `6ch-usbup,latching-mute,trig-preview,browser-scroll` | `771211068fee2aa673ed1df1afe4b7daf864500ce061ea0e88d9a11185819b37` |

| `sdvintage-exact` (avec `--syntakt Syntakt_OS1.42.syx`) | `8e2290a79fb1406ce65b3af3c5d3d95faade666e98eb8ecce0c0fa25fe87b15d` |
| `6ch-usbup,sdvintage-exact` (idem) | `97dadf3884a2703c4f7b230c9a046ae735292d57ac6576ff2e6d5bf72a12c670` |
| `syntakt-vintage` (idem) | `b4de3ec5f7eda7504bf03e7141f57bae6cf5bc137d39f6704da60881d56ed9b0` |
| `sdvintage-7th` (idem) | `c73ad4c796b94ab39d106d0798091eb39b5e3e31f66d7fe78e2db30db44daad3` |
| `syntakt-cp` (idem) | `baf05027e0644df679269672d939b83d67c100de069bc3ec2397d1ad39580de5` |
| `syntakt-toy` (idem) | `667c2655ad79692d895d18463660e43bc46f03c421ad03de6fc0116e05881a51` |
| `syntakt-sd-cp-toy` (idem) | `859fc46cc8e794430e8c9553a92bb6fe42a315a423b75f96134644534a2002c5` |
| `syntakt-bits` (idem) | `901205ed00b3e5652130f10b2f5b3e5ad9a48574392b9591b1ccd3d1cbdf8e8a` |
| `syntakt-sd-cp-toy-bits` (idem) | `d37c343583fe6b6f19dcf90fb2243b43301fee9d6a7ce78c4253823eb55c7e3f` |
| `syntakt-swarm` (idem) | `872c6ee8e4af779cc7b6184979174ee6a2f8eb7b9372044b41c0e5bd39b0888f` |
| `syntakt-sd-cp-toy-bits-swarm` (idem) | `c4616b24e394383986f1f31c6c5bf3bc78322593c6997bd0a199c55fd26f9b3c` |

### Model-TG

`tweaks/model-cycles_OS1.13/30-model-tg.json` vient du build de [Model-TG](https://github.com/TinyGregAudio/Model-TG) lui-même (licence MIT),
au commit épinglé dans `tools/gen_model_tg.py`, avec les binutils m68k, depuis une copie de sa source avec deux retouches (`MC_PATCHES` : en
mode mute, chaque touche de piste mute tout de suite, [note 31 §10](notes/31-model-tg.md) ; avec l'audio USB multipiste, une piste mutée n'est
plus coupée net sur sa piste USB, [note 34 §3](notes/34-glitches-usb-multipiste.md)), plus l'envoi à l'USB à heure fixe (`tools/usb_steady.py`) :
```sh
git clone https://github.com/TinyGregAudio/Model-TG vendor/Model-TG
git -C vendor/Model-TG checkout 70b39dd6787770ebefc7a2d78dea1678ec012679   # v1.1.0
python3 tools/gen_model_tg.py --cycles model-cycles_OS1.13.syx --model-tg vendor/Model-TG [--check]
```

| `-t` | MAIN OS patché (SHA-256) |
|---|---|
| `model-tg` | `2a939b7f00b6868644e2570759ff9f15b955fce3da261b5924e430bdb19202a6` (sans nos ajouts : `a049d724…`, celle annoncée par Model-TG pour sa v1.1.0) |
| `6ch-usbup,model-tg` | `de84566595e7d7fc840fe1f6c7af8d468c444b49ec7a4a573ffb7838bcce8fa5` |

Le même script écrit `30-model-tg-st.json`, la base de la **version combinée avec les moteurs du Syntakt** : Model-TG construit par son
build depuis une copie de sa source, avec les mêmes ajouts et une retouche de plus (sa zone d'échantillons s'arrête 1 Mo plus bas). Les moteurs s'appliquent
par-dessus (`31-syntakt-tg-<moteurs>.json`, `requires`), voir [note 31 §4](notes/31-model-tg.md) :
```sh
python3 tools/gen_syntakt_engines.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx --all --tg [--check]
python3 tools/build.py -i model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx -t model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm
python3 tools/emu/test_model_tg_syntakt.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx
```

| `-t` | MAIN OS patché (SHA-256) |
|---|---|
| `model-tg-st,syntakt-tg-sd` | `67c8c4504d6f1614887bd888ce6ee9f51096a2a5556dde1c77295311b600d57b` |
| `model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm` | `4b59a9a75dcb80034410e8ed68356bb80c05c4a67335ec2b487e44d07a1732a1` |
| `6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm` | `516f1dcaa136abd8ad99157e214b6137f59b5a1ad958d196b5bc074d7d888d0f` |

Les 2 303 combinaisons proposées par le flasher web sont toutes listées dans `docs/flasher/app.js` (`REF_MAINOS`), calculées par
`tools/ref_mainos.py` (qui réécrit le bloc ; `--check` pour vérifier) ;
`tools/webflash_smoke.sh model-cycles_OS1.13.syx Syntakt_OS1.42.syx` les reconstruit toutes dans la page et les compare.
SD VINTAGE v1 (clean-room d'origine, **testée sur le matériel** le 29/09/2026, compilée par GCC 13.3) donnait `80b7b2bd…` seule et `38754937…` avec `6ch-usbup` ;
la v2 est compilée par `m68k-elf-gcc` 16.2 (Homebrew), voir [note 16 §6](notes/16-moteur-syntakt.md).

### Arpégiateur

`tweaks/model-cycles_OS1.13/40-arp.json` est produit par `tools/gen_arp.py`, qui compile `tools/machines/arp/` (`m68k-elf-gcc`)
et le lie dans quatre masques de sprites libérés ([note 32](notes/32-arpegiateur.md)). La preuve fait tourner le code du tweak
et celui de l'OS, jusqu'à la vraie boucle d'événements de l'interruption audio, et le live rec par les vraies fonctions
d'envoi de note de l'OS :
```sh
python3 tools/gen_arp.py --cycles model-cycles_OS1.13.syx [--check]
python3 tools/emu/test_arp.py --cycles model-cycles_OS1.13.syx \
    [--with 6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm --syntakt Syntakt_OS1.42.syx]
```

| `-t` | MAIN OS patché (SHA-256) |
|---|---|
| `arp` | `e445bf895123d3fc94762a65739558b579ec8df3000c9bdf5747a3d73287e6a6` |
| `model-tg,arp` | `28f3029d0d05476580ab2776e94f135047ab36623b756f60f4b9d8f80533927e` |
| `6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm,arp` | `ac33f7e7df8ab3f59ebdd164bcebef3842f4b52915c843d7287d5c4a851655fc` |

L'arpégiateur et les moteurs du Syntakt libèrent le même masque (`0x4016cae8`) : les deux constructeurs (`tools/build.py`,
`docs/flasher/builder.js`) acceptent une écriture déjà faite à l'identique par un autre tweak.

### Effacer un trig

`tweaks/model-cycles_OS1.13/41-trig-hold.json` est produit par `tools/gen_trig_hold.py`, qui assemble
`tools/machines/trig_hold/trig_hold.S` (166 o avec l'heure d'appui des 16 touches de pas) au début du masque de sprite libéré
`0x4015c044`, devant les stubs de `6ch-usbup` ([note 33](notes/33-effacer-un-trig.md)). La preuve fait tourner la vraie chaîne de
l'OS, de la lecture des touches (anti-rebond, horloge de maintien à 120 Hz) au mode grille, à la milliseconde :
```sh
python3 tools/gen_trig_hold.py --cycles model-cycles_OS1.13.syx [--check]
python3 tools/emu/test_trig_hold.py --cycles model-cycles_OS1.13.syx \
    [--with 6ch-usbup,model-tg-st,arp,syntakt-tg-sd-cp-toy-bits-swarm --syntakt Syntakt_OS1.42.syx]
```

| `-t` | MAIN OS patché (SHA-256) |
|---|---|
| `trig-hold` | `bbb8a4217a888c46a60cfb17ae444bec9cf21d6ff2d2d36bf8d1f1cdb81d1ef4` |
| `6ch-usbup,trig-hold` | `304c2f9a1656d35abacd5d6d2161d181fbc763fa6ac4c432b2226332554ccb1b` |
| `model-tg,trig-hold` | `89d8b86d3b6eaf7b5288dc33c390103fbd2a27154839e55e4702b625b29df738` |
| `6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm,trig-hold,arp` | `7588d23b82af9cf51f54f6fd96b21e9f036494aa58626dc794992df426b55fe8` |

Avec `6ch-usbup`, les deux tweaks réécrivent de la même façon le pointeur du sprite dont le masque est libéré.

### Variante `6ch-usbup`

`tweaks/model-cycles_OS1.13/11-6ch-usbup.json` n'est pas écrit à la main : `tools/relocate_6ch.py` le dérive du patch 6 canaux
(stubs déplacés dans une cave ; descripteurs et table des modes USB laissés d'origine), sans l'image firmware, avec les binutils m68k.
Depuis la [note 34](notes/34-glitches-usb-multipiste.md), il rend aussi le flux USB robuste : envoi de chaque bloc au début de
l'interruption suivante (`tools/machines/usb6/feed.S`, écritures dans `tools/usb_steady.py`, les mêmes que dans Model-TG et les moteurs
du Syntakt), file alignée au démarrage, ring de 9 cases de 168 o au lieu de 8 de 192 o, copie des 6 pistes déroulée
(`tools/machines/usb6/tracks6.S`). La preuve fait tourner le vrai pilote USB de l'OS avec un contrôleur modélisé :
```sh
python3 tools/relocate_6ch.py --check                  # le fichier versionné est-il à jour ?
python3 tools/emu/test_usb_in.py --cycles model-cycles_OS1.13.syx [--seconds 2] [--long 60]   # ~15 min
```

### Machine SD VINTAGE

`tweaks/model-cycles_OS1.13/20-sdvintage-snare.json` est produit par `tools/gen_sdvintage.py`, qui compile
`tools/machines/sdvintage/sdvintage.c` pour le ColdFire du M:C (paquet `gcc-m68k-linux-gnu`, testé avec GCC 13.3).
La validation rejoue le vrai moteur de l'OS dans un émulateur (paquets Python `unicorn` et `numpy`, plus `binutils-m68k-linux-gnu`) :
```sh
python3 tools/gen_sdvintage.py --check                               # le JSON versionné correspond-il au source ?
python3 tools/emu/test_sdvintage.py -i model-cycles_OS1.13.syx       # ~2 min ; --wav dossier/ pour écouter les rendus
```
Le vrai moteur du Syntakt, à la place de SNARE ([note 17](notes/17-portage-exact-syntakt.md)) ou en 7ᵉ machine SDVtg
([note 18](notes/18-septieme-machine.md)), a ses générateurs et ses preuves (`m68k-elf-gcc` / `m68k-elf-objdump`) :
```sh
python3 tools/gen_sdvintage_exact.py --syntakt Syntakt_OS1.42.syx --check
python3 tools/gen_sdvintage_7th.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx --check
python3 tools/emu/test_sdvintage_exact.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx
python3 tools/emu/test_sdvintage_7th.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx
python3 tools/gen_syntakt_machines.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx --check
python3 tools/emu/test_syntakt_machines.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx
python3 tools/gen_syntakt_engines.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx --all --check
python3 tools/emu/test_syntakt_machines.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx \
    --tweak tweaks/model-cycles_OS1.13/24-syntakt-sd-cp-toy.json
python3 tools/emu/test_sram_scratch.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx \
    --tweak tweaks/model-cycles_OS1.13/24-syntakt-sd-cp-toy-bits-swarm.json   # SRAM empruntée (notes/26)
python3 tools/emu/test_sram_code.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx \
    --tweak tweaks/model-cycles_OS1.13/24-syntakt-sd-cp-toy-bits-swarm.json   # code du Syntakt en SRAM (notes/28)
python3 tools/emu/test_model_tg.py --cycles model-cycles_OS1.13.syx                                  # Model-TG seul (notes/31, notes/34 §3)
python3 tools/emu/test_model_tg_syntakt.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx   # version combinée
python3 tools/ref_mainos.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx --check
```
Pour ajouter un moteur : l'ajouter à `CATALOG` de `tools/gen_syntakt_engines.py` (et ses plages copiées), puis relancer
`gen_syntakt_engines.py --all` et `--all --tg`, `gen_flasher_tweaks.py` et `ref_mainos.py`, et tester chaque nouveau tweak en émulation.

## Flasher (rappel)

1. **STARTUP MENU** : éteindre, maintenir **[FUNC]**, allumer, **[TRIG 4]** (OS UPGRADE).
2. Envoyer le `.syx` modifié sur le **MIDI IN** de l'appareil (`flash.sh` / `flash.bat`, SysEx Librarian ou C6),
   par câble jack stéréo depuis une interface à sortie TRS, ou par l'adaptateur DIN fourni.
   L'upgrade par le menu de démarrage **ne marche pas en USB MIDI** — MIDI IN obligatoire.
3. Détails, tests et récupération : [`notes/06-flash-et-recuperation.md`](notes/06-flash-et-recuperation.md).

## Autre chaîne d'outils

Le C [`mischa85/elektron-firmware-tool`](https://github.com/mischa85/elektron-firmware-tool) fait le même travail
de conteneur ; voir [`notes/02-format-os-syx.md`](notes/02-format-os-syx.md).
