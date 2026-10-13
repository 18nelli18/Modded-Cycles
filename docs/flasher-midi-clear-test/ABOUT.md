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

## 2026-10-12-midi-trig-clear

Clearing a B-side trig now removes its note, velocity, length, slide, timing and per-step chance/retrigger/arp locks. Re-adding the step starts at C5, velocity 100 and length 1 with no locks. Other steps, lane defaults and A-side tracks remain unchanged. Experimental trig-clear fix; saving MIDI sequences remains unfinished. The hardware-tested audio LFO 2 sound-save feature remains included (only five settings saved).

Supprimer un trig B efface note, vélocité, durée, slide, timing et locks chance/retrigger/arp. Le recréer donne C5, vélocité 100 et durée 1 sans lock. Les autres pas, défauts de voie et pistes A sont inchangés. Correction expérimentale ; sauvegarde des séquences MIDI inachevée. La sauvegarde du LFO 2 audio testée sur matériel reste incluse (cinq réglages sauvés seulement).
