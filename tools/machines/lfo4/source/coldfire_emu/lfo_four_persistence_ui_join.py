# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Lachlan Fysh
# Original authored source selected for review. re/tools/coldfire_emu/lfo_four_persistence_ui_join.py; lines 1-85.
# Unresolved integration bindings: see DEPENDENCIES.json.
"""Join persistence readiness to existing menu edit/draw/readback admission.

New source-derived layer over the frozen composition. Protocol writers still
use the core writer gate and may repair a context; UI consumers cannot edit or
borrow extra storage during that operation. No media or firmware construction.
"""
from dataclasses import replace

from . import lfo_four_persistence_composition as composition

life = composition.lifetime
transaction = composition.transaction
selector = composition.selector
reader = life.reader
rep = life.menus.replace_once


def context_check(*, reject):
    # A0 is an already identity/geometry-checked retained owner. IPL is still
    # raised for the existing bounded claim; no callbacks execute here.
    return f""" moveal PERSISTENCE_CONTEXT_SLOT,%a1
 tstl %a1
 beq {reject}
 cmpal %a1@(4),%a0
 bne {reject}
 tstl %a1@(24)
 bne {reject}
"""


def lifetime_source():
    return rep(transaction.lifetime_source(),
        'admit_claim:\n moveq #1,%d0\n',
        'admit_claim:\n'+context_check(reject='admit_bad')+' moveq #1,%d0\n')


def reader_source():
    source = rep(reader.SOURCE.read_text(),
        ' moveal %sp@(8),%a0\n tstl %a0\n beq acquire_stock',
        ' moveal %sp@(8),%a0\n tstl %a0\n beq acquire_stock\n'
        ' tstl STATUS+4\n bne acquire_done\n cmpal STATUS,%a0\n bne acquire_done')
    source = rep(source, ' clrl SLOT\n clrl SLOT-4\n moveq #1,%d0',
        ' jsr DISABLE\n moveq #1,%d0')
    # Before stock-selection early return as well as the read-gate store.
    return rep(source, ' movel %sp@(12),%d1\n cmpil #6,%d1\n',
        context_check(reject='acquire_done')+' movel %sp@(12),%d1\n cmpil #6,%d1\n')


def join(supplied, slot, *, runtime_binding=False):
    if not isinstance(supplied, selector.Join):
        raise TypeError('supply checked selector/persistence composition')
    rb = dict(supplied.transaction.supplied.reader.bindings,
        STATUS=transaction.STATUS,
        DISABLE=supplied.transaction.entry('terminal_disable'),
        SELECTOR_DRAW=life.menus.UI+supplied.base[2]['selector_draw'],
        PERSISTENCE_CONTEXT_SLOT=slot)
    rc, rs = life.owned.generated('\n'.join(f'.equ {n},{v:#x}' for n,v in rb.items())+
        '\n'+reader_source())
    lb = dict(supplied.bindings, PERSISTENCE_CONTEXT_SLOT=slot,
        READER_NORMAL=reader.CODE+rs['normal_ctor'],
        READER_SETUP=reader.CODE+rs['setup_ctor'])
    for name in life.DRAW_NAMES:
        lb['READER_'+name.removeprefix('draw_').upper()] = reader.CODE+rs[name]
    final_lifetime = lifetime_source()
    if runtime_binding:
        final_lifetime = life.runtime_source(final_lifetime)
    lc, ls = life.owned.generated('\n'.join(f'.equ {n},{v:#x}' for n,v in lb.items())+
        '\n'+final_lifetime)
    parts = tuple((a, lc if a == life.CODE else rc if a == reader.CODE else data)
        for a,data in supplied.components)
    spans = sorted((a,a+len(data)) for a,data in parts)
    if any(left[1]>right[0] for left,right in zip(spans,spans[1:])):
        raise ValueError('UI readiness code overlaps another component')
    names = {0x4001c3de:'normal_ctor',0x4001c444:'setup_ctor'}
    overlays = tuple(replace(o,replacement=reader.k.words(life.CODE+ls[names[o.address]]))
        if o.address in names else o for o in supplied.overlays)
    return replace(supplied, reader_code=rc, reader_symbols=rs,
        lifetime_code=lc, lifetime_symbols=ls, bindings=lb,
        components=parts, overlays=overlays)


def compose(*, stock_owner, main=composition.random.engine.f.MAIN_PATH, runtime_binding=False):
    supplied, ps, layout, slot = composition.compose(stock_owner=stock_owner,main=main,
        runtime_binding=runtime_binding)
    return join(supplied,slot,runtime_binding=runtime_binding),ps,layout,slot
