# Modded-Cycles

Firmware mods for the **Elektron Model:Cycles**. The first goal: send the **6 tracks over USB as 6 separate channels**
instead of the stereo mix only, so you can record real stems in your DAW. Then go further: new machines, more channels, more features.

> ⚠️ **No Elektron firmware is included in this repository** — neither original nor modified.
> You bring your own copy of the official OS, downloaded from elektron.se.
> This repository only contains analysis, byte-level patch tables, assembly/C sources and tools.
> Not affiliated with or endorsed by Elektron. Flashing a modified OS is **at your own risk** and may void your warranty.

## Quick start: flash from your browser

Open the **[web flasher](https://18nelli18.github.io/Modded-Cycles/flasher/)** in Chrome, Edge or Opera (desktop).
It builds the modified firmware from your official OS file and sends it to your Model:Cycles over Web MIDI.
Everything happens in your browser: nothing is uploaded anywhere.

You need:
- your official **`model-cycles_OS1.13.syx`** ([elektron.se](https://www.elektron.se/support-downloads/modelcycles), unzip the download);
- a **MIDI interface** connected to the Model:Cycles **MIDI IN** (3.5 mm jack: use the DIN adapter supplied with the Model:Cycles,
  or a stereo jack cable if your interface has a TRS MIDI out). It is also your way back if anything goes wrong.

The startup menu (`FUNC` + power on, then `TRIG 4`) only listens to the MIDI IN, never to USB.
A USB-only first flash is possible from the official OS (`CONFIG > UPGRADE`), but getting back to stock may then require the MIDI IN.

## Command line

A pure-Python toolchain: no compiler, no firmware in the repo. See [`BUILD.md`](BUILD.md) (in French).

```sh
python3 tools/build.py --list
python3 tools/build.py -i model-cycles_OS1.13.syx -t 6ch-usbup         # 6 channels, keeps OS updates over USB
python3 tools/build.py -i model-cycles_OS1.13.syx -t 6ch-multiout      # 6 channels, reference build
python3 tools/build.py -i model-cycles_OS1.13.syx -t sdvintage-snare   # SD VINTAGE machine instead of SNARE
```

Then flash with the ready-made scripts. They install the dependencies, check the file, guide you and send it — see [`FLASH.md`](FLASH.md) (in French).

```sh
./flash.sh        # macOS / Linux
flash.bat         # Windows (double-click)
```

The web flasher is a JavaScript port of `build.py` and `mtlib`, checked byte for byte against the Python
(`tools/webflash_check.sh`, `tools/webbuild_check.sh`, `tools/webflash_smoke.sh`).

## Features

By priority. Feasibility is detailed in [note 10](notes/10-faisabilite-fonctionnalites.md) (in French).

| Feature | Status |
|---|---|
| **6-channel** USB output | ✅ code ready, buildable here — **waiting for a hardware test** |
| Keep **OS updates over USB** with the 6-channel mod | 🟡 `6ch-usbup` variant ready and checked in emulation — **waiting for a hardware test** ([note 13](notes/13-6ch-upgrade-usb.md)) |
| Extra drum engine: **SD VINTAGE** (vintage snare, inspired by the Syntakt) | 🟡 step 1 (replaces SNARE) ready and validated in the emulated engine — **waiting for a hardware test**; 7th machine: plan ready ([note 14](notes/14-machine-sd-vintage.md)) |
| **12-channel** USB output (per-track pan) | 🟡 feasible, to develop (through an **8-channel** milestone: 6 tracks + stereo mix, [note 11](notes/11-conception-8-canaux.md)) |
| Change the **effect algorithms** | 🔴 no (tweaking parameters: 🟡) |
| **Sample engine** (like the Model:Samples) | 🔴 out of reach as a Model:Cycles mod |
| **2 LFOs**, syncable and assignable | 🟠 heavy (more destinations for the current LFO: 🟡) |
| **Polyrhythm** (per-track time signature) | 🟡 partly there in stock firmware |
| **MIDI control over USB** (clock, start/stop) | ✅ already supported in stock firmware (settings only) |
| **Arpeggiator** (chromatic mode) | 🟠 long term |
| **Scale** (chromatic mode) | 🟡 feasible, medium effort |
| **Polyphony** for the synth engine | 🔴 very hard |

## Project status

- The 6-tracks-over-USB mod **exists** ([scottmetoyer/ms-multi-output](https://github.com/scottmetoyer/ms-multi-output), MIT)
  and is ported here as a tweak. Our build **reproduces the known-good MAIN OS byte for byte**.
  It has **never been flashed on a real Model:Cycles** yet (only on a Model:Samples running the Cycles OS).
- The official OS **1.13** (latest version) has been analysed in depth ([note 09](notes/09-analyse-firmware-1.13.md)).
- The synth engine (the 6 machines are 6 *mappings* of one FM engine) is decoded and **emulated** (`tools/emu/`).
  One more engine, **SD VINTAGE**, is written in C, compiled for the ColdFire CPU and validated in the emulated engine ([note 14](notes/14-machine-sd-vintage.md)).
- **Milestone 1**: validate the 6-channel mod on a real Model:Cycles. Nothing has been flashed yet.

Roadmap: [`notes/08-feuille-de-route.md`](notes/08-feuille-de-route.md) (in French).

## Documentation

The technical documentation is written in French.

| Document | Topic |
|---|---|
| [`BUILD.md`](BUILD.md) | Building a modified firmware image (pure Python) |
| [`FLASH.md`](FLASH.md) | **Flashing your Model:Cycles**: detailed guide and scripts |
| [`dossier-technique.md`](dossier-technique.md) | Summary of the Elektronauts thread "Model:Cycles Q&A with Ess", every fact quoted from its source |
| [`notes/README.md`](notes/README.md) | **Index of the technical notes** and key figures |
| [`notes/10-faisabilite-fonctionnalites.md`](notes/10-faisabilite-fonctionnalites.md) | **Feasibility, feature by feature** |
| [`tools/`](tools/) · [`tweaks/`](tweaks/) · [`docs/flasher/`](docs/flasher/) | Build tools (mtlib), patch tables (JSON), web flasher |

## Credits

Upstream projects, all MIT licensed, none including firmware:

- [`scottmetoyer/ms-multi-output`](https://github.com/scottmetoyer/ms-multi-output) — the 6-channel mod (Model:Samples and Model:Cycles)
- [`drumkilla/elektron-model-tweaks`](https://github.com/drumkilla/elektron-model-tweaks) — `mtlib` (SysEx transport, aPLib, ELE3 container and HMAC in Python) and the JSON tweak format, vendored in `tools/mtlib/`
- [`mischa85/elektron-firmware-tool`](https://github.com/mischa85/elektron-firmware-tool) — unpacking, repacking and re-signing `.syx` files (alternative C toolchain)
- [`mxldyn/octamax`](https://github.com/mxldyn/octamax) — reverse engineering of the Octatrack OS (method, tools, pitfalls)
