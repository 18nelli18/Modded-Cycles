# 114 — Premiere ouverture MIDI pendant la lecture

Demande AveyCole 17/10/2026 : rendre B utilisable lors de sa premiere ouverture pendant Play, sans quitter et revenir. Precisions : LEDs des premiers pas paraissent boucler et aucune sortie MIDI. Source : conversation. Adresses : VA OS1.13.

## Reponse courte

[FAIT] transport.s fermait explicitement ml_native_tick si le contexte paresseux ne correspondait pas a ml_start_context enregistre au dernier Play, ou si aucun Start n avait ete observe. Le contexte est volontairement absent avant premiere ouverture ; le premier Play memorise donc zero. Les tests historiques validaient cette fermeture.

Le candidat redirige uniquement deux branches conditionnelles vers l appel audio existant, avec now et playing courants. Une premiere ouverture demarre la sequence B depuis son premier pas au tick suivant ; aucune attente de nouveau Play. A continue sans remise a zero. Pour aligner un nouveau depart commun : Stop puis Play. Il ne s agit pas d une reconstruction retrospective de phase de chaque voie.

## Code et limites

ml_native_tick+0x32 :005c vers0050 ; +0x3c :0052 vers0046. Controle des instructions voisines et des adresses API de chaque recette relogee. Aucune allocation, nouveau payload, thread ou E/S audio ajoute. Start/Continue deja armes gardent leurs branches natives. ml_context nul reste inactif. Les fichiers MIDI restent charges seulement en B lecture arretee ; aucun acces disque ajoute pendant Play.

Le compositeur recalcule compression/references et source du loader repeat. Page flasher-midi-entry-test derivee du test quick-save2 : diagnostics conserves, correctif quick-save2 encore en verification et non considere resolu sur appareil. Principal et 909 inchanges.

## Preuves

Generator tools/gen_midi_entry_test.py --check, navigateur tools/test_midi_entry_flasher.js (toutes machines avec Banque, Banque seule sans Wizard, et sans Banque). Vrai boot navigateur puis tools/emu/test_midi_entry.py : reference bloquee sur17pas ; candidat102 note-on six canaux, curseur0..15 puis0, Stop/Start/Pause/Continue, pattern intact et zero allocation/sortie physique depuis IRQ. Horloge et files natives executees. LEDs, port physique et ouverture via boutons restent a verifier sur appareil.
