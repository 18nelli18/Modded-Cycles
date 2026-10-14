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
- La piste active peut également être exclue. Les LEDs affichent le masque choisi.
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

Adaptations visibles : à la demande du propriétaire après le premier essai
matériel, `cac_skip` ne conserve plus l’exception amont qui incluait toujours
la piste active. Le handler LED utilise ce même filtre, donc une piste active
exclue reste éteinte. Le helper conserve sa réservation de 52 octets avec du
padding après RTS ; aucun symbole ou autre placement ne change.

`test_control_all_config.py` exécute les cinq boucles natives et les handlers
placés pour 64 masques × six pistes actives. Callbacks de paramètres, objets
UI/projet et pilote LED contrôlés ; branches, compteurs, pile, exclusions,
MACHINES et LEDs réels vérifiés. Press/release/repeat/long et transmission
des touches étrangères ou relâchées après un appui antérieur sont couverts.
Le build navigateur couvre Control All seul et la sélection complète avec
et sans ChordKeys/USB6. Le transfert simulé vérifie les blocs et le conteneur.

## Publication

Page `flasher-controls-test`, build `2026-10-13-controls-baseline-lfo`.
Recette et références intégrales publiées dans son dossier `source`.
Le flasher principal ne change pas. Pas de sauvegarde MIDI réintroduite.
Le gain CPU réel et le comportement matériel de Control All restent à tester.

Premier test matériel : fonctionnalité confirmée par le propriétaire, hormis
l’impossibilité d’exclure la piste active. Révision ci-dessus à vérifier sur
matériel ; toutes les boucles natives, dont le masque toutes pistes exclues,
sont revérifiées en émulation.

La même révision restaure le traitement LFO publié après le signalement de
ralentissement du premier test (note76). Cette restauration ne constitue
pas encore une preuve que les copies LFO étaient la cause ; test matériel
comparatif et audit des réservations Control All en cours.
