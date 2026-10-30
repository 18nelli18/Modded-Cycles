# Direct Pattern Jump

PPPCCC/gialloinfuso, MIT, pinned at
[`43b894bd14f55313cef6381af9a008acec3ed0f1`](https://github.com/gialloinfuso/PPPCCC-M-S-Mods/tree/43b894bd14f55313cef6381af9a008acec3ed0f1).
`upstream.py` retains the original generator with local imports. `common.py`
provides its small assembler and reads displaced instructions from the user's
official OS. Supermodel adds the saved Global JUMP switch, OFF gates and menu.

Build with `tools/gen_direct_jump.py`; native proofs are
`tools/emu/test_direct_jump.py` and `test_direct_jump_ui.py`. See note204.
Test images and ROM data remain outside Git. No hardware result is claimed.
