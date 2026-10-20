# 58 · Le système de fichiers des Model par USB : commandes, statuts et le piège des 1 024 octets

En cherchant à sauvegarder le +Drive d'un Model:Cycles depuis un ordinateur et à y déposer des tables d'ondes, on a
buté pendant trois jours sur des échecs qui semblaient venir de la machine : listes de dossiers qui ne répondaient
jamais au-delà d'une soixantaine d'entrées, lecture de fichiers qui expirait au premier bloc, requête sur `/projects`
silencieuse. Aucun de ces problèmes ne venait du Model:Cycles **ni du protocole** : tous venaient du buffer de réception
de la bibliothèque MIDI de l'hôte, fixé à 1 024 octets. Cette note rassemble ce qui a été établi sur la famille de
commandes « raw », et le piège côté hôte, pour que la prochaine fois se règle en une minute.

Adresses : VA de l'OS 1.13. Rien ici ne dépend d'un mod : tout a été mesuré sur un Model:Cycles en OS 1.13 d'origine
côté protocole (le firmware en place avait des mods, mais la famille « raw » est celle de l'OS, notes/41).

## 1. En bref

| | État |
|---|---|
| La trame : en-tête de 5 octets, puis décodage 7 bits | `[FAIT]` mesuré, §2 |
| Le type de la réponse est celui de la requête avec le bit 7 (`0x14` → `0x94`) | `[FAIT]` §2 |
| Les commandes de la famille « raw » (lister, écrire, lire, supprimer…) | `[FAIT]` §3 |
| Statut : `1` = réussi, **sauf** `CLOSE_READER` où c'est `0` ; `READ_DIR` et `READ` n'ont pas de statut | `[FAIT]` §4 |
| Le « hash » du catalogue est un hash de **contenu**, calculé à la fermeture | `[FAIT]` mesuré, §5 |
| Les fichiers sont enregistrés **sans extension** | `[FAIT]` §6 |
| Le piège côté hôte : RtMidi reçoit au plus ~1 024 octets | `[FAIT]` mesuré, §7 |
| Explication des « limites » observées (≈ 64 entrées, blocs de 8 Ko) | `[FAIT]` §7 |
| Sauvegarde complète du +Drive depuis un PC | `[FAIT en dehors du dépôt]` §8 |

## 2. La trame

Même cadre que le protocole de Transfer (notes/37), avec une règle qui a coûté cher :

```
F0 00 20 3C 10 00 | <7 bits encodé> | F7
                     └─ seq(2) 0 0 type(1) corps…
```

- le **type** est le premier octet du corps de la requête ; la réponse porte le même avec le bit 7 ;
- la séquence (2 octets) revient telle quelle et sert à apparier ;
- **il faut retirer l'en-tête de 5 octets AVANT le décodage 7 bits**. Décoder la trame entière donne des types
  fantaisistes (`0x00`, `0x24`, `0x2c`…) et fait rejeter des réponses parfaitement valides. C'est l'erreur qui a
  fait croire à un proxy défaillant.

## 3. Les commandes de la famille « raw »

L'OS du Model:Cycles ne répond qu'à la famille « raw » ; la famille « sample » d'un Model:Samples est relabellisée par
Model-TG (notes/41). Constantes d'Elektroid (`src/connectors/elektron.c`), vérifiées sur la machine.

| Commande | Réponse | Corps de la requête | Réponse |
|---|---|---|---|
| `0x14` | `0x94` | chemin + `0` | entrées à partir de l'octet 5 : hash u32, taille u32, protection, type (`0x44` = dossier), nom, `0` |
| `0x15` | `0x95` | chemin | statut |
| `0x16` | `0x96` | chemin | statut (dossier vide seulement) |
| `0x24` | `0xA4` | chemin | statut |
| `0x26` | `0xA6` | chemin | — (non exploré) |
| `0x33` | `0xB3` | chemin | statut `1`, `id` en `[6..9]`, `taille` en `[10..13]` |
| `0x35` | `0xB5` | `id`, `taille`, `début` (u32 chacun) | données **à partir de l'octet 22** |
| `0x34` | `0xB4` | `id` | statut `0` |
| `0x43` | `0xC3` | `taille`, chemin | statut `1`, `id` en `[6..9]` |
| `0x45` | `0xC5` | `id`, longueur, décalage, octets (blocs de `0x2000`) | statut |
| `0x44` | `0xC4` | `id`, taille totale | statut ; la machine **hache le fichier ici**, donc prévoir large |
| `0x53` | `0xD3` | chemin + 9 octets | espace des presets (`/` → une entrée « projects »), pas les dossiers d'échantillons |

## 4. Statuts

- `1` = réussi pour `OPEN_WRITE`, `WRITE`, `CLOSE_WRITE`, `OPEN_READER`, `CREATE_DIR`, `DELETE_*` ;
- `0` = réussi pour **`CLOSE_READER`** (seule exception trouvée) ;
- `READ_DIR` et `READ` **n'ont pas d'octet de statut** : leur corps commence directement par les données. Lire le
  statut sur `READ_DIR` revient à lire le premier octet du premier hash, qui vaut `0` pour un dossier — d'où des
  succès apparents uniquement sur les dossiers.

## 5. Le hash du catalogue est un hash de contenu

`docs/notes/sample_format.md` de Model-TG laisse la question ouverte (« soit un hash maison, soit un localisateur de
stockage »). Mesure : deux fichiers **identiques au bit près**, déposés sous deux noms différents, reviennent avec
**le même** hash dans `READ_DIR` (`60e72095` pour les deux). Le hash ne dépend donc que du contenu, et il est calculé
par l'OS à la fermeture du fichier après écriture (`0x4007c022 → 0x4007e2f6`). Ce n'est ni un CRC32 ni un Adler32 ;
cela n'a pas d'importance : `READ_DIR` le rend prêt.

Conséquence pratique : un fichier réécrit à l'identique garde son hash, ce qui explique la déduplication du loader.

## 6. Noms sans extension

Les fichiers sont enregistrés **sans extension** (`wt_sin`, `SY Anton`), et la famille « raw » les relit ainsi. Un
`READ_DIR` sur un dossier dont on connaît les noms n'est pas nécessaire pour vérifier un envoi : `OPEN_READER` rend
la taille du fichier demandé, ce qui suffit.

## 7. Le piège côté hôte : 1 024 octets

`RtMidi.h` :

```cpp
unsigned int bufferSize;
RtMidiInData() : … bufferSize(1024), bufferCount(4) {}
virtual void setBufferSize( unsigned int size, unsigned int count );
```

L'entrée MIDI de RtMidi — donc de `mido`/python-rtmidi, qui sert à tous nos outils — **reçoit au plus 1 024 octets
par message SysEx**. Au-delà, la réponse n'arrive pas du tout : pas d'erreur, pas de troncature visible, seulement un
délai qui expire. Mesure sur un `READ` de fichier, en faisant varier la taille du bloc demandé :

| Bloc demandé | Résultat |
|---|---|
| 256, 512, 700 octets | reçus intégralement |
| 900, 1 000, 1 024, 1 100, 1 500, 2 048, 4 096 | **expiration** |

C'est ce qui a produit les trois faux diagnostics :

- un dossier de 74 entrées (~1,5 Ko de réponse) « ne répond pas » → il passe dès que la réception suit ;
- un `READ` de bloc de 8 Ko (0x2000, la taille d'Elektroid) « ne répond pas » → même cause ;
- `0x53 /projects`, dont la réponse est plus grosse que celles de `/`, « ne répond pas » → même cause.

python-rtmidi 5.0.0 **n'expose pas** `setBufferSize` (`dir(MidiIn)` ne contient que `__sizeof__`). La correction côté
hôte : recevoir par `winmm` directement (`midiInOpen` + `midiInPrepareHeader` + `midiInAddBuffer` avec des tampons de
64 Ko). En Python, `ctypes` suffit, sans rien compiler ; l'émission peut rester chez `mido`.

Sur les plateformes qui n'ont pas cette limite (ALSA, CoreMIDI), le problème n'existe pas : c'est pour cela
qu'Elektroid, qui parle ALSA, ne l'a jamais rencontré.

## 8. Ce que cela permet

- **Sauvegarde complète du +Drive** depuis un PC : parcours récursif par `READ_DIR`, `OPEN_READER`/`READ`/`CLOSE_READER`
  pour chaque fichier, `manifest.json` avec taille et hash. Mesuré : 798 fichiers, 30 dossiers, ~14 Mo, reprise
  incrémentale en 7 s (les fichiers dont taille et hash correspondent sont sautés).
- **Dépôt de fichiers** : `OPEN_WRITE`/`WRITE`/`CLOSE_WRITE`, avec vérification par `OPEN_READER` (taille) puisqu'un
  dossier de plus de 64 entrées n'a pas besoin d'être listé pour être vérifié.
- **Dépannage** : quand une réponse « manque », regarder d'abord sa taille avant d'accuser la machine.

## 9. Ce qui reste à vérifier

- `0x26` (informations par chemin) et la variante par hash et taille (`0x23`, famille « sample ») : non explorées.
- La suppression d'un dossier non vide : `DELETE_DIR` refuse, mais rien ne dit comment vider proprement un dossier en
  une commande.
- `0x53` : la structure exacte de la réponse (`01 00 00 00 | 00 00 00 00 | 01 00 00 00 | 01 | "projects" | 00 | 01 | …`)
  n'est pas décodée ; seule la commande qui porte `/` a été observée.
- L'outil de sauvegarde vit hors du dépôt : il n'utilise que les commandes ci-dessus, donc rien à intégrer ici, mais
  la vérification sur la machine de chacun reste à faire.
