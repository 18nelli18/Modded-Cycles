# 18 · SD VINTAGE en 7ᵉ machine « SDVtg », à côté de SNARE

Travail du 30/09/2026, à la demande de l'utilisateur : ajouter SD VINTAGE **dans la liste des machines**, sans remplacer SNARE (SD Basic), avec les bons affichages de potards.
Point de départ : le plan de [14 §8](14-machine-sd-vintage.md) et le moteur exact de [17](17-portage-exact-syntakt.md), testé sur la machine.

Toutes les adresses sont celles du MAIN OS 1.13 officiel. Source : désassemblage de l'image stock (`m68k-elf-objdump`, ColdFire V4e), sauf mention du manuel.

## 0. En bref

| | État |
|---|---|
| Inventaire de tout ce qui dépend du nombre de machines | `[FAIT]` §1–§6 |
| Tweak `sdvintage-7th` : 7ᵉ machine « SDVtg », SNARE d'origine intacte | `[FAIT]` `tools/gen_sdvintage_7th.py`, `tools/machines/syntakt_bridge/machine7.S` (§7) |
| Potards propres : noms et défauts du Syntakt | `[FAIT]` 5 descripteurs de plus (§6) |
| **Preuve en émulation** : 20 vérifications sur le vrai code de l'OS | `[FAIT]` `tools/emu/test_sdvintage_7th.py` (§8) |
| Flasher web : 2ᵉ variante de la case SD VINTAGE | `[FAIT]` (§7) |
| Test sur la machine | 1ᵉʳ essai 30/09 : 7ᵉ repère visible, mais **molette bloquée à Chord** → borne oubliée, corrigée (§10) ; 2ᵉ essai `[À FAIRE]` |

**Choix de l'utilisateur** (30/09/2026, en regardant son Cycles) :
- l'écran affiche le **nom long** du paramètre quand on tourne un potard (« Snare Color ») ;
- changer de machine **applique les valeurs par défaut** de la nouvelle machine ;
- d'où l'**option B** : des descripteurs propres à SDVtg, avec les noms et les défauts du Syntakt ;
- nom dans la liste : **SDVtg** (5 lettres comme « Snare » et « Chord », sûr de tenir à l'écran).

L'OS borne partout l'index de machine à 0..5 **sans lire hors de ses tables** : une machine 6 non gérée donne « Error », l'icône CHORD ou aucun paramètre, jamais une lecture au hasard.

## 1. Comment l'OS gère les machines

- **Manuel** (Model:Cycles User Manual, OS 1.13, §10.2 et §9.12.3) :
  - la touche [MACHINES] ouvre la liste, parcourue avec LEVEL/DATA ;
  - la machine peut être **verrouillée par pas** (« machine locks ») ;
  - COLOR, SHAPE, SWEEP et CONTOUR changent de rôle selon la machine ;
  - CC 70 = « Machine Selection » (annexe A).
- **Paramètre « Algorithm »** (descripteur n° 41, `0x4010e5d8`, nom court ALG, slot 9) : l'écran MACHINES lit la machine avec ce descripteur (`vtable[28](piste, 0x29)` en `0x400a25d8`), et l'édition passe par le setter générique `0x4000a980`, qui borne à [min, max] du descripteur. **Le max (5) décide donc de ce qu'on peut choisir partout** : menu, machine locks, CC.
- **Descripteurs** (`0x4010dce0`, 76 entrées de `0x38` o, [14 §2.1](14-machine-sd-vintage.md)) : pour chaque machine 0..5, quatre entrées COLOR/SHAPE/SWEEP/CONTOUR (champ machine = 0..5) suivies d'un « Amp Decay » avec le défaut propre à la machine.
  - Les noms courts sont les mêmes pour toutes les machines (COLR, SHPE, SWEP, CONT, DEC) ; les noms longs changent (« Snare Color »…), et **c'est le nom long que l'écran affiche** quand on tourne un potard (observé par l'utilisateur).
  - Les entrées des 6 machines partagent les mêmes slots (`0x0b..0x0e`, `0x12`) : un son stocke ses valeurs **par slot**, commun à toutes les machines. Ajouter une machine ne devrait donc pas changer le format des projets.

## 2. Moteur audio

Boucle des voix `0x400a7d4a` ([14 §2.3](14-machine-sd-vintage.md)) :
- bornes `moveq #5` en `0x400a7dba` (index au déclenchement) et `0x400a7df4` (garde du dispatch) → 6. `0x400a7dc0` (valeur de repli d'un index invalide) reste 5 ;
- table d'octets `0x40118640` (`00 01 02 03 04 05 00 00`) : l'octet `0x40118646` passe à `06` ;
- tables `render` `0x40118610` et `update` `0x40118628`, 6 entrées chacune et **contiguës** : les recopier à 7 entrées ailleurs, et réécrire leurs deux références (`0x400a7e16`, `0x400a7d6c`).
- Entrée 6 = la passerelle du moteur exact ([17 §4](17-portage-exact-syntakt.md)). **SNARE redevient la SNARE d'origine**, défauts d'origine compris.
- Machine locks : quand un pas change de machine, la boucle remet la voix à zéro (`0x400a7ab8`), ce qui efface la marque de la passerelle ; elle réinitialise alors la voix Syntakt au déclenchement suivant. Rien de plus à faire.

## 3. Rendre la machine 6 sélectionnable

Un seul octet : le max du descripteur « Algorithm », champ `0x4010e5e4`, `0x0500` → `0x0600` (valeurs 8.8).
Le CC 70 passe a priori par le même descripteur (drapeaux 0, contre `0x600` pour les potards : probablement une valeur entière). La valeur 6 devrait donc choisir SD VINTAGE : à vérifier.

## 4. Écran MACHINES et icônes

**Écran MACHINES** (`DrumSelect`, dessin à partir de `0x400a25e0`) :
- borne `moveq #5` en `0x400a25e0` : au-delà, il écrit « Error » et ne dessine pas d'icône ;
- nom : table de 6 pointeurs `0x401177e4` (Kick, Snare, Metal, Perc, Tone, Chord), suivie d'autres données. Seul `0x400a2614` la lit → recopier une table de 7 noms ailleurs ;
- deux images : `*(0x40fe32cc) + 28·m` et `*(0x40fe384c) + 28·m`, sans borne. Ce sont des tableaux de 6 descripteurs de sprites chargés au démarrage (`moveq #6` en `0x400b1424`, `0x400aef22`, `0x400af510`). Pour m = 6, il faut **pointer sur l'icône SNARE** (m = 1), faute de 7ᵉ image.

**Autres icônes de machine**, déjà bornées à 5 (une machine 6 montrerait l'icône CHORD) : `0x4001b6a6`, `0x400a40bc`, `0x400a4de6`, `0x400a4fc6`. Les faire afficher l'icône SNARE pour 6 : un octet ou un petit détour par site.

Les noms de machines ne servent **qu'à** l'écran MACHINES. Le navigateur de presets classe les sons par **tags** (KICK, SNARE… VINTAGE, table `0x4013e624`), indépendants de la machine : rien à changer.

## 5. Potards : la recherche « machine → descripteur »

Au démarrage, `0x4005a274` construit des tables de correspondance dans le BSS à partir des descripteurs :

| Table (BSS) | Contenu | Taille |
|---|---|---|
| `0x40a79418` | par machine, 8 index de descripteurs (slots 9..0x10 ; decay en tête) | 6 × 32 o |
| `0x40a7ada4` | par machine, CC 16..23 → descripteur | 6 × 32 o |
| `0x40a7ace4` | par machine, NRPN 128..135 → descripteur (inutilisé : aucun paramètre de machine n'a de NRPN) | 6 × 32 o |
| `0x40a79394`, `0x40a7a2e0`, `0x40a7a4e0`… | paramètres communs (slot, CC, NRPN) | |

Le constructeur range un descripteur dans la rangée de sa machine si son champ machine vaut 0..5 (`0x4005a340`). Les valeurs 6..9 forment un autre groupe. Aucun descripteur n'utilise 6.

Les fonctions qui lisent ces tables sont toutes bornées à la machine 5 :

| Fonction | Rôle | Machine 6 dans l'OS stock |
|---|---|---|
| `0x4005a692` (méthode, vtable `0x400fd168`) | (slot, machine) → descripteur | renvoie 0 = descripteur « Error / ERR » |
| `0x4005a556` | le descripteur est-il propre à une machine (champ ≤ 5) ? | — |
| `0x4000aa9a` (méthode, vtable `0x400fd16c`) | le descripteur s'applique-t-il à la piste ? (machines égales) | non |
| `0x4005a8ce` | (piste, machine, CC) → descripteur | table commune |
| `0x4005a92e` | (piste, machine, NRPN) → descripteur | table commune |

## 6. Descripteurs propres à SDVtg (option B retenue)

- **Table recopiée et agrandie.** La table ne peut pas grandir sur place : `0x4010ed80` porte une autre table utilisée. Elle est donc recopiée **depuis ton OS** dans la charge utile (`0x43034000`), avec 5 entrées de plus : 76..79 = COLOR/SHAPE/SWEEP/CONTOUR de SDVtg (champ machine 6), 80 = son « Amp Decay » (défaut 33).
  - Elles reprennent tout de SNARE (slot, plage, CC 16..19, drapeaux, groupe « Drum »), sauf les noms et les défauts. Noms tirés du manuel du Syntakt (section SD VINTAGE) : Inharmonicity / INHM, Freq Complex / FCMP, Pitch Sweep / SWEP, Mod Envelope / MENV ; défauts 0 / 110 / 74 / 80 / 33.
  - Le max du paramètre « Algorithm » passe à 6 **dans la copie**.
- **37 références** à la table (33 `lea`, un `move.l #`, 2 `addi.l` et un `move.l` vers `+8` / `+0x20`) pointent sur la copie. **43 bornes** d'accesseurs passent de 76/75 à 81/80.
  - Les bornes sont toutes celles des fonctions qui lisent la table, relevées automatiquement. Aucune autre borne 75/76 de l'OS n'est proche d'un appel à ces fonctions.
  - Deux « 76 » voisins **ne sont pas** des bornes de descripteurs (`0x4004df68`, `0x4004df82` : taille d'une structure de son de 76 o) : non modifiés.
  - L'ancienne table reste en place, intacte : une référence oubliée lirait encore des données justes pour 0..75.
- **État par descripteur** (trouvé en chemin) : 76 objets de 100 o à `0x40a71754`, construits un par un au démarrage par une routine de ~4 Ko (`0x400def5c..`). Leurs deux accesseurs (`0x4004df40`, `0x4004dfa2`) passent par un détour : 76..80 utilisent les objets de SNARE (51..55). Une piste n'a qu'une machine, donc le partage est sans conflit, et la routine de construction n'est pas touchée.
- **Tables du BSS** : les rangées par machine et les rangées de CC sont déplacées dans la charge utile avec 7 rangées (`0x43035200`, `0x43035300`, 7 réf.). Le constructeur efface 7 rangées et accepte le champ machine 6 (`0x4005a2b8`, `0x4005a340`).
- **Recherches** : bornes 5 → 6 dans `0x4005a692` et `0x4005a556`. Détour dans `0x4005a8ce` : piste 0..5 comme avant, machine 0..6. `0x4000aa9a` n'a rien à changer : il compare 6 à 6. NRPN inchangé.
- **Défauts au changement de machine** : ils viennent du descripteur trouvé, donc ceux du Syntakt pour SDVtg, sans code de plus.

## 7. Implémentation `[FAIT]`


**Fichiers** :
- `tools/gen_sdvintage_7th.py` génère `tweaks/model-cycles_OS1.13/22-sdvintage-7th.json`. Il réutilise l'analyse du Syntakt de `gen_sdvintage_exact.py` (même moteur, même passerelle), lit ton OS Cycles pour **vérifier les octets d'origine de chaque écriture**, et refuse toute écriture qui en chevauche une autre ;
- `tools/machines/syntakt_bridge/machine7.S` : 5 détours (état par descripteur ×2, CC, images de l'écran MACHINES, petite icône) ;
- `build.py` / `builder.js` : nouveau type de morceau de charge utile, `"cycles": [début, fin]`, copié depuis **ton** MAIN OS d'origine (comme les morceaux `"syntakt"`). Aucun octet Elektron dans le dépôt.

**111 écritures dans l'OS** :

| Groupe | Écritures |
|---|---|
| Démarrage (comme [17](17-portage-exact-syntakt.md)) | crochet `0x400004b2`, code de recopie dans le masque `0x4016cae8`, redirection du sprite |
| Descripteurs | 37 références, 43 bornes |
| Tables du BSS | 7 références, taille effacée, champ machine ≤ 6 |
| Recherches | 2 bornes, détour CC |
| Réglage de la machine d'une piste (`0x4001477e`) | borne `0x400147a4` : accepte 6 |
| État par descripteur | 2 détours |
| Moteur | bornes `0x400a7dba`, `0x400a7df4` ; octet `0x40118646` ; tables update/render à 7 entrées (entrée 6 = passerelle) |
| Écran MACHINES | borne `0x400a25e0`, 7 noms (« SDVtg »), 7 repères (`0x400a26e8`), détour des images (celles de SNARE pour SDVtg) |
| Icônes bornées | `0x4001b69c`, `0x400a40a6`, `0x400a4fb0` (valeur de repli 5 → 1), détour `0x400a4dc4` |

**Charge utile** (218 112 o, recopiée au démarrage) :

| Adresse | Contenu |
|---|---|
| `0x43000000..0x43033000` | moteur SD VINTAGE et passerelle, comme [17 §3](17-portage-exact-syntakt.md) |
| `0x43033000` | détours (`machine7.S`) |
| `0x43033800` | 7 noms, tables update/render à 7 entrées, chaînes |
| `0x43034000` | 81 descripteurs (76 copiés de ton OS + 5 de SDVtg) |
| `0x43035200`, `0x43035300` | rangées par machine et rangées de CC (7 × 32 o chacune) |

**Tailles** :
- MAIN OS décompressé : 1 962 304 o. Il finit à `0x401df540`, sous la zone de transit du bootstrap (`0x40200000`).
- `.syx` : 1 037 344 o.
- MAIN OS patché, SDVtg seul : `4c522c1c…`.

**Flasher web** : la case SD VINTAGE a deux variantes, « À la place de SNARE » (par défaut, testée) et « En 7ᵉ machine, SDVtg » (nouvelle). 47 combinaisons sont comparées à leur empreinte de référence (`REF_MAINOS`).

## 8. Preuve en émulation `[FAIT]`

`tools/emu/test_sdvintage_7th.py` exécute le **vrai code de l'OS**, stock et modifié, fonction par fonction :

| Vérification | Résultat |
|---|---|
| Décompression par le vrai bootstrap (`0x800006bc`) | OS relu à l'identique, fin `0x401df540` |
| Crochet de démarrage | charge utile recopiée intacte |
| Constructeur des tables `0x4005a274` | tout le BSS identique au stock ; rangées 0..5 identiques ; rangée 6 = (80, 0, 76, 77, 78, 79), CC 16..19 → 76..79 |
| (slot, machine) → descripteur, machines 0..6 × 34 slots | identique, sauf les 5 réponses de SDVtg |
| « propre à une machine », 90 index | identique, plus 76..79 |
| CC reçu → descripteur, 8 pistes × 7 machines × 128 CC | identique, sauf pistes 0..5 en machine 6, CC 16..19 |
| 23 accesseurs appelés pour 0..75 | identiques au stock (pointeurs ramenés à la copie) ; les 17 méthodes d'objet sont vérifiées au désassemblage (43 bornes, 5 `jmp`) |
| Descripteurs 76..80 | machine 6, slots, noms, plages, défauts 0/110/74/80/33 ; « Algorithm » va jusqu'à 6 |
| État par descripteur | 0..75 inchangés ; 76..80 → objets de SNARE |
| Écran MACHINES (dessin intercepté) | pour 0..5 : mêmes noms et mêmes images que le stock ; 7 repères ; pour 6 : « SDVtg », images de SNARE, 7ᵉ repère plein (stock : « Error ») |
| Réglage de la machine d'une piste (`0x4001477e`, objets factices) | identique pour 0..5 ; 6 accepté et défauts de la machine chargés (stock : refusé) ; 7 refusé |
| Icône bornée | identique pour 0..5 ; SNARE au lieu de CHORD pour 6 |
| Son | SDVtg identique au Syntakt (6 cas, 1 LSB) ; **SNARE identique échantillon par échantillon à l'OS stock** ; repos : 0 instruction du Syntakt ; machine lock SNARE → SDVtg sur une piste : les deux jouent |

Le portage « à la place de SNARE » ([17](17-portage-exact-syntakt.md)) reste identique.

## 9. Compatibilité et sécurité

- **Projets existants** : inchangés (machines 0..5, même code qu'avant pour elles).
- **Projet ou preset avec SDVtg relu sur l'OS officiel** (ou avec le mod « à la place de SNARE ») : d'après les bornes ci-dessus, aucun plantage attendu. La piste joue CHORD (borne de la boucle), l'écran MACHINES affiche « Error », les potards pointent sur le descripteur « ERR » (sans effet), les icônes montrent CHORD. Avant de revenir à l'OS officiel, repasser ces pistes sur une autre machine.
- **Démarrage** : au démarrage, seuls le crochet de recopie et le constructeur des tables changent, et tous deux sont vérifiés en émulation. Le reste ne diffère qu'avec une piste en SDVtg. Aucune instruction du Syntakt ne s'exécute avant qu'une piste SDVtg soit jouée.
- **Secours sans interface MIDI** : si un projet avec SDVtg faisait planter l'interface à chaque démarrage, EMPTY RESET (TRIG 2) ou FACTORY RESET (TRIG 3) dans le menu de démarrage ([FUNC] à l'allumage) réinitialise le projet actif (manuel §13). Le Cycles redémarre alors, et `CONFIG › UPGRADE` reste possible. Les projets doivent être sauvegardés avant (Transfer).

## 10. Test sur la machine

**1ᵉʳ essai (30/09/2026, 1ʳᵉ version)** : l'OS démarre, l'écran MACHINES dessine bien 7 repères, mais la molette s'arrête à Chord.
- Cause : le réglage de la machine d'une piste, `0x4001477e`, refuse toute valeur au-delà de 5 (`moveq #5 ; cmp ; bcs.w` → sortie, en `0x400147a4`) avant d'écrire la machine dans le son (+38) et d'appeler le chargement des défauts (`0x40014072`).
- Pourquoi il avait échappé à l'inventaire :
  - la borne est placée **avant** la lecture de +38, que j'avais relevée ;
  - et une borne « ≤ 5 » ressemble à celle des 6 pistes.
- Corrigé : borne 5 → 6. Le test d'émulation exécute maintenant ce réglage (objets factices) : l'OS stock refuse 6, la version corrigée l'accepte et charge les défauts de SDVtg.
- Recherche systématique des autres cas : toutes les écritures du champ machine (+38), et toutes les sorties « `moveq #5` ; `cmp` ; `bcs`/`bhi` » dans une fonction qui touche ce champ. Seul ce site est concerné.

**2ᵉ essai** `[À FAIRE]` :

1. Sauvegarder les projets (Transfer).
2. Flasher par USB (`CONFIG › UPGRADE`) la variante « En 7ᵉ machine, SDVtg ».
3. Menu MACHINES : 7 machines, « SDVtg » en dernier avec l'icône de SNARE, 7ᵉ repère allumé.
4. Choisir SDVtg sur une piste : les potards affichent Inharmonicity, Freq Complex, Pitch Sweep, Mod Envelope ; les valeurs passent aux défauts du Syntakt (0, 110, 74, 80, DECAY 33).
5. Jouer : son du Syntakt. Repasser une piste en SNARE : la SNARE d'origine, défauts d'origine (0, 127, 8, 0, 40).
6. À vérifier aussi : un machine lock vers SDVtg, le CC 70 à la valeur 6, les CC 16..19 sur une piste SDVtg, un projet sauvegardé puis rechargé.
