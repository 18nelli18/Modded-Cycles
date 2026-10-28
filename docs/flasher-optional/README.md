# Supermodel Machine Optional

Experimental separate flasher, based on approved Full v215 and Lite v216 (release 2.56). The main flasher links here; its firmware images and preparation code are unchanged.

Only some combinations have been tested on hardware. Use this version at your own risk. Build, browser and native emulation checks do not establish hardware compatibility for every combination.

The six stock machines and shared quality of life features are always included. Select any of the nineteen additions. None returns exact Lite v216; all returns exact Full v215. Mixed selections retain a fixed runtime layout with excluded DSP dormant, so removing a machine does not reduce file size or free its reserved state. Existing sounds using an excluded machine remain stored but play silently until an available machine is selected.

Users supply official firmware files. Preparation and Model:Samples conversion run locally in the browser, using the existing main flasher's verified builder and transfer code. No user firmware is uploaded. The two approved base images use their existing immutable URLs and checksum-verified fallback. No extra firmware image is distributed by this page.

`optional-builder.js` verifies both approved SysEx hashes and official Cycles OS 1.13, applies guarded own-code patches from `recipe.js`, verifies Python/browser byte parity, then prepares a fixed four-literal selection mask. All custom masks have the same packed layout and capacity. Only MAIN is changed; original bootstrap and updater sections remain protected. Both Model:Samples installation paths use the existing guarded converter.

The selector sources are in `tools/machines/optional_selection/`; `tools/gen_optional_selection.py` regenerates the own-code recipe inputs from the pinned approved base, its generated build metadata and the user's official Cycles image. Supply `--base`, `--metadata`, `--cycles`, `--cross` (compiler prefix) and optional `--output`. The base hash is mandatory and cannot silently follow a newer release.

Validation recorded in `BUILD.json`: exhaustive selector checks for all 524,288 masks, native selector/dispatch/service tests, 44 representative signed images on Cycles and both Samples paths, 44 native payload bootstraps, eight native Samples bootstrap/signature checks, and real browser tests of selection, requirements, stale results and sending locks. Hardware testing remains incomplete.
