# Genie lamp / mute lights and synth Attack

New test, main and 909 unchanged by this candidate. The shared per-track filter has been removed following the hardware clicking report. Wizard retains its own filter.

- Select Sample Wizard + Sequence Generator: S.G. lamp at left, four menu rows at right; Generate first, Queue next.
- Hold FUNC and press a track pad in Genie: mute/unmute stock audio tracks. Muted pads are dim, unmuted pads lit. The native background step display and trigger pulse path remain active.
- Select Synth Attack: MACHINES + DECAY changes Attack on stock and added synth/drum machines. Hold a trig to lock Attack. Sound saves preserve it. Wizard keeps its existing attack and receives no duplicate envelope.
- Zero Attack bypasses processing exactly. The ramp reaches full level in approximately 2.03 seconds at the maximum setting.
- The new UI and Attack currently use Sample Wizard's shared support. Without Wizard, the previous Genie implementation remains unchanged. LFO 2/3/4 compatibility remains a separate unfinished task; Second LFO works in this candidate.
- Existing cards retain the owner's hardware-tested designation. New Attack and this combination still require hardware verification. A badge changing under Select All is a known display issue queued immediately after publication.

Validated in native ColdFire emulation: six-track attack/zero bypass/retriggers, sound and lock codecs, all 64 mute masks, actual LED manager/RTTI/first-wins writer with a background step fixture, native OLED raster, startup/cache/31 CHORD tables with and without extra machines. Browser: nine real selected builds, signed containers/reference checks, EN/FR and actual HTML resource loading. Physical cache and MIDI/audio hardware are not emulated.
