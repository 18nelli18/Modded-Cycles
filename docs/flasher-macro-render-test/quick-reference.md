# Feature and shortcut overview

A.V.’s Supermodel Edition · 18 October 2026

Added gestures only; stock-style transport, copy, clear and paste actions are omitted.

Install the relevant feature first. Hold the first button while pressing or turning the next control. TRIG means a step key; pad means a track pad; DATA means LEVEL/DATA. MACHINES is the physical button sometimes called PRESET in sampler instructions.

## Current feature overview

Main flasher 1.83 · updated 18 October 2026. Install only the features you need; the flasher checks compatible combinations. [Supermodel 909 Edition](../flasher-supermodel-909/) has its own selection and release.

| Feature | Current behavior |
|---|---|
| Added machines | MACRO, ACID, WAVE, TINY, RETROSYN and the selectable Syntakt-derived engines. Syntakt engines require your own Syntakt OS file. |
| Swarm LITE | Replaces the seven-oscillator Swarm with three oscillators: fundamental plus two detuned saws. Lower CPU load, with a leaner and possibly quieter sound; heavy arrangements can still click. |
| Sample Wizard | Independent sampler with sample locks, playback modes, slicing and resampling. Sample Preview is hardware tested. Model-TG is retired from the main flasher. |
| RETROSYN / ChordKeys | Six retro oscillator types; ChordKeys adds scale-based chord playing and voicings. Choose any combination of the added machines; only checked machines appear. Sample Wizard is optional. |
| Per-track filter / Synth Attack | Added cutoff, resonance and attack controls; filter parameter locks and Control All. The released filter includes the repair for distortion after switching away from Sample Wizard. |
| Control All Config / Beat Repeat | Choose included audio tracks; momentary repeat across sixteen divisions, with a brief division popup. |
| MIDI Out Bank — experimental | Six parallel MIDI lanes with CC assignments/locks, slides, retrigger/arp, chance, two MIDI LFOs and project sidecar saving. Optional and installable without beat repeat. Beat repeat can also be installed without MIDI Out Bank. Outside record mode all available pages are lit and the playing page blinks. In record mode the selected page stays solid and the playing page blinks. Normal-mode entry inherits A-side selected page. Normal length is shared with A-side and editable from B: FUNC + PAGE opens Length without entering edit mode; press DATA then turn for exact length, or press PAGE for 16-step sizes regardless of edit selection. Per-track mode keeps independent MIDI lane lengths. |
| Sequence Genie / SCRAMBLE | Generate or mutate sequences, queue at Loop/Page boundaries, and randomize audio parameters or B-side CCs. |
| Arpeggiator / Second LFO | Held-note arpeggiation and an additional modulation page. Oct 0 cycles only held notes; 1–3 add octave copies. Hardware confirmed on both sides. |
| Performance and editing | Latching mutes, step preview, slide trigs, scrolling names, three-line browser, numeric volume/pan, dim trigless steps and trig-removal grace. |
| Routing / tempo / startup | Six-channel USB audio, combined MIDI OUT + THRU, tempo up to 546 BPM and a choice of startup animation. |

**Saving:** hold **FUNC + SETTINGS** for the restored stock permanent-save action. The confirmed repair also prevents FUNC remaining latched when leaving the save menu. For MIDI data, stop playback before saving and wait for **MIDI SAVED**. Saved MIDI loads **only when entering B-side, with playback stopped**; sidecar files are outside Elektron SysEx backups.

**Diagnostics:** CPU/peak/CUT displays belong to test builds only and are absent from main.

## Performance and sound

| Feature | Gesture | Result |
|---|---|---|
| Control All Config | TRACK + TRIG 1–6 | Include or exclude tracks from Control All. The selected track can also be excluded. Choices reset on power-off. |
| Control All Beat Repeat | Hold TRACK + RETRIG, then hold TRIG 1–16 | Repeat the included audio tracks. The newest held TRIG chooses the division and shows a brief popup. Release the division pad or either modifier to stop. Both modifiers must stay held. |
| Latching mute | Hold TRACK, tap FUNC | Keep mute mode open. Tap FUNC to leave. |
| Trig preview | While stopped or paused, hold TRIG + PAGE | Audition that step with its note and locks. |
| Audio slide trigs | SETTINGS + TRIG | Toggle a parameter slide on the step. |
| Synth Attack | MACHINES + DECAY | Set the added attack control on supported synth/drum tracks. |
| Per-track filter | MACHINES + SWEEP / CONTOUR | Cutoff / resonance. Hold TRACK as well for Control All over included audio tracks. Neutral is maximum cutoff and zero resonance. |
| MACRO lo-fi | FUNC + PITCH on a MACRO track | Left: 46K–4K sample rate; right: 12B–2B bit depth; centre: OFF. The value popup shows the setting. |

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

## Hardware-confirmed changes — now in main 1.83

[Open the Octave 0 + MIDI B-side cursor test](../flasher-arp-zero-test/?v=2026-10-17-arp-zero-test-2).

| Change | What to check |
|---|---|
| Octave 0 on A and B | FUNC + RETRIG → Oct. 0 cycles only held notes; 1 adds one octave, 2 adds two, 3 adds three. Existing saved settings keep their sound; only the displayed numbering changes. |
| B-side first entry / cursor | Open B-side during playback; verify MIDI starts without exiting/re-entering and that REC shows one cursor. Each lane retains its own length and speed. |
| Test setup | Keep Control All Beat Repeat selected when installing MIDI Out Bank in this combined test. That requirement does not apply to main. CPU/peak/CUT diagnostics remain available in the test. |

Octave 0, the B-side cursor and the crash repair were confirmed by AveyCole in test 2 and are now released in main 1.83. Saved MIDI loading still requires stopped playback. MIDI beat repeat and MIDI filter work were canceled and are not part of this test.

## LFO destinations and quick assignment — 1.90

Attack (ATK), Filter (FLT) and Resonance (RES) are selectable in either audio LFO when their modules are installed. Hold LFO + MACHINES and turn DECAY / SWEEP / CONTOUR to assign them; turn again to adjust depth. Without MACHINES, the knobs assign their ordinary parameters. Sample Wizard uses its native Filter / Resonance destinations on SWEEP / CONTOUR in either modifier state, with stable labels during movement. Both LFO menus stay open after quick assignment. MACHINES combinations do not leave the machine selector behind. Retrosyn labels are Timbre / Oscillator / Pitch Sweep / Chord Arp. Diagnostics remain test-only.

## Silent track selection - 1.91

Optional **Silent track selection** (hardware tested): plain T1-T6 pads select silently; **TRACK + pad** selects and plays, including live recording. Preset-browser preview is preserved. Unchecked by default.
