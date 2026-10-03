# Provenance des tweaks

| Fichier | Auteur | Origine |
|---|---|---|
| `01-latching-mute.json`, `02-trig-preview.json`, `03-browser-scroll.json` | drumkilla | [drumkilla/elektron-model-tweaks](https://github.com/drumkilla/elektron-model-tweaks), commit `6e0b4df`, `tweaks/model-cycles_OS1.13/`. Repris **sans modification** (licence MIT, texte dans [`tools/mtlib/LICENSE`](../../tools/mtlib/LICENSE)). |
| `10-6ch-multiout.json` | d'après scottmetoyer | Table de patchs de [scottmetoyer/ms-multi-output](https://github.com/scottmetoyer/ms-multi-output) (MIT), cible Cycles, mise au format tweak ([note 01](../../notes/01-ms-multi-output.md)). |
| `11-6ch-usbup.json` | ce projet | Dérivé de `10-6ch-multiout` par `tools/relocate_6ch.py` ([note 13](../../notes/13-6ch-upgrade-usb.md)). |
| `30-model-tg.json` | TinyGregAudio | [TinyGregAudio/Model-TG](https://github.com/TinyGregAudio/Model-TG), version `v1.1.0` (commit `70b39dd`), construit par son propre `build.py --modded-cycles` pour ce flasher (son `docs/PAYLOAD.md`) depuis une copie de sa source avec une retouche de ce projet (`MC_PATCHES` de `tools/gen_model_tg.py` : en mode mute, chaque touche de piste mute tout de suite, au lieu d'attendre la sortie du mode), généré par `tools/gen_model_tg.py` ; l'identifiant, l'ordre, le nom, la description et la liste des incompatibilités sont aussi les nôtres. Licence MIT, texte dans [`LICENSE-Model-TG`](LICENSE-Model-TG). Empreinte du MAIN OS : `08d9f075…` ; sans la retouche, `a049d724…`, celle que son auteur annonce pour la v1.1.0 ([note 31 §10](../../notes/31-model-tg.md)). |
| `30-model-tg-st.json` | TinyGregAudio, deux retouches de ce projet | Même source et même build que `30-model-tg.json`, avec la même retouche des mutes et une ligne de plus changée (`REGION_END`, sa zone d'échantillons s'arrête 1 Mo plus bas, `ST_PATCHES` de `tools/gen_model_tg.py`), plus les adresses de ses symboles (dont l'état de ses slide trigs, pour nos tests). Base de la version combinée avec les moteurs du Syntakt (`31-syntakt-tg-….json`, ce projet), [note 31 §4](../../notes/31-model-tg.md). Licence MIT. |
| `20-sdvintage-snare.json` | ce projet | Compilé depuis `tools/machines/sdvintage/` par `tools/gen_sdvintage.py` ([note 14](../../notes/14-machine-sd-vintage.md)). |
| `40-arp.json` | ce projet | Arpégiateur à la place du retrig : compilé depuis `tools/machines/arp/` (`arp.c`, `arp_hooks.S`, `arp.ld`) par `tools/gen_arp.py`, dans quatre masques de sprites libérés (`0x4018a788`, `0x4016cba8`, et les masques 47×47 `0x40189930`, `0x4018a220`, `tools/sprites.py`). Réglages dans l'octet +512 de la piste du pattern, inutilisé par l'OS ([note 32](../../notes/32-arpegiateur.md)). |

SHA-256 des fichiers de drumkilla, identiques à ceux du dépôt d'origine :

```
21de02b88903b2012c88f31ef3b593afa0b37f48c22884986961cee0fb5b0f47  01-latching-mute.json
fe7fb5218336272af8bb88a274d37ff249ab98415b2e327d2a49ae116da7b038  02-trig-preview.json
fbfa29a8873e18831d860ae489440e89c308612437379589d5ed7fc670d5d234  03-browser-scroll.json
```

Seul ajout de notre côté : l'entrée `cave_refs_ok` de `device.json`, qui explique pourquoi l'écriture de `browser-scroll`
dans la table de glyphes de la police de chiffres est sans danger ([note 15 §2](../../notes/15-demandes-reddit.md#point-technique--une-exception-au-contrôle-des-caves)).
