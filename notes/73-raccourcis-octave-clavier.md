# 73 — Raccourcis d'octave du clavier

Demande du contributeur, transmise le 14/10/2026, touches révisées le 18/10/2026 : TRACK + TRIG 15 pour descendre le clavier d'une octave, TRACK + TRIG 16 pour monter, avec mise à jour du KBT réel dans Track Setup et sans éclairage ajouté. Contribution originale de djdoz, MIT selon `CONTRIBUTING.md`. Tweak `49-octave-shortcuts.json`, générateur `tools/gen_octave_shortcuts.py`, preuve `tools/emu/test_octave_shortcuts.py`. Adresses : VA de l'OS 1.13.

## Réponse courte

[FAIT en émulation] Un appui règle KBT de −/+12 par le setter stock ; le maintien ne répète pas. Les limites stock −60…+60 s'appliquent. Les relâchements rejoignent le callback d'origine, dont les notes tenues conservent leur pitch initial. Pas de note jouée ou enregistrée par le raccourci, pas d'éclairage ajouté. Mode grille inchangé. La version initiale ne se combine pas avec Model-TG ni Chord Keys.

## 1. Chemins de l'OS

| Adresse | Rôle |
|---|---|
| `0x400ff9cc` → `0x4001a0d2` | [FAIT] Slot d'événement de KeyboardView. TRIG 1…16 = codes logiques 16…31. |
| `0x40024078` | [FAIT] TrackSelectionView : laisse ces TRIG passer au traitement suivant. |
| `0x4007faf4` | [FAIT] État des touches : TRACK = code 2, FUNC = 1, PATTERN = 3, RETRIG = 4. Table de correspondance en `0x4010ae5c`, bits physiques en `0x40f95744`. |
| `0x4006b978`, `0x4006bb18` | [FAIT] Mode grille et clavier désactivé ; aucune interception dans ces états. |
| `0x400cf866` → `0x4000f23e` | [FAIT] Son courant employé par le clavier et Track Setup. |
| `0x40016da6`, `0x40016dd6` | [FAIT] Getter et setter KBT signé, octet +`0x2d1` du son ; setter borné à −60…+60, notification stock par le slot virtuel +`0x10`. |
| `0x4003e3b6`, `0x4003e412` | [FAIT] Affichage de KBT dans Track Setup et réglage incrémental ; utilisent ces mêmes getter/setter. |
| `0x40019f44`, `0x40019d00` | [FAIT] Ajout et retrait des notes tenues du clavier ; le pitch enregistré à l'appui sert au relâchement. |

## 2. Code et contrat

Le wrapper reçoit `(KeyboardView, KeyEvent)` et renvoie un booléen consommé. Il préserve les registres non volatils et la pile. Seuls les codes 30/31, à l'appui (flag bit 0), TRACK tenu et FUNC/PATTERN/RETRIG libres, hors grille/clavier désactivé, entrent dans le raccourci. Un maintien (flag bit 3) est consommé sans changer KBT. Un appui frais appelle getter puis setter stock avec −/+12.

Tout autre événement, dont tous les relâchements, rejoint `0x4001a0d2` avec les arguments d'origine. Cela garde le note-off du pitch mémorisé, même si KBT a changé entre-temps. Aucun état global ni octet de projet nouveau, aucun popup. Le KBT garde sa sauvegarde normale. Le décalage par demi-tons est conservé sauf quand une limite raccourcit le déplacement.

## 3. Place et incompatibilités

[FAIT] 264 o de code original dans le masque 47×47 `0x4018d4a8` (376 o), dont la constante `0x400acd56` est redirigée vers la copie identique gardée `0x40172220` par `sprites.redirect_write`. Ce masque est déjà utilisé par Chord Keys : le partage est exclusif, comme les masques communs à Chord Keys et à l'écoute des samples (notes/46). Le générateur vérifie l'identité des masques avant chaque build.

Trois écritures seulement : constante du masque, code du wrapper, pointeur du callback. Aucune section supplémentaire, aucun chargeur de démarrage, aucune allocation RAM, aucune routine de mise à jour USB modifiée. Le registre et les contrôles de chevauchement vérifient la composition.

Chord Keys remplace le même callback, donc incompatibilité déclarée. Le source de Model-TG au commit `70b39dd` remplace aussi ce slot par son `tick_hook`, qui appelle le clavier stock puis entretient les samples et l'interface ; sa Scale Lock utilise des hooks de note séparés. Cette contribution réserve cette incompatibilité explicitement (`model-tg` et `model-tg-st`), plutôt que de remplacer son service. Une version compatible demanderait une chaîne des deux callbacks et une preuve de leurs services. Aucun mod compatible des branches ouvertes relevées le 14/10/2026 n'occupe ce masque ; les autres occupants sont des versions de Chord Keys, exclues.

## 4. Preuve stock/modifié

[FAIT en émulation] Unicorn exécute le code assemblé, les callbacks OS KeyboardView et TrackSelectionView, le getter réel des modificateurs, getter/setter KBT, callback d'affichage KBT du menu, et les listes de notes tenues. Les KeyEvent sont reconstruits ; projet/son, livraison de notification, dessin et envoi audio sont interceptés. Avec l'arpégiateur, l'objet des données de piste et l'allocation de son tampon sont fournis par le banc de test ; son getter de vitesse s'exécute réellement.

| Vérification | Stock | Modifié |
|---|---|---|
| TRACK + TRIG 15/16, tous les KBT −60…+60 | KBT inchangé | −/+12, borné, notification stock |
| Clavier ou flag live rec | Comportement stock | Même raccourci |
| Affichage KBT du menu | Valeur initiale | Nouvelle valeur immédiate |
| Maintien du raccourci | Pas de changement KBT | Pas de répétition |
| Autres TRIG, autres modificateurs, grille, clavier désactivé | Référence | Même retour, données et notes |
| Six pistes | Référence | Seul le son de la piste active change |
| Note tenue avant changement de KBT | Pitch initial au note-off | Même pitch au note-off |
| Registres non volatils et pile | Préservés | Préservés |

5 698 appels, 23 588 assertions par configuration. Passe seul et avec `6ch-usbup,syntakt-sd-cp-toy-bits-swarm,arp,trig-hold,tempo-max,boot-anim,multiline-browser,level-pan-values,trigless-dim,lfo-plus,midi-both`. Le générateur `--check`, les trois écritures seules et la longueur inchangée de l'image font partie de la preuve. La lecture physique des touches, la pile complète des vues, le DSP et les services de stockage ne sont pas émulés par ce test.

## 5. Retour matériel et prochain essai

Le 14/10/2026, le contributeur rapporte « It has passed » pour le prototype stock OS1.13 avec ces raccourcis. Ce premier prototype utilisait TRACK + TRIG 1/16. Le 18/10/2026, le contributeur demande TRACK + TRIG 15/16 : seuls les deux comparateurs du code de touche passent de 16 à 30. Le traitement et la taille du wrapper restent les mêmes ; cette révision demande un nouvel essai matériel. Ce retour ne vaut pas essai du build intégré par Maxime : statut **experimental**, PR draft.

[À FAIRE] Essai du mainteneur, d'abord seul, puis avec les mods compatibles ci-dessus : KBT 0 → +12 → 0, +5 → +17 → +5, indépendance des pistes, un seul déplacement au maintien, les deux ordres de relâchement, note tenue pendant le déplacement sans note bloquée, enregistrement live sans note du raccourci, grille inchangée, bornes −60/+60, sauvegarde/rechargement normaux et mise à jour USB toujours disponible. Le flasher doit exclure Model-TG et Chord Keys dans les deux sens.

## 6. Touches adjacentes (18/10/2026)

À la demande du contributeur, octave bas passe à TRACK + TRIG 15 (code 30) ; octave haut reste TRACK + TRIG 16 (code 31). TRACK + TRIG 1 suit de nouveau le clavier stock. La preuve compare tous les TRIG au stock hors des deux raccourcis et couvre le relâchement du TRIG 15 déjà tenu. Le retour matériel du 14/10 concerne uniquement le premier prototype.
