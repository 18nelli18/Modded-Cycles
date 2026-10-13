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
