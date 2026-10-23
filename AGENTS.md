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
