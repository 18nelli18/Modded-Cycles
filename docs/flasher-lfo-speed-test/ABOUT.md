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

## 2026-10-13-lfo2-speed-knob

LFO 2 input test: on A-side, the trig keyboard and pads remain playable while the page is open, and the physical LFO SPEED knob edits LFO 2 speed with stock range and direction, while other ordinary synth knob turns pass to the stock controls. Hold LFO and turn a knob for quick assignment as before. B-side LFO pages keep the keyboard and pads on their MIDI lanes and do not edit audio parameters. Includes native five-field LFO2 sound saving, live MIDI recording, complete trig clear and Genie chance reset. MIDI sequence saving is not included. New input routing needs hardware testing.

Test saisie LFO 2 : côté A, clavier TRIG et pads restent jouables dans la page ; le potard LFO SPEED édite la vitesse LFO 2 avec plage et direction natives ; les autres potards passent aux contrôles synthé natifs. LFO maintenu + potard conserve le quick assign. Les pages LFO B gardent clavier et pads sur leurs voies MIDI, sans modifier les paramètres audio. Sauvegarde native des cinq réglages LFO2, live-rec MIDI, reset trig et chance Genie inclus. Sauvegarde des séquences MIDI exclue. Nouveau routage à tester sur matériel.
