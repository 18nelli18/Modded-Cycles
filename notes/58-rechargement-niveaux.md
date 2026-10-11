# 58 — Recharger le pattern en gardant les niveaux

Demande privée du 12/10/2026 : intégrer le maintien des niveaux des pistes au
raccourci FUNC + RELOAD PTN. Contribution originale de djdoz, sous MIT (texte
`LICENSE-reload-keep-levels`). Recette `52-reload-keep-levels.json`, générateur
`tools/gen_reload_keep_levels.py`, source `tools/machines/reload_keep_levels/`,
preuve `tools/emu/test_reload_keep_levels.py`. Adresses : VA de l'OS 1.13.

## Réponse courte

Un appui bref sur FUNC + PATTERN garde les niveaux actuels des six pistes pendant
le rechargement normal du pattern. PAN et les autres réglages se restaurent.
Sauvegarde, maintien du raccourci et rechargements du menu restent d'origine.
L'intégration est **expérimentale**, en attente du test matériel du mainteneur.
Elle peut se combiner avec le mod d'affichage volume/PAN déjà présent.

## 1. Route de l'OS

| Adresse | Rôle |
|---|---|
| `0x4001c19c` | Appel du raccourci bref ; retour `0x4001c1a2` |
| `0x400107d8` | Rechargement séquence/kit, crée le cadre A6 |
| `0x400106de` | Lecture du kit, sans nouveau cadre A6 |
| `0x400107a4` | Appel du décodeur de kit |
| `0x4005d080` | Décodeur v4 : six mots du tampon +20 vers kit +16 |
| `0x404d2978` | Tampon temporaire de lecture |
| `0x4001b88a`, `0x4002cad6` | Retours des appels de rechargement du menu |

[FAIT] Le niveau entier est l'octet haut du mot 8.8, vérifié par les accesseurs
`0x40009c5a`/`0x40009ca0`. Le décodeur borne les six mots à `0x7f00`.
[FAIT] À l'appel du décodeur, A6 désigne toujours le cadre du rechargement parent.
Le crochet vérifie A6+4 : seuls les appels du raccourci bref sont concernés.

## 2. Modification

Le crochet vérifie les pointeurs et la version 4, puis remplace les six mots de
niveau dans le **tampon de lecture** par les mots actuels du kit destination.
Il termine par `jmp 0x4005d080`, avec pile et arguments intacts. Le décodeur et
la notification natifs voient directement les niveaux retenus : pas de correction
après rechargement ni de nouvelle écriture dans un fichier. D0/A0/A1 sont volatils,
les registres conservés par l'ABI restent intacts. Aucun état global.

## 3. Place et coexistence

80 octets dans le masque 27×27 libéré `0x4014a890` (108 octets disponibles).
Sa seule référence, la constante du constructeur `0x400bb1fc`, est redirigée
vers la copie identique gardée `0x4014a550`. L'appel `0x400107a4` est réécrit
sur six octets. Trois écritures au total, sans ajout à l'image, sans accroche de
boot, sans réservation de RAM et sans modification du chemin audio.

[FAIT] Le contrôle des overlaps passe sur les recettes de la branche principale.
Le registre des masques est régénéré et vérifié sur le fichier officiel.
Le prototype d'affichage de PR #72 et l'affichage en place de `main` ne touchent
pas cet appel ou ce masque. La preuve avec les mods utilise l'affichage en place.

## 4. Preuve et construction

```sh
python3 tools/gen_reload_keep_levels.py --cycles model-cycles_OS1.13.syx
python3 tools/gen_reload_keep_levels.py --cycles model-cycles_OS1.13.syx --check
python3 tools/emu/test_reload_keep_levels.py --cycles model-cycles_OS1.13.syx
python3 tools/emu/test_reload_keep_levels.py --cycles model-cycles_OS1.13.syx \
  --with level-pan-values,6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm,arp,trig-hold,tempo-max,boot-anim,trigless-dim,lfo-plus \
  --syntakt Syntakt_OS1.42.syx
python3 tools/build.py -i model-cycles_OS1.13.syx -t reload-keep-levels -o build/reload.syx
```

[FAIT en émulation] 1 260 comparaisons et 378 696 instructions par configuration,
seul, avec les dix mods ci-dessus, avec MACRO + SD du Syntakt + affichage + filtre,
et avec affichage + filtre + USB multipiste + arpégiateur + trig-hold. Niveaux entiers 0–127 et fractions valides,
six valeurs, patterns 0/1/95, trois routes, version invalide et erreur de lecture.
108 cas exécutent aussi le parent `0x400107d8` : le cadre A6 est donc réellement
créé et restauré. Pile, registres conservés, retour, appels aux services natifs et
tous les octets du kit hors niveau sont identiques. Le parent et le décodeur de
niveau sont le vrai code de l'OS ; stockage, décodage des sons/FX/séquence,
allocation de messages UI et notification sont simulés. Le test ne prouve pas
la restitution de toutes les données de séquence ni le temps réel.

Unicorn 2.1.4 ARM64 termine avec SIGILL sur cet hôte macOS. Le même test passe
avec Python 3.13 et Unicorn 2.1.4 x86_64 sous Rosetta ; aucun résultat ARM n'est
revendiqué. Le générateur utilise GNU binutils m68k-elf, cible 54418.
La preuve existante `test_level_pan.py --with reload-keep-levels` passe aussi :
pixels et durée de l’affichage restent identiques en présence du rechargement.

[FAIT] Générateur et `--check`, overlaps, registre/relevé des masques, compilation
Python et contrôles de blancs passent. Builder Python/JavaScript et vérificateur
SysEx concordent. `REF_MAINOS`/`REF_MODS` sont à jour (920 combinaisons, 147 mods) ;
les quatre parts du smoke test navigateur passent et couvrent les 920 builds,
plus l'interface et les transferts simulés. Les empreintes CLI seul/avec affichage
sont dans `BUILD.md`. Le contrôle préexistant `relocate_6ch.py --check` diffère avec
le binutils de cet hôte ; la recette USB n'a pas été modifiée.

## 5. Retour matériel et test restant

Le contributeur a confirmé le maintien des niveaux sur le firmware autonome
combiné à l'affichage PAN/volume, le 11/10/2026 : après rechargement,
0/20/40/60/80/120 restent au lieu des valeurs sauvegardées 10/30/50/70/90/110.
Ce retour **n'est pas** un test du port en masque libéré par le mainteneur.

[À FAIRE] Maxime : cocher ce mod seul puis avec Volume et pan en chiffres ;
appui bref FUNC + SETTINGS, changer les six niveaux, PAN et un pas, puis appui
bref FUNC + PATTERN. Niveaux conservés, PAN/pas restaurés. Vérifier ensuite le
maintien du raccourci et le menu (niveaux restaurés), les changements de pattern,
la sauvegarde, lecture/audio/MIDI et CONFIG > UPGRADE. Tester les gros ensembles
seulement après le cas simple. Aucun firmware, dump, manuel, capture ou chemin
personnel n'est inclus dans cette contribution.
