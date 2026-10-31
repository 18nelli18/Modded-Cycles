# Registre de la place libre et des points d'accroche — Model:Cycles OS 1.13

Généré par `tools/registry.py` à partir des tweaks de ce dossier (notes/52) : ne pas éditer à la main. `python3 tools/registry.py` le régénère, `--check` vérifie qu'il est à jour, `--git <branche>` y ajoute à l'écran les mods d'autres branches, `--cycles <OS officiel>` vérifie le relevé des masques sur l'image.

Adresses : VA de l'OS 1.13 (la section 3 commence en `0x40000400`). Un mod qui veut de la place prend un masque marqué *libre* au §1 (`sprites.redirect_write`, voir `tools/AGENTS.md`), régénère ce fichier et le commet avec son tweak. `tools/check_overlaps.py` refuse deux mods installables ensemble aux mêmes octets ; ce registre refuse une écriture dans un masque dont le sprite n'est pas redirigé.

## En bref

- 285 tweaks, 32 057 écritures.
- Masques de sprites libérables : 164 (35 960 o), dont 88 pris (25 544 o) et **76 libres (10 416 o)**.
- Crochets sur l'OS : 123 adresses détournées, dont 62 à l'identique par des mods de familles différentes.
- Pointeurs réécrits : 58 adresses. Écritures dans des octets 0xFF hors masques : 15 zones.
- Charges utiles ajoutées après l'OS : 263 tweaks ; place restante au §3.

## 1. Masques de sprites libérés

Les masques d'un groupe sont identiques octet pour octet et chacun n'est désigné que par la constante 32 bits de son constructeur (notes/14 §5, notes/32 §11, notes/52). Faire pointer cette constante sur la copie gardée libère le masque : le rendu ne change pas et l'OS, chargé en SDRAM, n'y lit plus rien. Règles : un mod qui écrit dans un masque le redirige dans le même tweak (ou dans un tweak qu'il demande) ; personne n'écrit dans une copie gardée ; deux mods ne partagent un masque que s'ils ne s'installent jamais ensemble, ou l'un par-dessus l'autre.

### 47×47 : 21 masques de 376 o (copie gardée `0x40172220`) : 21 pris, 0 libres (0 o)

| masque | constante | état | mods (octets écrits) |
|---|---|---|---|
| `0x4016b6f8` | `0x400b133e` | pris (348/376 o) | mod-settings (348 o) |
| `0x4016b9e8` | `0x400b131c` | pris (304/376 o) | mod-settings (304 o) |
| `0x40171f30` | `0x400b05a0` | pris (348/376 o) | mod-settings (348 o) |
| `0x40172608` | `0x400b0544` | pris (268/376 o) | mod-settings (268 o) |
| `0x40179730` | `0x400af64a` | pris (176/376 o) | mod-settings (176 o) |
| `0x40182b38` | `0x400adfda` | pris (370/376 o) | step-rec (370 o) |
| `0x40182e28` | `0x400adfba` | pris (372/376 o) | step-rec (372 o) |
| `0x40183118` | `0x400adf9e` | pris (292/376 o) | sample-preview (292 o), sample-preview-st (292 o) |
| `0x40185018` | `0x400adba8` | pris (300/376 o) | sample-preview (300 o), sample-preview-st (300 o) |
| `0x40185968` | `0x400ada00` | pris (332/376 o) | sample-preview (332 o), sample-preview-st (332 o) |
| `0x40185c58` | `0x400ad9e0` | pris (312/376 o) | sample-preview (312 o), sample-preview-st (312 o) |
| `0x40189930` | `0x400ad328` | pris (354/376 o) | arp (354 o) |
| `0x4018a220` | `0x400ad202` | pris (359/376 o) | arp (359 o) |
| `0x4018cd48` | `0x400acdb2` | pris (346/376 o) | step-rec (346 o) |
| `0x4018d1b8` | `0x400acd76` | pris (370/376 o) | step-rec (370 o) |
| `0x4018d4a8` | `0x400acd56` | pris (358/376 o) | step-rec (358 o) |
| `0x4018dba8` | `0x400accfe` | pris (114/376 o) | trigless-dim (114 o) |
| `0x4018f4b4` | `0x400ac8d0` | pris (360/376 o) | level-pan-values (360 o) |
| `0x4018fc74` | `0x400ac81c` | pris (364/376 o) | level-pan-values (364 o) |
| `0x401904b4` | `0x400ac784` | pris (370/376 o) | multiline-browser (370 o) |
| `0x40192734` | `0x400ac2b2` | pris (318/376 o) | trigless-dim (318 o) |

### 48×22 : 42 masques de 192 o (copie gardée `0x4014b364`) : 33 pris, 9 libres (1 728 o)

| masque | constante | état | mods (octets écrits) |
|---|---|---|---|
| `0x40152d38` | `0x400b9726` | pris (36/192 o) | multiline-browser (36 o) |
| `0x401592bc` | `0x400b7404` | pris (188/192 o) | model-tg (188 o), model-tg-st (188 o) |
| `0x4015943c` | `0x400b73e4` | pris (186/192 o) | model-tg (186 o), model-tg-st (186 o) |
| `0x4015f38c` | `0x400b504a` | pris (124/192 o) | model-tg (124 o), model-tg-st (124 o) |
| `0x40165fec` | `0x400b28b4` | pris (180/192 o) | model-tg (180 o), model-tg-st (180 o) |
| `0x40168a84` | `0x400b1bc0` | pris (58/192 o) | model-tg (58 o), model-tg-st (58 o) |
| `0x40168da4` | `0x400b1b32` | pris (168/192 o) | model-tg (168 o), model-tg-st (168 o) |
| `0x4016bcd8` | `0x400b12fe` | pris (190/192 o) | model-tg (190 o), model-tg-st (190 o) |
| `0x4016dab8` | `0x400b0f78` | pris (154/192 o) | model-tg (154 o), model-tg-st (154 o) |
| `0x4016fae8` | `0x400b0b20` | pris (160/192 o) | model-tg (160 o), model-tg-st (160 o) |
| `0x40170c48` | `0x400b08da` | pris (132/192 o) | model-tg (132 o), model-tg-st (132 o) |
| `0x40171a48` | `0x400b06ec` | pris (76/192 o) | model-tg (76 o), model-tg-st (76 o) |
| `0x40172a68` | `0x400b0508` | pris (158/192 o) | model-tg (158 o), model-tg-st (158 o) |
| `0x40172be8` | `0x400b04ec` | pris (111/192 o) | model-tg (111 o), model-tg-st (111 o) |
| `0x401736c8` | `0x400b036c` | libre | |
| `0x40177f28` | `0x400af962` | libre | |
| `0x40178708` | `0x400af812` | libre | |
| `0x40178fc0` | `0x400af6e2` | libre | |
| `0x401792b0` | `0x400af6a6` | libre | |
| `0x40179430` | `0x400af686` | libre | |
| `0x401795b0` | `0x400af66a` | libre | |
| `0x40179b18` | `0x400af60e` | libre | |
| `0x4017c97c` | `0x400aee4e` | libre | |
| `0x401829b8` | `0x400adff6` | pris (92/192 o) | tempo-sync (92 o) |
| `0x40183408` | `0x400adf7e` | pris (186/192 o) | tempo-sync (186 o) |
| `0x40184808` | `0x400adc40` | pris (190/192 o) | tempo-sync (190 o) |
| `0x40184af8` | `0x400adc04` | pris (112/192 o) | tempo-sync (112 o) |
| `0x40184c78` | `0x400adbe4` | pris (112/192 o) | tempo-sync (112 o) |
| `0x40187528` | `0x400ad742` | pris (190/192 o) | mod-settings (190 o) |
| `0x401876a8` | `0x400ad726` | pris (161/192 o) | mod-settings (161 o) |
| `0x40188f98` | `0x400ad3a0` | pris (104/192 o) | mod-settings (104 o) |
| `0x4018a608` | `0x400ad1c6` | pris (166/192 o) | step-rec (166 o) |
| `0x4018b9c8` | `0x400ad048` | pris (114/192 o) | tempo-sync (114 o) |
| `0x4018bb48` | `0x400ad028` | pris (117/192 o) | tempo-sync (117 o) |
| `0x4018cbc8` | `0x400acdce` | pris (plein) | tempo-sync (192 o) |
| `0x4018d038` | `0x400acd92` | pris (plein) | tempo-sync (192 o) |
| `0x4018d798` | `0x400acd3a` | pris (152/192 o) | step-rec (152 o) |
| `0x4018f80c` | `0x400ac894` | pris (128/192 o) | step-rec (128 o) |
| `0x40190184` | `0x400ac7e0` | pris (100/192 o) | step-rec (100 o) |
| `0x40190334` | `0x400ac7a4` | pris (126/192 o) | tempo-sync (126 o) |
| `0x4019089c` | `0x400ac748` | pris (168/192 o) | tempo-sync (168 o) |
| `0x40192a24` | `0x400ac292` | pris (177/192 o) | tempo-sync (177 o) |

### 35×35 : 19 masques de 280 o (copie gardée `0x4014a660`) : 15 pris, 4 libres (1 120 o)

| masque | constante | état | mods (octets écrits) |
|---|---|---|---|
| `0x4014ab5c` | `0x400bb120` | pris (152/280 o) | track-filter (152 o) |
| `0x4014b85c` | `0x400bae4e` | pris (148/280 o) | track-filter (148 o) |
| `0x4014d74c` | `0x400bac28` | pris (164/280 o) | track-filter (164 o) |
| `0x401542f8` | `0x400b91d8` | pris (162/280 o) | track-filter (162 o) |
| `0x401548b4` | `0x400b903a` | pris (206/280 o) | track-filter (206 o) |
| `0x4015b8f8` | `0x400b668c` | pris (260/280 o) | track-filter (260 o) |
| `0x4015f50c` | `0x400b5028` | pris (260/280 o) | track-filter (260 o) |
| `0x401601fc` | `0x400b4b4a` | pris (260/280 o) | track-filter (260 o) |
| `0x40160864` | `0x400b48ac` | pris (260/280 o) | track-filter (260 o) |
| `0x40160b6c` | `0x400b4870` | pris (216/280 o) | track-filter (216 o) |
| `0x40160e6c` | `0x400b482e` | pris (256/280 o) | track-filter (256 o) |
| `0x401625bc` | `0x400b3e2a` | pris (136/280 o) | track-filter (136 o) |
| `0x40163fb8` | `0x400b34c8` | pris (147/280 o) | track-filter (147 o) |
| `0x4016616c` | `0x400b2898` | pris (164/280 o) | track-filter (164 o) |
| `0x40166760` | `0x400b272e` | pris (208/280 o) | track-filter (208 o) |
| `0x40167c50` | `0x400b211e` | libre | |
| `0x401696a0` | `0x400b1540` | libre | |
| `0x401699a8` | `0x400b1500` | libre | |
| `0x4016aa28` | `0x400b1480` | libre | |

### 34×34 : 14 masques de 272 o (copie gardée `0x4016bfc8`) : 14 pris, 0 libres (0 o)

| masque | constante | état | mods (octets écrits) |
|---|---|---|---|
| `0x4016f8c8` | `0x400b0b3c` | pris (236/272 o) | lfo-plus (236 o) |
| `0x40173848` | `0x400b0350` | pris (206/272 o) | lfo-plus (206 o) |
| `0x401780a8` | `0x400af946` | pris (262/272 o) | lfo-plus (262 o) |
| `0x401784e8` | `0x400af832` | pris (plein) | lfo-plus (272 o) |
| `0x401835b8` | `0x400adedc` | pris (plein) | lfo-plus (272 o) |
| `0x40184df8` | `0x400adbc8` | pris (plein) | lfo-plus (272 o) |
| `0x40185308` | `0x400adb8c` | pris (plein) | lfo-plus (272 o) |
| `0x40185f48` | `0x400ad9c4` | pris (268/272 o) | lfo-plus (268 o) |
| `0x40186238` | `0x400ad988` | pris (258/272 o) | lfo-plus (258 o) |
| `0x40189618` | `0x400ad364` | pris (232/272 o) | lfo-plus (232 o) |
| `0x4018af88` | `0x400ad18a` | pris (180/272 o) | lfo-plus (180 o) |
| `0x4018b1a8` | `0x400ad16e` | pris (206/272 o) | lfo-plus (206 o) |
| `0x4018ff64` | `0x400ac7fc` | pris (90/272 o) | lfo-plus (90 o) |
| `0x40192ba4` | `0x400ac276` | pris (132/272 o) | midi-live-both (132 o) |

### 27×27 : 24 masques de 108 o (copie gardée `0x4014a550`) : 0 pris, 24 libres (2 592 o)

| masque | constante | état | mods (octets écrits) |
|---|---|---|---|
| `0x4014a890` | `0x400bb1fc` | libre | |
| `0x4014aa34` | `0x400bb178` | libre | |
| `0x4014af84` | `0x400bb044` | libre | |
| `0x4014b05c` | `0x400bb028` | libre | |
| `0x4014b5b4` | `0x400baf2e` | libre | |
| `0x4014b784` | `0x400bae6e` | libre | |
| `0x4014e608` | `0x400ba8f2` | libre | |
| `0x40152f88` | `0x400b96ce` | libre | |
| `0x40159a04` | `0x400b71ea` | libre | |
| `0x40159adc` | `0x400b71ce` | libre | |
| `0x4015b820` | `0x400b66a8` | libre | |
| `0x4015bf24` | `0x400b6476` | libre | |
| `0x4015c9a4` | `0x400b6232` | libre | |
| `0x4015fb6c` | `0x400b4e5a` | libre | |
| `0x40160a94` | `0x400b488c` | libre | |
| `0x401617a8` | `0x400b4386` | libre | |
| `0x40161880` | `0x400b4366` | libre | |
| `0x401629dc` | `0x400b3d96` | libre | |
| `0x40163a60` | `0x400b362e` | libre | |
| `0x40167900` | `0x400b21ac` | libre | |
| `0x40167aa8` | `0x400b216c` | libre | |
| `0x40168440` | `0x400b1d7c` | libre | |
| `0x401688b4` | `0x400b1c5e` | libre | |
| `0x401698d0` | `0x400b1522` | libre | |

### 31×22 : 18 masques de 124 o (copie gardée `0x4016e980`) : 0 pris, 18 libres (2 232 o)

| masque | constante | état | mods (octets écrits) |
|---|---|---|---|
| `0x4016f7d0` | `0x400b0b5c` | libre | |
| `0x4016fd60` | `0x400b0ae4` | libre | |
| `0x40172510` | `0x400b0564` | libre | |
| `0x40178888` | `0x400af7f6` | libre | |
| `0x40179a20` | `0x400af62e` | libre | |
| `0x4017a4d4` | `0x400af43c` | libre | |
| `0x401837d8` | `0x400adeba` | libre | |
| `0x401871a0` | `0x400ad77e` | libre | |
| `0x40189838` | `0x400ad344` | libre | |
| `0x4018a510` | `0x400ad1e6` | libre | |
| `0x4018bcc8` | `0x400ad00c` | libre | |
| `0x4018f98c` | `0x400ac874` | libre | |
| `0x4018fa84` | `0x400ac858` | libre | |
| `0x4018fb7c` | `0x400ac838` | libre | |
| `0x401907a4` | `0x400ac768` | libre | |
| `0x40190a1c` | `0x400ac72c` | libre | |
| `0x40194ad4` | `0x400abeaa` | libre | |
| `0x40195a7c` | `0x400abc76` | libre | |

### 26×26 : 14 masques de 104 o (copie gardée `0x4014b4e4`) : 0 pris, 14 libres (1 456 o)

| masque | constante | état | mods (octets écrits) |
|---|---|---|---|
| `0x401573cc` | `0x400b83da` | libre | |
| `0x40160d9c` | `0x400b4850` | libre | |
| `0x40162ab4` | `0x400b3d76` | libre | |
| `0x401630e4` | `0x400b3b2e` | libre | |
| `0x401638c0` | `0x400b366a` | libre | |
| `0x40163990` | `0x400b364a` | libre | |
| `0x40163b38` | `0x400b360e` | libre | |
| `0x40166690` | `0x400b274c` | libre | |
| `0x401679d8` | `0x400b218a` | libre | |
| `0x40167b80` | `0x400b2144` | libre | |
| `0x40168c4c` | `0x400b1b80` | libre | |
| `0x40168fb4` | `0x400b1a72` | libre | |
| `0x40179c98` | `0x400af5f2` | libre | |
| `0x40186168` | `0x400ad9a4` | libre | |

### 46×31 : 7 masques de 184 o (copie gardée `0x4016be58`) : 0 pris, 7 libres (1 288 o)

| masque | constante | état | mods (octets écrits) |
|---|---|---|---|
| `0x40170ad8` | `0x400b08f6` | libre | |
| `0x40171bc8` | `0x400b06d0` | libre | |
| `0x401728f8` | `0x400b0528` | libre | |
| `0x40179140` | `0x400af6c2` | libre | |
| `0x40184988` | `0x400adc20` | libre | |
| `0x40185648` | `0x400ada58` | libre | |
| `0x401857f8` | `0x400ada1c` | libre | |

### 41×41 : 1 masques de 328 o (copie gardée `0x40187298`) : 1 pris, 0 libres (0 o)

| masque | constante | état | mods (octets écrits) |
|---|---|---|---|
| `0x4018d918` | `0x400acd1a` | pris (296/328 o) | model-tg (296 o), model-tg-st (296 o) |

### 52×22 : 1 masques de 208 o (copie gardée `0x4014bfe4`) : 1 pris, 0 libres (0 o)

| masque | constante | état | mods (octets écrits) |
|---|---|---|---|
| `0x4016ea78` | `0x400b0d50` | pris (152/208 o) | model-tg (152 o), model-tg-st (152 o) |

### Masques 0xFF redirigés vers `0x40154ae4` (notes/14 §5)

Trois masques entièrement à 0xFF, les plus grands ; plusieurs mods s'y partagent la place (`check_overlaps.py` garantit qu'ils n'écrivent pas les mêmes octets, ou à l'identique).

| masque | taille | constante | état | mods (octets écrits) |
|---|---|---|---|---|
| `0x4015c044` | 720 o | `0x400b6434` | pris (550/720 o) | 6ch-usbup (384 o), acid (208 o), macro (208 o), macro-acid (208 o), mod-settings (384 o), model-tg (208 o), model-tg-st (208 o), syntakt-* (32/32, 208 o), syntakt-*-acid (31/31, 208 o), syntakt-*-macro (31/31, 208 o), syntakt-*-macro-acid (31/31, 208 o), trig-hold (166 o) |
| `0x4016cae8` | 1024 o | `0x400b1106` | pris (1016/1024 o) | acid (104 o), acid-tg (96 o), arp (824 o), macro (104 o), macro-acid (112 o), macro-acid-tg (104 o), macro-tg (96 o), sdvintage-7th (40 o), sdvintage-exact (40 o), sdvintage-snare (973 o), syntakt-* (32/32, 80 o), syntakt-*-acid (31/31, 188 o), syntakt-*-macro (31/31, 188 o), syntakt-*-macro-acid (31/31, 188 o), syntakt-tg-* (33/33, 172–188 o), syntakt-tg-*-acid (31/31, 180 o), syntakt-tg-*-macro (31/31, 180 o), syntakt-tg-*-macro-acid (31/31, 180 o), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn (180 o), syntakt-vintage (40 o) |
| `0x4018a788` | 1024 o | `0x400ad1aa` | pris (1016/1024 o) | arp (1016 o), sdvintage-snare (638 o) |

## 2. Autres écritures dans des octets 0xFF (caves)

Octets à 0xFF dans l'OS d'origine, hors des masques ci-dessus (tables à trous, fins de blocs). `build.py` refuse d'y écrire si l'image d'origine pointe dedans, sauf référence vérifiée à la main (`device.json`, `cave_refs_ok`).

| adresse | octets | mods |
|---|---|---|
| `0x4010dd18` | 8 | model-tg, model-tg-st |
| `0x4010df48` | 8 | model-tg, model-tg-st |
| `0x40147f22` | 2 | browser-scroll, model-tg, model-tg-st |
| `0x40147f25` | 126 | browser-scroll, model-tg, model-tg-st |
| `0x40147fa4` | 52 | browser-scroll, model-tg, model-tg-st |
| `0x40148328` | 104 | latching-mute, model-tg, model-tg-st |
| `0x401485f0` | 16 | browser-scroll, model-tg, model-tg-st |
| `0x40148662` | 348 | latching-mute, model-tg, model-tg-st |
| `0x401487e0` | 4 | latching-mute, model-tg, model-tg-st |
| `0x401487ec` | 2 | latching-mute, model-tg, model-tg-st |
| `0x401489fa` | 2 | model-tg, model-tg-st, trig-preview |
| `0x401489fd` | 246 | model-tg, model-tg-st, trig-preview |
| `0x40148af4` | 76 | model-tg, model-tg-st, trig-preview |
| `0x40148b41` | 15 | model-tg, model-tg-st, trig-preview |
| `0x40148b51` | 49 | model-tg, model-tg-st, trig-preview |

## 3. Charges utiles ajoutées après l'OS

Code trop gros pour un masque, ajouté à la fin de l'image (`at`) et copié au démarrage en mémoire (`dest`) ; les charges d'un même firmware s'enchaînent dans l'ordre `order` (notes/17, 31), ce que `check_overlaps.py` vérifie pour chaque ensemble installable. L'image ne peut pas dépasser `0x40200000`.

| mod | order | dans l'image (`at`) | octets | fin | en mémoire (`dest`) | octets | demande |
|---|---|---|---|---|---|---|---|
| sdvintage-exact | 21 | `0x401aa140` | 205 200 | `0x401dc2d0` | `0x43000000` | 205 200 |  |
| sdvintage-7th | 22 | `0x401aa140` | 218 208 | `0x401df5a0` | `0x43000000` | 218 208 |  |
| syntakt-vintage | 23 | `0x401aa140` | 218 560 | `0x401df700` | `0x43000000` | 218 560 |  |
| syntakt-bits | 24 | `0x401aa140` | 264 448 | `0x401eaa40` | `0x43000000` | 264 448 |  |
| syntakt-bits-acid | 24 | `0x401aa140` | 150 405 | `0x401cecc5` | `0x43000000` | 492 288 |  |
| syntakt-bits-macro | 24 | `0x401aa140` | 234 234 | `0x401e343a` | `0x43000000` | 476 128 |  |
| syntakt-bits-macro-acid | 24 | `0x401aa140` | 239 457 | `0x401e48a1` | `0x43000000` | 492 288 |  |
| syntakt-bits-swarm | 24 | `0x401aa140` | 269 056 | `0x401ebc40` | `0x43000000` | 269 056 |  |
| syntakt-bits-swarm-acid | 24 | `0x401aa140` | 156 654 | `0x401d052e` | `0x43000000` | 492 288 |  |
| syntakt-bits-swarm-macro | 24 | `0x401aa140` | 240 467 | `0x401e4c93` | `0x43000000` | 476 128 |  |
| syntakt-bits-swarm-macro-acid | 24 | `0x401aa140` | 245 674 | `0x401e60ea` | `0x43000000` | 492 288 |  |
| syntakt-cp | 24 | `0x401aa140` | 260 352 | `0x401e9a40` | `0x43000000` | 260 352 |  |
| syntakt-cp-acid | 24 | `0x401aa140` | 145 749 | `0x401cda95` | `0x43000000` | 492 288 |  |
| syntakt-cp-bits | 24 | `0x401aa140` | 264 448 | `0x401eaa40` | `0x43000000` | 264 448 |  |
| syntakt-cp-bits-acid | 24 | `0x401aa140` | 150 663 | `0x401cedc7` | `0x43000000` | 492 288 |  |
| syntakt-cp-bits-macro | 24 | `0x401aa140` | 234 486 | `0x401e3536` | `0x43000000` | 476 128 |  |
| syntakt-cp-bits-macro-acid | 24 | `0x401aa140` | 239 699 | `0x401e4993` | `0x43000000` | 492 288 |  |
| syntakt-cp-bits-swarm | 24 | `0x401aa140` | 269 056 | `0x401ebc40` | `0x43000000` | 269 056 |  |
| syntakt-cp-bits-swarm-acid | 24 | `0x401aa140` | 156 876 | `0x401d060c` | `0x43000000` | 492 288 |  |
| syntakt-cp-bits-swarm-macro | 24 | `0x401aa140` | 240 688 | `0x401e4d70` | `0x43000000` | 476 128 |  |
| syntakt-cp-bits-swarm-macro-acid | 24 | `0x401aa140` | 245 920 | `0x401e61e0` | `0x43000000` | 492 288 |  |
| syntakt-cp-macro | 24 | `0x401aa140` | 229 579 | `0x401e220b` | `0x43000000` | 476 128 |  |
| syntakt-cp-macro-acid | 24 | `0x401aa140` | 234 803 | `0x401e3673` | `0x43000000` | 492 288 |  |
| syntakt-cp-swarm | 24 | `0x401aa140` | 269 056 | `0x401ebc40` | `0x43000000` | 269 056 |  |
| syntakt-cp-swarm-acid | 24 | `0x401aa140` | 156 623 | `0x401d050f` | `0x43000000` | 492 288 |  |
| syntakt-cp-swarm-macro | 24 | `0x401aa140` | 240 451 | `0x401e4c83` | `0x43000000` | 476 128 |  |
| syntakt-cp-swarm-macro-acid | 24 | `0x401aa140` | 245 662 | `0x401e60de` | `0x43000000` | 492 288 |  |
| syntakt-cp-toy | 24 | `0x401aa140` | 260 352 | `0x401e9a40` | `0x43000000` | 260 352 |  |
| syntakt-cp-toy-acid | 24 | `0x401aa140` | 146 013 | `0x401cdb9d` | `0x43000000` | 492 288 |  |
| syntakt-cp-toy-bits | 24 | `0x401aa140` | 264 448 | `0x401eaa40` | `0x43000000` | 264 448 |  |
| syntakt-cp-toy-bits-acid | 24 | `0x401aa140` | 150 868 | `0x401cee94` | `0x43000000` | 492 288 |  |
| syntakt-cp-toy-bits-macro | 24 | `0x401aa140` | 234 694 | `0x401e3606` | `0x43000000` | 476 128 |  |
| syntakt-cp-toy-bits-macro-acid | 24 | `0x401aa140` | 239 918 | `0x401e4a6e` | `0x43000000` | 492 288 |  |
| syntakt-cp-toy-bits-swarm | 24 | `0x401aa140` | 269 056 | `0x401ebc40` | `0x43000000` | 269 056 |  |
| syntakt-cp-toy-bits-swarm-acid | 24 | `0x401aa140` | 157 081 | `0x401d06d9` | `0x43000000` | 492 288 |  |
| syntakt-cp-toy-bits-swarm-macro | 24 | `0x401aa140` | 240 900 | `0x401e4e44` | `0x43000000` | 476 128 |  |
| syntakt-cp-toy-bits-swarm-macro-acid | 24 | `0x401aa140` | 246 121 | `0x401e62a9` | `0x43000000` | 492 288 |  |
| syntakt-cp-toy-macro | 24 | `0x401aa140` | 229 839 | `0x401e230f` | `0x43000000` | 476 128 |  |
| syntakt-cp-toy-macro-acid | 24 | `0x401aa140` | 235 057 | `0x401e3771` | `0x43000000` | 492 288 |  |
| syntakt-cp-toy-swarm | 24 | `0x401aa140` | 269 056 | `0x401ebc40` | `0x43000000` | 269 056 |  |
| syntakt-cp-toy-swarm-acid | 24 | `0x401aa140` | 156 850 | `0x401d05f2` | `0x43000000` | 492 288 |  |
| syntakt-cp-toy-swarm-macro | 24 | `0x401aa140` | 240 667 | `0x401e4d5b` | `0x43000000` | 476 128 |  |
| syntakt-cp-toy-swarm-macro-acid | 24 | `0x401aa140` | 245 893 | `0x401e61c5` | `0x43000000` | 492 288 |  |
| syntakt-sd | 24 | `0x401aa140` | 260 352 | `0x401e9a40` | `0x43000000` | 260 352 |  |
| syntakt-sd-acid | 24 | `0x401aa140` | 145 754 | `0x401cda9a` | `0x43000000` | 492 288 |  |
| syntakt-sd-bits | 24 | `0x401aa140` | 264 448 | `0x401eaa40` | `0x43000000` | 264 448 |  |
| syntakt-sd-bits-acid | 24 | `0x401aa140` | 150 690 | `0x401cede2` | `0x43000000` | 492 288 |  |
| syntakt-sd-bits-macro | 24 | `0x401aa140` | 234 521 | `0x401e3559` | `0x43000000` | 476 128 |  |
| syntakt-sd-bits-macro-acid | 24 | `0x401aa140` | 239 723 | `0x401e49ab` | `0x43000000` | 492 288 |  |
| syntakt-sd-bits-swarm | 24 | `0x401aa140` | 269 056 | `0x401ebc40` | `0x43000000` | 269 056 |  |
| syntakt-sd-bits-swarm-acid | 24 | `0x401aa140` | 156 902 | `0x401d0626` | `0x43000000` | 492 288 |  |
| syntakt-sd-bits-swarm-macro | 24 | `0x401aa140` | 240 726 | `0x401e4d96` | `0x43000000` | 476 128 |  |
| syntakt-sd-bits-swarm-macro-acid | 24 | `0x401aa140` | 245 942 | `0x401e61f6` | `0x43000000` | 492 288 |  |
| syntakt-sd-cp | 24 | `0x401aa140` | 260 352 | `0x401e9a40` | `0x43000000` | 260 352 |  |
| syntakt-sd-cp-acid | 24 | `0x401aa140` | 146 012 | `0x401cdb9c` | `0x43000000` | 492 288 |  |
| syntakt-sd-cp-bits | 24 | `0x401aa140` | 264 448 | `0x401eaa40` | `0x43000000` | 264 448 |  |
| syntakt-sd-cp-bits-acid | 24 | `0x401aa140` | 150 880 | `0x401ceea0` | `0x43000000` | 492 288 |  |
| syntakt-sd-cp-bits-macro | 24 | `0x401aa140` | 234 718 | `0x401e361e` | `0x43000000` | 476 128 |  |
| syntakt-sd-cp-bits-macro-acid | 24 | `0x401aa140` | 239 926 | `0x401e4a76` | `0x43000000` | 492 288 |  |
| syntakt-sd-cp-bits-swarm | 24 | `0x401aa140` | 269 056 | `0x401ebc40` | `0x43000000` | 269 056 |  |
| syntakt-sd-cp-bits-swarm-acid | 24 | `0x401aa140` | 157 090 | `0x401d06e2` | `0x43000000` | 492 288 |  |
| syntakt-sd-cp-bits-swarm-macro | 24 | `0x401aa140` | 240 912 | `0x401e4e50` | `0x43000000` | 476 128 |  |
| syntakt-sd-cp-bits-swarm-macro-acid | 24 | `0x401aa140` | 246 116 | `0x401e62a4` | `0x43000000` | 492 288 |  |
| syntakt-sd-cp-macro | 24 | `0x401aa140` | 229 849 | `0x401e2319` | `0x43000000` | 476 128 |  |
| syntakt-sd-cp-macro-acid | 24 | `0x401aa140` | 235 056 | `0x401e3770` | `0x43000000` | 492 288 |  |
| syntakt-sd-cp-swarm | 24 | `0x401aa140` | 269 056 | `0x401ebc40` | `0x43000000` | 269 056 |  |
| syntakt-sd-cp-swarm-acid | 24 | `0x401aa140` | 156 856 | `0x401d05f8` | `0x43000000` | 492 288 |  |
| syntakt-sd-cp-swarm-macro | 24 | `0x401aa140` | 240 675 | `0x401e4d63` | `0x43000000` | 476 128 |  |
| syntakt-sd-cp-swarm-macro-acid | 24 | `0x401aa140` | 245 891 | `0x401e61c3` | `0x43000000` | 492 288 |  |
| syntakt-sd-cp-toy | 24 | `0x401aa140` | 260 352 | `0x401e9a40` | `0x43000000` | 260 352 |  |
| syntakt-sd-cp-toy-acid | 24 | `0x401aa140` | 146 224 | `0x401cdc70` | `0x43000000` | 492 288 |  |
| syntakt-sd-cp-toy-bits | 24 | `0x401aa140` | 264 448 | `0x401eaa40` | `0x43000000` | 264 448 |  |
| syntakt-sd-cp-toy-bits-acid | 24 | `0x401aa140` | 151 089 | `0x401cef71` | `0x43000000` | 492 288 |  |
| syntakt-sd-cp-toy-bits-macro | 24 | `0x401aa140` | 234 919 | `0x401e36e7` | `0x43000000` | 476 128 |  |
| syntakt-sd-cp-toy-bits-macro-acid | 24 | `0x401aa140` | 240 123 | `0x401e4b3b` | `0x43000000` | 492 288 |  |
| syntakt-sd-cp-toy-bits-swarm | 24 | `0x401aa140` | 269 056 | `0x401ebc40` | `0x43000000` | 269 056 |  |
| syntakt-sd-cp-toy-bits-swarm-acid | 24 | `0x401aa140` | 157 290 | `0x401d07aa` | `0x43000000` | 492 288 |  |
| syntakt-sd-cp-toy-bits-swarm-macro | 24 | `0x401aa140` | 241 114 | `0x401e4f1a` | `0x43000000` | 476 128 |  |
| syntakt-sd-cp-toy-bits-swarm-macro-acid | 24 | `0x401aa140` | 246 316 | `0x401e636c` | `0x43000000` | 492 288 |  |
| syntakt-sd-cp-toy-macro | 24 | `0x401aa140` | 230 058 | `0x401e23ea` | `0x43000000` | 476 128 |  |
| syntakt-sd-cp-toy-macro-acid | 24 | `0x401aa140` | 235 279 | `0x401e384f` | `0x43000000` | 492 288 |  |
| syntakt-sd-cp-toy-swarm | 24 | `0x401aa140` | 269 056 | `0x401ebc40` | `0x43000000` | 269 056 |  |
| syntakt-sd-cp-toy-swarm-acid | 24 | `0x401aa140` | 157 061 | `0x401d06c5` | `0x43000000` | 492 288 |  |
| syntakt-sd-cp-toy-swarm-macro | 24 | `0x401aa140` | 240 896 | `0x401e4e40` | `0x43000000` | 476 128 |  |
| syntakt-sd-cp-toy-swarm-macro-acid | 24 | `0x401aa140` | 246 093 | `0x401e628d` | `0x43000000` | 492 288 |  |
| syntakt-sd-macro | 24 | `0x401aa140` | 229 585 | `0x401e2211` | `0x43000000` | 476 128 |  |
| syntakt-sd-macro-acid | 24 | `0x401aa140` | 234 810 | `0x401e367a` | `0x43000000` | 492 288 |  |
| syntakt-sd-swarm | 24 | `0x401aa140` | 269 056 | `0x401ebc40` | `0x43000000` | 269 056 |  |
| syntakt-sd-swarm-acid | 24 | `0x401aa140` | 156 627 | `0x401d0513` | `0x43000000` | 492 288 |  |
| syntakt-sd-swarm-macro | 24 | `0x401aa140` | 240 462 | `0x401e4c8e` | `0x43000000` | 476 128 |  |
| syntakt-sd-swarm-macro-acid | 24 | `0x401aa140` | 245 664 | `0x401e60e0` | `0x43000000` | 492 288 |  |
| syntakt-sd-toy | 24 | `0x401aa140` | 260 352 | `0x401e9a40` | `0x43000000` | 260 352 |  |
| syntakt-sd-toy-acid | 24 | `0x401aa140` | 146 016 | `0x401cdba0` | `0x43000000` | 492 288 |  |
| syntakt-sd-toy-bits | 24 | `0x401aa140` | 264 448 | `0x401eaa40` | `0x43000000` | 264 448 |  |
| syntakt-sd-toy-bits-acid | 24 | `0x401aa140` | 150 897 | `0x401ceeb1` | `0x43000000` | 492 288 |  |
| syntakt-sd-toy-bits-macro | 24 | `0x401aa140` | 234 717 | `0x401e361d` | `0x43000000` | 476 128 |  |
| syntakt-sd-toy-bits-macro-acid | 24 | `0x401aa140` | 239 946 | `0x401e4a8a` | `0x43000000` | 492 288 |  |
| syntakt-sd-toy-bits-swarm | 24 | `0x401aa140` | 269 056 | `0x401ebc40` | `0x43000000` | 269 056 |  |
| syntakt-sd-toy-bits-swarm-acid | 24 | `0x401aa140` | 157 112 | `0x401d06f8` | `0x43000000` | 492 288 |  |
| syntakt-sd-toy-bits-swarm-macro | 24 | `0x401aa140` | 240 930 | `0x401e4e62` | `0x43000000` | 476 128 |  |
| syntakt-sd-toy-bits-swarm-macro-acid | 24 | `0x401aa140` | 246 137 | `0x401e62b9` | `0x43000000` | 492 288 |  |
| syntakt-sd-toy-macro | 24 | `0x401aa140` | 229 848 | `0x401e2318` | `0x43000000` | 476 128 |  |
| syntakt-sd-toy-macro-acid | 24 | `0x401aa140` | 235 056 | `0x401e3770` | `0x43000000` | 492 288 |  |
| syntakt-sd-toy-swarm | 24 | `0x401aa140` | 269 056 | `0x401ebc40` | `0x43000000` | 269 056 |  |
| syntakt-sd-toy-swarm-acid | 24 | `0x401aa140` | 156 858 | `0x401d05fa` | `0x43000000` | 492 288 |  |
| syntakt-sd-toy-swarm-macro | 24 | `0x401aa140` | 240 678 | `0x401e4d66` | `0x43000000` | 476 128 |  |
| syntakt-sd-toy-swarm-macro-acid | 24 | `0x401aa140` | 245 895 | `0x401e61c7` | `0x43000000` | 492 288 |  |
| syntakt-swarm | 24 | `0x401aa140` | 269 056 | `0x401ebc40` | `0x43000000` | 269 056 |  |
| syntakt-swarm-acid | 24 | `0x401aa140` | 156 342 | `0x401d03f6` | `0x43000000` | 492 288 |  |
| syntakt-swarm-macro | 24 | `0x401aa140` | 240 169 | `0x401e4b69` | `0x43000000` | 476 128 |  |
| syntakt-swarm-macro-acid | 24 | `0x401aa140` | 245 392 | `0x401e5fd0` | `0x43000000` | 492 288 |  |
| syntakt-toy | 24 | `0x401aa140` | 260 352 | `0x401e9a40` | `0x43000000` | 260 352 |  |
| syntakt-toy-acid | 24 | `0x401aa140` | 145 736 | `0x401cda88` | `0x43000000` | 492 288 |  |
| syntakt-toy-bits | 24 | `0x401aa140` | 264 448 | `0x401eaa40` | `0x43000000` | 264 448 |  |
| syntakt-toy-bits-acid | 24 | `0x401aa140` | 150 668 | `0x401cedcc` | `0x43000000` | 492 288 |  |
| syntakt-toy-bits-macro | 24 | `0x401aa140` | 234 488 | `0x401e3538` | `0x43000000` | 476 128 |  |
| syntakt-toy-bits-macro-acid | 24 | `0x401aa140` | 239 707 | `0x401e499b` | `0x43000000` | 492 288 |  |
| syntakt-toy-bits-swarm | 24 | `0x401aa140` | 269 056 | `0x401ebc40` | `0x43000000` | 269 056 |  |
| syntakt-toy-bits-swarm-acid | 24 | `0x401aa140` | 156 873 | `0x401d0609` | `0x43000000` | 492 288 |  |
| syntakt-toy-bits-swarm-macro | 24 | `0x401aa140` | 240 690 | `0x401e4d72` | `0x43000000` | 476 128 |  |
| syntakt-toy-bits-swarm-macro-acid | 24 | `0x401aa140` | 245 908 | `0x401e61d4` | `0x43000000` | 492 288 |  |
| syntakt-toy-macro | 24 | `0x401aa140` | 229 568 | `0x401e2200` | `0x43000000` | 476 128 |  |
| syntakt-toy-macro-acid | 24 | `0x401aa140` | 234 795 | `0x401e366b` | `0x43000000` | 492 288 |  |
| syntakt-toy-swarm | 24 | `0x401aa140` | 269 056 | `0x401ebc40` | `0x43000000` | 269 056 |  |
| syntakt-toy-swarm-acid | 24 | `0x401aa140` | 156 616 | `0x401d0508` | `0x43000000` | 492 288 |  |
| syntakt-toy-swarm-macro | 24 | `0x401aa140` | 240 438 | `0x401e4c76` | `0x43000000` | 476 128 |  |
| syntakt-toy-swarm-macro-acid | 24 | `0x401aa140` | 245 649 | `0x401e60d1` | `0x43000000` | 492 288 |  |
| macro | 25 | `0x401aa140` | 104 196 | `0x401c3844` | `0x43000000` | 324 576 |  |
| macro-acid | 25 | `0x401aa140` | 110 804 | `0x401c5214` | `0x43000000` | 492 288 |  |
| acid | 26 | `0x401aa140` | 11 380 | `0x401acdb4` | `0x43000000` | 221 928 |  |
| model-tg | 30 | `0x401aa140` | 87 984 | `0x401bf8f0` | `0x401aa140` | 87 984 |  |
| model-tg-st | 30 | `0x401aa140` | 87 984 | `0x401bf8f0` | `0x401aa140` | 87 984 |  |
| syntakt-tg-bits | 31 | `0x401bf8f0` | 234 568 | `0x401f8d38` | `0x46700000` | 264 448 | model-tg-st |
| syntakt-tg-bits-acid | 31 | `0x401bf8f0` | 150 718 | `0x401e45ae` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-bits-macro | 31 | `0x401bf8f0` | 234 565 | `0x401f8d35` | `0x46700000` | 476 128 | model-tg-st |
| syntakt-tg-bits-macro-acid | 31 | `0x401bf8f0` | 239 792 | `0x401fa1a0` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-bits-swarm | 31 | `0x401bf8f0` | 241 528 | `0x401fa868` | `0x46700000` | 269 056 | model-tg-st |
| syntakt-tg-bits-swarm-acid | 31 | `0x401bf8f0` | 156 968 | `0x401e5e18` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-bits-swarm-macro | 31 | `0x401bf8f0` | 240 800 | `0x401fa590` | `0x46700000` | 476 128 | model-tg-st |
| syntakt-tg-bits-swarm-macro-acid | 31 | `0x401bf8f0` | 246 018 | `0x401fb9f2` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-cp | 31 | `0x401bf8f0` | 227 792 | `0x401f72c0` | `0x46700000` | 260 352 | model-tg-st |
| syntakt-tg-cp-acid | 31 | `0x401bf8f0` | 146 068 | `0x401e3384` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-cp-bits | 31 | `0x401bf8f0` | 235 204 | `0x401f8fb4` | `0x46700000` | 264 448 | model-tg-st |
| syntakt-tg-cp-bits-acid | 31 | `0x401bf8f0` | 150 980 | `0x401e46b4` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-cp-bits-macro | 31 | `0x401bf8f0` | 234 839 | `0x401f8e47` | `0x46700000` | 476 128 | model-tg-st |
| syntakt-tg-cp-bits-macro-acid | 31 | `0x401bf8f0` | 240 039 | `0x401fa297` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-cp-bits-swarm | 31 | `0x401bf8f0` | 242 040 | `0x401faa68` | `0x46700000` | 269 056 | model-tg-st |
| syntakt-tg-cp-bits-swarm-acid | 31 | `0x401bf8f0` | 157 180 | `0x401e5eec` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-cp-bits-swarm-macro | 31 | `0x401bf8f0` | 241 032 | `0x401fa678` | `0x46700000` | 476 128 | model-tg-st |
| syntakt-tg-cp-bits-swarm-macro-acid | 31 | `0x401bf8f0` | 246 239 | `0x401fbacf` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-cp-macro | 31 | `0x401bf8f0` | 229 923 | `0x401f7b13` | `0x46700000` | 476 128 | model-tg-st |
| syntakt-tg-cp-macro-acid | 31 | `0x401bf8f0` | 235 146 | `0x401f8f7a` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-cp-swarm | 31 | `0x401bf8f0` | 241 528 | `0x401fa868` | `0x46700000` | 269 056 | model-tg-st |
| syntakt-tg-cp-swarm-acid | 31 | `0x401bf8f0` | 156 926 | `0x401e5dee` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-cp-swarm-macro | 31 | `0x401bf8f0` | 240 781 | `0x401fa57d` | `0x46700000` | 476 128 | model-tg-st |
| syntakt-tg-cp-swarm-macro-acid | 31 | `0x401bf8f0` | 245 995 | `0x401fb9db` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-cp-toy | 31 | `0x401bf8f0` | 228 368 | `0x401f7500` | `0x46700000` | 260 352 | model-tg-st |
| syntakt-tg-cp-toy-acid | 31 | `0x401bf8f0` | 146 321 | `0x401e3481` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-cp-toy-bits | 31 | `0x401bf8f0` | 235 708 | `0x401f91ac` | `0x46700000` | 264 448 | model-tg-st |
| syntakt-tg-cp-toy-bits-acid | 31 | `0x401bf8f0` | 151 193 | `0x401e4789` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-cp-toy-bits-macro | 31 | `0x401bf8f0` | 235 040 | `0x401f8f10` | `0x46700000` | 476 128 | model-tg-st |
| syntakt-tg-cp-toy-bits-macro-acid | 31 | `0x401bf8f0` | 240 249 | `0x401fa369` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-cp-toy-bits-swarm | 31 | `0x401bf8f0` | 242 532 | `0x401fac54` | `0x46700000` | 269 056 | model-tg-st |
| syntakt-tg-cp-toy-bits-swarm-acid | 31 | `0x401bf8f0` | 157 377 | `0x401e5fb1` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-cp-toy-bits-swarm-macro | 31 | `0x401bf8f0` | 241 231 | `0x401fa73f` | `0x46700000` | 476 128 | model-tg-st |
| syntakt-tg-cp-toy-bits-swarm-macro-acid | 31 | `0x401bf8f0` | 246 438 | `0x401fbb96` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-cp-toy-macro | 31 | `0x401bf8f0` | 230 176 | `0x401f7c10` | `0x46700000` | 476 128 | model-tg-st |
| syntakt-tg-cp-toy-macro-acid | 31 | `0x401bf8f0` | 235 390 | `0x401f906e` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-cp-toy-swarm | 31 | `0x401bf8f0` | 242 000 | `0x401faa40` | `0x46700000` | 269 056 | model-tg-st |
| syntakt-tg-cp-toy-swarm-acid | 31 | `0x401bf8f0` | 157 150 | `0x401e5ece` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-cp-toy-swarm-macro | 31 | `0x401bf8f0` | 240 994 | `0x401fa652` | `0x46700000` | 476 128 | model-tg-st |
| syntakt-tg-cp-toy-swarm-macro-acid | 31 | `0x401bf8f0` | 246 204 | `0x401fbaac` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-sd | 31 | `0x401bf8f0` | 227 792 | `0x401f72c0` | `0x46700000` | 260 352 | model-tg-st |
| syntakt-tg-sd-acid | 31 | `0x401bf8f0` | 146 069 | `0x401e3385` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-sd-bits | 31 | `0x401bf8f0` | 235 216 | `0x401f8fc0` | `0x46700000` | 264 448 | model-tg-st |
| syntakt-tg-sd-bits-acid | 31 | `0x401bf8f0` | 151 005 | `0x401e46cd` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-sd-bits-macro | 31 | `0x401bf8f0` | 234 862 | `0x401f8e5e` | `0x46700000` | 476 128 | model-tg-st |
| syntakt-tg-sd-bits-macro-acid | 31 | `0x401bf8f0` | 240 065 | `0x401fa2b1` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-sd-bits-swarm | 31 | `0x401bf8f0` | 242 060 | `0x401faa7c` | `0x46700000` | 269 056 | model-tg-st |
| syntakt-tg-sd-bits-swarm-acid | 31 | `0x401bf8f0` | 157 216 | `0x401e5f10` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-sd-bits-swarm-macro | 31 | `0x401bf8f0` | 241 059 | `0x401fa693` | `0x46700000` | 476 128 | model-tg-st |
| syntakt-tg-sd-bits-swarm-macro-acid | 31 | `0x401bf8f0` | 246 267 | `0x401fbaeb` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-sd-cp | 31 | `0x401bf8f0` | 228 380 | `0x401f750c` | `0x46700000` | 260 352 | model-tg-st |
| syntakt-tg-sd-cp-acid | 31 | `0x401bf8f0` | 146 327 | `0x401e3487` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-sd-cp-bits | 31 | `0x401bf8f0` | 235 732 | `0x401f91c4` | `0x46700000` | 264 448 | model-tg-st |
| syntakt-tg-sd-cp-bits-acid | 31 | `0x401bf8f0` | 151 209 | `0x401e4799` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-sd-cp-bits-macro | 31 | `0x401bf8f0` | 235 050 | `0x401f8f1a` | `0x46700000` | 476 128 | model-tg-st |
| syntakt-tg-sd-cp-bits-macro-acid | 31 | `0x401bf8f0` | 240 263 | `0x401fa377` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-sd-cp-bits-swarm | 31 | `0x401bf8f0` | 242 552 | `0x401fac68` | `0x46700000` | 269 056 | model-tg-st |
| syntakt-tg-sd-cp-bits-swarm-acid | 31 | `0x401bf8f0` | 157 394 | `0x401e5fc2` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-sd-cp-bits-swarm-macro | 31 | `0x401bf8f0` | 241 247 | `0x401fa74f` | `0x46700000` | 476 128 | model-tg-st |
| syntakt-tg-sd-cp-bits-swarm-macro-acid | 31 | `0x401bf8f0` | 246 452 | `0x401fbba4` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-sd-cp-macro | 31 | `0x401bf8f0` | 230 191 | `0x401f7c1f` | `0x46700000` | 476 128 | model-tg-st |
| syntakt-tg-sd-cp-macro-acid | 31 | `0x401bf8f0` | 235 396 | `0x401f9074` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-sd-cp-swarm | 31 | `0x401bf8f0` | 242 020 | `0x401faa54` | `0x46700000` | 269 056 | model-tg-st |
| syntakt-tg-sd-cp-swarm-acid | 31 | `0x401bf8f0` | 157 155 | `0x401e5ed3` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-sd-cp-swarm-macro | 31 | `0x401bf8f0` | 241 004 | `0x401fa65c` | `0x46700000` | 476 128 | model-tg-st |
| syntakt-tg-sd-cp-swarm-macro-acid | 31 | `0x401bf8f0` | 246 212 | `0x401fbab4` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-sd-cp-toy | 31 | `0x401bf8f0` | 228 876 | `0x401f76fc` | `0x46700000` | 260 352 | model-tg-st |
| syntakt-tg-sd-cp-toy-acid | 31 | `0x401bf8f0` | 146 538 | `0x401e355a` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-sd-cp-toy-bits | 31 | `0x401bf8f0` | 236 220 | `0x401f93ac` | `0x46700000` | 264 448 | model-tg-st |
| syntakt-tg-sd-cp-toy-bits-acid | 31 | `0x401bf8f0` | 151 396 | `0x401e4854` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-sd-cp-toy-bits-macro | 31 | `0x401bf8f0` | 235 258 | `0x401f8fea` | `0x46700000` | 476 128 | model-tg-st |
| syntakt-tg-sd-cp-toy-bits-macro-acid | 31 | `0x401bf8f0` | 240 471 | `0x401fa447` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-sd-cp-toy-bits-swarm | 31 | `0x401bf8f0` | 243 044 | `0x401fae54` | `0x46700000` | 269 056 | model-tg-st |
| syntakt-tg-sd-cp-toy-bits-swarm-acid | 31 | `0x401bf8f0` | 157 597 | `0x401e608d` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-sd-cp-toy-bits-swarm-macro | 31 | `0x401bf8f0` | 241 446 | `0x401fa816` | `0x46700000` | 476 128 | model-tg-st |
| syntakt-tg-sd-cp-toy-bits-swarm-macro-acid | 31 | `0x401bf8f0` | 246 655 | `0x401fbc6f` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn | 31 | `0x401bf8f0` | 251 585 | `0x401fcfb1` | `0x46700000` | 504 168 | model-tg-st |
| syntakt-tg-sd-cp-toy-macro | 31 | `0x401bf8f0` | 230 387 | `0x401f7ce3` | `0x46700000` | 476 128 | model-tg-st |
| syntakt-tg-sd-cp-toy-macro-acid | 31 | `0x401bf8f0` | 235 602 | `0x401f9142` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-sd-cp-toy-swarm | 31 | `0x401bf8f0` | 242 512 | `0x401fac40` | `0x46700000` | 269 056 | model-tg-st |
| syntakt-tg-sd-cp-toy-swarm-acid | 31 | `0x401bf8f0` | 157 357 | `0x401e5f9d` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-sd-cp-toy-swarm-macro | 31 | `0x401bf8f0` | 241 218 | `0x401fa732` | `0x46700000` | 476 128 | model-tg-st |
| syntakt-tg-sd-cp-toy-swarm-macro-acid | 31 | `0x401bf8f0` | 246 421 | `0x401fbb85` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-sd-macro | 31 | `0x401bf8f0` | 229 924 | `0x401f7b14` | `0x46700000` | 476 128 | model-tg-st |
| syntakt-tg-sd-macro-acid | 31 | `0x401bf8f0` | 235 142 | `0x401f8f76` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-sd-swarm | 31 | `0x401bf8f0` | 241 524 | `0x401fa864` | `0x46700000` | 269 056 | model-tg-st |
| syntakt-tg-sd-swarm-acid | 31 | `0x401bf8f0` | 156 929 | `0x401e5df1` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-sd-swarm-macro | 31 | `0x401bf8f0` | 240 797 | `0x401fa58d` | `0x46700000` | 476 128 | model-tg-st |
| syntakt-tg-sd-swarm-macro-acid | 31 | `0x401bf8f0` | 245 999 | `0x401fb9df` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-sd-toy | 31 | `0x401bf8f0` | 228 368 | `0x401f7500` | `0x46700000` | 260 352 | model-tg-st |
| syntakt-tg-sd-toy-acid | 31 | `0x401bf8f0` | 146 324 | `0x401e3484` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-sd-toy-bits | 31 | `0x401bf8f0` | 235 728 | `0x401f91c0` | `0x46700000` | 264 448 | model-tg-st |
| syntakt-tg-sd-toy-bits-acid | 31 | `0x401bf8f0` | 151 218 | `0x401e47a2` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-sd-toy-bits-macro | 31 | `0x401bf8f0` | 235 068 | `0x401f8f2c` | `0x46700000` | 476 128 | model-tg-st |
| syntakt-tg-sd-toy-bits-macro-acid | 31 | `0x401bf8f0` | 240 286 | `0x401fa38e` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-sd-toy-bits-swarm | 31 | `0x401bf8f0` | 242 552 | `0x401fac68` | `0x46700000` | 269 056 | model-tg-st |
| syntakt-tg-sd-toy-bits-swarm-acid | 31 | `0x401bf8f0` | 157 416 | `0x401e5fd8` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-sd-toy-bits-swarm-macro | 31 | `0x401bf8f0` | 241 256 | `0x401fa758` | `0x46700000` | 476 128 | model-tg-st |
| syntakt-tg-sd-toy-bits-swarm-macro-acid | 31 | `0x401bf8f0` | 246 471 | `0x401fbbb7` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-sd-toy-macro | 31 | `0x401bf8f0` | 230 182 | `0x401f7c16` | `0x46700000` | 476 128 | model-tg-st |
| syntakt-tg-sd-toy-macro-acid | 31 | `0x401bf8f0` | 235 388 | `0x401f906c` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-sd-toy-swarm | 31 | `0x401bf8f0` | 242 008 | `0x401faa48` | `0x46700000` | 269 056 | model-tg-st |
| syntakt-tg-sd-toy-swarm-acid | 31 | `0x401bf8f0` | 157 153 | `0x401e5ed1` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-sd-toy-swarm-macro | 31 | `0x401bf8f0` | 241 008 | `0x401fa660` | `0x46700000` | 476 128 | model-tg-st |
| syntakt-tg-sd-toy-swarm-macro-acid | 31 | `0x401bf8f0` | 246 218 | `0x401fbaba` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-swarm | 31 | `0x401bf8f0` | 240 904 | `0x401fa5f8` | `0x46700000` | 269 056 | model-tg-st |
| syntakt-tg-swarm-acid | 31 | `0x401bf8f0` | 156 659 | `0x401e5ce3` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-swarm-macro | 31 | `0x401bf8f0` | 240 504 | `0x401fa468` | `0x46700000` | 476 128 | model-tg-st |
| syntakt-tg-swarm-macro-acid | 31 | `0x401bf8f0` | 245 725 | `0x401fb8cd` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-toy | 31 | `0x401bf8f0` | 227 780 | `0x401f72b4` | `0x46700000` | 260 352 | model-tg-st |
| syntakt-tg-toy-acid | 31 | `0x401bf8f0` | 146 055 | `0x401e3377` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-toy-bits | 31 | `0x401bf8f0` | 235 200 | `0x401f8fb0` | `0x46700000` | 264 448 | model-tg-st |
| syntakt-tg-toy-bits-acid | 31 | `0x401bf8f0` | 150 986 | `0x401e46ba` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-toy-bits-macro | 31 | `0x401bf8f0` | 234 836 | `0x401f8e44` | `0x46700000` | 476 128 | model-tg-st |
| syntakt-tg-toy-bits-macro-acid | 31 | `0x401bf8f0` | 240 042 | `0x401fa29a` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-toy-bits-swarm | 31 | `0x401bf8f0` | 242 032 | `0x401faa60` | `0x46700000` | 269 056 | model-tg-st |
| syntakt-tg-toy-bits-swarm-acid | 31 | `0x401bf8f0` | 157 185 | `0x401e5ef1` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-toy-bits-swarm-macro | 31 | `0x401bf8f0` | 241 024 | `0x401fa670` | `0x46700000` | 476 128 | model-tg-st |
| syntakt-tg-toy-bits-swarm-macro-acid | 31 | `0x401bf8f0` | 246 248 | `0x401fbad8` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-toy-macro | 31 | `0x401bf8f0` | 229 901 | `0x401f7afd` | `0x46700000` | 476 128 | model-tg-st |
| syntakt-tg-toy-macro-acid | 31 | `0x401bf8f0` | 235 126 | `0x401f8f66` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-toy-swarm | 31 | `0x401bf8f0` | 241 512 | `0x401fa858` | `0x46700000` | 269 056 | model-tg-st |
| syntakt-tg-toy-swarm-acid | 31 | `0x401bf8f0` | 156 927 | `0x401e5def` | `0x46700000` | 492 288 | model-tg-st |
| syntakt-tg-toy-swarm-macro | 31 | `0x401bf8f0` | 240 770 | `0x401fa572` | `0x46700000` | 476 128 | model-tg-st |
| syntakt-tg-toy-swarm-macro-acid | 31 | `0x401bf8f0` | 245 983 | `0x401fb9cf` | `0x46700000` | 492 288 | model-tg-st |
| macro-acid-tg | 32 | `0x401bf8f0` | 111 156 | `0x401dab24` | `0x46700000` | 492 288 | model-tg-st |
| macro-tg | 32 | `0x401bf8f0` | 104 628 | `0x401d91a4` | `0x46700000` | 324 576 | model-tg-st |
| acid-tg | 35 | `0x401bf8f0` | 11 812 | `0x401c2714` | `0x46700000` | 221 928 | model-tg-st |
| syntakt-meter | 90 | `0x401aa140` | 269 056 | `0x401ebc40` | `0x43000000` | 269 056 |  |
| syntakt-tg-meter | 91 | `0x401bf8f0` | 243 492 | `0x401fb014` | `0x46700000` | 269 056 | model-tg-st |
| syntakt-tg-profile | 92 | `0x401bf8f0` | 243 924 | `0x401fb1c4` | `0x46700000` | 269 056 | model-tg-st |

Fin la plus haute : `0x401fcfb1`, soit 12 367 o avant la limite (une charge posée sur une autre, comme les moteurs du Syntakt sur Model-TG, est déjà comptée à sa place dans la chaîne).

## 4. Points d'accroche (crochets) sur l'OS

Instructions de l'OS remplacées par un détour (`jsr`, `jmp`, `bsr.l`, `bra.l`) vers le code d'un mod, ou vers une autre fonction de l'OS. Deux mods installables ensemble ne peuvent détourner la même adresse qu'avec les mêmes octets (`check_overlaps.py`) ; sinon ils se déclarent `conflicts`. Les combinaisons de moteurs du Syntakt visent des décalages différents dans leur charge utile : une ligne par adresse et par zone visée, avec le nombre de cibles (moteurs résumés en familles : présents/total). Le rôle de chaque crochet est dans la note du mod.

| adresse | origine (hex) | détour | vers | mods | notes |
|---|---|---|---|---|---|
| `0x400004b2` | `4feffff048d700f0` | jmp | masque `0x4016cae8` +0x0 | acid, macro, macro-acid, sdvintage-7th, sdvintage-exact, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-vintage | notes/17, notes/18, notes/36 |
| `0x4000154a` | `4eb940044df8` | jsr | masque `0x40192ba4` +0x70 `midi_gate` | midi-live-both | notes/53 |
| `0x4000156a` | `4eb940044df8` | jsr | masque `0x40192ba4` +0x70 `midi_gate` | midi-live-both | notes/53 |
| `0x40001590` | `4eb940044df8` | jsr | masque `0x40192ba4` +0x70 `midi_gate` | midi-live-both | notes/53 |
| `0x400027e8` | `203c0030008072302540…` | jmp | OS `0x4019b136` | 6ch-multiout |  |
| `0x400027e8` | `203c0030008072302540…` | jmp | masque `0x4015c044` +0xd2 | 6ch-usbup | notes/36 |
| `0x400029e4` | `e7882239404a05e8d280…` | jmp | OS `0x4019b244` | 6ch-multiout |  |
| `0x400029e4` | `e7882239404a05e8d280…` | jmp | masque `0x4015c044` +0x1e0 | 6ch-usbup | notes/36 |
| `0x40002a06` | `206f002422414281d1c5…` | jmp | OS `0x4019b1e0` | 6ch-multiout |  |
| `0x40002a06` | `206f002422414281d1c5…` | jmp | masque `0x4015c044` +0x17c | 6ch-usbup | notes/36 |
| `0x40002a42` | `721320402004e3ace788…` | jmp | OS `0x4019b182` | 6ch-multiout |  |
| `0x40002a42` | `721320402004e3ace788…` | jmp | masque `0x4015c044` +0x11e | 6ch-usbup | notes/36 |
| `0x4000576c` | `45f940004e40` | lea a2 | masque `0x4016b6f8` +0x14 `usb_boot` | mod-settings | notes/72 |
| `0x40005f36` | `b2ac00286730` | jmp | masque `0x4018dba8` +0x0 | trigless-dim | notes/45 |
| `0x40006086` | `4ef94008e77e` | jmp | masque `0x4018dba8` +0x20 | trigless-dim | notes/45 |
| `0x40006a76` | `4eb940076ca2` | jsr | masque `0x40182b38` +0x94 `sr_leds` | step-rec | notes/73 |
| `0x40007120` | `4eb94006ba76` | jsr | masque `0x40182b38` +0x4a `sr_off` | step-rec | notes/73 |
| `0x4000721c` | `4eb94006ba76` | jsr | masque `0x40182b38` +0x2e `sr_on` | step-rec | notes/73 |
| `0x400081e4` | `4eb940082464` | jsr | masque `0x40182b38` +0xae `sr_tick` | step-rec | notes/73 |
| `0x400081f2` | `4eb940090f48` | jsr | masque `0x4018f4b4` +0x0 | level-pan-values | notes/44 |
| `0x4000a986` | `48d70cfc246f0030` | jsr | masque `0x40184808` +0x68 `ts_hook` | tempo-sync | notes/82 |
| `0x4000bae0` | `204031842a14` | jsr | masque `0x40182b38` +0x66 `sr_set` | step-rec | notes/73 |
| `0x4000c140` | `4e56ffe0202e000c` | jmp | masque `0x401835b8` +0x0 `lfo_dest` | lfo-plus | notes/56 |
| `0x4001413e` | `205242a72f0a` | jmp | charge utile (image) +0x10ed6 | model-tg, model-tg-st | notes/31, notes/86 |
| `0x400169f0` | `4feffff448d7040c` | jmp | charge utile (image) +0x4fba | model-tg, model-tg-st | notes/31, notes/86 |
| `0x4001a1c4` | `4eb940016086` | jsr | masque `0x4018a788` +0x16 | arp | notes/32 |
| `0x4001aa4e` | `4fefffe048d70cfc` | jmp | masque `0x4018f4b4` +0xc | level-pan-values | notes/44 |
| `0x4001b22a` | `4e56ffc048d73cfc` | jmp | masque `0x4018f4b4` +0x78 | level-pan-values | notes/44 |
| `0x4001c0d2` | `4e56ffa848d73c7c` | jsr | masque `0x4018d918` +0x0 | model-tg, model-tg-st | notes/31, notes/86 |
| `0x4001c27c` | `4eb94006b736` | jsr | masque `0x4016ea78` +0x0 | model-tg, model-tg-st | notes/31, notes/86 |
| `0x4001c3dc` | `4eb940025798` | jsr | masque `0x401784e8` +0xa8 `lfo_ctor` | lfo-plus | notes/56 |
| `0x4001d25e` | `4eb940016086` | jsr | masque `0x4018a788` +0x1a | arp | notes/32 |
| `0x4001d8ae` | `280f06840000003c` | jsr | masque `0x40192a24` +0x94 `ts_face` | tempo-sync | notes/82 |
| `0x4001d8d6` | `4eb940071a04` | jsr | masque `0x4019089c` +0x90 `ts_draw` | tempo-sync | notes/82 |
| `0x4001d91c` | `2045e78ced8891c1` | jsr | masque `0x4018d038` +0x7a `ts_dots` | tempo-sync | notes/82 |
| `0x4001e8da` | `202f0020226a0068` | jsr | charge utile (mémoire), 16 cibles selon la combinaison | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage | notes/18, notes/31, notes/36, notes/43, notes/54 |
| `0x4001eb50` | `2f024eb94005a4e8588f…` | jmp | masque `0x4018af88` +0x0 `lfo_learn` | lfo-plus | notes/56 |
| `0x4001f4f0` | `4e56ffac48d73cfc` | jsr | masque `0x4016ea78` +0x18 | model-tg, model-tg-st | notes/31, notes/86 |
| `0x4001f97e` | `4e56ffd848d73c0c` | jsr | masque `0x4016ea78` +0x40 | model-tg, model-tg-st | notes/31, notes/86 |
| `0x40021f56` | `2f034e944879404a8cb8…` | jsr | charge utile (image) +0x4f1a | model-tg, model-tg-st | notes/31, notes/86 |
| `0x4002249c` | `4eb940072490` | jsr | masque `0x4015c044` +0x28 `th_press` | trig-hold | notes/33 |
| `0x400224ee` | `2f034eb9400724a0` | jmp | cave `0x401489fa` +0x0 | model-tg, model-tg-st, trig-preview | notes/31, notes/34, notes/86 |
| `0x40022d44` | `4eb940072460` | jsr | masque `0x4015c044` +0x3a `th_hold` | trig-hold | notes/33 |
| `0x40022da6` | `4eb94006b736` | jsr | masque `0x4015c044` +0x6c `th_release` | trig-hold | notes/33 |
| `0x4002351a` | `2f024eb9400740ca` | jmp | cave `0x40148328` +0x0 | latching-mute, model-tg, model-tg-st | notes/31, notes/86 |
| `0x400243d6` | `700ab084673e` | jmp | masque `0x40182b38` +0x0 `sr_key` | step-rec | notes/73 |
| `0x40025e10` | `4feffff02f0a` | jmp | masque `0x401784e8` +0xf6 `lfo_gate` | lfo-plus | notes/56 |
| `0x400262ac` | `4fef000c200f` | jmp | masque `0x4018af88` +0x7c `lfo_led` | lfo-plus | notes/56 |
| `0x4002d480` | `4cef7c7c0018` | jmp | masque `0x4016cae8` +0xc0 | arp | notes/32 |
| `0x4002f7d8` | `4cef7c7c0018` | jmp | charge utile (image) +0x11382 | model-tg, model-tg-st | notes/31, notes/86 |
| `0x40032aee` | `4cef7c7c0018` | jmp | charge utile (image) +0xd448 | model-tg, model-tg-st | notes/31, notes/86 |
| `0x4003560a` | `4eb940044df84a8057c0…` | jmp | masque `0x40192ba4` +0x0 `midi_key` | midi-live-both | notes/53 |
| `0x4003c99a` | `4cee3cfcff98` | jmp | masque `0x4016b6f8` +0x0 `cfg_tail` | mod-settings | notes/72 |
| `0x4004486c` | `4eb94005a274` | jsr | masque `0x40166760` +0xaa `tf_boot` | track-filter | notes/47 |
| `0x4004a448` | `242f0018262f` | jmp | masque `0x40168a84` +0x0 | model-tg, model-tg-st | notes/31, notes/86 |
| `0x4004df40` | `704c222f0004` | jmp | charge utile (mémoire), 3 cibles selon la combinaison | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage | notes/18, notes/31, notes/36, notes/43, notes/54 |
| `0x4004df5c` | `7206202f0004` | jmp | charge utile (mémoire), 9 cibles selon la combinaison | acid, macro, macro-acid, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-vintage | notes/18, notes/36 |
| `0x4004df5c` | `4ef9401ae84e` | jmp | charge utile (mémoire), 8 cibles selon la combinaison | acid-tg, macro-acid-tg, macro-tg, syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn | notes/31, notes/36, notes/43, notes/54 |
| `0x4004df5c` | `7206202f0004` | jmp | charge utile (image) +0x470e | model-tg, model-tg-st | notes/31, notes/86 |
| `0x4004df76` | `7205202f0004` | jmp | charge utile (mémoire), 9 cibles selon la combinaison | acid, macro, macro-acid, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-vintage | notes/18, notes/36 |
| `0x4004df76` | `4ef9401b278e` | jmp | charge utile (mémoire), 8 cibles selon la combinaison | acid-tg, macro-acid-tg, macro-tg, syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn | notes/31, notes/36, notes/43, notes/54 |
| `0x4004df76` | `7205202f0004` | jmp | charge utile (image) +0x864e | model-tg, model-tg-st | notes/31, notes/86 |
| `0x4004dfa2` | `704c222f0004` | jmp | charge utile (mémoire), 3 cibles selon la combinaison | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage | notes/18, notes/31, notes/36, notes/43, notes/54 |
| `0x4004dfda` | `203c00000100` | jmp | masque `0x4018b9c8` +0x0 `ts_dfmt` | tempo-sync | notes/82 |
| `0x4004e00e` | `203cffffc000` | jmp | masque `0x40183408` +0x66 `ts_lfmt` | tempo-sync | notes/82 |
| `0x40053a6c` | `4fefff8048d77cfc42af…` | jsr | OS `0x4008e6ba` | boot-anim | notes/39 |
| `0x40056610` | `4fefffd848d73cfc` | jmp | charge utile (image) +0xdc1a | model-tg, model-tg-st | notes/31, notes/86 |
| `0x40056b38` | `4878000448798000b990` | jsr | charge utile (image) +0xab2c | model-tg, model-tg-st | notes/31, notes/86 |
| `0x400581ae` | `716801ac41f940149310` | jsr | masque `0x401829b8` +0x0 `ts_audio` | tempo-sync | notes/82 |
| `0x400584f6` | `203c8000100c` | jsr | masque `0x40184808` +0x0 `ts_smooth` | tempo-sync | notes/82 |
| `0x400587f6` | `4eb940091f20` | jsr | masque `0x4018a788` +0x1b2 | arp | notes/32 |
| `0x40058ca0` | `a93c00000020` | jsr | masque `0x4015c044` +0x1f8 | 6ch-usbup, acid, macro, macro-acid, mod-settings, model-tg, model-tg-st, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31) | notes/31, notes/36, notes/72, notes/86 |
| `0x40058e28` | `72ff242a0008202a000c` | jsr | masque `0x4018a788` +0x0 | arp | notes/32 |
| `0x4005910e` | `4aaa0030670c2002` | jsr | masque `0x40183118` +0x0 `pv_copy` | sample-preview, sample-preview-st | notes/46 |
| `0x40059382` | `4eb94005979e` | jsr | charge utile (mémoire), 14 cibles selon la combinaison | syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn | notes/31, notes/36 |
| `0x40059392` | `4eb940002912` | jsr | masque `0x4015c044` +0x292 | 6ch-usbup, acid, macro, macro-acid, mod-settings, model-tg, model-tg-st, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31) | notes/31, notes/36, notes/72, notes/86 |
| `0x400593ce` | `4eb940002912` | jsr | masque `0x4015c044` +0x292 | 6ch-usbup, acid, macro, macro-acid, mod-settings, model-tg, model-tg-st, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31) | notes/31, notes/36, notes/72, notes/86 |
| `0x400597c6` | `4eb940091ab2` | jsr | masque `0x40186238` +0x0 `lfo_audio` | lfo-plus | notes/56 |
| `0x4005981e` | `4eb9401b7180` | jsr | charge utile (mémoire) +0x33520 | syntakt-tg-* (1/33) | notes/31 |
| `0x40059852` | `4eb940056f58` | jsr | masque `0x40168da4` +0x0 | model-tg, model-tg-st | notes/31, notes/86 |
| `0x40059852` | `4eb940056f58` | jsr | masque `0x4014ab5c` +0x0 `tf_post` | track-filter | notes/47 |
| `0x40059872` | `4eb9401b7b78` | jsr | charge utile (mémoire) +0x33550 | syntakt-tg-* (1/33) | notes/31 |
| `0x40059dea` | `76ff781533c38c000000` | jmp | masque `0x40192734` +0x0 `td_led` | trigless-dim | notes/45 |
| `0x4005a31a` | `20065286eb88` | jmp | charge utile (mémoire), 8 cibles selon la combinaison | acid-tg, macro-acid-tg, macro-tg, syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn | notes/31, notes/36, notes/43, notes/54 |
| `0x4005a340` | `7005b085643e` | jmp | charge utile (mémoire), 16 cibles selon la combinaison | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage | notes/31, notes/36, notes/43, notes/54 |
| `0x4005a4ea` | `202f0004b280` | jmp | masque `0x4018ff64` +0x0 `lfo_id2k` | lfo-plus | notes/56 |
| `0x4005a50a` | `724c202f0004` | jmp | charge utile (mémoire), 15 cibles selon la combinaison | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage | notes/31, notes/36, notes/43, notes/54 |
| `0x4005a6a6` | `4ef9401ae8fc` | jmp | charge utile (mémoire), 8 cibles selon la combinaison | acid-tg, macro-acid-tg, macro-tg, syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn | notes/31, notes/36, notes/43, notes/54 |
| `0x4005a6a6` | `7205b2826430` | jmp | charge utile (image) +0x47bc | model-tg, model-tg-st | notes/31, notes/86 |
| `0x4005a6b6` | `4ef9401ae936` | jmp | charge utile (mémoire), 8 cibles selon la combinaison | acid-tg, macro-acid-tg, macro-tg, syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn | notes/31, notes/36, notes/43, notes/54 |
| `0x4005a6b6` | `eb8a41f940a7` | jmp | charge utile (image) +0x47f6 | model-tg, model-tg-st | notes/31, notes/86 |
| `0x4005a8f0` | `7405b4816532` | jmp | charge utile (mémoire), 3 cibles selon la combinaison | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage | notes/18, notes/31, notes/36, notes/43, notes/54 |
| `0x4005aa22` | `202f000cb481` | jmp | masque `0x4018b1a8` +0x2c `lfo_plk_load` | lfo-plus | notes/56 |
| `0x4005aa34` | `7417b480640c` | jmp | masque `0x40166760` +0x8a `tf_conv` | track-filter | notes/47 |
| `0x4005aecc` | `4feffff448d7` | jmp | charge utile (image) +0x9b82 | model-tg, model-tg-st | notes/31, notes/86 |
| `0x4005aecc` | `4feffff448d7` | jmp | masque `0x40166760` +0x0 `tf_load` | track-filter | notes/47 |
| `0x4005af1c` | `41f94010eea8` | jsr | masque `0x401784e8` +0x0 `lfo_unpack` | lfo-plus | notes/56 |
| `0x4005af3e` | `712a001c20310c00` | jsr | masque `0x401784e8` +0x12 `lfo_tail` | lfo-plus | notes/56 |
| `0x4005afa0` | `4feffff448d7` | jmp | charge utile (image) +0x9ae2 | model-tg, model-tg-st | notes/31, notes/86 |
| `0x4005afa0` | `4feffff448d7` | jmp | masque `0x4016616c` +0x0 `tf_save2` | track-filter | notes/47 |
| `0x4005b028` | `356b005e005c` | jsr | masque `0x40186238` +0x82 `lfo_pack` | lfo-plus | notes/56 |
| `0x4005b054` | `4feffff448d7` | jmp | charge utile (image) +0x9afc | model-tg, model-tg-st | notes/31, notes/86 |
| `0x4005b054` | `4feffff448d7` | jmp | masque `0x4016616c` +0x1c `tf_save1` | track-filter | notes/47 |
| `0x4005b0dc` | `356b005e005c` | jsr | masque `0x40186238` +0x82 `lfo_pack` | lfo-plus | notes/56 |
| `0x4005b2ae` | `4fefffe448d77c0c` | jmp | masque `0x40189618` +0x0 `kit_save` | lfo-plus | notes/56 |
| `0x4005b9c6` | `16b5480317420001` | jsr | masque `0x4018b1a8` +0x0 `lfo_plk_save` | lfo-plus | notes/56 |
| `0x4005d080` | `4fefffdc48d77c3c` | jmp | masque `0x40189618` +0x74 `kit_load` | lfo-plus | notes/56 |
| `0x400618e2` | `e18b35430026` | jsr | masque `0x401784e8` +0x94 `lfo_init` | lfo-plus | notes/56 |
| `0x4007240c` | `206f00042028` | jmp | charge utile (image) +0x4828 | model-tg, model-tg-st | notes/31, notes/86 |
| `0x40081474` | `b08365000178` | jmp | charge utile (image) +0x1102e | model-tg, model-tg-st | notes/31, notes/86 |
| `0x4008171e` | `4ef9401b3214` | jmp | masque `0x40185968` +0x0 `pv_note` | sample-preview, sample-preview-st | notes/46 |
| `0x4008173c` | `b083650001ce` | jmp | charge utile (image) +0x10fe4 | model-tg, model-tg-st | notes/31, notes/86 |
| `0x40081908` | `4ebaf2ec588f` | jsr | masque `0x40189930` +0x102 | arp | notes/32 |
| `0x40084b8e` | `487800222d48` | jmp | charge utile (image) +0x9dbc | model-tg, model-tg-st | notes/31, notes/86 |
| `0x40084c14` | `721b4fef0028` | jmp | charge utile (image) +0x9e42 | model-tg, model-tg-st | notes/31, notes/86 |
| `0x4008f1f0` | `226f0004206f0008` | jmp | masque `0x40185308` +0x9c `kit_copy` | lfo-plus | notes/56 |
| `0x40091b38` | `362c0006e4a7` | jsr | masque `0x40184af8` +0x0 `ts_lfo` | tempo-sync | notes/82 |
| `0x40094c9a` | `71aa00084fef0020` | jmp | charge utile (image) +0xd62a | model-tg, model-tg-st | notes/31, notes/86 |
| `0x400a2638` | `eb8c48780001` | jmp | charge utile (mémoire), 17 cibles selon la combinaison | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage | notes/18, notes/31, notes/36, notes/43, notes/54 |
| `0x400a26a2` | `7850428545f9` | jmp | charge utile (mémoire), 13 cibles selon la combinaison | acid-tg, macro-acid, macro-acid-tg, macro-tg, syntakt-* (27/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn | notes/31, notes/36, notes/43, notes/54 |
| `0x400a4dc4` | `700541e8000a` | jmp | charge utile (mémoire), 17 cibles selon la combinaison | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage | notes/18, notes/31, notes/36, notes/43, notes/54 |
| `0x400a5588` | `2eaa028c4e95` | jmp | masque `0x401904b4` +0x2a `ml_row` | multiline-browser | notes/40 |
| `0x400a55a4` | `4fef001c226e` | jmp | masque `0x401904b4` +0x5e `ml_after` | multiline-browser | notes/40 |
| `0x400a5612` | `20522f0a20680040` | jsr | masque `0x401904b4` +0x10 `ml_bound` | multiline-browser | notes/40 |
| `0x400a576e` | `4eb940071da4` | jsr | masque `0x401904b4` +0x102 `ml_icon` | multiline-browser | notes/40 |
| `0x400a578c` | `2d40ffe020454e91` | jsr | masque `0x40152d38` +0x0 `ml_name` | multiline-browser | notes/40 |
| `0x400a6426` | `4eb9400a3052` | jsr | masque `0x40185c58` +0x0 `pv_parse` | sample-preview, sample-preview-st | notes/46 |
| `0x400a6816` | `206800504e90` | jsr | charge utile (image) +0x116de | model-tg, model-tg-st | notes/31, notes/86 |
| `0x400a7da8` | `2d41003c4a936730` | jmp | charge utile (image) +0x1f2a | model-tg, model-tg-st | notes/31, notes/86 |
| `0x400a7dfe` | `b08465224ef9` | jmp | charge utile (mémoire), 11 cibles selon la combinaison | acid-tg, macro-acid-tg, macro-tg, syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn | notes/31, notes/36, notes/43, notes/54 |
| `0x400a7dfe` | `b08465222046` | jmp | charge utile (mémoire), 7 cibles selon la combinaison | syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31) | notes/36 |
| `0x400a7e02` | `204622704c002f0a2f0e…` | jmp | charge utile (image) +0x2918 | model-tg, model-tg-st | notes/31, notes/86 |
| `0x400a7e24` | `269522434280` | jmp | charge utile (mémoire), 9 cibles selon la combinaison | syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn | notes/31, notes/36 |
| `0x400a8906` | `287c8000caa8` | jmp | charge utile (image) +0xde1a | model-tg, model-tg-st | notes/31, notes/86 |
| `0x400a956c` | `2f0a226f00084280` | jmp | charge utile (image) +0xddfa | model-tg, model-tg-st | notes/31, notes/86 |
| `0x400a98c4` | `22115c8124730800` | jmp | charge utile (image) +0xdcfe | model-tg, model-tg-st | notes/31, notes/86 |
| `0x400a9daa` | `4feffff448d70c04` | jmp | charge utile (image) +0xdd1c | model-tg, model-tg-st | notes/31, notes/86 |
| `0x400d97f8` | `2f4a0008245f` | jmp | masque `0x401784e8` +0xcc `lfo_dtor` | lfo-plus | notes/56 |

## 5. Pointeurs réécrits

Constantes 32 bits de l'OS (tables de fonctions, données) qui pointent maintenant vers le code ou les données d'un mod. Même regroupement qu'au §4.

| adresse | ancien | vers | mods |
|---|---|---|---|
| `0x40000532` | `401bf40c` | masque `0x4016cae8` +0x0 | acid-tg, macro-acid-tg, macro-tg, syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn |
| `0x4000a94e` | `4010dce0` | charge utile (mémoire) +0x34000 | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage |
| `0x4000b214` | `4010dce0` | charge utile (mémoire) +0x34000 | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage |
| `0x4000b236` | `4010dce0` | charge utile (mémoire) +0x34000 | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage |
| `0x4000b3ec` | `4010dce0` | charge utile (mémoire) +0x34000 | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage |
| `0x4000b47e` | `4010dce0` | charge utile (mémoire) +0x34000 | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage |
| `0x4000b522` | `4010dce0` | charge utile (mémoire) +0x34000 | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage |
| `0x4000b662` | `4010dce0` | charge utile (mémoire) +0x34000 | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage |
| `0x4000b6f4` | `4010dce0` | charge utile (mémoire) +0x34000 | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage |
| `0x4000b790` | `4010dce0` | charge utile (mémoire) +0x34000 | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage |
| `0x4001d5ee` | `4010dce0` | charge utile (mémoire) +0x34000 | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage |
| `0x4001d902` | `4010dce0` | charge utile (mémoire) +0x34000 | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage |
| `0x4001e032` | `4010dce0` | charge utile (mémoire) +0x34000 | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage |
| `0x4001f32e` | `4010dce0` | charge utile (mémoire) +0x34000 | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage |
| `0x40022a84` | `4010dce0` | charge utile (mémoire) +0x34000 | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage |
| `0x40022b06` | `4010dce0` | charge utile (mémoire) +0x34000 | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage |
| `0x40029e88` | `4010dce0` | charge utile (mémoire) +0x34000 | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage |
| `0x4002b438` | `4010dce0` | charge utile (mémoire) +0x34000 | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage |
| `0x40046d64` | `4010dce0` | charge utile (mémoire) +0x34000 | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage |
| `0x4004e32e` | `4010dce0` | charge utile (mémoire) +0x34000 | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage |
| `0x4005a2be` | `40a79418` | charge utile (mémoire), 5 valeurs selon la combinaison | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage |
| `0x4005a2de` | `4010dce0` | charge utile (mémoire) +0x34000 | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage |
| `0x4005a322` | `40a79418` | charge utile (mémoire), 5 valeurs selon la combinaison | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage |
| `0x4005a390` | `40a79418` | charge utile (mémoire), 5 valeurs selon la combinaison | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage |
| `0x4005a3aa` | `40a7ada4` | charge utile (mémoire), 5 valeurs selon la combinaison | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage |
| `0x4005a4f4` | `4010dce0` | charge utile (mémoire) +0x34000 | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage |
| `0x4005a516` | `4010dce0` | charge utile (mémoire) +0x34000 | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage |
| `0x4005a538` | `4010dce0` | charge utile (mémoire) +0x34000 | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage |
| `0x4005a562` | `4010dce0` | charge utile (mémoire) +0x34000 | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage |
| `0x4005a59a` | `4010dce0` | charge utile (mémoire) +0x34000 | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage |
| `0x4005a5d8` | `4010dce0` | charge utile (mémoire) +0x34000 | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage |
| `0x4005a60a` | `4010dce0` | charge utile (mémoire) +0x34000 | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage |
| `0x4005a634` | `4010dce0` | charge utile (mémoire) +0x34000 | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage |
| `0x4005a67a` | `4010dce8` | charge utile (mémoire) +0x34008 | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage |
| `0x4005a6ba` | `40a79418` | charge utile (mémoire), 4 valeurs selon la combinaison | acid, macro, macro-acid, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-vintage |
| `0x4005a6f0` | `40a79418` | charge utile (mémoire), 5 valeurs selon la combinaison | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage |
| `0x4005a77e` | `4010dd00` | charge utile (mémoire) +0x34020 | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage |
| `0x4005a78a` | `4010dd00` | charge utile (mémoire) +0x34020 | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage |
| `0x4005a7bc` | `4010dce0` | charge utile (mémoire) +0x34000 | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage |
| `0x4005a7dc` | `4010dce0` | charge utile (mémoire) +0x34000 | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage |
| `0x4005a804` | `4010dce0` | charge utile (mémoire) +0x34000 | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage |
| `0x4005a826` | `4010dce0` | charge utile (mémoire) +0x34000 | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage |
| `0x4005a848` | `4010dce0` | charge utile (mémoire) +0x34000 | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage |
| `0x4005a86a` | `4010dce0` | charge utile (mémoire) +0x34000 | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage |
| `0x4005a912` | `40a7ada4` | charge utile (mémoire), 5 valeurs selon la combinaison | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage |
| `0x4005b998` | `4010ee4c` | masque `0x40160e6c` +0x7c | track-filter |
| `0x4005baca` | `4010ee4c` | masque `0x40160e6c` +0x7c | track-filter |
| `0x400a2614` | `401177e4` | charge utile (mémoire) +0x33800 | acid, macro, macro-acid, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-vintage |
| `0x400a2614` | `401bf54e` | charge utile (mémoire), 2 valeurs selon la combinaison | acid-tg, macro-acid-tg, macro-tg, syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn |
| `0x400a7d6c` | `40118628` | charge utile (mémoire), 9 valeurs selon la combinaison | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, sdvintage-7th, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn, syntakt-vintage |
| `0x400a7dc4` | `40118640` | charge utile (mémoire), 9 valeurs selon la combinaison | acid, acid-tg, macro, macro-acid, macro-acid-tg, macro-tg, syntakt-* (32/32), syntakt-*-acid (31/31), syntakt-*-macro (31/31), syntakt-*-macro-acid (31/31), syntakt-tg-* (33/33), syntakt-tg-*-acid (31/31), syntakt-tg-*-macro (31/31), syntakt-tg-*-macro-acid (31/31), syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn |
| `0x400a7e16` | `40118610` | charge utile (mémoire), 2 valeurs selon la combinaison | acid, macro, macro-acid, sdvintage-7th, syntakt-vintage |
| `0x400fd150` | `4000ae20` | masque `0x40185f48` +0x5a | lfo-plus |
| `0x400fd190` | `4000ba7a` | masque `0x40185f48` +0x6e | lfo-plus |
| `0x401005a8` | `4001e814` | masque `0x401625bc` +0x0 | track-filter |
| `0x401016e4` | `40024e86` | masque `0x40173848` +0x0 | lfo-plus |
| `0x401016ec` | `400426fa` | masque `0x401835b8` +0xa2 | lfo-plus |
| `0x40118614` | `400ab6e8` | charge utile (mémoire) +0x31196 | sdvintage-exact |
| `0x40118614` | `400ab6e8` | masque `0x4018a788` +0x0 | sdvintage-snare |
| `0x4011862c` | `400ab3b0` | charge utile (mémoire) +0x31000 | sdvintage-exact |
| `0x4011862c` | `400ab3b0` | masque `0x4016cae8` +0x0 | sdvintage-snare |

## 6. Données sauvegardées (déclaré d'après les notes)

Ce que les écritures ne montrent pas : les octets des structures sauvegardées (pattern, projet) qu'un mod s'attribue. Un nouveau mod qui en prend un l'ajoute à `DECLARED` dans `tools/registry.py`, avec sa note. La mémoire où tournent les charges utiles est au §3 ; l'état que les mods gardent dans leurs masques, au §1.

| mod | ce qu'il s'attribue | source |
|---|---|---|
| arp | octet +512 de chaque piste dans le pattern : sens de l'arpège et octaves (inutilisé par l'OS, sauvegardé avec le pattern) | notes/32 §4 |
| lfo-plus | octets +88..+91 de l'enregistrement d'un son : LFO 2 empaqueté (format de DavidCaruso) ; mémoire 0x4233f000..0x4233f49b, au-dessus du BSS de l'OS, remise à zéro au premier usage | notes/56 §3 |
| step-rec | mémoire 0x4233e800..0x4233e8ff, dans le trou libre au-dessus du BSS de l'OS (0x423380b0..0x4233efff, notes/56 §3.5.2) : les variables du step record, posées à son entrée (seul sr_active, dans un masque, vaut 0 au démarrage) | notes/73 §3 |
| mod-settings | octets 0x404e9b80..0x404e9b8f du bloc des réglages de l'OS (0x404e9b10, 272 o, flash 0x78000), hors de sa somme de contrôle : l'enregistrement « MODS » des réglages des mods (0x404e9b63..0x404e9c0f n'est ni lu ni écrit par l'OS) | notes/72 §3 |
| mod-settings | octets de l'OS réécrits pendant qu'il tourne (« runtime », vérifié par `check_overlaps.py`) : `0x4000253b` (2 o), `0x40002564` (3 o), `0x400027b3` (2 o), `0x400027d3` (5 o), `0x400027e8` (23 o), `0x4000281f` (2 o), `0x400029b9` (2 o), `0x400029d2` (6 o), `0x400029e4` (11 o), `0x40002a06` (25 o), `0x40002a42` (11 o), `0x40002ceb` (2 o), `0x4019b2fa` (2 o), `0x4019b387` (2 o), `0x4019b397` (2 o) | notes/72 |

## 7. Ce que chaque mod touche

Nombre d'écritures de chaque sorte (une plage pour une famille de moteurs).

| mod | écritures | patchs | crochets | pointeurs | masques | redirections | caves | charge utile (image) | note |
|---|---|---|---|---|---|---|---|---|---|
| latching-mute | 8 | 3 | 1 | 0 | 0 | 0 | 4 |  |  |
| trig-preview | 6 | 0 | 1 | 0 | 0 | 0 | 5 |  | notes/34 |
| browser-scroll | 5 | 1 | 0 | 0 | 0 | 0 | 4 |  |  |
| 6ch-multiout | 29 | 25 | 4 | 0 | 0 | 0 | 0 |  |  |
| 6ch-usbup | 25 | 12 | 7 | 0 | 5 | 1 | 0 |  | notes/36 |
| mod-settings | 28 | 1 | 5 | 0 | 13 | 9 | 0 |  | notes/72 |
| sdvintage-snare | 10 | 4 | 0 | 2 | 2 | 2 | 0 |  | notes/16 |
| sdvintage-exact | 9 | 4 | 1 | 2 | 1 | 1 | 0 | 205 200 o | notes/17 |
| sdvintage-7th | 116 | 58 | 9 | 47 | 1 | 1 | 0 | 218 208 o | notes/18 |
| syntakt-vintage | 117 | 57 | 11 | 47 | 1 | 1 | 0 | 218 560 o |  |
| syntakt-* (32 tweaks) | 124 | 56–57 | 16–17 | 47 | 2 | 2 | 0 | 260 352–269 056 o | notes/36 |
| syntakt-*-acid (31 tweaks) | 124 | 56 | 17 | 47 | 2 | 2 | 0 | 145 736–157 290 o | notes/36 |
| syntakt-*-macro (31 tweaks) | 124 | 56 | 17 | 47 | 2 | 2 | 0 | 229 568–241 114 o | notes/36 |
| syntakt-*-macro-acid (31 tweaks) | 124 | 56 | 17 | 47 | 2 | 2 | 0 | 234 795–246 316 o | notes/36 |
| macro | 122 | 56 | 14 | 48 | 2 | 2 | 0 | 104 196 o | notes/36 |
| macro-acid | 122 | 55 | 15 | 48 | 2 | 2 | 0 | 110 804 o | notes/36 |
| acid | 122 | 56 | 14 | 48 | 2 | 2 | 0 | 11 380 o | notes/36 |
| model-tg | 196 | 111 | 38 | 0 | 16 | 16 | 15 | 87 984 o | notes/86 |
| model-tg-st | 196 | 111 | 38 | 0 | 16 | 16 | 15 | 87 984 o | notes/31 |
| syntakt-tg-* (33 tweaks) | 117–119 | 51 | 17–19 | 47 | 1 | 1 | 0 | 227 780–243 924 o | notes/31, notes/36 |
| syntakt-tg-*-acid (31 tweaks) | 117 | 51 | 17 | 47 | 1 | 1 | 0 | 146 055–157 597 o | notes/36 |
| syntakt-tg-*-macro (31 tweaks) | 117 | 51 | 17 | 47 | 1 | 1 | 0 | 229 901–241 446 o | notes/36 |
| syntakt-tg-*-macro-acid (31 tweaks) | 117 | 51 | 17 | 47 | 1 | 1 | 0 | 235 126–246 655 o | notes/36 |
| syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn | 117 | 51 | 17 | 47 | 1 | 1 | 0 | 251 585 o | notes/36 |
| macro-acid-tg | 114 | 50 | 15 | 47 | 1 | 1 | 0 | 111 156 o | notes/54 |
| macro-tg | 114 | 50 | 15 | 47 | 1 | 1 | 0 | 104 628 o | notes/43 |
| sample-preview | 11 | 0 | 3 | 0 | 4 | 4 | 0 |  | notes/46 |
| sample-preview-st | 11 | 0 | 3 | 0 | 4 | 4 | 0 |  | notes/46 |
| acid-tg | 114 | 50 | 15 | 47 | 1 | 1 | 0 | 11 812 o | notes/54 |
| arp | 14 | 0 | 6 | 0 | 4 | 4 | 0 |  | notes/32 |
| trig-hold | 5 | 0 | 3 | 0 | 1 | 1 | 0 |  | notes/33 |
| tempo-max | 12 | 12 | 0 | 0 | 0 | 0 | 0 |  | notes/38 |
| boot-anim | 1 | 0 | 1 | 0 | 0 | 0 | 0 |  | notes/39 |
| multiline-browser | 19 | 10 | 5 | 0 | 2 | 2 | 0 |  | notes/40 |
| step-rec | 24 | 0 | 6 | 0 | 9 | 9 | 0 |  | notes/73 |
| level-pan-values | 8 | 1 | 3 | 0 | 2 | 2 | 0 |  | notes/44 |
| trigless-dim | 8 | 1 | 3 | 0 | 2 | 2 | 0 |  | notes/45 |
| track-filter | 40 | 1 | 6 | 3 | 15 | 15 | 0 |  | notes/47 |
| midi-both | 3 | 3 | 0 | 0 | 0 | 0 | 0 |  | notes/53 |
| midi-live-both | 6 | 0 | 4 | 0 | 1 | 1 | 0 |  | notes/53 |
| lfo-plus | 48 | 0 | 18 | 4 | 13 | 13 | 0 |  | notes/56 |
| tempo-sync | 33 | 0 | 9 | 0 | 12 | 12 | 0 |  | notes/82 |

