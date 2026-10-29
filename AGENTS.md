# AGENTS.md — Modded Cycles

Guidance for coding agents working on this repository. Read this file first, then the `AGENTS.md` of every folder
you touch:

| Folder | Read before you change |
|---|---|
| [`tools/AGENTS.md`](tools/AGENTS.md) | generators, the Python build, ColdFire code, emulation proofs |
| [`tweaks/AGENTS.md`](tweaks/AGENTS.md) | the tweak JSON files and `PROVENANCE.md` |
| [`docs/AGENTS.md`](docs/AGENTS.md) | the website, the web flasher, the guide, the release notes |
| [`notes/AGENTS.md`](notes/AGENTS.md) | the technical notes |

## What this project is

Firmware mods for the **Elektron Model:Cycles, OS 1.13** (ColdFire MCF54415, big-endian m68k). A mod is a *tweak*: a
table of byte writes (`old` → `new`) applied to section 3 (the MAIN OS) of the user's **own** official `.syx`, plus,
for some mods, code compiled or assembled into free space. Users pick mods in a web flasher
(`docs/flasher/`, served by GitHub Pages at <https://18nelli18.github.io/Modded-Cycles/>), which builds the firmware in
the browser and sends it over USB. A pure-Python toolchain (`tools/build.py`) does the same build on the command line.

Owner: Maxime (GitHub `18nelli18`). He tests every firmware change on his own Model:Cycles.

## Hard rules

1. **Never commit an Elektron firmware image**, original or modified, or any bytes copied from one (no `.syx`, `.zip`,
   extracted sections, dumps). `.gitignore` covers `firmware/`, `*.syx`, `*.zip`, `build/`, `vendor/`, `*.wav`. A tweak
   carries only its own writes; code taken from the Syntakt OS is extracted **at build time** from the user's file
   (recipes and relocation tables only, see notes/17).
2. **Build from the official image only**, never on top of a previous build. Every write carries its `old` bytes and
   the build refuses a mismatch. Stock hashes are in `tweaks/model-cycles_OS1.13/device.json`.
3. **Hardware testing is Maxime's.** A new mod ships as `"status": "experimental"`. Only after he reports that it works
   on his Model:Cycles does it become `"tested"`, in a separate commit ("… tested on the Model:Cycles"). Never mark
   anything tested yourself, never claim a hardware result you did not get from him.
4. **One user-visible change, one PR**, with its docs, guide, release notes and note in the same PR. Open it as a
   draft and ask before merging; Maxime merges after testing on the hardware.
5. **Prove it in emulation first.** Every mod has a generator with `--check` and a proof under `tools/emu/` that runs
   the OS's own code (Unicorn), stock vs patched. Unproven code does not go in the flasher.
6. **Recovery must stay possible.** Only section 3 is touched; the bootloader and updater stay identical, so the
   STARTUP MENU (MIDI IN) can always bring back the official OS. The web flasher only offers tweaks that keep
   `CONFIG › UPGRADE` over USB working.
7. **Respect the licenses and credit authors.** drumkilla's tweaks and `tools/mtlib/` (MIT), Model-TG by
   TinyGregAudio (MIT, `LICENSE-Model-TG`), ms-multi-output by scottmetoyer (MIT). Record the origin of every tweak in
   `tweaks/model-cycles_OS1.13/PROVENANCE.md` and set `credit` on its flasher card.

## Languages

- **Talk to Maxime in French.**
- **French**: technical notes (`notes/`), `BUILD.md`, `FLASH.md`, `dossier-technique.md`, `PROVENANCE.md`, tweak
  `name`/`description`, comments and docstrings in `tools/`.
- **English**: `README.md`, commit messages, PR titles and bodies, the code of the web pages.
- **Both, side by side**: everything users see on the site (flasher cards, guide, release notes, home page), as
  `en`/`fr` pairs or `data-l="en"`/`data-l="fr"` spans. Never add one language without the other.
- User-facing text speaks to musicians: what the mod does on the machine, which buttons to press, its limits. No
  addresses or jargon there; those belong in the notes.

## Repository map

```
tweaks/model-cycles_OS1.13/   tweak JSON files (generated), device.json, PROVENANCE.md
tools/build.py                Python build: applies tweaks, checks caves, repacks and re-signs (mtlib)
tools/gen_*.py                one generator per mod: writes its tweak JSON, --check verifies it is up to date
tools/machines/<mod>/         C and assembly sources compiled into the firmware
tools/emu/                    Unicorn emulation of the OS: test_<mod>.py proofs, mcengine.py, emac.py, syntakt.py
tools/gen_flasher_tweaks.py   FEATURES list -> docs/flasher/tweaks.js (generated)
tools/check_overlaps.py       no firmware needed: mods that can be ticked together never write the same bytes, except
                              the same whole write or a mod applied on top of another (`requires`) (notes/49)
tools/registry.py             no firmware needed: builds tweaks/model-cycles_OS1.13/REGISTRY.md from the tweaks, the
                              registry of free space (freed sprite masks, caves, payloads) and OS hooks (notes/52)
tools/ref_mainos.py           reference hashes in docs/flasher/app.js: each mod (REF_MODS) and a sample of combinations
                              (REF_MAINOS: each card alone, every pair, the largest ones)
tools/web*_check.*, webflash_smoke.*   checks of the web flasher against the Python build (node, jsdom)
docs/                         GitHub Pages site: index.html, flasher/, guide/, assets/release.js
notes/                        numbered technical notes (French), index in notes/README.md
BUILD.md, FLASH.md            command-line build and flashing (French)
.github/                      discord.yml + scripts/discord.mjs: new versions, mod status changes and merged PRs -> Discord
README.md                     English overview for Model:Cycles owners (mod table)
```

## Adding a feature for users (the usual PR)

Follow the shape of the last ones (tempo-max: commits `5997b4a`, `14fb9fa`, `6e592bc`; trig-hold, arp). In order:

1. **Investigate and write the note.** New file `notes/NN-<slug>.md` (next free number; 53 is the last) with the
   user's request and its source, the OS code involved (addresses, `[FAIT]`/`[HYP]`), the design, free space used and
   conflicts with other tweaks. Add a row to `notes/README.md`. See `notes/AGENTS.md`.
2. **Write the generator** `tools/gen_<mod>.py` (and sources under `tools/machines/<mod>/` if it has code). It reads
   the official `.syx`, checks the stock bytes, and writes `tweaks/model-cycles_OS1.13/NN-<id>.json`; `--check`
   compares with the committed file. See `tools/AGENTS.md` and `tweaks/AGENTS.md`.
3. **Prove it**: `tools/emu/test_<mod>.py`, stock vs patched, on the OS's own code, alone and with the other mods
   (`--with 6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm,arp,trig-hold,… --syntakt Syntakt_OS1.42.syx`).
   `tools/check_overlaps.py` must pass: its writes overlap no tweak it can be installed with (run it with `--git` on
   the open branches too), or it declares `conflicts`. Code goes in a mask marked free in
   `tweaks/model-cycles_OS1.13/REGISTRY.md`; `python3 tools/registry.py` regenerates that file (commit it) and refuses
   a write in a mask whose sprite is not redirected.
4. **Register it**: `tweaks/model-cycles_OS1.13/PROVENANCE.md` row; `BUILD.md` section with the commands and the
   MAIN OS SHA-256 of the main combinations.
5. **Put it in the flasher**: add it to `FEATURES` in `tools/gen_flasher_tweaks.py` (`"status": "experimental"`, and
   its section `cat`), regenerate `docs/flasher/tweaks.js`, regenerate `REF_MAINOS` and `REF_MODS` with
   `tools/ref_mainos.py`, add its row texts (`FEAT` en + fr: `label`, `short`, `desc`) and guide anchor (`GUIDE_OF`) in
   `docs/flasher/app.js`, update the lists checked by `tools/webflash_smoke.js`. See `docs/AGENTS.md`.
6. **Document it for users**: a guide section in `docs/guide/index.html` (en + fr, buttons to press, limits), a new
   release at the top of `docs/assets/release.js` (en + fr), bump the `MC_BUILD` / `?v=` stamp on the pages, a row
   in the mod table of `README.md`.
7. **Validate** (below), commit, push, open a **draft** PR, and tell Maxime what to test on the machine.
8. **After his test**: a small follow-up commit flips the status to `tested` (generator `FEATURES`, `tweaks.js`,
   guide, release notes, README, note: "Testé sur la machine (JJ/MM/AAAA)"). If he reports a problem, record it in the
   note, fix, and bump the release.

A fix to an existing mod follows the same path, minus the new files: note section, generator, proof, regenerated
JSON/`tweaks.js`/`REF_MAINOS`, release entry.

## Validation before pushing

Without firmware (always possible, run them all):

```sh
python3 tools/gen_flasher_tweaks.py --check      # tweaks.js matches tweaks/
python3 tools/check_overlaps.py                  # mods ticked together never write the same bytes (notes/49), except the
                                                 # same whole write or a mod on top of another (`requires`)
python3 tools/registry.py --check                # REGISTRY.md (free space and hooks, notes/52) matches tweaks/
python3 tools/relocate_6ch.py --check            # needs m68k binutils (below)
tools/webbuild_check.sh                          # builder.js == build.py, byte for byte (node)
tools/webflash_check.sh                          # flasher.js validates .syx like mtlib (node)
tools/webflash_smoke.sh                          # the flasher page in jsdom (node, npm, network)
python3 -m py_compile tools/*.py tools/emu/*.py
```

With the official files (download them from elektron.se into `firmware/`, which is git-ignored:
`model-cycles_OS1.13.syx`, SHA-256 `44fe5862…9800640c`; `Syntakt_OS1.42.syx` for the Syntakt engines):

```sh
python3 tools/gen_<mod>.py --cycles firmware/model-cycles_OS1.13.syx --check
python3 tools/emu/test_<mod>.py --cycles firmware/model-cycles_OS1.13.syx
python3 tools/ref_mainos.py --cycles firmware/model-cycles_OS1.13.syx --syntakt firmware/Syntakt_OS1.42.syx --check
tools/webflash_smoke.sh firmware/model-cycles_OS1.13.syx firmware/Syntakt_OS1.42.syx   # the REF_MAINOS sample, each mod checked
```

Emulation needs `pip install unicorn numpy`. Code mods need the m68k toolchain (`m68k-linux-gnu-*` from the Debian/Ubuntu
packages `binutils-m68k-linux-gnu gcc-m68k-linux-gnu`, or `m68k-elf-*`); some committed outputs were compiled with a
specific GCC (SD VINTAGE v2 with `m68k-elf-gcc` 16.2, notes/16 §6), so `--check` can differ with another compiler.
If a check cannot run (no network, no toolchain), say so in the PR instead of skipping it silently.

## Commits and PRs

- Commit messages in English: a short subject saying what the user gets ("Tempo up to 546 BPM (tempo-max tweak,
  notes/38)"), a body with the why, the bullets of what changed, and how it was proven.
- Merge `main` into a feature branch rather than rebasing shared branches; regenerate `tweaks.js` and `REF_MAINOS`/`REF_MODS`
  after a merge instead of resolving their conflicts by hand.
- The PR body says what the user sees before and after, how it was proven, and **what Maxime should test on the
  machine** (which mods ticked, which buttons, what to listen or look for).


## AveyCole test/release policy (2026-10-17)

AveyCole explicitly requests the CPU average/peak and CUT diagnostic display in all future test builds, and never in released main firmware. Keep the diagnostic in test-page compositions only. When a test includes audio beat repeat and the SY load counters, retain the TRACK + RETRIG release popup. If a test lacks those counters, explain that limitation instead of fabricating readings. Do not promote diagnostic payloads or UI cards into the main release flasher when promoting a tested repair. Preserve this separation in generators and publication diffs.

## AveyCole private companion builds (2026-10-22)

AveyCole requests both shared-filter and no-shared-filter private variants by
default for future CPU/engine tests. Both retain Sample Wizard's internal
Polivoks-style filter unless explicitly changed. Build and prove each composition
independently; serve separate checksum-pinned pages and cross-link them. Keep
previous comparisons and released main fixed unless promotion is requested.

## AveyCole main 2.16 promotion (2026-10-22)

AveyCole explicitly approved promoting the exact shared-filter v33 file to main
as release 2.16, retaining its saved DX toggle (Off by default). This supersedes
the older no-diagnostics policy for this approved release. Publish that exact
checksum-pinned image through the existing tracked fixed-main delivery path;
do not add other firmware images or private dumps. Credit Glycinate for Feral.

## AveyCole main2.17 promotion (2026-10-22)

AveyCole explicitly approved promoting the exact shared-filter v40 image to main,
with updated feature/shortcut guides and PDF, after reporting “v40 worked”.
This approved release retains DX and every cumulative CPU fix. Its SysEx SHA256
is `8e11e8bed03666f4444f818f6a5d7dea67199f077eddf9d623de81584041e7cb`.
Update only the established tracked fixed-main delivery image; never add other
firmware dumps. Preserve private comparisons. Follow-up credit and low-bit
investigation requests do not authorize silently changing these approved bytes.

## AveyCole main2.18 promotion (2026-10-22)

AveyCole explicitly approved the attached shared-filter v42 with “perfect, push this to be main”. Its SysEx SHA256 is `ea901ab5301763d0ebdd3e4656da57857c308f2a57a5ec841af6dff5d8718560`. Promote this exact image with BACK latch exit, edit protection and the v41 Tone/crusher repairs. Preserve earlier private comparisons. The saved DX option and all cumulative CPU fixes remain in this approved image.

## AveyCole main2.19 promotion (2026-10-22)

AveyCole reports the TINY-addition test working and explicitly requests “push 43 all features to main”. Promote the all-features shared-filter v43, SHA256 `106fe446fdc9a43cd3ea89c241b65ba198ae8a2b347913a4453cf81b1392ac67`, retaining every v42 feature and all nineteen engines. The subsequent request to move TINY before MIDI Out concerns menu order; preserve saved machine IDs. Feral default/Color silent spots are a subsequent audit, not silently folded into this approved release.

## AveyCole main2.20 promotion (2026-10-22)

AveyCole reports “v46 worked, make that the main push”. Promote the exact shared-filter v46, SHA256 `2db3be51ad7f7e44bfbd7919cd4babb583a38746672728bca2ef8c87d093627e`, with the per-track six-parameter SCRAMBLE checklist, v45 Feral Formula startup repair and v44 menu order. Preserve saved machine IDs, all prior features and private comparisons. Subsequent label refinements belong in a separate private build.

## AveyCole main2.21 promotion and private delivery (2026-10-22)

AveyCole tested the exact shared-filter v48 and reports “this worked, push to main”. Promote SHA256 `ec6717091c7e016ead30d5d5b3e1be7a0d72c936b5c833913594830373fd92d6`, with parameter retention and separate per-track Wizard/synth dial banks during the current MACHINES session. Stock-style menu lifetime was explicitly accepted; do not claim per-engine preset banks across menu sessions. Main includes all prior v46 features. Future private tests need both direct `.syx` files; the user no longer needs private flasher pages.

## AveyCole main2.22 promotion (2026-10-22)

AveyCole explicitly approved the shared-filter v50 at `output/firmware/validation/all-features-polivoks-cpu-trim-test-v50.syx` with “push this to main”. SHA256 `78a0a39695cc7bf9824cd71f4f2ac0874f327046240b94028daa51db50a4a39f`. Promote exactly this image: Shadow19 after TINY18 before MIDI17, original pulsar/noise design inspired by Opal Dust by Fors, and six icons for Shadow/WAVE/TINY/MIDIOut/ACID/Feral. Preserve existing IDs, Wizard bank isolation and all prior features. Reports of icons looking great in v49 are UI feedback, not a claimed exhaustive hardware audio test. Subsequent remaining-icon and independent crusher-send requests are private follow-ups, never folded into these approved bytes.

## AveyCole main2.23 promotion (2026-10-22)

AveyCole reports that all-features v53 worked and explicitly requests pushing it to main. Promote the exact shared-filter image, SHA256 `9a3384e76134f0ed7e9fbcc700220641a9d3ee46f855ef0ae0987a8117a17d77`, with v51 remaining themed icons and separate per-track crusher sends in Both1/Both2. FUNC+DelaySend adjusts crusher0..127; plain DelaySend stays native. Both1 leaves direct clean, Both2 adds independent direct wet/dry. Crusher feeds native delay. The v52 missing selected-track-object exception is fixed. Sends are global per track, stopped-only saved, default0, without p-lock/LFO destinations. Preserve the exact approved bytes and all previous releases.

## AveyCole main2.24 promotion (2026-10-23)

AveyCole reports “Everything works great” and requests publishing the exact shared-filter v55 as main’s served .syx. SHA256 `ed59a947965aff8fc15369c61624baf1a564c6e07e42d837b6277ca6e1405c57`; MAIN SHA256 `8701f142868f862a916037039bcab824bde002b96cab9f511b235b20eb5f8c7a`. Includes all v54 work, deferred boxed FX menus, chorus/reverb and Vinyl combinations, mixed controls, physical-only diagnostics, slower machine scrolling and retrig-latched temp shortcuts. Publish exactly these bytes through the existing fixed-main delivery path. The guide must explicitly say Reverb Tone is set in standard REVERB mode with FUNC+REVERB SIZE and carried into combined modes. The later request for SETTINGS+SIZE/TIME shortcuts belongs in private v56; user explicitly chose “Publish v55 now; test v56 separately”.

## AveyCole main2.25 promotion (2026-10-23)

AveyCole supplied the exact shared-filter `all-features-polivoks-cpu-trim-test-v57.syx` and stated it should be the .syx the main flasher serves. SHA256 `35370f22a4d6423bb3c66f290da8e45c0fd02fe5083942fe02980bc765cce045`; MAIN SHA256 `3f9dd0211da1321e4f504bc6f0bc87306f740a4d8e1318aaf33771c8daed8b2b`. Publish exactly these bytes through the existing fixed-main delivery path. Replaces the v55 image of main2.24; the guide adds the SETTINGS + Size/Time Tone/Feedback shortcuts in combined FX modes and the opaque FX popups. No hardware result is recorded here: none was reported with the promotion.


## AveyCole Vinyl publication (2026-10-23)

AveyCole explicitly requested the revised Vinyl crackle be finished and pushed to main, then reported "Crackle sounds better" while testing the cumulative v59. Publish the identical Vinyl DSP in shared-filter v58 only, SHA256 `c155ee9df5d4b8450f2faa876ccaa51ea5addc15b60e2fce415b92d0844a6752`, through the existing fixed-main image path as2.26. This is not a claim that the exact v58 image received a complete hardware test. Ping Pong/Shimmer and their v60 repair remain private until separately approved. Preserve Claude's2.25 work and all existing main features. Only shared-filter private builds are requested at present.

## AveyCole main2.27 promotion (2026-10-23)

AveyCole reports "64 seemed to work for me" and requests publication with updated shortcuts and a printable overview. Promote exact shared-filter v64 SHA256 `77f533e3d6856ab204ff121ddd9c2562d90b378cfa59d24e7befa592ccf6357a` (MAIN `2192a9ab2deba19d3362622f1f9dca5b545dda4c690b394096e737c2bf55c2a6`). Delay IDs5/6/7 are Ping Pong/Shimmer1/Shimmer2. Shimmer1 is the filtered/aligned full-octave return ; Shimmer2 preserves v62 mixed/diffused DSP. Keep prior private files. Publish only the established fixed-main image with bilingual guides/PDF. No further firmware edits are included in this approval.

## AveyCole main2.28 promotion (2026-10-23)

AveyCole tested v66 on Tone (direct and marked-step SCRAMBLE) and reports "Okay, that worked, publish 66". Publish the exact shared-filter v66 SHA256 `f94a8f52b1832099e30df16fd48361eb2934a4fe08c7e2b56f864cae5132441a` (MAIN `e1cdefe371cf938d4d4aa2c84080a50dafc3514cccc3a476490f2d396be11a8e`). Decay is slot18/CC80; use its native common descriptor for inverse validation. v65 mistakenly targeted Punch slot15/CC66 and must not be promoted. Preserve all v64 effects and prior private files. Update bilingual guides/PDF and only the established fixed-main image.


## AveyCole main 2.29 promotion (2026-10-23)

AveyCole requests "push v70" after praising PS1 reverb in v69. Publish exact shared-filter v70, SHA256 `21d21e29611a02f426c7e6f61066c771d8ed6e6c43b2695994f9b8961ed9d8b0`, MAIN `65d75a6fb846519ff3a01f9abd8c39a1a6145a14f9d88497684744467ed2c04c`. v70 builds on v66, adds PS1 reverb and excludes CLOUD. Preserve private CLOUD comparisons and the unresolved Density scrolling report. PS1 DSP is identical in v69/v70; do not claim a separate full-composition v70 hardware test. Update EN/FR shortcuts and PDF. Only the established tracked fixed-main .syx delivery path is authorized.

## AveyCole main 2.30 promotion (2026-10-23)

AveyCole reports “that worked, push v85 with updated controls and such”. Publish exact shared-filter v85, SHA256 `96f97b9fb98056978b3b30c039e43db28183cc6324d076b50f84e3d790de194a`, MAIN `7912d7c2912da1bd42ef47a607465f32267d34e0ea77dd53a951fb343247c938`, through the existing tracked fixed-main image only. Includes SPEAK with calibrated level and softened consonants, fresh SCRAMBLE deletion, immediate native Reverb formatting, cumulative PS1/filter CPU work and the FUNC tap/hold DX shortcut. Both Shimmers and all combined FX modes are removed. Preserve all private comparisons. Update EN/FR controls and printable PDF. The subsequent adult SPEAK word-bank request is private only and must never enter this public release.

## AveyCole main 2.31 promotion (2026-10-23)

Explicit request: “perfect put the non swear version on main”, clarified “of v87”. Publish exact regular shared-filter v87 SHA256 `97d4c95a3ab7c7e5b8e5a8bb9eb10d6d004bb03a52a3937d2d6ff03ba71570bf`, MAIN `4f2800f2d7218118788a4fbd284b5486487836253649215e9fe047eb845f5b61`. The regular 128-word bank stays intact. Includes softer noisy consonants and SPEAK idle-counter handling during unfinished words; true pressure/stolen/fading rules remain. No adult bank, DUB or ROOM is authorized for this public release. Update EN/FR controls and PDF. Private files remain separate.

## AveyCole main 2.32 promotion (2026-10-23)

AveyCole explicitly requests “okay, push v90 to main”. Publish exact regular shared-filter v90 SHA256 `218aebccdd0b5f13896f80310a041f8eb95c90e3a98ab62b1985c9083518d008`, MAIN `413659a209f2c8c31e7080394c81c8a5e562c4bd13c5093ded00044a90f19821`, via the established fixed-main image. Includes ROOM, distinct filtered stereo DUB and calibrated/brighter SPEAK. Update EN/FR controls and PDF. Adult v90 stays private; no adult lexicon may enter the public checkout. DUCK is a subsequent private v90-based test, never included in this approved image.

## AveyCole main 2.33 promotion (2026-10-23)

AveyCole reports “that worked, push 94 and give me the adult version”. Publish exact regular shared-filter v94 SHA256 `f0663f703bb6d85e85dfcc2fa5c99ae1785ab696bd9fe750e532759d1878e46d`, MAIN `a7a59a46646ee7e3d9f26c5d7197721b07d207e2c5fca853b99c45019ff432d8`. Includes DUCK, RING MOD, PHASER and live-trigger encoder safeguards. Update controls/PDF. Adult v94 remains private. Later experimental revisions and requested GATED reverb/menu reorder are separate tests, not included in this approved image.

## AveyCole main 2.34 promotion (2026-10-24)

AveyCole supplied the exact shared-filter `all-features-polivoks-cpu-trim-test-v101.syx` and asked that it be the .syx the main flasher serves, with the matching 2.34 shortcut guide PDF. SHA256 `bb566c59d353fb11ac2f7edce74723d7fba5346e2934bb8f5ea4210cee405e4c`, MAIN `e59ad39ea940fb05dfd87145bfa6e42fffc79e8405cbaead04dabcd07263b920`. Publish exactly these bytes through the existing tracked fixed-main image only. Replaces the v94 image of main 2.33; per the supplied guide it adds GATED and HALL reverbs and the new reverb-slot menu order, and raises the PS1 and Vinyl wet returns by 6 dB. No hardware result was reported with the promotion, so none is claimed. Adult SPEAK banks stay private.


## AveyCole main2.35 promotion (2026-10-24)

User: “105 worked” then “Publish 105 retro build”. Exact regular-vocabulary shared-filter v105retro SHA256 `ef01ba93a63f7dda8d161d6aa7f19a60114f7b190e3d6687a5b15df42f149bc8`, MAIN `56ed414d68925c2f2f6f0d2807f120fed4e57a6e788a08afbbb83cbcd87b670a`. RETROSYN22 before MIDI Out17; 23 machines. Bank import page joins existing WAV converter side by side. Preserve the user-written flasher blurb verbatim. No adult vocabulary or ACID/SY BITS106 changes.


## AveyCole main2.36 promotion (2026-10-24)

User: “111 worked, push that to main”. Publish exact regular shared-filter111 SHA256 `fa66d0aa955ed68461ae5be5fbbd87c4a89fd3a53ff2cd693ccf48bd2589951a`, MAIN `a31131af8c4b93a2cab3f471612ddac84e08e2c2dbd8327cae480b8e81f00744`. Includes ACID filter-only Decay and velocity Accent, fine SY BITS detune/live compact signed decimal, Elder+6dB. RETROSYN preserved before MIDI Out. Adult remains private. Preserve the user flasher blurb verbatim.


## AveyCole supplied blurb update (2026-10-24)

After main111, AveyCole supplied a full replacement English blurb and requested the existing layout. Preserve its spelling/punctuation, including Tiny,: and varie. Keep the eight feature bullets, new WAV/DX7 importer paragraph, READ callout, donation link and sign-off. French equivalent retained. New fixed-features block SHA256 `00da19e1c4ba5c0cd9de3190e39106aa70576916f5b0c9581671af684c4cd3a7`. Future releases preserve this new supplied text unless explicitly changed. Firmware remains exact111.


## AveyCole main2.37 promotion (2026-10-24)

User: "115 worked, go ahead and push that." Exact regular shared-filter v115 SHA256 `9305c3ae7727fde21bd63fec305a7cdb89ab0bf6f77332bf372f92848fdb476a`, MAIN `6bbae768295095d82d106606af79b24f76ff868f34e35b2fc5c85b7128bfaff4`. Includes WAVE boot starter, direct-entry fallback and BACK parent navigation, safe custom-file buffers. Hardware report accepted; publish exact bytes only. Adult stays private. Preserve the supplied flasher blurb byte for byte.


## AveyCole main 2.38 promotion (2026-10-24)

User: "121 worked push to main". Publish the exact regular shared-filter v121 SHA256 `8c2ed40ff1687dfa9ecaace5234b902133db1df45bb266d94f0ecfa0b5d4c834`, MAIN `cb9b7745abb1b349ed42ea0183a1c1713927d7ff9ab858e6850df7726ba3f296`. Pattern FX types/settings/sends, blank defaults, actual queued activation and WAVE +6 dB. Includes the v120 startup repair confirmed by the user before pattern work. Do not incorporate later lab refinements. Adult stays private. User additionally requests resource links on the combined importer page. Preserve the supplied flasher blurb byte for byte: "Don't edit the blurb."


## AveyCole main2.39 promotion (2026-10-24)

User: "122 worked, push that to main." Publish exact regular shared-filter122 SHA256 `7d2d564cc1cf34c585ec2bad3134531197d97d2136ef57cab73ca53d31172db0`, MAIN `196f12214a3d382cfc037e5d933e17c4ffdb74171b177cf18453445a1e889a07`. Sidechain routing and controls plus Scramble masks per pattern, readable stacked Side/Chain menu. Adult stays private; preserve supplied blurb byte for byte. F2 pattern records read old FXS1;121 cannot restore new custom FX records.


## AveyCole main2.40 promotion (2026-10-24)

User: "Perfect, push v127 to main". Exact regular shared-filter127 SHA `cb19d4d68c2a341bf92a2d26c73c1f042d7f7ff335ae3fcf06d0a615439b72bb`, MAIN `04905a7ad1f75d5fd3b0a6c14e7c7e0c9c220a45c88ecd99b96fa9ec671da6e2`. Tap opens Mod Setup, hold Scramble once; held-step tap marks only. S.Chn >, Trk. N, Dpt/Atk/Hld/Rel aligned in selector. Elder original, Shadow+12dB. Adult remains private; supplied blurb unchanged.


## AveyCole main2.41 promotion (2026-10-24)

User: "It worked, go ahead and push v128". Exact regular128 SHA `a3df9c7ca6e6f566e6747dab872223189e236a18567ba0163523b8b612a5ad0d`, MAIN `c7fcbbae50ac86ed190cb3d50eea4755137cc546dcc603e26a3f66d2b747b8e2`. S.Chn Mute On/Off per source and pattern, defaultOff. Adult remains private and blurb byte-identical. FXS1/F2 read; F3 emitted only with Mute On, older firmware cannot restore those added settings.


## AveyCole main2.42 promotion (2026-10-24)

User: "Go ahead and push that" after receiving129. Publish exact regular129 SHA `71697a12c13b38e9ec30efde7f91c378390b6a909b950389e5e8b534bc9cd55b`, MAIN `4ab1f623db445f10d58d131b8178ea40c9afb049e46af3e5e5da3e75586d38fe`. UI-only Mod Setup -> MACHINES handoff; audio and saved settings exact128. Adult remains private and supplied blurb byte-identical. No new shortcuts; existing2.41 guide still applies.


## AveyCole main2.43 promotion (2026-10-25)

User: "130 worked, push to main". Publish exact regular130 SHA `881099ad7b7d8505f1850f13ffb17eb5688ffa5e69e0038d9cf1e2ae5be22fb3`, MAIN `176faf7748d706a15f65652383a7e5cc495817ff78bfad830dd6de71f288fe18`. Rev./Del. Sidechain return targets per source/pattern; F4 keeps the same54reserved bytes and CRC24, reads FXS1/F2/F3. Adult private, supplied blurb identical.


## AveyCole main2.44 promotion (2026-10-25)

User: "Go ahead and push v141". Promote exact standard shared-filter141 SHA `d6b621c9b4aee2f38a26348fa9a3ea37c42f7caff334bcfad4ff1c510a34bb76`, MAIN `0e2b8f2c14fa836532a1a7eb5f9907d29f36e36f0afa0ebe18a071f57ec40bd9`. Popup fix, full MIDI/audio word restoration before late cleanup, PUNCH engine and PUNCH-controlled Shadow distortion. Adult stays private; supplied blurb unchanged. No PUNCH/TINY decay changes.


## AveyCole main2.45 promotion (2026-10-25)

User: "Go ahead and push to main" for the supplied `all-features-polivoks-cpu-trim-test-v142.syx`. Publish exact standard shared-filter v142 SHA `1eca04fe97951920d2b57c915c0447a5da2739f6008d754e3273be46e364962a`, MAIN `12ec632b7596b23d7afd575eeeeff32a5eeaef3ea8d245b18bee94e1d9a99a68`, through the established fixed-main image only. Adds quantized mute/solo: Mod Setup (SETTINGS + TRACK) > QntM, On/Off and the time division, Off by default. No hardware result was reported with the promotion, so none is claimed. Adult stays private. The flasher blurb was changed at AveyCole's explicit request on 2026-10-25 (Sidechain bullet added after SCRAMBLE; "varie" corrected to "variate"); its fixed-features block SHA256 is now `b3486b46a278b7d5561c3edd549f4adf299d358012b2631a0a6ab353232e2205` and is the text to preserve byte for byte from here on, replacing the earlier `00da19e1…` pin.


## AveyCole main2.46 promotion (2026-10-25)

User: "push to main, consistently 75 99 00 during same pattern". Promote exact standard145 SHA `f7f9e92d902f92c6f56c5baa964216c14cb35175271db160d8d6557e0c52535d`, MAIN `7cf4f9f66587dc1866f679dd76c4d40d3403efa943806e3f4ac5abc1da730549`. PUNCH optimizations plus MACRO parallel filter and faster HALL, QntM retained. Hardware report is A75 P99 O0 N0 for this user pattern only. Guides remain byte-identical at the user's request; no control or sound changes. Adult stays private; protected blurb hash `b3486b46a278b7d5561c3edd549f4adf299d358012b2631a0a6ab353232e2205` preserved. Continue optimization research separately from these approved bytes.


## AveyCole main2.47 promotion (2026-10-25)

User authorizes publishing148 and continuing optimization only in test. Exact standard148 SHA `442c1720818c7c5e6798cadbebbd29e37288eae09d9a80c3ce3b7b743f2397d4`, MAIN `3a225d0ecd7e08cc14f35c7c4cf0b5a02086bd06a1aa35261d289fbb8cec8e72`. DUB stereo on base146;147 optimizations excluded after higher hardware P report. No new hardware CPU result claimed. Adult private. Update DUB guide text; protected blurb unchanged. DX7 importer reliability investigation remains separate.


## AveyCole main2.48 promotion (2026-10-25)

User: "but goahead and push159 as well". Publish exact standard159 SHA `fb0d1b480d21910e6c0c63f300b6383f802a1cbbf490eb7e55f6932951a6047f`, MAIN `e743c142835072c4050c60d42d9b86f7c89e3fb209a416ff6d7b1e97416a9ec4` through the existing fixed-main path. No new hardware result claimed. Adult stays private, protected blurb unchanged. Includes waveform/footer volume, Groove/Strum, Global/Track menus, popup labels,151 bank fix and155 optimizations. Subsequent VA/LXR work stays private.


## AveyCole main 2.49 promotion (2026-10-26)

User supplied `Supermodel_v163_Filter_LFO_Polarity.syx` (four new filter modes, LFO Polarity options): "Make sure this .syx is served by my main flasher." Publish exact standard v163 SHA `952b5b70dc095e3e68a68df0562d08fa300f4eca48775439d4a776f04e7d222f`, MAIN `4ac6a3c4cb0712e2a2bf80d17a8bc1b5c36326df02286c6860048eb7c133b410`, through the established fixed-main image only. Replaces v159 of main 2.48. No hardware result reported, none claimed. Adult stays private; protected blurb hash `b3486b46a278b7d5561c3edd549f4adf299d358012b2631a0a6ab353232e2205` unchanged. Shortcut guide/PDF not yet updated for the new filter modes and LFO Polarity.


## AveyCole main2.50 promotion (2026-10-26)

User: "okay push that" for v164 label fix. Exact SHA `b5afb6e34b0fcaa0f1b32536781ce132a7228c965f7132a85e203d181d6326a0`, MAIN `47fe78cc738784f0719cc48d7358518ac4d0b5683b57f7d3cd28450077e1b7ce`. Only native Resonance font selection changes; audio/runtime preserved. Mod Setup popup overlap remains reported and is a separate repair. BRAIDS scale lock follows that repair. Protected blurb and2.49 controls guides remain unchanged.


## AveyCole main2.51 promotion (2026-10-26)

User: "that worked. Let's push that to main and work on copy persistence" for exact v175. Promote SHA `99d392585a03a0f94cab0eb76fd1c16def0cc690230e909e821a09e01fa69bee`, MAIN `a04f16bf2037166cbab9f7d01d31bb04573bbf5b48c46432e96e69a04ae0e1f5`. Includes selectable1/2/3/4 LFOs, square/depth fixes, Off/ORGN/BRDS, nineteen scales, compact LFO memory, startup guards and WAVE/GATED separation. Hardware success reported; no new CPU result claimed. Sound-copy polarity remains a separate private follow-up. Keep protected fixed-features blurb unchanged.


## AveyCole main2.52 promotion (2026-10-26)

User supplied `Supermodel_v186_All_LFO_Copy_ESTUS_Optimized.syx` ("Make sure this is the .syx served by main"; Codex ran out of usage mid-push). Publish exact standard v186 SHA `5ec78631f29a4ffcaedac2d940eb6c7d87fa28de1b231e974c8e27f90704c4cb`, MAIN `6be17c5d328fc87ffed9b585df853410ef0976a18ffee97d9f958a91983518d3`, through the established fixed-main image only. Replaces v175 of main 2.51. No hardware result reported, none claimed. The release note says only "Estus Refilled." at AveyCole's request. Guides/PDF unchanged; protected blurb hash `b3486b46a278b7d5561c3edd549f4adf299d358012b2631a0a6ab353232e2205` unchanged. Adult stays private.


## AveyCole main2.53 promotion (2026-10-27)

User confirmed the final v189 fixes and explicitly requested "Perfect, push it." This authorizes updating and pushing the existing tracked fixed-main firmware path docs/flasher/all-features-usb-2ch-default.syx with exact v189 SHA `6a729fbf198b50768ec1bfade96d6627ab11f08cea210f452586927d207a3282`, overriding the generic no-firmware-commit rule for this established release file only. Main2.52 release notes and protected flasher description remain unchanged. LFO clear and ESTUS live controls confirmed earlier; final destination result approved. No hardware CPU measurement claimed. Separate optional-machine flasher remains private work.

## Main2.53 delivery repair (2026-10-27)

User reports a main-flasher checksum mismatch and requests the fix. Authorizes publishing the same approved v189 bytes under `docs/flasher/Supermodel_2.53_6a729fbf198b.syx` to prevent shared-path cache collisions, retaining the established legacy path. Both files must have SHA `6a729fbf198b50768ec1bfade96d6627ab11f08cea210f452586927d207a3282`; every download source remains checksum and SysEx verified. Firmware and release version unchanged.

## AveyCole main2.54 promotion (2026-10-27)

User: "Push to main, make sure the file size thing doesn't happen again." Authorizes exact v194 SHA `da908d5ff722164d1fb8efaf38f508a1197a1a23b73fe27bd6e2c72d0ef4d6e1`, MAIN `bf71efa56d4780d67b6fd538129d40f0f9968148207f5fee9f786aed82cb61f4`, at the established legacy path and immutable `docs/flasher/Supermodel_2.54_da908d5ff722.syx`. Full v191 base with Page Len1–16, explicitly dark inactive trigs and Estus advanced native locks; SPEAK and Feral retained. Model:Samples exact-image preparation, native bootstrap and flash-capacity checks are release gates. No hardware result inferred from publication approval. Private no-SPEAK/no-Feral variant excluded. Protected flasher blurb unchanged.

## AveyCole main2.55 promotion (2026-10-27)

User tested v199 and approved "Perfect, push." Publish exact SHA `c37e8a1a97a6849ff094a095caac5de54b39d9cc03ca0e88396b629d17bba05b`, MAIN `4ad9b5bcc8cddd00db1a55bc52e0a46a175abcce89c3ee3f06a7a097530e3f85`, immutable `docs/flasher/Supermodel_2.55_c37e8a1a97a6.syx` and established legacy path. Includes sustained Warp timer fix and GRID RECORD hidden steps; user confirms both. Preserve all machines and prior features. TINY sustain/PUNCH remains private and excluded. Protected flasher blurb unchanged. Native Samples layout and flash capacity remain release gates.

## AveyCole main2.56 Full/Lite promotion (2026-10-27)

User: "Seems much more responsive now. and dx works. Let's push211 as lite and the filter clear full version", followed by "then work on machine-optional". Publish Full208 SHA `5efc8abf7f4b6113d8d084897e3a17546be0107d74ec1d603b122bb0bd0c3980` and Lite211 SHA `df9b8d2241e28df96f81d51b68fba171ac6bd8d09daf70233deb2b7b4d04cd3f` at `docs/flasher/Supermodel_2.56_5efc8abf7f4b.syx`, `docs/flasher/Supermodel_Lite_2.56_df9b8d2241e2.syx` and the established legacy Full alias. Full208 is verified204 plus the requested new/cleared-sound LOW/open defaults and filter copy/Undo support. Lite211 retains the stock-six startup repair and correct native state-connect +20 offset, plus deferred preference writes during input. Hardware feedback confirms filter clear and Lite211 DATA/DX; no exhaustive hardware feature claim. This explicit release authorization overrides the generic firmware-commit/PR rules for these exact files through the established fixed-image path. Keep the protected blurb byte-identical. Future builds display the flasher release number. Future Full/Lite/optional builds retain LOW/open127/resonance0 for new and cleared sounds only; never reset saved filters at boot. Machine Optional is separate subsequent work.

## AveyCole blurb update (2026-10-27)

User explicitly adds two bullets: "4 Filter Types: Choose between Low Pass, High Pass, Bandpass, and Low/High Pass by pressing Settings + Machines and turning Sweep." and "Per-Page Length Options/Active Step Warp". Matching French text is included. These exact insertions are authorized; all other protected blurb bytes remain unchanged. New protected block SHA256 `b6ab6a510ac726ddad5f5f53afea3e915ffa14c5813bc6ab8c5712b23e00fa7d` supersedes the earlier b3486b46 pin for future work. Firmware images and release2.56 remain unchanged. Machine Optional remains the primary subsequent task.

## AveyCole Full215 promotion and Lite test gate (2026-10-27)

User requests "Okay, push215 as main full build" and "include those fixes in the lite build, make sure to let me test first". Publish exact Full215 SHA `c00942b054d0478e117ee889ee80761e91c77b30d3a0465122d5dec000f912e6`, MAIN `a82d10eaccea90141951015a1e4b38ad732fdd2b32b17a4b45e37d3bfbad137e`, immutable `Supermodel_2.56_c00942b054d0.syx` and the established Full alias. This explicitly authorizes these firmware files through the existing delivery path. Keep release/title2.56 to deliver the exact approved bytes. Public Lite remains exact211 until the user approves a separate Lite test. Do not infer exhaustive hardware testing from publication approval.

The Full edition blurb is exactly "All added machines and quality of life features." with matching French. Do not re-add implementation history, filter defaults or other technical details there. The separate protected fixed-features block keeps SHA `b6ab6a510ac726ddad5f5f53afea3e915ffa14c5813bc6ab8c5712b23e00fa7d` unchanged.


## Lite216 publication (2026-10-27)

User explicitly requests making216 the live Lite version. Publish exact approved SHA `0a6e67c552c3a799cb4090357ebe8018503efdebaae9ad3aaa3e68b5f3bd4e0e` under its immutable filename, preserving Full215 and release/title2.56. Lite216 carries full LFO2 pattern storage, playable LFO menus and clipboard164 on the stock-six Lite211 base. Publication approval does not imply exhaustive hardware verification. Protected fixed-features block unchanged. Machine Optional work follows.


## Machine Optional publication (2026-10-27)

User explicitly requests linking the separate Machine Optional flasher from main, with a hardware-testing/own-risk warning and brief machine descriptions. Authorizes docs/flasher-optional/ and one link outside the protected main blurb. Full215 and Lite216 firmware bytes, checksums, release and main behavior stay unchanged. No new firmware images are committed. The optional edition is experimental: fixed runtime layout, excluded DSP dormant, none exact Lite216 and all exact Full215; mixed selections are not all hardware-tested. Per-track FX investigation remains separate private work.


## AveyCole Full/Lite playability promotion (2026-10-28)

User: "Push these to main and keep the machine optional flasher the same."
Publish the exact delivered Full SHA `fec67ab4282a68b3c5538e76c87fba0c3d16e5cff5f6c15b5bb54202d952cb58`
and Lite SHA `b5220ffdcf541a9109c389de4d6a9a38eba4539f173ee2ba960603221926f563`
through the established checksum-pinned Full/Lite loader and legacy Full alias.
This explicitly authorizes these fixed delivery images and direct main push;
it supersedes the generic firmware-commit and draft-PR requirements here.
Keep release/startup title 2.56 to preserve the approved bytes. Legacy, Vinyl
and ChordKeys are removed; sound machines gain distinct Punch transients.
Keep the protected fixed-features blurb byte-identical and put the current
build notice outside it. Every docs/flasher-optional file and its shared runtime
dependencies must remain unchanged. Its recipe still targets Full215/Lite216.
No hardware result is inferred: the held-step Punch/Gate issue remains
unreproduced and Chord + Control All filter clicking remains unverified.


## Main reference cleanup (2026-10-28)

User explicitly requests removing all main-site references to the retired chord
keyboard, crackle effect and six-operator machine, and retaining bank import only
in Machine Optional. This authorizes editing the protected description; its new
SHA256 is `0427d0a2b828f098b818ebce1507e9ad5076f21e24bd8fcb078602c11fbd00a4`. Firmware bytes remain exact. Optional converter and old
guide/release dependencies are isolated before cleaning shared main pages.

## Release numbers and Optional updates (2026-10-29)

The user requires the startup-screen release number and flasher release number
to advance together on every release push. Do not reuse 2.56 for new firmware.
Verify the compiled title against its metadata and verify each delivered edition
matches the flasher release before pushing. Internal asset-staging commits belong
to the same release and are pushed together with its final loader update.

The user authorizes updating Machine Optional with per-track FX and subsequent
fixes and explicitly requests keeping its extra Legacy/ChordKeys choices.
Preserve all nineteen optional machine choices and Optional's extra features;
do not inherit the main edition's feature removals. Mark new validation accurately
and do not carry old hardware or exhaustive-combination results onto new binaries.

## Release 2.58 (2026-10-29)

The user explicitly requests "push to main" for the deferred new-sound LOW reset, ACID added-transient removal and All Sound Off FX tail reset. Publish the verified 2.58 Full/Lite and Optional bases through the existing fixed-image paths; startup titles and both flashers must match 2.58. Main Full SHA dec88b00faca94e7ee58c808a05c1624611b9403b29cbaa745a804bfeb012e32; Lite a46b2fe88f1c4ad08cfbae96882725a2821891508231c7f7730672cdecd68946; Optional Full 46021f2591e2f05b6d1492f1876c2d07addb84a6f1ded55275d6be5e4511ef22; Optional Lite 3f8ea64121df94b17b222f0b61593b83c389b0bd2fc87aaa71eb0113aef71fb2. This authorizes these exact firmware assets and direct main release. Preserve Optional extras and the protected blurb. Validation is native emulation/browser/signature testing, not hardware confirmation. Proofs: docs/flasher/release258-validation.json and docs/flasher-optional/validation258.json.

## Global ACID release and Lite parity (2026-10-29)

The user confirms the ACID A/F/AF prototype works, requests moving it to Global and saving one choice globally, then explicitly authorizes "push that". Publish the verified 2.60 global-selector Full/Optional images and title-only updated Lite/Optional Lite through the established fixed-image paths. This authorizes the exact new release assets and direct main push. Main Full SHA9faeca94dc5ef71905511aa8855ab555e475d827555dbe343e25a2af7800aea4; Optional Full SHA2a61e86e0cd4f9802cece1057d2f3806fe01490fea50b0a354d51885afbb462c. Global revision hardware confirmation is pending. The user requires all non-machine Full features in Lite; ACID is explicitly excluded as an added-machine option. Keep parity checks and Optional extras. Preserve the protected blurb and the single guide-download link.

## POTS release2.61 (2026-10-29)

AveyCole explicitly requests "Go ahead and push that and add it to the list of delays in all builds". This authorizes direct main release of the verified2.61 POTS firmware assets through the established fixed-image paths: Full2eb4b07f45ee24b7d9f198b09094db358b1d995fa8111b80daf6e114f9fac5c6; Lite7f000ba151c24b77e40d92fa8a640910e375ffd4eee2064f677eeb7697012c51; Optional Fullff8eddcd16d6dcc30111d2064a905eb7c142818d52f27d653696636fefe607c0; Optional Lite6cde04f1ab8bb202799c3e96b7170fac47cc90707020ff356585eba80773d692. Preserve Optional extras, protected blurb, shared Full/Lite features and single guide-download link. Startup and both flashers display2.61. POTS is emulation-verified, not yet hardware-confirmed.
