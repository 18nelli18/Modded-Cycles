# Modded-Cycles

Notes techniques pour un projet de **mod firmware de l'Elektron Model:Cycles** : faire sortir en USB les **6 pistes séparément**
au lieu du seul mix stéréo, puis explorer des extensions (mix + pistes, panoramique, effets).

> ⚠️ **Aucune image firmware Elektron n'est incluse dans ce dépôt** — ni originale, ni modifiée.
> On travaille sur sa **propre** copie de l'OS officiel, téléchargée légalement depuis elektron.se.
> Ce dépôt ne contient que de l'analyse, des tables de diff (octets), des sources assembleur et des outils.
> Projet non affilié à Elektron, sans lien ni soutien de leur part. Flasher un OS modifié se fait **à ses risques** et peut annuler la garantie.

## Construire et flasher

Chaîne d'outils **Python pur**, sans dépendance ni image firmware : voir [`BUILD.md`](BUILD.md).
```sh
python3 tools/build.py --list
python3 tools/build.py -i model-cycles_OS1.13.syx -t 6ch-multiout   # référence (testée en cross-flash)
python3 tools/build.py -i model-cycles_OS1.13.syx -t 6ch-usbup      # garde l'upgrade USB (jamais flashée)
python3 tools/build.py -i model-cycles_OS1.13.syx -t sdvintage-snare  # machine SD VINTAGE à la place de SNARE (jamais flashée)
```
**Flasher** : scripts clés en main (installent les dépendances, vérifient, guident, flashent) — voir [`FLASH.md`](FLASH.md).
```sh
./flash.sh            # macOS / Linux
flash.bat             # Windows (double-clic)
```
**Ou depuis Chrome, sans rien installer** : le [flasher Web MIDI](docs/flasher/) (`docs/flasher/`) sait **construire**
l'image modifiée à partir de ton OS officiel **et** l'envoyer par Web MIDI, entièrement dans le navigateur
(rien n'est envoyé à un serveur, aucune image firmware n'est fournie). C'est le port JS de `build.py`/`mtlib`,
vérifié à l'octet près contre le Python (`tools/webflash_check.sh`, `tools/webbuild_check.sh`).
Une fois GitHub Pages activé, il sera en ligne sur `https://18nelli18.github.io/Modded-Cycles/flasher/`.
⚠️ Le flash passe par le **MIDI IN** de l'appareil (sa prise jack TRS 3,5 mm : câble jack stéréo depuis une interface à sortie TRS, ou adaptateur DIN fourni).
Le menu de démarrage ignore l'USB, et `6ch-multiout` casse l'upgrade USB ; la variante `6ch-usbup` devrait le garder (à tester, [note 13](notes/13-6ch-upgrade-usb.md)).
Lis [`FLASH.md`](FLASH.md) avant.

## Contenu

| Document | Sujet |
|---|---|
| [`BUILD.md`](BUILD.md) | Comment construire une image modifiée (Python pur) |
| [`FLASH.md`](FLASH.md) | **Comment flasher son Model:Cycles** (guide détaillé + scripts) |
| [`dossier-technique.md`](dossier-technique.md) | Synthèse du fil Elektronauts « Model:Cycles Q&A with Ess », chaque info sourcée |
| [`notes/README.md`](notes/README.md) | **Index des notes techniques** et chiffres clés |
| [`notes/10-faisabilite-fonctionnalites.md`](notes/10-faisabilite-fonctionnalites.md) | **Faisabilité, fonction par fonction** (à lire pour l'état des lieux) |
| [`tools/`](tools/) · [`tweaks/`](tweaks/) | Build (mtlib) et tables de patchs (format JSON) |

## Fonctionnalités visées (par priorité, cf. [note 10](notes/10-faisabilite-fonctionnalites.md))

| Fonction | État |
|---|---|
| Sortie multipiste **6 canaux** | ✅ code prêt, buildable ici — **attend un test matériel** |
| Garder l'**upgrade USB** avec le mod 6 canaux | 🟡 variante `6ch-usbup` prête et vérifiée en émulation — **attend un test matériel** ([note 13](notes/13-6ch-upgrade-usb.md)) |
| Moteur de percussion en plus : **SD VINTAGE** (caisse claire vintage, d'après le Syntakt) | 🟡 étape 1 (à la place de SNARE) prête et validée dans le moteur émulé — **attend un test matériel** ; 7ᵉ machine : plan prêt ([note 14](notes/14-machine-sd-vintage.md)) |
| Sortie multipiste **12 canaux** (pan par piste) | 🟡 faisable, à développer (via un jalon **8 canaux**) |
| Modifier les **algos d'effet** | 🔴 non (réglages de paramètres : 🟡) |
| **Moteur Sample** (façon Model:Samples) | 🔴 hors de portée comme mod du M:C |
| **2 LFO** synchronisables et assignables | 🟠 lourd (élargir les destinations du LFO actuel : 🟡) |
| **Polyrythmie** (time signature par piste) | 🟡 en partie déjà présente en stock |
| **Contrôle MIDI USB** (clock, start/stop) | ✅ déjà supporté en stock (réglage) |
| **Arpégiateur** (mode chromatique) | 🟠 long terme |
| **Scale** (mode chromatique) | 🟡 faisable, effort moyen |
| **Polyphonie** du synthé | 🔴 très difficile |

## Où en est le projet

- Le mod « 6 pistes en USB » **existe** ([scottmetoyer/ms-multi-output](https://github.com/scottmetoyer/ms-multi-output), MIT),
  porté ici au format tweak ; notre build **reproduit le MAIN OS connu-bon à l'octet près**. Mais il n'a **jamais été flashé sur un vrai Model:Cycles**.
- L'OS officiel **1.13** (dernière version) a été analysé en profondeur ([note 09](notes/09-analyse-firmware-1.13.md)).
- Le moteur de synthèse (6 machines = 6 *mappings* d'un même moteur FM) est décodé et **émulé** (`tools/emu/`). Un moteur de plus,
  **SD VINTAGE**, est écrit en C, compilé pour le ColdFire et validé dans le vrai moteur émulé ([note 14](notes/14-machine-sd-vintage.md)).
- **Jalon 1** : valider le 6 canaux sur un vrai Model:Cycles. Rien n'a encore été flashé.

Détails et étapes : [`notes/08-feuille-de-route.md`](notes/08-feuille-de-route.md).

## Crédits (dépôts amont, tous MIT, sans firmware inclus)

- [`scottmetoyer/ms-multi-output`](https://github.com/scottmetoyer/ms-multi-output) — le mod 6 canaux (Model:Samples et Model:Cycles)
- [`drumkilla/elektron-model-tweaks`](https://github.com/drumkilla/elektron-model-tweaks) — `mtlib` (transport SysEx, aPLib, conteneur ELE3/HMAC en Python) et le format de tweak JSON, vendus dans `tools/mtlib/`
- [`mischa85/elektron-firmware-tool`](https://github.com/mischa85/elektron-firmware-tool) — dépaquetage / repaquetage / re-signature des `.syx` (chaîne C alternative)
- [`mxldyn/octamax`](https://github.com/mxldyn/octamax) — rétro-ingénierie de l'OS Octatrack (méthode, outils, pièges)
