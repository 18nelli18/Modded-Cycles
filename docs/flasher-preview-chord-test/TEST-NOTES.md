# Sample Preview + ChordKeys

Separate hardware test based on the current main flasher. Removes the obsolete mutual exclusion for the relocated ChordKeys implementation; the non-WAVE pair keeps its firmware bytes unchanged. With WAVE, guarded browser and pad continuations preserve wavetable selection/loading as well as Wizard preview. WAVE is compatible as well.

Select Sample Preview and ChordKeys; Wizard is enabled automatically. On a Wizard track open FUNC + MACHINES, highlight a sample and play its pad/keyboard to audition it.

Validated: signed browser builds for the pair, Genie, Attack, all compatible features with and without WAVE, and no extra machines. Native startup preserves ChordKeys, Wizard and stock CHORD tables. Real native browser and note paths include resident/missing samples, failed/busy loads, ordinary presets, non-Wizard tracks and register preservation. Filesystem and sample loader are simulated. The WAVE-native test exercises its real browser and pad routes; filesystem/sample loading are simulated. Physical hardware remains to be checked. Main and the separate filter test remain unchanged.
