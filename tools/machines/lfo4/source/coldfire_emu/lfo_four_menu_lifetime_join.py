# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Lachlan Fysh
# Original authored source selected for review. re/tools/coldfire_emu/lfo_four_menu_lifetime_join.py; lines 30-51,80-98.
# Unresolved integration bindings: see DEPENDENCIES.json.
def runtime_source(source=None):
    """Derive runtime admission from frozen lifetime or terminal-latch source.

    owner+40 was written before publication and is immutable authority. These
    checks assume the constructed owner is retained; bounds do not establish it.
    """
    source = SOURCE.read_text() if source is None else source
    return menus.replace_once(source,
        ' movel %a0@(40),%d1\n cmpil #STOCK_OWNER,%d1\n bne admit_done\n',
        f''' movel %a0@(40),%d1
 beq admit_done
 andil #3,%d1
 bne admit_done
 moveal %a0@(40),%a1
 cmpal #{NATIVE_M_ARENA:#x},%a1
 bcs admit_done
 cmpal #{NATIVE_M_ARENA_END-NATIVE_M_BYTES:#x},%a1
 bhi admit_done
 movel %a1@,%d1
 cmpil #{NATIVE_M_VPTR:#x},%d1
 bne admit_done
''')


def ui_source(core_symbols):
    """Transfer authored UI lease ownership to the enclosing lifetime wrapper.

    Keep all existing mode guards, original closures and invalidation. Remove
    only the now-nested authored begin/end calls; no MAIN body is bypassed.
    """
    source = menus.ui_source(core_symbols)
    rep = menus.replace_once
    begin = owned.CODE + core_symbols["write_begin"]
    end = owned.CODE + core_symbols["write_end"]
    source = rep(source, f"guard_extra:\n jsr {begin:#x}\n tstl %d0\n beq guard_bad_busy\n",
                 "guard_extra:\n /* Enclosing lifetime wrapper holds writer72. */\n")
    source = rep(source, f" movel %d0,%sp@-\n jsr {end:#x}\n pea %a2@(0x38)",
                 " movel %d0,%sp@-\n pea %a2@(0x38)")
    source = rep(source, f" moveal %d0,%a2\n jsr {begin:#x}\n tstl %d0\n beq selector_done\n movel %a2,%d0\n moveal SLOT,%a3",
                 " moveal %d0,%a2\n /* Enclosing lifetime wrapper holds writer72. */\n movel %a2,%d0\n moveal SLOT,%a3")
    source = rep(source, f"selector_publish:\n movel %d0,%a3@\n jsr {end:#x}",
                 "selector_publish:\n movel %d0,%a3@")
    return source
