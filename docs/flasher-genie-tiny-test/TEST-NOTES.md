# Sequence Genie + TINY test — 16 October 2026

- Sequence Genie uses the no-Model-TG experimental path and requires Sample Wizard for this build. TINY is an optional machine choice; other compatible options remain selectable. Select All includes the combined Genie + Sample Wizard + TINY path.
- TINY was confirmed by A.V. to work in the previous test build.
- The queued Genie tick reserves 36 bytes for its register frame and preserves the live registers it uses before chaining to the native LED callback.
- This candidate fixes a lamp-state collision: the lamp subobject now lives at offset `0x3000`, beyond queued playback snapshots at `0x2D24..0x2FF5`. The dynamic object allocation grows to `0x3010`, enough for the lamp's 12 bytes of state.
- Browser-side recipe/build checks passed for TINY + Genie + Wizard and Select All, including checks of the relocation and allocation bytes. Native ColdFire emulation was unavailable, so the Genie lamp fix is not hardware verified.
- Hardware test: open Genie after its intro, generate with playback stopped and while playback is running, then generate again after a queued sequence applies. Confirm the lamp/menu renders and no exception occurs.
