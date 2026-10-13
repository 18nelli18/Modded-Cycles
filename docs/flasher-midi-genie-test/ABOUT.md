# Audio LFO 2 sound saving — hardware tested

AveyCole confirmed hardware testing and authorized promotion to main on 12 October 2026.
Only five audio LFO 2 settings save with the sound: speed, multiplier, waveform,
destination and depth. Fade resets to 0x4000, start phase and mode reset to zero
when loading sounds. MIDI-bank saving remains unfinished and is not included.

The tested firmware writes, payloads, MIDI transfer implementation and reference
hashes are unchanged from flasher-lfo-save-test (2026-10-12-lfo2-native-save).
This promotion changes only user-facing documentation and tested metadata.

Credits: 18nelli18 MIT implementation, inspired by DavidCaruso.
Speed/depth use the upstream 8-bit saved precision.
Incompatible with Track Filter and LFO 2/3/4 (shared sound fields).
MACRO, ACID, Model-TG and the existing MIDI bank remain available.

## 2026-10-12-midi-genie-chance-reset

Experimental Sequence Genie fix: every Generate option clears per-step chance on the selected B-side lane; Undo restores the previous chance locks. Queued generation is cancelled if chance is edited before commit. A separate, parallel six-track MIDI OUT sequencer alongside the six audio tracks. FUNC + SETTINGS + TRACK opens B-side. Live recording: hold RECORD and press PLAY; press PLAY again while holding RECORD to switch quantized/unquantized recording. Keyboard and pad notes record into the selected MIDI lane. Unquantized timing uses 1/64-step resolution; recorded lengths use whole steps. Live recording was tested on hardware. Clearing a trig removes all its per-step settings and locks; re-adding starts at C5, velocity 100 and length 1. MIDI sequences and MIDI LFO settings remain RAM only. Audio LFO 2 saves its first five settings with the sound. All existing mod selections remain available.

Correction expérimentale Sequence Genie : toutes les options Generate effacent la chance de pas de la voie B choisie ; Undo restaure les locks précédents. Une édition chance avant commit annule le candidat en attente. Séquenceur MIDI OUT parallèle de six pistes, indépendant des six pistes audio. FUNC + SETTINGS + TRACK ouvre B. Live-rec : RECORD + PLAY ; PLAY avec RECORD maintenu bascule quantifié/libre. Notes clavier/pad enregistrées dans la voie MIDI choisie. Timing libre au 1/64 de pas ; durées en pas entiers. Live-rec testé sur matériel. Supprimer un trig efface ses réglages et locks ; le recréer donne C5, vélocité 100 et durée 1. Séquences et LFO MIDI en RAM seulement. Le LFO 2 audio sauve ses cinq premiers réglages avec le son. Toutes les sélections existantes restent disponibles.
