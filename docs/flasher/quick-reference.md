# New feature shortcut guide

A.V.’s Supermodel Edition · 16 October 2026

Added gestures only; stock-style transport, copy, clear and paste actions are omitted.

Install the relevant feature first. Hold the first button while pressing or turning the next control. TRIG means a step key; pad means a track pad; DATA means LEVEL/DATA. MACHINES is the physical button sometimes called PRESET in sampler instructions.

## Performance and sound

| Feature | Gesture | Result |
|---|---|---|
| Control All Config | TRACK + TRIG 1–6 | Include or exclude tracks from Control All. The active track follows the native active-track exception. Choices reset on power-off. |
| Control All Beat Repeat | Hold TRACK + RETRIG, then hold TRIG 1–16 | Repeat the included audio tracks. The newest held TRIG chooses the division and shows a brief popup. Release the division pad or either modifier to stop. Both modifiers must stay held. |
| Latching mute | Hold TRACK, tap FUNC | Keep mute mode open. Tap FUNC to leave. |
| Trig preview | While stopped or paused, hold TRIG + PAGE | Audition that step with its note and locks. |
| Audio slide trigs | SETTINGS + TRIG | Toggle a parameter slide on the step. |
| Synth Attack | MACHINES + DECAY | Set the added attack control on supported synth/drum tracks. |
| Per-track filter | MACHINES + SWEEP / CONTOUR | Cutoff / resonance. Hold TRACK as well for Control All over included audio tracks. Neutral is maximum cutoff and zero resonance. |
| MACRO lo-fi | FUNC + PITCH on a MACRO track | Left reduces sample rate; right reduces bit depth. |

### Beat repeat divisions

| TRIG | Division | TRIG | Division |
|---|---|---|---|
| 1 | 1/64 | 9 | 3/16 |
| 2 | 1/48 | 10 | 1/4 |
| 3 | 1/32 | 11 | 1/3 |
| 4 | 1/24 | 12 | 3/8 |
| 5 | 1/16 | 13 | 1/2 |
| 6 | 1/12 | 14 | 2/3 |
| 7 | 1/8 | 15 | 3/4 |
| 8 | 1/6 | 16 | 1 bar |

Long audio slices halve at slow tempos to fit the history buffer. The released audio repeat does not repeat outgoing MIDI notes; the MIDI test below adds B-note retriggering.

## Sequence Genie, SCRAMBLE and modulation

| Feature | Gesture | Result |
|---|---|---|
| Sequence Genie | SETTINGS + PAGE | Open the generator for the selected audio track or B MIDI lane. DATA selects; click, turn, click to edit. Queue chooses Loop or Page boundaries. |
| A-side SCRAMBLE | SETTINGS + TRACK | Randomize four synthesis controls. Sampler tracks are excluded. |
| A-side step SCRAMBLE | Hold TRIG(s), then SETTINGS + TRACK | Toggle fresh randomized values on those steps each pass, retaining the base sound. |
| B-side SCRAMBLE | SETTINGS + TRACK | Randomize the selected lane’s assigned MIDI CC values. |
| Second LFO | Press LFO twice | Open LFO 2. On its page, LFO SPEED edits LFO 2. |
| LFO 2 quick assignment | On A-side LFO 2, hold LFO and turn a parameter knob | Select that destination; further turning adjusts signed depth. |
| Scale Lock | FUNC + PAGE | Access added scale/key settings with the performance support installed. |
| Arpeggiator / ChordKeys settings | FUNC + RETRIG | Access the added direction/octave or ChordKeys options, according to the installed feature. |
| Arpeggiator performance | Hold RETRIG while holding notes | Play the held notes through the arpeggiator; A.On provides its latch option. |
| ChordKeys | On a CHORD track, play TRIG 1–16 | 1–7: I–VII; 8–14: one octave up; 15–16: I–II two octaves up. |

## Sample Wizard and sample preview

| Feature | Gesture | Result |
|---|---|---|
| Sample lock | Hold a step TRIG + MACHINES | Choose a sample lock for that step on a Wizard track. |
| Playback modes | SETTINGS + MACHINES | Open the sampler’s playback-mode controls. |
| Mode options | SETTINGS + PUNCH | Open the selected sampler mode’s options. |
| Resampling | SETTINGS + REC | Open resampling controls. |
| Sample Preview — hardware tested | FUNC + MACHINES; highlight a sample, then play its track pad or keyboard TRIG | Audition the highlighted sample in the Wizard browser. Scrolling alone is silent. Compatible with ChordKeys and WAVE. |
| Slice editor: upper slices | Hold FUNC + TRIG 1–16 | Play slices 17–32 while the slice editor is open. |
| Slice editor: zero crossing | FUNC + marker knobs 1 / 2 | Snap the respective slice marker to a zero crossing. |
| Slice editor: remove marker | FUNC + click DATA | Remove a slice marker. DATA alone splits; PUNCH controls tap slicing. |

## MIDI B-side and routing

| Feature | Gesture | Result |
|---|---|---|
| Enter / leave MIDI B-side | FUNC + SETTINGS + TRACK | Open or close the six parallel MIDI tracks. Use the combo from B home to exit; BACK there also exits. |
| MIDI CC assignment | SETTINGS + a gray knob | Assign that knob to a MIDI CC on the selected B lane. |
| MIDI CC lock | Hold TRIG + an assigned knob | Add a CC parameter lock to that MIDI step. |
| MIDI note / CC slide | SETTINGS + TRIG | Enable or disable a slide. Notes overlap for legato; CCs glide toward the marked step’s values. |
| MIDI keyboard setup | FUNC + TRACK | Set keyboard transpose and Pad Note. |
| MIDI CC LFO 2 | Press LFO twice on B-side | Open the second MIDI CC LFO. In Dst, click DATA, choose OFF or CC0–127, then click DATA to confirm; BACK cancels. |
| Combined MIDI OUT + THRU | Set CONFIG → MIDI → PORTS → OUT/THRU to THR, then FUNC + click DATA | Toggle the Cycles’ own outgoing MIDI while retaining incoming MIDI Thru. |

Saved MIDI loads only when entering B-side while playback is stopped. Stop before Save Project and wait for MIDI SAVED. Sidecar MIDI files are outside Elektron SysEx backups.

## Separate MIDI performance test

These two additions are experimental and available only on the [MIDI performance test page](../flasher-midi-performance-test/?v=2026-10-16-midi-performance-test-1), currently using the fixed six-voice 909 profile and four local WAVs.

| Feature | Gesture | Result |
|---|---|---|
| MIDI beat repeat | Hold TRACK + RETRIG, then hold a division TRIG | Retrigger each included B lane’s latest sequenced note, using its current MIDI channel and port. Release stops the repeated notes. This repeats notes rather than capturing a MIDI phrase; native A-side MIDI output is outside this test. |
| B-side Control All filter: audio + MIDI | In B-side, hold TRACK + MACHINES and turn SWEEP / CONTOUR | Update included internal audio filters and send CC74 / CC71 to the configured B instruments. MIDI-muted lanes receive no CC; their internal audio filters still change. |
