# 81 — `SETTINGS` tenu : rendre la sauvegarde du pattern quand `FUNC` est tenu

**Sûreté** : `[HYP]` pour la lecture du code de Model-TG, `[FAIT en émulation]` pour la preuve, rien de testé sur la
machine de Maxime. Le patch vit dans `tools/gen_model_tg.py` (`MC_PATCHES`), donc dans la copie de la source de
Model-TG que le générateur assemble ; il n'y a ni nouveau tweak ni nouvelle entrée dans `os.json`.

## 1. Ce que l'utilisateur voit

- **Avant** : dans le stock, `FUNC` tenu + `SETTINGS` tenu ouvre la sauvegarde du pattern (le prompt ; un appui bref
  enregistre sans prompt). Avec Model-TG, `SETTINGS` est le modificateur des accords (soupage, mode, resampling,
  retrig, trigs de slide), et son appui long est avalé sans condition : le prompt ne vient plus, et le seul chemin
  restant est `SETTINGS` › CONFIG › PATTERN.
- **Après** : `SETTINGS` tenu **sans** `FUNC` reste le modificateur (aucun prompt ne surgit au milieu d'un accord) ;
  `SETTINGS` tenu **avec** `FUNC` rend la main à l'OS d'origine, qui affiche le prompt de sauvegarde. L'appui bref
  ouvre toujours le menu Config, et son relâchement après un accord reste avalé.

## 2. Pourquoi `FUNC`, et pas un réglage

Le code de Model-TG avale le bit 5 (appui long) sans regarder `FUNC` : c'était volontaire, parce que tenir `SETTINGS`
sert aux accords et que le prompt n'a rien à faire là. Model-TG n'utilise `FUNC` + `SETTINGS` nulle part (une seule
lecture du bit `FUNC` dans tout le fichier, ailleurs). La distinction existe donc déjà dans les indicateurs de
l'événement (bit 1), et une option de réglage n'aurait pas de second état sensé.

## 3. Le patch

Dans `src/model_tg.s`, en tête de `kh_mod` :

```
    btst    #5,%d1
    beqs    kh_mod_short          | pas l'appui long : chemin habituel
    btst    #1,%d1                | FUNC tenu avec SETTINGS ?
    beqs    kh_eat                | seul : toujours le modificateur des accords
    rts                           | avec FUNC : le prompt de sauvegarde d'origine
kh_mod_short:
```

`kh_eat` rend 0 (événement consommé) ; un `rts` ordinaire laisse le code de touche dans `d0`, et l'OS d'origine
traite l'événement. Le patch coûte **quatre octets** dans le blob de Model-TG.

## 4. Ce que le patch entraîne : la chaîne des moteurs

Ces quatre octets décalent les symboles de Model-TG **après** `kh_mod`, et les tweaks `31-syntakt-tg-…` (moteurs
Syntakt posés dans Model-TG) relisent ses adresses absolues : sans régénération, la construction de l'OS refuse
d'écrire (`octets 'old' attendus … mais trouves …`). La chaîne se régénère par les générateurs, avec **les
compilateurs d'origine** — c'est la règle du projet, et c'est vérifiable :

| Élément | Compilateur des octets versionnés | Vérification |
|---|---|---|
| Moteurs Syntakt (`31-syntakt-tg-…`) | `m68k-elf-gcc` **16.2** (Homebrew) | `gen_syntakt_engines.py --check` : `… est à jour` |
| MACRO (Braids, C++) | `m68k-linux-gnu-g++` **13.3** (Ubuntu 24.04) | `gen_macro.py --check` : `25-macro.json est à jour` |
| ACID et combinaisons | idem (C) | `gen_acid_combos.py --check` |

Les deux compilateurs ont été reconstitués hors de la machine de Maxime : GCC 16.2.0 compilé depuis les sources
pour `m68k-elf` (C), et les binaires exacts d'Ubuntu 24.04 (`g++-13-m68k-linux-gnu 13.3.0-6ubuntu2~24.04`, paquet
`gcc-13-cross-ports`, composant *universe*) pour `m68k-linux-gnu`. Les deux `--check` ci-dessus sont la preuve que
ce sont bien les bons : ils reproduisent les fichiers versionnés à l'octet.

## 5. Preuve en émulation

`tools/emu/test_tg_keys.py` exécute le **vrai** `key_hook` de Model-TG assemblé depuis la source retouchée, sur le
MAIN OS patché, et lui donne de faux événements de touche (code en +12, indicateurs en +16) :

```
ok  appui long + FUNC : rendu à l'OS (d0 = 0xd), SETTINGS pas tenu
ok  appui long seul   : avalé (d0 = 0), le modificateur des accords reste
ok  appui bref        : rendu, SETTINGS tenu, pas d'accord
ok  répétition        : rendue
ok  relâchement après un accord : avalé, pas de menu Config derrière
ok  relâchement d'un appui simple : rendu
ok  une autre touche avec FUNC    : rendue telle quelle
```

## 6. Limites

- Rien n'est testé sur la machine de Maxime : la sauvegarde par `FUNC` + `SETTINGS` tenu est à confirmer, ainsi que
  l'absence de prompt pendant un accord.
- Si un jour Model-TG prend `FUNC` + `SETTINGS` pour autre chose, le patch est à revoir (il rendrait la touche à
  l'OS au lieu de la lui laisser).
