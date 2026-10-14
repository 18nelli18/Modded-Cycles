# Supermodel integration — third-party notices

These notices cover the new ChordKeys and Slice integration. Existing mod
licenses remain beside their recipes and are linked from their flasher cards.
Firmware images are not bundled. Recipe `old` fields are checks against the
user's firmware; Elektron's firmware is not licensed under these MIT notices.

- **ChordKeys:** Nico Heuser, integrated by 18nelli18 and contributors in
  [PR #87](https://github.com/18nelli18/Modded-Cycles/pull/87), revision
  `770369210cab889fd8642184632d7b9853afd33e`, based on Nico revision
  `c34e7973139ed8f27c46b57666b66ec84c15f8e1`. MIT; copyright 2026
  18nelli18 and Modded-Cycles contributors. The original sources and own compiled
  recipe are pinned. Supermodel changes their placement and separates HARMONY
  from its audio LFO2 depth. The MIT text is in
  [tools/LICENSE-ChordKeys.txt](tools/LICENSE-ChordKeys.txt) and beside the copied
  sources in `tools/machines/chord_keys_compat/LICENSE`.
- **Model-TG Slice varispeed:** TinyGregAudio and
  [roterodamus](https://github.com/roterodamus/Model-TG), revision
  `0c567d8c9e3d0c61837e1d91ac2f5c747ea9763f`. MIT, copyright 2026
  TinyGregAudio. Supermodel adapts that delta to its pinned Model-TG base without
  moving existing exported functions. The MIT text remains in
  [LICENSE-Model-TG](tweaks/model-cycles_OS1.13/LICENSE-Model-TG), with a copy beside
  the adapter in `tools/machines/model_tg_varispeed/LICENSE`.

The integration remains experimental pending hardware testing. MIDI Bank
storage hooks remain disabled; its sequences, CC assignments and locks are RAM-only.
