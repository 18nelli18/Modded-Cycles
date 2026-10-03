# Modded-Cycles

Firmware mods for the **Elektron Model:Cycles**. The first goal: send the **6 tracks over USB as 6 separate channels**
instead of the stereo mix only, so you can record real stems in your DAW. Then go further: new machines, more channels, more features.

> ⚠️ **No Elektron firmware is included in this repository** — neither original nor modified.
> You bring your own copy of the official OS, downloaded from elektron.se.
> This repository only contains analysis, byte-level patch tables, assembly/C sources and tools.
> Not affiliated with or endorsed by Elektron. Flashing a modified OS is **at your own risk** and may void your warranty.

## Quick start: flash from your browser

Open the **[web flasher](https://18nelli18.github.io/Modded-Cycles/flasher/)** in Chrome, Edge or Opera (desktop).
What each mod does, step by step: the **[guide](https://18nelli18.github.io/Modded-Cycles/guide/)**.
Tick the mods you want, drop your official OS file, connect the Model:Cycles over USB and flash.
The page builds the modified firmware from your file and sends it over Web MIDI.
Everything happens in your browser: nothing is uploaded anywhere.

You need:
- your official **`model-cycles_OS1.13.syx`** ([elektron.se](https://www.elektron.se/support-downloads/modelcycles), unzip the download);
- a **USB cable**. On the Model:Cycles, open `CONFIG > UPGRADE` and confirm: it waits for the firmware.

The web flasher only sends over USB, and only offers mods that keep OS updates over USB working.
Its **Samples OS** tab turns the Model:Cycles into a Model:Samples (drop both official OS files); coming back needs a MIDI interface.
The **SD VINTAGE** box adds the real Syntakt SD VINTAGE engine as a 7th machine **SDVtg** next to SNARE (default), or puts it in place of SNARE; both tested on a real Model:Cycles: drop your official `Syntakt_OS1.42.syx` ([elektron.se](https://www.elektron.se/support-downloads/syntakt); 1.41 works too, same engines) as well, the engine is read from it in your browser.
If a Model:Cycles ever stops starting, recovery goes through the startup menu (`FUNC` + power on, then `TRIG 4`),
which only listens to the **MIDI IN**: that needs a MIDI interface and the command-line scripts below ([`FLASH.md`](FLASH.md)).

## Command line

A pure-Python toolchain: no compiler, no firmware in the repo. See [`BUILD.md`](BUILD.md) (in French).

```sh
python3 tools/build.py --list
python3 tools/build.py -i model-cycles_OS1.13.syx -t 6ch-usbup         # 6 channels, keeps OS updates over USB
python3 tools/build.py -i model-cycles_OS1.13.syx -t 6ch-multiout      # 6 channels, reference build (no USB updates)
python3 tools/build.py -i model-cycles_OS1.13.syx -t sdvintage-snare   # SD VINTAGE machine instead of SNARE
python3 tools/build.py -i model-cycles_OS1.13.syx -t 6ch-usbup,latching-mute,trig-preview,browser-scroll
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
| **6-channel** USB output | ✅ **tested on a real Model:Cycles** — in the web flasher |
| Keep **OS updates over USB** with the 6-channel mod | ✅ `6ch-usbup`, the version the web flasher installs ([note 13](notes/13-6ch-upgrade-usb.md)) |
| **The real Syntakt SD VINTAGE engine**, extracted at build time from *your* Syntakt OS file | ✅ `sdvintage-exact`: the Syntakt's own code and tables, relocated into the Model:Cycles, replace SNARE — **sample-identical** to the Syntakt in emulation, and the bootstrap's own decompressor reads the bigger OS back exactly; **tested on a real Model:Cycles** (2026-09-30, flashed over USB from the web flasher); now command line only (`build.py --syntakt`): the web flasher only adds engines ([note 17](notes/17-portage-exact-syntakt.md)) |
| The real SD VINTAGE as a **7th machine** (SDVtg), next to SNARE | ✅ `sdvintage-7th`: 7 machines in the MACHINES menu, its own knob names and defaults from the Syntakt (Inharm, Freq Complex, Pitch Sweep, Mod Envelope), SNARE unchanged; **tested on a real Model:Cycles** (2026-09-30, web flasher); 26 checks on the OS's own code in emulation ([note 18](notes/18-septieme-machine.md)) |
| The real **CP VINTAGE** clap as an **8th machine** (CPVtg), with SDVtg | ✅ `syntakt-vintage`: 8 machines in the MACHINES menu, CPVtg with the Syntakt's knob names and defaults (Body Char, Balance, Spacing Crunch, Body Envelope); sample-identical to the Syntakt in emulation (26 checks); **tested on a real Model:Cycles** (2026-09-30, web flasher) ([note 19](notes/19-cp-vintage-8e-machine.md)) |
| **Pick the Syntakt engines you want** (SD VINTAGE, CP VINTAGE, **SY TOY**, **SY BITS**, **SY SWARM**) | ✅ one checkbox per engine in the web flasher, any combination, added after the 6 original machines; **SYToy** (SY TOY: Form, Impact, Bright, Partial Decay) is sample-identical to the Syntakt in emulation and **tested on a real Model:Cycles**, alone and with SDVtg + CPVtg (2026-09-30); **SYBit** (SY BITS: Detune, Balance, Rate Redux, Waveform, PUNCH = Bit Redux) is sample-identical in emulation and **tested on a real Model:Cycles** on its own ([note 21](notes/21-sy-bits.md)); the new **SYSwm** (SY SWARM supersaw: Noise Mod, Detune Anim, Detune, Osc Mix, PUNCH = sub-octave) is sample-identical in emulation and **not hardware-tested yet** ([note 22](notes/22-sy-swarm.md)). Set tracks that use an added machine back to an original machine before changing the choice or going back to the official firmware ([note 20](notes/20-moteurs-syntakt-a-cocher.md)) |
| Extra drum engine: **SD VINTAGE** (vintage snare from the Syntakt) | ✅ step 1 (replaces SNARE) **tested on a real Model:Cycles**; **v2 retuned on the real Syntakt SD VINTAGE** running in our emulator (same pitch, sweep, decay and noise spectrum, knobs mean what they mean on the Syntakt) — command line only for now ([note 16](notes/16-moteur-syntakt.md)) |
| **12-channel** USB output (per-track pan) | 🟡 feasible, to develop (through an **8-channel** milestone: 6 tracks + stereo mix, [note 11](notes/11-conception-8-canaux.md)) |
| Change the **effect algorithms** | 🔴 no (tweaking parameters: 🟡) |
| **Sample engine** (like the Model:Samples) | ✅ through **[Model-TG](https://github.com/TinyGregAudio/Model-TG)** by TinyGregAudio (MIT): a Sampler machine with seven playback modes, resampling, a retrig page with master FX, slide trigs and more. Offered in the web flasher at its version 1.1, built by its own build with one change from this project: in mute mode, each track key mutes at once, as with the latching mute alone (Model-TG queues them until you leave the mode); on its own or with the 6-channel mod. With the Syntakt engines: a combined version (the Sampler stays the 7th machine, the engines follow), where slide trigs work on the engines too. Model-TG 1.1 with the 5 engines and 6-channel audio is **tested on the hardware** ([note 31](notes/31-model-tg.md), in French) |
| **2 LFOs**, syncable and assignable | 🟠 heavy (more destinations for the current LFO: 🟡) |
| **Polyrhythm** (per-track time signature) | 🟡 partly there in stock firmware |
| **MIDI control over USB** (clock, start/stop) | ✅ already supported in stock firmware (settings only) |
| **Arpeggiator** (in place of the retrig) | ✅ in the web flasher: hold several notes with RETRIG (or A.On) and they play as an arpeggio at the retrig rate; FUNC + RETRIG gains **Arp** (UP, DOWN, UPDN, RAND, PLAY, OFF) and **Oct** (1 to 4), saved with the pattern. In live recording, the notes it plays are recorded one by one (version 1.13, checked in the emulator, waiting for a hardware test). Checked in the emulator against the OS's own event loop, and **tested on the hardware** with Model-TG, the 5 engines and 6-channel audio ([note 32](notes/32-arpegiateur.md), in French) |
| **Scale** (chromatic mode) | 🟡 feasible, medium effort |
| **Polyphony** for the synth engine | 🔴 very hard |

Also in the web flasher, by [drumkilla](https://github.com/drumkilla/elektron-model-tweaks) (tested on real hardware by their author,
our build matches their own tool byte for byte):

| Tweak | What it does |
|---|---|
| `latching-mute` | Hold `TRK` and tap `FUNC`: mute mode stays on, so you mute tracks without holding `FUNC` |
| `trig-preview` | Sequencer stopped: hold a step and press `PAGE` to hear it (note, length, p-locks) |
| `browser-scroll` | Long names scroll in the sound browser |

Requests from the community (Reddit) and how we handle them: [note 15](notes/15-demandes-reddit.md) (in French).

| Request | Status |
|---|---|
| Mute without holding `FUNC` | ✅ `latching-mute` (above) |
| Bundle with trig preview | ✅ `trig-preview` (above) |
| Run the **Model:Samples OS** on a Model:Cycles | ✅ **tested on a real Model:Cycles** (2026-09-29) — *Samples OS* tab of the web flasher, or `tools/crossflash.py`. Built from both official files: same bootstrap, same updater, same RAM setup on both machines. The way back to the Cycles OS goes through the MIDI IN (note 15 §3) |
| Port the **Syntakt digital machines** | 🟡 the Syntakt's audio engine (a second ColdFire) runs in our emulator; its FM machines turn out to be the Model:Cycles machines plus SD VINTAGE and CP VINTAGE. SD VINTAGE v2 is retuned on it ([note 16](notes/16-moteur-syntakt.md)) |

## Project status

- The 6-tracks-over-USB mod **exists** ([scottmetoyer/ms-multi-output](https://github.com/scottmetoyer/ms-multi-output), MIT)
  and is ported here as a tweak. Our build **reproduces the known-good MAIN OS byte for byte**.
  It now **works on a real Model:Cycles** (before, it had only run on a Model:Samples running the Cycles OS).
- The official OS **1.13** (latest version) has been analysed in depth ([note 09](notes/09-analyse-firmware-1.13.md)).
- The synth engine (the 6 machines are 6 *mappings* of one FM engine) is decoded and **emulated** (`tools/emu/`).
  One more engine, **SD VINTAGE**, is written in C, compiled for the ColdFire CPU and validated in the emulated engine ([note 14](notes/14-machine-sd-vintage.md)).
- **Milestone 1 reached (2026-09-29)**: the 6-channel mod and SD VINTAGE work on a real Model:Cycles.

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
| [`notes/21-architecture-materielle.md`](notes/21-architecture-materielle.md) | **Hardware architecture**, read from photos of the PCB: CPU, memories, USB PHY, audio output, MIDI input, key and LED latches |
| [`tools/`](tools/) · [`tweaks/`](tweaks/) · [`docs/flasher/`](docs/flasher/) | Build tools (mtlib), patch tables (JSON), web flasher |

## Credits

Upstream projects, all MIT licensed, none including firmware:

- [`scottmetoyer/ms-multi-output`](https://github.com/scottmetoyer/ms-multi-output) — the 6-channel mod (Model:Samples and Model:Cycles)
- [`drumkilla/elektron-model-tweaks`](https://github.com/drumkilla/elektron-model-tweaks) — the latching-mute, trig-preview and browser-scroll tweaks (in `tweaks/`, unchanged), `mtlib` (SysEx transport, aPLib, ELE3 container and HMAC in Python) and the JSON tweak format, vendored in `tools/mtlib/`
- [`TinyGregAudio/Model-TG`](https://github.com/TinyGregAudio/Model-TG) — the Sampler machine, resampling, retrig and master FX, slide trigs, and more; generated from a pinned commit (v1.1.0) by `tools/gen_model_tg.py` with its own build, from a copy of its source with one listed change (mutes at once; `tweaks/model-cycles_OS1.13/30-model-tg.json`, license in `LICENSE-Model-TG`); `30-model-tg-st.json`, the base of the combined version, is built the same way with one more listed change
- [`mischa85/elektron-firmware-tool`](https://github.com/mischa85/elektron-firmware-tool) — unpacking, repacking and re-signing `.syx` files (alternative C toolchain)
- [`mxldyn/octamax`](https://github.com/mxldyn/octamax) — reverse engineering of the Octatrack OS (method, tools, pitfalls)
