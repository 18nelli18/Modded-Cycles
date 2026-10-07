# 49 — Vérifier le flasher mod par mod, pas combinaison par combinaison

Question de Maxime, le 07/10/2026, dans le fil du projet sur le guide « comment fonctionne un mod » : « à chaque fois
que j'ajoute un mod, je génère toutes les combinaisons d'OS disponibles ? Ce n'est pas juste un bloc ajouté ou
retiré ? J'aimerais que tous ces mods soient modulaires, et que les gens puissent par la suite mettre leur mod
personnalisé en plus de ceux existants. » La réponse et un chemin en quatre étapes vers des mods modulaires et des
mods perso ont été rédigés pour lui dans le fil ; cette note est l'**étape 1** : la vérification du flasher ne double
plus à chaque mod. Outils : `tools/check_overlaps.py` (nouveau), `tools/ref_mainos.py` (réécrit),
`docs/flasher/builder.js`, `docs/flasher/app.js`, `tools/webflash_smoke.js`. Aucun octet de firmware ne change.

## Réponse courte

- **Aucun firmware n'est stocké** : la page construit le firmware dans le navigateur, depuis le fichier officiel de
  l'utilisateur, en appliquant les mods cochés. Ce qui doublait à chaque mod, c'était la **vérification** :
  `REF_MAINOS` listait l'empreinte du MAIN OS de chacune des 9 215 combinaisons proposées (90 % des 1,36 Mo de
  `app.js`), et `tools/webflash_smoke.sh` les reconstruisait toutes dans la page (de 45 min à 1 h 40 en morceaux, faute
  de mémoire sinon). [FAIT]
- Elle est remplacée par trois choses :
  1. `tools/check_overlaps.py`, **sans firmware** : deux mods qu'on peut installer ensemble n'écrivent jamais aux mêmes
     octets (sauf écriture identique ou mod posé par-dessus l'autre), et leurs charges utiles s'enchaînent ;
  2. `REF_MODS` : l'empreinte des écritures et de la charge utile de **chaque tweak**, vérifiée par la page **à chaque
     build** ;
  3. `REF_MAINOS` réduit à un **échantillon de 416 combinaisons** construites en entier : chaque carte seule, chaque
     paire, les plus grandes.
- Les firmwares sont les mêmes octet pour octet : les 416 empreintes sont celles de l'ancienne liste, et les 9 215
  combinaisons, reconstruites dans la page avec le nouveau code, donnent le même MAIN OS qu'avant, chaque mod vérifié
  (§6). [FAIT]
- La liste grandit maintenant d'une quarantaine d'entrées par carte au lieu de doubler, et `app.js` passe de
  1 364 561 à 188 803 octets (`main` 1.28, avec le sélecteur de mods).

## 1. Ce qui grandissait

Chaque carte indépendante double le nombre de combinaisons ; les moteurs du Syntakt (31 combinaisons de moteurs, avec
ou sans Model-TG) multiplient le tout. Mesuré le 07/10/2026 sur `main` et les PR ouvertes (bloc `REF_MAINOS`, taille de
`app.js`) [FAIT] :

| Où | Combinaisons | `app.js` |
|---|---:|---:|
| `main` (1.28) | 9 215 | 1 364 561 o |
| PR clavier d'accords (#50), filtre par piste (#55) | 17 407 | 2,5 Mo |
| PR menu multiligne (#52) | 18 431 | 2,7 Mo |
| PR mods de djd_oz (#53, deux cartes) | 36 863 | 5,6 Mo |
| toutes les PR ouvertes fusionnées | ≈ 300 000 [HYP, calcul] | ≈ 50 Mo [HYP] |

`REF_MAINOS` n'était pas un verrou : une combinaison absente de la liste se construisait et s'envoyait quand même, sans
la mention « Conforme au build de référence » (`prepareFirmware` de `app.js`) ; `docs/AGENTS.md` et `FLASH.md`
disaient le contraire, corrigés ici. Aucune note ni aucun commit ne rapporte un bug que seul ce test exhaustif aurait
trouvé : les échecs enregistrés sont des manques de mémoire du conteneur ; les chevauchements entre mods ont été vus
par les générateurs, le registre des pochoirs ou des comparaisons à la main (le 07/10/2026, chord-keys contre
level-pan-values, avant 02cd68d). [FAIT]

## 2. Pourquoi un échantillon suffit

Le MAIN OS d'une combinaison, c'est l'OS d'origine, plus les écritures de chaque mod coché, appliquées dans l'ordre des
tweaks, plus les charges utiles ajoutées l'une après l'autre (`tools/build.py`, `builder.js`). Ce que l'ancienne liste
prouvait, c'est que la page (`builder.js`) et l'outil Python donnent le même résultat pour chaque combinaison.
Découpé :

1. **Chaque mod** : les octets que la page lit dans `tweaks.js` (écritures, charge utile construite depuis le fichier de
   l'utilisateur) sont ceux de Python. C'est `REF_MODS`, vérifié à chaque build, quelle que soit la combinaison.
2. **L'assemblage** : si deux mods installables ensemble n'écrivent jamais aux mêmes octets, l'ordre ne compte pas et
   chaque octet changé vient d'un seul mod. Les seuls cas où deux mods touchent les mêmes octets sont prévus par les
   deux builders : la même écriture entière (un pochoir libéré par les deux, écrite une fois) et un mod posé sur un
   autre par `requires` (les moteurs de la version combinée sur `model-tg-st`, notes/31). C'est
   `tools/check_overlaps.py`, pour toutes les combinaisons que `build.py` accepte (pas seulement celles de la page).
3. **Le code d'assemblage lui-même** (ordre, écriture partagée, chaîne `requires`, charges utiles enchaînées, contrôle
   des zones 0xFF) est le même pour toutes les combinaisons ; l'échantillon l'exerce : chaque carte seule, chaque paire
   (toutes les interactions à deux), et les plus grandes (tout ce qui va ensemble, coché ensemble).

Limites :
- Un refus du contrôle des zones 0xFF qui n'apparaîtrait qu'avec trois mods ou plus (une référence de l'OS réécrite
  par un mod vers une zone qu'un troisième remplit) se verrait comme un **build refusé** dans la page, jamais comme un
  firmware faux. Aucun cas connu. [HYP]
- Les incompatibilités sans octet commun (un crochet qui n'a qu'un propriétaire, une zone de mémoire partagée à
  l'exécution, un réglage enregistré au même endroit du pattern) restent à déclarer à la main dans `conflicts` :
  `check_overlaps.py` ne voit que les octets écrits dans l'image et la mémoire où tournent les charges utiles.
- L'échantillon prouve « page = Python ». Que le firmware marche reste l'affaire des preuves en émulation et des essais
  de Maxime, comme avant.

## 3. `tools/check_overlaps.py`

Lit les JSON de `tweaks/` (ou de branches, `--git REF`, réunies), sans firmware, et vérifie :

- chaque écriture : `old` et `new` en hexadécimal sans espace, non vides, de même longueur, dans la section 3
  (`section_len` de `device.json`) ; des ids uniques ; chaque `requires` existe (un `conflicts` vers un tweak absent,
  d'une autre branche, est seulement signalé) ;
- les chevauchements : pour chaque paire de tweaks installables ensemble (aucun conflit entre eux ni entre ce qu'ils
  demandent par `requires`), toute écriture commune doit être la même écriture entière ou une chaîne `requires` ;
- les charges utiles (`append`) de chaque ensemble installable : chacune commence là où finit la précédente (`at`),
  l'ensemble finit sous `0x40200000`, et leurs zones d'exécution (`dest`) ne se chevauchent pas.

Avec plusieurs `--git`, un même id aux mêmes écritures sur deux branches n'en fait qu'un (leurs `conflicts` et
`requires` réunis) ; deux versions différentes deviennent deux tweaks incompatibles.

Résultats du 07/10/2026 [FAIT] :

| Où | Résultat |
|---|---|
| `main` | 80 tweaks, 8 472 écritures, 705 cas prévus, 70 ensembles de charges utiles : aucun problème |
| chacune des 7 PR de mods ouvertes, seule | aucun problème (deux tweaks de #56 et #59 nomment `chord-keys`, absent de leur branche) |
| `main` + les 7 PR ensemble | 91 tweaks, 8 871 écritures : aucun problème |
| djd_oz avant 02cd68d + clavier d'accords | **3 chevauchements** : `level-pan-values` (deux zones) et `trigless-dim` sur les pochoirs de `chord-keys` |

La dernière ligne rejoue le conflit de pochoirs trouvé à la main le 07/10/2026 : l'outil le voit. Durée : 0,5 s.

## 4. `REF_MODS` et `REF_MAINOS` (`tools/ref_mainos.py`)

- `REF_MODS[id] = { w, p }` pour chacun des 72 tweaks de `tweaks.js` : `w` = SHA-256 des écritures mises bout à bout
  (pour chacune : `off` sur 4 octets, longueur de `old` sur 4 octets, `old`, longueur de `new` sur 4 octets, `new` ;
  `writes_bytes()` en Python, `writesBytes()` dans `builder.js`) ; `p` = SHA-256 de la charge utile telle qu'elle va
  dans l'image (`payload_image(payload_runtime(…))`), pour les tweaks `append`, depuis les fichiers officiels.
- `REF_MAINOS` : le MAIN OS, construit en entier comme `build.py` (`check_conflicts`, `apply_writes`, `check_caves`,
  `build_payload`), de :
  - chaque carte seule, chaque variante, chaque combinaison de moteurs du Syntakt : 40 ;
  - chaque paire de cartes que la page laisse cocher ensemble : 312 ;
  - les plus grandes : à partir de chaque carte, on coche toutes les autres qui vont avec, dans l'ordre des cartes puis
    à l'envers, avec et sans les moteurs du Syntakt : 64.
  Total 416, en 2 minutes. Les règles des cartes sont lues comme dans `app.js` : `excludes` et `includes` (jamais
  ensemble), `with` (un autre tweak quand une autre carte est cochée), Model-TG avec les moteurs (leur version `tg`).
  Le `requires` d'une carte n'est qu'affiché par la page depuis le sélecteur de mods (1.28, « avec … ») : il ajoute
  l'autre carte à l'échantillon, et une sélection dont un tweak n'a pas le tweak qu'il demande est écartée (les deux
  builds la refusent). Les PR ouvertes avaient dû adapter l'ancien script à chaque nouvelle
  forme de carte ; celui-ci les lit toutes.
- Croissance : la k-ième nouvelle carte ajoute 1 entrée seule, une paire avec chaque autre carte et chaque combinaison
  de moteurs (≈ 9 + 31), et quelques grandes : une quarantaine, au lieu de doubler. [FAIT pour main, calcul ensuite]

## 5. La page

- `builder.js` : `build(…, { refMods })` compare l'empreinte des écritures de chaque tweak choisi et de chaque charge
  utile construite ; un écart refuse le build (« écritures différentes de la référence », « charge utile différente
  de la référence »). `modsChecked` dit que chaque tweak avait son empreinte et qu'elle correspond.
- `app.js` : une combinaison de l'échantillon affiche « Conforme au build de référence » (MAIN OS entier, comme
  avant) ; les autres « Chaque mod est conforme à son build de référence ». Version 1.30, tampon `2026-10-07-06`.
- Les deux builders refusent maintenant de la même façon un hexadécimal mal formé (`fromHex` lisait un caractère
  invalide comme 0x00, `bytes.fromhex` acceptait des espaces) et une écriture hors de la section 3 (Python lisait un
  `off` négatif depuis la fin). Aucun tweak du dépôt n'était concerné ; c'est en vue des mods perso (étape 3).

## 6. Preuves

| Vérification | Résultat |
|---|---|
| les 416 clés de l'échantillon dans l'ancienne liste, même empreinte | 416 / 416 [FAIT] |
| les 9 215 combinaisons de l'ancienne liste, reconstruites dans la page (jsdom) avec le nouveau `builder.js`/`app.js` : même MAIN OS qu'avant, chaque mod vérifié | ÉQUIV [FAIT] |
| `tools/webflash_smoke.sh` avec les fichiers officiels : les 416 combinaisons, une combinaison de trois cartes hors échantillon (construite, chaque mod vérifié), un mod falsifié (écritures, puis charge utile) refusé | SMOKE [FAIT] |
| `gen_flasher_tweaks.py --check`, `webbuild_check.sh`, `webflash_check.sh`, `py_compile` | OK [FAIT] |

## 7. Pour la suite

- Les PR ouvertes, après fusion de `main` : régénérer `tweaks.js`, puis `REF_MAINOS`/`REF_MODS` avec le nouveau
  `ref_mainos.py` (leurs retouches de l'ancien script ne servent plus), et lancer `check_overlaps.py`.
- Étape 2 : un registre de la place libre et des points d'accroche, tiré des tweaks eux-mêmes, que `check_overlaps.py`
  vérifierait aussi (zones réservées, crochets à un seul propriétaire, octets de pattern).
- Étapes 3 et 4 (mods perso dans le flasher, page qui place le code elle-même) : décisions de Maxime sur les règles 5
  et 6 d'`AGENTS.md`, la licence et la forme d'un catalogue.
