# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Lachlan Fysh
# Original authored source selected for review. re/tools/coldfire_emu/lfo_four_selector_oom_join.py; lines 17-31.
# Unresolved integration bindings: see DEPENDENCIES.json.
def ui_source(core_symbols,append):
    source = life.ui_source(core_symbols)
    source = life.menus.replace_once(source,' pea 84\n jsr 0x400802e0',
        ' pea 84\n.globl selector_item_allocate\nselector_item_allocate:\n jsr 0x400802e0')
    return life.menus.replace_once(source, ' jsr 0x40072ce6\n addql #8,%sp', f''' jsr {append:#x}
 addql #8,%sp
 tstl %d0
 bne selector_append_ok
 /* Private item never published: dispose all four closures and free it
  * through the authentic deleting destructor, not a naked free. */
 movel %a3,%sp@-
 jsr 0x400dadc4
 addql #4,%sp
 bra setup_done
selector_append_ok:''')
