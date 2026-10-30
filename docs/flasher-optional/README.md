# Supermodel Machine Optional 2.62

The updated Optional Full and Lite bases include per-track FX, Global FX
MST/TRK controls, per-pattern/project FX persistence, the later LFO/filter and
native audio/DMA fixes, packed repeat-history writes, distinct Punch attacks
and the inactive-FX zero bypass. Both startup screens and this flasher display
2.62. Optional retains Legacy, ChordKeys, Vinyl and all nineteen machine choices.
Legacy keeps its original full-rate processing; only MACRO's existing supported
models receive the selective ECO behavior used by main Full.

The six stock machines and shared features are always included. None returns
the exact updated Optional Lite base; all returns the exact updated Optional
Full base. These bases differ from main's feature-removal editions. Mixed
selections retain a fixed runtime layout with excluded DSP dormant. Removing
a machine does not reduce file size or free its reserved state. Existing sounds
using excluded machines remain stored but play silently until an available
machine is selected.

The browser verifies checksum-pinned immutable Full/Lite assets and applies
guarded own-code patches from `recipe.js`. It checks Python/browser byte parity
and uses four independent literal bytes for the selection mask. Only MAIN is
changed; recovery/updater sections remain protected. Both Model:Samples
installation paths use the existing guarded converter. Files are processed
locally; user firmware is not uploaded.

Audio-module sources are in `tools/machines/track_fx/`; selection sources are
in `tools/machines/optional_selection/`. `tools/gen_optional_selection.py`
requires explicitly pinned Full/Lite hashes for a new release. Run
`tools/check_release_versions.py --base origin/main` before each release push
to verify the new release number, image hashes and actual compiled title bytes.

Fresh 2.62 checks cover both base bootstraps, per-track controls and storage,
96 native mixer comparisons, eight signed selections on Cycles and both Samples
transports, eight native payload boots, 65 native selector masks, 5265 selector
comparisons and 1625 native dispatch checks. The browser checks all nineteen
choices, All/None/Legacy-only selection, displayed versions and the sending lock.
See `validation257.json` for the exact results and scope.

Experimental: hardware timing and every mixed selection remain unverified.
The prior selector/gate patch bytes are unchanged, but earlier whole-image or
hardware validation is not claimed for these new binaries. Held-step Punch/Gate
behavior and rhythmic Chord/filter clicking still need device confirmation.
# Machinedrum engine choices / Moteurs Machinedrum

The experimental Machinedrum integration adds TRX-B2, TRX-SD and TRX-CH as
three choices, credited to Talachan12's port. There are 22 optional choices;
the original 19 remain checked initially. Selecting a TRX engine requires the
official Machinedrum UW OS 1.63 `.syx`, or the verified 1.63 reference `.bin`.
Files stay in the browser. These choices generate an experimental 2.62 image;
normal selections continue using the pinned 2.62 bases until release promotion.
Native emulation is verified; hardware confirmation is pending.

L'integration experimentale ajoute TRX-B2, TRX-SD et TRX-CH, d'apres le port
de Talachan12. Il y a22choix ; les19precedents restent coches au depart.
Un moteur TRX exige le SYX officiel Machinedrum UW1.63 ou le BIN1.63 epingle.
Les fichiers restent dans le navigateur. Ces choix generent une image2.62
experimentale ; les choix ordinaires conservent les socles2.62 jusqu'a la
promotion de release. Emulation native verifiee ; confirmation appareil attendue.

Build source: `tools/gen_optional_machinedrum.py`. Proof:
`machinedrum-validation.json`. Technical details: note203.
