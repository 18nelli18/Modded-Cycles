# 77 — Control All Config dans le test Supermodel

13/10/2026, demande d’aveycole. Source MIT :
[durchgemacht/cycles-control-all-config](https://github.com/durchgemacht/cycles-control-all-config),
commit `429563bf13feb05edd0c7510efbc9f719b3741ff`.
La source et la licence originales restent dans
`tools/machines/control_all_config`. L’amont décrit un prototype émulé,
sans validation matérielle. Cette intégration reste expérimentale.

## Geste et portée

- TRACK + TRIG 1–6 exclut/inclut les pistes audio correspondantes.
- TRACK + potentiomètre conserve Control All sur les pistes incluses.
- La piste active suit toujours. Les LEDs affichent cette inclusion effective.
- Exclusion également pour MACHINES, destination LFO, profondeur, PUNCH/GATE.
- Choix en RAM, remis à toutes les pistes incluses au démarrage.

Le mod ne remappe pas les CC ni le Control All de la banque B. Il ne change
pas les gestes ChordKeys. L’optimisation des copies LFO est une modification
séparée, également présente dans cette page.

## Placement et validation

Les deux masques choisis par l’amont sont déjà occupés dans Supermodel.
`gen_control_all_config.py` sépare les fonctions sans changer leurs contrats
et choisit neuf queues de masques libres, en vérifiant le catalogue complet
et le correctif de suppression de trigs. 508 octets propres sont placés ;
les références des sprites vont vers leurs copies identiques répertoriées.
Le masque `0x4018dba8` reste réservé à un futur chemin rapide LFO OFF.

Cinq trampolines rejouent exactement les six octets natifs déplacés puis
reviennent à l’instruction suivante. Deux entrées de vtable reçoivent les
handlers de touches et de LEDs. Aucun de ces sept hooks n’est utilisé par
la sélection actuelle. Les adresses et anciens octets sont contrôlés contre
l’OS officiel 1.13 fourni par l’utilisateur.

Adaptation visible : le handler LED utilise `cac_skip`, afin que la piste
active reste allumée même si son bit d’exclusion est défini. Le comportement
de paramètres amont incluait déjà toujours cette piste.

`test_control_all_config.py` exécute les cinq boucles natives et les handlers
placés pour 64 masques × six pistes actives. Callbacks de paramètres, objets
UI/projet et pilote LED contrôlés ; branches, compteurs, pile, exclusions,
MACHINES et LEDs réels vérifiés. Press/release/repeat/long et transmission
des touches étrangères ou relâchées après un appui antérieur sont couverts.
Le build navigateur couvre Control All seul et la sélection complète avec
et sans ChordKeys/USB6. Le transfert simulé vérifie les blocs et le conteneur.

## Publication

Page `flasher-controls-test`, build `2026-10-13-control-all-copy-test`.
Recette et références intégrales publiées dans son dossier `source`.
Le flasher principal ne change pas. Pas de sauvegarde MIDI réintroduite.
Le gain CPU réel et le comportement matériel de Control All restent à tester.
