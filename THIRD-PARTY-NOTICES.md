# License scope and third-party notices

## What the license covers

The MIT License in [`LICENSE`](LICENSE) applies to the original work of the Modded-Cycles authors and contributors in
this repository: the tools and generators, the mod sources (C and assembly) and the code compiled from them, the tweak
files, the emulation proofs, the web flasher and the website, the guide and the technical notes. A file or folder that
names another license is under that license instead (see the table below).

## What it does not cover

This license grants no rights in:

- **Elektron firmware** (Model:Cycles, Model:Samples and Syntakt OS). No firmware image is included in this repository
  or on the website. You supply your own official file from elektron.se, and a firmware built from it contains
  Elektron's software: it is for your own use on your own machine. Do not redistribute built `.syx` files.
- **The bytes copied from Elektron firmware** that appear in the tweak files and in `docs/flasher/tweaks.js`: the
  `old` bytes used to check your file, relocation values, and short fragments inside patches and payloads. They remain
  Elektron's and are included only so the build can check and patch your own file. The same goes for the short
  excerpts of Elektron code and manuals, and of NXP data sheets, quoted in the notes.
- **Third-party code and data** listed below, which keep their own licenses.
- **Quotations** from the Elektronauts forum and other sources, which belong to their authors and are quoted with
  attribution.
- **Trademarks.** Elektron, Model:Cycles, Model:Samples, Syntakt and Elektron Transfer are trademarks of Elektron Music
  Machines MAV AB. Modded-Cycles is an independent project, not affiliated with or endorsed by Elektron. The name and
  logo "Modded-Cycles" identify this project: a modified version should use another name or say clearly that it is
  unofficial.

Modifying firmware is at your own risk. The software is provided "as is", without warranty, as the license says. No
license settles whether tools that rebuild and re-sign firmware are allowed where you live: that is a separate
question.

## Third-party code in this repository

| Component | Where it is used here | Author | License | License text |
|---|---|---|---|---|
| [elektron-model-tweaks](https://github.com/drumkilla/elektron-model-tweaks) | `tools/mtlib/` (copied unchanged); tweaks `01`–`03` (`02` with a 3-byte change) and their copy inside `30-model-tg*.json`; the JavaScript port of mtlib in `docs/flasher/builder.js` and the `.syx` checks in `docs/flasher/flasher.js` | drumkilla | MIT | [`tools/mtlib/LICENSE`](tools/mtlib/LICENSE), [`tweaks/model-cycles_OS1.13/LICENSE-elektron-model-tweaks`](tweaks/model-cycles_OS1.13/LICENSE-elektron-model-tweaks) |
| [elektron-firmware-tool](https://github.com/mischa85/elektron-firmware-tool) | the basis of mtlib's container, codec and signature code (drumkilla's README), and the codec sketch in `notes/07` §3 | Marcel Bierling | MIT | [`tools/mtlib/LICENSE-elektron-firmware-tool`](tools/mtlib/LICENSE-elektron-firmware-tool) |
| [ms-multi-output](https://github.com/scottmetoyer/ms-multi-output) | `10-6ch-multiout.json`; its stubs reused in `11-6ch-usbup.json` (`tools/relocate_6ch.py`) and listed in `notes/07` §1; `tools/flash.py`, adapted from its `flash.py` | Scott Metoyer | MIT | [`tweaks/model-cycles_OS1.13/LICENSE-ms-multi-output`](tweaks/model-cycles_OS1.13/LICENSE-ms-multi-output) |
| [Model-TG](https://github.com/TinyGregAudio/Model-TG) | `30-model-tg.json` and `30-model-tg-st.json`, built by its own build; the excerpts in `tools/gen_model_tg.py`; the `31-syntakt-tg-*.json` files build on it | TinyGregAudio | MIT | [`tweaks/model-cycles_OS1.13/LICENSE-Model-TG`](tweaks/model-cycles_OS1.13/LICENSE-Model-TG) |
| [eurorack](https://github.com/pichenettes/eurorack) (Braids and stmlib) | the MACRO machine: `braids/macro_oscillator`, `analog_oscillator`, `digital_oscillator`, `resources` and `stmlib/utils/random` at commit `08460a6`, compiled unchanged into `25-macro.json`, `32-macro-tg.json` and the `*-macro.json` Syntakt files (`tools/gen_macro.py`, `tools/gen_macro_syntakt.py`). The sources are fetched into `vendor/` at build time, not stored here | Émilie Gillet | MIT | [`tweaks/model-cycles_OS1.13/LICENSE-Braids`](tweaks/model-cycles_OS1.13/LICENSE-Braids) |
| [Elektroid](https://github.com/dagargo/elektroid) | `tools/webxfer_check.py`, a Python transcription of `src/connectors/elektron.c` that checks the web flasher's fast USB sending. The flasher itself implements the protocol as Elektroid documents it | David García Goñi | GPL-3.0-or-later | [`LICENSES/GPL-3.0-or-later.txt`](LICENSES/GPL-3.0-or-later.txt) |

The web flasher serves the MIT texts next to the code that carries them (`docs/flasher/LICENSE-*.txt`, written by
`tools/gen_flasher_tweaks.py`).

Methods and ideas only, no code: [octamax](https://github.com/mxldyn/octamax) by mxldyn (no license published) and
[octa-bt-pt](https://github.com/bryantysinger/octa-bt-pt) by Bryan Tysinger (MIT). See `notes/03` and `notes/05`.

## Tools used but not included

The emulation proofs import [Unicorn](https://www.unicorn-engine.org/) (GPL-2.0) and numpy (BSD-3-Clause); the
command-line tools use mido and python-rtmidi (MIT); the web checks install jsdom (MIT) from npm; the mod code is
built with the GNU m68k toolchain (GPL-3.0), with `-nostdlib`, so no GCC runtime code ends up in the firmware. The
site loads its fonts (Familjen Grotesk, Tiny5, SIL Open Font License 1.1) from Google Fonts. None of these is
distributed with this repository.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). Contributions are accepted under the MIT License; a mod folder may carry its
own permissive license (MIT, BSD, ISC, 0BSD) in a `LICENSE` file next to it.
