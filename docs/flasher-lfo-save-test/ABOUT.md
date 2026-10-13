# Audio LFO 2 native sound-save test

Experimental. Main flasher and MIDI persistence are unchanged.

Five saved fields: speed, multiplier, waveform, destination, depth.
Fade defaults to 0x4000, start phase and mode to 0 on sound load.
Speed/depth use the upstream saved precision (7 low bits discarded).
Credits: 18nelli18 MIT implementation, idea and format from DavidCaruso.

Native hooks inside the OS functions preserve Model-TG entry detours.
The private context and audio/prepare entry addresses retain the published MIDI bank ABI.
No filesystem sidecars or MIDI save hooks are installed by this candidate.
Track Filter and LFO 2/3/4 are incompatible (shared sound fields and sprite space).
MACRO, ACID, Model-TG and the current MIDI bank remain available.

## Validation

- Native sound converters: both save formats, reload, older sounds, new sounds, unknown tags.
- Six-track UI bridge, OFF mapping, all eight editable fields, only five persisted.
- Native audio dispatcher: inactive identical to stock, 64 blocks with both LFOs active.
- Menu/quick-assign regression suite with separate bridge proof.
- Browser builds for the combined selection with USB6 enabled and disabled.

Hardware verification pending: edit five fields, Save Project, change fields,
Reload Project and power cycle. Confirm fade/start/mode reset as documented.
Test sound save/recall and MIDI bank playback too. MIDI persistence remains unfinished.
