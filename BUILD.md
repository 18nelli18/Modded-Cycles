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
   MIT) : `latching-mute`, `trig-preview`, `browser-scroll`. Notre build donne le **même MAIN OS, octet pour octet**, que leur
   propre `tweak.py` (vérifié pour chacun et pour les trois ensemble), à une retouche près : depuis le 04/10/2026, `trig-preview`
   accepte aussi le séquenceur en pause (3 octets, [note 34](notes/34-ecoute-en-pause.md)).
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
| `6ch-usbup` | `57fa258f209c10359f6888af79087f656e994930ff86ffcc1e2e2e48512d9530` |
| `sdvintage-snare` (v2, recalée sur le Syntakt) | `11049726efa102028f7365b0a672c8a244b98edcef5e7c8b5e0aafba369f60d3` |
| `6ch-multiout,sdvintage-snare` | `80d0d717c5054f9277c2ddadb588e3578968cc1427610c7367ee408fa8ffd2de` |
| `6ch-usbup,sdvintage-snare` | `9416ac0b7f0bffda6b91490aacf1b00f831196466f5f64dc87b3a3b63cbc9ccb` |
| `latching-mute,trig-preview,browser-scroll` | `c6aea7e51d1caf3e9be4553f3a0c5b033592d804cb25226ef9df3fd19add8c08` (`tweak.py` de drumkilla, sans la retouche de note 34 : `71fef138…`) |
| `6ch-usbup,latching-mute,trig-preview,browser-scroll` | `b8911cb1692476c266fdad6fae7bdabd824bd8976149cc5a2baae4dfb9252176` |

| `sdvintage-exact` (avec `--syntakt Syntakt_OS1.42.syx`) | `8e2290a79fb1406ce65b3af3c5d3d95faade666e98eb8ecce0c0fa25fe87b15d` |
| `6ch-usbup,sdvintage-exact` (idem) | `bd729d526c992fb5d678a1a2793d012fdcec47f6584631fc01afa896483fc061` |
| `syntakt-vintage` (idem) | `b4de3ec5f7eda7504bf03e7141f57bae6cf5bc137d39f6704da60881d56ed9b0` |
| `sdvintage-7th` (idem) | `c73ad4c796b94ab39d106d0798091eb39b5e3e31f66d7fe78e2db30db44daad3` |
| `syntakt-cp` (idem) | `e9e3a8c7aa438a00cc028574b78dac33a6b7a44cdf98623eaa1edcf4668ac1ee` |
| `syntakt-toy` (idem) | `a3d8fad221ed0920ec15ea0e791e3be3e869b04b147affefcda4108d0248796c` |
| `syntakt-sd-cp-toy` (idem) | `ea04669bbe10d83505cd9c2b4654f46c53dd1fc55d4d5229d2cad33c6e5f0a0e` |
| `syntakt-bits` (idem) | `0e73d4f76bb947db6392b7e1e1547f2951ec8fe1924668bec532ee9b531f93bd` |
| `syntakt-sd-cp-toy-bits` (idem) | `c6add70bea5a1f6d0d4bf6aa26ae454dc6f873c6ab55937edbd7d9ad7d96c86c` |
| `syntakt-swarm` (idem) | `b47c9d7d2fb8d9568503033a3d0f318396c4b52b8df34c081564005c92b69517` |
| `syntakt-sd-cp-toy-bits-swarm` (idem) | `c6cdfe22fe5a280c1e42ae1f11ae25156d86b36da1e9d0e83f1d6c3227117b7c` |

### Model-TG

`tweaks/model-cycles_OS1.13/30-model-tg.json` vient du build de [Model-TG](https://github.com/TinyGregAudio/Model-TG) lui-même (licence MIT),
au commit épinglé dans `tools/gen_model_tg.py`, avec les binutils m68k, depuis une copie de sa source avec ses retouches (`MC_PATCHES` : en
mode mute, chaque touche de piste mute tout de suite, [note 31 §10](notes/31-model-tg.md) ; sa copie de l'écoute d'un pas accepte le
séquenceur en pause, [note 34](notes/34-ecoute-en-pause.md) ; avec l'audio USB multipiste, une piste mutée n'est plus coupée net sur sa
piste USB, [note 35 §3](notes/35-glitches-usb-multipiste.md) ; son filtre par piste est retiré, à taille constante, au profit de
`48-track-filter`, `RM_PATCHES`, [note 47 §11](notes/47-filtre-piste.md)), plus l'envoi à l'USB à heure fixe (`tools/usb_steady.py`) :
```sh
git clone https://github.com/TinyGregAudio/Model-TG vendor/Model-TG
git -C vendor/Model-TG checkout 70b39dd6787770ebefc7a2d78dea1678ec012679   # v1.1.0
python3 tools/gen_model_tg.py --cycles model-cycles_OS1.13.syx --model-tg vendor/Model-TG [--check]
```

| `-t` | MAIN OS patché (SHA-256) |
|---|---|
| `model-tg` | `56300c8b4a543db53e06a3c7cb56193d362dbc3db274a1cd45f7d4f15476a00f` (sans nos ajouts : `a049d724…`, celle annoncée par Model-TG pour sa v1.1.0) |
| `6ch-usbup,model-tg` | `b79360772b6fe9e7e03af676ceae53cce93cb391a66764c0f84c13117883489b` |

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
| `model-tg-st,syntakt-tg-sd` | `8f08080d9b1d8f27553acef913a1872040262427ea40046876ad79859fcb4d97` |
| `model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm` | `de8cac03b9aa114e692f6de86aee33030becd145c9a739a9b15c93626d0f7065` |
| `6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm` | `010baba77269635f61638caa4d9ba4ad49575ba478f6d351260a5451991616ac` |

Le flasher web vérifie chaque mod, à chaque build, contre l'outil Python ([note 49](notes/49-verification-mod-par-mod.md)) :
`REF_MODS` de `docs/flasher/app.js` donne l'empreinte des écritures et de la charge utile de chaque tweak, et `REF_MAINOS`
le MAIN OS d'un échantillon de combinaisons (chaque carte seule, chaque paire, les plus grandes : 464 aujourd'hui).
`tools/ref_mainos.py` réécrit les deux blocs (`--check` pour vérifier) ; `tools/check_overlaps.py` prouve, sans firmware,
que deux mods qu'on peut cocher ensemble n'écrivent jamais aux mêmes octets (sauf écriture identique ou mod posé
par-dessus l'autre par `requires`) ; `tools/registry.py` écrit `tweaks/model-cycles_OS1.13/REGISTRY.md`, le registre
de la place libre (masques de sprites pris et libres, caves, charges utiles) et des crochets posés sur l'OS
([note 52](notes/52-registre-place-libre.md)), à régénérer et commettre avec tout nouveau tweak ;
`tools/webflash_smoke.sh model-cycles_OS1.13.syx Syntakt_OS1.42.syx` reconstruit l'échantillon dans la page et le compare.
SD VINTAGE v1 (clean-room d'origine, **testée sur le matériel** le 29/09/2026, compilée par GCC 13.3) donnait `80b7b2bd…` seule et `38754937…` avec `6ch-usbup` ;
la v2 est compilée par `m68k-elf-gcc` 16.2 (Homebrew), voir [note 16 §6](notes/16-moteur-syntakt.md).

### Écoute des samples (Model-TG)

`tweaks/model-cycles_OS1.13/33-sample-preview.json` (sur `model-tg`) et `33-sample-preview-st.json` (sur `model-tg-st`,
mêmes écritures) sont produits par `tools/gen_sample_preview.py`, qui assemble `tools/machines/sample_preview/` et le lie
dans quatre masques de sprites 47×47 libérés, partagés avec `chord-keys`, qui exclut Model-TG (`conflicts`)
([note 46](notes/46-ecoute-des-samples.md)). Le code appelle celui de
Model-TG aux adresses des `symbols` de `30-model-tg*.json` ; le générateur vérifie ce code avant d'écrire. Le tweak
exige Model-TG (`requires`) : les builds de Model-TG sans lui ne changent pas. La preuve fait tourner le vrai code de
l'OS et de Model-TG, du navigateur à la boucle des voix (avec `--syntakt` seul, les deux versions) :
```sh
python3 tools/gen_sample_preview.py --cycles model-cycles_OS1.13.syx [--check]
python3 tools/build.py -i model-cycles_OS1.13.syx -t model-tg,sample-preview
python3 tools/build.py -i model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx \
    -t model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm,sample-preview-st
python3 tools/emu/test_sample_preview.py --cycles model-cycles_OS1.13.syx \
    [--with 6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm,arp,trig-hold,tempo-max,boot-anim] \
    [--syntakt Syntakt_OS1.42.syx]
```

| `-t` | MAIN OS patché (SHA-256) |
|---|---|
| `model-tg,sample-preview` | `a6a4aa2228db2fb126e5ea88822f962f8a743ee77af96842f366f0f2ee1c88b5` |
| `6ch-usbup,model-tg,sample-preview` | `4a9b2f67213f1af1ccd2d740aa64c32032ac33904d5884ca2eaed1dead9c3e36` |
| `model-tg,arp,trig-hold,tempo-max,boot-anim,sample-preview` | `df6adf9607db59875408097821ce28d9a45c30e942cb7985c57f117550410998` |
| `model-tg-st,syntakt-tg-sd,sample-preview-st` (avec `--syntakt`) | `867e8e4298024b787d15c02b605e38188fc82353a2a5e773504347c483142be5` |
| `model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm,sample-preview-st` (idem) | `9b0eb18e944bf9c3cfd70c6daae253dee2ba7e3f794e63b2d2fad57c65fe644f` |
| `6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm,sample-preview-st` (idem) | `54536f98a9f599d2886a09fd969eb4fed4e336024d798d81491f642290661d4a` |
| `6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm,trig-hold,arp,tempo-max,boot-anim,sample-preview-st` (idem) | `8d491ab9e77bc53fcb7f812403f857e090b82ac3aad195944c667263496275f9` |
| `model-tg-st,macro-tg,sample-preview-st` (avec la machine MACRO) | `9e3b1ce3972403c2bfec864c7691bfeef00c0161fde6e2778c7d64b5946b710e` |

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
| `model-tg,arp` | `cf121fb269111b6c57c74736d05916f9c16168b2c22142b5b1d192351bf7b22a` |
| `6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm,arp` | `88cddfd13f999a4bfa75df6415fa3faadcde584b42a9c15f3a497e0cf199d6a9` |

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
| `6ch-usbup,trig-hold` | `5be28240875818efd2b912680bb589300cd51a2c0aa4a86ae289b3241fbf7f44` |
| `model-tg,trig-hold` | `286a46c7ea7a8371060e47ed01ca4840be7495775f64c7391b0e56b26625d34c` |
| `6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm,trig-hold,arp` | `4e46adc484059955a8b1caa23bbfa56e965519dc2e36001b5f54462463ea1697` |

Avec `6ch-usbup`, les deux tweaks réécrivent de la même façon le pointeur du sprite dont le masque est libéré.

### Tempo jusqu'à 546 BPM

`tweaks/model-cycles_OS1.13/42-tempo-max.json` est produit par `tools/gen_tempo_max.py` : les six bornes à 300 BPM (moteur,
horloge MIDI reçue, projet, pattern, menu Tempo) passent à 546,0 BPM, plafond du champ 16 bits du projet, ainsi que les deux
contrôles au chargement ; la remise dans le cycle de la phase du LFO devient une boucle (au-delà de 351,6 BPM, le pas peut
dépasser un cycle). 12 écritures, aucune place libre ([note 38](notes/38-tempo-546-bpm.md)). La preuve fait tourner le vrai
code de l'OS, d'origine et modifié, jusqu'aux 6 LFO (EMAC exacte) :
```sh
python3 tools/gen_tempo_max.py --cycles model-cycles_OS1.13.syx [--check]
python3 tools/emu/test_tempo_max.py --cycles model-cycles_OS1.13.syx
```

| `-t` | MAIN OS patché (SHA-256) |
|---|---|
| `tempo-max` | `5d6417b175e89b68c76743bbcad45306ba210969ad049fc1bfa6da46e432eaef` |
| `6ch-usbup,tempo-max` | `0f7a47738be9a70aa3c8e586d28636c535d787693ddf6cc756c92b5824717d42` |
| `model-tg,tempo-max` | `7ba3424c47f023a0a3de3f8952bdf26eb58c94d2f4a4b9df70783de0d4339d95` |
| `6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm,trig-hold,arp,tempo-max` | `3a0d2672e7791f62f41439987435609bd7a63d8284b8841bcef5ec06cb17e5dd` |

### OS Cycles pour Model:Samples (et retour par USB)

Pas un tweak : `tools/crossflash.py` met l'OS Cycles officiel dans le conteneur officiel du Model:Samples, en changeant les
32 octets de la constante de sa clé de vérification (`0x401296b2`) pour qu'il accepte la signature du Samples ; le retour
est l'OS Samples officiel, inchangé, dans le transport SysEx du Cycles ([note 41](notes/41-os-cycles-sur-samples.md)).
La clé vient du `.syx` officiel du Samples, jamais du dépôt. La preuve fait tourner les vérifications de mise à jour des
deux OS sur les deux fichiers :
```sh
python3 tools/crossflash.py --cycles model-cycles_OS1.13.syx --samples model-samples_OS1.13.syx --to samples
python3 tools/crossflash.py --cycles model-cycles_OS1.13.syx --samples model-samples_OS1.13.syx --back-samples
python3 tools/emu/test_crossflash_samples.py --cycles model-cycles_OS1.13.syx --samples model-samples_OS1.13.syx
```

| Fichier | SHA-256 |
|---|---|
| `model-cycles_OS1.13_for-model-samples.syx` | `c06c23f31e50fac6ad40cd0f633acd4a7da4f63c929dff563dae887b93105dd4` |
| son MAIN OS | `b6fbc48f7d7d07cecae3859e07270fa2298f393e8afa2643144bdb4efc317aad` |
| `model-samples_OS1.13_back-from-cycles-os.syx` | `d63ce13dd1a5039d11b60d3f69d4e88e9d0f56fb2e7350c105ec641d32083680` |

### OS Cycles avec mods pour Model:Samples

Le firmware est **toujours l'OS du Model:Cycles**, avec les mods choisis, quelle que soit la machine
([note 57](notes/57-os-cycles-quelle-que-soit-la-machine.md)) : sur un Model:Samples, le sampling vient de Model-TG. On
construit les mods comme pour un Model:Cycles, puis `tools/mods_for_samples.py` met ce MAIN OS dans le conteneur officiel
du Samples avec le même correctif de 32 octets que `crossflash.py --to samples` (toujours appliqué), et écrit deux
fichiers : `_smp-os` pour un Model:Samples sous son OS (transport `0x0F`), `_cyc-os` pour un Model:Samples déjà sous un
OS Cycles de la page ou de ce script (transport `0x11`, pour changer de mods). La page fait la même chose
(`MCBuilder.modsForSamples`, choix de la machine dans l'onglet Mods).
```sh
python3 tools/build.py -i model-cycles_OS1.13.syx -t model-tg,arp -o mods.syx
python3 tools/mods_for_samples.py --cycles model-cycles_OS1.13.syx --samples model-samples_OS1.13.syx --mods mods.syx
python3 tools/emu/test_mods_for_samples.py --cycles model-cycles_OS1.13.syx --samples model-samples_OS1.13.syx \
    --syntakt Syntakt_OS1.42.syx
```

Sans mods (l'OS Cycles officiel en `--mods`), le fichier `_smp-os` est octet pour octet celui de
`crossflash.py --to samples`. Empreintes de la preuve (le MAIN OS installé est celui de `REF_MAINOS` sauf les 32 octets
de la clé) :

| Combinaison | `_smp-os` (SHA-256) | `_cyc-os` (SHA-256) |
|---|---|---|
| `model-tg` | `1985e8e703092b768d32aa2c9b446cb0f95c1f944dc3e206f75973337469f686` | `1317199fbc625c38700344b69ce00496cdee0c8be6fae305843e6373e6394d19` |
| `6ch-usbup,model-tg` | `fdbf4621e291618a98de64c561a39de59852d5a4dfdb58c927e312467557a839` | `a5a21ac6dfe5697b9e39fa80518a53989af4be8edac3cf9cbe6f1ebddb00ce79` |
| `model-tg-st,sample-preview-st,macro-tg` | `4b069c69c47c6ef55ab6e50d067b2a8ced067fe3ed1b883419f5731db4044f5f` | `156ef6c22544de9873ed2119b30d4619354848cd27ca429e79bd1d628c586ffd` |
| `6ch-usbup,model-tg-st,sample-preview-st,trig-hold,arp,tempo-max,boot-anim,syntakt-tg-sd-cp-toy-bits-swarm` | `f030b1a210c3ed9e5e2026dd0ac00daa99ca2a99cb963133f27d7e160f36fbcc` | `62d70e2bac0b22af70a56f71dc24791c52f79bda105c6375b9a3561a7e6b8a96` |

### Animation de démarrage modded-cycles

`tweaks/model-cycles_OS1.13/43-boot-anim.json` est produit par `tools/gen_boot_anim.py` : le corps de la tâche d'animation de
démarrage de l'OS (`0x40053a6c`) est réécrit à sa place, assemblé depuis `tools/machines/boot_anim/` (690 o sur 1 032, aucune
place libre). Mêmes 80 images de 20 ms, même fin ; les carrés du logo puis « modded-cycles » ([note 39](notes/39-animation-demarrage.md)).
La preuve fait tourner la tâche d'origine et la nouvelle avec le vrai code de l'écran de l'OS, jusqu'au registre du DSPI1, et
compare chaque image vue sur l'écran au modèle du générateur ; le modèle de l'écran est d'abord validé par un « 7 » des grands
chiffres de l'OS, écrit par son code de texte (l'OS compte les lignes depuis le bas, note 39 §2) ; `--gif` écrit l'animation vue :
```sh
python3 tools/gen_boot_anim.py --cycles model-cycles_OS1.13.syx [--check]
python3 tools/emu/test_boot_anim.py --cycles model-cycles_OS1.13.syx [--gif anim.gif] \
    [--with 6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm,arp,trig-hold,tempo-max]
```

| `-t` | MAIN OS patché (SHA-256) |
|---|---|
| `boot-anim` | `388ed6c6ee65529e2dc2d2c93aadb37c6878324acf90ad931d5ca3f7c6b68b27` |
| `6ch-usbup,boot-anim` | `76b1a532c8119ce222a3545b8a21b4cf0b2e12887e40c32f9a80b0d70975533e` |
| `model-tg,boot-anim` | `02bc2c9498bd8364f95bc3359f6009715f11884781e1293d5dd5995bfd136de5` |
| `6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm,trig-hold,arp,tempo-max,boot-anim` | `2c3d7bc3b1b2cd11b21cc9c9c91989407319b95cdc3129135109ba124f5fd9b3` |

### Accords de gamme sur TRIG 1–16

Contribution de Nico Heuser ([PR #46](https://github.com/18nelli18/Modded-Cycles/pull/46)).
`45-chord-keys.json` est généré depuis `tools/machines/chord_keys/` par `tools/gen_chord_keys.py`
(GCC m68k-elf 16.2.0, binutils 2.47 : ceux de Homebrew, ou compilés depuis les sources d'Ubuntu comme au
[§16 de la note 42](notes/42-clavier-accords-diatoniques.md)). Le générateur refuse `m68k-linux-gnu-gcc` : son ABI lit
dans `a0` les pointeurs que l'OS rend dans `d0`, ce qui fausserait les appels à l'OS ([note 42 §6](notes/42-clavier-accords-diatoniques.md)).
**Testé** sur la machine par Maxime, seul et avec six autres mods (07/10/2026), puis la correction de la note
bloquée (note 42 §16, 10/10/2026). Sélectionnez une piste CHORD,
puis activez **Keys** dans **FUNC + RETRIG**. Root, Scale et I–VII choisissent la tonique, le mode
et les extensions diatoniques ; le majeur s'affiche **MAJ**. Hors édition des pas, TRIG 1–7 jouent I–VII,
8–14 les mêmes degrés une octave plus haut, 15–16 I–II deux octaves plus haut. Les grands pads T1–T6
conservent leur sélection et leur jeu stock ; les accords des TRIG ne déclenchent pas le retrig/arpège.
Réglages par piste, enregistrés avec le pattern. **I–VII** seuls choisissent les extensions ; **SHAPE** règle
la disposition (**BASE**, **CLS0–3**, **OPN0–3**) et **COLOR** les niveaux, sans changement d'octave.
Model-TG est explicitement incompatible.

Quatorze masques identiques sont redirigés avant d'y placer les 5 063 octets de code, constantes et état ; seule la section 3 change. Aucun firmware
n'est distribué dans le dépôt. Génération, preuve autonome, puis preuve avec tous les mods compatibles :

```sh
python3 tools/test_chord_keys.py
python3 tools/gen_chord_keys.py --cycles firmware/model-cycles_OS1.13.syx --check
python3 tools/emu/test_chord_keys.py --cycles firmware/model-cycles_OS1.13.syx
python3 tools/emu/test_chord_keys.py --cycles firmware/model-cycles_OS1.13.syx \
  --with 6ch-usbup,latching-mute,trig-preview,browser-scroll,trig-hold,arp,tempo-max,boot-anim,syntakt-sd-cp-toy-bits-swarm \
  --syntakt firmware/Syntakt_OS1.42.syx
python3 tools/emu/test_chord_keys_release.py --cycles firmware/model-cycles_OS1.13.syx
python3 tools/build.py -i firmware/model-cycles_OS1.13.syx -t chord-keys \
  -o build/model-cycles_OS1.13_chord-keys.syx
```

| `-t` | MAIN OS patché (SHA-256) |
|---|---|
| `chord-keys` | `901675f5b8291f3b91d134208236e83431d6a079c73c2d5f1e4e54ebc334321f` |
| `6ch-usbup,chord-keys` | `d6e43f0ca6a8df953df7a12da7458c70552f1b3a8de1bb39213f0c52168f0352` |
| `6ch-usbup,arp,trig-hold,tempo-max,boot-anim,chord-keys` | `0922d3967c6d29ea86c14ffe41a5555cfb5346ecffb6298fe84c8ba3e3c51c43` |
| `macro,chord-keys` | `5acc062be3c532f94e13615c7da89f3e1a60eab8520a9ee1e89d2113669505e9` |
| `6ch-usbup,latching-mute,trig-preview,browser-scroll,trig-hold,arp,tempo-max,boot-anim,chord-keys,syntakt-sd-cp-toy-bits-swarm` | `569e6bb39b628ebbd8a8f1ef64e43f0097f4c3d4bb8430974f01dab6d82ca110` |

La preuve exécute les touches, pads, menus, sauvegardes et calculs CHORD du véritable OS ; 14 000 accords
BASE, 2 205 combinaisons SHAPE et les chemins inactifs sont comparés à la référence. COLOR, les frontières de
SHAPE, les libellés et le plafond aigu du premier opérateur sont contrôlés. Les frontières simulées, le coût en instructions et
les vérifications restantes sur la machine sont détaillés dans [la note 42](notes/42-clavier-accords-diatoniques.md).
Les accords étendus restent limités à quatre notes ; l'enregistrement conserve la fondamentale et le réglage
du degré s'applique à la relecture, sans enregistrer une extension différente par trig.

### Machine MACRO (les modèles de Braids)

`tweaks/model-cycles_OS1.13/25-macro.json` (7e machine) et `32-macro-tg.json` (avec Model-TG : 8e machine, par-dessus
`model-tg-st`) sont produits par `tools/gen_macro.py` : le code de Braids d'Émilie Gillet (MIT,
[pichenettes/eurorack](https://github.com/pichenettes/eurorack) au commit `08460a6`, stmlib `e3bd7c9`) compilé tel quel
avec la passerelle `tools/machines/macro/macro.cc`, en charge utile rangée après l'image et reconstituée au démarrage à
`0x43000000` (`0x46700000` avec Model-TG), avec la mécanique des machines ajoutées des moteurs du Syntakt
([note 43](notes/43-machine-macro.md)) ; 13 modèles rendus à 48 kHz et le lo-fi RATE/BITS sur FINE
([note 55](notes/55-macro-allegee-et-lofi.md)). Le générateur a besoin du clone d'eurorack (sous `vendor/`, ignoré par git) et de
`m68k-linux-gnu-g++` (les JSON versionnés viennent du GCC 13.3 d'Ubuntu 24.04 : un autre GCC donne d'autres octets) ; la
preuve, de `g++` pour Braids compilé pour l'ordinateur, la référence :
```sh
git clone https://github.com/pichenettes/eurorack vendor/eurorack
git -C vendor/eurorack checkout 08460a69a7e1f7a81c5a2abcc7189c9a6b7208d4
git -C vendor/eurorack submodule update --init stmlib
python3 tools/gen_macro.py --cycles model-cycles_OS1.13.syx --eurorack vendor/eurorack [--check]
python3 tools/emu/test_macro.py --cycles model-cycles_OS1.13.syx --eurorack vendor/eurorack [--quick] \
    [--with 6ch-usbup,model-tg-st,sample-preview-st,trig-hold,arp,tempo-max,boot-anim]
python3 tools/emu/test_macro.py --cycles model-cycles_OS1.13.syx --eurorack vendor/eurorack --spectres   # notes/55 §2
```
Avec les moteurs du Syntakt : les tweaks combinés de la section suivante. Incompatible avec SD VINTAGE (même mécanique,
même place).

| `-t` | MAIN OS patché (SHA-256) |
|---|---|
| `macro` | `f39223c286166b1d018d215b36e3fbd3dedaba9ed05681a2784c407c92f6d7c6` |
| `6ch-usbup,macro` | `bf83bbf3c61495114e427dd70f46fb84270617476afd5309456adb4c9fe21bc0` |
| `model-tg-st,macro-tg` | `f710475fbfb15caa261c81a3a13e99bc21385caab8adc3d93595b8ab56dd4ebe` |
| `6ch-usbup,model-tg-st,macro-tg,trig-hold,arp,tempo-max,boot-anim` | `b1295ad6789430649dc190654e6483c26d9fb9c305bf0d328c669aceebdc7bb1` |

### MACRO avec les moteurs du Syntakt

`tweaks/model-cycles_OS1.13/24-syntakt-<moteurs>-macro.json` et `31-syntakt-tg-<moteurs>-macro.json` (avec Model-TG,
par-dessus `model-tg-st`) sont produits par `tools/gen_macro_syntakt.py` : les moteurs exactement comme dans leur tweak
(passerelle reprise octet pour octet, pas recompilée), MACRO en dernière machine, après eux ; la charge utile commune
(476 128 o) est rangée compressée et décompressée au démarrage ([note 50](notes/50-macro-avec-moteurs-syntakt.md)).
Mêmes besoins que les deux mods (fichier Syntakt, clone d'eurorack, `m68k-linux-gnu-g++` 13.3) :
```sh
python3 tools/gen_macro_syntakt.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx \
    --eurorack vendor/eurorack [--engines sd,cp] [--tg] [--check]
python3 tools/emu/test_macro_syntakt.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx \
    --eurorack vendor/eurorack [--engines sd,cp] [--only alone|tg] [--with 6ch-usbup,trig-hold,arp,tempo-max,boot-anim]
```

| `-t` (avec `--syntakt Syntakt_OS1.42.syx`) | MAIN OS patché (SHA-256) |
|---|---|
| `syntakt-sd-macro` | `db0cf81eb99790a7da888cd220386dd93b4ad9f5d88495b4948d22e1e791d1f3` |
| `syntakt-sd-cp-toy-bits-swarm-macro` | `10f4e481090ec12bdb73760f89cc307f9fc755060758173c24de15820217cb9f` |
| `6ch-usbup,syntakt-sd-cp-toy-bits-swarm-macro,trig-hold,arp,tempo-max,boot-anim` | `89370adafa0491712dc2d710d85a6d3bf6b60d19f6a0702ac950bde24e387b32` |
| `model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm-macro` | `76409e8cf573361b96acfad732d26c3c85430c04b02bca9ddd65a722b6be0f5d` |
| `6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm-macro,trig-hold,arp,tempo-max,boot-anim` | `29b8a65099b27dcb1c0d2f1a10fbcc0044a9cb9acf552e4e3af3b36a31f27402` |
| `6ch-usbup,model-tg-st,sample-preview-st,syntakt-tg-sd-cp-toy-bits-swarm-macro,trig-hold,arp,tempo-max,boot-anim` | `224cf1584265de8a720072465e3e973430e653617b4fdca0e8cc8b83cd7bd89f` |

### Navigateur sur plusieurs lignes

`tweaks/model-cycles_OS1.13/44-multiline-browser.json` est produit par `tools/gen_multiline_browser.py`, qui assemble
`tools/machines/multiline_browser/multiline_browser.S` (370 o) dans le masque de sprite 47×47 libéré `0x401904b4`
(`tools/sprites.py`) : le navigateur de presets (sons, dossiers, échantillons de Model-TG) montre 3 lignes en petite police au
lieu d'une, « > » devant la ligne du curseur, le son chargé inversé, un repère de 7 px pour les dossiers. Quatre accroches dans
le dessin `0x400a539c`, huit constantes, et deux retouches de la liste dans un sous-dossier de +Drive (`0x4003f622`,
`0x400406a8`) pour que le curseur y descende sur les 3 lignes au lieu de rester sur la 1ʳᵉ ; l'accroche du défilement des noms longs (`0x400a55a1`, browser-scroll et Model-TG)
n'est pas touchée et ne sert qu'à la ligne du curseur ([note 40](notes/40-navigateur-multiligne.md)). La preuve fait tourner le
vrai dessin, avec les vraies polices, dans un vrai écran de l'OS ; `--png` écrit l'écran d'origine et le modifié :
```sh
python3 tools/gen_multiline_browser.py --cycles model-cycles_OS1.13.syx [--check]
python3 tools/emu/test_multiline_browser.py --cycles model-cycles_OS1.13.syx [--png dossier] \
    [--with 6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm,trig-hold,arp,tempo-max --syntakt Syntakt_OS1.42.syx]
```

| `-t` | MAIN OS patché (SHA-256) |
|---|---|
| `multiline-browser` | `75a5054403de65968e07bed84f3fcb183719b965626fd0c042b29bc963f8af31` |
| `6ch-usbup,multiline-browser` | `ce1681cd208f4ca812f25b9386ad64fd0c4aa5957314cde5ba6f77a302d2c49f` |
| `browser-scroll,multiline-browser` | `32e4a6b8e3897a1faa8ab12b33cd8e82b5a214cd3e91b80824ab17bc9d6042c1` |
| `model-tg,multiline-browser` | `be23e22f382e26612aa759f8877c14834b22bafe38027df2fd0942516c391ca4` |
| `boot-anim,multiline-browser` | `120860e74d59d207951128ed926d8e0196d9d16142c6a67b004d64510bed339e` |
| `6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm,trig-hold,arp,tempo-max,boot-anim,multiline-browser` | `433ebe27c1742aa9abe5d6cbdaf2269b3319f4c7910ddddf5bf05d786b2a2fef` |

### Volume et pan en chiffres sur l'écran principal

`tweaks/model-cycles_OS1.13/46-level-pan-values.json` est produit par `tools/gen_level_pan.py` : d'après le mod de djd_oz,
LEVEL/DATA affiche le volume de la piste sélectionnée (0 à 127) à la place du haut-parleur, FUNC + LEVEL/DATA son pan (-64 à
63) à la place du « R », 3 s après le dernier mouvement ; LEVEL/DATA avance de 1 au lieu de 2 sur l'écran principal. Assemblé
depuis `tools/machines/level_pan/` dans deux masques de sprites libérés ([note 44](notes/44-volume-pan-en-chiffres.md)). La
preuve passe par le vrai tick de la tâche de l'interface, le pas de LEVEL/DATA, le gestionnaire des encodeurs et le dessin de
l'écran principal, compare chaque pixel au modèle pour les 256 valeurs, et, avec `--djd`, au fichier de djd_oz ; `--show`
dessine l'écran avec les barres de l'OS :
```sh
python3 tools/gen_level_pan.py --cycles model-cycles_OS1.13.syx [--check]
python3 tools/emu/test_level_pan.py --cycles model-cycles_OS1.13.syx [--show] \
    [--djd model-cycles_OS1.13_PAN-Level-values-3s-turn-only.syx] \
    [--with 6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm,arp,trig-hold,tempo-max,boot-anim,trigless-dim \
     --syntakt Syntakt_OS1.42.syx]
```

### Trigless trigs atténués

`tweaks/model-cycles_OS1.13/47-trigless-dim.json` est produit par `tools/gen_trigless_dim.py` : d'après le mod de djd_oz, en
mode grille, une touche qui porte un trigless trig prend l'état de LED 260 (traité comme 4 par l'OS) ; l'interruption du
panneau, qui charge les verrous des LED, ne l'allume qu'une milliseconde sur trois (333 Hz) en rechargeant sa rangée en plus
du tour d'origine. Assemblé depuis `tools/machines/trigless_dim/` dans deux masques de sprites libérés
([note 45](notes/45-trigless-trigs-attenues.md)). La preuve fait tourner le vrai code de l'interruption du panneau, du tick des
LED et de l'image de l'interface sur une même ligne de temps, d'origine contre modifié, avec un modèle des verrous ; `--defsym`
construit les variantes d'essai (jamais versionnées, `--out` hors de `tweaks/`) :
```sh
python3 tools/gen_trigless_dim.py --cycles model-cycles_OS1.13.syx [--check]
python3 tools/gen_trigless_dim.py --cycles model-cycles_OS1.13.syx --defsym WAIT=68 --out essai-0p5us.json
python3 tools/emu/test_trigless_dim.py --cycles model-cycles_OS1.13.syx \
    [--with 6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm,arp,trig-hold,tempo-max,boot-anim,level-pan-values \
     --syntakt Syntakt_OS1.42.syx]
```

| `-t` | MAIN OS patché (SHA-256) |
|---|---|
| `level-pan-values` | `7fb415147e8605ab035e3fc064986b1c640cddc7ced972ad5b6ff6fcaa9f5eb7` |
| `trigless-dim` | `ff47b71399d7ab72a53f73e2e0ff0f5759e4ef20fe1da1780eb0c28e85ed4631` |
| `level-pan-values,trigless-dim` | `c4a547df87f681e27e5f7d0b04d9e08d601017577f810e2dced51eb4a68797e6` |
| `model-tg,level-pan-values,trigless-dim` | `d1af08f19b37b65255d5da62741943ab265577119540965787de50bc6c23fd54` |
| `6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm,trig-hold,arp,tempo-max,boot-anim,level-pan-values,trigless-dim` | `82d422e6b3eb2ee782aefd3b5ce1edbf1c5420ae94145c5ec5839ff13dd2a2ab` |

### THRU qui envoie aussi le MIDI du Cycles (d'AveyCole)

Deux tweaks d'AveyCole ([AveyCole/Modded-Cycles](https://github.com/AveyCole/Modded-Cycles), commit `ba5f8bb`), produits par
`tools/gen_midi_thru.py`, qui s'excluent ([note 53](notes/53-midi-thru-aveycole.md)) :

- `50-midi-both.json` (`midi-both`) : avec THR choisi dans CONFIG › MIDI › PORTS › OUT/THRU, le Cycles relaie le MIDI reçu et
  envoie aussi son horloge, ses notes et ses paramètres. Les trois portes de sortie (`0x4000154a`, `0x4000156a`, `0x40001590`)
  ne lisent plus le réglage. Aucune place libre.
- `51-midi-live-both.json` (`midi-live-both`) : sur la ligne OUT/THRU qui affiche THR, FUNC + appui sur LEVEL/DATA alterne THR
  seul et THR + MIDI du Cycles (valeur 2 du réglage `0x404e9b50`). `tools/machines/midi_thru/midi_thru.S` (132 o) est assemblé
  dans le masque de sprite 34×34 libéré `0x40192ba4` (`tools/sprites.py`) ; le fork le mettait en `0x40167c50`.

La preuve fait tourner les vraies portes de sortie, le vrai relais, la vraie touche de la ligne et son affichage, d'origine et
modifiés, et compare avec la version du fork :
```sh
python3 tools/gen_midi_thru.py --cycles model-cycles_OS1.13.syx [--check]
python3 tools/emu/test_midi_thru.py --cycles model-cycles_OS1.13.syx \
    [--with 6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm,trig-hold,arp,tempo-max --syntakt Syntakt_OS1.42.syx]
```

| `-t` | MAIN OS patché (SHA-256) |
|---|---|
| `midi-both` | `5d0755ef0bd34617bcd5adbb54f09c77cd066e7439d26cc460bbadb0090bb75f` |
| `midi-live-both` | `ca439a48cb8d818c8c09a8bfc8fa1ac391ffa5f9263e971db39ff602afce6742` |
| `6ch-usbup,midi-both` | `efc0f1c328f8b65eedd45bc20dd68b513eb091ea1c67d8d3fba0d0e60081b17a` |
| `6ch-usbup,midi-live-both` | `09f5b51061b2d387c897824984618f7f8b92d2d5028750115b3f6cb3eb2748dc` |
| `model-tg,midi-live-both` | `6cb5a13cd7c98c4e50dcaaaf0a3e92e5857de71307bc90b2301477b8c4950946` |
| `6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm,trig-hold,arp,tempo-max,boot-anim,multiline-browser,midi-both` | `b5842855f66e1a432fa268916c8da255187f9adbba0c8251ba1a5913a62d7037` |
| `6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm,trig-hold,arp,tempo-max,boot-anim,multiline-browser,midi-live-both` | `6678a43aea610a2c235cc0032d21d0d5eba53984022215756724e8457337017e` |

### Filtre par piste

`tweaks/model-cycles_OS1.13/48-track-filter.json` est produit par `tools/gen_track_filter.py` : le filtre (`track_filter.S`), les
potards, l'affichage et la sauvegarde (`tf_ui.S`) sont assemblés depuis `tools/machines/track_filter/` et liés par
`track_filter.ld` dans quinze masques de sprites 35×35 libérés (3 001 o) ; les tables sont calculées par le générateur. Quatre
paramètres de toutes les machines sur les descripteurs « Error » 1 à 4, accroche après Volume + Dist ([note 47](notes/47-filtre-piste.md)).
Le même script écrit `48-track-filter-tg.json` et `48-track-filter-tg-st.json`, le filtre par-dessus `model-tg` ou
`model-tg-st` (sans son filtre de piste) : sauvegarde chaînée avec celle de Model-TG, côté stéréo du Sampler filtré, seize
masques ([note 47 §11](notes/47-filtre-piste.md)). La preuve fait tourner la vraie boucle des voix et le vrai site de l'accroche, l'OS sans
le filtre à côté, puis l'interface et la sauvegarde fonction par fonction :
```sh
python3 tools/gen_track_filter.py --cycles model-cycles_OS1.13.syx [--check]
python3 tools/emu/test_track_filter.py --cycles model-cycles_OS1.13.syx [--quick] \
    [--with 6ch-usbup,syntakt-sd-cp-toy-bits-swarm,arp,trig-hold,tempo-max,boot-anim --syntakt Syntakt_OS1.42.syx]
    [--with syntakt-sd-cp-toy-bits-swarm-macro,6ch-usbup,chord-keys,level-pan-values,trigless-dim,multiline-browser,… --syntakt Syntakt_OS1.42.syx]
    [--with model-tg,6ch-usbup,sample-preview,…]
    [--with model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm[-macro],sample-preview-st,6ch-usbup,… --syntakt Syntakt_OS1.42.syx]
```

| `-t` | MAIN OS patché (SHA-256) |
|---|---|
| `track-filter` | `a4b782e30ab8787588337a5b7fad3a49ae04e9991e39948c310651298925c339` |
| `6ch-usbup,track-filter` | `6c1efc7852909c7175f792892ec0f8bd35923f7ab64b26ee9d60b214b6615d96` |
| `6ch-usbup,syntakt-sd-cp-toy-bits-swarm,trig-hold,arp,tempo-max,boot-anim,track-filter` | `83a344a4fd64b7e3b6f98e58149874390193306871294a704f4a6f5c8fa6ad8c` |
| `macro,track-filter` | `af02e6411df4ab6c53bf98afcdcc817d3626ad123ec66ade3061fd9fe9f2cce7` |
| `model-tg,track-filter-tg` | `adcc9e26cfa4c488849483173ef4e1dafd29985aae1c4fe0e65c85997a0b125d` |
| `6ch-usbup,model-tg,sample-preview,track-filter-tg` | `d0e6080419f9bd70672e3ce48b2a87b71c49fc058d40507aff1e73a47ea1d758` |
| `model-tg-st,macro-tg,track-filter-tg-st` | `4f5b284d7905532adfc1791d9f90bad8cce8161e9cfc8287f1e9e8afe0226e1d` |
| `6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm,sample-preview-st,track-filter-tg-st` | `63b6166584eb0554d816fa7903a8093466c28638240727947d80315b2346bf8c` |
| `6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm-macro,sample-preview-st,track-filter-tg-st` | `218a55eda822625c66836357d3418bcf1f3a0724deae657526c200714953817a` |

### Écoute d'un pas en pause

`trig-preview` (et sa copie dans Model-TG) accepte le séquenceur en pause, où le met un Stop MIDI reçu même à l'arrêt : 3 octets
retouchés en `0x40148a30` ([note 34](notes/34-ecoute-en-pause.md)). La preuve passe par le vrai gestionnaire du Stop MIDI de l'OS,
puis par le mode grille :
```sh
python3 tools/emu/test_trig_preview.py --cycles model-cycles_OS1.13.syx \
    [--with 6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm,arp,trig-hold --syntakt Syntakt_OS1.42.syx]
```

### Variante `6ch-usbup`

`tweaks/model-cycles_OS1.13/11-6ch-usbup.json` n'est pas écrit à la main : `tools/relocate_6ch.py` le dérive du patch 6 canaux
(stubs déplacés dans une cave ; descripteurs et table des modes USB laissés d'origine), sans l'image firmware, avec les binutils m68k.
Depuis la [note 35](notes/35-glitches-usb-multipiste.md), il rend aussi le flux USB robuste : envoi de chaque bloc au début de
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
python3 tools/emu/test_model_tg.py --cycles model-cycles_OS1.13.syx                                  # Model-TG seul (notes/31, notes/35 §3)
python3 tools/emu/test_model_tg_syntakt.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx   # version combinée
python3 tools/ref_mainos.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx --check
```
Pour ajouter un moteur : l'ajouter à `CATALOG` de `tools/gen_syntakt_engines.py` (et ses plages copiées), puis relancer
`gen_syntakt_engines.py --all` et `--all --tg`, `gen_flasher_tweaks.py`, `check_overlaps.py` et `ref_mainos.py`, et tester chaque
nouveau tweak en émulation.

## Flasher (rappel)

1. **STARTUP MENU** : éteindre, maintenir **[FUNC]**, allumer, **[TRIG 4]** (OS UPGRADE).
2. Envoyer le `.syx` modifié sur le **MIDI IN** de l'appareil (`flash.sh` / `flash.bat`, SysEx Librarian ou C6),
   par câble jack stéréo depuis une interface à sortie TRS, ou par l'adaptateur DIN fourni.
   L'upgrade par le menu de démarrage **ne marche pas en USB MIDI** — MIDI IN obligatoire.
3. Détails, tests et récupération : [`notes/06-flash-et-recuperation.md`](notes/06-flash-et-recuperation.md).

## Autre chaîne d'outils

Le C [`mischa85/elektron-firmware-tool`](https://github.com/mischa85/elektron-firmware-tool) fait le même travail
de conteneur ; voir [`notes/02-format-os-syx.md`](notes/02-format-os-syx.md).
