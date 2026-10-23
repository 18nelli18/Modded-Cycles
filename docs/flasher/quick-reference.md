# Feature and shortcut guide

Supermodel 2.27 - 23 October 2026

Main 2.27. Hold the first button while pressing the next button or turning the named knob. TRIG means a step key; pad means a track key; DATA means LEVEL/DATA. All listed features are included.

## Included features

**Machines and sound:** Six stock engines plus Sample Wizard, SD Vintage, Clap Vintage, SY Toy, SY Bits, Swarm LITE, MACRO, ACID, WAVE, Feral by Glycinate, Elder, TINY, Shadow and MIDI Out. Elder is an original synth inspired by Junior by Fors. Machine browsing retains synth values; Wizard’s four dials stay separate while MACHINES stays open.

**Performance and sequencing:** Arpeggiator, held-note octave 0, ChordKeys and harmony locks, Sequence Genie, SCRAMBLE, slides, trig preview, Step Recorder, latching mute and solo.

**Filters and effects:** Polivoks-style track/Wizard filters, second LFO, MACRO Fine/Lo-Fi; Delay/Crush combinations, Chorus 1/2 + Reverb and Vinyl + Reverb. FX menus apply only on TRACK release. Opaque FX overlay; SETTINGS + Size/Time adjusts Tone/Feedback in combined modes. Vinyl dust continues through musical gaps. Includes stereo Ping Pong, full-octave Shimmer 1 and the earlier mixed/diffuse Shimmer 2.

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
| SCRAMBLE | Quick tap SETTINGS + TRACK | On release, randomize the selected track’s checked parameters. Choose Pitch, Decay, Color, Shape, Sweep and Contour in Mod Setup > Scramble. The original four default On. Marked steps follow the same checklist without changing the base sound. |
| Control All setup | TRACK + TRIG 1–6 | Include or exclude audio tracks from Control All changes. |
| Audio beat repeat | Hold TRACK + RETRIG , then hold a TRIG 1–16 | The held step selects a repeat division for included audio tracks. Release a modifier or division pad to stop. |
| Repeat mode latch | Hold TRACK + double-tap RETRIG | Release both; hold a TRIG to repeat, release it to stop. BACK exits. Copy/paste/clear blocked; plain PLAY/STOP available. Temporary, not saved. Stock FUNC + SETTINGS/PATTERN temp save/reload stay available; diagnostics never appear from latching. |
| Control All filter | Hold TRACK + MACHINES ; turn SWEEP / CONTOUR | Adjust cutoff/resonance across included audio tracks. Without TRACK, adjust the selected track. |
| Synth Attack | MACHINES + DECAY | Adjust the added attack control on supported machines. |
| Arpeggiator / ChordKeys settings | FUNC + RETRIG | Open the settings for the active Arpeggiator or ChordKeys feature. Arpeggiator octave 0 cycles only through held notes. |
| ChordKeys | Select the Chord machine, then play TRIG 1–16 | Play scale-based chord voicings from the step keys. To leave a ChordKeys track you must use TRACK + Track Pad. |
| ChordKeys harmony locks | Grid record: hold a step TRIG and press T1-T6 . Live record: play a chord and use the harmony pads. | Record the chosen harmony on the step. Press the same harmony pad again on a held grid step to restore its base harmony. Harmony locks save with the pattern independently of LFO 2. |

## Effects

| Feature | Controls | Behavior |
|---|---|---|
| Reverb-slot menu | Hold TRACK + REVERB SIZE | Opaque popup over the normal screen; three scrolling choices. Left/up: VINYL, then VINYL+REV. Center: REVERB. Right/down: CHORUS 1, CHORUS 2, CHOR1+REV, CHOR2+REV. Browse without changing sound; release TRACK to apply, BACK to cancel. |
| Delay-slot menu | Hold TRACK + DELAY TIME | Left/up from DELAY: CRUSH 1, CRUSH 2, PING PONG, SHIMMER 1, SHIMMER 2. Right/down: CRU1+DEL, CRU2+DEL. Opaque menu; sound stays unchanged until TRACK release. BACK cancels. |
| Reverb Tone | REVERB: FUNC + SIZE; combined: SETTINGS + SIZE | In CHOR1+REV, CHOR2+REV and VINYL+REV, hold SETTINGS and turn REVERB SIZE for native Tone without leaving the mode. Releasing SETTINGS returns to Reverb Size. Standard REVERB mode keeps FUNC + SIZE. |
| Chorus alone | SIZE = Speed; FUNC + SIZE = Depth | Chorus I/II Speed and Depth 0-127. REVERB SEND becomes Chorus Send per track. |
| Chorus + Reverb controls | SIZE / FUNC + SIZE / FUNC first, then TRACK + SIZE | Reverb Size / Chorus Speed / Chorus Depth. A held FUNC-first TRACK does not open Track Setup. |
| Chorus + Reverb sends | REVERB SEND / FUNC + REVERB SEND | Native Reverb Send / separate Chorus Send 0-127 per track. Either effect can be used independently. |
| Vinyl alone | SIZE / FUNC + SIZE / FUNC first, then TRACK + SIZE | Crackle / Warble Amount / Warble Speed. Vinyl Send 0 is dry. Bright independent pops/clicks continue through musical gaps; Crackle 0 switches dust off. Track level, pan and mute apply. |
| Vinyl + Reverb controls | SIZE / FUNC + SIZE / FUNC first, then TRACK + SIZE | Reverb Size / Crackle / Warble Amount. FUNC first, then TRACK + REVERB SEND adjusts Warble Speed. |
| Vinyl + Reverb sends | REVERB SEND / FUNC + REVERB SEND | Native Reverb Send / separate Vinyl Send per track. Vinyl Send 0 leaves normal reverb. |
| Delay Time / Feedback | DELAY: TIME / FUNC + TIME; combined: SETTINGS + TIME | Plain TIME keeps native Time in CRU1+DEL/CRU2+DEL. Hold SETTINGS and turn DELAY TIME for native Feedback; releasing SETTINGS returns to Time. FUNC first, then TRACK + DELAY SEND also adjusts Feedback. |
| Ping Pong | TIME / FUNC + TIME or SETTINGS + TIME / DELAY SEND | Time / Feedback / per-track send. Stereo echoes alternate left and right; listen on headphones or both outputs. Replaces standard delay, with no combined variant. |
| Shimmer 1 / Shimmer 2 | TIME / FUNC + TIME or SETTINGS + TIME / DELAY SEND | Time / Feedback / per-track send. Shimmer 1: every echo shifts up an octave, filtered for smoother repeats. Shimmer 2: earlier clean-echo/diffuse-octave blend. No combined variants. |
| Crusher Rate | CRUSH: TIME; CRU+DEL: FUNC + TIME | Rate 0-127, about 750 Hz-48 kHz. Lower is rougher; higher cleaner. |
| Crusher Bits | CRUSH: FUNC + TIME; CRU+DEL: FUNC first, then TRACK + TIME | Bits 2-16. Low values affect quiet signals too. Silence stays silent. |
| Crusher / Delay sends | Combined: DELAY SEND / FUNC + DELAY SEND | Delay Send / separate Crush Send 0-127 per track. CRU1+DEL keeps direct clean; CRU2+DEL blends direct clean/crushed even at delay 0. Crusher 0 gives clean echoes. Solo modes show Crush Send. |
| Effect settings and save | Release TRACK; stop playback | Global modes and effect controls, plus six separate sends per effect, save after stopping. New controls/sends have no p-lock/LFO destinations. Native delay/reverb parameters retain stock behavior. |

## Machines and sound controls

| Feature | Controls | Behavior |
|---|---|---|
| Machine browsing | MACHINES + turn DATA | Fast turns move at most one machine per accepted event, spaced by 40 ms, to avoid skipping Sample Wizard. Saved machine IDs and TINY/Shadow/MIDI order stay unchanged. |
| Elder controls | Select Elder in MACHINES | COLOR = Wave; SHAPE = Warp; SWEEP = Noise; CONTOUR = Motion. PITCH, DECAY, PUNCH, Gate and Fine remain available. Original synth inspired by Junior by Fors. |
| Saved Retrosyn sounds | Elder replaces ChpHzrd / Retrosyn | The same machine slot now plays Elder, so previous Retrosyn sounds change timbre. The other engines and previous CPU fixes are retained. Feral is by Glycinate. |
| TINY controls | Select TINY in MACHINES | COLOR: Tone; SHAPE: Model0–51; SWEEP: Mod; CONTOUR: Excite. All52 original models; Feral and every other engine remain. |
| Shadow controls | Select Shadow after TINY in MACHINES | COLOR: Grain; SHAPE: Density; SWEEP: Spread; CONTOUR: Chaos. PUNCH: ratcheting attack. Pitch, Fine, Decay and Gate remain. Original pulsar/noise engine inspired by Opal Dust by Fors. |

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
| Playback modes | SETTINGS + MACHINES | All seven modes: One-Shot, Loop, Slice, Granular, Stretch, Pluck and Wavetable. SETTINGS + PUNCH opens options for the current mode. Wizard dial values stay separate from synth values during the current MACHINES session; leaving and returning restores them. |
| Slice editor | FUNC + step key; FUNC + click DATA | Play upper slices; remove a slice marker with the DATA click. Marker knobs can snap to zero crossings. |
| Permanent quick save | Hold FUNC + SETTINGS | Save the project permanently using the stock quick-save action. |
| Temporary save / reload | Short FUNC + SETTINGS / FUNC + PATTERN | Stock temporary copy save / reload, including while retrig mode is latched. |

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
| DX | Off / On Default: Off | Optional CPU diagnostic. Physically hold TRACK + RETRIG for at least 350 ms and release. Latching retrig never triggers the popup. Off by default. |
| SCRM | DATA opens; turn and press DATA; BACK returns | Six checkboxes per track: Pitch, Decay, Color, Shape, Sweep, Contour. Pitch/Decay default Off; the original four default On. Choices persist across projects and power cycles; saving waits until playback stops. Wizard allows Pitch/Decay; its sample/mode controls stay excluded. |

These are global preferences. BACK closes Mod Setup and saves its global preferences; each track’s Scramble checklist saves when you return from its submenu. If playback is running, the save waits until it stops. Stop playback and allow saving to finish before powering off. Saved choices return after reboot. Effect modes and crusher settings also save after playback stops.

Startup defaults: stock pads and mute behavior; USB 2ch; Num Off; DX Off. Reverb and Delay are the default effect modes when no effect preferences are saved. Six-channel USB excludes the stereo effect returns.
