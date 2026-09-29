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
| `6ch-usbup` | `db3d26cc3a48d1155933240c7d1d5476c8f56d2b6a54be1ffe7f5327e54c0521` |
| `sdvintage-snare` | `80b7b2bd003f2695488d629c0fab56c84e10213898c9820c321efa711f6957c7` |
| `6ch-multiout,sdvintage-snare` | `4494fb764c7643b2a9acea8b4fa2cafe10ee7d9644e56d08e333ee019f4cbe72` |
| `6ch-usbup,sdvintage-snare` | `38754937b06e3815ee1da9c93137d46283b612e1881772f4d034fb9f998b3335` |
| `latching-mute,trig-preview,browser-scroll` | `71fef138b1ae16f3ad440ecaa6a6327c1a987ce2c8a86b74329f68159981a15c` (= `tweak.py` de drumkilla) |
| `6ch-usbup,latching-mute,trig-preview,browser-scroll` | `fd57831c61926fb3b1902cadcb0f95e68db3bb637b4cd20860a0efc46db82cfa` |

Les 15 combinaisons proposées par le flasher web sont toutes listées dans `docs/flasher/app.js` (`REF_MAINOS`).

### Variante `6ch-usbup`

`tweaks/model-cycles_OS1.13/11-6ch-usbup.json` n'est pas écrit à la main : `tools/relocate_6ch.py` le dérive du patch 6 canaux
(mêmes stubs, déplacés dans une cave ; descripteurs et table des modes USB laissés d'origine).
```sh
python3 tools/relocate_6ch.py --check                  # le fichier versionné est-il à jour ?
python3 tools/relocate_6ch.py --cave 0x4018a788:1024   # viser un autre masque libéré (VA:taille), puis rebuild
```

### Machine SD VINTAGE

`tweaks/model-cycles_OS1.13/20-sdvintage-snare.json` est produit par `tools/gen_sdvintage.py`, qui compile
`tools/machines/sdvintage/sdvintage.c` pour le ColdFire du M:C (paquet `gcc-m68k-linux-gnu`, testé avec GCC 13.3).
La validation rejoue le vrai moteur de l'OS dans un émulateur (paquets Python `unicorn` et `numpy`, plus `binutils-m68k-linux-gnu`) :
```sh
python3 tools/gen_sdvintage.py --check                               # le JSON versionné correspond-il au source ?
python3 tools/emu/test_sdvintage.py -i model-cycles_OS1.13.syx       # ~2 min ; --wav dossier/ pour écouter les rendus
```

## Flasher (rappel)

1. **STARTUP MENU** : éteindre, maintenir **[FUNC]**, allumer, **[TRIG 4]** (OS UPGRADE).
2. Envoyer le `.syx` modifié sur le **MIDI IN** de l'appareil (`flash.sh` / `flash.bat`, SysEx Librarian ou C6),
   par câble jack stéréo depuis une interface à sortie TRS, ou par l'adaptateur DIN fourni.
   L'upgrade par le menu de démarrage **ne marche pas en USB MIDI** — MIDI IN obligatoire.
3. Détails, tests et récupération : [`notes/06-flash-et-recuperation.md`](notes/06-flash-et-recuperation.md).

## Autre chaîne d'outils

Le C [`mischa85/elektron-firmware-tool`](https://github.com/mischa85/elektron-firmware-tool) fait le même travail
de conteneur ; voir [`notes/02-format-os-syx.md`](notes/02-format-os-syx.md).
