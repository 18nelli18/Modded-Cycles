# Supermodel Machine Optional 3.06

The updated 3.06 bases synchronize FX at the live pattern boundary, preventing
another pattern's FX from being saved into the outgoing pattern. The version
stays 3.06; new immutable image hashes and cache stamps identify this fix.
Reselect intended FX once if wrong choices were already saved.

The 3.06 Optional Full and Lite bases use master FX shared across all six
tracks, with effect choices and added settings saved per pattern. The FX/MST
menu row is removed. GOV offers Lod, Trk and INV; INV reverses the track-order
stealing priority from 6 toward 1. Track Swap preserves full track levels,
handles all four menu rows, and rejects mismatched project/pattern contexts.
Legacy, ChordKeys, Vinyl and all nineteen original machine choices remain;
TRX-B2, TRX-SD and TRX-CH bring the selector to twenty-two choices.

The six stock machines and shared features are always included. None returns
the exact Optional Lite base. The original nineteen choices without TRX use
the Optional Full base; All also selects the three TRX engines and requires
the official Machinedrum file. These bases differ from main's feature-removal editions. Mixed
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

Current 3.06 checks cover all four base cold boots, native GOV/INV and menu
navigation, master FX project save/load into a fresh emulator, native Swap
level reads and context-race refusals. Nine Optional selections and six
Machinedrum selections pass integrity/capacity checks; three custom outputs
also boot and preserve the new feature modules. Main Full/Lite selection,
file requirements, exact downloads and asynchronous cache handling pass in a
real browser. The preceding personal test build was confirmed by the user;
this does not establish hardware results for every machine combination.

Les quatre socles3.06 sont verifies en emulation : demarrage, GOV/INV,
navigation, FX master par pattern et protections Swap. Neuf selections
Optional et six selections Machinedrum passent les controles de capacite et
d'integrite ; trois sorties personnalisees demarrent avec les modules nouveaux
conserves. Le test personnel precedent a ete confirme, sans validation
materielle de toutes les combinaisons.

# Machinedrum engine choices / Moteurs Machinedrum

The experimental Machinedrum integration adds TRX-B2, TRX-SD and TRX-CH as
three choices, credited to Talachan12's port. There are 22 optional choices;
the original 19 remain checked initially. Selecting a TRX engine requires the
official Machinedrum UW OS 1.63 `.syx`, or the verified 1.63 reference `.bin`.
Files stay in the browser. These choices generate an experimental 3.06 image;
normal selections continue using the pinned 3.06 bases until release promotion.
Native emulation is verified; hardware confirmation is pending.

L'integration experimentale ajoute TRX-B2, TRX-SD et TRX-CH, d'apres le port
de Talachan12. Il y a22choix ; les19precedents restent coches au depart.
Un moteur TRX exige le SYX officiel Machinedrum UW1.63 ou le BIN1.63 epingle.
Les fichiers restent dans le navigateur. Ces choix generent une image3.06
experimentale ; les choix ordinaires conservent les socles3.06 jusqu'a la
promotion de release. Emulation native verifiee ; confirmation appareil attendue.

Build source: `tools/gen_optional_machinedrum.py`. Proof:
`machinedrum-validation.json`. Technical details: note203.
