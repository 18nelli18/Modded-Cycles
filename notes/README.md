# Notes de développement : mod USB multipiste Model:Cycles

Notes de travail tirées de l'analyse de dépôts GitHub (analysés le 25/09/2026). Elles complètent
[`../dossier-technique.md`](../dossier-technique.md), tiré du fil Elektronauts.

> **Conventions**
> - **`[FAIT]`** : lu dans le code ou la doc d'un dépôt, ou décodé à l'octet près.
> - **`[HYP]`** : hypothèse ou interprétation de ma part, à confirmer sur l'image firmware.
> - **`[À FAIRE]`** : action à mener.
> - Toutes les adresses sont des adresses virtuelles ColdFire (VA) de l'OS **1.13**, sauf mention contraire.

---

## ⚡ Ce qu'il faut retenir en premier

1. **Le mod existe déjà en grande partie.** Le dépôt `scottmetoyer/ms-multi-output` fournit une cible
   `--target cycles` qui envoie **les 6 pistes du Model:Cycles sur 6 canaux USB** (48 kHz, 32 bits, High Speed).
   Le mixage stéréo n'est alors plus envoyé en USB.
   - Le **code patché est vérifié sur du matériel**, mais sur un Model:Samples qui fait tourner l'OS Cycles (« cross-flash »).
   - **Aucun vrai Model:Cycles n'a jamais été flashé** avec ce build. C'est la première chose à faire dans ce projet ([`06`](06-flash-et-recuperation.md)).
2. **La chaîne d'outils est connue et scriptable.** On extrait la section 3 (MAIN OS) avec `elektron-firmware-tool`,
   on applique une table de patchs octet par octet, puis on reconditionne et re-signe (HMAC recalculé).
   Aucune signature cryptographique n'empêche le flash.
3. **Filet de sécurité.** Le bootloader se trouve dans un secteur que les mises à jour d'OS n'écrivent jamais.
   On revient toujours à l'OS officiel par l'**entrée MIDI IN** de l'appareil, une prise jack TRS 3,5 mm (le menu de démarrage ignore l'USB).
   **Une interface MIDI reliée à ce MIDI IN est obligatoire avant tout flash** : sortie TRS + simple câble jack stéréo,
   ou sortie DIN + adaptateur fourni ([12](12-flash-par-jack-trs.md)).
4. **Limites du mod actuel** :
   - pistes mono (pan non appliqué) ;
   - delay et reverb absents ;
   - plus de mix stéréo en USB ;
   - `CONFIG → UPGRADE` par USB cassé tant que le mod est installé ;
   - hôte USB High Speed obligatoire ;
   - le LEVEL de piste est-il appliqué avant le point de prélèvement ? Inconnu sur le Cycles.

## Sources analysées

| Dépôt | Statut | Commit analysé | Rôle |
|---|---|---|---|
| [scottmetoyer/ms-multi-output](https://github.com/scottmetoyer/ms-multi-output) | ✅ lu en entier | `3edf617` (19/09/2026) | Le mod 6 canaux (M:S et **M:C**) |
| [mischa85/elektron-firmware-tool](https://github.com/mischa85/elektron-firmware-tool) | ✅ lu en entier | `a5bce9a` (08/09/2026) | Dépaquetage / repaquetage / re-signature des `.syx` |
| `bryantysinger/elektron-models-teardown` | ❌ **supprimé** par l'auteur (confirmé par l'utilisateur) | n/a | Analyse du firmware des Models ; perdu, rien n'en dépend |
| **Image officielle OS 1.13** | ✅ **téléchargée et analysée** le 25/09/2026 | 1.13 (dernière) | Voir [09](09-analyse-firmware-1.13.md). Fichiers dans `firmware/` (non versionné) |
| [bryantysinger/octa-bt-pt](https://github.com/bryantysinger/octa-bt-pt) | ➕ bonus (seul dépôt public du même auteur) | `e970dd0` | Patch de valeurs du firmware Octatrack : méthode registre, vérification, hashs |
| [mxldyn/octamax](https://github.com/mxldyn/octamax) | ➕ bonus (crédité par ms-multi-output) | `7d9debc` | Rétro-ingénierie complète de l'OS Octatrack : technique code cave + détour, Ghidra, émulateur, pièges |
| [drumkilla/elektron-model-tweaks](https://github.com/drumkilla/elektron-model-tweaks) | ✅ lu et **adopté** (mtlib versé dans `tools/`) | `6e0b4df` (19/09/2026) | Outillage Python pur (SysEx/aPLib/ELE3/HMAC), format de tweak JSON, 3 tweaks QoL pour le M:C 1.13 |

## Plan des notes

| Fichier | Contenu |
|---|---|
| [01-ms-multi-output.md](01-ms-multi-output.md) | Fonctionnement du mod 6 canaux, **table de patchs Cycles décodée**, stubs, historique et leçons |
| [02-format-os-syx.md](02-format-os-syx.md) | Format `.syx` → conteneur ELE3 → sections aPLib → MAIN OS ; checksums, HMAC, CLI de l'outil |
| [03-plateforme-coldfire.md](03-plateforme-coldfire.md) | CPU MCF5441x, carte mémoire connue, pièges de l'ISA ColdFire, outils de rétro-ingénierie |
| [04-usb-audio.md](04-usb-audio.md) | Pilote USB (dQH/dTD), descripteurs UAC2, table de modes USB, ring, bande passante, compatibilité OS |
| [05-methode-patch.md](05-methode-patch.md) | Technique code cave + détour, règles de sûreté, build reproductible, leçons des crashs |
| [06-flash-et-recuperation.md](06-flash-et-recuperation.md) | Procédures de build, de flash et de récupération ; pièges de `flash.py` avec le Cycles |
| [07-snippets.md](07-snippets.md) | Code prêt à l'emploi : stubs ASM relogés Cycles, helpers Python, commandes shell |
| [08-feuille-de-route.md](08-feuille-de-route.md) | Étapes du projet, extensions (8 / 12 / 14 canaux, FX), questions ouvertes, risques |
| [09-analyse-firmware-1.13.md](09-analyse-firmware-1.13.md) | **Vérifié sur l'image officielle** : structure ELE3, menu de démarrage, réglages USB, réécriture des descripteurs, mixeur |
| [10-faisabilite-fonctionnalites.md](10-faisabilite-fonctionnalites.md) | **Faisabilité des 10 fonctionnalités souhaitées**, par priorité, avec effort et inconnues matérielles |
| [11-conception-8-canaux.md](11-conception-8-canaux.md) | **Conception du mode 8 canaux** (6 pistes + mix) : stubs `tracks8`/`prime8` vérifiés, éditions, rings à finaliser |
| [12-flash-par-jack-trs.md](12-flash-par-jack-trs.md) | **Flasher avec un simple câble jack stéréo** : entrée MIDI TRS (types A et B), interfaces à sortie TRS, piste « sortie casque » simulée |

## Chiffres clés (OS 1.13)

| Élément | Model:Cycles | Model:Samples |
|---|---|---|
| Device id SysEx | `0x11` | `0x0F` |
| SHA-256 du `.syx` officiel | `44fe5862…9800640c` | `e11859b6…398a2ce8` |
| SHA-256 section 3 d'origine | `cc99d4f0…ee98` | `a351392c…1ab2` |
| SHA-256 section 3 patchée | `65e24b50…9555` | `321b2ea6…1a69` |
| SHA-256 du `.syx` construit | `9c631bc2…22f6` (`mc-multi-output.syx`) | `9ab32674…0169` |
| Nombre de runs de patch | 29 | 41 (diff minimal, même sémantique) |
| Blocs audio par piste (`TRACK_BASE`) | `0x80001858` | `0x80001b48` |
| Variable « base de la case courante du ring » (`SLOT_BASE`) | `0x404a05e8` | `0x404af45c` |
| Stubs (prime / token / tracks / dstoff) | `0x4019b136` / `0x4019b182` / `0x4019b1e0` / `0x4019b244` | `0x401a0144` / `0x401a0190` / `0x401a01ec` / `0x401a0250` |
| Hooks dans le pilote USB | identiques : `0x400027e8`, `0x40002a42`, `0x40002a06`, `0x400029e4` | idem |
| Conversion offset ↔ VA (section 3) | `VA = offset + 0x40000400` | idem |
