# Four native LFO contribution source for review

This is a comprehensive original-source proposal at private Cycles pin `68438b1a417390f1f60f50f925acdeea1ddba6ce`, against Modded-Cycles `afed481dc35f4cfc24013508afebc300efcc15b3`.

It carries native runtime/publication, selector and both native menus, display/invalidation/navigation interfaces, reader/menu lifetimes and checked append, safe destination lookup/enumeration/editor, RANDOM and SPEED, Sound/Project/BANK/save/read persistence source. The portable codec and host publication checker support the native stack; they do not replace it.

Complete authored files and partial authored files are identified in `SOURCE-MANIFEST.json`. Existing code is retained; headers and extraction boundaries do not implement missing firmware integration. `DEPENDENCIES.json` lists unresolved bindings, macros, globals, original-function stubs and caller lifetime contracts. Several assembler files are intentionally incomplete and must not be assembled or installed as a product. No target builder, flasher/release registration, firmware image or copied stock numerical kernel is supplied.

The pure host subsets preserve the original test functions and synthetic inputs while omitting assembler setup, stock tables and private fixtures. Their result is only a host contract check. Prior CPU evidence is retained privately and summarized in the review; separate passes and 176 broad checks are not complete LFO acceptance.

Future draft series: (1) owned runtime + native editor + safe destinations; (2) SPEED/RANDOM/sync/reset/Fade/phase; (3) full-capacity Sound persistence with portable host support; (4) Project/BANK/media lifecycle; (5) combined layout/boot/resource/physical qualification. Historical original contracts feed the relevant stages. The independent validator allocation guard is optional and its current mixed stock-window source is excluded, not substituted for the LFOs.

Required endpoint: four proper LFOs per track, all stock waveforms/destinations and full editing/control/persistence. Current prototype source does not establish that installed behavior. Profile synchronization, p-lock/recording, transport/MIDI cadence, observer/concurrency/rebind/reset/destroy, general Project switching, durable media/cache/DMA, boot/heap/stack/deadline/coexistence and physical acceptance remain open.

MIT is approved for original contributed code only. This directory's LICENSE lists its exact additions and the new note/index row; the separate portable foundation retains its existing scoped notice. Neither license covers vendor firmware/data, existing upstream/private content or excluded material. `EXCLUSIONS.json` records exact omitted files/ranges and dependencies rather than hiding them.

Synthetic-only check (no target/compiler/firmware input):

```sh
env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tools/machines/lfo4/source python3 -B -m unittest \
  coldfire_emu.test_lfo_four_publication_contract \
  coldfire_emu.live_profile_candidate.test_contract_host \
  coldfire_emu.live_profile_candidate.native_adapter.test_oracle_host \
  coldfire_emu.live_profile_candidate.native_adapter.safe_enum.test_model_host \
  coldfire_emu.test_menu_rows_host -v
```

Target-backed historical reproduction commands and exact evidence pins are retained privately. No target-backed tests were executed for this extracted handoff. This draft supplies source for review and does not install or qualify the four-LFO feature.
