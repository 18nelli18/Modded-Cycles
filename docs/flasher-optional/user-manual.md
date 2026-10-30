# SUPERMODEL
## User manual · Release 2.64

Model:Cycles · Full / Lite / Machine Optional

# Contents & conventions

A practical reference for Supermodel 2.64 on Model:Cycles.

Use the chapter list below for a complete walkthrough, or turn to the shortcut reference when you need a particular gesture. The machine chapters describe the Full library. Machine Optional controls are grouped in their own chapter.

# Buttons & editions

Read gestures consistently and find the chapters that apply to your build.

| Notation | Meaning |
| --- | --- |
| TRACK + RETRIG | Hold the first button while pressing the second. |
| TRACK + turn TIME | Keep TRACK held while turning the TIME knob. |
| Tap / hold | Tap means press and release promptly. Hold means keep the button pressed. |
| TRIG / track pad | TRIG means one of the 16 step keys. Track pad means T1–T6. |
| DATA | The LEVEL/DATA encoder. “Click DATA” means press it. |
| Global > FX | Navigate to Global, then the FX row. |
| Parameter lock | A value stored on a step. Hold that step and adjust the relevant control. |

## Editions

Full includes the full machine library and the shared performance, effects, filter, modulation and MIDI functions. Lite uses the six Model:Cycles audio machines with the shared functions. Machine Optional lets you choose the machines you want; the relevant chapters apply when those machines are enabled.

This manual focuses on Supermodel’s controls and workflows. Model:Cycles’ normal pattern, sound and configuration operations remain part of everyday use.

## Acknowledgments

Glycinate, Fors.Fm, PPPCCC, DavidCaruso, Emilie Gillet, Durchgemacht, 18nelli18, and every member of the Modded-Cycles Discord server who rode with me through this. Y'all rule.

# Your first session

Build a small pattern, shape it, and save the result.

## A simple starting workflow

1. Choose an audio track with a track pad. To select its machine, press MACHINES, then turn DATA.
2. Create or load a pattern using the normal recording controls. For note-by-note entry while stopped, press REC twice to enter Step Recorder.
3. Play notes to enter steps. PLAY advances one step; STOP moves back. Press REC again to leave Step Recorder.
4. Adjust the machine’s sound controls. For the track filter, hold MACHINES and turn SWEEP for cutoff or CONTOUR for resonance.
5. Add an effect with the track’s REVERB SEND or DELAY SEND. To choose an effect, hold TRACK and turn SIZE or TIME; release TRACK to apply.
6. Use Save Project to preserve the project and its pattern-specific settings. Stop playback and allow saving to finish before switching off.

## Open Mod Setup

Tap SETTINGS + TRACK and release both buttons. Choose Global, Track or Song. Turn DATA to select a row; click to edit, turn to change the value, and click again to finish. BACK leaves editing before returning to the previous level.

**Tap and hold do different jobs** — A quick SETTINGS + TRACK tap opens Mod Setup. Holding the same combination runs SCRAMBLE once. With a step held, a quick tap toggles that step’s Scramble mark.

## A useful habit

Keep track pads and TRIG keys distinct. For example, TRACK + TRIG 1–6 changes Control All participation; it uses the step keys, not the six track pads.

# Global preferences

Tap SETTINGS + TRACK, choose Global, then select a row.

| Row | Choices and operation |
| --- | --- |
| Pad | Stk: a pad selects and plays. SIL: a pad selects silently; TRACK + pad selects and plays. Default: Stk. |
| USB | 2ch: stereo mix to the computer. 6ch: six separate mono tracks. Stop playback before changing. Default: 2ch. |
| Num | Off or On. On displays numeric volume and pan values as you adjust them. Default: Off. |
| Mute | Stk: momentary mute controls. LTC: TRACK + tap FUNC latches mute mode. Default: Stk. |
| Dly | Stk: normal Delay Time. Div: musical divisions, including dotted and triplet positions. Default: Stk. |
| DX | Off or On. Enables the diagnostic display gesture. Default: Off. |
| QntM | Enable quantized mute/solo and choose its time division. Default: Off. |
| Grv | Groove On/Off and Type, plus CHORD Strum. Swing sets groove strength. |
| LFOs | Choose 1, 2, 3 or 4 audio LFOs per track. Default: 2. |
| FX | MST shares effect selection. TRK follows the selected track for light effects; heavy effects stay shared. |
| ACID | A: amp envelope. F: filter envelope. AF: both. Applies to every ACID track when ACID is installed. Default: F. |
| JUMP | Off / On. With On, PATTERN then FUNC + TRIG jumps immediately and keeps playback position. Default: Off. Saves globally. |

## Save global preferences

BACK closes Mod Setup and saves global preferences. If playback is running, the save waits until it stops. Stop playback and allow the save to finish before powering off.

**Pattern settings use Save Project** — Sidechain, Scramble checklists, FX choices and their pattern-specific controls are saved with the project. Closing Mod Setup alone does not save those project changes.

# Tracks, mute & repeat

Select and perform tracks while keeping the controls close at hand.

## Mute and solo

Set Global > Mute > LTC. Hold TRACK and tap FUNC to latch mute mode. Tap track pads to mute or unmute them. Tap FUNC again to leave.

While mute mode is latched, hold FUNC and press a track pad to solo it. Press that pad again, or leave mute mode, to restore the previous mute state. Tracks that were already muted stay muted.

Global > QntM controls quantized mute and solo. Enable it and choose a time division to place those actions on the selected timing grid.

## Choose Control All tracks

Hold TRACK and press TRIG 1–6 to toggle the audio tracks that follow Control All. The selected track always participates. To control filters across those tracks, hold TRACK + MACHINES and turn SWEEP or CONTOUR.

## Momentary audio beat repeat

1. Hold TRACK + RETRIG.
2. Hold a TRIG 1–16 to choose a repeat division for the included audio tracks.
3. Release the division key or either modifier to stop repeating.

## Latch repeat mode

Hold TRACK and double-tap RETRIG, then release both. Hold a TRIG to repeat; release it to stop. BACK exits the mode. PLAY/STOP and temporary save/reload remain available.

**Stop the music and tails** — One STOP preserves effect tails. Press STOP twice to invoke All Sound Off and clear reverb and delay tails.

# Notes, scales & page length

Use step entry, parameter movement and musical pitch rules.

| Task | Controls and behavior |
| --- | --- |
| Step Recorder | While stopped, press REC twice. Play notes; PLAY advances and STOP moves back one step. REC leaves the mode. |
| Preview a step | Hold TRIG + PAGE while stopped or paused. The step plays with its note and parameter locks. |
| Parameter slide | SETTINGS + TRIG toggles a parameter slide on the step. |
| Arpeggiator | FUNC + RETRIG opens its settings. Octave 0 cycles through the notes you are holding. |
| Page length | FUNC + PAGE > Page Len sets 1–16 active steps per page. |
| Warp | On spreads those active steps across the normal page duration. Off keeps normal step speed. The setting follows PTN or TRK scope and saves with the pattern. |

## Scale Lock

Open FUNC + PAGE and use Lock, Scl and Key. Choose one of 19 whole-semitone scales and a key.

| Lock mode | Pitch behavior |
| --- | --- |
| Off | Pitch passes without scale locking. |
| ORGN | Successive input notes map to successive scale degrees. |
| BRDS | Pitch snaps to the nearest in-scale note. An exact tie chooses the lower note. |

Lock mode, scale and key save globally while playback is stopped.

**Page length example** — With Page Len set to 8, Warp On stretches the eight active steps across the normal page duration. Warp Off plays those eight steps at the normal step speed.

# Pattern jumps & trig selection

Choose patterns and edit groups of existing steps.

## Direct Pattern Jump

1. Open Mod Setup with SETTINGS + TRACK. Choose Global &gt; JUMP &gt; On.
2. Press PATTERN, then FUNC + the pattern TRIG to jump immediately while keeping playback position.

With JUMP Off, pattern changes use normal timing. The preference saves globally while stopped; Off is the default.

## Select trigs without holding them

1. Press TRACK + PAGE, then release both buttons.
2. Tap existing note trigs, lock trigs or steps containing parameter locks to select or deselect them. Selected steps blink.
3. Use the usual held-step editing controls on the selection. PAGE changes page while keeping the selection.
4. In selection mode, FUNC + PAGE selects all eligible trigs or clears the selection. Press TRACK + PAGE again to leave and clear it.

**TRACK is momentary** — Track selection is active only while TRACK is physically held. Releasing TRACK leaves trig selection available. Empty steps are not created by selecting; steps hidden by Page Len are excluded. Selection mode starts Off after power-up.

# Build a song

An arrangement of patterns, repeats and six track mutes.

1. Tap SETTINGS + TRACK to open Mod Setup.
2. Choose Song beside Global and Track, then press DATA.
3. While stopped, turn DATA to select a row in the four-row grid.

| Control | Action |
| --- | --- |
| PITCH | Choose the row pattern, A01-F16. |
| DECAY | Set the row repeats, 1-64. |
| TRIG 1-6 | Toggle each track mute for the selected row. |
| PAGE | Insert a copy after the selected row. |
| FUNC + PAGE | Delete the selected row; at least one row remains. |
| Click DATA | Choose STOP or LOOP at the end. FUNC + DATA also works. |
| BACK | Leave the Song editor. |

**Stop before editing** — Row changes are available while playback is stopped and Song is inactive. If a song is active or paused, press STOP twice to cancel it before editing. Song is not inside Global.

# Play and save a song

Use native pattern-chain playback for the arrangement.

## A simple arrangement

Set row 1 to A01 x4. Press PAGE to insert a copy, then set row 2 to A02 x2. Set row 3 to A03 x2. These rows use eight expanded pattern plays.

1. Choose STOP to end after the last row, or LOOP to repeat the arrangement.
2. Press PLAY from the Song editor to begin at the first row. The display follows the playing row.
3. Press STOP to pause using native transport. Press PLAY to continue. STOP twice cancels Song and clears reverb/delay tails.
4. Use Save Project to preserve the arrangement and the six tracks ACID glide/legato settings.

## Length and mutes

The complete arrangement must fit 64 expanded pattern plays: add the repeats across all rows. For example, four rows repeated 16 times each use the limit. A song that exceeds it does not start and shows the 64-play limit.

Song mutes combine with existing track mutes. A track muted outside Song remains muted when the row permits it. Choosing a pattern chain manually cancels Song playback.

**Pattern length matters** — Song follows each pattern native chain timing. An infinite chain length can hold a row indefinitely. Set a finite chain length when you want the song to advance.

# Generate, Scramble & Humanize

Three ways to shape a pattern with different amounts of control.

## Sequence Genie

Press SETTINGS + PAGE to open the generator for the selected track. Use DATA to navigate. Choose Generate to generate, or Queue to schedule generation. Set Loop/Page timing to choose when queued generation occurs.

## Set the Scramble checklist

1. Select a track and tap SETTINGS + TRACK.
2. Open Track > SCRM.
3. Use DATA to toggle Pitch, Decay, Color, Shape, Sweep and Contour. Pitch/Decay default Off; the four sound controls default On.

Each pattern keeps six track checklists. Use Save Project to keep them after reloading. For Sample Wizard, Scramble can use Pitch and Decay; the sample and playback-mode controls are outside its checklist.

## Scramble a sound or step

Hold SETTINGS + TRACK to randomize the checked parameters once. Keeping the combination held does not keep rerolling the sound.

To mark a step, hold its TRIG and quickly tap SETTINGS + TRACK. Marked steps use the track’s checklist without changing the base sound. Deleting the trig clears its mark and locks.

## Humanize Apply / Undo

Open Track > Human. Choose a track or All, set Tim and Vel from 0–100, then stop playback and choose Apply. The timing and velocity changes are written into the pattern. Undo restores the previous values.

**Controlled variation** — Use a short checklist when the basic sound should remain recognizable. For timing variation, Humanize writes a result into the pattern; it does not reroll notes during playback.

# Groove, Strum & Sidechain

Shape rhythmic feel and let one track control the level of others.

## Groove and CHORD Strum

Open Global > Grv. Enable Groove, then choose Boom Bap, Disco, Reggae, Bongo, Caixixi, Highlife or Kuduro. SWING controls its strength. With Groove Off, SWING uses the normal swing behavior and the selected groove type is remembered.

Str spaces CHORD voices from −80 to +80 ms. The sign reverses strum direction; 0 plays the voices together. Strum works independently of Groove On/Off. Four voices spaced 80 ms apart span 240 ms.

## Set up Sidechain

1. Select the source track whose trigs will drive the ducking.
2. Tap SETTINGS + TRACK, then open Track > S.Chn.
3. Check destination tracks and/or Rev. and Del. to duck effect returns. Click DATA to toggle a target.
4. Scroll below the targets and set Depth, Attack, Hold and Release. Save the project.

| Control | Range and role |
| --- | --- |
| Dpt | Depth: 0–100%, in 16 levels. |
| Atk | Attack: 0–160 ms. |
| Hld | Hold: 0–120 ms. |
| Rel | Release: 10 ms–3 s. |
| Mute | On: muting the source stops its Sidechain action, including exclusion by solo. Off: the source keeps driving Sidechain while muted. Default: Off. |

All checked targets use the source’s settings. Multiple sources apply the deepest duck on each destination. Untick every target to disable a source. Routing and controls save per source and pattern.

**Starting point** — Use a four-on-the-floor source, Depth 60%, Attack 0 ms, Hold 0 ms and Release 150 ms. Sidechain routing and the DUCK delay are separate controls.

# Filters & attack

Shape a track, or apply the same gesture across your Control All selection.

## Track filter

| Gesture | Parameter |
| --- | --- |
| MACHINES + SWEEP | Filter cutoff on the selected audio track. |
| MACHINES + CONTOUR | Filter resonance on the selected audio track. |
| TRACK + MACHINES + SWEEP / CONTOUR | Cutoff or resonance across the included Control All audio tracks. |
| SETTINGS, then MACHINES + turn SWEEP | Choose HIGH, LOW, BAND or LO/HI. Release the modifiers to apply the filter type. |
| MACHINES + DECAY | Attack on supported machines. |

## Choose a filter for the job

LOW reduces high frequencies as you lower cutoff. HIGH removes low frequencies. BAND emphasizes a band around cutoff. LO/HI provides the combined low/high response. Use resonance to emphasize the area around the cutoff.

A cleared or freshly initialized sound starts at LOW, cutoff 127 and resonance 0. A saved sound keeps its stored filter type and settings. Sample Wizard uses its own internal filter.

## Modulate filter or attack

On an LFO page, hold LFO + MACHINES and turn DECAY, SWEEP or CONTOUR to select Attack, Filter or Resonance as the destination.

**If a track is unexpectedly quiet** — Check mute and solo state, volume, filter type and cutoff, then the machine’s own controls. A high-pass setting with a high cutoff can remove much of a bass sound.

# Audio LFOs

Each audio track can use up to four LFOs.

## Choose how many LFOs are active

Open Global > LFOs and choose 1, 2, 3 or 4. The default is 2. Press LFO repeatedly to cycle through the enabled pages. LFO3 and LFO4 use the same control layout as LFO2. Disabled LFOs stop running and keep their settings.

## Assign a destination quickly

1. Open the LFO page you want to edit.
2. Hold LFO and turn the knob for the destination.
3. For Attack, Filter or Resonance, also hold MACHINES and turn DECAY, SWEEP or CONTOUR.

## Polarity and trigger mode

| Setting | Operation |
| --- | --- |
| Bi | Bipolar modulation, moving to both sides of the destination’s base value. |
| Uni | Unipolar modulation, following the sign of Depth. |
| Mode | Choose FRE, TRG, HLD, ONE or HLF in the LFO menu. |

All enabled LFO banks participate in sound copy, sound clear and sound Undo.

## Keep your modulation

Save Project preserves the pattern and track LFO settings, including the complete LFO2 setup and the LFO3/4 banks. Stop playback and allow saving to finish before powering off.

**Sound exports and project storage** — Ordinary Elektron sound and SysEx exports do not carry every LFO bank setting. Use Save Project for the complete pattern setup.

## MIDI tracks

MIDI Out has its own two LFOs that send MIDI CC values. Their destinations and editing workflow are described in the MIDI chapters.

# Choose & route effects

Each pattern has a reverb slot and a delay slot. Track sends set how much signal reaches them.

## Choose an effect

1. Hold TRACK and turn REVERB SIZE for the reverb slot, or DELAY TIME for the delay slot.
2. Turn left to move up the list; turn right to move down. Browse while keeping TRACK held.
3. Release TRACK to apply the highlighted choice. Press BACK to cancel.

| Reverb slot | Delay slot |
| --- | --- |
| GATED | PHASER |
| HALL | DUCK |
| ROOM | DUB |
| PS1 | POTS |
| REVERB | PING PONG |
| CHORUS 1 | DELAY |
| CHORUS 2 | CRUSH 1 |
| RING MOD | CRUSH 2 |

## MST and TRK

Open Global > FX. MST uses shared effect selection. TRK lets the same selection gestures follow the selected track for light effects. Heavy reverbs and delays remain shared, including POTS. Use each track’s SEND to set its amount.

## Save the pattern’s effects

Use Save Project to keep selected types, effect controls and extra sends. Blank patterns use standard Reverb and Delay. A queued pattern applies its effect choices when it begins playing.

Track send controls support parameter locks. Effect-specific controls do not all have parameter-lock or LFO destinations; use the track sends when you need per-step effect amounts.

**Tails** — One STOP leaves tails playing. Double STOP clears reverb and delay tails, including PS1 and POTS.

# Reverb, chorus & ring modulation

Use REVERB SEND for the amount from each track.

| Effect | SIZE | FUNC + SIZE |
| --- | --- | --- |
| REVERB | Size; INF at maximum | Tone: −64 to +63 |
| GATED | Gate time | Pre-delay |
| HALL | Decay | Tone |
| ROOM | Decay | Tone |
| PS1 | Decay | Tone |
| CHORUS 1 / 2 | Speed | Depth |
| RING MOD | Frequency | Depth |

## Choose a space

REVERB provides the standard size and tone controls, with INF at maximum Size. HALL has a wide stereo tail with long reflections. ROOM gives compact stereo ambience. PS1 has a dark, grainy, PlayStation-inspired character.

## GATED

SIZE sets a gate time of about 40 ms–6.7 s after the input falls quiet. FUNC + SIZE sets pre-delay from 0–568 ms; SETTINGS + SIZE sets tone. For a snare, try gate time 16–32 and pre-delay around 25–40 ms.

## Chorus and Ring Mod

CHORUS 1 and CHORUS 2 use Speed and Depth from 0–127. RING MOD gives metallic sine-wave ring modulation. Its Frequency and Depth are shared by tracks in the pattern; automate track amounts with REVERB SEND locks.

**Another way to reach tone** — For HALL, ROOM, PS1 and RING MOD, SETTINGS + SIZE also accesses the secondary control. GATED uses SETTINGS + SIZE specifically for Tone.

# Delay, phaser & crusher

Use DELAY SEND for the track amount; Time and its modifier control the selected effect.

| Effect | TIME | FUNC + TIME |
| --- | --- | --- |
| DELAY | Time | Feedback |
| PING PONG | Time | Feedback |
| DUB | Time | Feedback |
| POTS | Time | Feedback |
| DUCK | Time | Feedback |
| PHASER | Rate | Depth |
| CRUSH 1 / 2 | Rate: 0–127 | Bits: 2–16 |

## Echo character

DELAY is the standard delay. PING PONG alternates echoes left and right; listen through both outputs or headphones. DUB produces strongly filtered stereo echoes that narrow progressively in the feedback loop.

POTS produces telephone-style mono echoes on both output channels. Use Time, Feedback and the track’s Delay Send normally. It is one shared delay in MST and TRK. Save Project keeps the selection; double STOP clears its tail.

## DUCK

The wet signal ducks while the send input plays and swells back afterward. Hold FUNC first, then TRACK: TIME sets Amount and DELAY SEND sets Release. Try Amount 127 and Release 32–64 on sparse notes. Amount 0 gives standard Delay behavior.

## Phaser and crushers

PHASER is a two-stage stereo phaser. TIME sets Rate; FUNC + TIME sets Depth. For Feedback, hold FUNC first, then TRACK + TIME, or use SETTINGS + TIME.

CRUSH 1 leaves direct sound clean. CRUSH 2 blends direct clean and crushed sound. DELAY SEND becomes Crush Send; these modes produce no delay echoes. Lower Rate or Bits makes the texture rougher. Rate spans about 750 Hz–48 kHz.

Global > Dly > Div shows musical divisions for Delay, including dotted and triplet values. Matching positions follow exact tempo divisions; other positions retain their continuous timing.

# Machine library

Press MACHINES, then turn DATA to choose a machine.

| Machine | Sound and purpose |
| --- | --- |
| KICK / SNARE / METAL / PERC / TONE / CHORD | The six Model:Cycles audio machines. |
| Sample Wizard | Sample playback, slicing, granular, stretch, pluck and wavetable modes. |
| SD Vintage | Tunable snare with a metallic body. |
| Clap Vintage | Clap synthesis with body and attack spacing. |
| SY Toy | Tuned percussion with impact and evolving partials. |
| SY Bits | Digital oscillators, detune and rate/bit reduction. |
| Swarm | Three detuned saws for leads and basses. |
| MACRO | 47 synthesis models, from classic tones to textures. |
| ACID | Resonant bass synthesis with envelope and drive. |
| WAVE | Wavetable scanning and custom table import. |
| Feral | Ten synthesis models for characterful electronic sounds. |
| ELDER | Chip-style synthesis for melodies, basses and percussion. |
| TINY | 52 synthesis models with Tone, Mod and Excite. |
| Shadow | Pulsar/noise synthesis with Grain, Density, Spread and Chaos. |
| SPEAK | 128-word speech synthesis. |
| RETROSYN | Six chip oscillator styles, fixed arpeggios and four-bit PUNCH. |
| PUNCH | Twelve FM percussion models. |
| ESTUS | Eight drum engines with sound-shaping and advanced controls. |
| MIDI Out | Notes, chords, CC controls and two MIDI LFOs for external instruments. |

Full includes this library. Lite uses the six Model:Cycles audio machines and the shared performance, effects and modulation functions. Machine Optional follows your enabled machine selection.

Numeric sound controls commonly span 0–127, with 64 as the midpoint. PITCH and FINE are centered: displayed 0 means no pitch offset. Model selectors and ratio controls use their own scales.

# MACRO

Explore 47 synthesis models with four sound controls, fine tuning and Lo-Fi.

Choose MACRO in MACHINES, then turn SHAPE to select a model from 0–46. The screen shows the model name and number. Model choice supports step parameter locks.

| Panel knob | Displayed function | Use |
| --- | --- | --- |
| COLOR | Timbre | Sets the model’s principal timbre parameter. |
| SHAPE | Model | Chooses one of the 47 synthesis models. |
| SWEEP | Color | Sets the model’s second sound parameter. |
| CONTOUR | Env Timbre | Sets the amount of envelope movement applied to Timbre. At 0, this envelope amount is zero. |

## Pitch and envelope

Use PITCH and note entry to tune the sound. Hold SETTINGS + turn PITCH for fine pitch. DECAY, Gate and PUNCH are available for shaping the note.

## Lo-Fi

Hold FUNC + turn PITCH. The center position is OFF. Turn left to reduce sample rate, or right to reduce bit depth. Choose the side according to the texture you want.

## A useful way to explore

1. Pick a model with SHAPE.
2. Keep CONTOUR low while exploring COLOR and SWEEP.
3. Raise CONTOUR and adjust DECAY to hear envelope movement in the timbre.
4. Use Lo-Fi for rate or bit-depth texture, then add track filter or effects as needed.

**Model behavior** — Different models use their timbre parameters differently. A knob’s minimum position is not a universal neutral setting.

# ACID & WAVE

Resonant bass synthesis and wavetable motion.

## ACID

| Knob | Function |
| --- | --- |
| COLOR | Cutoff |
| SHAPE | Resonance |
| SWEEP | Envelope modulation amount |
| CONTOUR | Drive |
| DECAY | Envelope decay |

In Global > ACID, choose A for amp envelope, F for filter envelope, or AF for both. This one setting applies to every ACID track and saves globally; F is the default. With A/AF, Gate Off allows amp decay during a held note; Gate On sustains until note-off.

Velocities 97–127 add progressive filter and level accent. Velocities 0–96 use the unaccented response. Velocity also controls note volume.

PUNCH selects the oscillator waveform: Off is saw, On is square. Overlapping note lengths link ordinary notes according to the track glide and legato settings. See ACID articulation for the physical controls.

## WAVE

AV-WAVE-Morph supplies 16 morphable frames as a starting table. COLOR selects table position; SHAPE adds envelope movement. Import custom tables for individual tracks. In the browser, BACK goes up one folder; at /Wavetables, BACK closes the selector.

# ACID articulation

Separate pitch glide, legato and envelope destination.

## Set the selected track

| Gesture | Setting |
| --- | --- |
| SETTINGS + PITCH | Glide: OFF, or values 1-127 for approximately 50-360 ms. Default is about 50 ms. |
| SETTINGS + DECAY | Legato: left OFF, right ON. Default ON. |

These settings apply only to the selected ACID track and save with the project. They are track settings, not per-step parameter locks. Release SETTINGS after editing.

## Link notes with LEN

Set a note length so it overlaps the following note. With legato On, the envelope continues across those ordinary linked notes. Glide controls how quickly pitch moves. With glide Off and legato On, pitch changes immediately without an envelope restart.

With legato Off, ordinary notes restart the envelope. Glide can still be active. Detached notes restart the envelope regardless of legato.

## Choose the envelope destination

Global &gt; ACID selects A for amp, F for filter or AF for both. This choice applies to all ACID tracks and saves globally; F is the default. In A/AF, Gate Off permits amp decay during a held note; Gate On sustains until note-off.

**Arpeggiator and retrig** — Each arpeggiator/retrig note restarts the selected A/F/AF envelope, including when note lengths overlap. Ordinary linked notes still follow the track glide/legato settings.

# ELDER, TINY, Shadow & Feral

Choose a model or texture, then shape its movement.

| Machine | COLOR | SHAPE | SWEEP | CONTOUR |
| --- | --- | --- | --- | --- |
| ELDER | Wave | Warp | Noise | Motion |
| TINY | Tone | Model 0–51 | Mod | Excite |
| Shadow | Grain | Density | Spread | Chaos |

## ELDER

A chip-style synth inspired by Junior by Fors. Pitch, Fine, Decay, PUNCH and Gate are available. A simple starting point is Wave 0, Warp 0, Noise 0, Motion 0 and Decay 50.

## TINY

Explore its 52 models with SHAPE. Tone, Mod and Excite shape the selected model. Start with Tone 64, Model 0, Mod 64, Excite 32 and Decay 60, then vary one control at a time.

## Shadow

A pulsar/noise synth inspired by Opal Dust by Fors. Grain, Density, Spread and Chaos control its texture. PUNCH adds distortion and a ratcheting attack. Pitch, Fine, Decay and Gate remain available.

## Feral

Feral by Glycinate provides ten synthesis models for unusual electronic sounds. Choose a model and use its sound controls to explore its character. Use the track filter, LFOs and sends to shape the result further.

## RETROSYN

A chip synth with six SHAPE models, fixed arpeggios and four-bit PUNCH. COLOR, SWEEP and CONTOUR shape the chosen sound. Pitch, Decay and Gate are available.

**Starting values** — The minimum position is not a universal clean-sound setting. A model selector, a ratio control and a continuous timbre control each have their own meaning.

# PUNCH, ESTUS & SY Bits

Use dedicated sound engines for tuned percussion, drums and digital textures.

## PUNCH

SHAPE chooses KIK, TOM, BNG, CNG, TAI, TIM, MAR, DJB, BLK, GNG, BUB or ZAP. COLOR controls timbre; SWEEP chooses the ratio, and FUNC + SWEEP adjusts between ratios. CONTOUR and DECAY shape the sound.

A starting point: Color 64, KIK, ratio 4:1, Contour 40 and Decay 50.

## ESTUS

SHAPE selects KICK, TOM, PERC, SNARE, CLAP, CL HAT, OP HAT or CYMBAL. The display labels follow the engine.

| Engine group | COLOR / SWEEP / CONTOUR |
| --- | --- |
| KICK, TOM, PERC | Pitch Amount / Pitch Decay / FM Drive |
| SNARE | Noise Mix / Noise Tone / Snap |
| CLAP | Spread / Tone / Claps |
| CL HAT, OP HAT, CYMBAL | Tune / Noise / Brightness |

Hold SETTINGS and turn COLOR / SHAPE / SWEEP / CONTOUR for Waveform / FM Ratio / Drive / Transient. You can edit during playback or hold a step with the same gesture to lock the setting. Some engines do not use every advanced control.

## SY Bits

Plain COLOR adjusts whole-semitone detune. FUNC + COLOR adjusts the fractional part in 0.01-semitone steps across −24.00 to +24.00. These values support sound saving and parameter locks.

SD Vintage, Clap Vintage and SY Toy offer snare, clap and tuned-percussion starting points. Swarm provides three detuned saws for pitched parts.

# Sample Wizard

Audition, lock and transform samples from the track’s browser.

## Preview and sample locks

1. Press FUNC + MACHINES to open sample selection.
2. Highlight a sample. Press the track pad or a keyboard TRIG to audition it; scrolling alone stays silent.
3. To lock it to a step, keep the browser open with the desired sample highlighted, then hold that step’s TRIG + MACHINES.

## Playback modes

SETTINGS + MACHINES selects One-Shot, Loop, Slice, Granular, Stretch, Pluck or Wavetable. SETTINGS + PUNCH opens options for the current mode.

## Slice editing

Use FUNC + a step key to play upper slices. FUNC + click DATA removes a slice marker. Marker knobs can snap to zero crossings.

## Resample

On a Sample Wizard track, press SETTINGS + REC to open Resample. Choose recording options and save the resulting take from that menu.

## Read the display

The home screen shows the sample name, waveform, track and duration. Volume segments show the track volume setting. During playback, pitch, start, end and other parameter locks take priority over CTRL-ALL; CTRL-ALL still edits the base sound for unlocked notes.

**Before locking a sample** — Open the sample browser first and highlight the exact sample you want. The lock gesture uses the highlighted browser entry.

# SPEAK

Build phrases from a 128-word library while controlling pitch and delivery.

| Control | Function |
| --- | --- |
| COLOR | Voice / formant character |
| SHAPE | Word index 0–127; display shows the word and index |
| SWEEP | Speed: 64 is normal, lower is slower |
| CONTOUR | Articulation |

Word changes take effect at the next trig. Voice, Speed and Articulation remain live. Pitch changes independently of word speed. Decay, Fine, PUNCH, Gate, Attack, filters and FX sends are available.

## Program a phrase

1. Choose SPEAK and begin with Decay 127 so complete words can play. A useful level starting point is Vol+Dist 60, with PUNCH off.
2. Place trigs with enough space for each word. Hold each trig and turn SHAPE to lock its word.
3. Lock Pitch and other controls as needed. If words run together, leave more space or increase Speed.

## Example sentence

| Word | Index |
| --- | --- |
| HELLO | 31 |
| I | 0 |
| AM | 62 |
| A | 17 |
| ROBOT | 113 |
| I | 0 |
| LOVE | 35 |
| MUSIC | 106 |

Word and the ordinary sound parameters support locks and LFO destinations. COLOR, SHAPE, SWEEP and CONTOUR use MIDI CC 16, 17, 18 and 19. The complete indexed word list appears in the reference pages.

# Connect & sequence MIDI

Use MIDI Out as a silent track for an external instrument.

## Set the destination

1. Choose MIDI Out in MACHINES.
2. Press FUNC + TRACK to open Track Setup.
3. Select a row with DATA, click before editing, turn to change it, then click again. BACK exits.

| Setting | Choices |
| --- | --- |
| Channel | 1–16 or Global. This is the outgoing channel. |
| Output | Global, Off, USB, DIN or Both. |
| KbT | Keyboard transpose. |
| Pad Note | The note sent by the track pad. |

## Play from an external keyboard

In CONFIG > MIDI, enable note reception and use the track receive channel or auto channel. Incoming notes follow the chosen Output. Track Setup’s Channel sets the outgoing destination, not the receive channel.

Live recording captures notes, velocity and length. For step entry, stop playback, press REC twice, then play and release notes to advance. Normal note/grid controls and FUNC + PAGE pattern-length editing are available.

## Arpeggiate and change machines

Open FUNC + RETRIG > Arp. Enable A. On, or hold RETRIG, to arpeggiate incoming notes. When you choose an audio machine, held and sequenced MIDI notes are released on their original channel and port.

**OUT and THRU together** — Set CONFIG > MIDI > PORTS > OUT/THRU to THR. FUNC + click DATA toggles the Cycles’ own outgoing MIDI while retaining incoming MIDI Thru.

# CC knobs & MIDI LFOs

Assign nine knobs and two LFOs to MIDI controller numbers.

## Assign and record CC controls

1. On MIDI Out, hold SETTINGS and turn one of the nine gray knobs. Choose OFF or CC 0–127.
2. Turn the assigned knob alone to send its value, from 0–127.
3. Hold a TRIG and turn the assigned knob to store a lock. An empty step becomes lock-only. Live recording captures knob movement.

Every lock retains both its CC number and its value. Chance and Swing keep their usual controls. The LFO Speed knob edits the currently open MIDI LFO.

## Edit the two MIDI LFOs

Press LFO to cycle through LFO 1, LFO 2 and the track screen. Use DATA to select a field, click to edit, and BACK to leave.

| Field order | Controls |
| --- | --- |
| 1–4 | Wav, Mul, Dst, Dep |
| 5–8 | Speed, Fade, Phase, Mode |

Dst is OFF or CC 0–127. Editing the destination suspends that LFO’s output until you leave the field. Other assigned knobs continue sending CC.

## Quick LFO assignment

Hold LFO and turn an assigned CC knob to choose its destination. Continue turning for depth.

## Save

Use the normal project or permanent quick-save operation to preserve MIDI settings and locks. Temporary save/reload is available for performance snapshots.

# Saving, USB & diagnostics

Match the save operation to the settings you want to keep.

| Operation | What it does |
| --- | --- |
| Save Project | Keeps the project, including pattern FX choices, Sidechain routing, Scramble checklists and the pattern/track LFO setup. |
| Hold FUNC + SETTINGS | Opens the permanent pattern-save action. |
| Short FUNC + SETTINGS | Stores a temporary pattern snapshot. |
| FUNC + PATTERN | Reloads the temporary snapshot. Available in latched repeat mode. |
| BACK from Mod Setup | Saves global preferences; a pending save waits for playback to stop. |

## USB audio

In Global > USB, choose 2ch for the stereo mix or 6ch for six separate mono tracks. The six tracks are sent before pan and without stereo effect returns. Stereo audio from the computer to Cycles is available in either mode.

Stop playback before changing USB mode. The audio device reconnects; select the resulting channel layout in your DAW if needed.

## Delay divisions

Global > Dly > Div displays musical divisions for Delay. It includes dotted and triplet values; only matching positions use exact divisions of the tempo.

## DX diagnostics

Set Global > DX > On. Tap FUNC, press it again within 350 ms, hold for at least 0.5 seconds, then release. Other controls cancel the gesture. The display shows/resets A/P/O/N: average CPU, peak CPU, overruns and governor voice drops.

**Before powering off** — Stop playback, save the project when needed, and allow pending preference saves to finish. Temporary snapshots are for performance recall, not a substitute for a permanent save.

# Optional controls

These controls apply when their corresponding Machine Optional choices are enabled.

## LEGACY

A six-operator FM machine using a shared 32-voice bank. The active bank is shared by all LEGACY tracks.

1. On LEGACY, press FUNC + MACHINES.
2. Turn DATA to choose a stored DX7 bank.
3. Click DATA to load it, or press BACK to cancel.

Use the Machine Optional flasher’s bank importer to import banks.

## ChordKeys

On CHORD, open FUNC + RETRIG and set Keys On. Outside grid recording, TRIG 1–16 plays scale-based chord voicings. TRACK + a track pad changes track.

In grid recording, hold a TRIG and press T1–T6 to lock harmony. Repeat the same pad to restore the base harmony.

## Vinyl

| Gesture | Parameter |
| --- | --- |
| REVERB SEND | Vinyl amount from the track |
| SIZE | Crackle |
| FUNC + SIZE | Warble Amount |
| Hold FUNC first, then TRACK + SIZE | Warble Speed |

**Modifier order** — For Warble Speed, hold FUNC before TRACK. This keeps the gesture distinct from entering latching mute mode.

# Machinedrum engines

TRX-B2, TRX-SD and TRX-CH are optional machine choices.

Enable the desired engines in Machine Optional and supply your own Machinedrum UW OS 1.63 file in the flasher. Press MACHINES, then turn DATA to choose an enabled engine. The other Optional choices remain available.

| Engine | Panel controls |
| --- | --- |
| TRX-B2 | Bass drum: PITCH = pitch; DECAY = decay; COLOR = distortion; SHAPE = dirt; SWEEP = pitch ramp; CONTOUR = hold; PUNCH = tick. |
| TRX-SD | Snare: PITCH = pitch; DECAY = decay; COLOR = snap; SHAPE = tone; SWEEP = bump; CONTOUR = bump envelope; PUNCH = clip. |
| TRX-CH | Closed hi-hat: PITCH = resonator low-pass/tuning; DECAY = decay; COLOR = metal; SHAPE = high-pass; SWEEP = resonance; CONTOUR = gap. |

These controls belong to the installed machine. Shared track filtering, modulation, sends and sequencing remain available. Lite contains the six stock audio machines.

# Everyday shortcuts

Hold the first button while pressing the second button or turning the knob.

| Task | Gesture | Result |
| --- | --- | --- |
| Mod Setup | Tap SETTINGS + TRACK | Global preferences and track tools |
| Machine selection | Press MACHINES, then turn DATA | Choose a machine |
| Step Recorder | Stopped: REC twice | PLAY forward; STOP back; REC exit |
| Step preview | TRIG + PAGE | Audition with note and locks |
| Parameter slide | SETTINGS + TRIG | Toggle slide |
| Sequence Genie | SETTINGS + PAGE | Generate or queue |
| Scramble sound | Hold SETTINGS + TRACK | Use track checklist |
| Scramble step | TRIG + quick SETTINGS + TRACK | Toggle step mark |
| Mute latch | TRACK + tap FUNC | Requires Mute: LTC |
| Solo | Latched mute: FUNC + track pad | Press again to restore mutes |
| Control All tracks | TRACK + TRIG 1–6 | Toggle participation |
| Audio repeat | TRACK + RETRIG, then TRIG | Hold the repeat division |
| Repeat latch | TRACK + double-tap RETRIG | BACK exits |
| Filter cutoff / resonance | MACHINES + SWEEP / CONTOUR | Add TRACK for Control All |
| Filter type | SETTINGS, then MACHINES + SWEEP | Release to apply |
| Attack | MACHINES + DECAY | Supported machines |
| Reverb / delay choice | TRACK + SIZE / TIME | Release to apply; BACK cancel |
| LFO destination | LFO + destination knob | Add MACHINES for filter/attack |
| Arpeggiator | FUNC + RETRIG | Open Arp settings |
| Scale / page length | FUNC + PAGE | Lock, scale, key, Page Len, Warp |
| Permanent quick save | Hold FUNC + SETTINGS | Pattern-save action |
| Temporary save / reload | Short FUNC + SETTINGS / FUNC + PATTERN | Performance snapshot |
| Silence effect tails | STOP twice | All Sound Off |

# Song and articulation shortcuts

Physical controls for arrangement and linked notes.

| Task | Gesture | Result |
| --- | --- | --- |
| Song editor | SETTINGS + TRACK > Song > DATA | Open the arrangement grid. |
| Song row / pattern / repeats | DATA / PITCH / DECAY | Select row and its contents. |
| Song row mutes | TRIG 1-6 | Toggle track mutes for the row. |
| Song insert / delete | PAGE / FUNC + PAGE | Copy-insert or delete a row. |
| Song end behavior | Click DATA | STOP / LOOP. |
| ACID glide / legato | SETTINGS + PITCH / DECAY | Selected ACID track only. |
| Trig selection | TRACK + PAGE | Toggle selection mode. |
| Selection all / none | Selection active: FUNC + PAGE | Select all eligible trigs or clear. |
| Pattern jump | Global JUMP On; PATTERN then FUNC + TRIG | Jump at the current position. |

Use Save Project for the song and per-track ACID settings. JUMP and the ACID A/F/AF envelope destination save globally.

Bug reports: aveycole.github.io/Supermodel/bugs/. Reports and follow-up discussion are collected in the shared inbox.

# Word library

Choose the index with SHAPE, or parameter-lock a word on each step.

For speech controls and an example phrase, see the SPEAK chapter.

# Find it quickly

An alphabetical guide to the manual.

Supermodel 2.64 • Model:Cycles • English print edition • 30 October 2026.
