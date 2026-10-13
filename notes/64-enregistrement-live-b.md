# 64 — Enregistrement live dans les voies MIDI B

Demande d’AveyCole, 12/10/2026 : priorité au live-rec B, quantifié/libre avec les raccourcis natifs. Sources `midi_lanes/live_record*.s`, générateur `gen_midi_saving_test.py --audio-lfo --working --live-record`. Adresses : VA de l’OS 1.13.

## En bref

[FAIT en émulation] Le clavier et les pads MIDI B capturent note/vélocité dans la voie sélectionnée pendant le mode live-rec natif. RECORD + PLAY active ce mode ; une nouvelle pression PLAY, RECORD toujours maintenu, bascule la quantification native. La durée se termine au relâchement, au remplacement par une nouvelle note ou à l’annulation clavier. Aucune écriture dans les pistes audio.

## 1. Contrat natif

- `4006ba76` lit lecture active et UI+359 (live-rec).
- `4001334c` lit la quantification ; `400133ca` la bascule.
- Branche PLAY `4002449c` : RECORD maintenu active live-rec, puis bascule au prochain appui.
- UI B transmet REC/PLAY/STOP aux handlers globaux. STOP annule d’abord les notes clavier privées.

## 2. Capture et lecture

Chaque voie utilise son couple deadline/prochain pas et sa durée de pas. Lecture de l’horloge sous une section IPL7 courte ; capture/édition en UI IPL0. Quantifié : pas le plus proche. Libre : pas courant et retard positif 0..63/64. Le retard reste dans les bits2..7 du byte flags ; bits0/1 restent trig/slide. Le scheduler applique le retard sans déplacer sa grille nominale. Les durées enregistrées sont arrondies au pas entier, 1..64 ; ce n’est pas une capture de gate fractionnaire. Une nouvelle note clôt le gate précédent. La capture refuse paquets invalides, projet/pattern non joué, horloge arrêtée/pause et contexte absent. La release n’écrase pas un pas modifié entre-temps.

## 3. Sauvegarde et place

MBK4 garde exactement 4992 octets de données / 5024 de record. MBK2 et MBK3 restent lisibles ; MBK3 refuse les anciens bits réservés non nuls, même avec CRC valide. Les anciens builds de sauvegarde ne lisent pas MBK4. Les copies SEQ explicites et checkpoints WRK conservent les retards.

Réserve Model-TG portée de 8 à 9 blocs de 16384 octets ; sept blocs restent dans sa liste native. Le vrai boot vérifie les pointeurs et la décompression. ACID et MACRO sont conservés ; USB6 reste facultatif. [À FAIRE matériel] Charge/cache Model-TG et comportement du transport complet.

## 4. Preuves et limites

- `test_midi_live_record_mode.py` : getters et branche PLAY natifs, entrée live-rec et bascules répétées. Notifications et objets d’environnement simulés.
- `test_midi_live_record_capture.py` : six voies isolées, note/vélocité, quantification, wrap, timing libre, gates, nouvelle note, garde pause/paquet/édition concurrente.
- `test_midi_lane_keyboard.py --live-record` : vrais événements clavier/pad B, Stop, slide conservant le retard.
- `test_midi_lane_clock.py --conditions --live-record` : lecture des retards, vitesses/longueurs indépendantes, absence de dérive, heure musicale OS réelle ; charge audio physique non mesurée.
- Tests bundle, stockage/session et flasher : boot réel, MBK2/3→4, roundtrip offsets, WRK/SEQ, construction navigateur avec/sans USB6 et transport simulé exact.

Le build est expérimental. La capture MIDI externe entrante n’est pas ajoutée ici. Vérifier sur matériel entrée/sortie live-rec, quantification, notes tenues, sauvegarde/rechargement et redémarrage. Aucun firmware Elektron distribué : seulement sources propres et recettes de patches.
