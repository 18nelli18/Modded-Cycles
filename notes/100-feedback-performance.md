# 100 — Popup beat repeat et LEDs mute B

Demande AveyCole dans cette conversation, 16/10/2026 : afficher brievement la division beat repeat et retrouver les LEDs mute natives pendant FUNC cote B. Derniere correction utilisateur : aucun surlignage de piste selectionnee pendant FUNC. Publication en test uniquement, verification materielle attendue. Adresses : VA de l'OS 1.13.

## En bref

Deux changements UI independants : beat repeat seul affiche sa division ; MIDI seul utilise le masque B pour ses pads. Compatibles ensemble et avec les autres cartes. Le principal 1.73 et ses octets restent inchanges.

## 1. Popup bref

`select_held` compare ancienne/nouvelle division. Un nouvel index valide appelle `br_popup` depuis le clavier UI seulement, avec TRACK + RETRIG et sans annulation/IPL. Releases finales, touches repetees et rendu audio n'allouent pas de popup. Retour a une autre touche encore tenue affiche sa division. Les seize labels vont de 1/64 a 1 BAR.

`popup.s` reprend le helper propre du support commun : chaine native 0x400f980c, constructeur Popup 0x400747c0, presentation 0x4007700e et destruction des references temporaires. Duree courte native, aucun multiplicateur de maintien. Aucun pointeur vers une chaine locale de pile. Le code et ses pointeurs sont reloges par le generateur habituel ; module 2 572 octets, chargeur ROM identique (104 octets). Aucun ajout au rendu audio ou au stockage.

## 2. LEDs mute B

[FAIT] Le backend epingle calcule auparavant toujours l'etat pad depuis `mlp_track`. Le candidat remplace seulement ce bloc de 14 octets, avec signature exacte et appel vers `mute_feedback.s`. Hors FUNC : meme selection (etat 3), autres pads eteints (1). Pendant FUNC : enabled=1 et mute=0 donne allume fixe (2), sinon eteint (1), y compris piste selectionnee. Donnees B de 264 octets par piste ; aucune lecture de mute audio A.

Le chemin serial/pulse B reste apres le writer, identique. `mlp_pulse_guard` continue de filtrer les pulses A. Le wrapper du poll compare `mlp_func`, invalide les LEDs lors de chaque transition, puis rejoue le tick de potards d'origine et reprend le poll a +6. Ainsi le changement reste visible transport arrete. Allocation nulle dans les callbacks LED. Export des nouveaux symboles et ML_BANK_END pour le relogement dynamique et les extensions de sauvegarde.

## 3. Generation et preuves

```
python3 tools/gen_midi_current.py --mute-feedback --output build/feedback-midi-data.js
python3 tools/gen_beat_repeat.py --catalog build/midi-persistence-main/all.json --catalog build/midi-persistence-main/alone.json --catalog build/midi-persistence-main/supports.json --catalog build/midi-persistence-main/wizard-chord.json --catalog build/midi-persistence-main/all-native.json --output build/feedback-beat-data.json
python3 tools/gen_performance_feedback_flasher.py --beat-data build/feedback-beat-data.json --midi-data build/feedback-midi-data.js
node tools/test_beat_repeat_flasher.js --feedback
```

GCC m68k-linux-gnu 15.2, -mcpu=54418. Onze builds navigateur signes : neuf profils beat repeat et deux profils MIDI sans repeat. Preuves sur leurs vrais SYX : boot/cache natifs, seize labels sans doublon, gestes maintenus et 64 masques Control All ; LEDs B sur 64 masques x six selections, retour hors FUNC, pulses B seuls, invalidation arretee. Controle des saves existants et parite Python/navigateur. Seuls singletons peripheriques et objets UI externes sont simules ; aucune affirmation de test physique.

## 4. Essai materiel attendu

Verifier la lisibilite et disparition rapide du popup, les releases TRACK/RETRIG pendant son affichage, changements rapides et dernier TRIG tenu. Dans B, tenir FUNC puis muter/demuter les six pistes, transport lance et arrete : aucun surlignage de selection ; pistes non coupees fixes ; coupees sombres sauf notes B. Relacher FUNC restaure la selection. Tester avec et sans Wizard, Genie, RETROSYN/TINY, et sauvegarde MIDI. Aucun changement principal avant confirmation AveyCole.
