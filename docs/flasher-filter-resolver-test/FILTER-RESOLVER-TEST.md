# Per-track filter resolver test

This isolated test page uses the existing TINY/MACRO/Syntakt-capable flasher and a candidate resolver hook for Per-track Filter. Model-TG is excluded because it has its own conflicting filter implementation. Per-track Filter is designed to coexist with Second LFO, Sample Wizard, Sample Preview, and Synth Attack; its settings now occupy separate parameter and sound-save slots.

Hardware check: build with Per-track Filter and any combination of Second LFO, Sample Wizard, Sample Preview, Synth Attack, Syntakt, MACRO, and/or TINY. On a Syntakt track, hold MACHINES and turn SWEEP; it should select Filter Cutoff rather than Detune. Check cutoff/resonance on included synth/drum machines, plus LFO 2 sound save/load. This is experimental and not hardware verified. Main remains unchanged.
