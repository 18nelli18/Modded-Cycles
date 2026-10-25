# Feature and shortcut guide

Supermodel 2.40 - 24 October 2026

Main 2.40. Hold the first button while pressing the next button or turning the named knob. TRIG means a step key; pad means a track key; DATA means LEVEL/DATA. All listed features are included.

## Included features

**Machines and sound:** Six stock engines plus Sample Wizard, SD Vintage, Clap Vintage, SY Toy, SY Bits, Swarm LITE, MACRO, ACID, WAVE, Feral by Glycinate, Elder, TINY, Shadow, SPEAK, LEGACY, RETROSYN and MIDI Out. Elder is an original synth inspired by Junior by Fors.

**Performance and sequencing:** Arpeggiator, held-note octave 0, ChordKeys and harmony locks, Sequence Genie, SCRAMBLE, slides, trig preview, Step Recorder, latching mute and solo. Trigger-based Sidechain and per-pattern Scramble checklists.

**Filters and effects:** Per-track resonant filter and attack. GATED, HALL, ROOM, PS1, Vinyl, Ring Mod and two Choruses; DUCK, DUB, Ping Pong, Phaser and two Crushers.

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
| SCRAMBLE | Hold SETTINGS + TRACK | Randomize the checked Pitch, Decay, Color, Shape, Sweep and Contour parameters once per hold. Choose parameters in Mod Setup > SCRM. Pitch/Decay default Off; Color/Shape/Sweep/Contour default On. Marked steps use the same checklist without changing the base sound. Checklists save per pattern with Save Project. A short tap without held steps opens Mod Setup. |
| SCRAMBLE step / delete | Hold a step + quick SETTINGS + TRACK; delete normally | Toggle SCRAMBLE on that step. Deleting its trig clears the mark and locks; a replacement trig starts clean. Neighboring steps and tracks keep their settings. |
| Control All setup | TRACK + TRIG 1–6 | Include or exclude audio tracks from Control All changes. |
| Audio beat repeat | Hold TRACK + RETRIG , then hold a TRIG 1–16 | The held step selects a repeat division for included audio tracks. Release a modifier or division pad to stop. |
| Repeat mode latch | Hold TRACK + double-tap RETRIG | Release both; hold a TRIG to repeat, release it to stop. BACK exits. PLAY/STOP and FUNC + SETTINGS/PATTERN temporary save/reload remain available. |
| Control All filter | Hold TRACK + MACHINES ; turn SWEEP / CONTOUR | Adjust cutoff/resonance across included audio tracks. Without TRACK, adjust the selected track. |
| Synth Attack | MACHINES + DECAY | Adjust the added attack control on supported machines. |
| Arpeggiator / ChordKeys settings | FUNC + RETRIG | Open the settings for the active Arpeggiator or ChordKeys feature. Arpeggiator octave 0 cycles only through held notes. |
| ChordKeys | Select the Chord machine, then play TRIG 1–16 | Play scale-based chord voicings from the step keys. To leave a ChordKeys track you must use TRACK + Track Pad. |
| ChordKeys harmony locks | Grid record: hold a step TRIG and press T1-T6 . Live record: play a chord and use the harmony pads. | Record a harmony on the step. Press the same harmony pad again on a held step to restore its base harmony. |

## Effects

| Feature | Controls | Behavior |
|---|---|---|
| Reverb-slot menu | Hold TRACK + REVERB SIZE | Top to bottom: GATED, HALL, ROOM, PS1, REVERB, VINYL, CHORUS 1, CHORUS 2, RING MOD. Turn left to move up, right to move down. Browse without changing sound; release TRACK to apply, BACK to cancel. |
| Delay-slot menu | Hold TRACK + DELAY TIME | Top to bottom: PHASER, DUCK, DUB, PING PONG, DELAY, CRUSH 1, CRUSH 2. From DELAY, left/up selects Ping Pong; right/down selects Crush 1 then Crush 2. Release TRACK to apply; BACK cancels. |
| Standard Reverb | REVERB SEND / SIZE / FUNC + SIZE | Per-track Send / Size, including INF at maximum / Tone -64 through 0 to +63. |
| GATED reverb | REVERB SEND / SIZE; FUNC + SIZE; SETTINGS + SIZE | Gated Send / Gate Time; Pre-delay; Tone. Gate Time: about 40 ms–6.7 s after input falls quiet. Pre-delay: 0–568 ms. Try Gate Time 16–32 and Pre-delay 25–40 ms on a snare. |
| HALL reverb | REVERB SEND / SIZE / FUNC + SIZE or SETTINGS + SIZE | Hall Send per track / Decay / Tone. Wide stereo tail with longer reflections than ROOM; maximum SIZE gives a long damped tail. |
| Ring Mod | REVERB SEND / SIZE / FUNC + SIZE or SETTINGS + SIZE | Ring Send per track / Frequency / Depth. Metallic sine ring modulation replaces the reverb return. Select RING MOD below Chorus 1/2. Frequency and Depth shared by tracks in this pattern; use the native track Send for locks. |
| Phaser | DELAY SEND / TIME / FUNC + TIME; FUNC first, then TRACK + TIME | Phaser Send per track / Rate / Depth; FUNC then TRACK + TIME is Feedback (also SETTINGS + TIME). Two-stage stereo phaser replaces the delay return. Select PHASER above DUCK. Hold FUNC before TRACK to avoid the mute latch. |
| DUCK delay | DELAY SEND / TIME / FUNC + TIME or SETTINGS + TIME; FUNC then TRACK + TIME or DELAY SEND | Native Delay Send / Time / Feedback. Hold FUNC first, then TRACK: TIME adjusts Amount; DELAY SEND adjusts Release. Strong wet ducking while the send input plays, then a swelling return; feedback remains intact. Try Amount 127, Release 32-64 on sparse notes. Amount 0 is standard Delay. |
| ROOM reverb | REVERB SEND / SIZE / FUNC + SIZE or SETTINGS + SIZE | Room Send per track / Decay / Tone. Compact stereo room ambience. Select ROOM above PS1; release TRACK to apply. |
| PS1 reverb | REVERB SEND / SIZE / FUNC + SIZE or SETTINGS + SIZE | PS1 Send per track / Decay / Tone. PlayStation-inspired stereo tail with a dark, grainy character. |
| Chorus 1 / 2 | REVERB SEND / SIZE / FUNC + SIZE | Chorus Send per track / Speed / Depth. Speed and Depth 0-127. Replaces reverb in this slot. |
| Vinyl | REVERB SEND; SIZE / FUNC + SIZE / FUNC first, then TRACK + SIZE | Vinyl Send; Crackle / Warble Amount / Warble Speed. Hold FUNC first, then TRACK for Speed. Send 0 is dry; Crackle 0 switches dust off. Bright independent pops/clicks continue through gaps. Track level, pan and mute apply. |
| Standard Delay | DELAY SEND / TIME / FUNC + TIME | Per-track Delay Send / native Time / native Feedback. |
| DUB delay | DELAY SEND / TIME / FUNC + TIME or SETTINGS + TIME | Per-track Delay Send / native Time / Feedback. Strongly filtered echoes alternate left and right, progressively narrowing in the feedback loop. Headphones or both outputs reveal the movement. |
| Ping Pong | DELAY SEND / TIME / FUNC + TIME or SETTINGS + TIME | Per-track send / Time / Feedback. Stereo echoes alternate left and right; listen through headphones or both outputs. |
| Crusher Rate / Bits | CRUSH 1 or 2: TIME / FUNC + TIME | Rate 0-127, about 750 Hz-48 kHz / Bits 2-16. Lower Rate or Bits is rougher. CRUSH 1 keeps the direct signal clean; CRUSH 2 blends direct clean/crushed. DELAY SEND is labeled Crush Send; no delay echoes in Crush modes. |
| Effect settings and save | Save Project | Each pattern remembers its selected FX types, added controls and extra sends. Save the project to keep them after reloading. Blank patterns use standard Delay/Reverb and default added controls. A queued pattern applies its FX when it begins playing. Added FX controls have no p-lock/LFO destinations; native track sends support locks. |

## Machines and sound controls

| Feature | Controls | Behavior |
|---|---|---|
| Machine browsing | MACHINES + turn DATA | Turn DATA to choose a machine. MIDI Out is last. |
| Elder controls | Select Elder in MACHINES | COLOR = Wave; SHAPE = Warp; SWEEP = Noise; CONTOUR = Motion. PITCH, DECAY, PUNCH, Gate and Fine remain available. Original synth inspired by Junior by Fors. |
| TINY controls | Select TINY in MACHINES | COLOR: Tone; SHAPE: Model 0–51; SWEEP: Mod; CONTOUR: Excite. |
| Shadow controls | Select Shadow after TINY in MACHINES | COLOR: Grain; SHAPE: Density; SWEEP: Spread; CONTOUR: Chaos. PUNCH: ratcheting attack. Pitch, Fine, Decay and Gate are available. Pulsar/noise synth inspired by Opal Dust by Fors. |
| WAVE starter | Select WAVE and play | AV-WAVE-Morph is already loaded: 16 morphable frames, no first import required. COLOR selects position; SHAPE adds envelope movement. Custom tables replace the starter on their track. |
| WAVE folder navigation | BACK in the WAVE browser | BACK goes up one folder; at /Wavetables it closes the selector. |
| ACID filter Decay | DECAY | DECAY controls filter envelope decay. Volume holds until note-off, followed by a short release. |
| ACID Accent | Velocity 97-127 | Progressive filter transient and level accent. Velocity 0-96 keeps the normal unaccented response; native velocity volume response is retained. |
| SY BITS fine detune | FUNC + COLOR | 0.01-semitone steps from -24.00 to +24.00. Plain COLOR changes whole semitones; FUNC + COLOR adjusts the fractional part. Supports sound saving and parameter locks. |
| RETROSYN | MACHINES, immediately before MIDI Out | COLOR, SHAPE (six models), SWEEP and CONTOUR. PITCH, DECAY, Gate and Punch are available. |

## LEGACY machine

| Feature | Controls | Behavior |
|---|---|---|
| LEGACY / selection | MACHINES: before RETROSYN and MIDI Out | Dexed MSFA six-operator FM with all 32 algorithms; one voice per track. MIDI Out remains last. COLOR = Velocity, SHAPE = Voice, SWEEP = Brightness, CONTOUR = EG Time. Native locks/CC/LFO mappings; Voice and Velocity are captured on the next trigger. |
| Voice library | SHAPE: slots 0-31 | 32 bundled voices selected with SHAPE. The complete indexed factory voice library follows. Import a cartridge to replace the active bank. |
| Velocity / brightness | COLOR / SWEEP | Velocity 0-127 controls the cartridge operators response at each trigger; default 100. Brightness 64 preserves the patch. Lower softens modulation; higher adds bite. |
| Envelope time | CONTOUR / DECAY | EG Time 64 preserves the patch envelope timing; lower is faster, higher slower. DECAY and gate still set the native amplitude envelope. PITCH and FINETUNE transpose the voice; fixed-frequency operators follow their cartridge settings. |
| Import a DX7 bank | Flasher > WAV / DX7 bank importers | Stop playback. Choose a Yamaha 32-voice .syx bank, connect Model:Cycles USB MIDI, choose slot 1-16 and send. Wait for LEGACY BANK SAVED. Reusing a slot replaces it. Importing does not change the active sound. |
| Load a stored bank | LEGACY: FUNC + MACHINES; DATA; BACK | Hold FUNC while pressing MACHINES to open the bank library. Turn DATA to choose; press DATA to load; BACK cancels. Factory restores the included voices. One active 32-voice bank is shared by every LEGACY track. Banks persist after reboot and are separate from Elektron project backups. |
| Credits and load | Dexed / Google MSFA | Based on Dexed/MSFA by Google, Pascal Gauthier and contributors. Six-operator patches can use substantial CPU. |

## LEGACY voice library

| Feature | Controls | Behavior |
|---|---|---|
| 0 | Tooropulse | Legowelt Magic cart |
| 1 | Delicho | Legowelt Magic cart |
| 2 | EinstofPia | Legowelt Magic cart |
| 3 | Overcast P | Legowelt Magic cart |
| 4 | STRINGS 1 | ROM1A |
| 5 | PWMfuzzy | Legowelt Magic cart |
| 6 | Sharpieblo | Legowelt Magic cart |
| 7 | RoboticSeq | Legowelt Magic cart |
| 8 | SplitStran | Legowelt Magic cart |
| 9 | PIANO   1 | ROM1A |
| 10 | Heimwave | Legowelt Magic cart |
| 11 | CLAV    1 | ROM1A |
| 12 | Synthotape | Legowelt Magic cart |
| 13 | Wavesply | Legowelt Magic cart |
| 14 | Poldermood | Legowelt Magic cart |
| 15 | FelineSaw | Legowelt Magic cart |
| 16 | Aguirio | Legowelt Magic cart |
| 17 | E.PIANO 1 | ROM1A |
| 18 | E.ORGAN 1 | ROM1A |
| 19 | Pinkcookie | Legowelt Magic cart |
| 20 | ObieSplash | Legowelt Magic cart |
| 21 | MARIMBA | ROM1A |
| 22 | Garudaydre | Legowelt Magic cart |
| 23 | VillageOrg | Legowelt Magic cart |
| 24 | BASS    1 | ROM1A |
| 25 | Litehouze | Legowelt Magic cart |
| 26 | NostroSpli | Legowelt Magic cart |
| 27 | Velobleepb | Legowelt Magic cart |
| 28 | DimPacific | Legowelt Magic cart |
| 29 | SequenceMe | Legowelt Magic cart |
| 30 | BRASS   1 | ROM1A |
| 31 | Swissynth | Legowelt Magic cart |

## SPEAK voice machine

| Feature | Controls | Behavior |
|---|---|---|
| Select SPEAK | MACHINES: after Shadow, before LEGACY | 128-word speech engine. Start around Vol+Dist 60, Punch off. |
| Voice / Word / Speed / Articulation | COLOR / SHAPE / SWEEP / CONTOUR | Voice/formant character / Word 0-127 / Speed (64 normal, lower slower) / Articulation. SHAPE shows the word and index. Word changes take effect at the next trig; the other three controls remain live. |
| Pitch and envelope | PITCH / notes; DECAY, Fine, Punch, Gate, Attack | Pitch changes independently of word speed. Begin with Decay 127 to hear complete words. Filters and FX sends are available. |
| Word sequences and modulation | Hold a trig + SHAPE, then lock Pitch and other knobs normally | Word and other native parameters support p-locks and LFO destinations. COLOR/SHAPE/SWEEP/CONTOUR use MIDI CC 16/17/18/19. Leave space for the word or increase Speed. |
| Example sentence | SHAPE words and note locks on successive trigs | HELLO 31, I 0, AM 62, A 17, ROBOT 113, I 0, LOVE 35, MUSIC 106. Full indexed word library follows at the end of this guide. |

## LFO and MACRO controls

| Feature | Controls | Behavior |
|---|---|---|
| Second audio LFO | Press LFO twice | Open LFO 2 and edit its speed, shape, destination and depth. |
| LFO quick assignment | On an LFO page, hold LFO and turn a destination knob | Assign the corresponding ordinary knob destination. To select the added Attack, Filter or Resonance targets, also hold MACHINES . |
| Attack / Filter / Resonance LFO targets | On an LFO page, hold LFO + MACHINES while turning DECAY , SWEEP or CONTOUR | Choose Attack, Filter or Resonance with the corresponding knob while holding MACHINES. |
| MACRO fine tune | SETTINGS + turn PITCH | Adjust fine pitch. Plain PITCH retains its regular control; FUNC + PITCH is MACRO Lo-Fi. Lo-Fi lowers sample rate to the left, bit depth to the right, with OFF at center. Model names and numbers 0–46 are shown. |

## Sample Wizard and saving

| Feature | Controls | Behavior |
|---|---|---|
| Sample Preview | FUNC + MACHINES ; highlight a sample, then press its track pad or keyboard trig | Audition the highlighted sample. Scrolling through the list remains silent. |
| Sample lock | Open the sample selection menu and highlight a sample; then hold a step TRIG + MACHINES | Lock the highlighted sample to that step on a Sample Wizard track. The sample browser must be open with the desired sample selected. |
| Playback modes | SETTINGS + MACHINES | One-Shot, Loop, Slice, Granular, Stretch, Pluck and Wavetable. SETTINGS + PUNCH opens options for the current mode. |
| Slice editor | FUNC + step key; FUNC + click DATA | Play upper slices; remove a slice marker with the DATA click. Marker knobs can snap to zero crossings. |
| Permanent quick save | Hold FUNC + SETTINGS | Save the project permanently using the stock quick-save action. |
| Temporary save / reload | Short FUNC + SETTINGS / FUNC + PATTERN | Stock temporary copy save / reload, including while retrig mode is latched. |

## MIDI Out machine

| Feature | Controls | Behavior |
|---|---|---|
| Select and set up | MACHINES : MIDI Out; FUNC + TRACK | Silent MIDI track. Track Setup: Channel, Output, KbT (keyboard transpose), Pad Note. Turn DATA to select; click DATA before editing; BACK exits. Channel: 1-16 / Global. Output: Global / Off / USB / DIN / Both. |
| CC assignment and locks MIDI Out machine only | SETTINGS + gray knob; hold steps + assigned knob for locks | Assign OFF or CC0-127 to nine knobs. Turn a knob alone to send its value. Each lock keeps the CC number and value. Live recording captures knob changes. |
| Two MIDI LFOs | LFO : LFO 1, LFO 2, track screen; BACK exits | DATA selects; click to edit. Order: Wav, Mul, Dst, Dep, Speed, Fade, Phase, Mode. LFO Speed adjusts the open LFO. Hold LFO + an assigned CC knob: assign destination, then turn further for depth. |
| Notes and save | Normal note/grid controls; FUNC + PAGE ; FUNC + SETTINGS | Incoming MIDI notes use the track receive channel or auto channel; live and step recording keep notes, velocity and length. FUNC + PAGE edits pattern length. Project/quick save keeps MIDI settings and locks. |
| MIDI OUT + THRU | CONFIG → MIDI → PORTS → OUT/THRU: THR; then FUNC + click DATA | Toggle the Cycles’ own outgoing MIDI while retaining incoming MIDI Thru. |

## Mod Setup

Tap SETTINGS + TRACK and release to open Mod Setup. Hold the combo to run SCRAMBLE once instead; continuing to hold does not repeat it. With a TRIG held, a quick tap toggles its Scramble mark. DATA selects a row; click to edit, turn, click again to return. Stk = Stock; SIL = Silent; LTC = Latch.

| Feature | Controls | Behavior |
|---|---|---|
| Pad | Stk / SIL Default: Stk | Stk keeps the original track-pad behavior: a pad selects and plays its track. Silent selects the track without sounding it; hold TRACK and press a track pad to select and play. ChordKeys tracks still require TRACK + track pad to leave the track. |
| USB | 2ch / 6ch Default: 2ch | 2ch sends the stereo mix to the computer. 6ch sends six separate mono tracks, before pan and without the mix delay/crusher/reverb/chorus returns. Stereo audio from the computer to Cycles works in both modes. Stop playback before changing this toggle. Changing modes reconnects the USB audio device; select its new channel layout in your DAW if needed. |
| Num | Off / On Default: Off | Off keeps the original volume and pan display. On shows numeric volume and pan values when you adjust those controls. |
| Mute | Stk / LTC Default: Stk | Stk keeps the original momentary mute controls. With LTC selected, hold TRACK and tap FUNC to stay in mute mode, then tap track pads to mute or unmute. Tap FUNC again to leave. In latched mute mode, hold FUNC and press a track pad to solo it; press the soloed pad again, or leave mute mode, to restore the previous mutes. |
| Delay | Stk / Div Default: Stk | Stk preserves the original Delay Time display and timing. Div displays musical divisions, including dotted and triplet values, and corrects the matching timing positions to exact divisions of the tempo. Other Delay Time positions retain their original timing; this does not quantize every knob position. Applies while using Delay mode. |
| DX | Off / On Default: Off | With DX On: tap FUNC, press FUNC again within 350 ms, hold at least 0.5 seconds, then release. Other controls cancel the gesture. Shows/resets A/P/O/N: average/peak CPU load, overruns, governor voice drops. Off by default. |
| SCRM | DATA opens; turn and press DATA; BACK returns | Six checkboxes per track: Pitch, Decay, Color, Shape, Sweep, Contour. Pitch/Decay default Off; Color/Shape/Sweep/Contour default On. Each pattern keeps its own six checklists; Save Project preserves them after reloading. Wizard allows Pitch/Decay; its sample/mode controls stay excluded. |
| Sidechain routing | Select source; tap SETTINGS + TRACK; S.Chn > DATA | Check any of the other five tracks with DATA to duck their volume on source note triggers. The source cannot target itself. Scroll with DATA; click a checkbox to toggle. Multiple sources use the deepest duck on each target. DUCK remains a separate delay type. Trk. 1–6 identify targets; the source is omitted. |
| Dpt / Atk / Hld / Rel | Scroll below checkboxes; click DATA, turn, click to finish | Dpt = Depth, Atk = Attack, Hld = Hold, Rel = Release. Depth: 0–100%, 16 levels. Atk: 0–160 ms. Hold: 0–120 ms. Rel: 10 ms–3 s. BACK finishes editing, then returns to Mod Setup. Start with a four-on-the-floor source, Depth 60%, Attack 0 ms, Hold 0 ms, Release 150 ms. Untick all targets to disable that source. |
| Per-pattern saving | Save Project after edits | Sidechain routing and controls, six Scramble checklists, FX types and added FX settings belong to each pattern. Save the project to keep changes after reloading. Blank patterns have Sidechain off and the default Scramble checklist. Queued changes apply when the next pattern starts. |

BACK closes Mod Setup and saves its global preferences. If playback is running, the save waits until it stops. Stop playback and allow saving to finish before powering off. Sidechain routing/settings, Scramble checklists and FX types/added settings are per pattern: Save Project preserves these after reloading. Closing a submenu alone does not save the project.

## SPEAK word library

| Index | Word | Index | Word | Index | Word | Index | Word |
|---:|---|---:|---|---:|---|---:|---|
| 0 | I | 32 | GOODBYE | 64 | IS | 96 | ONE |
| 1 | YOU | 33 | GOOD | 65 | WAS | 97 | TWO |
| 2 | WE | 34 | BAD | 66 | WERE | 98 | THREE |
| 3 | THEY | 35 | LOVE | 67 | WILL | 99 | FOUR |
| 4 | HE | 36 | LIKE | 68 | CAN | 100 | FIVE |
| 5 | SHE | 37 | WANT | 69 | COULD | 101 | SIX |
| 6 | IT | 38 | NEED | 70 | HAVE | 102 | SEVEN |
| 7 | ME | 39 | KNOW | 71 | HAS | 103 | EIGHT |
| 8 | US | 40 | THINK | 72 | HAD | 104 | NINE |
| 9 | THEM | 41 | FEEL | 73 | BEEN | 105 | ZERO |
| 10 | MY | 42 | SEE | 74 | IN | 106 | MUSIC |
| 11 | YOUR | 43 | HEAR | 75 | ON | 107 | SOUND |
| 12 | OUR | 44 | SAY | 76 | AT | 108 | BEAT |
| 13 | THIS | 45 | SPEAK | 77 | TO | 109 | RHYTHM |
| 14 | THAT | 46 | TELL | 78 | FOR | 110 | BASS |
| 15 | THESE | 47 | ASK | 79 | FROM | 111 | DRUM |
| 16 | THOSE | 48 | DO | 80 | WITH | 112 | MACHINE |
| 17 | A | 49 | MAKE | 81 | WITHOUT | 113 | ROBOT |
| 18 | AN | 50 | PLAY | 82 | OF | 114 | HUMAN |
| 19 | THE | 51 | STOP | 83 | UP | 115 | TIME |
| 20 | AND | 52 | START | 84 | DOWN | 116 | NIGHT |
| 21 | OR | 53 | GO | 85 | HERE | 117 | DAY |
| 22 | BUT | 54 | COME | 86 | THERE | 118 | WORLD |
| 23 | IF | 55 | STAY | 87 | NOW | 119 | FRIEND |
| 24 | SO | 56 | MOVE | 88 | THEN | 120 | HAPPY |
| 25 | BECAUSE | 57 | TURN | 89 | AGAIN | 121 | SAD |
| 26 | YES | 58 | TAKE | 90 | ALWAYS | 122 | NEW |
| 27 | NO | 59 | GIVE | 91 | NEVER | 123 | CAREFUL |
| 28 | NOT | 60 | GET | 92 | ALL | 124 | CREATURE |
| 29 | PLEASE | 61 | BE | 93 | SOME | 125 | LOUD |
| 30 | THANK | 62 | AM | 94 | MORE | 126 | DREAM |
| 31 | HELLO | 63 | ARE | 95 | LESS | 127 | FUTURE |

Startup defaults: stock pads and mute behavior; USB 2ch; Num Off; DX Off. Blank patterns use standard Reverb and Delay with default added FX settings. Six-channel USB excludes the stereo effect returns.
