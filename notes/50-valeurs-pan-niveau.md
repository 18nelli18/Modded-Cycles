# 50 — Valeurs PAN et niveau sur l’écran principal

Demande privée, octobre 2026 : afficher une valeur pendant trois secondes lors
 d’un tour de LEVEL/DATA, à la place du symbole correspondant (manuel OS1.13,
§6.1). Recette `44-pan-level-display.json`, générateur `tools/gen_pan_level.py`,
source `tools/machines/pan_level/pan_level.S`, preuve ciblée
`tools/emu/test_pan_level.py`. Adresses : VA de l’OS 1.13.

## Réponse courte

Prototype expérimental proposé pour revue, **non inscrit au flasher**. Tour
normal : niveau 0–127 à la place du haut-parleur. FUNC + tour : PAN -64–63 à
la place de R. Chaque tour relance le délai de 90 ticks UI, par piste et par
paramètre. Clics inchangés. Pas normal un, maintien rapide seize.

## 1. Code concerné

| Adresse | Rôle |
|---|---|
| `0x4001aa4e` | Gestionnaire d’encodeur de l’écran principal |
| `0x4001abda` | Thunk de l’interface secondaire ; cible directe du gestionnaire |
| `0x4001aac2` | Appel au calcul de delta : multiplicateurs normal/maintenu |
| `0x4001b22a` | Dessin principal, puis remplacement des symboles |
| `0x400081f2` | Dispatch UI, incrément de l’horloge puis appel original |
| `0x40009c5a` | Niveau entier de la piste |
| `0x4000045c` | Copie de la charge utile avant effacement du BSS |
| `0x42339000` | Charge utile et état temporaire |

[FAIT] Le thunk secondaire contourne une modification de la seule vtable
principale ; les détours portent donc sur les entrées réelles. Les prologues
sont rejoués ; leurs octets sont lus depuis le fichier fourni à la construction.
[FAIT] Le clavier `0x4001c0d2` reste identique à l’OS officiel.
[FAIT] Le pas d’origine est deux : les niveaux impairs sautent 100. Le crochet
du calcul de delta impose un, sans changer le multiplicateur rapide seize.

## 2. Dessin et mémoire

Police originale du mod, 3 × 7 pixels ; PAN en x114–127/y21–29 ; niveau en
x65–77/y8–16. Le dessin de l’OS restaure les symboles à l’expiration. Le niveau
127 utilise la marge gauche sans déplacer sa barre (début x79). État dans la
tâche UI, six délais pour chaque paramètre ; aucune modification audio.

[HYP] 90 ticks correspondent à trois secondes à la cadence nominale 30 Hz.
[À FAIRE] Propriété de la RAM au-dessus du BSS, boot complet, modes de lock,
réentrée, rendu complet et coexistence. Le payload autonome reproduit la
construction locale ; il n’est pas chaîné aux boot payloads des autres mods.
Les autres recettes `append` sont déclarées incompatibles. Aucun firmware,
log personnel, dump, manuel ou ancien essai n’est inclus dans cette contribution.

## 3. Construction et validation

```sh
python3 tools/gen_pan_level.py --cycles model-cycles_OS1.13.syx
python3 tools/gen_pan_level.py --cycles model-cycles_OS1.13.syx --check
python3 tools/check_overlaps.py
python3 tools/build.py -i model-cycles_OS1.13.syx -t pan-level-display -o build/pan-level.syx
python3 tools/emu/test_pan_level.py --cycles model-cycles_OS1.13.syx
```

Le générateur vérifie le hash officiel et chaque écriture, puis vérifie que
l’application de la recette reconstitue exactement le binaire construit.
MAIN OS attendu : `9d716a2be3b67fbe2d2512a38dfa886890d5a73cf5c9bdc13f24f462bb3bc50d`.
Le JSON ne contient que les écritures propres au patch et une recette de
charge utile ; les prologues déplacés sont des plages `cycles`, pas des dumps.

[FAIT] Génération et `--check`, contrôle des overlaps et construction passent.
La preuve ciblée exécute le delta d’origine/nouveau, les glyphes et l’armement
des délais ; les services de projet sont simulés. Elle n’est pas une preuve
du dispatch complet. **Exécution bloquée sur macOS ARM : Unicorn 2.1.4 termine
avec SIGILL (code 132), sans résultat. Aucun succès en émulation revendiqué.**

## 4. Avant activation

[À FAIRE] Faire passer la preuve ciblée sur un hôte supporté, ajouter les
preuves du boot, dispatch, dessin principal et restauration réelle des symboles,
prouver la RAM et vérifier CONFIG › UPGRADE. Puis intégrer les cartes bilingues,
guide et références du flasher. Le prototype reste hors du flasher entre-temps.
Maxime doit vérifier les six pistes, limites PAN/niveau, délai et relance,
CTRL ALL, navigation, clics d’origine, lecture et mise à jour USB. Aucun
résultat matériel final revendiqué pour cette version.
