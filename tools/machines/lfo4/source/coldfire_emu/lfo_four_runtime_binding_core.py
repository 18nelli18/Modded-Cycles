# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Lachlan Fysh
# Original authored source selected for review. re/tools/coldfire_emu/lfo_four_runtime_binding_core.py; lines 1-93.
# Unresolved integration bindings: see DEPENDENCIES.json.
"""Opt-in derived startup binding; historical checked recipe stays unchanged.

The retained owner+40 is the binding authority, not a freshly supplied vtable.
Bounds and tags are structural checks, not allocation/provenance proof. Callers
must own the constructor-backed full parent and serialize initial publication.
"""
from . import lfo_four_owned_candidate as joined
from . import test_lfo2_owned_heap_setup as heap


def derive(source, owner_bytes, context_bytes=698992):
    rep = joined.replace_once
    anchor = ' clrl %a6@(-4)\n movel SLOT,%d0\n bne setup_done'
    replacement = f''' clrl %a6@(-4)
 /* Validate the complete native parent before dereference or allocation. */
 moveal %a6@(8),%a3
 movel %a3,%d0
 andil #3,%d0
 bne setup_binding_reject
 cmpal #0x40000000,%a3
 bcs setup_binding_reject
 cmpal #0x47ffec00,%a3
 bhi setup_binding_reject
 movel %a3@,%d0
 cmpil #0x400fcf3c,%d0
 bne setup_binding_reject
 movel SLOT,%d0
 beq setup_binding_new
 /* Only the same boot-retained owner may be reused. Never replace it. */
 moveal %d0,%a0
 andil #15,%d0
 bne setup_binding_reject
 cmpal #{heap.ARENA:#x},%a0
 bcs setup_binding_reject
 cmpal #{heap.ARENA_END-owner_bytes:#x},%a0
 bhi setup_binding_reject
 movel %a0@,%d0
 cmpil #0x4c464f34,%d0
 bne setup_binding_reject
 movel %a0@(4),%d0
 cmpil #1,%d0
 bne setup_binding_reject
 cmpal %a0@(40),%a3
 bne setup_binding_reject
 cmpal %a0@(6444),%a0
 bne setup_binding_reject
 movel %a0@(6448),%d0
 cmpil #0x524e4731,%d0
 bne setup_binding_reject
 lea %a0@(4400),%a1
 cmpal RUNTIME_SLOT,%a1
 bne setup_binding_reject
 moveal BASE+(persistence_context_slot-setup),%a1
 tstl %a1
 beq setup_binding_reject
 movel %a1,%d0
 andil #15,%d0
 bne setup_binding_reject
 cmpal #{heap.ARENA:#x},%a1
 bcs setup_binding_reject
 cmpal #{heap.ARENA_END-context_bytes:#x},%a1
 bhi setup_binding_reject
 movel %a1@,%d0
 cmpil #0x4c465347,%d0
 bne setup_binding_reject
 cmpal %a1@(4),%a0
 bne setup_binding_reject
 cmpal %a1@(12),%a3
 bne setup_binding_reject
 movel %a1@(8),%d0
 cmpl 0x404d2974,%d0
 bne setup_binding_reject
 movel %a0,%d0
 bra setup_done
setup_binding_new:'''
    source = rep(source, anchor, replacement)
    return rep(source, 'setup_done:\n',
        ' bra setup_done\nsetup_binding_reject:\n moveq #0,%d0\nsetup_done:\n')


def startup_source(source):
    """Skip getter on NULL factory and setup on NULL getter; restore caller.

    No stock factory internals or source63 installer behaviour are replaced.
    This closes the authored wrapper's boundaries, not factory-internal OOM.
    """
    rep = joined.replace_once
    source = rep(source, ' jsr 0x400cf866\n movel %d0,%sp@-',
        ' jsr 0x400cf866\n tstl %d0\n beq startup_restore\n movel %d0,%sp@-')
    source = rep(source, ' jsr 0x4000eb9c\n movel %d0,%sp@',
        ' jsr 0x4000eb9c\n tstl %d0\n beq startup_drop_argument\n movel %d0,%sp@')
    return rep(source, ' addql #4,%sp\n movew %sp@(60),%d0',
        'startup_drop_argument:\n addql #4,%sp\nstartup_restore:\n movew %sp@(60),%d0')
