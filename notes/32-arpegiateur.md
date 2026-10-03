# 32 · Arpégiateur à la place du retrig

Travail du 03/10/2026, à la demande de l'utilisateur : « J'aimerais que tu intègres une fonction d'arpégiateur. Par défaut le retrigger, menu accessible via FUNC + RETRIG, active la répétition sur une seule note lorsqu'elle est jouée. J'aimerais que ce soit plutôt un arpégiateur, et que dans le menu retrig on ait des options d'arpégiateur, genre le sens de l'arpège, etc. »

Choix de l'utilisateur (questions du 03/10/2026) :
- **sens** : montant, descendant, aller-retour, aléatoire, ordre de jeu (et « Off », le retrig d'origine) ;
- **une note ajoutée pendant l'arpège** entre dans l'arpège sans couper le rythme ;
- **réglages enregistrés avec le pattern**, comme `Rte` et `Len`.

Source de tout ce qui suit : désassemblage du MAIN OS 1.13 officiel (`m68k-elf-objdump`), sauf mention contraire.

## 0. En bref

| | État |
|---|---|
| Retrig d'origine : menu, envoi de la note, répétitions | `[FAIT]` compris (§1–§3) |
| Place pour le code | `[FAIT]` masque libéré `0x4018a788` (§5) |
| Place pour les réglages | `[FAIT]` octet +512 de la piste, inutilisé et sauvegardé (§4) |
| Code de l'arpégiateur et lignes du menu | `[FAIT]` `tweaks/model-cycles_OS1.13/40-arp.json` (§9) |
| Preuve en émulation | `[FAIT]` jusqu'à la vraie boucle d'événements de l'OS, sur 4 firmwares (§9) |
| Flasher web, guide | `[FAIT]` carte « Arpégiateur », section 9 du guide, version 1.12 |
| Essai sur la machine | `[FAIT]` 2e essai, après correction : « ça marche nickel ! » (§10) ; étiquette « testé » après un essai depuis le flasher |

## 1. Le menu « Retrig Setup » (FUNC + RETRIG)

- Classe `RetrigPadsMenuView` (nom RTTI en `0x40126f7b`), titre « Retrig Setup » (`0x40126f53`). Constructeur `0x4002d138`.
- Trois lignes : `Rte` (`0x40126f46`), `Len` (`0x40126f4a`), `A.On` (`0x40126f4e`).
- Chaque ligne est un `MenuItem` de 84 o (`new 0x54`), construit par `0x400734b0(item, &libellé, &appui, &affichage, &changement, -1, 8)`, puis ajouté au menu par `0x40072ce6(menu, item)`. Les quatre arguments sont des `std::function` de 16 o : stockage en +0, gestionnaire en +8, appel en +12.

| Ligne | Libellé | Appui | Affichage | Changement |
|---|---|---|---|---|
| `Rte` | `0x4002cc1c` | `0x4002ccaa` | `0x4002d6e4` | `0x4002d48c` |
| `Len` | `0x4002cc44` | `0x4002ccd0` | `0x4002d768` | `0x4002d4f4` |
| `A.On` | `0x4002cc6c` | — | `0x4002d660` | `0x4002d52c` |

- Valeurs : `Rte` = octet +514 de la piste (accès `0x40016086` / `0x400160b6`, 0 à 16, affiché « 1/n » par la table `0x4010ce4c`). `Len` = octet +513 (`0x4001611a` / `0x4001614a`, 0 à 127). `A.On` = un booléen par piste dans un autre objet (`0x4000ccc0` / `0x4000cd2a`).
- Une modification de `Rte` est aussi envoyée au retrig en cours (`0x400588f0`).

## 2. De la touche à la note

- Appui sur une touche de note : `0x4001a0xx`. Si RETRIG est tenu (`0x4007faf4(4)`, code de touche 4) ou si `A.On` est actif, la vitesse du retrig est passée à `0x40019f44(objet, touche, piste, note, vélocité, vitesse)`, sinon -1.
- L'objet garde la liste des touches tenues en +148 (vecteur d'entrées de 20 o : actif, touche, note, piste, 1).
- Note jouée : `0x40019e7a`, puis `0x4008171e(piste, note, vélocité, 0x40, …, -1, vitesse)`. Ce dernier construit un message de 56 o (indicateur 0x8000 si retrig) et l'envoie au côté audio par `0x4005894a`.
- Relâchement : `0x40019d00` → `0x40019c84` → `0x4008145e(piste, note, 0x40)` : message de fin de note, même chemin.

## 3. Côté audio : les répétitions

- `0x4005894a` transforme le message en événement (type 0, +4 = 1 note / 2 fin, +8 piste, +12 = 2 pour le jeu en direct, +22 vélocité, +28 note, +40 indicateurs, +56 vitesse, +60 durée, +64 courbe) et le met dans la file `0x40fe15fc`.
- La file est lue au début de chaque bloc audio (`0x40058d46`). Les notes passent par `0x40058e28`.
- Note avec l'indicateur retrig (0x8000) et sans 0x40000 (pas une répétition) : `0x400585a8` prépare l'état de la piste, 28 o en `0x40a78d58 + 28 × piste` :
  - +0 compteur, +4 fin (-1 : tant que la touche est tenue), +12 durée, +16 position dans le cycle de 960, +20 copie de l'événement, +24 vitesse.
- Les répétitions sont des événements de type 6, programmés par `0x40058552` et traités par `0x40058736` :
  - chaque tic, un motif de bits par vitesse (`0x4010ce90`) dit s'il faut rejouer ;
  - si oui, la copie (+20) est recopiée dans un nouvel événement (`0x40091f20`, en `0x400587f6`) avec l'indicateur 0x40000, et insérée juste après dans la file : elle est jouée comme une note.
- Fin de note (+4 = 2) : seulement si c'est la note en cours de la piste (`0x40fe4cb4[piste]`), `0x400588c8` arrête un retrig sans fin (`0x40058530`).
- **Conséquence (comportement d'origine)** : une nouvelle touche remplace la note répétée ; relâcher une autre touche ne fait rien ; relâcher la note en cours arrête tout, même si d'autres touches sont tenues.

## 4. Où ranger le sens et les octaves : l'octet +512 de la piste

- La piste d'un pattern existe sous deux formes de 722 o : en mémoire (`B`, `0x406f3a40 + pattern × 30710 + piste × 722`, pattern en cours : `0x40054828`) et dans le fichier (`A`). `0x4005b4ec` (`A` → `B`, au chargement) et `0x4005b642` (`B` → `A`, à l'enregistrement) recopient les champs un par un.
- `B[512]` ↔ `A[704]` est recopié tel quel dans les deux sens, sans borne. Aucune fonction de l'OS 1.13 ne le lit ni ne l'écrit en dehors de ces conversions (et des conversions d'anciennes versions de fichier, `0x4005c040`, `0x4005c1cc`). Les accesseurs des champs de piste (`0x40015800..0x40017200`) couvrent 513–515, 516, 580, 644, 708–721, mais pas 512.
- Model-TG ne l'utilise pas (son `src/model_tg.s`, v1.1.0).
- Codage retenu : bits 0–2 = sens (0 montant, 1 descendant, 2 aller-retour, 3 aléatoire, 4 ordre de jeu, 5 Off ; 6 et 7 lus comme montant), bits 3–4 = octaves − 1. **0 = montant, 1 octave** : les projets existants passent en arpégiateur, ce qui revient au retrig d'origine tant qu'on ne tient qu'une note.
- L'OS d'origine ignore cet octet : un projet enregistré avec l'arpégiateur reste sûr sans lui.

## 5. Où loger le code : le masque libéré `0x4018a788`

- 1 024 o de `0xFF`, masque du sprite 64×128 (damier inverse), libéré en faisant lire à ce sprite le masque partagé identique `0x40154ae4` (constante `0x400ad1aa`, `tools/sprites.py`, [notes/14 §5](14-machine-sd-vintage.md)).
- Seul `sdvintage-snare` (build.py seulement, pas dans le flasher) l'utilise : l'arpégiateur lui sera incompatible.
- Aucun autre tweak (6 canaux, Model-TG, moteurs du Syntakt, drumkilla) n'écrit dans `0x40058736..0x4005881a`, `0x400585a8`, `0x40058e28..0x40058fa2`, ni dans le menu. Model-TG accroche l'entrée de `0x4008171e` et `0x4008145e` (Scale Lock), côté interface : sans conflit.

## 6. Conception

- **Notes tenues** : le côté audio garde, par piste, la liste des notes enfoncées en jeu direct avec le retrig.
- **Filtre** en tête du traitement des notes (`0x40058e28`), pour le jeu en direct (+12 = 2) :
  - note retrig nouvelle alors qu'un arpège tourne sur la piste : ajoutée à la liste, événement ignoré (+12 = -1) : le rythme continue ;
  - première note : liste remise à cette note, le retrig d'origine démarre ;
  - fin de note : retirée de la liste ; s'il en reste, ignorée ; sinon, elle devient la fin de la note en cours (+28 = `0x40fe4cb4[piste]`), et l'OS arrête tout comme d'habitude.
- **Répétition** (`0x400587f6`) : après la copie, la note devient la suivante de l'arpège.
- **Suivante** : montant/descendant/aller-retour d'après la dernière note jouée (robuste quand la liste change) ; ordre de jeu par position ; aléatoire par un générateur congruentiel. Octaves : chaque note tenue + 12 × k.
- **Menu** : deux lignes de plus, « Arp » et « Oct », construites comme les autres en fin de constructeur, avec les gestionnaires de `std::function` de l'OS.

## 7. Vérifié pour l'écriture du code (03/10/2026)

- **Constructeur du menu exécuté en émulation** (`t7.UI`, `SR` = 0x2700, `new` `0x400802e0` et `delete` `0x400802ec` interceptés) : trois appels à `0x400734b0`, arguments dans l'ordre (libellé, appui, affichage, changement, -1, 8).
  - `Len` : libellé gestionnaire `0x4002ceae` (fermeture vide de 1 o) ; appui `0x4002cf00` + `0x4002ccd0` (fermeture = le menu) ; affichage `0x4002cf5c` (fermeture = le menu) ; changement `0x4002cfb8` (fermeture vide).
  - `A.On` : appui = bascule `0x4002d52c`, pas de fonction de changement.
- **Conventions des fonctions appelées** (à recopier) :
  - libellé : adresse de la chaîne de retour dans `a0`, `0x400f980c(a0, texte, &allocateur)` (`0x4002cc44`) ;
  - affichage : `0x40072260(tampon, 0x40140ab0)`, puis `0x40071a04(arg E+12, tampon, (arg E+16) + 24, arg E+20, 4, format, valeur)`, puis `0x40072080(tampon)` (`0x4002d768`) ;
  - changement : écart en E+12 (`0x4002d4f4`).
- Formats : « %s » en `0x40124b58`, « %d » en `0x40126f6e` (fin de « 1/%d »).
- Écriture d'un réglage de piste : pointeur par `vtable[40]` de l'objet `0x4000f23e(0x400cf866())`, puis `vtable[16](objet, &0x400ff5ac)` pour signaler la modification (comme `0x4001614a`).
- Points d'accroche, aucun saut vers leur intérieur :
  - `0x40058e28` (10 o : `moveq #-1,d1 ; move.l 8(a2),d2 ; move.l 12(a2),d0`) → `jsr` filtre + 2 `nop`, le filtre rejoue ces trois instructions ; `a0`/`a1` sont libres à cet endroit (la suite, `0x40058e3e` et `0x400591a4`, ne les lit pas avant de les écrire) ;
  - `0x400587f6` (`jsr 0x40091f20`, copie de 80 o) → `jsr` copie + note de l'arpège ;
  - `0x4002d480` (`movem.l 24(sp),d2-d6/a2-a6`) → `jmp` vers nos lignes, puis épilogue rejoué (`lea 128(sp),sp ; rts`).
- Côté audio, pattern en cours : `*(0x40a7887c) + 30706` (0 à 95), piste `0x406f3a40 + pattern × 30710 + piste × 722`.

## 8. Reste à faire

- **Essai sur la machine** : ouvrir FUNC + RETRIG (cinq lignes, Arp et Oct lisibles et réglables), jouer plusieurs notes avec RETRIG tenu, chaque sens, les octaves, l'enregistrement du pattern. Puis l'étiquette « testé ».
- Non émulé : l'écran lui-même (place des deux lignes, défilement du menu), la touche RETRIG et le mode clavier, l'enregistrement sur la carte mémoire.

## 9. Réalisation `[FAIT en émulation]`

**Fichiers** :
- `tools/machines/arp/arp.c` : le filtre et les répétitions (côté audio), les deux lignes du menu (côté interface) ;
- `tools/machines/arp/arp_hooks.S` : l'accroche du filtre, la fin du constructeur du menu, le libellé (chaîne rendue en `a0`) ;
- `tools/machines/arp/arp.ld` : deux zones ;
- `tools/gen_arp.py` → `tweaks/model-cycles_OS1.13/40-arp.json` (7 écritures).

**Place** (le code compilé fait 1 736 o, plus que les 1 024 o d'un masque) :
- partie audio et état : 976 o dans `0x4018a788` (masque libéré, constante `0x400ad1aa`) ;
- menu : 760 o dans `0x4016cba8..0x4016cee8`, la fin du masque `0x4016cae8`, dont les moteurs du Syntakt gardent le début (188 o au plus) pour leur crochet de démarrage.
- Les deux tweaks font alors la même écriture du pointeur de sprite (`0x400b1106`). `tools/build.py` et `docs/flasher/builder.js` acceptent désormais une écriture déjà faite à l'identique par un autre tweak (sinon, les octets d'origine doivent toujours correspondre).
- Incompatible avec `sdvintage-snare` (build.py seulement), qui occupe les deux masques.

**Menu** : une seule fonction de libellé, d'affichage et de changement pour les deux lignes. Le gestionnaire de `std::function` `0x4002cf00` de l'OS (fermeture de 4 o copiée telle quelle) garde, selon la fonction, le texte du libellé, le menu (pour l'appui d'origine `0x4002ccd0`) ou le numéro de la ligne. Valeurs affichées : `UP`, `DOWN`, `UPDN`, `RAND`, `PLAY`, `OFF` et 1 à 4. Le menu n'est construit qu'à l'ouverture de FUNC + RETRIG (`new 0x250` puis `0x4002d138`, appelé en `0x4001cb3e`) : rien ne change au démarrage.

**Preuve** (`tools/emu/test_arp.py`, sur `arp` seul, `model-tg + arp`, `6ch-usbup + model-tg-st + syntakt-tg-sd-cp-toy-bits-swarm + arp`, et drumkilla + `syntakt-sd-cp` + `arp`) : TOUT OK.
- Filtre (accroche réelle) : instructions remplacées rejouées, registres gardés ; 1re note laissée à l'OS ; notes ajoutées ignorées (+12 = -1) ; fins de note ; sens OFF ; liste oubliée quand l'OS a arrêté le retrig ; autres événements intacts.
- Répétitions (accroche réelle, vraie copie `0x40091f20`) : suites exactes pour chaque sens, 1, 2 et 4 octaves (bornées à 127), le reste de l'événement intact ; RAND jamais deux fois la même de suite.
- Menu (vrai constructeur) : cinq lignes, libellés « Arp » et « Oct » construits en vraie `std::string` (ancienne ABI de la libstdc++ : un pointeur, la longueur 12 o avant), affichage au format et à la place de `Len`, changements bornés de l'octet +512 avec les autres bits gardés, signalés comme ceux de `Len`.
- De bout en bout, **vraie boucle d'événements de l'interruption audio** (`0x40058d46..0x400591e4`, file et réserves de l'OS initialisées par `0x40091d94`, notes entrées par `0x4005894a` comme depuis l'interface) :
  - note 60 avec retrig : jouée, retrig sans fin en place, 1re répétition programmée ;
  - note 64 ajoutée : pas jouée tout de suite ;
  - répétitions 64, 60, 64, 60… (UP), la hauteur suit ;
  - fin de la 60 : seule la 64 continue ; fin de la 64 : l'OS arrête le retrig et libère la copie, plus rien ensuite ;
  - sens OFF : la nouvelle note remplace l'autre, comme d'origine.

**Flasher web** : carte « Arpégiateur » (expérimentale), placée avant celle des moteurs du Syntakt (les clés des combinaisons mettent les moteurs en dernier). `webflash_smoke.sh` ALL OK (1 275 vérifications), les 1 151 combinaisons reconstruites dans la page identiques à `tools/build.py` ; `webbuild_check.sh` OK (parité Python/JS, règles des caves).

**Coût** (instructions, émulation) : filtre 19 par note du séquenceur, 89 par note jouée en direct ; une répétition 236 avec une note (copie d'origine comprise), au pire environ 1 400 (UP ou UPDN, 12 notes sur 4 octaves), soit environ 1,3 % d'un bloc, seulement au bloc où elle tombe.

## 10. Essai sur la machine et correction (03/10/2026)

**1er essai** (firmware de `build.py`, 6 canaux + Model-TG + 5 moteurs + arpégiateur, MAIN OS `5bc0135e…`). Retour de l'utilisateur : « L'arpégiateur marche, par contre uniquement en montant. Les paramètres de l'arp (down, random, off, etc.) ne changent rien, et le paramètre d'octave non plus. »

**Cause** : le côté audio lisait le réglage dans la banque de patterns du séquenceur (`0x406f3a40 + pattern × 30710`). Le menu, lui, écrit dans les données de l'objet « piste » de l'interface (`0x4000cfcc(0x4000f208(…), piste)`, `vtable[10]` = le pointeur en +16, `0x400d639e`). C'est une autre copie : l'interface envoie au séquenceur des adresses dans sa banque (`0x400083c8`, `0x4002018a`, `0x400203b4`), qu'elle remplit elle-même. Le côté audio lisait donc toujours 0 (montant, 1 octave).
- Les tests ne l'avaient pas vu : celui du menu utilisait un objet factice, et celui de bout en bout écrivait l'octet directement dans la banque du séquenceur. Le lien entre les deux n'était pas vérifié.

**Correction** : l'interface transmet le réglage au côté audio (`ui_cfg`, un octet par piste dans la zone audio).
- À chaque note jouée : les deux seuls endroits qui lisent `Rte` pour une note (`0x4001a1c4`, piste en `d3`, et `0x4001d25e`, piste en `d2`) passent par `arp_rate_d3` / `arp_rate_d2`. `arp_rate` lit les données de l'objet de la piste, rend `Rte` comme `0x40016086` (octet +514, 0 sans données), et note l'octet +512 de cette piste. C'est le même objet que celui du menu, pour la même piste (`0x4000f23e` = `0x4000cfcc(0x4000f208(…), 0x40012412(…))`).
- À chaque changement dans le menu : la piste sélectionnée (`0x40012412(0x4000eb90(0x400cf866()))`, comme la fonction de changement de `Rte` en `0x4002d48c`) reçoit le nouvel octet tout de suite, même pendant que les notes sont tenues.
- Le filtre et les répétitions lisent `ui_cfg` au lieu de la banque.
- Place : 1 010 o dans la zone audio, 824 o dans celle du menu. 9 écritures sur l'OS (2 de plus). Le tweak exporte l'adresse de `ui_cfg` (`symbols`, pour les tests).

**Tests** (`tools/emu/test_arp.py`, TOUT OK sur les 4 firmwares) : le réglage arrive maintenant au côté audio par les vraies accroches, dans tous les tests.
- Nouveau : les deux accroches rendent `Rte` comme `0x40016086` et transmettent le réglage, avec les registres gardés ; rien sans données ni hors des pistes 0 à 5.
- Nouveau : chaque changement dans le menu est transmis tout de suite pour la piste sélectionnée.
- Nouveau, de bout en bout : `DOWN` sur 2 octaves (76, 72, 64, 60…), puis passage à `UP` pendant que les notes sont tenues, puis à 1 octave.
- Firmware d'essai suivant : `build/model-cycles_OS1.13_model-tg-1.1_syntakt-5-moteurs_6ch_arp2.syx`, MAIN OS `ae96a31d…`.

**2e essai** (ce firmware, construit par `build.py`, même MAIN OS que le flasher pour cette combinaison). Il était demandé de changer Arp et Oct en jouant plusieurs notes avec RETRIG, puis de vérifier les réglages après enregistrement et redémarrage. Retour de l'utilisateur : « ça marche nickel ! » (la tenue des réglages après redémarrage n'est pas confirmée explicitement). L'étiquette « testé » attend l'essai d'un firmware construit par le flasher.

**3e essai** (même jour, `…_arp3.syx`, MAIN OS `d2e1aeb9…`, avec aussi les mutes immédiats de Model-TG, notes/31 §10) : il était demandé de vérifier les mutes, l'arpégiateur, et si possible la tenue des réglages après enregistrement et redémarrage. Retour de l'utilisateur : « c bon ça fonctionne nickel ».
