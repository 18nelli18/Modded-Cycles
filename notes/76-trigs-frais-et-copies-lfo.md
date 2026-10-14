# 76 — Pas frais et copies LFO2 allégées

13/10/2026, demande d’aveycole dans Codex. Le clear d’un trig doit retirer
tous ses locks sur A et B, dont SCRAMBLE. L’utilisateur signale aussi des
ralentissements audio/timing en ajoutant Syntakt et ACID aux percussions.
Adresses : VA de l’OS 1.13. Aucun résultat matériel pour ces nouveautés.

## Résultat

[FAIT en émulation] Suppression grille A : le vrai release UI retire 33 slots
natifs puis les flags résiduels, dont SCRAMBLE et slide. Les autres pas,
pistes et défauts de piste restent intacts. Le mode clavier reste inchangé.

[FAIT en émulation] Suppression B existante : six voies ×64 pas, douze locks
CC par pas, chance/retrigger/arp/nudge et slide remis aux défauts. Les
assignations et bases des potards ne changent pas. Recréation C5/100/1.

[FAIT en émulation] Deux copies internes de LFO2 utilisent une instruction
ColdFire mémoire→mémoire au lieu d’un passage par D1. Le dispatch complet
exécute 476 instructions de moins par bloc. Frames de paramètres et phases
natives identiques sur 120 blocs, destinations communes, saturation et 32
tailles/configurations de mixer. Même résultat avec/sans Banque MIDI.

[À FAIRE] Mesurer le gain en cycles sur matériel et rejouer le pattern qui
sature. Le compteur d’instructions n’est pas un pourcentage CPU. Ce correctif
ne réduit ni la qualité, ni la fréquence de calcul du son ou des LFO. Aucun
gain suffisant pour résoudre toute surcharge Syntakt/ACID n’est annoncé.

## Suppression A

`0x40022dd0` appelle normalement `0x40017c4e(track,step,0)` sur release en
mode grille. Le chemin natif libère les locks mais conserve notamment le
bit6 réservé à SCRAMBLE. Le wrapper propre `step_delete.s` rejoue ce clear,
vérifie le pas, efface le mot de flags puis notifie par le setter de note.
Pas de nouvelle allocation, attente, disque, état global ou chemin audio.

Masque `0x40195a7c`,124 octets,120 utilisés ; constructeur redirigé vers
la copie identique répertoriée par `sprites.py`. Générateur
`gen_step_delete_reset.py` : image officielle vérifiée et refus de toute
collision dans le catalogue fourni. Dans le test, ces écritures sont
intégrées à Banque MIDI, avec ou sans ChordKeys.

`test_step_delete_reset.py` exécute le gestionnaire grille, getters/setters
et pool natifs : six pistes, quatre pages,33 slots, régression stock du
bit SCRAMBLE et absence après correction. Sélection/observateurs contrôlés.
`test_midi_step_clear.py` exécute le menu B placé et ses helpers réels ;
le choix de pattern est contrôlé, constructeur/LFO vérifiés séparément.

## Copies LFO2

`gen_lfo_copy_fast.py` recompile d’abord les deux anciennes fonctions propres
aux adresses de leur recette et refuse une différence source/recette.
Il remplace seulement les corps plus courts de `lf2_copy_frame` et
`lf2_mix`, avec padding **après** RTS. Aucun symbole, hook ou champ sauvegardé
ne bouge. D0/D1 restent des temporaires selon l’ABI ; les registres conservés
et pointeurs finaux sont inchangés.

Deux variantes du flasher sont conservées : avec Banque MIDI et LFO2 seul.
Le choix dynamique conserve leurs autres différences et leurs hashes.
`test_lfo_copy_fast.py` exécute le dispatch LFO1/LFO2 natif et les copies
placées. Les buffers privés, paramètres, phases et résultats sont identiques.
Cette optimisation existe même destination OFF, si le contexte LFO2 a été
initialisé ; elle n’agit pas dans un firmware sans Second LFO.

## Page de test

`gen_controls_test_flasher.py` produit `flasher-controls-test`, sélection
Supermodel/ChordKeys/roterodamus conservée. Les gestes ChordKeys restent
inchangés à la demande explicite du propriétaire. Banque MIDI toujours en
RAM ; aucune sauvegarde, lecture ou initialisation disque réintroduite.

Build navigateur vérifié : LFO seul, sélection complète avec/sans USB6 et
avec/sans ChordKeys ; CRC/conteneur et transfert simulé 689 blocs conformes.
Les références intégrales sont dans `source/controls-reference-check.json`.
Les nouveautés restent expérimentales. Le Clear piste avec reset des deux
LFO et Undo commun est encore une tâche séparée.

## Retour matériel et retrait des copies

Le propriétaire signale un ralentissement majeur, même avec les machines
stock, et une charge culminant au-dessus de109 % sur le premier test.
Les copies mémoire→mémoire sont donc retirées du test de contrôle ; les deux
recettes LFO reviennent exactement à leur version publiée antérieure.
Le compteur d’instructions émulées ne prouvait pas le coût en cycles réel.
La cause reste à isoler ; ne pas réutiliser l’optimisation ni le candidat OFF
qui en dépend avant résolution. Le flasher principal n’avait pas reçu ces
optimisations. La révision du test porte le build
`2026-10-13-controls-baseline-lfo`.
