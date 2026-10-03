# 31 · Model-TG : intégration

Travail du 01/10/2026, à la demande de l'utilisateur : « Voici un autre projet que j'aimerais que tu intègres à notre projet : https://github.com/TinyGregAudio/Model-TG. Gère bien tout ce qui concerne la performance, l'optimisation, etc., pour l'intégrer au précédent ajout sans tout détruire. »

Décisions de l'utilisateur, après l'analyse du §3 :
- **Model-TG seul d'abord** dans le flasher, puis la version combinée avec les moteurs du Syntakt ;
- dans la version combinée, **le Sampler en 7ᵉ machine**, les moteurs du Syntakt ensuite (8ᵉ à 12ᵉ).

## 0. En bref

| | État |
|---|---|
| Model-TG seul dans le flasher web | `[FAIT]` tel que son propre build l'exporte, même empreinte (§2) |
| Model-TG avec l'audio USB 6 canaux | `[FAIT]` aucune écriture commune ; pas encore testé sur la machine (§2) |
| Conflits avec les moteurs du Syntakt | `[FAIT]` analysés (§3) |
| Version combinée Model-TG + moteurs du Syntakt | `[FAIT]` en ligne (1.6), démarre et joue sur la machine (firmware de diagnostic, §6) ; charge à optimiser (§7) |
| Passage à Model-TG v1.1.0 (slide trigs) | `[FAIT]` slides prouvés aussi sur nos moteurs en émulation ; fonctionne sur la machine (§9) |

## 1. Ce qu'est Model-TG

Source : dépôt [TinyGregAudio/Model-TG](https://github.com/TinyGregAudio/Model-TG), commit `454963b` (01/10/2026, sa `v1.0.0`), `README.md`, `docs/INTERNALS.md`, `docs/PAYLOAD.md` et `build.py`. Passage à sa `v1.1.0` : §9.

- **Ce qu'il ajoute** :
  - une machine **Sampler** (index 6, la 7ᵉ) à sept modes de lecture ;
  - le rééchantillonnage, une page de retrig avec 12 effets master ;
  - Attack, Filtre et Résonance sur les machines d'origine ;
  - Scale Lock, l'envoi d'échantillons par Elektron Transfer, une page System (charge processeur) ;
  - une charge processeur plus basse.
- **Licence MIT**. Aucun octet Elektron dans le dépôt : l'image se construit depuis l'OS de l'utilisateur, comme ici.
- **Comment il se pose dans l'OS** (`build.py`, `docs/INTERNALS.md`) :
  - un seul bloc de code de **80 592 o** en `0x401ab750`, exécuté **en place** ;
  - ce bloc occupe 5 des 16 blocs de 16 Ko du **cache du système de fichiers** (`0x401ab750..0x401eb750`), retirés au cache en réécrivant son initialisation (`0x400792f2`, `0x400792bc`) ;
  - **131 écritures** sur l'OS, toutes vérifiées sur les octets d'origine ;
  - son crochet de démarrage remplace l'appel de la remise à zéro du BSS (`jsr 0x400004b2` en `0x40000530`). Il règle aussi `ACR1` (cache en écriture immédiate pour `0x4C000000..0x4FFFFFFF`) et remet le BSS à zéro, sauf son bloc ;
  - il garde une **zone d'échantillons de 64 Mo** en `0x4a800000..0x4e800000` (la réserve du Model:Samples).
- **Ses optimisations** (`docs/INTERNALS.md`) :
  - pistes muettes non calculées ;
  - effets d'envoi sautés quand tout est silencieux (étage de sortie au repos : environ 24 → 13 %) ;
  - KICK et CHORD plus rapides, à l'identique ;
  - temps de chaque piste mesuré par un minuteur (`0xfc07800c`).
- **Prévu pour ce flasher** : `build.py --modded-cycles` exporte Model-TG au format de nos tweaks (`docs/PAYLOAD.md`). Le texte demande :
  - un ajout après l'OS sans fichier Syntakt ;
  - de le garder exclusif ;
  - d'afficher la provenance et la licence MIT.

## 2. Phase 1 : Model-TG seul dans le flasher `[FAIT]`

**Génération** : `tools/gen_model_tg.py`, depuis un clone du dépôt au commit épinglé.
- Il lance le `build.py` de Model-TG, relu au préalable : il n'appelle que l'assembleur, l'éditeur de liens, git et l'outil de dépaquetage, et n'écrit que dans son dossier `build/`.
  - On lui donne la section 3 dépaquetée par nos outils, et un outil de dépaquetage qui ne fait rien.
  - Ses écritures et son ajout sont repris tels quels. Seuls l'identifiant, le nom, la description et la liste des incompatibilités sont les nôtres.
- Résultat : `tweaks/model-cycles_OS1.13/30-model-tg.json` (131 écritures, 86 240 o ajoutés après l'OS), et sa licence `LICENSE-Model-TG`.
- **Notre constructeur redonne l'empreinte annoncée par son build** : MAIN OS `fb985a16…`. Le générateur le vérifie à chaque fois.

**Flasher web** :
- Une carte « Model-TG », par TinyGregAudio, avec un lien vers sa licence (servie à côté de la page) et ses crédits.
  - Rappel quand elle est cochée : n'installer un OS qu'avec l'identité CYC (Device Config > Transfer) ; les projets avec le Sampler ne jouent pas sur un autre firmware.
- **Exclusive** :
  - avec les trois tweaks de drumkilla, que Model-TG contient déjà (son mute verrouillé est modifié) ;
  - avec les moteurs du Syntakt : 12 écritures communes, §3.
  - Cocher l'une décoche l'autre.
- Un tweak « append » sans morceau du Syntakt ne demande plus le fichier Syntakt (`builder.js`, `build.py`).
- **Avec l'audio USB 6 canaux** : aucune écriture commune, donc la combinaison est proposée (MAIN OS `1511f84c…`).
  - Pas encore testée sur la machine.
  - En particulier, le rééchantillonnage de l'audio USB de l'ordinateur (mode A+M de Model-TG) n'a pas été essayé avec le mod 6 canaux.
- 513 combinaisons, `webflash_smoke.sh` ALL OK (621 vérifications, dont l'exclusivité et les deux combinaisons Model-TG). Build `2026-10-01-12`, version 1.5.

**Pas d'émulation de Model-TG pour l'instant** :
- Notre banc ne rejoue que la boucle des voix. Les voix de Model-TG y sortent presque muettes, parce que son code attend un état mis en place au démarrage et par l'interface.
- Son build est testé sur la machine par son auteur. Pour la phase 2, il faudra un banc qui reproduit cet état.

## 3. Conflits avec les moteurs du Syntakt

Source : comparaison des écritures (`30-model-tg.json` et nos tweaks `24-syntakt-*`), et lecture de `src/model_tg.s`, `src/phase1.s` et `build.py`.

**Écritures communes** : 12 endroits.

| Endroit | Model-TG | Nous |
|---|---|---|
| Bornes du nombre de machines (`0x400147a5`, `0x400148ab`, `0x400148b3`, `0x400a25e1`, `0x400a26e9`, `0x400a7df5`) | 5 → 6 | 5 → 5 + n |
| Recherche de descripteur (`0x4004df5c`, `0x4004df76`) | ses détours (Sampler) | nos détours (machines ajoutées) |
| LFO et Amp Decay par machine (`0x4005a6a6`, `0x4005a6b6`) | `sampler_lfo_gate`, `sampler_amp_gate` | nos bornes |
| Noms des machines (`0x400a2615`) | sa table de noms | notre table |
| Appel update/render de chaque piste (`0x400a7e02`) | `sampler_dispatch` | notre détour en `0x400a7dfe` |

**Autres conflits, sans octet commun** :
- **Démarrage** : son crochet remplace l'**appel** de `0x400004b2` ; le nôtre est **dans** `0x400004b2`, qui ne serait plus appelée. Notre charge utile ne serait jamais recopiée.
- **Tables update/render** : nous les déplaçons pour y ajouter nos machines ; son dispatch lit la table de render d'origine (`0x40118610`, 6 entrées) en dur.
- **Mémoire** :
  - les adresses `0x48000000..` sont une seconde vue, sans cache, des mêmes 128 Mo que `0x40000000..` (la sortie audio en `0x4a3ed080` correspond à `0x423ed080`) ;
  - sa zone d'échantillons correspond donc à `0x42800000..0x46800000`, **où se trouve notre charge utile** (`0x43000000..0x43042000`) : charger des échantillons l'écraserait.
- **Place sous la zone de travail du bootstrap** : après son bloc (`0x401bf220`), il reste **265 696 o** jusqu'à `0x40200000`. Notre charge utile à 5 moteurs fait **269 056 o**.
- **Pistes muettes** : son dispatch a sa propre logique (`voice_quiet`, `sil_note`). Elle juge une voix d'après l'état de voix du Cycles, que nos moteurs du Syntakt ne mettent pas à jour. Et notre régulateur ne verrait pas le Sampler.

**Ce qui est compatible** :
- Son CHORD optimisé (`chord_osc`) reçoit ses tables d'ondes par les pointeurs que nous redirigeons (`0x40118590`, [28](28-code-syntakt-en-sram.md)) : il suivra.
- Son Sampler calcule dans son propre tampon (`sampler_buf`), pas dans la zone de travail en SRAM que nous empruntons ([26](26-sram-empruntee.md)). Il ne touche pas aux zones de SRAM reprises aux tables de CHORD.
- Sa sonde de charge (vecteur de l'interruption audio, `0x4005966a`) et ses crochets de l'étage de sortie (`0x40059872`, `0x4005981e`) ne recouvrent pas les nôtres (`0x40059382`).
- Ses optimisations (effets au repos, KICK, CHORD) s'ajoutent aux nôtres.

## 4. Phase 2 : Model-TG + moteurs du Syntakt `[FAIT en émulation]`

Le plan du 01/10 (banc, mémoire, taille, démarrage, machines, boucle des voix, preuve) est suivi point par point. Rien n'est réécrit dans le code de Model-TG : nos détours passent devant les siens et lui rendent la main.

### 4.1 Deux tweaks, l'un sur l'autre

Source : `tools/gen_model_tg.py`, `tools/gen_syntakt_engines.py` (`--tg`), `tools/build.py`, `docs/flasher/builder.js`.

- **`30-model-tg-st.json`** : Model-TG construit par **son propre build**, depuis une copie de sa source avec **une seule retouche** (`ST_PATCHES`) :
  - `REGION_END = 0x4e800000` devient `0x4e700000` (`src/model_tg.s`) ;
  - sa zone d'échantillons perd 1 Mo (63 Mo au lieu de 64) ;
  - tout ce qu'il range au sommet de la zone (cordes de Pluck, noms des emplacements, historiques de retrig, tranches) est défini depuis `REGION_END` et descend avec : 52 octets de son bloc changent, ses 131 écritures non.
  - Le tweak garde aussi les adresses de 21 de ses symboles (`symbols`), lues dans son ELF, dont nos détours ont besoin.
- **`31-syntakt-tg-<moteurs>.json`** (31 combinaisons) : nos moteurs, appliqués **par-dessus** (`requires: model-tg-st`).
  - Leurs écritures sont vérifiées sur l'image après celles de Model-TG.
  - Leur ajout suit le sien dans l'image.
- **Constructeur** (Python et JS) :
  - tweaks appliqués dans l'ordre de leur champ `order` ;
  - plusieurs ajouts à la suite ;
  - `requires` vérifié ;
  - ajout **rangé en morceaux** (`pack`, ci-dessous) ;
  - refus d'une image qui finirait au-delà de `0x40200000`.
- Model-TG seul reste **exactement** son build officiel (`30-model-tg.json`, MAIN OS `fb985a16…`). Nos tweaks seuls ne changent pas d'un octet (`gen_syntakt_engines.py --all --check`).

### 4.2 Mémoire et taille

Source : `LAYOUT`/`set_base` et `segments` de `tools/gen_syntakt_engines.py` ; `machines/syntakt_bridge/stub.S`.

- **Adresse d'exécution** : `0x46700000` au lieu de `0x43000000` (`PAY_TG`). C'est le dernier Mo de la zone de Model-TG, vu par l'alias avec cache (`0x4e700000` sans cache), et Model-TG l'a vérifié intact sur la machine (§3).
  - Toutes nos adresses sont à un décalage fixe de cette base (`LAYOUT`).
  - Les 13 bits de poids faible ne changent pas : nos données tombent sur les mêmes lignes du cache de 8 Ko que dans la version seule.
- **Taille** : l'image n'enregistre que les morceaux non nuls de la charge utile (`pack`, réunion des `parts`) ; le reste est remis à zéro au démarrage.
  - 5 moteurs : 269 056 o en mémoire, **242 852 o** dans l'image.
  - L'image se termine en `0x401fa6d8`, sous `0x40200000`. Il reste environ 22 Ko.

### 4.3 Démarrage

Source : `stub.S` (`PACK`, `CHAIN_TO`) ; `phase1.s` de Model-TG (`boot_extra_hook`).

- Le `jsr` de `0x40000530`, où Model-TG appelle son `boot_extra_hook`, appelle **notre crochet**. Celui-ci :
  1. remet la zone `0x46700000..` à zéro ;
  2. y recopie les morceaux depuis l'image ;
  3. remplit les deux zones de SRAM (code et voix du Syntakt, [28](28-code-syntakt-en-sram.md), [29](29-voix-syntakt-en-sram.md)) ;
  4. saute à `boot_extra_hook`, qui règle `ACR1` et remet le BSS à zéro sauf son bloc.
- Il n'utilise que d0, d1, a0 et a1, et laisse la pile telle que le `jsr` l'a faite.

### 4.4 Machines et interface

Sources : `detours_asm`, `tg_records` et `build_tweak` de `tools/gen_syntakt_engines.py` ; dans `src/model_tg.s` de Model-TG : `descr_hook`, `descr_b_hook`, `sampler_lfo_gate`, `sampler_amp_gate`, `apply_names`, `mod_held`.

- **Numérotation** : le Sampler reste l'index 6 (7e machine), nos moteurs vont de 7 à 6 + n. Les bornes passent à 6 + n, y compris celles que Model-TG avait mises à 6.
- **Noms** : les 7 de Model-TG (son Sampler affiche le nom de l'échantillon, `mach_nbuf`), puis les nôtres.
- **Enregistrements par machine** (`0x4004df5c`, `0x4004df76`) :
  - nos machines ont les leurs ;
  - les autres passent par `descr_hook` et `descr_b_hook` ;
  - comme Model-TG, nos détours gardent a0 et a1.
- **Touche Attack** : tant que Model-TG la voit tenue (`mod_held`), les potards DECAY, SWEEP et CONTOUR de nos machines prennent Attack, Filtre et Résonance, comme sur les machines d'origine.
- **Libellés** : `apply_names` (Model-TG) renomme 4 paramètres sur la page du Sampler, dans la table d'origine `0x4010dce0`. L'OS lit notre copie agrandie (DESCN), donc nos détours recopient ces libellés à chaque recherche d'enregistrement.
- **Paramètres** (`paramIdFor`, `0x4005a692`) : nos détours `lfo_gate` et `amp_gate` passent devant ceux du Sampler. Nos machines suivent le chemin d'origine, avec nos rangées.
- **Constructeur des rangées** (`0x4005a274`) : il range les Amp Decay propres à chaque machine avec un compteur, dans l'ordre des descripteurs. Le détour `amp_row` saute la rangée 6 du Sampler, qui n'en a pas.
  - Trouvé par le test : sans lui, l'Amp Decay de chaque moteur tombait sur la machine précédente.
- **Icônes** :
  - écran MACHINES : l'icône du Sampler (index 6) pour la 7e machine, l'image choisie pour chacun des nôtres ;
  - les petites icônes bornées : celle de CHORD au-delà de 5, comme Model-TG (la version seule montre SNARE).

### 4.5 Boucle des voix et régulateur

Sources : `dispatch_tg_asm` de `tools/gen_syntakt_engines.py`, `voice_gate`/`voice_done` de `bridge_engines.c` ; `sampler_dispatch`, `amp_hook` (`ah_noenv`), `voice_quiet`, `prof_trk` de Model-TG.

- **Un seul détour** en `0x400a7dfe` :
  1. borne ;
  2. régulateur (`voice_gate`) ;
  3. puis selon la machine :
     - machines d'origine et Sampler : le dispatch de Model-TG, avec ses pistes muettes et sa mesure par piste ;
     - nos moteurs : la passerelle, puis la fin de son étage d'amplitude (`ah_noenv`). Ils reçoivent ainsi **Attack, Filtre/Résonance et le rééchantillonnage de la piste** de Model-TG, et leur temps s'affiche sur sa **page System**.
- **Fin commune** : toutes les pistes finissent en `0x400a7e24`. `tg_after` y appelle le régulateur (`voice_done`), puis refait les trois instructions remplacées.
- **Régulateur** :
  - notre arrêt des voix muettes ne vaut que pour nos moteurs : Model-TG a déjà le sien pour les machines d'origine et le Sampler ;
  - en surcharge, il éteint une voix d'origine ou un moteur du Syntakt ;
  - il n'éteint jamais le Sampler, ni la piste que Model-TG enregistre (`rs_src`) ou dont il édite les tranches (`sle_trk`), qui doivent garder le temps.

## 5. Preuve en émulation `[FAIT]`

Source : `tools/emu/test_model_tg_syntakt.py` (5 moteurs, SD + SWARM, et le firmware de diagnostic), avec `tools/emu/test_model_tg.py` (banc de Model-TG).

| Vérification | Résultat |
|---|---|
| Démarrage : notre crochet puis `boot_extra_hook`, pile et registres d2..d7/a2..a6 intacts | OK |
| Charge utile reconstituée octet par octet à `0x46700000`, SRAM remplie, le reste intact | OK |
| Rangées, recherches (slot, machine) et CC, machine d'un descripteur : 0..6 identiques à Model-TG seul | OK |
| Enregistrements (Sampler compris), touche Attack, libellés, noms, potards, changement de machine réel | OK |
| Son : 6 machines d'origine identiques à Model-TG seul (son build officiel) | identiques |
| Son : Sampler sans échantillon | muet, le reste identique |
| Son : chacun des 5 moteurs du Syntakt, en 8e à 12e machine | identique, échantillon par échantillon, à nos moteurs seuls |
| Son : 6 pistes ensemble (KICK, SD, Sampler, CHORD, SWARM, CP) | chaque piste identique à sa référence |
| Régulateur en surcharge (97 %) | voix éteintes, jamais le Sampler ni la piste dont Model-TG édite les tranches (même règle que pour la piste qu'il enregistre, dont la capture n'est pas émulée) |

Les tests de la version seule (moteurs, régulateur, compteur, SRAM, démarrage) et de Model-TG seul passent toujours.

## 6. Essai sur la machine `[FAIT]`

Retour de l'utilisateur le 01/10/2026, firmware de diagnostic sans l'audio 6 canaux (`91-syntakt-tg-meter.json`, construit par `build.py`, pas encore par le flasher) :

- **Démarrage et machines** : l'OS démarre ; le Sampler et les moteurs du Syntakt apparaissent après Chord.
- **Sampler** : un échantillon envoyé par Elektron Transfer (identité SMP) se charge par le navigateur de presets (FUNC + MACHINE) et joue.
- **Touche Attack** : le « PRESET » du guide de Model-TG est la touche **MACHINE**, tenue sans FUNC. Source : `src/model_tg.s`, codes de touches mesurés par son auteur (`KEY_PRESET = 5`). Elle donne Attack, Filtre et Résonance sur toutes les machines, moteurs du Syntakt compris.
- **Motif de 6 pistes** (SD Vintage x 2, SY Toy, Perc/Metal d'origine, Sampler, Tone d'origine) :

| Mesure | Valeur |
|---|---|
| Notre compteur (fonction audio `0x4005979e`), pic/moyenne | 93 / 79 % |
| Page System de Model-TG (de l'entrée de l'interruption audio à la fin du mix), maintenant / au pire | 90 / 101 % |
| Part de chaque piste (System) | SD 8, SY Toy 6, SD 3, Perc 6, Sampler 8, Tone 6 % |
| À l'oreille | coupures ou craquements, très occasionnels |

**Lecture** :
- Les moteurs du Syntakt coûtent autant que les machines d'origine et que le Sampler. Les 6 voix font environ 37 % ; le reste de la fonction audio (mixage, effets d'envoi, effets master) en fait environ 40 %.
- La page System commence à l'entrée de l'interruption (`0x40058c5e`, `isr_prof` de Model-TG). Notre compteur ne mesure que la fonction audio, appelée plus tard dans cette interruption : il lit environ **11 points de moins**.
- Le seuil de pic de notre régulateur (93 %) correspond donc à environ 104 % du vrai temps : un bloc peut déborder avant qu'il réagisse. C'est la cause probable des craquements.

**Essai d'un firmware construit par le flasher** (02/10/2026, version 1.8) : Model-TG + les 5 moteurs, avec l'audio USB 6 canaux, « tout marche » (retour de l'utilisateur). Cette combinaison a été marquée « testée » dans le flasher (`HW_TESTED_TG` de `tools/gen_syntakt_engines.py`) ; les autres combinaisons avec Model-TG restaient « expérimentales ». Depuis le passage à Model-TG v1.1.0 (§9), le flasher ne construit plus ce firmware-là : l'étiquette est retirée en attendant un nouvel essai.

## 7. Optimisation `[FAIT]`

Demande de l'utilisateur, le 01/10/2026 : « J'aimerais quand même avoir un peu de marge pour éviter les dépassements du processeur […] on va essayer d'optimiser sans perdre de fonctions. »

**Notre intégration n'est pas la cause.** Modèle de cache des notes 27–28 (8 Ko d'instructions et 8 Ko de données, 1,54 cycle par instruction et 15 cycles par ligne lue ou écrite en SDRAM), boucle des voix émulée, 6 pistes qui jouent (SD, SY Toy, SD, PERC, TONE, KICK) :

| Firmware | Instructions par bloc | Lignes d'instructions lues | Coût estimé (% d'un bloc à 250 MHz) |
|---|---|---|---|
| Nos moteurs seuls | 45 484 | 112 | 43,6 |
| Avec Model-TG | 45 656 | 278 | 45,3 |

Model-TG autour de nos moteurs ajoute environ 1,7 point, surtout en défauts de cache d'instructions (son code des voix s'ajoute au nôtre). Le reste du temps est ailleurs : début de l'interruption, mixage, effets d'envoi.
- Model-TG estime le delay et la reverb à environ 12 % du processeur, même sans rien à traiter (commentaire de `fx_early` dans `src/model_tg.s`).

**Firmware de profilage** (`92-syntakt-tg-profile.json`, `gen_syntakt_engines.py --tg --meter --profile`) :
- Ce qu'il mesure, au minuteur de la page System de Model-TG (`0xfc07800c`), depuis l'entrée de l'interruption (son `prof_t0`) :
  - le début de la fonction audio ;
  - la boucle des voix, par une sonde autour du `jsr` de `0x4005981e` ;
  - l'étage de sortie (mix, effets d'envoi et master), par une sonde autour de `0x40059872`.
- Ce que montre l'écran MACHINES, en « pic/moyenne » :
  1. tout ;
  2. début de l'interruption ;
  3. fonction audio avant les voix ;
  4. boucle des voix ;
  5. entre les voix et la sortie ;
  6. sortie ;
  7. notre compteur habituel.
- Les sondes sont vérifiées en émulation :
  - retour, pile et registres intacts ;
  - parts calculées sur des blocs simulés ;
  - le reste du firmware passe `test_model_tg_syntakt.py`.

**Mesure sur la machine** : retour de l'utilisateur, firmware de profilage, même motif de 6 pistes, avec delay et reverb, « pic/moyenne » :

| Partie | % d'un bloc |
|---|---|
| Tout (depuis l'entrée de l'interruption) | 91 / 80 |
| Début de l'interruption, avant la fonction audio | 7 / 1 |
| Fonction audio avant les voix | 3 / 3 |
| Boucle des voix | 56 / 58 (lecture douteuse : une moyenne ne peut pas dépasser son pic ; la somme des parts donne plutôt environ 52) |
| Entre les voix et la sortie | 6 / 5 |
| Sortie (mix, delay, reverb, effets master) | 20 / 19 |
| Notre compteur habituel | 90 / 80 |

**Lecture** :
- Notre compteur voit presque tout : le début de l'interruption ne fait que 1 % en moyenne. L'écart avec la page System (90 %) vient de sa façon de compter, pas d'un temps qui nous échapperait.
- Le temps est dans le calcul du son : les voix (environ 52 %, dont 37 % pour les 6 voix elles-mêmes selon la page System) et la sortie (environ 20 %, dont environ 12 % pour le delay et la reverb).
- **Pics** : en émulation, la boucle des voix est la même à chaque bloc, trigs compris (44,7 %). Avec les caches vidés, elle passe de 45,5 à 50,1 %. Entre deux blocs, l'interface et le séquenceur prennent les 8 Ko de chaque cache. Le bloc suivant relit alors le code des machines d'origine (348 lignes), leurs états de voix (130 lignes) et notre passerelle (78 lignes). Le reste des pics vient du séquenceur (7 % au pire, 1 % en moyenne).

**Optimisations de la version combinée** (la version seule ne change pas d'un octet) :
- **Notre code le plus appelé en SRAM** : `update`, `voice_after`, `voice_gate`, `audio_end`, `govern`, `render` et les plus petites, environ 1,8 Ko. Elles vont dans la fin libre des deux zones de SRAM reprises à CHORD, que le crochet de démarrage remplit déjà (`SRAM_HOT`, `sram_sections`).
  - Résultat (modèle de cache) : la boucle des voix passe de 45,3 à 44,4 % d'un bloc, et de 50,1 à 49,2 % caches vidés. Sortie identique.
- **Crête du régulateur** : le OU des valeurs absolues, sans branchement, au lieu du maximum. Exacte pour le test du seuil, qui est une puissance de 2. Les pistes jamais éteintes (Sampler, pistes protégées) ne sont plus parcourues. Gain faible : GCC compilait déjà bien la boucle.
- **Arrêt des voix muettes** de nouveau pour les machines d'origine, comme sans Model-TG. Sous forte charge, une fin de note sous -66 dB s'arrête après 16 blocs, au lieu de -90 dB et 0,25 s avec Model-TG. Le Sampler reste exclu.
  - Vérifié en émulation (DECAY 20) : chaque voix est identique à Model-TG seul jusqu'à son arrêt, et repart comme lui au trig suivant.

**Ce qu'on ne peut pas gagner sans rien perdre** : le reste est le vrai calcul du son.
- Chaque moteur du Syntakt coûte environ 7 % d'un bloc par voix. Son code est celui du Syntakt et s'exécute déjà en SRAM.
- Une machine d'origine coûte environ 6 %, le Sampler 8 %, le delay et la reverb environ 12 %.
- Notre propre code ne pèse plus qu'environ 1,5 % de la boucle des voix.
- Pour plus de marge, il faudrait choisir :
  - couper plus tôt (régulateur plus strict) ;
  - ou jouer moins de voix lourdes à la fois.

## 8. Ce qui reste `[À FAIRE]`

- **Étiquette « testé » de Model-TG v1.1.0** (§9) : la version combinée fonctionne sur la machine (firmware de `build.py`, même MAIN OS). L'étiquette revient après l'essai d'un firmware construit par le flasher.

- **Optimiser sans perdre de fonctions** (demande de l'utilisateur) : mesurer d'abord où passent les ~50 % hors des voix (début de l'interruption, mixage et effets), puis viser les plus gros postes.
- **Régulateur** : mesurer depuis l'entrée de l'interruption, comme la page System, pour qu'il réagisse avant un débordement.
- Les autres combinaisons avec Model-TG restent « expérimentales » tant qu'elles n'ont pas été essayées sur la machine.
- **Projets** : une piste réglée sur une machine ajoutée n'a pas le même numéro dans les deux versions (8e machine = SDVtg avec Model-TG, 7e sans). Un projet fait avec l'une joue une autre machine sur l'autre. Le flasher le dit.
- Non essayé : le rééchantillonnage d'une piste d'un moteur du Syntakt.

## 9. Passage à Model-TG v1.1.0 `[FAIT]`

Demande de l'utilisateur, le 03/10/2026 : « TinyGregAudio a mis à jour son projet […] Quels sont les changements par rapport à la version que j'avais intégrée ? », puis « vas-y ».

Source : dépôt [TinyGregAudio/Model-TG](https://github.com/TinyGregAudio/Model-TG), étiquette `v1.1.0` (commit `70b39dd`, 02/10/2026). Il y a 9 commits depuis `454963b`, qui est sa `v1.0.0`, la version que nous avions intégrée. Fichiers lus : `README.md`, `docs/USER_GUIDE.md`, `docs/INTERNALS.md`, `docs/FLASHER.md`, `build.py` et `src/model_tg.s`.

**Ce qui change chez lui** :
- **Les slide trigs**, seule nouveauté musicale (`docs/USER_GUIDE.md`, « Slide trigs ») :
  - SETTINGS maintenu + une touche de pas fait du pas un slide trig, ou le remet en trig normal. Sur un pas vide, la combinaison pose directement un slide trig. Les slide trigs clignotent deux fois sur les touches de pas.
  - Chaque paramètre continu qui diffère entre le trig précédent et le slide trig glisse pendant tout l'intervalle. La valeur est celle du p-lock, ou celle du son.
  - Ne glissent pas : la machine, le Gate, ni le multiplicateur, la destination, la forme et le mode de trig du LFO.
  - La marque est le bit 12 des drapeaux du pas, que l'OS n'utilise pas : elle est sauvée avec le pattern et copiée avec le pas.
- **Son propre flasher web** (https://tinygregaudio.github.io/Model-TG/), qui construit Model-TG seul. Son `docs/BUILD.md` cite toujours le nôtre comme autre possibilité.
- **Build** :
  - même image quelle que soit la version des binutils : ses lectures de symboles `.globl` sont écrites en relatif au PC ;
  - bloc de code de 82 282 o, sur 6 blocs du cache au lieu de 5 ; `reserved_end` passe de `0x401bf220` à `0x401bf8c0` ;
  - zone d'échantillons réduite de 2 Ko (`PCM_TOP = SLD_BASE`).
- **4 nouveaux points d'accroche dans l'OS** (`build.py`) :
  - remise à zéro d'un pas, `0x400169f0` → `sld_reset` ;
  - dessin des lumières des pas, `0x40021f56` → `sld_led` ;
  - les deux appels du constructeur de trigs, `0x400551a6` et `0x40055bfa` → `sld_seq`, qui arme le glissement ;
  - en plus, `sld_apply`, appelé en tête de `sampler_pre` (accroché en `0x400a7da8` comme avant), réécrit à chaque bloc les paramètres lissés de la piste.

**Effet sur notre intégration** :
- Aucun de nos tweaks n'écrit sur ces 4 adresses (vérifié sur tous les fichiers de `tweaks/model-cycles_OS1.13/`).
- Le format d'export n'a pas changé (`docs/PAYLOAD.md`). `MODEL_TG_COMMIT` passe à `70b39dd`, puis tout est régénéré :
  - `30-model-tg.json` : 136 écritures, 87 936 o ajoutés. **MAIN OS `a049d724…`**, l'empreinte que son auteur annonce pour la v1.1.0 (commit `a140e7e`, `flasher/model-tg.json`).
  - `30-model-tg-st.json` : notre seule retouche (`REGION_END`) s'applique toujours. L'état des slides (`SLD_BASE`) est défini depuis `REGION_END` et descend avec lui. Ses symboles exportés comprennent maintenant `SLD_BASE`, `sld_init` et `blk_clk`, pour nos tests.
  - Les 31 fichiers `31-syntakt-tg-….json` et les firmwares de diagnostic 91 et 92 : seules changent les adresses de Model-TG (ses symboles, la fin de son bloc). Notre charge utile ne bouge pas, et l'image se termine toujours sous `0x40200000`.
- **Nos moteurs du Syntakt glissent aussi.** Leur passerelle lit les mêmes paramètres lissés que les machines d'origine (le `a2` de la boucle des voix, `update` de `bridge_engines.c`). `sld_apply` les réécrit avant notre aiguillage (`0x400a7dfe`).

**Preuve en émulation** :
- `test_model_tg.py` (Model-TG seul) passe, ainsi que `test_model_tg_syntakt.py` : 5 moteurs (34 vérifications), SD + SWARM (28) et le firmware de diagnostic 91 (34).
- Nouvelle partie 5 de `test_model_tg_syntakt.py` : un glissement armé comme le fait `sld_seq`, sur Pitch, Color et Amp Decay, pendant 200 blocs.
  - Les mots écrits suivent la formule de `sld_apply`.
  - Le rendu est identique, échantillon par échantillon, à celui où le banc écrit lui-même la même rampe, et différent sans glissement.
  - Vérifié sur TONE (Model-TG seul, puis version combinée) et sur chacun des 5 moteurs du Syntakt.
  - Le séquenceur (`sld_seq`) n'est pas émulé.
- Flasher web : `webflash_smoke.sh` ALL OK (671 vérifications), avec les nouvelles empreintes des 575 combinaisons. Sa vérification des étiquettes suit maintenant `tg_tested`.
- Firmware d'essai (`build.py -t 6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm`) : MAIN OS `0a3c035e…`, la même empreinte que dans le flasher.

**Charge** : boucle des voix émulée, motif de 6 pistes du §6 (SD Vintage x 2, SY Toy, PERC, Sampler sans échantillon, TONE), instructions par bloc. Conversion : 1,54 cycle par instruction, 166 667 cycles par bloc.

| Firmware | Instructions par bloc | Écart | Environ, en % d'un bloc |
|---|---|---|---|
| v1.0.0 | 43 558 | | |
| v1.1.0, avant le premier Play (`sld_init` à 0) | 43 582 | +24 | +0,02 |
| v1.1.0, en lecture, sans slide | 43 726 | +168 | +0,16 |
| v1.1.0, les 6 pistes qui glissent sur leurs 19 paramètres | 45 526 | +1 968 | +1,8 |

- Au repos : environ 28 instructions par voix et par bloc.
- Côté séquenceur (non émulé, lecture du code) : à chaque trig qui part, `sld_seq` cherche le trig suivant de la piste, à environ 9 instructions par pas parcouru (63 pas au pire). Si c'est un slide trig, il lit les 26 paramètres des deux pas. Pire cas estimé : environ 1 300 instructions (environ 1,2 % d'un bloc) par piste, au seul pas qui arme le glissement.

**Essai sur la machine** (03/10/2026) : firmware d'essai Model-TG v1.1.0 + les 5 moteurs + l'audio 6 canaux, construit par `build.py` (MAIN OS `0a3c035e…`, la même empreinte que le flasher). Il était demandé de vérifier le démarrage, les moteurs et le Sampler, et un slide trig sur une piste d'un moteur du Syntakt. Retour de l'utilisateur : « c bon ça marche ».

**Étiquette « testé »** : retirée de la version combinée (`HW_TESTED_TG` vide), car le firmware que construit le flasher n'est plus celui essayé le 02/10/2026. L'essai du 03/10/2026 a été fait sur un firmware construit par `build.py` (même MAIN OS). L'étiquette revient après l'essai d'un firmware construit par le flasher.
