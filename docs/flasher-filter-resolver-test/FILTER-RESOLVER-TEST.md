# Per-track filter resolver test

This isolated test page uses the existing TINY/MACRO/Syntakt-capable flasher and a candidate resolver hook for Per-track Filter. Model-TG is excluded because it has its own conflicting filter implementation.

Hardware check: build with Per-track Filter and Syntakt, MACRO, and/or TINY selected. On a Syntakt track, hold MACHINES and turn SWEEP; it should select Filter Cutoff rather than Detune. Check the actual cutoff/resonance behavior on each included machine. This is experimental and not hardware verified. Main remains unchanged.
