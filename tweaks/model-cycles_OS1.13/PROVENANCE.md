# Provenance des tweaks

| Fichier | Auteur | Origine |
|---|---|---|
| `01-latching-mute.json`, `02-trig-preview.json`, `03-browser-scroll.json` | drumkilla | [drumkilla/elektron-model-tweaks](https://github.com/drumkilla/elektron-model-tweaks), commit `6e0b4df`, `tweaks/model-cycles_OS1.13/`. Repris **sans modification** (licence MIT, texte dans [`tools/mtlib/LICENSE`](../../tools/mtlib/LICENSE)). |
| `10-6ch-multiout.json` | d'après scottmetoyer | Table de patchs de [scottmetoyer/ms-multi-output](https://github.com/scottmetoyer/ms-multi-output) (MIT), cible Cycles, mise au format tweak ([note 01](../../notes/01-ms-multi-output.md)). |
| `11-6ch-usbup.json` | ce projet | Dérivé de `10-6ch-multiout` par `tools/relocate_6ch.py` ([note 13](../../notes/13-6ch-upgrade-usb.md)). |
| `30-model-tg.json` | TinyGregAudio | [TinyGregAudio/Model-TG](https://github.com/TinyGregAudio/Model-TG), commit `454963b`, tel que son propre `build.py --modded-cycles` l'exporte pour ce flasher (son `docs/PAYLOAD.md`), généré par `tools/gen_model_tg.py` ; seuls l'identifiant, l'ordre, le nom, la description et la liste des incompatibilités sont les nôtres. Licence MIT, texte dans [`LICENSE-Model-TG`](LICENSE-Model-TG). Empreinte du MAIN OS : `fb985a16…`, celle que son build annonce ([note 31](../../notes/31-model-tg.md)). |
| `30-model-tg-st.json` | TinyGregAudio, une retouche de ce projet | Même source et même build que `30-model-tg.json`, depuis une copie de sa source avec une seule ligne changée (`REGION_END`, sa zone d'échantillons s'arrête 1 Mo plus bas, `ST_PATCHES` de `tools/gen_model_tg.py`), plus les adresses de ses symboles. Base de la version combinée avec les moteurs du Syntakt (`31-syntakt-tg-….json`, ce projet), [note 31 §4](../../notes/31-model-tg.md). Licence MIT. |
| `20-sdvintage-snare.json` | ce projet | Compilé depuis `tools/machines/sdvintage/` par `tools/gen_sdvintage.py` ([note 14](../../notes/14-machine-sd-vintage.md)). |

SHA-256 des fichiers de drumkilla, identiques à ceux du dépôt d'origine :

```
21de02b88903b2012c88f31ef3b593afa0b37f48c22884986961cee0fb5b0f47  01-latching-mute.json
fe7fb5218336272af8bb88a274d37ff249ab98415b2e327d2a49ae116da7b038  02-trig-preview.json
fbfa29a8873e18831d860ae489440e89c308612437379589d5ed7fc670d5d234  03-browser-scroll.json
```

Seul ajout de notre côté : l'entrée `cave_refs_ok` de `device.json`, qui explique pourquoi l'écriture de `browser-scroll`
dans la table de glyphes de la police de chiffres est sans danger ([note 15 §2](../../notes/15-demandes-reddit.md#point-technique--une-exception-au-contrôle-des-caves)).
