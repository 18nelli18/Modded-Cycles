# Feature and shortcut guide

Supermodel 2.17 - 22 October 2026

Main 2.17. Hold the first button while pressing the next button or turning the named knob. TRIG means a step key; pad means a track key; DATA means LEVEL/DATA. All listed features are included.

## Included features

**Machines and sound:** Six stock engines plus Sample Wizard, SD Vintage, Clap Vintage, SY Toy, SY Bits, Swarm LITE, MACRO, ACID, WAVE, Feral by Glycinate, Elder and MIDI Out. Elder is an original synth inspired by Junior by Fors.

**Performance and sequencing:** Arpeggiator, held-note octave 0, ChordKeys and harmony locks, Sequence Genie, SCRAMBLE, slides, trig preview, Step Recorder, latching mute and solo.

**Filters and effects:** Per-track attack and resonant two-pole Polivoks-style lowpass; Wizard internal lowpass; second LFO; MACRO fine tune and Lo-Fi; Reverb/Chorus I/Chorus II and Delay/Crush/Both.

**Routing and workflow:** MIDI Out with nine CC knobs, locks and two MIDI LFOs; MIDI OUT/THRU toggle; USB stereo or six tracks; permanent quick save, saved Mod Setup and optional DX diagnostics.

## Track, step and performance controls

| Feature | Controls | Behavior |
|---|---|---|
| Step Recorder | Playback stopped: press REC twice; PLAY advances; STOP goes back; press REC again to exit | Enter step recording and play notes to write successive steps. PLAY advances one step; STOP moves back one step; press REC again to leave Step Recorder. |
| Latching mute | TRACK + tap FUNC | First choose Mute: LTC in Mod Setup. Then latch mute mode with this gesture; tap FUNC again to leave. Mute: Stk keeps stock behavior (default). |
| Solo in mute mode | In latching mute mode, hold FUNC + press T1–T6 | Solo that track. Press the soloed track again to restore the previous mute state; tracks already muted remain muted. |
| Silent track selection | Choose Silent in Mod Setup ; tap T1–T6 | Select a track without triggering its sound. TRACK + pad selects and plays. Stock pad behavior (Stk) is the default; select Silent to enable silent selection. |
| Trig preview | Hold TRIG + PAGE | Audition the selected step with its note and locks while stopped or paused. |
| Slide trig | SETTINGS + TRIG | Toggle a parameter slide on the step. |
| Sequence Genie | SETTINGS + PAGE | Open the generator for the selected track. Select with DATA; choose Generate or Queue and set Loop/Page timing. |
| SCRAMBLE | Quick tap SETTINGS + TRACK | On release, randomize supported synthesis parameters for the selected track. SCRAMBLE is able to be parameter-locked to steps in the sequencer. |
| Control All setup | TRACK + TRIG 1–6 | Include or exclude audio tracks from Control All changes. |
| Audio beat repeat | Hold TRACK + RETRIG , then hold a TRIG 1–16 | The held step selects a repeat division for included audio tracks. Release a modifier or division pad to stop. |
| Control All filter | Hold TRACK + MACHINES ; turn SWEEP / CONTOUR | Adjust cutoff/resonance across included audio tracks. Without TRACK, adjust the selected track. |
| Synth Attack | MACHINES + DECAY | Adjust the added attack control on supported machines. |
| Arpeggiator / ChordKeys settings | FUNC + RETRIG | Open the settings for the active Arpeggiator or ChordKeys feature. Arpeggiator octave 0 cycles only through held notes. |
| ChordKeys | Select the Chord machine, then play TRIG 1–16 | Play scale-based chord voicings from the step keys. To leave a ChordKeys track you must use TRACK + Track Pad. |
| ChordKeys harmony locks | Grid record: hold a step TRIG and press T1-T6 . Live record: play a chord and use the harmony pads. | Record the chosen harmony on the step. Press the same harmony pad again on a held grid step to restore its base harmony. Harmony locks save with the pattern independently of LFO 2. |

## Effects and Elder

| Feature | Controls | Behavior |
|---|---|---|
| Chorus / Reverb mode | TRACK + REVERB SIZE | Turn right: Reverb → Chorus I → Chorus II; left to go back. Chorus I is slower/smoother; II is faster/deeper. Reverb restores normal Size/Tone. |
| Chorus Speed / Depth | REVERB SIZE / FUNC + REVERB SIZE | Speed / Depth, each 0–127. REVERB SEND sets the amount per track. Start at Speed 42, Depth 64 with a modest send. |
| Delay / Crush / Both mode | TRACK + DELAY TIME | Turn right: Delay → Crush → Both; left to go back. Crush processes the send immediately; Both crushes the delay echoes. |
| Delay Time / Feedback | In Delay mode: TIME / FUNC + TIME | Normal delay Time / Feedback. To adjust them in Both, switch to Delay, adjust, then return to Both. Delay and crusher settings remain separate. |
| Crusher Rate | In Crush/Both: DELAY TIME | Rate 0–127, about 750 Hz–48 kHz. Lower is rougher; higher is cleaner. DELAY SEND sets the amount per track. |
| Crusher Bits | In Crush/Both: FUNC + DELAY TIME | Bits 2–16. Fewer bits sound crunchier. Start at Rate 96, Bits 12 with a modest Delay Send. |
| Effect settings and save | Release TRACK; stop playback | Effect modes and crusher Rate/Bits are global and save after playback stops. Rate/Bits are not p-lock destinations; track sends retain their locks. Chorus Speed/Depth use the pattern’s Reverb Size/Tone values. Both adds processing cost. |
| Elder controls | Select Elder in MACHINES | COLOR = Wave; SHAPE = Warp; SWEEP = Noise; CONTOUR = Motion. PITCH, DECAY, PUNCH, Gate and Fine remain available. Original synth inspired by Junior by Fors. |
| Saved Retrosyn sounds | Elder replaces ChpHzrd / Retrosyn | The same machine slot now plays Elder, so previous Retrosyn sounds change timbre. The other engines and previous CPU fixes are retained. Feral is by Glycinate. |

## LFO and MACRO controls

| Feature | Controls | Behavior |
|---|---|---|
| Second audio LFO | Press LFO twice | Open LFO 2 and edit its speed, shape, destination and depth. |
| LFO quick assignment | On an LFO page, hold LFO and turn a destination knob | Assign the corresponding ordinary knob destination. To select the added Attack, Filter or Resonance targets, also hold MACHINES . |
| Attack / Filter / Resonance LFO targets | On an LFO page, hold LFO + MACHINES while turning DECAY , SWEEP or CONTOUR | Select Attack, Filter or Resonance as supported by the machine. Release MACHINES for ordinary knob control. Sample Wizard labels its native filter controls Filter and Resonance. |
| MACRO fine tune | SETTINGS + turn PITCH | Adjust fine pitch. Plain PITCH retains its regular control; FUNC + PITCH is MACRO Lo-Fi. Lo-Fi lowers sample rate to the left, bit depth to the right, with OFF at center. Model names and numbers 0–46 are shown. |

## Sample Wizard and saving

| Feature | Controls | Behavior |
|---|---|---|
| Sample Preview | FUNC + MACHINES ; highlight a sample, then press its track pad or keyboard trig | Audition the highlighted sample. Scrolling through the list remains silent. |
| Sample lock | Open the sample selection menu and highlight a sample; then hold a step TRIG + MACHINES | Lock the highlighted sample to that step on a Sample Wizard track. The sample browser must be open with the desired sample selected. |
| Playback modes | SETTINGS + MACHINES | All seven modes: One-Shot, Loop, Slice, Granular, Stretch, Pluck and Wavetable. SETTINGS + PUNCH opens options for the current mode. |
| Slice editor | FUNC + step key; FUNC + click DATA | Play upper slices; remove a slice marker with the DATA click. Marker knobs can snap to zero crossings. |
| Permanent quick save | Hold FUNC + SETTINGS | Save the project permanently using the stock quick-save action. |

## MIDI Out machine

| Feature | Controls | Behavior |
|---|---|---|
| Select and set up | MACHINES : MIDI Out; FUNC + TRACK | Silent MIDI track. Track Setup: Channel, Output, KbT (keyboard transpose), Pad Note. Turn DATA to select; click DATA before editing; BACK exits. Channel: 1-16 / Global. Output: Global / Off / USB / DIN / Both. |
| CC assignment and locks MIDI Out machine only | SETTINGS + gray knob; hold steps + assigned knob for locks | Assign OFF or CC0-127 to nine knobs. Turn a knob alone to send its value. Each lock keeps the CC number and value. Live recording captures knob changes. Chance and Swing retain their stock controls. |
| Two MIDI LFOs | LFO : LFO 1, LFO 2, track screen; BACK exits | DATA selects; click to edit. Order: Wav, Mul, Dst, Dep, Speed, Fade, Phase, Mode. LFO Speed adjusts the open LFO. Hold LFO + an assigned CC knob: assign destination, then turn further for depth. |
| Notes and save | Normal note/grid controls; FUNC + PAGE ; FUNC + SETTINGS | Incoming MIDI notes use the track receive channel or auto channel; live and step recording keep notes, velocity and length. FUNC + PAGE edits pattern length. Project/quick save keeps MIDI settings and locks. |
| MIDI OUT + THRU | CONFIG → MIDI → PORTS → OUT/THRU: THR; then FUNC + click DATA | Toggle the Cycles’ own outgoing MIDI while retaining incoming MIDI Thru. |

## Mod Setup

Hold SETTINGS + TRACK until Mod Setup opens, then release both buttons. A short tap runs SCRAMBLE on release. DATA selects a row; click to edit, turn, click again to return. Stk = Stock; SIL = Silent; LTC = Latch.

| Feature | Controls | Behavior |
|---|---|---|
| Pad | Stk / SIL Default: Stk | Stk keeps the original track-pad behavior: a pad selects and plays its track. Silent selects the track without sounding it; hold TRACK and press a track pad to select and play. ChordKeys tracks still require TRACK + track pad to leave the track. |
| USB | 2ch / 6ch Default: 2ch | 2ch sends the stereo mix to the computer. 6ch sends six separate mono tracks, before pan and without the mix delay/crusher/reverb/chorus returns. Stereo audio from the computer to Cycles works in both modes. Stop playback before changing this toggle. Changing modes reconnects the USB audio device; select its new channel layout in your DAW if needed. |
| Num | Off / On Default: Off | Off keeps the original volume and pan display. On shows numeric volume and pan values when you adjust those controls. |
| Mute | Stk / LTC Default: Stk | Stk keeps the original momentary mute controls. With LTC selected, hold TRACK and tap FUNC to stay in mute mode, then tap track pads to mute or unmute. Tap FUNC again to leave. In latched mute mode, hold FUNC and press a track pad to solo it; press the soloed pad again, or leave mute mode, to restore the previous mutes. |
| Delay | Stk / Div Default: Stk | Stk preserves the original Delay Time display and timing. Div displays musical divisions, including dotted and triplet values, and corrects the matching timing positions to exact divisions of the tempo. Other Delay Time positions retain their original timing; this does not quantize every knob position. Applies while using Delay mode. |
| DX | Off / On Default: Off | Enable the A/P/O/N popup after beat repeat: average and peak audio load, overloaded blocks and newly cut voices. Counters reset after the popup. Off disables the popup and counters. Saved with the other Mod Setup preferences. |

These are global preferences. BACK closes Mod Setup and saves all six choices together. If playback is running, the save waits until it stops. Stop playback and allow saving to finish before powering off. Saved choices return after reboot. Effect modes and crusher settings also save after playback stops.

Startup defaults: stock pads and mute behavior; USB 2ch; Num Off; DX Off. Reverb and Delay are the default effect modes when no effect preferences are saved. Six-channel USB excludes the stereo effect returns.
