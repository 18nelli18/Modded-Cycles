# 08 · Feuille de route, extensions, questions ouvertes

Point de départ (25/09/2026) : le « 6 pistes en USB » existe dans ms-multi-output, mais n'a **jamais tourné sur un vrai Model:Cycles**.
Le projet commence donc par **valider**, puis **améliorer**.

---

## Étape 0 : réunir le nécessaire

- [x] ~~Retrouver le dépôt de teardown~~ : **supprimé par l'auteur** (confirmé). Rien n'en dépend.
- [x] **Version d'OS** : la dernière = **1.13** (confirmé, [09 §1](09-analyse-firmware-1.13.md#1-version-provenance-empreintes)). Le patch s'applique tel quel.
- [x] **Interface MIDI DIN** : l'utilisateur en a une.
- [x] **OS 1.13 téléchargé** (accord donné), SHA-256 du `.syx` vérifié, **build reproductible ✅** ([09 §1](09-analyse-firmware-1.13.md#1-version-provenance-empreintes)). Fichiers dans `firmware/` (non versionné).
- [ ] Sauvegarder les projets et sons de l'utilisateur (Transfer) **avant tout flash**.

## Étape 1 (jalon 1) : 6 pistes USB sur un vrai Model:Cycles

- [ ] Build `--target cycles` avec un hash ✅ ([06 §1](06-flash-et-recuperation.md#1-construire-limage---target-cycles)).
- [ ] Flash par DIN, avec `--allow-any-device` ([06 §2](06-flash-et-recuperation.md#2-flasher)).
- [ ] Dérouler le plan de test ([06 §3](06-flash-et-recuperation.md#3-vérifier-premier-vrai-modelcycles)) et **consigner les résultats** dans `tests/`.
- [ ] Avec l'accord de l'utilisateur : ouvrir l'issue demandée par l'auteur de ms-multi-output.

## Étape 2 : environnement de rétro-ingénierie sur l'OS Cycles 1.13

- [ ] `elektron-firmware-tool -v` : inventaire des sections. Extraire la section 3 (SHA `cc99d4f0…`).
- [ ] Projet Ghidra (`68000:BE:32:Coldfire`, base `0x40000400`) ; étiqueter les points connus ([03 §7](03-plateforme-coldfire.md#7-points-de-repère-à-étiqueter-dans-ghidra-cycles-113)).
- [ ] Dumper la **table des modes USB complète** et la **config HS de 328 o** ([07 §4](07-snippets.md#4-dumper-la-table-des-modes-usb-et-les-descripteurs-à-tester)).
- [ ] Élucider les 3 constantes non expliquées : `0x4000253b` (15 → 3), `0x4000281f` (11 → 6), `0x40002564` (`0x9b80` → `0x9e00`, fin du ring ?).
- [ ] Trouver le **mixeur** (références à `0x80001858`, [07 §5](07-snippets.md#5-trouver-le-mixeur-pour-le-pan-les-fx-et-le-mode-8-canaux-à-tester)) : coefficients de pan, bus d'envoi FX, saturation du master.
- [ ] Identifier le **contexte d'exécution du feeder USB** (interruption ? niveau ?) et sa marge temporelle.
- [ ] Cartographier la **RAM libre** après le ring et les **caves de code** non référencées ([05 §1](05-methode-patch.md#1-technique-du-détour-et-de-la-code-cave)).
- [ ] Option : harnais Unicorn pour rejouer le chemin du feeder (méthode d'octamax).

## Étape 3 : extensions, de la plus simple à la plus lourde

### A. 8 canaux = 6 pistes + mix stéréo (recommandé comme jalon 2)

> ▶️ **Conception détaillée et avancée dans [11-conception-8-canaux.md](11-conception-8-canaux.md)** : stubs `tracks8` et `prime8` assemblés et vérifiés, éditions inline confirmées, dimensionnement des rings à finaliser sur matériel.

Pourquoi : cela corrige le plus gros défaut du mod actuel (**plus de mix ni de FX en USB**). Et la géométrie devient **presque entièrement « puissance de 2 »**.

| Constante | 6 canaux (ms-multi-output) | **8 canaux** (F = 32 o) | Modifiable sur place ? |
|---|---|---|---|
| `bNrChannels` IT et AS (+68, +209) | 6 | **8** | oui (1 o) |
| `wMaxPacketSize` (+225) | 168 | **224** (`0xE0`) | oui (1 o, < 256) |
| dQH `MaxPacketLength` (`0x40002ceb`) | `0xa8` | **`0xE0`** | oui, si l'octet porte les bits 16..23 `[HYP]` |
| Token de prime | `0x00900080` | **`0x00C00080`** (192 o) + longueur privée 192 | non : stub `prime8` (192 hors de portée de `moveq`) |
| Token de fin de case | ×24 (stub) | ×32 : `moveq #19`→`#21` (`7213`→`7215`) et `lsl.l #3,d0`→`#5` (`e788`→`eb88`) | **oui : plus besoin de stub** |
| Offset destination | ×24 (stub) | ×32 : `lsl.l #3,d0` → `lsl.l #5,d0` (`e788`→`eb88`) en `0x400029e4` | **oui : plus besoin de stub** |
| Stride (2 sites) | 192 | **224** = (x<<8) − (x<<5) : `lsl #3`→`#5` et `lsl #6`→`#8` (`e189`/`e18a`), `sub.l` conservé | **oui**, même forme que le stock |
| Profondeur et masque | 8 / 7 | 8 / 7 (capacité 48 trames) | déjà fait |
| Taille du ring | 1536 o | **1792 o** (`0x700`), soit +256 o | ⚠️ vérifier la RAM libre |
| Stub de copie | tracks6 | **tracks8** = tracks6 + 2 mots du mix par trame | stub |

Esquisse du cœur de `tracks8` (`[HYP]`, non testé) :
```asm
        movea.l %sp@(80),%a3            | source du mix (36(sp) d'origine + 44 du prologue)
        adda.l  %d5,%a3                 | + offset, comme la boucle d'origine
        ...                             | par trame : les 6 échantillons de piste (comme tracks6), puis :
        move.l  %a3@+,%d2 ; .short 0x02c2 ; move.l %d2,%a1@+     | L
        move.l  %a3@+,%d2 ; .short 0x02c2 ; move.l %d2,%a1@+     | R
```
Points à confirmer d'abord :
1. le mix est lu **linéairement**, sans masque, comme dans la boucle d'origine ;
2. `d0` (mots longs = trames × 2) correspond bien au même nombre de trames que les blocs de piste ;
3. le mix contient les FX et la saturation du master ;
4. les deux constantes inconnues ne dépendent pas de la géométrie.

### B. 12 ou 14 canaux (pistes stéréo avec pan, et mix en option)

- F = 48 ou 56 o : pas des puissances de 2, donc stubs pour token, dstoff et stride. `wMaxPacketSize` > 255 : écrire 2 octets LE.
  dQH MPL > 255 : modifier aussi les bits hauts ([04 §4-5](04-usb-audio.md#5-recette--changer-le-nombre-de-canaux-n-liste-de-toutes-les-constantes)).
- **Prérequis** : rétro-ingénierie du mixeur pour lire les coefficients de pan par piste. Ensuite, soit multiplier dans le stub (EMAC ou `muls.l`),
  soit détourner la boucle de sommation pour écrire L/R par piste dans un buffer annexe. Coût en code et en RAM nettement plus élevé.

### C. Retours d'effets (delay / reverb) sur des canaux dédiés

- Localiser les buffers de sortie des FX (bus d'envoi dérivés de la somme, d'après le README) et les ajouter comme paire stéréo.

### D. Mode sélectionnable dans SETTINGS (stéréo / 6 / 8 canaux…)

- Rétro-ingénierie de l'interface (références de chaînes, voir `string_func_map` d'octamax) et de la persistance des réglages (sauvegarde à l'extinction).
- Changer de config USB implique une ré-énumération (déconnexion logicielle). Gros chantier : bien plus tard.

### E. Récupérer l'upgrade USB et le Full Speed

- Déplacer les stubs dans une vraie cave de code ([05 §1](05-methode-patch.md#1-technique-du-détour-et-de-la-code-cave)) et ne rediriger que les entrées nécessaires de la table des modes.

### F. Portage vers d'autres versions d'OS

- Même méthode que l'auteur (Samples → Cycles) : traduction d'adresses, avec vérification `expect` sur chaque site.

## Questions ouvertes

Mises à jour après l'analyse de l'image 1.13 ([09](09-analyse-firmware-1.13.md)).

| # | Question | Statut / comment y répondre |
|---|---|---|
| Q1 | Où est le dépôt `elektron-models-teardown` ? | ✅ **résolu** : supprimé par l'auteur (confirmé par l'utilisateur). Rien n'en dépend. |
| Q2 | Rôle de `0x4000253b` (15 → 3), `0x4000281f` (11 → 6), `0x40002564` (+0x280) | Ghidra, section 3 (extraite). Le désassemblage confirme que `0x40002564` façonne la borne du ring (`0x80009b80`). |
| Q3 | La RAM après la fin du ring (`…9e00`) est-elle libre ? | références aux adresses voisines (`mcfw.code_refs`) sur la section extraite |
| Q4 | Le LEVEL / VOLUME+DIST est-il appliqué avant le point de prélèvement sur le Cycles ? | test matériel (sinus, THD) |
| Q5 | Le buffer de mix : linéaire ? post-saturation ? avec FX ? | ▶️ **en cours** : mixeur localisé (`0x40056930`), reste à qualifier la source du feeder ([09 §6](09-analyse-firmware-1.13.md#6-le-mixeur--où-sont-le-volume-le-pan-et-les-envois-fx-vérifié)) |
| Q6 | Contexte d'exécution du feeder (ISR, IPL) et marge CPU | Ghidra (vecteurs, `move #…,sr`) |
| Q8 | Comportement sur un hôte ou un hub Full Speed après patch | test matériel |
| Q9 | Le M:C a-t-il un mode USB « MIDI seul » que le patch casserait ? | ✅ **résolu** : oui, `USB MODE = MID` (manuel §12.7.1). Le patch redirige aussi ce mode vers la config 6 canaux ([09 §4](09-analyse-firmware-1.13.md#4-réglages-usb-de-la-machine-manuel--image)). À tester. |
| Q10 | Quel `-mcpu` de GAS accepte `byterev` ? | `m68k-elf-as --help` |
| Q11 | Un OS Cycles plus récent que 1.13 existe-t-il ? | ✅ **résolu** : non, 1.13 est la dernière ([09 §1](09-analyse-firmware-1.13.md#1-version-provenance-empreintes)) |
| Q12 | Le bootloader accepte-t-il un texte de version modifié (`-V`) ? | test prudent, DIN prêt |
| Q13 | Cause du blocage (« wedge ») sous Windows | repro + capture USB |
| **Q14** | Le patch survit-il à un **changement de mode USB à chaud** (A+M ↔ MID) ? La fonction de « fixup » des descripteurs réécrit les blobs à l'init USB ([09 §5](09-analyse-firmware-1.13.md#5--découverte-importante--les-descripteurs-sont-réécrits-à-lexécution)). | test matériel |

## Risques

- **Brick « mou »** : récupérable par le menu de démarrage en DIN, si et seulement si une interface DIN est disponible.
  Brick dur peu probable : le bootloader n'est jamais écrit par les mises à jour d'OS.
- Garantie ; support Elektron impossible ; usage personnel uniquement.
- **Ne jamais publier d'image firmware** (originale ou modifiée) : seulement des tables d'octets et des sources.
- Rendu : les stems n'ont ni le pan, ni les FX, ni la saturation du bus de mix. Le mode 8 canaux (A) atténue ce problème.
