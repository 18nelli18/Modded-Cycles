# Per-track Filter resolver test notes

- This page combines the filter resolver candidate with the native-sound Second LFO candidate. Their writes do not overlap; both patch sets applied to the official OS 1.13 image successfully in the local build check.
- Filter controls now occupy k24–27 and use save bytes +84/+86. Second LFO remains at k28–32 and +88–91.
- The feature resolver allows Filter with Second LFO, Sample Wizard, Sample Preview, and Synth Attack. Model-TG remains excluded due to its separate filter implementation.
- Check on hardware: select Filter with each desired option; on Syntakt, MACHINES + SWEEP should select Filter Cutoff rather than Detune. Verify filter sound, LFO 2 save/load, Wizard playback, preview, and attack.
- Firmware emulation currently exits with SIGILL even on Filter alone, so this candidate is not hardware verified. Main remains unchanged.
