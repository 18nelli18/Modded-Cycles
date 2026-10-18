# Supermodel 909 — feature and shortcut overview

909.7 · 18 October 2026

Fixed 909 Edition: six 909 voices, Sample Wizard, ACID, per-track filter, slide trigs, Sequence Genie, SCRAMBLE, Second LFO, MIDI Out Bank with saving, combined MIDI OUT + THRU, latching mute, Control All Config, Control All Beat Repeat, A/B arpeggiators and 909 startup. Load official Cycles OS1.13 and four local WAVs for closed/open hats, crash and ride. No sample audio is hosted.

Shared features match main1.89: the filter transition repair, stock permanent save (hold FUNC + SETTINGS), A/B Oct0, first-entry B playback and one recording cursor. Normal pattern length is shared between A and B and editable from either side. In B, FUNC + PAGE opens Length: press DATA before turning, or press PAGE for 16-step sizes regardless of edit selection. Per-track mode keeps independent MIDI lengths. Page LEDs follow stock REC/non-REC modes; entering B inherits the selected A page in normal mode. MIDI speeds remain independent. Main hardware-confirmed fixes; 909 integration checked in emulation. No diagnostic display in this release.

Stop before saving MIDI and wait for MIDI SAVED. Saved MIDI loads only when entering B-side with playback stopped; sidecar files are outside Elektron SysEx backups.

Added shortcuts below; stock-style transport/copy/clear/paste omitted. TRIG = step key, pad = track pad, DATA = LEVEL/DATA.

## Performance and sound

| Feature | Gesture | Result |
|---|---|---|
| Sample Preview | FUNC + MACHINES, highlight a sample, then play a pad or keyboard | Audition in the Sample Wizard browser before loading. |
| Control All Config | TRACK + TRIG 1–6 | Include or exclude tracks from Control All. The selected track can also be excluded. Choices reset on power-off. |
| Control All Beat Repeat | Hold TRACK + RETRIG, then hold TRIG 1–16 | Repeat the included audio tracks. The newest held TRIG chooses the division and shows a brief popup. Release the division pad or either modifier to stop. Both modifiers must stay held. |
| Latching mute | Hold TRACK, tap FUNC | Keep mute mode open. Tap FUNC to leave. |
| Trig preview | While stopped or paused, hold TRIG + PAGE | Audition that step with its note and locks. |
| Audio slide trigs | SETTINGS + TRIG | Toggle a parameter slide on the step. |
| Synth Attack | MACHINES + DECAY | Set the added attack control on supported synth/drum tracks. |
| Per-track filter | MACHINES + SWEEP / CONTOUR | Cutoff / resonance. Hold TRACK as well for Control All over included audio tracks. Neutral is maximum cutoff and zero resonance. |

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

Long audio slices halve at slow tempos to fit the history buffer. Beat repeat affects internal audio; it does not repeat outgoing MIDI notes.

## Sequence Genie, SCRAMBLE and modulation

| Feature | Gesture | Result |
|---|---|---|
| Sequence Genie | SETTINGS + PAGE | Open the generator for the selected audio track or B MIDI lane. DATA selects; click, turn, click to edit. Generate is first; Queue is second. Loop waits for the selected track’s next loop, Page for the next 16-step page. |
| A-side SCRAMBLE | SETTINGS + TRACK | Randomize four synthesis controls. Sampler tracks are excluded. |
| A-side step SCRAMBLE | Hold TRIG(s), then SETTINGS + TRACK | Toggle fresh randomized values on those steps each pass, retaining the base sound. |
| B-side SCRAMBLE | SETTINGS + TRACK | Randomize the selected lane’s assigned MIDI CC values. |
| Second LFO | Press LFO twice | Open LFO 2. On its page, LFO SPEED edits LFO 2. |
| LFO 2 quick assignment | On A-side LFO 2, hold LFO and turn a parameter knob | Select that destination; further turning adjusts signed depth. |
| Scale Lock | FUNC + PAGE | Access added scale/key settings with the performance support installed. |
| A/B arpeggiator settings | FUNC + RETRIG | On either side, set arp direction and Oct0–3. Oct0 uses only held notes. |
| A/B arpeggiator performance | Hold RETRIG while holding notes | Play the held notes through the arpeggiator; A.On provides its latch option. |

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
