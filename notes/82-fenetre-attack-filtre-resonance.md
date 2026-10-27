# 82 — Fenêtre de valeur d'Attack, du Filtre et de la Résonance (Model-TG)

Rapport d'un utilisateur (27/10/2026, sa propre machine) : sous MACHINES + DECAY / SWEEP / CONTOUR, Model-TG montre
Attack, Filtre et Résonance sur toutes les machines, mais leur fenêtre de valeur n'a ni grand nombre ni courbe : un
petit potard décalé vers le bas à la place. Les Filtre et Résonance du Sampler (One shot) sont bien dessinés. Demande :
le même dessin pour les trois, et pour Attack la courbe de Decay retournée de gauche à droite, qui suit la valeur.
Code : `tools/popup_view.py`, `tools/machines/popup_view/`, une entrée de `MC_PATCHES` dans `tools/gen_model_tg.py`.
Preuve : `tools/emu/test_popup_view.py`. Adresses : VA de l'OS 1.13.

## Réponse courte

Les trois paramètres sont des identifiants « Error » de l'OS (0x0d, 0x0c, 0x0b) que Model-TG met dans les
positions DECAY / SWEEP / CONTOUR quand MACHINES est tenu (`dh_pass`, `dh_atk`). Leur objet d'interface n'a pas de
dessin. Le dessin de la fenêtre emprunte maintenant celui d'un vrai paramètre : Filtre et Résonance ceux du Sampler,
Attack celui d'Amp Decay, courbe retournée. Le nom reste celui de Model-TG. Aucun symbole de Model-TG ne bouge.

## 1. La fenêtre de valeur dans l'OS `[FAIT]`

- Slot 144 de la vtable de ParameterPageView (`0x4001d818`), appelé par le rendu `0x4001e40a` en
  (vue, écran, id, valeur, verrou, 1), après le cadre du nom ; le rendu finit par inverser le carré de gauche
  (`0x40070dea(écran, 0, 0, 63, 63, -1)`). Model-TG le détourne (`wf_popup`) pour Start/End du Sampler et saute au
  code d'origine par `wp_stock` sinon.
- Objet d'interface d'un identifiant : `0x40a71754 + id * 100`. `+0x2c` non nul : vt[64] (`0x4000a66a`) dessine un
  potard 19 × 17 en (96, 34) et rend 1, le grand nombre n'est pas écrit. `+0x5c` / `+0x60` : la courbe.
- Amp Decay (0x18) : sprite 50 × 22 du vecteur `0x40fe401c` (15 sprites) choisi par la valeur, centré en (32, 19),
  donc x 7..56, y 8..29 (l'écran compte y depuis le bas). Filtre du Sampler (0x49) : `0x40fe3ce0`, 7 sprites 48 × 22 ;
  Résonance (0x4a) : `0x40fe3364`, 11 sprites 48 × 22. Grand nombre 0..127 et cinq points pour les trois.
- 0x0b, 0x0c, 0x0d : `+0x2c` = `0x40047b6c`, `+0x5c` = 0 ; leurs bornes (`0x4010dce0 + id * 56`) vont bien de 0 à
  0x7f00, les points se dessinent.

Relevé de l'OS : agent agy (rapport `popup-envelope-re.md` du bus des agents), mesuré au banc par l'agent DSH ;
une affirmation du rapport était fausse (bornes 0..0), corrigée par la mesure.

## 2. La retouche `[FAIT en émulation]`

- `MC_PATCHES` : `wp_stock: jmp 0x4001d818` devient `jmp 0x401592bc` (même taille : la chaîne des moteurs du Syntakt,
  qui lit des adresses de Model-TG, n'est pas à régénérer).
- `pv_popup` (`0x401592bc`, masque de sprite 48 × 22 libéré, 192 o) : 0x0c → 0x49 et 0x0b → 0x4a sur la pile, puis
  le code d'origine ; 0x0d : la fenêtre d'Amp Decay sur une copie des six arguments, puis, dans l'écran (`16(écran)`,
  colonnes de `12(écran)` mots), les colonnes 7..56 échangées deux à deux sur les bits de y 8..29 (`0x00fffffc`).
  Retourner après coup est sûr : la fenêtre est redessinée en entier à chaque image.
- Le code et la redirection du sprite sont écrits avec Model-TG (`30-model-tg`, `30-model-tg-st`), comme
  `usb_steady` et `voice_loop`.

## 3. Preuve en émulation `[FAIT en émulation]`

`tools/emu/test_popup_view.py` appelle le vrai slot 144 (donc `wf_popup` de Model-TG, puis `pv_popup`) dans un vrai
écran de 128 × 64, polices et vecteurs de sprites construits par l'OS, valeurs 0, 0x2000, 0x4000, 0x7f00 :

| Identifiant | Avant | Après |
|---|---|---|
| 0x0c Filtre | potard 19 × 17, pas de nombre | pixel pour pixel la fenêtre de 0x49 ; « 0 », « 32 », « 64 », « 127 » |
| 0x0b Résonance | idem | pixel pour pixel la fenêtre de 0x4a |
| 0x0d Attack | idem | la courbe d'Amp Decay retournée (x 7..56, y 8..29), le reste de la fenêtre d'Amp Decay tel quel ; quatre images différentes |

Avec Model-TG seul, et avec model-tg-st et les cinq moteurs du Syntakt. `--png` écrit les fenêtres.

## 4. À vérifier sur la machine

- MACHINES + DECAY / SWEEP / CONTOUR sur une machine d'origine, du Syntakt, MACRO, ACID et le Sampler (Attack) :
  nom, grand nombre, points, courbe qui suit le potard.
- Que le nom (cadre de gauche) reste « Attack », « Filter », « Res ».
- Non testé sur la machine de Maxime.
