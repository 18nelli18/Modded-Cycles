# Modded Cycles: A.V.’s Supermodel Edition

## Quick reference · 13 October 2026

Install the relevant mods first. Hold the first button, then press/turn the next control. **TRIG** = sequencer step; **pad** = track pad; **DATA** = LEVEL/DATA. **PRESET (MACHINES button)** follows Model-TG’s naming below. Independent MIDI Bank with project saving is hardware tested by AveyCole and available alone or alongside your selected machines.

**Storage:** **Stop playback before Save Project and wait for MIDI SAVED. Saved MIDI data loads only when you enter B-side and only while playback is stopped.** FUNC + SETTINGS + TRACK opens B-side. Unsaved edits are lost on power-off. MIDI files are outside Elektron backups and SysEx exports. A-side Second LFO saves **speed, multiplier, waveform, destination and depth** with the sound; fade, start phase and mode reset when loading a sound.

## Sequence Genie, Second LFO and SCRAMBLE

| Feature | How to use it |
|---|---|
| **Sequence Genie** | **SETTINGS + PAGE** opens the current track/lane’s generator. DATA selects; click, turn, click to edit. |
| Generator options | Scale/root, note range, density, velocity/decay/pan ranges, Both/Rhythm/Notes, mutation and Euclidean hits/rotation. B-side uses relevant MIDI controls. |
| Preview and queue | **PLAY / STOP** previews; **FUNC + pad** mutes that side. Generate queues the next loop during playback. **Cancel queue** cancels. Stop for **Undo**; closing discards Undo/queue. |
| **Second LFO** | Press **LFO twice**. DATA selects and edits settings. While this page is open, **LFO SPEED** edits LFO 2. A-side synth controls and keyboard playback remain active. |
| LFO 2 quick assignment | On A-side LFO 2, **hold LFO + turn a parameter knob** to assign its destination; further turning adjusts signed depth. |
| **A-side SCRAMBLE** | **SETTINGS + TRACK** randomizes four machine controls. **Hold TRIG(s), then SETTINGS + TRACK** toggles fresh values each pass, preserving the base sound. Sampler excluded; no Undo. |
| **B-side SCRAMBLE** | **SETTINGS + TRACK** randomizes the selected MIDI lane’s assigned CC values once and shows SCRAMBLE. |

## B-side: six parallel MIDI tracks

M1–M6 play alongside the six audio tracks; default channels **7–12**, assignable in Scale Setup. Display and pad pulses identify B-side activity.

| Action | Shortcut / behavior |
|---|---|
| Enter or leave B-side | **FUNC + SETTINGS + TRACK**. Repeat from B home to exit, or press **BACK** there. BACK inside a window returns to B. |
| Select / play a lane | Press its **track pad**. **FUNC + pad** toggles that lane’s MIDI output without muting its A-side audio track. |
| Grid or keyboard | **REC** toggles grid/keyboard. TRIGs place/remove steps in grid mode or play scale-aware notes otherwise. New steps: **C5**. |
| Edit a step | **Hold TRIG + DATA** to edit; click DATA to cycle **Note → Vel → Len** (highlighted). Clearing removes locks. |
| Live recording | **REC + PLAY** starts. Keep REC held; press PLAY again to toggle quantized/unquantized. |
| Pages and Scale Setup | **PAGE** cycles only through pages within the lane’s length. **FUNC + PAGE** opens length, speed, scale/key and MIDI channel settings. In Scale Setup, PAGE advances length in 16-step increments. |
| Keyboard setup | **FUNC + TRACK** opens **KbT** (keyboard transpose) and **Pad Note**. The keyboard remains playable. |
| Retrig / arpeggiator | **FUNC + RETRIG**: lane defaults. **Hold TRIG + RETRIG**: step menu; press RETRIG again to toggle On/Off. DATA edits; TRIG release closes. |
| Chance / conditions | Turn **CHANCE** for the lane’s stock-style menu; **hold TRIG + turn CHANCE** to lock a step. Release the TRIG to close. If CHANCE is assigned to a CC, it controls that CC instead. |
| Lane copy / clear / paste | **FUNC + REC / PLAY / STOP** = copy / clear / paste. Repeat clear/paste on the same lane to undo. |
| Step copy / paste | **Hold TRIG + REC** copies; **hold destination TRIG + STOP** pastes, including locks. Popup confirms. |
| Global tempo and windows | **TEMPO** opens the stock global tempo menu for all twelve tracks. Close with BACK or TEMPO to return to B-side. Closing B-side windows returns to B-side. |

## MIDI CC knobs, locks, slides and LFOs

| Action | Shortcut / behavior |
|---|---|
| Assign a gray knob | **SETTINGS + knob** selects **OFF/CC0–127** silently. Release SETTINGS to commit; existing locks keep playing. |
| Send / lock a CC value | Turn the assigned knob to send its base value. **Hold TRIG + turn the assigned knob** to store a step lock. |
| Trigless locks | **FUNC + TRIG** places a dim parameter-only step. Hold it + assigned knobs to lock CCs without a note. |
| Return to base | The **next active note without that knob’s lock** restores base. Empty/trigless steps retain the current value. |
| Note and CC slides | **SETTINGS + TRIG** toggles a slide, with a Slide On/Off popup. Notes overlap for legato; CC values glide toward the marked step’s values. |
| MIDI LFO 1 / 2 | Press **LFO**, then press it again for LFO 2. Each targets a CC on that lane’s channel. Keyboard playback stays active. |
| Confirm an LFO destination | **Dst → DATA → scroll OFF, CC0–127 → DATA** confirms. **BACK** cancels; another BACK closes. Names scroll; the confirmed destination keeps playing. |

## Other selectable mods

| Mod | Function / relevant controls |
|---|---|
| **Model-TG** | Sampler, resampling, master FX, synth additions, slide trigs and Scale Lock. **SETTINGS + PRESET**: Sampler playback mode; **SETTINGS + PUNCH**: mode options; **SETTINGS + REC**: resampling. **SETTINGS + RETRIG**: repeat/master FX page; **SETTINGS + BACK**: master FX off. **SETTINGS + TRIG**: audio slide; **FUNC + PAGE**: Scale Lock. **PRESET + DECAY / SWEEP / CONTOUR**: attack / filter / resonance. |
| **Sample preview** | On a Sampler track, **FUNC + MACHINES (PRESET browser)**, select a sample, then press the pad or keyboard TRIG to audition it. Scrolling is silent. |
| **Latching mute / trig preview** | Hold **TRACK + tap FUNC** to latch mute mode; tap FUNC to leave. With playback stopped/paused, **hold TRIG + PAGE** to audition the step and its locks. |
| **Arpeggiator / Chord Keys** | **FUNC + RETRIG** edits Arp direction/Oct or Chord Keys setup. Arp plays held notes with **RETRIG held** or A.On. Chord Keys on a CHORD track: TRIG1–7 = I–VII, 8–14 = octave up, 15–16 = I–II two octaves up. |
| **MACRO / ACID / Syntakt** | MACRO adds 47 Braids models: SHAPE selects; COLOR/SWEEP shape the sound; CONTOUR sets envelope amount; **FUNC + PITCH** adds lo-fi. ACID: COLOR cutoff, SHAPE resonance, SWEEP env mod, CONTOUR drive, DECAY decay; PUNCH switches saw/square. Overlapping ACID note lengths slide. Syntakt engines are added from your own uploaded Syntakt OS. |
| **Track Filter / LFO 2, 3, 4** | Optional alternatives to Second LFO. **MACHINES + SWEEP** sets LP/OFF/HP filter; CONTOUR resonance, COLOR/SHAPE envelope. Extra-LFO option cycles pages with repeated **LFO** presses; LFO2 saves with the sound, LFO3/4 remain RAM-only. The flasher enforces conflicts. |
| **USB audio / MIDI routing** | Six-channel USB sends six separate tracks instead of the stereo mix. The MIDI OUT + THRU combo combines outgoing and incoming MIDI. Select **CONFIG → MIDI → PORTS → OUT/THRU: THR**, then **FUNC + click DATA** to enable/disable the Cycles’ own outgoing MIDI. |
| **Display and editing** | Three-name browser; long names scroll. **DATA** shows volume, **FUNC + DATA** pan. Dim trigless steps; half-second trig-removal grace; 546 BPM maximum. |
| **Startup / Select All** | SUPERMODEL by A.V. replaces the startup animation. Select All prefers it over the old Modded Cycles animation, and keeps Model-TG plus Live MIDI OUT + THRU. |

ChordKeys requires Model-TG. MIDI Bank and extra synth machines are optional for ChordKeys; checking it does not select all mods.

Control All Config: hold TRACK + TRIG1–6 to include/exclude each audio track, including the selected track. TRACK + knob changes included tracks. Choices reset on power-off.

## Control All Beat Repeat (hardware tested)

Hold TRACK + RETRIG throughout, then hold a TRIG key. Release either modifier to stop. Control All Config chooses which tracks repeat. Hold both modifiers to replace its track choices with all sixteen repeat divisions; no dedicated screen or master FX. TRIG 3 = 1/32; TRIG 5 = 1/16; TRIG 7 = 1/8; TRIG 10 = 1/4; TRIG 16 = one bar (long slices halve at slow tempos). Newest held TRIG wins. Outgoing MIDI notes are not repeated. Hardware tested by AveyCole.

Experimental feedback: beat-repeat divisions appear briefly in a popup. During FUNC in B-side, unmuted pads stay lit and muted pads stay dark except B-note pulses. Selected-track highlight returns on FUNC release. Hardware verification pending.
