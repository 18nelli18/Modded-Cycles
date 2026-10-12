# 61 — Conditions de trig dans la banque MIDI B

Demande directe d'AveyCole, 12/10/2026 : conserver les choix et l'affichage
CHANCE stock sur les pas B, indépendamment des pistes audio. Générateur :
`tools/gen_midi_retrigger_test.py`, recette :
`docs/flasher-test-3/source/midi-retrigger.json`. Adresses : VA de l'OS1.13.
Statut expérimental ; aucun résultat matériel annoncé pour cette addition.

## Fonctionnement

REC actif : maintenir un ou plusieurs trigs B puis tourner CHANCE. Le menu
Chance reste dans B ; DATA édite également le choix affiché ; BACK revient
à la banque. Sans trig maintenu, CHANCE change le défaut de la voie.
Les choix sont ceux du formatter natif : FILL, PRE, NEI,1st et inverses,
probabilités natives et ratios A:B. Le choix hérité est affiché comme stock
et vaut100% en l'absence de défaut. Les noms/valeurs sont lus dans l'OS
utilisateur à l'exécution ; aucune table native extraite n'est distribuée.

L'encodeur CHANCE est13 (paramètre natif22), DATA est1. Le delta vient de
`0x4006f73a`. Le formatter de condition est `0x40050046`, sa table de noms
`0x40108f54`. Les inverses gardent le trait graphique stock. Aucun objet
conditionnel ni observer de piste A n'est construit.

Le dernier octet des records privés retrigger8 contient0 pour héritage,
1..101 pour probabilité explicite0..100%,102..165 pour index natif0..63.
Le menu écrit uniquement0 ou102..165. La copie de voie transporte les locks,
la suppression d'un pas et clear les effacent. L'historique96 contient six
records16 : dernier résultat, premier passage et phases modulo1..8.
PRE/inverse ne remplacent pas le résultat mémorisé ; NEI lit seulement le
voisin B précédent. Start et changement de pattern réinitialisent les phases,
Pause/Continue les conservent. Tirage xorshift privé par voie, sans RNG audio.

Une condition refusée n'émet aucun Note On et libère le propriétaire repeat
antérieur. Une condition acceptée arme les réglages retrigger/arp habituels.
PAGE maintenu fournit FILL momentané B ; l'état momentané natif de la voie
`0x40fde812+lane` et le latch natif `0x40fde818` sont également lus sans écriture.
Ces champs sont confirmés dans la routine conditionnelle native `0x400913f0`.

## Placement et preuves

Huit blocs cache sont réservés, huit restent liés pour le disque. La vraie
initialisation native `0x4007929c` est exécutée en émulation : pointeurs
avant/arrière cohérents, code préservé. Le helper condition_eval240o utilise
un masque sprite libre sélectionné/validé par le générateur ; son pointeur
image est redirigé vers le doublon conservé. Les8o de contexte merger passent
dans la banque décompressée. La recette décrit toutes les écritures ; aucune
extension du format ou de l'adresse limite firmware. Marge image finale8o.

Preuves exécutées :
- test_midi_lane_chance.py : les64 valeurs/formatters natifs, marqueurs inversés,
  toutes probabilités, historique et trois cycles de chaque ratio.
- test_midi_chance_menu.py : encodeur physique, DATA,64 choix, héritage,
  locks multiples, release sans suppression, BACK et FILL, isolation A.
- test_midi_lane_retrigger.py --conditions : gate réel pattern_tick, Off,
  FILL/PRE/inverses et probabilité0, retrigger/arp et saturation.
- test_midi_lane_clock.py --conditions : Start/Pause/Continue, wraps par voie,
  sept vitesses et avance musicale OS30..546BPM.
- test_midi_bank_bundle.py --pattern-banks --stock-display --lfo-cc --retrigger
  --conditions : vrai boot TG/Syntakt, décompression/cache, helper dans son
  masque final, chemin compact publié, FILL natif, notes DIN/USB et worker.
- test_midi_retrigger_flasher.js : démarrage EN/FR, références avec/sans USB6,
  construction et transfert UI simulé685blocs, CRC/conteneur exacts.

Le transport physique et la charge disque/audio restent à tester sur matériel.
Les séquences, locks et LFO B restent en RAM ; sauvegarde non implémentée.
La saisie live quantifiée/non quantifiée, nudge et clipboard par pas sont
encore à faire. Le flasher principal n'est pas modifié par ce candidat.
