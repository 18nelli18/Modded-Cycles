# 50 — MACRO et les moteurs du Syntakt sur la même machine

Demande de Maxime, le 07/10/2026 dans le fil de la machine MACRO, après l'avoir testée : « J'aimerai que le mod MACRO
soit combinable avec les mod syntakt. Les avoirs sur la machine tout les deux. » Jusqu'ici le flasher rendait les deux
cartes exclusives ([43 §6](43-machine-macro.md)). Tweaks `24-syntakt-<moteurs>-macro.json` (seuls) et
`31-syntakt-tg-<moteurs>-macro.json` (avec Model-TG), 31 combinaisons de moteurs chacun ; générateur
`tools/gen_macro_syntakt.py` ; preuve `tools/emu/test_macro_syntakt.py`. Adresses : VA de l'OS 1.13.

## Réponse courte

- **Les deux ensemble, MACRO en dernier** : les moteurs cochés gardent leurs numéros (à partir de la 7ᵉ machine, de la
  8ᵉ avec Model-TG), MACRO prend la machine suivante. Avec Model-TG et les 5 moteurs : Sampler 7ᵉ, moteurs 8ᵉ à 12ᵉ,
  MACRO 13ᵉ.
- **Une seule charge utile** porte les deux : la partie des moteurs est exactement celle de leur tweak (passerelle
  reprise octet pour octet, celle qui a été testée sur la machine), MACRO est posée au-dessus.
- **La place** : en clair, moteurs + MACRO dépassent la limite de l'image décompressée (`0x40200000`) d'environ 80 Ko
  avec Model-TG. La charge utile entière est donc rangée **compressée** (aPLib, la variante d'Elektron déjà utilisée
  pour la section 3) et décompressée au démarrage : 471 792 o en mémoire, 229 à 241 Ko dans l'image ; pire cas
  (Model-TG + 5 moteurs + MACRO) fin à `0x401fa5f4`, **23 052 o de marge** (§3).
- **Le régulateur de charge des moteurs** ([25](25-regulateur-de-charge.md), [36](36-regulateur-sans-coupures-inutiles.md))
  **veille aussi sur les pistes MACRO** dans ces combinaisons ; MACRO seule n'en a toujours pas.
- **Flasher** : les deux cartes se cochent ensemble ; la combinaison de moteurs prend alors sa version avec MACRO.
- **Prouvé en émulation** `[FAIT en émulation]` (§6), pas encore essayé sur la machine.

## 1. Pourquoi ce n'était pas possible tel quel `[FAIT]`

Les deux mods sont construits de la même façon (machines ajoutées, [20](20-moteurs-syntakt-a-cocher.md),
[43 §2](43-machine-macro.md)) et prennent les mêmes places :

| | Moteurs du Syntakt | MACRO seule |
|---|---|---|
| Charge utile au démarrage | `0x43000000` (`0x46700000` avec Model-TG) | idem |
| Disposition des tables, détours, descripteurs (`gs.LAYOUT`) | `+0x33000..0x36000` | idem |
| Crochet de démarrage | masque `0x4016cae8`, appelé à `0x400004b2` (ou par le `jsr` de `0x40000530` avec Model-TG) | idem |
| 1ʳᵉ machine ajoutée | 6 (7 avec Model-TG) | idem |

Les poser l'une après l'autre ne marche donc pas : il faut une charge utile commune, une seule table des machines
ajoutées (N moteurs + 1) et un seul crochet.

## 2. Montage

`gen_macro_syntakt.py` appelle `gen_syntakt_engines.build_tweak(…, own=…)` : les machines « à nous » (`own`) viennent
après les moteurs, avec leurs propres `update`/`render` et leurs morceaux de charge utile.

- **Moteurs** : exactement à la place que leur donne leur tweak (`24-syntakt-….json`, `31-syntakt-tg-….json`). Leur
  passerelle (`tools/machines/syntakt_bridge/`, compilée par `m68k-elf-gcc` 16.2, régulateur en assembleur `gov_asm.py`)
  **n'est pas recompilée** : un autre GCC donnerait d'autres octets, et ceux-là ont été testés sur la machine. Ses
  octets sont repris du tweak versionné ; ses symboles aussi (champ `gov`, tables `update`/`render` des données), et
  vérifiés en réassemblant ses détours : ils doivent redonner les octets du tweak. Avec Model-TG, l'adresse de
  `voice_done` se lit en assemblant les détours avec une valeur bidon et en comparant les 4 octets qui changent.
- **MACRO** : son code (Braids et sa passerelle, `tools/machines/macro/`) est compilé comme pour `25-macro.json`
  (`m68k-linux-gnu-g++` 13.3) à `PAY + 0x42000`, ses variables (6 voix de Braids) à `PAY + 0x5a000` ; fin de la charge
  utile à `PAY + 0x732f0` (471 792 o). Avec Model-TG, tout reste sous `PAY_TG + 0x100000`, le dernier Mo de la zone
  d'échantillons que Model-TG nous laisse ([31 §4](31-model-tg.md)).
- **Tables, détours, descripteurs, bornes** : ceux de `gen_syntakt_engines.py` pour N + 1 machines (au plus
  `MAX_EXTRA` = 6 : 5 moteurs + MACRO). Le dispatch envoie MACRO à ses `update`/`render` ; ses potards, son icône (celle
  de TONE) et sa chaîne d'ampli sont ceux de [43 §2](43-machine-macro.md).
- **Régulateur de charge** : celui de la passerelle des moteurs ([36](36-regulateur-sans-coupures-inutiles.md)) passe
  par le détour de la boucle des voix, que MACRO emprunte aussi : les pistes MACRO y entrent comme les autres (quand la
  charge reste trop haute, la voix qu'on entend le moins s'éteint en fondu ; jamais le Sampler ni la piste que Model-TG
  enregistre ou édite). MACRO seule n'a toujours pas de régulateur ([43 §11](43-machine-macro.md)).

## 3. Place : charge utile compressée `[FAIT]`

Les moteurs rangent leur charge utile en clair (seuls) ou en morceaux non nuls (avec Model-TG, `PACK`) ; MACRO seule
en morceaux (103 552 o). Ensemble, en morceaux, il manque environ 80 Ko avec Model-TG sous `0x40200000`. Toute la charge
utile est donc rangée compressée (`append.compress = "aplib"`) :

- au build (`tools/build.py`, `docs/flasher/builder.js`) : `aplib_grow.pack` / `aplibPack`, le même compresseur glouton
  que pour la section agrandie ([17](17-portage-exact-syntakt.md)), sans l'en-tête de 8 o ; même flux en
  Python et dans la page (`tools/webbuild_check.sh`) ;
- au démarrage : le crochet (`stub.S`, `APLIB`) décompresse de la fin de l'image vers `PAY` (zéros compris : les
  variables de MACRO et du Syntakt n'ont plus à être remises à zéro), puis appelle son **2ᵉ étage** (`BOOT2`), rangé
  dans la charge utile entre la fin des moteurs et MACRO.

Le crochet entier (décompression, tables de CHORD, deux copies vers la SRAM) faisait 252 o ; le masque `0x4016cae8`
n'en laisse que 192 au crochet, l'arpégiateur ayant la suite (`gen_arp.py`, `.cave_menu` à `0x4016cba8`) :
`tools/ref_mainos.py` l'a trouvé (octets `old` de l'arpégiateur). D'où les deux étages : 174 o au masque (166 avec
Model-TG, qui finit par `jmp boot_extra_hook`), `gen_syntakt_engines.py` vérifie la limite (`STUB_END`). Le 2ᵉ étage
(`BOOT2`, 60 o environ) :

1. **recopie les tables d'ondes de CHORD** de la SRAM (`0x80001c5c`, 22 tables, et `0x8000cac0`, 8 tables), où l'OS
   vient de les mettre (`0x4000045c`), à leur place dans la charge utile (`chord_at`, [28](28-code-syntakt-en-sram.md)). Le
   tweak des moteurs les recopie au build depuis le MAIN OS de l'utilisateur (morceaux `cycles`) ; ici, les reprendre
   en SRAM évite de ranger 30 840 o peu compressibles dans l'image ;
2. **copie le code du Syntakt en SRAM**, puis les états de voix, comme le crochet des moteurs.

| | Seuls (`syntakt-<moteurs>-macro`) | Avec Model-TG (`syntakt-tg-<moteurs>-macro`) |
|---|---|---|
| Charge utile en mémoire | 471 792 o à `0x43000000` | 471 792 o à `0x46700000` |
| Dans l'image (compressée) | 229 095 o (SDVtg) à 240 671 o (les 5) | 229 367 o (SDVtg) à 240 948 o (les 5) |
| Fin de l'image décompressée (limite `0x40200000`) | `0x401e4d1f` au plus (marge 111 329 o) | `0x401fa5f4` au plus (marge 23 052 o) |
| Crochet au masque `0x4016cae8` (192 o au plus) | 174 o | 166 o |
| Décompression au démarrage (émulation, flux de 241 Ko) | ~4,4 millions d'instructions | idem |

La décompression ajoute au démarrage quelques dizaines de millisecondes `[HYP]` (4,4 millions d'instructions à
250 MHz), cachées par le chargement du projet ; à vérifier à l'oreille et à l'œil sur la machine.

## 4. Le flasher

- `tools/gen_flasher_tweaks.py` : la carte MACRO perd `excludes` et gagne `joins: "syntakt"` ; chaque combinaison de
  moteurs porte sa version avec MACRO (`combo.macro` : `id`, `tg`, `tested`, `tg_tested`, d'après `HW_TESTED` et
  `HW_TESTED_TG` de `gen_macro_syntakt.py`). Dans `app.js`, MACRO cochée avec les moteurs n'ajoute aucun tweak
  (`joinedTo`), les moteurs prennent `combo.macro` (`versionOf`), Model-TG prend toujours `model-tg-st`. Les badges
  suivent les essais de la combinaison avec MACRO ; la carte des moteurs dit « + MACRO » et que MACRO vient en dernier.
- **Valeurs partagées dans `tweaks.js`** : le code de MACRO (196 Ko en hexadécimal) est le même dans les 31 tweaks
  seuls, et dans les 31 avec Model-TG. `gen_flasher_tweaks.py` range une seule fois toute valeur d'au moins 2 Ko qui se
  répète (`shared`, `{"$shared": k}`) et `tweaks.js` les remet en place au chargement ; `read_js()` fait de même en
  Python (`tools/ref_mainos.py`) et vérifie qu'on retrouve les tweaks de `tweaks/` à l'identique. `tweaks.js` passe de
  3,5 Mo à 4,5 Mo au lieu de 18 Mo. Les JSON de `tweaks/` restent complets.
- `REF_MAINOS` : chaque combinaison de cartes avec MACRO et des moteurs a son empreinte (§6).

## 5. Incompatibilités

- **SD VINTAGE** hors du flasher (`sdvintage-*`, `syntakt-vintage`, `syntakt-meter`…) : même crochet, même charge
  utile, comme pour les moteurs seuls.
- Une version combinée ne va ni avec `macro`/`macro-tg`, ni avec les tweaks des moteurs seuls, ni avec une autre
  version combinée (`conflicts`) : le flasher n'en prend qu'une. Sans Model-TG, elle ne va pas avec `model-tg-st`.
- Avec les autres mods du flasher (6 canaux, arpégiateur, trig-hold, tempo, animation, drumkilla, écoute des samples
  `sample-preview-st` avec Model-TG, [46](46-ecoute-des-samples.md)) : les écritures communes sont identiques
  (redirections de sprites, envoi USB à heure fixe), aucune ne diffère.

## 6. Preuve en émulation `[FAIT en émulation]`

`tools/emu/test_macro_syntakt.py`, sur le vrai code de l'OS (Unicorn), avec la charge utile telle que le crochet la
décompresse. Références : les moteurs seuls (leur tweak) et MACRO seule (`25-macro`, `32-macro-tg`, elle-même identique
à Braids compilé pour l'ordinateur, [43 §7](43-machine-macro.md)).

| Vérification | Seuls | Avec Model-TG |
|---|---|---|
| (à compléter) | | |

## 7. À vérifier sur la machine

1. Flasher Model-TG + les 5 moteurs + MACRO (le pire cas pour la place) : démarrage normal, sans attente visible de
   plus. MACHINES : Sampler 7ᵉ, SDVtg … SYSwm, puis MACRO 13ᵉ, avec l'icône de TONE.
2. Chaque moteur sonne comme avant ; MACRO comme avant (SHAPE, COLOR, SWEEP, CONTOUR, DECAY/GATE/PUNCH) ; CHORD sonne
   juste (ses tables d'ondes sont reprises de la SRAM au démarrage).
3. Machine locks entre un moteur, MACRO et une machine d'origine sur une même piste.
4. Charge : deux ou trois pistes MACRO lourdes (WAVE MAP) avec des moteurs : le régulateur doit éteindre en fondu une
   voix plutôt que de laisser craquer le son.
5. Sans Model-TG, une petite combinaison (SDVtg + MACRO : MACRO 8ᵉ).
6. Avant de reflasher autre chose, remettre sur une machine d'origine les pistes qui utilisent une machine ajoutée.
