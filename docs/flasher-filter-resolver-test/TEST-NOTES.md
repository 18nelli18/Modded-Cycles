# Genie + TINY test notes

- TINY was confirmed by A.V. to work in the previous test build.
- The queued Genie tick reserves 36 bytes for its register frame and preserves the live registers it uses before chaining to the native LED callback.
- The lamp subobject now lives at offset `0x3000`; queued playback snapshots occupy offsets `0x2D24..0x2FF5`. The dynamic object allocation grows to `0x3010`, enough for the lamp’s 12 bytes of state.
- Browser-side recipe/build checks passed for TINY + Genie + Wizard and Select All, including checks of the relocation and allocation bytes. Native ColdFire emulation was unavailable in this environment, so this is still a crash-fix candidate and is not hardware verified. Test first while stopped, then while playing, including another Generate after a queued sequence applies.
