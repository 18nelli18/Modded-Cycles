# 115 — Phase de lecture et curseur MIDI B

Demande AveyCole du 17/10/2026 : supprimer le second curseur pendant REC et joindre la phase A lors de la premiere ouverture B, en conservant les longueurs propres. Test uniquement, diagnostics conserves. Adresses : VA OS1.13.

## En bref

[FAIT en emulation] Le garde de pulse bloque les LEDs de pas A pendant B. Le curseur prive B utilise son passage dedie. En sortant B, les pulses A redeviennent natifs. Le premier contexte MIDI cree pendant Play rejoint la phase native ; les voies gardent leur longueur et vitesse.

## Implementation

`gen_midi_cursor_test.py`, `cursor_guard.s`, `cursor_phase.c/s`. Module612octets ajoute au transport du beat repeat, seulement dans `flasher-midi-entry-test`. Le wrapper appelle une fois le natif0x40053330, conserve d0/d1/a0/a1/SR, puis rejoint le contexte paresseux. Aucun changement des sources de donnees A.

Phase : pas0x40a7886c, sous-compteur0x40a78866, vitesse0x40a788b5, table0x4010afa4, prochaine horloge0x40a78628, maintenant0x8000184c. Les six voies sont validees avant publication ; initialisation des conditions comme le demarrage normal. Pas de notes de rattrapage ni allocation dans le tick.

La phase initiale utilise le cycle A courant, pas un historique absolu des boucles. Apres jonction, l'horloge B poursuit ses propres cycles. Chargement des MIDI sauvegardes toujours reserve a l'entree B avec lecture arretee.

## Validation

`test_midi_cursor_flasher.js` : builds all-midi, bank-alone, no-midi verifies et signes. `test_midi_cursor.py` :7vitesses A x7vitesses B x4fractions x6longueurs(5,7,12,16,31,64), deadlines, pas, absence de reseed/allocation ; six pistes xquatre pages xdeux modesREC/clavier. Wrapper natif et registres verifies. Snapshots natifs simules ; code prive et garde executes dans Unicorn.

[A FAIRE] Verification physique de l'entree pendant Play, du curseur unique REC et des longueurs/vitesses distinctes. Inclut la sauvegarde rapide confirmee test3. Ni diagnostics ni curseur experimental promus dans main.
