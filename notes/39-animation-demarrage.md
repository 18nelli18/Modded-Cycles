# 39 — Une animation de démarrage « modded-cycles » : le tweak `boot-anim`

Demande de Maxime (05/10/2026, fil du projet) : une animation personnalisée au démarrage, faite à partir du logo SVG du
site (quatre carrés arrondis en 2 × 2, celui en haut à droite en orange), ou à défaut un simple texte « modded-cycles ».
Tweak `43-boot-anim.json` (`tools/gen_boot_anim.py`, sources dans `tools/machines/boot_anim/`), preuve en émulation
(`tools/emu/test_boot_anim.py`). Adresses : VA de l'OS 1.13.

## Réponse courte

- **Une animation est possible, et sans rien ajouter au démarrage** : le MAIN OS joue déjà sa propre animation (des
  carreaux arrondis qui s'allument et s'éteignent au hasard) dans une petite tâche à part, pendant que la tâche
  principale charge le projet. On réécrit le corps de cette tâche, à sa place.
- Même cadence (une image toutes les 20 ms), même nombre d'images (80), même fin : **le démarrage ne dure pas plus
  longtemps**.
- Le bootstrap (menu de démarrage, section 2) n'est pas touché : FUNC à l'allumage ouvre toujours le menu de
  démarrage.

## 1. L'animation de l'OS d'origine `[FAIT]`

| Où | Quoi |
|---|---|
| `0x400054a2` | tâche de démarrage : `0x40005494` lit le bit 5 de `0x4013e4d0` (mot laissé par le bootstrap) ; à 1 : `0x4008e6ba` (écran effacé, pas d'animation), sinon `0x400539fc` |
| `0x400539fc` | sémaphores `0x40a78620` et `0x40a78618` à 0, crée la tâche d'animation : corps `0x40053a6c`, priorité 7, pile de 16 Ko à `0x40a745c0`, bloc de tâche `0x40a785c0` |
| `0x40053a6c..0x40053e74` | **corps de la tâche** (1 032 o). Seule référence : le `pea (0x40053a6c,pc)` de `0x40053a2e` |
| `0x40002144(0x400539b8, 2)` | minuteur toutes les 2 ticks ; `0x400539b8` incrémente `0x40a78618` (`0x40001bb0`) |
| `0x40053bd4..0x40053e30` | boucle : un pas par image, attente du tick (`0x40001aca`), envoi (`0x4008e622`), LED (`0x4008e77e`) |
| `0x40053e34` | fin : 10 ticks d'attente, `0x40001c80(0x40a78620)` (signal), `0x40002200(0x400539b8)` (retrait du minuteur), puis attente sans fin sur `0x40a78618` |
| `0x40053a54` | appelée par la tâche principale (`0x40007e74`) quand le projet est prêt : si l'animation a démarré, **attend** `0x40a78620`, puis l'écran normal (et `0x4008e8de` éteint toutes les LED) |

Ce qu'elle dessine : l'écran est découpé en 4 × 8 cases de 16 × 16. Un tableau de 80 numéros de case (chaque case deux
fois, les quatre premières colonnes une fois de plus) est mélangé (`0x4009572c`), puis chaque image **inverse** une
case : les carreaux apparaissent et disparaissent au hasard. Chaque case est dessinée avec un des 10 carreaux de 16 × 16
chargés au démarrage (`*0x40fe3840`, descripteurs de 28 o), choisi selon ses voisines (`0x400539c8`) pour que les
carreaux voisins se soudent ; des LED de trig s'allument au passage (`0x4008ea3e`).

Durée : 80 images + 10 ticks = 90 ticks de 20 ms, **1,8 s**. L'écran normal n'arrive qu'après, et après le chargement
du projet.

Le tick vaut 10 ms : PIT0 (`0x400019b4`) avec PCSR = `0x053f` (horloge du bus / 32) et PMR = 42 239, soit
135 168 000 / 32 / 42 240 = **100 Hz** (horloge du bus de [23](23-optimisation-charge.md), la même que le minuteur
DMA 0 de [33](33-effacer-un-trig.md)).

## 2. L'écran `[FAIT]`

| Où | Quoi |
|---|---|
| `0x40053e74(octets, n, dc)` | envoie n octets sur le **DSPI1** (`0xfc03c034`, mots de 9 bits : bit 8 = donnée (`0x100`) ou commande (0)), attend la fin (`0xfc03c02c` bit 28) |
| `0x40053f64(x, page)` | commandes `0xb0 \| (7 - page)`, `x & 15`, `0x10 \| x >> 4` : contrôleur de type ST7565, **pages de l'écran à l'envers** |
| `0x40053fb0(octets, n)` | données |
| `0x4008e580(x, page, 8 octets)` | position puis 8 octets |
| `0x401492f0` / `0x401492f4` | les deux tampons de 1 024 o (`0x40fdddec`, `0x40fdd9ec`, dans le BSS) : tampon de dessin, tampon affiché |
| `0x4008e728` / `0x4008e720` | rendent l'un ou l'autre |
| `0x4008e622` | envoie les blocs de 8 × 8 où le tampon de dessin diffère du tampon affiché, puis **échange** les deux |
| `0x4008e5a8` | envoie tout (jamais appelé) |
| `0x4008e6ba` | vide les deux tampons et tout l'écran |
| `0x40053fc6` | initialisation de l'écran (jamais appelée : c'est le bootstrap qui allume l'écran) |

Format des tampons, celui de `Bitmap` (`0x400701b8`, setPixel) pour une image de 128 × 64 : **colonne par colonne**,
8 o par colonne (deux mots de 32 bits), le pixel (x, y) est le bit `7 - (y & 7)` de l'octet `x × 8 + y / 8`. L'animation
d'origine dessine dans un `Bitmap` de 128 × 64 puis le recopie tel quel dans le tampon de dessin (`0x4008f1f0`, une
copie de mémoire).

**Dans ce repère, y monte : y = 0 est la ligne du bas de l'écran**, x = 0 la colonne de gauche. Le pixel vu à la ligne r
(comptée depuis le haut) est le pixel (x, 63 − r) de l'OS. `[FAIT]` La 1ʳᵉ version de l'animation supposait l'inverse et
s'est affichée à l'envers sur la machine (§8). Trois indices concordent :

- l'envoi : la page p de l'OS part en page `7 - p` du contrôleur, sa ligne `y & 7` au bit `7 - (y & 7)`, ce qui retourne
  tout l'écran sur un contrôleur réglé de façon standard (page 0 en haut, bit 0 = sa ligne du haut) ;
- le texte de l'OS : sa police de chiffres (`0x40148558`, glyphes de 5 lignes rangés colonne par colonne, table des
  glyphes `0x401485ee` de [15 §2](15-demandes-reddit.md)) n'est à l'endroit que si y monte. Écrit par `0x400716c0` en
  émulation, son « 7 » a la barre en haut et le pied à gauche seulement ainsi. D'un caractère au suivant, x avance
  (`0x40071786` : x + largeur + 1), donc pas de miroir gauche / droite ;
- la machine : l'écran MACHINES ([20 §1](20-moteurs-syntakt-a-cocher.md), essai du 02/10/2026) et le 1ᵉʳ essai de
  l'animation (05/10/2026).

## 3. La nouvelle animation

Le logo du site, à l'échelle de l'écran (128 × 64, une seule couleur) :

- quatre carrés de 16 × 16, 4 pixels d'écart (36 × 36 en tout), coins arrondis de 2 puis 1 pixel, en haut et centrés ;
- le carré orange devient le carré « d'accent » : un anneau de 3 pixels et un cœur de 6 × 6 ;
- « modded-cycles » dessous, centré, dans une police dessinée pour l'occasion : minuscules de 8 pixels de haut, traits
  de 2 pixels, jambages de 3 (98 × 14 pixels).

Déroulé, en images de 20 ms :

| Images | Quoi |
|---|---|
| 0–3 | écran vide |
| 4, 10, 16, 24 | apparition des carrés (haut gauche, bas gauche, bas droite, puis l'accent) : côtés 2, 6, 10, 14, 18, 18 puis 16 (un petit rebond) |
| 34–38 | l'accent se creuse (trou de 2 à 10 pixels), puis son cœur apparaît |
| 40–64 | « modded-cycles » s'écrit, une lettre toutes les deux images |
| 65–79 | image finale tenue |
| + 10 ticks | fin d'origine |

Aperçu (ce que reçoit l'écran en émulation) : `docs/assets/boot-anim.gif`, montré dans le guide.

## 4. Le code et la place

`tools/machines/boot_anim/boot_anim.S` (assembleur, pas de compilateur : `--check` ne dépend que des binutils), lié en
`0x40053a6c` par `boot_anim.ld`. Le générateur écrit à côté `anim.inc` (géométrie, horaire) et `anim_data.inc`
(carrés, rebond, colonnes du texte : 98 mots de 16 bits). **690 o sur les 1 032 du corps d'origine** ; le reste du corps
d'origine reste en place, sans plus rien pour y mener. **Aucune place libre utilisée.**

Le code et le modèle Python comptent y depuis le haut, comme on regarde l'écran ; seules les deux routines qui posent les
pixels (`pset`, `centered`) passent au repère de l'OS : ligne `63 - y`, soit le bit `y & 7` de l'octet `7 - y / 8` de la
colonne (§2).

Contrat, le même que l'original :

1. `0x4008e6ba` : l'écran entier est vidé d'abord. L'envoi ne transmet que les blocs qui changent, et les carreaux
   d'origine finissaient par couvrir tout l'écran ; ici une bonne partie reste vide, il ne faut donc rien laisser de ce
   que le bootstrap a pu y mettre.
2. Minuteur `0x400539b8` toutes les 2 ticks (`0x40002144`).
3. Pour chaque image : tampon de dessin (`0x4008e728`), effacé puis dessiné (carrés, trou et cœur de l'accent,
   lettres), attente du tick (`0x40001aca`), envoi (`0x4008e622`).
4. Fin d'origine : 10 ticks, signal `0x40a78620`, retrait du minuteur, attente sans fin.

Différences voulues : aucune LED de trig (l'original en allumait ; la tâche principale les éteint de toute façon), pas
d'allocation (l'original prenait 320 o de tas et un `Bitmap` de 1 024 o).

## 5. Conflits

Aucun autre tweak n'écrit dans `0x40053a6c..0x40053e74` ni dans le code de l'écran. Model-TG et les moteurs du Syntakt
s'accrochent au démarrage ailleurs (`0x400004b2`, notes/17 et 31) : la tâche d'animation est créée bien après. Le mode
« démarrage sans animation » (bit 5 de `0x4013e4d0`) reste tel quel.

## 6. Preuve en émulation `[FAIT en émulation]`

`tools/emu/test_boot_anim.py` fait tourner la tâche, d'origine puis modifiée, avec le **vrai code de l'écran** jusqu'au
registre du DSPI1 ; chaque mot envoyé est rejoué sur un modèle de l'écran **tel qu'on le voit** (commandes de page et de
colonne, page 0 en haut, bit 0 = sa ligne du haut, colonne 0 à gauche), que le « 7 » de l'OS valide d'abord (§2).
Interceptés : minuteur, sémaphores, et pour l'original l'allocation, le verrou des LED et ses carreaux (de faux carreaux
pleins, les vrais sont chargés au démarrage).

| Vérification | Origine | Modifiée |
|---|---|---|
| Un « 7 » écrit par le vrai code de texte de l'OS (`0x400716c0`, police `0x40148558`, vrai `Bitmap` `0x40070172`) apparaît à l'endroit : barre en haut, pied à gauche | — | oui |
| Le pixel (x, y) du vrai `Bitmap::setPixel` est vu en (x, 63 − y), et lui seul | — | oui (4 points, dont les coins) |
| Minuteur `0x400539b8`, 2 ticks | oui | oui |
| Images avant la fin | 80 | 80 |
| Puis 10 ticks, signal `0x40a78620`, retrait du minuteur, attente sans fin | oui | oui, mêmes appels dans le même ordre |
| Images vues sur l'écran = modèle Python du générateur (`frames()`) | — | 80 sur 80, pixel pour pixel (la 1ʳᵉ version : 4 à 79 différentes, à l'envers) |
| Écran vidé avant la 1ʳᵉ image (sa mémoire part de valeurs quelconques) | — | oui |
| Écritures hors des tampons de l'écran, de leurs pointeurs, de la pile et du DSPI1 | — | aucune |
| Avec `6ch-usbup, model-tg-st, syntakt-tg-sd-cp-toy-bits-swarm, arp, trig-hold, tempo-max` | — | mêmes appels, mêmes images |

```sh
python3 tools/gen_boot_anim.py --cycles model-cycles_OS1.13.syx --check
python3 tools/emu/test_boot_anim.py --cycles model-cycles_OS1.13.syx --gif anim.gif \
    --with 6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm,arp,trig-hold,tempo-max
```

## 7. Ce qui reste à vérifier sur la machine `[À FAIRE]`

- L'animation à l'allumage : les carrés, l'accent, le texte lisible et à l'endroit, sans reste de l'écran précédent.
- Le passage à l'écran normal comme avant (même délai), les LED de trig éteintes ensuite.
- FUNC à l'allumage ouvre toujours le menu de démarrage (rien n'a changé là, à confirmer quand même).
- L'orientation : à l'envers au 1ᵉʳ essai, corrigée (§8) ; à revoir à l'endroit.

## 8. 1ᵉʳ essai sur la machine (05/10/2026) : l'image à l'envers `[CORRIGÉ en émulation]`

Maxime a flashé, par le flasher du site, un firmware de test avec la seule animation (MAIN OS `a847f83b…`, 1ʳᵉ version).
Retour : « ça marche mais c'est à l'envers, le haut est en bas et le bas est en haut ». L'animation tourne donc, avec sa
durée et son passage à l'écran normal.

- **Cause** : §2 supposait que la ligne 0 d'un `Bitmap` était en haut de l'écran ; l'OS la met en bas. La preuve ne
  pouvait pas le voir : son modèle de l'écran était écrit dans le repère de l'OS, sans rien qui le relie à ce qu'on voit.
  [20 §1](20-moteurs-syntakt-a-cocher.md) l'avait pourtant établi sur la machine le 02/10/2026.
- **Haut / bas seulement** : le texte de l'OS s'écrit de gauche à droite à x croissant (§2), et le retour ne parle pas
  de texte en miroir.
- **Correction** : `pset` et `centered` écrivent la ligne `63 - y` (§4), 690 o au lieu de 698. Le modèle Python et
  l'aperçu (`docs/assets/boot-anim.gif`, identique octet pour octet) ne changent pas : ils montraient déjà l'image voulue.
- **Preuve** : le modèle de l'écran montre ce qu'on voit, et le point 2 le valide avec le texte de l'OS (§6). La 1ʳᵉ
  version y échoue (images 4 à 79 différentes du modèle), la nouvelle passe tous les points, seule et avec les autres mods.
- Nouvelles empreintes du MAIN OS : `boot-anim` seul `388ed6c6…`, les autres dans [BUILD.md](../BUILD.md) ; `REF_MAINOS`
  régénéré.
