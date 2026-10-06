# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Lachlan Fysh
# Original authored source selected for review. re/tools/coldfire_emu/lfo_four_owned_candidate.py; lines 37-40,43-77.
# Unresolved integration bindings: see DEPENDENCIES.json.
def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError(f"integration template changed: {old!r}")
    return source.replace(old, new, 1)


def ui_source(symbols):
    """Join the existing authored native callback wrappers to owned metadata.

No host-populated mirror of the eighteen extra configs or selector is used.
Extra edits/selection acquire the same writer lease as codec/render users.
Stock LFO1 tails into its original callback without borrowing an extra lease.
"""
    source = (HERE / "lfo_indexed_native.S").read_text()
    source = replace_once(source, ".equ BASE,0x41650000", f".equ BASE,{UI:#x}")
    source = ".equ SLOT,0x40000304\n" + source
    source = replace_once(source, " cmpl META+40,%d1", " moveal SLOT,%a1\n tstl %a1\n beq resolve_finish\n cmpl %a1@(40),%d1")
    source = replace_once(source, " moveal #META,%a1", " moveal SLOT,%a1")
    source = replace_once(source, " clrl META+8", " moveal SLOT,%a0\n tstl %a0\n beq guard_pass\n clrl %a0@(8)")
    source = replace_once(source, "guard_extra:\n", f"guard_extra:\n jsr {owned.CODE + symbols['write_begin']:#x}\n tstl %d0\n beq guard_bad_busy\n")
    source = replace_once(source, " movel %d0,%sp@-\n pea %a2@(0x38)", f" movel %d0,%sp@-\n jsr {owned.CODE + symbols['write_end']:#x}\n pea %a2@(0x38)")
    source = replace_once(source, "guard_bad_track:\n", "guard_bad_busy:\n moveq #4,%d0\n bra guard_blocked\nguard_bad_track:\n")
    source = replace_once(source, " movel %d0,META+8", " moveal SLOT,%a0\n movel %d0,%a0@(8)")
    source = replace_once(source, " movel %d0,META+12", " moveal SLOT,%a0\n tstl %a0\n beq install_status_done\n movel %d0,%a0@(12)\ninstall_status_done:")
    source = replace_once(source, " moveal #META,%a3", f" moveal %d0,%a2\n jsr {owned.CODE + symbols['write_begin']:#x}\n tstl %d0\n beq selector_done\n movel %a2,%d0\n moveal SLOT,%a3")
    source = replace_once(source, "selector_publish:\n movel %d0,%a3@", f"selector_publish:\n movel %d0,%a3@\n jsr {owned.CODE + symbols['write_end']:#x}")
    source = replace_once(source, "selector_draw_bad:\n moveq #63,%d0", "selector_draw_stock:\n moveq #49,%d0\n bra selector_draw_text\nselector_draw_bad:\n moveq #63,%d0")
    source = replace_once(source, "selector_draw:\n linkw %a6,#-4", "selector_draw:\n linkw %a6,#-4\n moveal SLOT,%a0\n tstl %a0\n beq selector_draw_stock")
    # Only the guard and selector draw use these remaining fixed metadata loads.
    if source.count(" moveal #META,%a0") != 3:
        raise ValueError("metadata template changed")
    source = source.replace(" moveal #META,%a0", " moveal SLOT,%a0")
    start = source.index("initialize_selection:\n")
    end = source.index("/* Extra entries", start)
    source = source[:start] + "initialize_selection:\n rts\n" + source[end:]
    source = replace_once(source, " clrl %sp@(20)\n addql #1,META+68", " clrl %sp@(20)\n moveal SLOT,%a0\n addql #1,%a0@(68)")
    # The active entry vtable uses the checked core's extra_store; this legacy
    # helper is not installed. Resolve all metadata references regardless.
    if re.search(r"(?:#META|META\+)", source):
        raise ValueError("fixed metadata escaped owned routing")
    return source
