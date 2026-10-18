# AGENTS.md — Modded Cycles

Guidance for coding agents working on this repository. This file holds what is always true; the procedures live
in **skills** (`.agents/skills/`, loaded on demand) and the roles in **pi agents** (`.pi/agents/`). Read the skill
that matches your task before you start: pi lists them automatically; other harnesses (Claude Code, Codex) should
open the `SKILL.md` named in the table below.

## What this project is

Firmware mods for the **Elektron Model:Cycles, OS 1.13** (ColdFire MCF54415, big-endian m68k). A mod is a *tweak*: a
table of byte writes (`old` → `new`) applied to section 3 (the MAIN OS) of the user's **own** official `.syx`, plus,
for some mods, code compiled or assembled into free space. Users pick mods in a web flasher
(`docs/flasher/`, served by GitHub Pages at <https://18nelli18.github.io/Modded-Cycles/>), which builds the firmware in
the browser and sends it over USB. A pure-Python toolchain (`tools/build.py`) does the same build on the command line.

**Always the Model:Cycles OS, whatever the machine** (decision of 10/10/2026, notes/57). The Mods tab also flashes a
Model:Samples, but what it installs is still the Model:Cycles OS with the mods (sampling comes from Model-TG): the machine
picker only changes the packing (official Model:Samples container and signature, the 32-byte key change of notes/41,
transport `0x0F` or `0x11`; `tools/mods_for_samples.py`, `MCBuilder.modsForSamples`). Build, prove and reference a mod
once, on the Model:Cycles OS; never add a mod built on the Samples OS.

Owner: Maxime (GitHub `18nelli18`). He tests every firmware change on his own Model:Cycles.

## Hard rules

1. **Never commit an Elektron firmware image**, original or modified, or anything extracted from one (no `.syx`,
   `.zip`, extracted sections, dumps, copied routines). `.gitignore` covers `firmware/`, `*.syx`, `*.zip`, `build/`,
   `vendor/`, `*.wav`. A tweak carries only its own writes and the short `old` bytes that check the user's file; code
   taken from the Syntakt OS is extracted **at build time** from the user's file (recipes and relocation tables only,
   see notes/17). Never write that a file holds "no Elektron bytes" when it carries `old` bytes.
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
7. **Respect the licenses and credit authors.** The project is MIT (`LICENSE`); the scope and every third-party
   license are in `THIRD-PARTY-NOTICES.md`: drumkilla's tweaks and `tools/mtlib/` (MIT), elektron-firmware-tool by
   Marcel Bierling (MIT), Model-TG by TinyGregAudio (MIT, `LICENSE-Model-TG`), ms-multi-output by scottmetoyer (MIT,
   `LICENSE-ms-multi-output`), Braids by Émilie Gillet (MIT, `LICENSE-Braids`, compiled unchanged for MACRO), Open303
   by Robin Schmidt (MIT, `LICENSE-Open303`, the model rewritten for ACID), and `tools/webxfer_check.py`, transcribed
   from Elektroid (GPL-3.0-or-later). Never transcribe or closely paraphrase code whose license does not allow it into
   the repo (GPL code into MIT files, code with no license); check an upstream's license before porting from it, and
   keep its notice next to the copy. Record the origin and license of every tweak in
   `tweaks/model-cycles_OS1.13/PROVENANCE.md` (and outside code in `THIRD-PARTY-NOTICES.md`), set `credit` on its
   flasher card, and serve its MIT text with the page (`license` in `FEATURES`). Outside contributions are merged
   only under the terms of `CONTRIBUTING.md`: work sent privately needs its author's written OK.
8. **Never stage blindly.** Commit explicit paths (`git add <files>`), never `git add -A` / `git add .`: the working
   tree may hold Maxime's untracked work (e.g. `Docs Optimisations/`) and local firmware files.

## Languages

- **Talk to Maxime in French.**
- **French**: technical notes (`notes/`), `BUILD.md`, `FLASH.md`, `dossier-technique.md`, `PROVENANCE.md`, tweak
  `name`/`description`, comments and docstrings in `tools/`.
- **English**: `README.md`, commit messages, PR titles and bodies, the code of the web pages, `AGENTS.md`, skills and
  agent definitions (`.agents/`, `.pi/`).
- **Both, side by side**: everything users see on the site (flasher cards, guide, release notes, home page), as
  `en`/`fr` pairs or `data-l="en"`/`data-l="fr"` spans. Never add one language without the other.
- User-facing text speaks to musicians: what the mod does on the machine, which buttons to press, its limits. No
  addresses or jargon there; those belong in the notes.

## Skills (`.agents/skills/<name>/SKILL.md`)

| Skill | Load it when you… |
|---|---|
| `modded-cycles-workflow` | start or plan a mod or a fix; need the full checklist and which files a change touches |
| `mainos-reverse-engineering` | need an OS address, routine, structure or hook point; includes `scripts/mainos.py` and the OS map |
| `coldfire-patching` | write ColdFire code into the OS: hook styles, stub contracts, free space, toolchain, safety rules |
| `tweak-generators` | write or change `tools/gen_*.py` and tweak JSON; pick a tweak number; a `--check` fails |
| `emulation-proofs` | prove a mod in Unicorn, reproduce a bug report, measure CPU cost |
| `flasher-integration` | add or change a card in the web flasher; regenerate `tweaks.js` / `REF_MAINOS` |
| `bilingual-user-docs` | write the guide, release notes, card texts, README row, cache stamp |
| `french-lab-notes` | write or update `notes/`, record a hardware result |
| `repo-validation` | validate before commit/push; includes `scripts/validate.sh` |
| `hardware-test-handoff` | commit, open the draft PR, give Maxime a test plan, flip a mod to tested |
| `licensing-provenance` | use outside code or a community mod; check nothing from Elektron is committed |

Folder `AGENTS.md` files (`tools/`, `tweaks/`, `docs/`, `notes/`) only hold that folder's local invariants and point
to these skills.

## Pi agents (`.pi/agents/`, pi-interactive-subagents) and prompts (`.pi/prompts/`)

| Agent | Model (claude-bridge) | Role |
|---|---|---|
| `mc-planner` | `claude-opus-5-5`, high | interactive design with Maxime (French), writes `.pi/plans/<date>-<slug>/plan.md` |
| `mc-scout` | `claude-sonnet-5-5`, minimal | read-only map of notes, mods, free space, open branches for a request |
| `mc-reverser` | `claude-fable-5-1`, high | reverse-engineers the OS, writes the note's OS and design sections |
| `mc-firmware-dev` | `claude-fable-5-1`, high | ColdFire code, generator, tweak JSON, proof, registers |
| `mc-web-dev` | `claude-sonnet-5-5`, medium | flasher card, guide, release notes, stamp, README |
| `mc-reviewer` | `claude-opus-5-5`, high | rules and firmware-safety review, no edits |
| `mc-validator` | `claude-haiku-4-5`, minimal | runs the validation suite, reports |

Prompts: `/new-mod <request>`, `/fix-mod <id> <report>`, `/investigate <question>`, `/validate [opts]`,
`/review-branch [branch]`, `/mark-tested <id> <date> <report>`. Plans and reviews go in `.pi/plans/` (git-ignored).
Only one agent edits the tree at a time; read-only agents may run in parallel.

## Repository map

```
tweaks/model-cycles_OS1.13/   tweak JSON files (generated), device.json, PROVENANCE.md, REGISTRY.md (generated)
tools/build.py                Python build: applies tweaks, checks caves, repacks and re-signs (mtlib)
tools/gen_*.py                one generator per mod: writes its tweak JSON, --check verifies it is up to date
tools/machines/<mod>/         C and assembly sources compiled into the firmware
tools/emu/                    Unicorn emulation of the OS: test_<mod>.py proofs, mcengine.py, seqrig.py, emac.py, syntakt.py
tools/gen_flasher_tweaks.py   FEATURES list -> docs/flasher/tweaks.js (generated)
tools/check_overlaps.py       no firmware: mods that can be ticked together never write the same bytes (notes/49)
tools/registry.py             no firmware: builds REGISTRY.md, the free space and OS hooks registry (notes/52)
tools/ref_mainos.py           REF_MODS and REF_MAINOS hashes in docs/flasher/app.js
tools/crossflash.py, tools/mods_for_samples.py   one OS in the other machine's container (notes/41, 57)
tools/web*_check.*, webflash_smoke.*   checks of the web flasher against the Python build (node, jsdom)
docs/                         GitHub Pages site: index.html, flasher/, guide/, assets/release.js
notes/                        numbered technical notes (French), index in notes/README.md
.agents/skills/               agent skills (procedures, references, scripts)
.pi/agents/, .pi/prompts/     pi subagent definitions and slash-command prompts
BUILD.md, FLASH.md            command-line build and flashing (French)
.github/                      discord.yml + scripts/discord.mjs: new versions, mod status changes, merged PRs -> Discord
README.md                     English overview for Model:Cycles owners (mod table)
LICENSE, THIRD-PARTY-NOTICES.md, CONTRIBUTING.md
```

Official files (never committed) go in `firmware/`: `model-cycles_OS1.13.syx` (SHA-256 `44fe5862…9800640c`) and
`Syntakt_OS1.42.syx` for the Syntakt engines, downloaded from elektron.se.

## The usual PR, in one breath

Note (`notes/NN-*.md`) → generator + sources → tweak JSON (`experimental`) → Unicorn proof alone and combined →
`check_overlaps.py`, `registry.py`, `PROVENANCE.md`, `BUILD.md` → flasher card, `tweaks.js`, `REF_MAINOS`/`REF_MODS`,
FEAT en+fr → guide, release entry, stamp, README → validation → draft PR with a test plan for Maxime → after his
report, a separate "tested" commit. Details: skill `modded-cycles-workflow`. Reference PRs: tempo-max (`5997b4a`,
`14fb9fa`, `6e592bc`), trig-hold, arp.

## Validation before pushing

```sh
.agents/skills/repo-validation/scripts/validate.sh            # everything that needs no firmware (+ jsdom smoke)
.agents/skills/repo-validation/scripts/validate.sh --gen gen_<mod>.py --proof test_<mod>.py --with <ids>
                                                              # + firmware checks when firmware/ has the official files
```

It runs `gen_flasher_tweaks.py --check`, `check_overlaps.py`, `registry.py --check`, `relocate_6ch.py --check`,
`webbuild_check.sh`, `webflash_check.sh`, `webflash_smoke.sh`, `py_compile`, and with the official files
`ref_mainos.py --check`, the smoke test on real files, the chosen generators' `--check` and proofs. Emulation needs
`pip install unicorn numpy`; code mods need the m68k toolchain (`m68k-linux-gnu-*` or `m68k-elf-*`; some committed
outputs depend on the exact compiler, see the `coldfire-patching` skill). If a check cannot run, say so in the PR
instead of skipping it silently.

## Commits and PRs

- Commit messages in English: a short subject saying what the user gets ("Tempo up to 546 BPM (tempo-max tweak,
  notes/38)"), a body with the why, the bullets of what changed, and how it was proven.
- Merge `main` into a feature branch rather than rebasing shared branches; regenerate `tweaks.js`, `REF_MAINOS`/`REF_MODS`
  and `REGISTRY.md` after a merge instead of resolving their conflicts by hand.
- The PR body says what the user sees before and after, how it was proven, and **what Maxime should test on the
  machine** (which mods ticked, which buttons, what to listen or look for). Template: skill `hardware-test-handoff`.
