# 18 · SD VINTAGE en 7ᵉ machine, à côté de SNARE (faisabilité)

Travail du 30/09/2026, à la demande de l'utilisateur : ajouter SD VINTAGE **dans la liste des machines**, sans remplacer SNARE (SD Basic), avec les bons affichages de potards.
Point de départ : le plan de [14 §8](14-machine-sd-vintage.md) et le moteur exact de [17](17-portage-exact-syntakt.md), testé sur la machine.

Toutes les adresses sont celles du MAIN OS 1.13 officiel. Source : désassemblage de l'image stock (`m68k-elf-objdump`, ColdFire V4e), sauf mention du manuel.

## 0. En bref

**C'est faisable.** Tout ce qui dépend du nombre de machines est localisé, et partout l'OS borne l'index de machine à 0..5 **sans lire hors de ses tables** : une machine 6 non gérée donne « Error », l'icône CHORD, ou aucun paramètre, jamais une lecture au hasard.

| Domaine | Ce qu'il faut changer | Difficulté |
|---|---|---|
| Moteur audio | 3 bornes, 1 octet, tables `update`/`render` à 7 entrées (§2) | faible, déjà cartographié |
| Choix de la machine (menu MACHINES, machine locks, CC 70) | borne max du paramètre « Algorithm » (§3) | 1 octet |
| Écran MACHINES | borne, 7ᵉ nom, icône (§4) | faible |
| Potards COLOR/SHAPE/SWEEP/CONTOUR/DECAY | 4 fonctions de recherche « machine → descripteur » (§5) | moyenne |
| Défauts propres à SD VINTAGE | descripteurs propres = déplacer la table (§6) | élevée (option B) |
| Icônes ailleurs (navigateur de presets, pistes) | 4 affichages bornés à 5 (§4) | faible |

Deux options pour les potards (§6) :
- **A — partager les descripteurs de SNARE.** Mêmes libellés, plages et CC que SNARE ; valeurs par défaut de SNARE au choix de la machine. Peu de code, risque faible.
- **B — descripteurs propres.** Défauts du Syntakt (0/110/74/80/33) et noms propres (par ex. INHM, FCMP, SWEP, MENV). Il faut déplacer la table des 76 descripteurs pour en ajouter 5.

## 1. Comment l'OS gère les machines

- **Manuel** (Model:Cycles User Manual, OS 1.13, §10.2 et §9.12.3) :
  - la touche [MACHINES] ouvre la liste, parcourue avec LEVEL/DATA ;
  - la machine peut être **verrouillée par pas** (« machine locks ») ;
  - COLOR, SHAPE, SWEEP et CONTOUR changent de rôle selon la machine ;
  - CC 70 = « Machine Selection » (annexe A).
- **Paramètre « Algorithm »** (descripteur n° 41, `0x4010e5d8`, nom court ALG, slot 9) : l'écran MACHINES lit la machine avec ce descripteur (`vtable[28](piste, 0x29)` en `0x400a25d8`), et l'édition passe par le setter générique `0x4000a980`, qui borne à [min, max] du descripteur. **Le max (5) décide donc de ce qu'on peut choisir partout** : menu, machine locks, CC.
- **Descripteurs** (`0x4010dce0`, 76 entrées de `0x38` o, [14 §2.1](14-machine-sd-vintage.md)) : pour chaque machine 0..5, quatre entrées COLOR/SHAPE/SWEEP/CONTOUR (champ machine = 0..5) suivies d'un « Amp Decay » avec le défaut propre à la machine.
  - Les noms courts sont les mêmes pour toutes les machines (COLR, SHPE, SWEP, CONT, DEC) ; seuls les noms longs changent (« Snare Color »…).
  - Les entrées des 6 machines partagent les mêmes slots (`0x0b..0x0e`, `0x12`) : un son stocke ses valeurs **par slot**, commun à toutes les machines. Ajouter une machine ne devrait donc pas changer le format des projets.

## 2. Moteur audio `[CONNU]`

Boucle des voix `0x400a7d4a` ([14 §2.3](14-machine-sd-vintage.md)) :
- bornes `moveq #5` en `0x400a7dba`, `0x400a7dc0` (index au déclenchement) et `0x400a7df4` (garde du dispatch) → 6 ;
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
| `0x40a7ace4` | par machine, NRPN 128..135 → descripteur | 6 × 32 o |
| `0x40a79394`, `0x40a7a2e0`, `0x40a7a4e0`… | paramètres communs (slot, CC, NRPN) | |

Quatre fonctions les lisent, toutes bornées à la machine 5 :

| Fonction | Rôle | Machine 6 aujourd'hui |
|---|---|---|
| `0x4005a692` (méthode, vtable `0x400fd168`) | (slot, machine) → descripteur | renvoie 0 = descripteur « Error / ERR » |
| `0x4000aa9a` (méthode, vtable `0x400fd16c`) | ce descripteur s'applique-t-il à la piste ? (machine du descripteur = machine de la piste) | non |
| `0x4005a8f0` | CC reçu → descripteur | table commune |
| `0x4005a92e` | NRPN reçu → descripteur | table commune |

Ce sont des méthodes appelées par tables virtuelles : les modifier elles-mêmes suffit, tous leurs appelants suivent.
**Option A** : dans ces 4 fonctions, traiter la machine 6 comme la machine 1. SD VINTAGE a alors exactement les potards, plages, CC et p-locks de SNARE, et les tables du BSS ne changent pas.

## 6. Défauts et noms propres (option B)

- L'OS remet un paramètre à son défaut par `0x4000b30e`, qui lit le défaut du descripteur (méthode de 4 classes, vtables `0x400fd0dc`, `0x400fd144`, `0x400fd1ac`, `0x400fd214`).
- Avec l'option A, choisir SD VINTAGE donnerait les défauts de SNARE (COLOR 0, SHAPE 127, SWEEP 8, CONTOUR 0, DECAY 40) au lieu de ceux du Syntakt (0, 110, 74, 80, 33). **À vérifier sur la machine** : l'OS applique-t-il les défauts de la machine quand on la change ?
- Pour des défauts et des noms propres, il faut 5 descripteurs de plus. La table ne peut pas grandir sur place : `0x4010ed80` porte une autre table utilisée (`0x4005cbbe`…). Il faudrait la **déplacer** avec 81 entrées :
  - 33 `lea 0x4010dce0` et 3 références internes à réécrire ;
  - les bornes `#76` / `#75` des accesseurs (une par accesseur, près de chaque `lea`) ;
  - la boucle du constructeur `0x4005a274` ;
  - une rangée 6 dans les 3 tables par machine du BSS, qui n'ont pas de place au-delà de la 6ᵉ : les déplacer aussi, ou les servir depuis notre charge utile.
- Plus sûr et plus léger, si l'OS applique bien des défauts au changement de machine : un petit détour dans `0x4000b30e` qui, pour une piste en machine 6, prend les défauts du Syntakt. Il garde l'option A pour tout le reste.

**Noms à l'écran** : quand on tourne un potard, l'OS affiche probablement le nom court (`0x4002650e` le dessine avec une police). Il est le même pour toutes les machines (COLR…) : avec l'option A, l'affichage de SD VINTAGE est donc celui de toutes les machines du Cycles. Des noms Syntakt (INHM…) demandent l'option B. **À confirmer à l'écran.**

## 7. Compatibilité et sécurité

- **Projets existants** : inchangés (machines 0..5, même code qu'avant pour elles).
- **Projet ou preset avec SD VINTAGE relu sur l'OS officiel** : d'après les bornes ci-dessus, aucun plantage attendu. La piste joue CHORD (borne de la boucle), l'écran MACHINES affiche « Error », les potards pointent sur le descripteur « ERR » (sans effet), les icônes montrent CHORD. Avant de revenir à l'OS officiel, repasser ces pistes sur une autre machine.
- **Démarrage** : le code ajouté ne change rien pour les machines 0..5. Il ne s'exécute différemment qu'avec une piste en machine 6.
- **Secours sans interface MIDI** : si un projet avec SD VINTAGE faisait planter l'interface à chaque démarrage, EMPTY RESET (TRIG 2) ou FACTORY RESET (TRIG 3) dans le menu de démarrage ([FUNC] à l'allumage) réinitialise le projet actif (manuel §13). Le Cycles redémarre alors, et `CONFIG › UPGRADE` reste possible. Les projets doivent être sauvegardés avant (Transfer).

## 8. Validation prévue (avant tout flash)

1. **Tables et recherches** : exécuter en émulation le vrai constructeur `0x4005a274`, puis les 4 recherches pour toutes les combinaisons (slot, machine 0..6). Stock et modifié doivent être **identiques pour 0..5**, et la machine 6 doit renvoyer les réponses de SNARE.
2. **Écran MACHINES** : exécuter son dessin avec les fonctions de dessin interceptées (texte `0x40071a04`, sprites `0x40071da4`), et relever pour m = 0..6 le nom et les images demandées.
3. **Audio** :
   - machine 6 identique au Syntakt (test du portage exact) ;
   - **machine 1 identique à la SNARE d'origine** (comparaison avec l'OS stock) ;
   - bascule par machine lock ;
   - repos sûr.
4. **Constructions** : même empreinte en Python et en JS ; le flasher web proposera « remplacer SNARE » ou « 7ᵉ machine », qui s'excluent.

## 9. Questions ouvertes (à regarder sur la machine)

- Changer de machine (menu MACHINES) remet-il COLOR/SHAPE/SWEEP/CONTOUR/DECAY aux défauts de la nouvelle machine ?
- Quel nom s'affiche quand on tourne COLOR : `COLR`, « Snare Color », autre ?
- Le nom de la 7ᵉ machine doit tenir entre x = 32 et l'icône (x = 96) : 5 lettres comme « Snare » et « Chord » tiennent. Pour « Vintage » (7 lettres), il faudra vérifier à l'écran.
