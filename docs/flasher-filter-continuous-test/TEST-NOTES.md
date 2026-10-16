# Continuous-history filter test

Separate experimental test; main keeps the hardware-verified Genie/Attack build with the shared filter withdrawn. Stable Supermodel 909 unchanged.

- Select All includes the corrected per-track low-pass filter, Synth Attack and Wizard support.
- MACHINES + SWEEP: cutoff. MACHINES + CONTOUR: resonance. Hold TRIG while adjusting for locks; CC74 cutoff / CC71 resonance.
- Fully open cutoff + resonance zero is an exact bypass. Wizard retains its own filter. No high-pass or separate filter envelope.
- The shared ladder now keeps its history across voice triggers. The old reset produced a repeated 64,913,408-unit block-boundary jump under a sustained-input fixture; the corrected history settles without that periodic jump. This is native-code evidence, not a hardware claim.
- Attack runs before the shared filter; sound saves retain Attack/cutoff/resonance and Second LFO's five stored settings. Wizard's packed sample mode/Slice state remains intact.
- Includes the hardware-confirmed Genie allocation correction/lamp and attack controls.
- New refinement: while FUNC is held in Genie, muted pads are off, unmuted pads lit; the native trigger-pulse path remains active on both. This refinement needs hardware verification.
- Existing hardware-tested badges persist under Select All. The corrected shared filter remains experimental.

Validation: actual ColdFire ladder discontinuity reproduction and continuous-history comparison; installed pre/post adapters and voice-pointer-free processing; seven native sound round-trips including Second LFO; ten signed browser selection builds with references; real HTML order/resources; complete Genie native constructor/intro/menu transition and LED manager proofs. Physical cache and physical MIDI/audio are not emulated.
