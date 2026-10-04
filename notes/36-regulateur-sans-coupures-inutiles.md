# 36 — Moins de notes coupées, et plus léger

Travail du 04/10/2026, à la demande de l'utilisateur : « Dans mes projets avec 6 pistes actives en même temps, j'ai
souvent la dernière qui est coupée. J'aimerais que tu fasses un gros travail d'optimisation et de performance, tout en
gardant bien les fonctionnalités. […] Utilise toutes tes capacités pour rendre tout ça le plus léger possible. »

Adresses : VA de l'OS 1.13. Firmware visé : 6ch-usbup + Model-TG + les 5 moteurs du Syntakt + trig-hold + arpégiateur
(celui essayé sur la machine le 04/10/2026, [35 §7](35-glitches-usb-multipiste.md)).

## 0. En bref

| | État |
|---|---|
| Qui coupe la piste : le régulateur de charge des moteurs du Syntakt ([25](25-regulateur-de-charge.md), [30](30-regulateur-charge-soutenue.md)) | `[FAIT]` lu dans son code (§1) |
| Défauts de sa règle : il réagit à un bloc lourd isolé, déjà passé (c'est lui qui coupe) ; sa règle de charge soutenue n'agissait jamais (arrondi de la moyenne lente) ; il choisit la voix la plus faible avant le mixeur | `[FAIT]` (§1) |
| Où passe le temps de la boucle des voix (émulation, par fonction) | `[FAIT]` (§2) |
| Nouvelle règle, écrite en assembleur à la place du code compilé (sans GCC 16.2) | `[FAIT]` (§3, §5) |
| Plus léger : suivi des voix par le régulateur avec Model-TG, division des pistes par 2 dans la boucle des voix de l'OS | `[FAIT]` (§4) |
| Preuves en émulation | `[FAIT]` (§6) |
| Essai sur la machine | `[À FAIRE]` (§8) |

## 1. Pourquoi la dernière piste est coupée `[FAIT]`

Le régulateur ([25](25-regulateur-de-charge.md), règle de [30](30-regulateur-charge-soutenue.md)) est dans la passerelle
des moteurs du Syntakt (`machines/syntakt_bridge/bridge_engines.c`, `audio_end` et `govern`). Il n'existe que dans les
firmwares avec les moteurs du Syntakt, avec ou sans Model-TG. À chaque bloc, il mesure la fonction audio (`0x4005979e`)
et, s'il le juge nécessaire, éteint en fondu une ou deux voix, jusqu'à leur prochain trig.

**Défaut 1 : un bloc lourd isolé suffit.** Tout bloc au-dessus de 93 % fait éteindre une voix (`PEAK`). Or les pics sont
des blocs isolés : un pas où plusieurs pistes partent (le séquenceur prend jusqu'à 7 % du bloc, [31 §7](31-model-tg.md)),
ou les caches vidés par l'interface entre deux blocs (+4,6 points, [31 §7](31-model-tg.md)). Relevés de l'utilisateur
avec 6 pistes et Model-TG : 90 à 93 % de pic pour 79 à 80 % de moyenne ([31 §6-7](31-model-tg.md)). Le bloc mesuré est
déjà passé : éteindre une voix ne le rattrape pas, et le suivant est d'ordinaire bien plus léger. La coupure ne sert à
rien, mais elle s'entend.

**Défaut 2 : la règle de charge soutenue n'agissait jamais.** `gov_slow += (gov_load - gov_slow) >> 8`, en 1/256 de
bloc : l'écart (moins de 256) divisé par 256 vaut 0, ou -1 quand la charge est sous la moyenne. Partie de 0 au démarrage,
la moyenne lente ne monte donc pas (sauf d'une unité par bloc au-dessus de 100 %) : `STEAL` (86 % soutenus,
[30](30-regulateur-charge-soutenue.md)) ne s'est jamais déclenché sur la machine. Les tests de la note 30 posaient la
moyenne lente à 88 % d'office, ce qui le masquait ; le compteur des firmwares de diagnostic a sa propre moyenne, juste.
Seul le défaut 1 coupait des voix. (La moyenne rapide, `>> 3`, a le même travers en plus petit : elle reste jusqu'à
7/256 sous la charge quand celle-ci monte.)

Et si elle avait agi : une fois une voix éteinte, la moyenne lente met des centaines de blocs à redescendre, et le temps
à libérer (« moyenne lente − 82 % ») ne tenait pas compte de la voix partie : une autre aurait été éteinte quelques
blocs plus tard, et ainsi de suite.

**Défaut 3 : la voix choisie.** La « plus faible » est celle dont la crête de sortie est la plus basse, avant le mixeur :
sans tenir compte de son volume, de ses envois, ni d'un mute. Une piste discrète par nature (charleston, SY SWARM aux
réglages par défaut, une note longue en fin de decay) part toujours la première, même montée au mixeur ; une piste mutée
mais encore calculée (avec l'audio 6 canaux, [35 §3](35-glitches-usb-multipiste.md)) n'est pas préférée. Et seules les
notes de plus de 16 blocs (11 ms) peuvent partir : sur un pas où 5 pistes repartent, la seule qui tient une note longue
est la seule candidate. D'où « souvent la dernière ».

## 2. Où passe le temps de la boucle des voix `[FAIT]`

Émulation de la vraie boucle des voix (`0x400a7d4a`), version combinée Model-TG + 5 moteurs, 6 pistes qui sonnent
(KICK, SDVtg, SYToy, PERC, TONE, SYSwm), instructions par bloc, attribuées par fonction (symboles de Model-TG tirés de son
ELF, fonctions de l'OS d'après les cibles de ses appels et les tables update/render) :

| Poste | Instructions par bloc | Part |
|---|---|---|
| Code du Syntakt (3 voix, en SRAM) | 25 261 | 53 % |
| Machines d'origine et leurs fonctions EMAC (3 voix) | ~15 000 | ~32 % |
| Boucle des voix de l'OS (dont la division des pistes par 2 : 1 344) | 2 000 | 4,2 % |
| Notre régulateur : `voice_after` 1 560, `voice_gate` 398, détours 210, passerelle 39 | 2 207 | 4,6 % |
| Model-TG autour des voix (`sil_note` ~650, étage d'amplitude, dispatch) | ~1 200 | 2,5 % |
| Total | 47 590 | ≈ 44 % d'un bloc (1,54 cycle par instruction) |

Par piste : KICK 7 160, SDVtg 8 865, SYToy 7 457, PERC 6 506, TONE 6 321, SYSwm 11 272. Le bloc d'un trig ne coûte pas plus
dans la boucle des voix (47 149).

- Le calcul du son lui-même (code du Syntakt, machines d'origine en EMAC serré, [35 §4](35-glitches-usb-multipiste.md))
  ne peut pas être allégé sans changer le son.
- Ce qui ne fait pas de son : notre régulateur, la division des pistes par 2 de l'OS, le suivi des voix de Model-TG.
- Hors de la boucle des voix (non émulable en entier, [27 §3.4](27-cinq-et-six-voix.md)) : mix (≈ 5 %), delay et reverb
  (≈ 12 %), le reste de l'interruption ([31 §7](31-model-tg.md)).

## 3. La nouvelle règle `[FAIT]`

Mêmes mesures qu'avant (charge du bloc, moyenne rapide 1/8 par bloc ≈ 5 ms, moyenne lente 1/256 ≈ 170 ms) et mêmes seuils
(`GOV` de `gen_syntakt_engines.py` : 86 / 82 / 93 / 89 / 96 %), mais :

| | Avant ([30](30-regulateur-charge-soutenue.md)) | Maintenant |
|---|---|---|
| Pic | un bloc au-dessus de 93 % | **le plus bas des deux derniers blocs** au-dessus de 93 % : la charge doit durer |
| Surcharge sévère (fondus de 2 blocs) | un bloc au-dessus de 96 % | idem, sur le pic qui dure |
| Moyennes | en 1/256 de bloc : la lente ne montait pas, la rapide restait jusqu'à 7/256 sous la charge | la lente en 1/65536 (`X_SLOW`), une rapide précise en 1/2048 (`X_FAST`) pour la règle ci-dessous ; la rapide du code C (`gov_avg`) reste celle de l'arrêt anticipé des fins de notes (au-dessus de 72 %), inchangé |
| Charge soutenue | moyenne lente au-dessus de 86 % (jamais atteint, §1) | **la plus basse des deux moyennes** au-dessus de 86 % : une fois des voix éteintes, la moyenne rapide redescend en quelques blocs |
| Temps à libérer | moins le coût des voix en fondu | moins aussi celui des voix éteintes depuis moins de 32 blocs, que les moyennes n'ont pas encore vues partir |
| Voix choisie | la crête la plus basse (avant le mixeur) | **la moins audible dans le mix** : somme des valeurs absolues de la piste (`0x80001858`, ce que reçoit le mixeur) × le plus grand de ses 6 gains de mixeur (principal G/D et envois, ceux que lit `voice_quiet` de Model-TG) ; une piste mutée a des gains nuls et part la première ; **à égalité, la note la plus ancienne** |
| Inchangé | | notes protégées (16 blocs, 4 en surcharge sévère), 2 voix par bloc au plus, fondus de 8 ou 2 blocs, ni le Sampler ni la piste que Model-TG enregistre ou édite, arrêt anticipé des fins de notes sous -66 dB au-dessus de 72 % |

Une coupure ne protège que les blocs suivants : attendre un bloc de plus avant de couper ne fait courir aucun risque de
plus au son (le fondu dure de toute façon 2 à 8 blocs, pendant lesquels la voix coûte encore).

## 4. Plus léger `[FAIT]`

**Avec Model-TG, le suivi de chaque voix par le régulateur** (`voice_gate` et `voice_after`, appelés pour chaque piste à
chaque bloc, en SRAM) est réécrit en assembleur (`machines/gov/voice_gate_tg.S`, `voice_after_tg.S`) :
- même rôle, mêmes variables : coût de la voix, fondu, compteur de blocs faibles, âge de la note, pistes protégées ;
- la voix est faible quand tous ses échantillons sont dans [-seuil, seuil[, testé par OU(x + seuil) < 2 seuil (non
  signé), 3 instructions par échantillon : exactement le test du code C (OU des valeurs absolues sous un seuil
  puissance de 2) ; la crête n'est plus calculée à chaque bloc, le régulateur ne la lit plus (§3).

**La division des pistes par 2 de l'OS** (`0x400a7e2a..0x400a7e38`, après update/render de chaque piste) : 7
instructions par échantillon avec un compteur ; réécrite dans les mêmes 14 octets avec la fin de la piste pour borne,
5 instructions (`tools/voice_loop.py`). Mêmes valeurs ; d0, d1 et a0 n'y sont plus lus après. Écrite par 6ch-usbup,
Model-TG (les deux tweaks) et les moteurs du Syntakt sans Model-TG (mêmes octets, acceptés deux fois par les
constructeurs).

**Mesure** (même boucle des voix qu'au §2, 6 pistes qui sonnent, Model-TG + 5 moteurs) : **47 507 → 46 385
instructions par bloc** (−1 122, −2,4 % de la boucle des voix, environ 1 % d'un bloc à 1,54 cycle par instruction). Le
reste de la boucle des voix est le calcul du son lui-même (§2).

## 5. Sans recompiler le C `[FAIT]`

Le code C de la passerelle est compilé par `m68k-elf-gcc` 16.2 (Homebrew), absent ici et que le réseau de cet
environnement ne laisse pas télécharger (ni ses sources). Recompiler avec GCC 13.3 changerait tout le code compilé des 62
tweaks. Le régulateur est donc remplacé **après** la compilation (`tools/gov_asm.py`), comme l'envoi à heure fixe
([35 §4](35-glitches-usb-multipiste.md)) :
- chaque fonction remplacée garde son adresse (champ `gov` du tweak : `audio_end`, et avec Model-TG `voice_gate`,
  `voice_after`) : la sonde, le détour de la boucle des voix et `voice_done` (compilé) appellent les mêmes adresses ;
- sa place est celle du code compilé, mesurée en suivant son graphe (branchements, jusqu'aux `rts`) ;
- la partie rare de la décision (`gov_cut.S`, `gov_key.S`, table des gains) va dans la place que libèrent les nouvelles
  fonctions (avec Model-TG, dans les zones de SRAM déjà rangées dans l'image : les morceaux et le crochet de démarrage
  ne changent pas) ou, sans Model-TG, dans la charge utile (recopiée en entier) ;
- les nouvelles variables sont dans la charge utile, hors de tout morceau : à zéro au démarrage ;
- l'assembleur résout tout (constantes absolues, étiquettes locales) : pas d'édition de liens, qui alignait le début
  d'une fonction sur 4 octets ; une pièce qui change de taille une fois placée est refusée.

`gen_syntakt_engines.py` applique la même étape à la fin de `build_tweak` (sauf aux firmwares de diagnostic 90 à 92,
dont le compteur est dans `audio_end`) : avec GCC 16.2, le générateur redonne les fichiers versionnés. Vérifié avec GCC
13.3 (§6).

## 6. Preuves `[FAIT]`

**Différentiel** (script de travail, non versionné) : le régulateur compilé (tweaks d'avant cette note) contre
l'assembleur, même firmware et mêmes pistes, 400 blocs, bloc par bloc : sorties des 6 pistes, et état du régulateur (blocs
faibles, âge, voix éteintes, fondus, coût mesuré, moyenne rapide du code C, arrêt anticipé, charge du bloc).

| Firmware | Sans régulateur | 50 % | 80 % | Charge variable 30..85 % |
|---|---|---|---|---|
| Model-TG + 5 moteurs (`voice_gate`, `voice_after`, `audio_end` en assembleur) | identique | identique | identique | identique |
| 5 moteurs seuls (`audio_end` en assembleur) | identique | identique | identique | identique |

Seul écart voulu : au tout premier bloc, le code C ignorait la mesure (période démesurée), l'assembleur la calcule (sans
effet : la moyenne rapide reste à 0). La moyenne lente et la période ne sont plus comparées : elles changent exprès (§3).

**`tools/emu/test_governor.py`** (réécrit, 5 moteurs) :

| Vérification | Résultat |
|---|---|
| 50 % | sortie identique, aucune voix éteinte |
| 80 %, puis 91 % pendant 300 blocs | seules les fins de notes sous -66 dB s'arrêtent, aucune extinction de force |
| Un bloc à 99 % tous les 10 blocs (75 % sinon) | **aucune voix éteinte** (le code C en éteignait une à chacun de ces blocs) |
| Deux blocs de suite à 99 % | extinction au 2e bloc |
| 95 % (puis 97 %) pendant 200 blocs | les moins audibles dans le mix, juste assez pour repasser sous 89 %, fondus de 8 (puis 2) blocs, autres voix identiques, plus rien après, retrig |
| Une des pistes les plus fortes mutée (gains nuls), ou à -30 dB au mixeur | c'est elle qui part |
| Toutes les pistes mutées (clés nulles), jouées dans un ordre donné | les plus anciennes d'abord |
| Charge qui suit les voix (7 % par voix, 6 voix : 88 %), moyenne lente déjà à 88 % | **une seule voix éteinte**, puis la charge soutenue retombe ; le code C, dans le même scénario (moyenne lente posée à 88 %), en éteignait deux |
| Moyenne lente partie de 0 sous une charge de 88 % | elle monte (le code C restait à 0) |

**Non-régression** : voir la fin de cette section (bancs complets sur le firmware de l'essai).

**Reproductibilité** : avec GCC 13.3, le générateur sort exactement « sa sortie sans les étapes de cette note, puis ces
étapes » sans Model-TG (5 moteurs ; SD seul ; SY TOY + SY SWARM) ; avec Model-TG, le code compilé par GCC 13.3 n'a pas les mêmes tailles et la
décision n'y trouve plus sa place (ce n'est pas le compilateur de référence ; avec GCC 16.2, les fichiers versionnés).

## 7. Empreintes

| `-t` | MAIN OS patché (SHA-256) |
|---|---|
| `6ch-usbup` | `57fa258f…` |
| `model-tg` | `aa0740d7…` |
| `6ch-usbup,model-tg` | `96b6aec2…` |
| `syntakt-sd-cp-toy-bits-swarm` (`--syntakt`) | `c6cdfe22…` |
| `6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm,trig-hold,arp` (`--syntakt`) | `ea715e19…` |

Valeurs complètes : [`BUILD.md`](../BUILD.md) et `REF_MAINOS` de `docs/flasher/app.js`. Le firmware d'essai du §8
(`build.py`, OS officiels) redonne `ea715e19…`, la même empreinte que le flasher.

## 8. Essai sur la machine `[À FAIRE]`

Firmware d'essai : 6ch-usbup + Model-TG + 5 moteurs + trig-hold + arpégiateur, construit par `build.py` depuis les OS
officiels de l'utilisateur (même MAIN OS que le flasher, §7).

1. Rejouer les projets à 6 pistes actives où la dernière était coupée : elle ne devrait plus l'être, sauf charge qui
   dure vraiment (alors c'est la voix qu'on entend le moins dans le mix qui part, et plus forcément la même).
2. Muter une piste pendant un passage chargé : si une voix doit partir, c'est elle.
3. Vérifier qu'il n'y a ni craquement ni micro-gel (le régulateur ne coupe plus sur un bloc isolé), et que l'interface
   reste fluide avec les 6 pistes, les effets et le Sampler.
4. L'audio USB 6 canaux, le mute verrouillé, l'arpégiateur et le maintien des trigs comme avant.

Si le son craque sur des moments denses, la persistance du pic (2 blocs) ou le seuil de 93 % se règlent dans
`machines/gov/audio_end.S` et `GOV` de `gen_syntakt_engines.py`.
